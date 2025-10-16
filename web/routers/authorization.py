"""Authorization router for checking who can act on behalf of whom"""

from fastapi import APIRouter, Depends, Query, Request

from web.dependencies import TODAY, get_machine_service, templates
from web.engines import EngineInterface

router = APIRouter(prefix="/authorization", tags=["authorization"])


# Define the authorization laws we have implemented
AUTHORIZATION_LAWS = {
    "person": [
        {
            "service": "RvIG",
            "law": "burgerlijk_wetboek/ouderlijk_gezag",
            "name": "Ouderlijk gezag",
            "description": "Ouders vertegenwoordigen hun minderjarige kinderen",
            "legal_basis": "BW 1:245",
            "parameter": "BSN_KIND",
        },
        {
            "service": "RECHTSPRAAK",
            "law": "burgerlijk_wetboek/curatele",
            "name": "Curatele",
            "description": "Curator vertegenwoordigt persoon onder curatele",
            "legal_basis": "BW 1:378",
            "parameter": "BSN_CURANDUS",
        },
        {
            "service": "ALGEMEEN",
            "law": "burgerlijk_wetboek/volmacht",
            "name": "Volmacht",
            "description": "Gevolmachtigde handelt op basis van volmacht",
            "legal_basis": "BW 3:60",
            "parameter": "BSN_VOLMACHTGEVER",
        },
    ],
    "organization": [
        {
            "service": "KVK",
            "law": "handelsregisterwet/vertegenwoordiging",
            "name": "KVK Vertegenwoordiging",
            "description": "Vertegenwoordigingsbevoegdheid volgens handelsregister",
            "legal_basis": "Handelsregisterwet Art. 10",
            "parameter": "RSIN",
        },
        {
            "service": "ALGEMEEN",
            "law": "burgerlijk_wetboek/volmacht",
            "name": "Bedrijfsvolmacht",
            "description": "Gevolmachtigde handelt namens bedrijf",
            "legal_basis": "BW 3:60",
            "parameter": "RSIN_VOLMACHTGEVER",
        },
    ],
}


