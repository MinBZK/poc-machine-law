"""API endpoints for the wallet module."""

import re

import httpx
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from web.dependencies import TODAY, get_case_manager, get_claim_manager, get_machine_service, templates
from web.engines import CaseManagerInterface, ClaimManagerInterface, EngineInterface
from web.feature_flags import is_wallet_enabled
from web.routers.laws import evaluate_law
from web.services.wallet import get_wallet_data

router = APIRouter(prefix="/wallet", tags=["wallet"])


class WalletStartRequest(BaseModel):
    usecase: str


@router.post("/")
async def housing(request_body: WalletStartRequest):
    """Handle housing use case requests.

    Validates that the payload contains exactly {"usecase": "housing"} and returns
    a session URL and token for the disclosure session.
    """
    # Validate that usecase is exactly "housing"
    if request_body.usecase != "housing":
        raise HTTPException(status_code=403, detail="invalid wallet usecase")

    # Prepare the disclosure session request
    disclosure_payload = {
        "usecase": "housing",
        "dcql_query": {
            "credentials": [
                {
                    "id": "housing_attestation",
                    "format": "dc+sd-jwt",
                    "meta": {"vct_values": ["com.example.housing"]},
                    "claims": [
                        {"path": ["rent"]},
                        {"path": ["service_charges"]},
                        {"path": ["eligible_service_charges"]},
                    ],
                }
            ]
        },
        "return_url_template": "http://127.0.0.1:8000/?wallet_session_token={session_token}",
    }

    # Make HTTP call to disclosure service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:3010/disclosure/sessions",
                json=disclosure_payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            # Parse the session token from the response
            disclosure_response = response.json()
            session_token = disclosure_response.get("session_token")

            if not session_token:
                raise HTTPException(status_code=500, detail="No session token received from disclosure service")

    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Failed to create disclosure session: {str(e)}")

    # Return the disclosure session information
    return JSONResponse(
        content={
            "status_url": f"http://127.0.0.1:3009/disclosure/sessions/{session_token}",
            "session_token": session_token,
        }
    )


class ValidityInfo(BaseModel):
    signed: str
    validFrom: str
    validUntil: str


class Attestation(BaseModel):
    attestation_type: str
    format: str
    attributes: dict[str, str]
    issuer_uri: str
    attestation_qualification: str
    ca: str
    validity_info: ValidityInfo


class DisclosedCredential(BaseModel):
    id: str
    attestations: list[Attestation]


class WalletDoneRequest(BaseModel):
    session_token: str
    bsn: str
    law: str
    service: str


