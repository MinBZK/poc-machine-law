"""Delegation router for handling act-on-behalf-of scenarios.

This router provides endpoints for:
- Viewing available delegations for a user
- Switching between delegation contexts
- Resetting to the user's own context
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from web.dependencies import get_machine_service
from web.engines import EngineInterface
from web.feature_flags import is_delegation_enabled

router = APIRouter(prefix="/delegation", tags=["delegation"])

# Session key for storing delegation context
DELEGATION_SESSION_KEY = "delegation_context"


def get_delegation_manager(machine_service: EngineInterface = Depends(get_machine_service)):
    """Get the DelegationManager from the machine service."""
    from machine.delegation.manager import DelegationManager

    # Get the services from the machine service
    services = machine_service.get_services()
    return DelegationManager(services)


def get_current_delegation_context(request: Request):
    """Get the current delegation context from the session."""
    from machine.delegation.models import DelegationContext

    session_data = request.session.get(DELEGATION_SESSION_KEY)
    if session_data:
        return DelegationContext.from_dict(session_data)
    return None


@router.post("/switch")
async def switch_delegation(
    request: Request,
    bsn: str = Form(...),
    subject_id: str = Form(...),
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """Switch to acting on behalf of another entity."""
    if not is_delegation_enabled():
        return RedirectResponse(url=f"/?bsn={bsn}", status_code=303)

    delegation_manager = get_delegation_manager(machine_service)
    context = delegation_manager.get_delegation_context(bsn, subject_id)

    if context:
        # Store the delegation context in the session
        request.session[DELEGATION_SESSION_KEY] = context.to_dict()

    return RedirectResponse(url=f"/?bsn={bsn}", status_code=303)


@router.post("/reset")
async def reset_delegation(request: Request, bsn: str = Form(...)):
    """Reset to the user's own context (stop acting on behalf of another)."""
    # Clear the delegation context from the session
    if DELEGATION_SESSION_KEY in request.session:
        del request.session[DELEGATION_SESSION_KEY]

    return RedirectResponse(url=f"/?bsn={bsn}", status_code=303)


@router.get("/api/current")
async def get_current_context(request: Request, bsn: str):
    """API endpoint to get the current delegation context as JSON."""
    context = get_current_delegation_context(request)
    if context:
        return {
            "active": True,
            "actor_bsn": context.actor_bsn,
            "subject_id": context.subject_id,
            "subject_type": context.subject_type,
            "subject_name": context.subject_name,
            "delegation_type": context.delegation_type,
            "permissions": context.permissions,
        }
    return {"active": False, "actor_bsn": bsn}


@router.get("/api/list")
async def list_delegations(
    bsn: str,
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """API endpoint to list all delegations for a user as JSON."""
    if not is_delegation_enabled():
        return {"delegations": [], "enabled": False}

    delegation_manager = get_delegation_manager(machine_service)
    delegations = delegation_manager.get_delegations_for_user(bsn)

    return {
        "enabled": True,
        "delegations": [
            {
                "subject_id": d.subject_id,
                "subject_type": d.subject_type,
                "subject_name": d.subject_name,
                "delegation_type": d.delegation_type,
                "permissions": d.permissions,
                "valid_from": d.valid_from.isoformat(),
                "valid_until": d.valid_until.isoformat() if d.valid_until else None,
            }
            for d in delegations
        ],
    }
