import json
import logging
import re
from datetime import datetime

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import HTMLResponse, JSONResponse

from web.dependencies import get_case_manager, get_claim_manager, templates
from web.engines import CaseManagerInterface, ClaimManagerInterface
from web.engines.http_engine.machine_client.regel_recht_engine_api_client.errors import UnexpectedStatus

router = APIRouter(prefix="/edit", tags=["edit"])
logger = logging.getLogger(__name__)


@router.get("/edit-form", response_class=HTMLResponse)
async def get_edit_form(
    request: Request,
    case_id: str,
    service: str,
    key: str,
    law: str,
    bsn: str,
    show_approve: bool = False,
    has_details: bool = False,
    details: str = None,
    claim_manager: ClaimManagerInterface = Depends(get_claim_manager),
):
    """Return the edit form HTML"""
    # Get all 'value' query parameters (there might be multiple for arrays)
    values = request.query_params.getlist("value")

    # Parse value(s)
    if len(values) == 0:
        parsed_value = None
    elif len(values) == 1:
        # Single value - try JSON parsing
        try:
            parsed_value = json.loads(values[0])
        except json.JSONDecodeError:
            parsed_value = values[0]
    else:
        # Multiple values - parse each as JSON and combine into array
        parsed_value = []
        for v in values:
            try:
                parsed_value.append(json.loads(v))
            except json.JSONDecodeError:
                parsed_value.append(v)

    # Parse details if present
    parsed_details = None
    if has_details and details:
        try:
            parsed_details = json.loads(details)
        except json.JSONDecodeError:
            parsed_details = None

    # Try to get existing claim by bsn, service, law and key
    claim_data = None
    existing_claims = claim_manager.get_claim_by_bsn_service_law(
        bsn=bsn,
        service=service,
        law=law,
        include_rejected=True,  # Include rejected claims to show history
    )

    if existing_claims and key in existing_claims:
        claim = existing_claims[key]
        claim_data = {
            "new_value": claim.new_value,
            "reason": claim.reason,
            "evidence_path": claim.evidence_path,
            "auto_approve": claim.status == "APPROVED",
            "status": claim.status,
        }

    return templates.TemplateResponse(
        "partials/edit_form.html",
        {
            "request": request,
            "case_id": case_id,
            "service": service,
            "key": key,
            "value": parsed_value,
            "law": law,
            "bsn": bsn,
            "show_approve": show_approve,
            "claim_data": claim_data,
            "details": parsed_details,
        },
    )


