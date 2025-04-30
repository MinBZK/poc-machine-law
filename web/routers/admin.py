import os
import sys
from datetime import datetime

from engines.factory import MachineType
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from pydantic import BaseModel
from starlette.responses import RedirectResponse

from machine.events.case.aggregate import CaseStatus
from web.config_loader import ConfigLoader
from web.dependencies import (
    get_case_manager,
    get_claim_manager,
    get_engine_id,
    get_machine_service,
    set_engine_id,
    templates,
)
from web.engines import CaseManagerInterface, ClaimManagerInterface, EngineInterface
from web.routers.laws import evaluate_law

config_loader = ConfigLoader()


router = APIRouter(prefix="/admin", tags=["admin"])


# Define Engine model
class Engine(BaseModel):
    id: MachineType
    name: str
    description: str
    active: bool = False


def get_engines() -> list[Engine]:
    return config_loader.config.get_engines()


def group_cases_by_status(cases):
    """Group cases by their current status"""
    # Initialize with all possible statuses
    grouped = {status.value: [] for status in CaseStatus}

    for case in cases:
        grouped[case.status].append(case)

    return grouped


@router.get("/")
async def admin_redirect(request: Request, services: EngineInterface = Depends(get_machine_service)):
    """Redirect to first available service"""
    discoverable_laws = await services.get_discoverable_service_laws()
    available_services = list(discoverable_laws.keys())
    return RedirectResponse(f"/admin/{available_services[0]}")


@router.get("/reset")
async def reset(request: Request):
    return RedirectResponse("/admin/control")


@router.get("/control")
async def control(request: Request, services: EngineInterface = Depends(get_machine_service)):
    """Show a button to reset the state of the application"""

    return templates.TemplateResponse(
        "admin/control.html",
        {"request": request, "engines": get_engines(), "current_engine_id": get_engine_id()},
    )


@router.post("/set-engine")
async def post_set_engine(
    request: Request, engine_id: str = Form(...), services: EngineInterface = Depends(get_machine_service)
):
    # Validate engine exists
    engine_exists = any(engine.get("id") == engine_id for engine in get_engines())
    if not engine_exists:
        raise HTTPException(status_code=404, detail="Selected engine not found")

    set_engine_id(engine_id)

    # Redirect back to admin dashboard
    return templates.TemplateResponse(
        "/admin/partials/engines.html",
        {"request": request, "engines": get_engines(), "current_engine_id": get_engine_id()},
    )


@router.post("/reset")
async def post_reset(request: Request, services: EngineInterface = Depends(get_machine_service)):
    """Reset the state of the application"""

    # Restart the application. Note: the state of the application is stored in such a complicated way in memory that it is easier to just restart the application
    os.execl(sys.executable, sys.executable, *sys.argv)


@router.get("/{service}")
async def admin_dashboard(
    request: Request,
    service: str,
    services: EngineInterface = Depends(get_machine_service),
    case_manager: CaseManagerInterface = Depends(get_case_manager),
):
    """Main admin dashboard view"""
    discoverable_laws = await services.get_discoverable_service_laws()
    available_services = list(discoverable_laws.keys())

    # Get cases for selected service
    service_laws = discoverable_laws.get(service, [])
    service_cases = {}
    for law in service_laws:
        cases = await case_manager.get_cases_by_law(service, law)
        service_cases[law] = group_cases_by_status(cases)

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "current_service": service,
            "available_services": available_services,
            "service_laws": service_laws,
            "service_cases": service_cases,
        },
    )


