import json

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
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
):
    """Return the edit form HTML"""
    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError:
        parsed_value = value

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
        claimant=None,
        case_id=case_id,
        evidence_path=evidence_path,
        law=law,
        bsn=bsn,
    )

    response = templates.TemplateResponse(
        "partials/edit_success.html",
        {"request": request, "key": key, "new_value": parsed_value, "claim_id": claim_id},
    )
    response.headers["HX-Trigger"] = "edit-dialog-closed"
    return response