@router.post("/attributes")
async def get_attributes(
    request: Request,
    session_token: str = Form(...),
    bsn: str = Form(...),
    law: str = Form(...),
    service: str = Form(...),
    machine_service: EngineInterface = Depends(get_machine_service),
    case_manager: CaseManagerInterface = Depends(get_case_manager),
    claim_manager: ClaimManagerInterface = Depends(get_claim_manager),
):
    """Retrieve and validate disclosed attributes from the wallet disclosure session.

    Args:
        request: The FastAPI request object
        session_token: Session token from the disclosure session
        bsn: BSN of the user
        law: Law to evaluate
        service: Service for the law
        machine_service: The machine service for law evaluation
        case_manager: The case manager for case data
        claim_manager: The claim manager for claim data

    Returns:
        TemplateResponse with application panel for HTMX targeting
    """

    # Make HTTP GET request to the verification_server
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://127.0.0.1:3010/disclosure/sessions/{session_token}/disclosed_attributes"
            )
            response.raise_for_status()

            # Parse the response
            disclosed_data = response.json()
    except httpx.HTTPError as e:
        return JSONResponse(content={"success": False, "message": f"Failed to retrieve disclosed attributes: {str(e)}"})

    # Parse into Pydantic models
    try:
        credentials = [DisclosedCredential(**cred) for cred in disclosed_data]
    except ValidationError as e:
        return JSONResponse(content={"success": False, "message": f"Invalid credential format: {str(e)}"})

    # Check that it contains exactly one object
    if len(credentials) != 1:
        return JSONResponse(
            content={"success": False, "message": f"Expected exactly 1 credential, got {len(credentials)}"}
        )

    credential = credentials[0]

    # Check that the id is "housing_attestation"
    if credential.id != "housing_attestation":
        return JSONResponse(
            content={
                "success": False,
                "message": f"Expected credential id 'housing_attestation', got '{credential.id}'",
            }
        )

    # Check that attestations has exactly one object
    if len(credential.attestations) != 1:
        return JSONResponse(
            content={"success": False, "message": f"Expected exactly 1 attestation, got {len(credential.attestations)}"}
        )

    attestation = credential.attestations[0]

    # Validate attestation fields
    expected_values = {
        "attestation_type": "com.example.housing",
        "format": "dc+sd-jwt",
        "issuer_uri": "https://housing.example.com",
        "attestation_qualification": "EAA",
        "ca": "ca.issuer.example.com",
    }

    for field, expected_value in expected_values.items():
        actual_value = getattr(attestation, field)
        if actual_value != expected_value:
            return JSONResponse(
                content={"success": False, "message": f"Expected {field} '{expected_value}', got '{actual_value}'"}
            )

    # Parse currency values and convert to cents
    parsed_attributes = {}
    currency_pattern = re.compile(r"€\s*([\d.]+),(\d{2})")

    for key, value in attestation.attributes.items():
        match = currency_pattern.match(value)
        if match:
            euros_str = match.group(1).replace(".", "")  # Remove thousand separators
            cents_str = match.group(2)
            parsed_attributes[key] = int(euros_str) * 100 + int(cents_str)
        else:
            return JSONResponse(content={"success": False, "message": f"Invalid currency format for {key}: {value}"})

    # Get law specification using machine service
    try:
        # Get rule spec from machine service
        rule_spec = machine_service.get_rule_spec(law, TODAY, service)

        # Build reverse mapping from wallet attributes to law field names
        wallet_to_field = {}
        for source in rule_spec.get("properties", {}).get("sources", []):
            wallet_attr = source.get("source_reference", {}).get("wallet_attribute")
            if wallet_attr:
                wallet_to_field[wallet_attr] = source["name"]

        # Transform parsed_attributes using the mapping
        for wallet_attr, value in parsed_attributes.items():
            field_name = wallet_to_field.get(wallet_attr)
            if field_name:
                id = claim_manager.submit_claim(service, field_name, value, "wallet", "housing corporation", law, bsn)
                claim_manager.approve_claim(id, "wallet", None)

        # Evaluate the law with the wallet attributes as overrides
        law, result, parameters = evaluate_law(
            bsn=bsn,
            law=law,
            service=service,
            machine_service=machine_service,
            approved=False,
            claim_manager=claim_manager,
        )

        # Get additional data needed for the template
        value_tree = machine_service.extract_value_tree(result.path)
        existing_case = case_manager.get_case(bsn, service, law)
        claims = claim_manager.get_claims_by_bsn(bsn, include_rejected=True)
        claim_map = {(claim.service, claim.law, claim.key): claim for claim in claims}

        # Return the application panel template
        return templates.TemplateResponse(
            "partials/tiles/components/application_panel.html",
            {
                "request": request,
                "service": service,
                "law": law,
                "rule_spec": rule_spec,
                "input": result.input,
                "result": result.output,
                "requirements_met": result.requirements_met,
                "path": value_tree,
                "bsn": bsn,
                "current_case": existing_case,
                "claim_map": claim_map,
                "missing_required": result.missing_required,
                "wallet_enabled": is_wallet_enabled(),
            },
        )
    except Exception as e:
        return JSONResponse(content={"success": False, "message": f"Error evaluating law: {str(e)}"})


@router.get("/get-data")
async def get_data(bsn: str, request: Request, service: str = None, law: str = None):
    """Get data from user's wallet for the specified BSN, service and law.

    This endpoint returns wallet data for the specified BSN, optionally filtered by service and law.
    """
    # Check if wallet feature is enabled
    if not is_wallet_enabled():
        return JSONResponse(
            status_code=403, content={"success": False, "message": "Wallet feature is currently disabled"}
        )

    # Get wallet data from our mock wallet data service
    wallet_data = get_wallet_data(bsn, service, law)

    if wallet_data:
        return JSONResponse(content={"success": True, "data": wallet_data})

    return JSONResponse(content={"success": False, "message": "No wallet data found for this BSN"})
