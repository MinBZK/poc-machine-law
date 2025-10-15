"""API endpoints for the wallet module."""

import re
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from web.feature_flags import is_wallet_enabled
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
                    ]
                }
            ]
        },
        "return_url_template": "http://127.0.0.1:8000/?wallet_session_token={session_token}"
    }

    # Make HTTP call to disclosure service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:3010/disclosure/sessions",
                json=disclosure_payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            # Parse the session token from the response
            disclosure_response = response.json()
            session_token = disclosure_response.get("session_token")

            if not session_token:
                raise HTTPException(
                    status_code=500,
                    detail="No session token received from disclosure service"
                )

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create disclosure session: {str(e)}"
        )

    # Return the disclosure session information
    return JSONResponse(
        content={
            "status_url": f"http://127.0.0.1:3009/disclosure/sessions/{session_token}",
            "session_token": session_token
        }
    )

class WalletDoneRequest(BaseModel):
    session_token: str

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

@router.post("/attributes")
async def get_attributes(request_body: WalletDoneRequest):
    """Retrieve and validate disclosed attributes from the wallet disclosure session.

    Args:
        request_body: Contains the session_token from the disclosure session

    Returns:
        JSONResponse with success status, and either attributes or error message
    """
    session_token = request_body.session_token

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
        return JSONResponse(content={"success": False, "message": f"Expected exactly 1 credential, got {len(credentials)}"})

    credential = credentials[0]

    # Check that the id is "housing_attestation"
    if credential.id != "housing_attestation":
        return JSONResponse(content={"success": False, "message": f"Expected credential id 'housing_attestation', got '{credential.id}'"})

    # Check that attestations has exactly one object
    if len(credential.attestations) != 1:
        return JSONResponse(content={"success": False, "message": f"Expected exactly 1 attestation, got {len(credential.attestations)}"})

    attestation = credential.attestations[0]

    # Validate attestation fields
    expected_values = {
        "attestation_type": "com.example.housing",
        "format": "dc+sd-jwt",
        "issuer_uri": "https://housing.example.com",
        "attestation_qualification": "EAA",
        "ca": "ca.issuer.example.com"
    }

    for field, expected_value in expected_values.items():
        actual_value = getattr(attestation, field)
        if actual_value != expected_value:
            return JSONResponse(content={"success": False, "message": f"Expected {field} '{expected_value}', got '{actual_value}'"})

    # Validate time validity
    try:
        valid_from = datetime.fromisoformat(attestation.validity_info.validFrom.replace("Z", "+00:00"))
        valid_until = datetime.fromisoformat(attestation.validity_info.validUntil.replace("Z", "+00:00"))
    except ValueError as e:
        return JSONResponse(content={"success": False, "message": f"Invalid datetime format: {str(e)}"})

    current_time = datetime.now(timezone.utc)

    if not (valid_from <= current_time <= valid_until):
        return JSONResponse(
            content={"success": False, "message": f"Attestation is not currently valid. Valid from {valid_from} to {valid_until}, current time is {current_time}"}
        )

    # Parse currency values and convert to cents
    parsed_attributes = {}
    currency_pattern = re.compile(r'€\s*([\d.]+),(\d{2})')

    for key, value in attestation.attributes.items():
        match = currency_pattern.match(value)
        if match:
            euros_str = match.group(1).replace(".", "")  # Remove thousand separators
            cents_str = match.group(2)
            parsed_attributes[key] = int(euros_str) * 100 + int(cents_str)
        else:
            return JSONResponse(content={"success": False, "message": f"Invalid currency format for {key}: {value}"})

    # All validations passed, return the parsed attributes
    return JSONResponse(content={"success": True, "attributes": parsed_attributes})

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