@router.get("/mijn-machtigingen")
async def my_authorizations(
    request: Request,
    bsn: str = Query("100000001", description="BSN of citizen"),
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """
    Show who is authorized to act on behalf of this citizen.

    Checks all relevant authorization laws to find who can represent this person.
    """
    profile = machine_service.get_profile_data(bsn)

    # Find all people/organizations authorized to act on behalf of this BSN
    # We need to check each potential actor against this target BSN
    authorizations = []
    all_profiles_dict = machine_service.get_all_profiles()

    # Check each potential actor
    for actor_bsn, actor_profile in all_profiles_dict.items():
        # Skip checking if the actor is the same as the target
        if actor_bsn == bsn:
            continue

        # Check each person-based authorization law
        for law_info in AUTHORIZATION_LAWS["person"]:
            try:
                # Build parameters based on law type
                parameters = {}

                if law_info["law"] == "burgerlijk_wetboek/ouderlijk_gezag":
                    parameters = {"BSN_OUDER": actor_bsn, "BSN_KIND": bsn}
                elif law_info["law"] == "burgerlijk_wetboek/curatele":
                    parameters = {"BSN_CURATOR": actor_bsn, "BSN_CURANDUS": bsn}
                elif law_info["law"] == "burgerlijk_wetboek/volmacht":
                    parameters = {
                        "BSN_GEVOLMACHTIGDE": actor_bsn,
                        "BSN_VOLMACHTGEVER": bsn,
                        "TARGET_TYPE": "PERSON",
                    }

                result = machine_service.evaluate(
                    service=law_info["service"],
                    law=law_info["law"],
                    parameters=parameters,
                    reference_date=TODAY,
                )

                # If someone is authorized, add to list
                if result.requirements_met and result.output.get("mag_vertegenwoordigen"):
                    auth_info = {
                        "actor_bsn": actor_bsn,
                        "actor_name": actor_profile.get("naam", "Onbekend"),
                        "law": law_info["name"],
                        "legal_basis": law_info["legal_basis"],
                        "description": law_info["description"],
                        "type": result.output.get("type_curatele") or result.output.get("type_volmacht") or "VOLLEDIG",
                        "scope": result.output.get("scope", []),
                        "beperkingen": result.output.get("beperkingen", []),
                    }
                    authorizations.append(auth_info)
            except Exception as e:
                # Log but don't fail - just skip this law
                # print(f"Error checking {actor_bsn} -> {bsn} via {law_info['law']}: {e}")
                continue

    return templates.TemplateResponse(
        "authorization/mijn_machtigingen.html",
        {
            "request": request,
            "bsn": bsn,
            "profile": profile,
            "authorizations": authorizations,
            "all_profiles": machine_service.get_all_profiles(),
        },
    )


@router.get("/machtigingscheck")
async def authorization_check_form(
    request: Request,
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """
    Show form to check if someone is authorized to act on behalf of another person/organization.
    """
    all_profiles = machine_service.get_all_profiles()

    return templates.TemplateResponse(
        "authorization/machtigingscheck.html",
        {
            "request": request,
            "all_profiles": all_profiles,
            "result": None,
        },
    )


@router.get("/check")
async def check_authorization(
    request: Request,
    actor_bsn: str = Query(..., description="BSN of person who wants to act"),
    target_type: str = Query("person", description="Type of target: person or organization"),
    target_id: str = Query(..., description="BSN or RSIN of target"),
    action: str = Query(None, description="Optional specific action"),
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """
    Check if actor is authorized to act on behalf of target.

    Returns the first matching authorization with legal basis.
    """
    actor_profile = machine_service.get_profile_data(actor_bsn)
    target_profile = None

    if target_type == "person":
        target_profile = machine_service.get_profile_data(target_id)

    # Check all relevant laws
    laws_to_check = AUTHORIZATION_LAWS.get(target_type, [])

    authorization_result = None
    checked_laws = []

    for law_info in laws_to_check:
        try:
            # Build parameters based on the law
            parameters = {}

            if law_info["law"] == "burgerlijk_wetboek/ouderlijk_gezag":
                parameters = {"BSN_OUDER": actor_bsn, "BSN_KIND": target_id}
            elif law_info["law"] == "burgerlijk_wetboek/curatele":
                parameters = {"BSN_CURATOR": actor_bsn, "BSN_CURANDUS": target_id}
            elif law_info["law"] == "burgerlijk_wetboek/volmacht":
                if target_type == "person":
                    parameters = {"BSN_GEVOLMACHTIGDE": actor_bsn, "BSN_VOLMACHTGEVER": target_id}
                else:
                    parameters = {"BSN_GEVOLMACHTIGDE": actor_bsn, "RSIN_VOLMACHTGEVER": target_id}
                if action:
                    parameters["ACTIE"] = action
            elif law_info["law"] == "handelsregisterwet/vertegenwoordiging":
                parameters = {"BSN_PERSOON": actor_bsn, "RSIN": target_id}

            result = machine_service.evaluate(
                service=law_info["service"],
                law=law_info["law"],
                parameters=parameters,
                reference_date=TODAY,
            )

            check_info = {
                "law": law_info["name"],
                "legal_basis": law_info["legal_basis"],
                "authorized": result.requirements_met and result.output.get("mag_vertegenwoordigen", False),
                "output": result.output,
            }

            checked_laws.append(check_info)

            # If authorized, use this as the result
            if check_info["authorized"] and not authorization_result:
                authorization_result = {
                    "authorized": True,
                    "law": law_info["name"],
                    "legal_basis": law_info["legal_basis"],
                    "description": law_info["description"],
                    "type": result.output.get("type_curatele") or result.output.get("type_volmacht") or result.output.get("bevoegdheid") or "VOLLEDIG",
                    "scope": result.output.get("scope", []),
                    "beperkingen": result.output.get("beperkingen", []),
                    "grondslag": result.output.get("vertegenwoordigings_grondslag", law_info["legal_basis"]),
                }
        except Exception as e:
            checked_laws.append({
                "law": law_info["name"],
                "legal_basis": law_info["legal_basis"],
                "authorized": False,
                "error": str(e),
            })
            continue

    # If no authorization found
    if not authorization_result:
        authorization_result = {
            "authorized": False,
            "reason": "Geen geldige machtiging gevonden",
        }

    return templates.TemplateResponse(
        "authorization/machtigingscheck.html",
        {
            "request": request,
            "all_profiles": machine_service.get_all_profiles(),
            "actor_bsn": actor_bsn,
            "actor_name": actor_profile.get("naam", "Onbekend") if actor_profile else "Onbekend",
            "target_type": target_type,
            "target_id": target_id,
            "target_name": target_profile.get("naam", target_id) if target_profile else target_id,
            "action": action,
            "result": authorization_result,
            "checked_laws": checked_laws,
        },
    )
