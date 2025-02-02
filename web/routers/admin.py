# web/routers/admin.py
from typing import Dict, List

from fastapi import APIRouter, Form
from starlette.responses import RedirectResponse

from claims.aggregate import ClaimStatus, Claim
from machine.service import Services

router = APIRouter(prefix="/admin", tags=["admin"])


def group_claims_by_status(claims: List[Claim]) -> Dict[ClaimStatus, List[Claim]]:
    """
    Groups claims by their status.
    Returns a dict where each key is a ClaimStatus and value is a list of claims.
    """
    grouped = {status.value: [] for status in ClaimStatus}  # Initialize empty list for each status
    for claim in claims:
        grouped[claim.status.value].append(claim)
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
        new_status: str = Form(...),  # This explicitly expects form data
        services: Services = Depends(get_services)
):
    """Handle claim movement between status lanes"""
    print(f"Moving claim {claim_id} to status {new_status}")  # Debug print
    try:
        claim = services.manager.get_claim_by_id(claim_id)

        claim.status = ClaimStatus[new_status]
        services.manager.save(claim)

        # Return the updated card
        return templates.TemplateResponse(
            "admin/partials/claim_card.html",
            {
                "request": request,
                "claim": claim,
                "status": new_status  # Include the status for the hidden input
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

    return templates.TemplateResponse(
        "admin/claim_detail.html",
        {
            "request": request,
            "claim": claim
        }
    )