@router.post("/update-value", response_class=HTMLResponse)
async def update_value(
    request: Request,
    service: str = Form(...),
    key: str = Form(...),
    new_value: str = Form(...),
    old_value: str = Form(...),
    reason: str = Form(...),
    case_id: str | None = Form(None),
    law: str = Form(...),
    bsn: str = Form(...),
    evidence: UploadFile = File(None),
    claimant: str = Form(...),
    auto_approve: bool = Form(False),
    claim_manager: ClaimManagerInterface = Depends(get_claim_manager),
):
    """Handle the value update by creating a claim"""
    logger.warn(
        f"Updating value - service: {service}, law: {law}, bsn: {bsn}, "
        f"case_id: {case_id}, reason: {reason}, claimant: {claimant}"
    )

    parsed_value = new_value
    parsed_old_value = old_value

    # Parse new value
    try:
        # Try parsing as JSON first (handles booleans)
        if new_value.lower() in ("true", "false"):
            parsed_value = new_value.lower() == "true"
        # Try parsing as JSON array or object
        elif new_value.startswith(("[", "{")):
            try:
                parsed_value = json.loads(new_value)
            except json.JSONDecodeError:
                # If JSON parsing fails, keep original string
                pass
        # Try parsing as number
        elif new_value.replace(".", "", 1).isdigit() or (
            new_value.startswith("-") and new_value[1:].replace(".", "", 1).isdigit()
        ):
            parsed_value = float(new_value) if "." in new_value else int(new_value)
        # Try parsing as date
        elif new_value and len(new_value.split("-")) == 3:
            try:
                from datetime import date

                year, month, day = map(int, new_value.split("-"))
                parsed_value = date(year, month, day).isoformat()
            except ValueError:
                # If date parsing fails, keep original string
                pass
    except (json.JSONDecodeError, ValueError):
        # If parsing fails, keep original string value
        pass

    # Parse old value using the same logic
    try:
        # Try parsing as JSON first (handles booleans)
        if old_value.lower() in ("true", "false"):
            parsed_old_value = old_value.lower() == "true"
        # Try parsing as JSON array or object
        elif old_value.startswith(("[", "{")):
            try:
                parsed_old_value = json.loads(old_value)
            except json.JSONDecodeError:
                # If JSON parsing fails, keep original string
                pass
        # Try parsing as number
        elif old_value.replace(".", "", 1).isdigit() or (
            old_value.startswith("-") and old_value[1:].replace(".", "", 1).isdigit()
        ):
            parsed_old_value = float(old_value) if "." in old_value else int(old_value)
        # Try parsing as date
        elif old_value and len(old_value.split("-")) == 3:
            try:
                from datetime import date

                year, month, day = map(int, old_value.split("-"))
                parsed_old_value = date(year, month, day).isoformat()
            except ValueError:
                # If date parsing fails, keep original string
                pass
    except (json.JSONDecodeError, ValueError):
        # If parsing fails, keep original string value
        pass

    # Note: No special handling needed for eurocent here, as the frontend already converts
    # the display value (e.g., €10.50) to the actual value in cents (1050) before submission

    evidence_path = None
    if evidence:
        # Save evidence file and get path
        # evidence_path = await save_evidence_file(evidence)
        pass

    try:
        claim_id = claim_manager.submit_claim(
            service=service,
            key=key,
            new_value=parsed_value,
            reason=reason,
            claimant=claimant,
            case_id=case_id,
            old_value=parsed_old_value,  # Now passing the old value properly
            evidence_path=evidence_path,
            law=law,
            bsn=bsn,
            auto_approve=auto_approve,
        )
    except ValueError as e:
        logger.error(f"Failed to submit claim: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    # Get details from form data if they exist
    from contextlib import suppress

    # Get the form data
    form = await request.form()
    details_json = form.get("details")
    details = None
    if details_json:
        with suppress(json.JSONDecodeError):
            details = json.loads(details_json)

    response = templates.TemplateResponse(
        "partials/edit_success.html",
        {
            "request": request,
            "key": key,
            "new_value": parsed_value,
            "claim_id": claim_id,
            "details": details,
        },
    )
    response.headers["HX-Trigger"] = "edit-dialog-closed"
    return response


@router.post("/reject-claim", response_class=HTMLResponse)
async def reject_claim(
    request: Request,
    claim_id: str = Form(...),
    reason: str = Form(...),
    claim_manager: ClaimManagerInterface = Depends(get_claim_manager),
):
    """Handle dropping a claim by rejecting it"""
    try:
        claim_manager.reject_claim(
            claim_id=claim_id,
            rejected_by="USER",  # You might want to get this from auth
            rejection_reason=f"Claim dropped: {reason}",
        )

        response = templates.TemplateResponse("partials/claim_dropped.html", {"request": request})
        response.headers["HX-Trigger"] = "edit-dialog-closed"
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reject_claim_form", response_class=HTMLResponse)
async def get_reject_claim_form(
    request: Request,
    claim_id: str,
):
    """Return the drop claim form HTML"""
    return templates.TemplateResponse(
        "partials/reject_claim_form.html",
        {
            "request": request,
            "claim_id": claim_id,
        },
    )


@router.post("/approve-claim", response_class=HTMLResponse)
async def approve_claim(
    request: Request,
    claim_id: str = Form(...),
    claim_manager: ClaimManagerInterface = Depends(get_claim_manager),
):
    """Handle approving a claim by verifying it with its original new_value"""
    try:
        claim_manager.approve_claim(
            claim_id=claim_id,
            verified_by="USER",
            verified_value=None,
        )

        response = templates.TemplateResponse("partials/claim_approved.html", {"request": request})
        response.headers["HX-Trigger"] = "edit-dialog-closed"
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/update-missing-values", response_class=HTMLResponse)
async def update_missing_values(
    request: Request,
    case_id: str = Form(None),
    service: str = Form(...),
    law: str = Form(...),
    bsn: str = Form(...),
    reason: str = Form(...),
    claimant: str = Form(...),
    claim_manager: ClaimManagerInterface = Depends(get_claim_manager),
):
    """Handle the bulk update of missing required values - multi value version"""

    # Get form data
    form_data = await request.form()
    logger.info(
        f"Updating missing values - service: {service}, law: {law}, bsn: {bsn}, "
        f"case_id: {case_id}, reason: {reason}, claimant: {claimant}"
    )

    # Extract keys, values and types as lists
    keys_list = []
    values_list = []
    types_list = []

    # Process form data with array-style naming
    key_pattern = r"keys\[(\d+)\]"
    value_pattern = r"values\[(\d+)\]"
    type_pattern = r"types\[(\d+)\]"

    key_dict = {}
    value_dict = {}
    type_dict = {}

    for key, value in form_data.items():
        key_match = re.match(key_pattern, key)
        if key_match:
            index = int(key_match.group(1))
            key_dict[index] = value
            continue

        value_match = re.match(value_pattern, key)
        if value_match:
            index = int(value_match.group(1))
            value_dict[index] = value
            continue

        type_match = re.match(type_pattern, key)
        if type_match:
            index = int(type_match.group(1))
            type_dict[index] = value
            continue

    # Sort by index
    max_index = max(set(key_dict.keys()) | set(value_dict.keys()) | set(type_dict.keys()))

    for i in range(max_index + 1):
        if i in key_dict and i in value_dict and i in type_dict:
            keys_list.append(key_dict[i])
            values_list.append(value_dict[i])
            types_list.append(type_dict[i])

    # Process each value with its proper type
    for i, (key, value, type_name) in enumerate(zip(keys_list, values_list, types_list)):
        parsed_value = value
        try:
            # Parse value based on type
            if type_name == "boolean":
                parsed_value = value.lower() == "true"
            elif type_name == "array" and (value.startswith(("[", "{"))):
                try:
                    parsed_value = json.loads(value)
                except json.JSONDecodeError:
                    # If JSON parsing fails, keep original string
                    pass
            elif type_name == "number":
                parsed_value = float(value) if "." in value else int(value)
            elif type_name == "date" and len(value.split("-")) == 3:
                try:
                    from datetime import date

                    year, month, day = map(int, value.split("-"))
                    parsed_value = date(year, month, day).isoformat()
                except ValueError:
                    pass
        except (ValueError, TypeError):
            # If parsing fails, keep as string
            pass

        # Submit each claim individually
        try:
            claim_manager.submit_claim(
                service=service,
                key=key,
                new_value=parsed_value,
                reason=f"{reason} (bulk update)",
                claimant=claimant,
                case_id=case_id,
                evidence_path=None,
                law=law,
                bsn=bsn,
                auto_approve=False,
            )
        except ValueError as e:
            logger.error(f"Failed to submit claim for key {key}: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to submit claim for {key}: {str(e)}")

    response = templates.TemplateResponse(
        "partials/edit_success.html",
        {
            "request": request,
            "key": "Benodigde gegevens",
            "new_value": "Bijgewerkt",
            "claim_id": None,
            "details": None,
        },
    )
    response.headers["HX-Trigger"] = "edit-dialog-closed, reload-page"
    return response


@router.post("/update-situation")
async def update_situation(
    request: Request,
    payload: dict = Body(...),
    case_manager: CaseManagerInterface = Depends(get_case_manager),
    claim_manager: ClaimManagerInterface = Depends(get_claim_manager),
):
    """
    Update a person's situation based on wizard input from the dashboard.
    Submits the updated situation as a new claim via the claim manager.
    """

    situation_type = payload.get("type")
    details = payload.get("details", "")
    bsn = payload.get("bsn")  # IMPROVE: get from session?

    if not all([situation_type, bsn]):
        return JSONResponse(
            {"status": "error", "message": "situation_type and bsn are required"},
            status_code=400,
        )

    # Prepare parameters for the case, using all payload fields except meta
    parameters = {k: v for k, v in payload.items() if k not in ("type", "bsn")}

    # Split the payload into multiple claims and assign them to the same case
    match situation_type:
        case "inkomen":
            service = "BELASTINGDIENST"
            law = "wet_inkomstenbelasting"
        case "woonadres":
            service = "RvIG"
            law = "wet_brp"

            # Set the correct claims
            verblijfplaats = {"type": "WOONADRES"}

            # Only set address attributes if the corresponding parameters exist
            if "adres.straat" in parameters:
                verblijfplaats["straat"] = parameters["adres.straat"]
            if "adres.huisnummer" in parameters:
                verblijfplaats["huisnummer"] = parameters["adres.huisnummer"]
            if "adres.postcode" in parameters:
                verblijfplaats["postcode"] = parameters["adres.postcode"]
            if "adres.woonplaats" in parameters:
                verblijfplaats["woonplaats"] = parameters["adres.woonplaats"]

            parameters["verblijfplaats"] = verblijfplaats
            parameters["land_verblijf"] = "NEDERLAND"

            # Build verblijfsadres only from available parameters
            address_parts = []
            if "adres.straat" in parameters and "adres.huisnummer" in parameters:
                address_parts.append(f"{parameters['adres.straat']} {parameters['adres.huisnummer']}")
            if "adres.postcode" in parameters and "adres.woonplaats" in parameters:
                address_parts.append(f"{parameters['adres.postcode']} {parameters['adres.woonplaats']}")

            if address_parts:
                parameters["verblijfsadres"] = ", ".join(address_parts)

            # Remove address fields that are no longer used (and do not correspond to claims) from parameters
            for k in ["adres.straat", "adres.huisnummer", "adres.postcode", "adres.woonplaats"]:
                parameters.pop(k, None)
        case "huurprijs":
            service = "TOESLAGEN"
            law = "wet_op_de_huurtoeslag"
        case "huishouden":
            service = "RvIG"
            law = "wet_brp"

            match payload.get("situation_household_change_type"):
                case "scheiden":
                    parameters["partner_bsn"] = None
                    parameters["partnerschap_type"] = "GEEN"

                # Show an error message for other household changes. IMPROVE: handle more household change types
                case _:
                    return JSONResponse(
                        {"status": "error", "message": "Deze flow is nog niet ondersteund."},
                        status_code=400,
                    )

            parameters.pop("situation_household_change_type", None)
        case _:
            return JSONResponse(
                {"status": "error", "message": f"unrecognized type: {situation_type}"},
                status_code=400,
            )

    # Get the effective_date from the parameters and parse it
    effective_date_str = parameters.pop("effective_date", None)
    effective_date = datetime.strptime(effective_date_str, "%Y-%m-%d").date() if effective_date_str else None

    # Create a case
    try:
        case_id = case_manager.submit_case(
            bsn=bsn,
            service=service,
            law=law,
            parameters=parameters
            | {
                "BSN": bsn
            },  # The Go engine expects the BSN to be present (with uppercase) in the case parameters, so we add it
            claimed_result=parameters,  # IMPROVE: other value?
            approved_claims_only=False,  # IMPROVE: or True?
            effective_date=effective_date,
        )
    except UnexpectedStatus as e:
        return JSONResponse(
            {
                "status": "error",
                "message": f"Server error: {e.status_code}. Response: {e.content.decode('utf-8') if e.content else 'No response content'}",
            },
            status_code=500,
        )
    except json.JSONDecodeError as e:
        return JSONResponse(
            {"status": "error", "message": f"Invalid JSON response from server: {str(e)}"},
            status_code=500,
        )
    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": f"Unexpected error: {str(e)}"},
            status_code=500,
        )

    # Add the claim(s) to the case
    for key, value in parameters.items():
        try:
            claim_manager.submit_claim(
                service=service,
                key=key,
                new_value=value,
                reason=details,
                claimant=bsn,
                law=law,
                bsn=bsn,
                case_id=case_id,
                # old_value: Any | None = None, # IMPROVE: fetch old value from existing situation or case if existing?
            )
        except ValueError as e:
            logger.error(f"Failed to submit claim for key {key}: {e}")
            return JSONResponse(
                {"status": "error", "message": f"Failed to submit claim for {key}: {str(e)}"},
                status_code=400,
            )

    return JSONResponse({"status": "ok", "message": "Situatie bijgewerkt"})
