"""
Session router for role selection and switching

Provides endpoints for:
- Getting available roles for current user
- Selecting a role to act as
- Clearing role selection (back to self)
"""

import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from machine.authorization import AuthorizationService, Role
from web.dependencies import TODAY, get_machine_service
from web.engines import EngineInterface

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/session", tags=["session"])


class RoleSelection(BaseModel):
    """Request body for selecting a role"""

    target_type: Literal["PERSON", "ORGANIZATION"]
    target_id: str  # BSN or RSIN
    action: str | None = None  # Optional action for scope verification


@router.get("/my-roles")
async def get_my_roles(
    request: Request,
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """
    Get all roles the current user can assume

    Returns list of roles including:
    - SELF role (always present)
    - PERSON roles (via ouderlijk gezag, curatele, volmacht)
    - ORGANIZATION roles (via KVK, volmacht)
    """
    # Get actor BSN from session
    actor_bsn = request.session.get("bsn")
    if not actor_bsn:
        raise HTTPException(status_code=401, detail="Not logged in")

    # Create authorization service
    auth_service = AuthorizationService(machine_service)

    # Get available roles
    roles = auth_service.get_available_roles(actor_bsn, reference_date=TODAY)

    # Convert to dict for JSON response
    return {
        "actor_bsn": actor_bsn,
        "roles": [
            {
                "type": role.type,
                "id": role.id,
                "name": role.name,
                "legal_ground": role.legal_ground,
                "legal_basis": role.legal_basis,
                "scope": role.scope,
                "restrictions": role.restrictions,
            }
            for role in roles
        ],
    }


@router.post("/select-role")
async def select_role(
    request: Request,
    role: RoleSelection,
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """
    Select a role to act as

    Verifies authorization and stores selection in session
    """
    # Get actor BSN from session
    actor_bsn = request.session.get("bsn")
    if not actor_bsn:
        raise HTTPException(status_code=401, detail="Not logged in")

    # Special case: selecting self
    if role.target_type == "PERSON" and role.target_id == actor_bsn:
        request.session.pop("acting_as", None)
        return {
            "status": "ok",
            "message": "Acting as self",
            "acting_as": None,
        }

    # Create authorization service
    auth_service = AuthorizationService(machine_service)

    # Verify authorization
    is_authorized, legal_ground = auth_service.verify_authorization(
        actor_bsn=actor_bsn,
        target_type=role.target_type,
        target_id=role.target_id,
        action=role.action,
        reference_date=TODAY,
    )

    if not is_authorized:
        raise HTTPException(
            status_code=403,
            detail=f"Not authorized to act on behalf of {role.target_type} {role.target_id}",
        )

    # Get target name from available roles (which already has the correct names)
    available_roles = auth_service.get_available_roles(actor_bsn, reference_date=TODAY)
    target_role = next((r for r in available_roles if r.id == role.target_id), None)
    target_name = target_role.name if target_role else f"{role.target_type} {role.target_id}"

    # Store in session
    request.session["acting_as"] = {
        "type": role.target_type,
        "id": role.target_id,
        "name": target_name,
        "legal_ground": legal_ground,
        "action": role.action,
    }

    return {
        "status": "ok",
        "message": f"Now acting as {target_name}",
        "acting_as": request.session["acting_as"],
    }


@router.post("/clear-role")
async def clear_role(request: Request):
    """
    Clear role selection and return to acting as self
    """
    actor_bsn = request.session.get("bsn")
    if not actor_bsn:
        raise HTTPException(status_code=401, detail="Not logged in")

    request.session.pop("acting_as", None)

    return {
        "status": "ok",
        "message": "Now acting as self",
        "acting_as": None,
    }


@router.get("/current-role")
async def get_current_role(
    request: Request,
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """
    Get the currently selected role
    """
    actor_bsn = request.session.get("bsn")
    if not actor_bsn:
        raise HTTPException(status_code=401, detail="Not logged in")

    acting_as = request.session.get("acting_as")

    if acting_as:
        return {
            "actor_bsn": actor_bsn,
            "acting_as": acting_as,
        }
    else:
        # Acting as self
        profile = machine_service.get_profile_data(actor_bsn)
        return {
            "actor_bsn": actor_bsn,
            "acting_as": {
                "type": "SELF",
                "id": actor_bsn,
                "name": profile.get("naam", f"BSN {actor_bsn}") if profile else f"BSN {actor_bsn}",
                "legal_ground": "Zelf",
            },
        }
