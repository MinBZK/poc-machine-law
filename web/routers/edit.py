import json
import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from web.dependencies import get_claim_manager, templates
from web.engines import ClaimManagerInterface

router = APIRouter(prefix="/edit", tags=["edit"])


@router.get("/edit-form", response_class=HTMLResponse)
async def get_edit_form(
    request: Request,
    case_id: str,
    service: str,
    key: str,
    value: str,
    law: str,
    bsn: str,
    show_approve: bool = False,
    has_details: bool = False,
    details: str = None,
    claim_manager: ClaimManagerInterface = Depends(get_claim_manager),
):
    """Return the edit form HTML"""
    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError:
        parsed_value = value

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


@router.get("/get-profile-data")
async def get_profile_data(bsn: str, request: Request, service: str = None, law: str = None):
    """Get data from user profile by BSN - for NL Wallet simulation"""

    from web.engines.py_engine.services.profiles import get_profile_data

    # Debug information
    print(f"Retrieving profile data for BSN={bsn}, service={service}, law={law}")

    profile = get_profile_data(bsn)

    if not profile:
        print(f"Profile not found for BSN={bsn}")
        return JSONResponse(content={"success": False, "message": "Profile not found"})

    # Create a flattened dictionary of profile data with focus on required fields
    flattened_data = {}

    # Check if this is a huurtoeslag request (wet_op_de_huurtoeslag)
    if service == "TOESLAGEN" and law == "wet_op_de_huurtoeslag":
        print(f"Looking for huurtoeslag wallet data for BSN={bsn}")
        if "sources" in profile and "RvIG" in profile["sources"]:
            rvig_data = profile["sources"]["RvIG"]

            # Check if we have huurtoeslag wallet data
            if "nl_wallet" in rvig_data and "huurtoeslag" in rvig_data["nl_wallet"]:
                wallet_data = rvig_data["nl_wallet"]["huurtoeslag"]
                print(f"Found wallet data for huurtoeslag: {wallet_data}")

                # Add these directly to flattened data
                for key, value in wallet_data.items():
                    flattened_data[key] = value

                # Successfully found wallet data for this specific service
                print(f"Returning wallet data: {flattened_data}")
                return JSONResponse(content={"success": True, "profile": flattened_data})
            else:
                print(f"No wallet data found for huurtoeslag in profile {bsn}")
        else:
            print(f"No RvIG data found in profile {bsn}")

    # If we didn't find specific wallet data for the requested service/law,
    # or no service/law was specified, fall back to general profile data

    # Extract basic personal info
    if "sources" in profile and "RvIG" in profile["sources"]:
        rvig_data = profile["sources"]["RvIG"]
        if "personen" in rvig_data and len(rvig_data["personen"]) > 0:
            person = rvig_data["personen"][0]
            for key, value in person.items():
                flattened_data[key] = value

        # Extract address data
        if "verblijfplaats" in rvig_data and len(rvig_data["verblijfplaats"]) > 0:
            address = rvig_data["verblijfplaats"][0]
            for key, value in address.items():
                flattened_data[key] = value

    # Extract income data
    if "sources" in profile and "BELASTINGDIENST" in profile["sources"]:
        tax_data = profile["sources"]["BELASTINGDIENST"]

        # Extract box1 income
        if "box1" in tax_data and len(tax_data["box1"]) > 0:
            income = tax_data["box1"][0]
            for key, value in income.items():
                if key != "bsn":  # Skip BSN as it's already included
                    flattened_data[key] = value

        # Extract box3 assets
        if "box3" in tax_data and len(tax_data["box3"]) > 0:
            assets = tax_data["box3"][0]
            for key, value in assets.items():
                if key != "bsn":
                    flattened_data[key] = value

    return JSONResponse(content={"success": True, "profile": flattened_data})
