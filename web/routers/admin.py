from fastapi import APIRouter, Request, Depends, HTTPException, Form
from starlette.responses import RedirectResponse
import json
from datetime import datetime

from machine.events.aggregate import CaseStatus
from machine.service import Services
from web.dependencies import get_services, templates

router = APIRouter(prefix="/admin", tags=["admin"])


def group_cases_by_status(cases):
    """Group cases by their current status"""
    # Initialize with all possible statuses
    grouped = {status.value: [] for status in CaseStatus}

    for case in cases:
        grouped[case.status].append(case)

    return grouped


@router.get("/")
async def admin_redirect(
        request: Request,
        services: Services = Depends(get_services)
):
    """Redirect to first available service"""
    discoverable_laws = services.get_discoverable_service_laws()
    available_services = list(discoverable_laws.keys())
    return RedirectResponse(f"/admin/{available_services[0]}")


@router.get("/{service}")
async def admin_dashboard(
        request: Request,
        service: str,
        services: Services = Depends(get_services)
):
    """Main admin dashboard view"""
    discoverable_laws = services.get_discoverable_service_laws()
    available_services = list(discoverable_laws.keys())

    # Get cases for selected service
    service_laws = discoverable_laws.get(service, [])
    service_cases = {}
    for law in service_laws:
        cases = services.manager.get_cases_by_law(law, service)
        service_cases[law] = group_cases_by_status(cases)

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "current_service": service,
            "available_services": available_services,
            "service_laws": service_laws,
            "service_cases": service_cases,
        }
    )


@router.post("/cases/{case_id}/move")
async def move_case(
        request: Request,
        case_id: str,
        new_status: str = Form(...),
        services: Services = Depends(get_services)
):
    """Handle case movement between status lanes"""
    print(f"Moving case {case_id} to status {new_status}")  # Debug print
    try:
        try:
            new_status_enum = CaseStatus(new_status)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")

        case = services.manager.get_case_by_id(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        # Based on the target status, call the appropriate method
        if new_status_enum == CaseStatus.IN_REVIEW:
            # Get latest results from events
            events = services.manager.repository.events.get_domain_events(case.id)
            latest_results = {}
            for event in reversed(events):
                if hasattr(event, 'claimed_result') and hasattr(event, 'verified_result'):
                    latest_results = {
                        'claimed_result': event.claimed_result,
                        'verified_result': event.verified_result
                    }
                    break

            case.add_to_manual_review(
                verifier_id="ADMIN",  # TODO: Get from auth
                reason="Manually moved to review",
                claimed_result=latest_results.get('claimed_result', {}),
                verified_result=latest_results.get('verified_result', {})
            )
        elif new_status_enum == CaseStatus.DECIDED:
            case.add_manual_decision(
                verified_result={},  # Would need the actual result
                reason="Manually decided",
                verifier_id="ADMIN"  # TODO: Get from auth
            )
        else:
            raise HTTPException(status_code=400, detail=f"Cannot move to status {new_status}")

        services.manager.save(case)

        # Return just the updated card
        return templates.TemplateResponse(
            "admin/partials/case_card.html",
            {
                "request": request,
                "case": case,
                "status": new_status
            }
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
        services: Services = Depends(get_services)
):
    """Complete manual review of a case"""
    try:
        case_id = services.manager.complete_manual_review(
            case_id=case_id,
            verifier_id="ADMIN",
            approved=decision,
            reason=reason
        )

        # Get the updated case
        updated_case = services.manager.get_case_by_id(case_id)

        # Check if request is from case detail page
        is_detail_page = request.headers.get('HX-Current-URL', '').endswith(f'/cases/{case_id}')

        if is_detail_page:
            # Create a decision event object for the template
            decision_event = {
                'event_type': 'Decided',
                'timestamp': datetime.now(),
                'data': {
                    'verified_result': updated_case.verified_result,
                    'reason': reason
                }
            }

            return templates.TemplateResponse(
                "admin/partials/event_detail.html",
                {
                    "request": request,
                    "event": decision_event,
                    "is_first": True
                }
            )

        # Return updated card for HTMX swap if not detail page
        return templates.TemplateResponse(
            "admin/partials/case_card.html",
            {
                "request": request,
                "case": updated_case,
                "status": updated_case.status
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cases/{case_id}")
async def view_case(
        request: Request,
        case_id: str,
        services: Services = Depends(get_services)
):
    """View details of a specific case"""
    case = services.manager.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Get events for the case
    notification_log = services.manager.notification_log
    events = []

    # Get notifications in batches of 10
    start = 1
    while True:
        try:
            notifications = notification_log.select(start=start, limit=10)
            if not notifications:
                break

            for notification in notifications:
                if notification.originator_id == case.id:
                    # Decode the state from bytes to JSON
                    state_data = json.loads(notification.state.decode('utf-8'))

                    # Extract timestamp if available
                    timestamp = state_data.get('timestamp', {}).get('_data_', None)
                    if timestamp:
                        timestamp = datetime.fromisoformat(timestamp)

                    events.append({
                        'timestamp': timestamp or str(notification.originator_version),
                        'event_type': notification.topic.split('.')[-1],
                        'data': {k: v for k, v in state_data.items()
                                 if k not in ['timestamp', 'originator_topic']}
                    })

            start += 10
        except ValueError:
            break

    # Sort events by timestamp
    events.sort(key=lambda x: str(x['timestamp']))
    case.events = events

    return templates.TemplateResponse(
        "admin/case_detail.html",
        {
            "request": request,
            "case": case
        }
    )
