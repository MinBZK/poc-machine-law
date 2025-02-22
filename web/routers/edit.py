import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse

from machine.service import Services
from web.dependencies import get_services, templates

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
    services: Services = Depends(get_services),
):
    """Return the edit form HTML"""
    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError:
        parsed_value = value

    # Try to get existing claim by bsn, service, law and key
    claim_data = None
    existing_claims = services.claim_manager.get_claim_by_bsn_service_law(
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
        },
    )


@router.post("/update-value", response_class=HTMLResponse)
async def update_value(
    request: Request,
    service: str = Form(...),
    key: str = Form(...),
    new_value: str = Form(...),
    reason: str = Form(...),
    case_id: str | None = Form(None),
    law: str = Form(...),
    bsn: str = Form(...),
    evidence: UploadFile = File(None),
    claimant: str = Form(...),  # Add this
    auto_approve: bool = Form(False),  # Add this
    services: Services = Depends(get_services),
):
    """Handle the value update by creating a claim"""
    parsed_value = new_value
    try:
        # Try parsing as JSON first (handles booleans)
        if new_value.lower() in ("true", "false"):
            parsed_value = new_value.lower() == "true"
        # Try parsing as number
        elif new_value.replace(".", "", 1).isdigit():
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

    evidence_path = None
    if evidence:
        # Save evidence file and get path
        # evidence_path = await save_evidence_file(evidence)
        pass

    claim_id = services.claim_manager.submit_claim(
        service=service,
        key=key,
        new_value=parsed_value,
        reason=reason,
        claimant=claimant,
        case_id=case_id,
        evidence_path=evidence_path,
        law=law,
        bsn=bsn,
        auto_approve=auto_approve,
    )

    response = templates.TemplateResponse(
        "partials/edit_success.html",
        {"request": request, "key": key, "new_value": parsed_value, "claim_id": claim_id},
    )
    response.headers["HX-Trigger"] = "edit-dialog-closed"
    return response


@router.post("/reject-claim", response_class=HTMLResponse)
async def reject_claim(
    request: Request,
    claim_id: str = Form(...),
    reason: str = Form(...),
    services: Services = Depends(get_services),
):
    """Handle dropping a claim by rejecting it"""
    try:
        services.claim_manager.reject_claim(
            claim_id=claim_id,
            rejected_by="USER",  # You might want to get this from auth
            rejection_reason=f"Claim dropped: {reason}",
        )

        response = templates.TemplateResponse("partials/claim_dropped.html", {"request": request})
        response.headers["HX-Trigger"] = "edit-dialog-closed"
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reject-claim-form", response_class=HTMLResponse)
async def get_reject_claim_form(
    request: Request,
    claim_id: str,
):
    """Return the drop claim form HTML"""
    return templates.TemplateResponse(
        "partials/reject-claim-form.html",
        {
            "request": request,
            "claim_id": claim_id,
        },
    )


@router.post("/approve-claim", response_class=HTMLResponse)
async def approve_claim(
    request: Request,
    claim_id: str = Form(...),
    services: Services = Depends(get_services),
):
    """Handle approving a claim by verifying it with its original new_value"""
    try:
        services.claim_manager.approve_claim(
            claim_id=claim_id,
            verified_by="USER",
            verified_value=None,
        )

        response = templates.TemplateResponse("partials/claim_approved.html", {"request": request})
        response.headers["HX-Trigger"] = "edit-dialog-closed"
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
