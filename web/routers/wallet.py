"""API endpoints for the wallet module."""

import os
import re

import httpx
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from web.dependencies import TODAY, get_case_manager, get_claim_manager, get_engine_id, get_machine_service, templates
from web.engines import CaseManagerInterface, ClaimManagerInterface, EngineInterface
from web.feature_flags import is_wallet_enabled
from web.routers.laws import evaluate_law

# Wallet configuration
RETURN_URL = os.environ.get("WALLET_RETURN_URL", "http://127.0.0.1:8000")
REQUESTER_URL = os.environ.get("WALLET_VERIFIER_REQUESTER_URL", "http://127.0.0.1:3010")
WALLET_URL = os.environ.get("WALLET_VERIFIER_WALLET_URL", "http://127.0.0.1:3009")

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
        "return_url_template": f"{RETURN_URL}/?wallet_session_token={{session_token}}",
    }

    # Make HTTP call to disclosure service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{REQUESTER_URL}/disclosure/sessions",
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
            "status_url": f"{WALLET_URL}/disclosure/sessions/{session_token}",
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
            response = await client.get(f"{REQUESTER_URL}/disclosure/sessions/{session_token}/disclosed_attributes")
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

    # In our DCQL query we requested one copy of a single credential.
    # If the wallet did not respond with exactly that, or if the credential was expired or invalid
    # or did not contain the requested attributes, then the `verification_server` would have
    # responded with an error message instead of verified attributes.
    # Therefore, if we are here then we may assume that we have our one copy of a single credential
    # and that it contains verified, i.e. trustworthy, attributes.
    attestation = credentials[0].attestations[0]

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
                claim_manager.approve_claim(id, attestation.issuer_uri, None)

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
                "current_engine_id": get_engine_id(),
            },
        )
    except Exception as e:
        return JSONResponse(content={"success": False, "message": f"Error evaluating law: {str(e)}"})