@router.post("/cases/{case_id}/move")
async def move_case(
    request: Request,
    case_id: str,
    new_status: str = Form(...),
    case_manager: CaseManagerInterface = Depends(get_case_manager),
):
    """Handle case movement between status lanes"""
    print(f"Moving case {case_id} to status {new_status}")  # Debug print
    try:
        try:
            new_status_enum = CaseStatus(new_status)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")

        case = await case_manager.get_case_by_id(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        # Based on the target status, call the appropriate method
        if new_status_enum == CaseStatus.IN_REVIEW:
            # Get latest results from events
            events = case_manager.repository.events.get_domain_events(case.id)
            latest_results = {}
            for event in reversed(events):
                if hasattr(event, "claimed_result") and hasattr(event, "verified_result"):
                    latest_results = {
                        "claimed_result": event.claimed_result,
                        "verified_result": event.verified_result,
                    }
                    break

            case.select_for_manual_review(
                verifier_id="ADMIN",  # TODO: Get from auth
                reason="Manually moved to review",
                claimed_result=latest_results.get("claimed_result", {}),
                verified_result=latest_results.get("verified_result", {}),
            )
        elif new_status_enum == CaseStatus.DECIDED:
            case.decide(
                verified_result={},  # Would need the actual result
                reason="Manually decided",
                verifier_id="ADMIN",  # TODO: Get from auth
            )
        else:
            raise HTTPException(status_code=400, detail=f"Cannot move to status {new_status}")

        await case_manager.save(case)

        # Return just the updated card
        return templates.TemplateResponse(
            "admin/partials/case_card.html",
            {"request": request, "case": case, "status": new_status},
        )
    except Exception as e:
        print(f"Error moving case: {e}")  # Debug print
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cases/{case_id}/complete-review")
async def complete_review(
    request: Request,
    case_id: str,
    decision: bool = Form(...),
    reason: str = Form(...),  # Note: changed from reasoning to match form
    case_manager: CaseManagerInterface = Depends(get_case_manager),
):
    """Complete manual review of a case"""
    try:
        case_id = case_manager.complete_manual_review(
            case_id=case_id, verifier_id="ADMIN", approved=decision, reason=reason
        )

        # Get the updated case
        updated_case = await case_manager.get_case_by_id(case_id)

        # Check if request is from case detail page
        is_detail_page = request.headers.get("HX-Current-URL", "").endswith(f"/cases/{case_id}")

        if is_detail_page:
            # Create a decision event object for the template
            decision_event = {
                "event_type": "Decided",
                "timestamp": datetime.now(),
                "data": {
                    "verified_result": updated_case.verified_result,
                    "reason": reason,
                },
            }

            return templates.TemplateResponse(
                "admin/partials/event_detail.html",
                {"request": request, "event": decision_event, "is_first": True},
            )

        # Return updated card for HTMX swap if not detail page
        return templates.TemplateResponse(
            "admin/partials/case_card.html",
            {"request": request, "case": updated_case, "status": updated_case.status},
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cases/{case_id}")
async def view_case(
    request: Request,
    case_id: str,
    machine_service: EngineInterface = Depends(get_machine_service),
    case_manager: CaseManagerInterface = Depends(get_case_manager),
    claim_manager: ClaimManagerInterface = Depends(get_claim_manager),
):
    """View details of a specific case"""
    case = await case_manager.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case.events = await case_manager.get_events(case.id)
    law, result, parameters = await evaluate_law(case.bsn, case.law, case.service, machine_service)
    value_tree = machine_service.extract_value_tree(result.path)
    claims = await claim_manager.get_claims_by_bsn(case.bsn, include_rejected=True)
    claim_ids = {claim.id: claim for claim in claims}
    claim_map = {(claim.service, claim.law, claim.key): claim for claim in claims}
    return templates.TemplateResponse(
        "admin/case_detail.html",
        {
            "request": request,
            "case": case,
            "path": value_tree,
            "claim_map": claim_map,
            "claim_ids": claim_ids,
        },
    )


@router.get("/claims/{claim_id}")
async def view_claim(
    request: Request,
    claim_id: str,
    claim_manager: ClaimManagerInterface = Depends(get_claim_manager),
    case_manager: CaseManagerInterface = Depends(get_case_manager),
):
    """View details of a specific claim"""
    claim = await claim_manager.get_claim(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    # Get related case if it exists
    related_case = None
    if claim.case_id:
        related_case = await case_manager.get_case_by_id(claim.case_id)

    return templates.TemplateResponse(
        "admin/claim_detail.html", {"request": request, "claim": claim, "related_case": related_case}
    )
