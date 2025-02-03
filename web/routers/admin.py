# web/routers/admin.py
from typing import Dict, List

from fastapi import APIRouter, Form
from starlette.responses import RedirectResponse

from claims.aggregate import ClaimStatus, Claim
from machine.service import Services

router = APIRouter(prefix="/admin", tags=["admin"])


def group_claims_by_status(claims):
    from claims.aggregate import ClaimStatus, get_status_value

    # Initialize with all possible statuses
    grouped = {status.value: [] for status in ClaimStatus}

    for claim in claims:
        # Use the helper function to get status value consistently
        status_value = get_status_value(claim.status)
        grouped[status_value].append(claim)

    return grouped


# web/routers/admin.py
from fastapi import APIRouter, Request, Depends, HTTPException
from web.dependencies import get_services, templates
from claims.aggregate import ClaimStatus

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/")
async def admin_redirect(request: Request, services: Services = Depends(get_services)
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

    # Get claims for selected service
    service_laws = discoverable_laws.get(service, [])
    service_claims = {}
    for law in service_laws:
        claims = services.manager.get_claims_by_law(law, service)
        print(f"Found {len(claims)} claims for {service}/{law}")  # Debug print
        service_claims[law] = group_claims_by_status(claims)

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "current_service": service,
            "available_services": available_services,
            "service_laws": service_laws,
            "service_claims": service_claims,
        }
    )


@router.post("/claims/{claim_id}/move")
async def move_claim(
        request: Request,
        claim_id: str,
        new_status: str = Form(...),
        services: Services = Depends(get_services)
):
    """Handle claim movement between status lanes"""
    print(f"Moving claim {claim_id} to status {new_status}")  # Debug print
    try:

        try:
            new_status_enum = ClaimStatus(new_status)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")

        # Use the move_claim method from ClaimsManager
        try:
            claim = services.manager.move_claim(claim_id, new_status_enum)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Return just the updated card
        return templates.TemplateResponse(
            "admin/partials/claim_card.html",
            {
                "request": request,
                "claim": claim,
                "status": new_status
            }
        )
    except Exception as e:
        print(f"Error moving claim: {e}")  # Debug print
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/lanes/{service}/{law}/{status}")
async def get_lane_claims(
        request: Request,
        service: str,
        law: str,
        status: str,
        services: Services = Depends(get_services)
):
    """Get claims for a specific lane"""
    try:
        storage_law = f"{law.lower()}wet" if law == "ZORGTOESLAG" else law.lower()
        claims = services.manager.get_claims_by_law(storage_law, service)
        grouped_claims = group_claims_by_status(claims)
        lane_claims = grouped_claims.get(status, [])

        return templates.TemplateResponse(
            "admin/partials/lane_content.html",
            {
                "request": request,
                "claims": lane_claims,
                "status": status,
                "service": service,
                "law": law
            }
        )
    except Exception as e:
        print(f"Error getting lane claims: {e}")  # Debug print
        raise HTTPException(status_code=400, detail=str(e))


import json
from datetime import datetime


@router.get("/claims/{claim_id}")
async def view_claim(
        request: Request,
        claim_id: str,
        services: Services = Depends(get_services)
):
    """View details of a specific claim"""
    claim = services.manager.get_claim_by_id(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    # Get events for the claim
    notification_log = services.manager.notification_log
    events = []

    # Get notifications in batches of 10 (the section size limit)
    start = 1
    while True:
        try:
            notifications = notification_log.select(start=start, limit=10)
            if not notifications:
                break

            for notification in notifications:
                if notification.originator_id == claim.id:
                    # Decode the state from bytes to JSON
                    state_data = json.loads(notification.state.decode('utf-8'))

                    # Extract timestamp from state if available
                    timestamp = state_data.get('timestamp', {}).get('_data_', None)
                    if timestamp:
                        timestamp = datetime.fromisoformat(timestamp)

                    events.append({
                        'timestamp': timestamp or str(notification.originator_version),
                        'event_type': notification.topic.split('.')[-1],  # Get just the event name
                        'data': {k: v for k, v in state_data.items()
                                 if k not in ['timestamp', 'originator_topic']}  # Filter out metadata
                    })

            start += 10
        except ValueError:
            # We've reached the end of the notifications
            break

    # Sort events by timestamp
    events.sort(key=lambda x: str(x['timestamp']))
    claim.events = events

    return templates.TemplateResponse(
        "admin/claim_detail.html",
        {
            "request": request,
            "claim": claim
        }
    )
