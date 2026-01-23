import os
from datetime import datetime
from uuid import UUID

from eventsourcing.application import AggregateNotFoundError
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from starlette.responses import RedirectResponse

from explain.llm_factory import LLMFactory
from machine.utils import RuleResolver
from web.config_loader import ConfigLoader
from web.dependencies import (
    get_case_manager,
    get_claim_manager,
    get_engine_id,
    get_machine_service,
    is_demo_mode,
    set_engine_id,
    templates,
)
from web.engines import CaseManagerInterface, ClaimManagerInterface, EngineInterface
from web.engines.http_engine.machine_client.regel_recht_engine_api_client.errors import UnexpectedStatus
from web.engines.models import CaseStatus
from web.feature_flags import FeatureFlags
from web.routers.laws import evaluate_law

config_loader = ConfigLoader()
llm_factory = LLMFactory()
rule_resolver = RuleResolver()


def get_person_name(bsn: str, services: EngineInterface) -> str:
    """Get person name from BSN, fallback to BSN if name not found"""
    try:
        profile_data = services.get_profile_data(bsn)
        if profile_data and "name" in profile_data:
            return profile_data["name"]
    except UnexpectedStatus as e:
        # Log the detailed error but still fallback to BSN
        error_message = e.content.decode("utf-8") if e.content else "No response content"
        print(f"Error getting profile for BSN {bsn}: {error_message}")
    except Exception:
        pass
    return bsn  # Fallback to BSN if name not found


router = APIRouter(prefix="/admin", tags=["admin"])


def get_llm_providers(request: Request) -> tuple[list[dict], str]:
    """Get all available LLM providers with their status and the current provider

    Args:
        request: Request object for checking session keys

    Returns:
        Tuple containing:
        - List of provider dictionaries with name, model_id, and configuration status
        - Current provider name
    """
    providers = []
    # Get the current provider name
    current_provider = llm_factory.get_provider(request)

    # Get available providers
    available_providers = llm_factory.get_available_providers()

    for provider_name in available_providers:
        # Get the service for this provider
        service = llm_factory.get_service(provider_name)

        # Check explicitly if we have a session key first
        has_session_key = request and service.SESSION_KEY in request.session

        # Then get the API key (which might be from session or env var)
        api_key = service.get_api_key(request)

        # Only mark as using session key if we actually have one in the session
        uses_session_key = has_session_key

        # Format key for display (only last 8 chars)
        masked_key = None
        if api_key and len(api_key) > 8:
            masked_key = "•••••••" + api_key[-8:]

        provider_info = {
            "name": provider_name,
            "model_id": service.model_id,
            "is_configured": llm_factory.is_provider_configured(provider_name, request),
            "masked_key": masked_key,
            "uses_session_key": uses_session_key,
        }
        providers.append(provider_info)

    return providers, current_provider


def group_cases_by_status(cases):
    """Group cases by their current status"""
    # Initialize with all possible statuses
    grouped = {status.value: [] for status in CaseStatus}

    for case in cases:
        grouped[case.status.value].append(case)

    return grouped


@router.get("/")
async def admin_redirect(request: Request, services: EngineInterface = Depends(get_machine_service)):
    """Redirect to first available service"""
    discoverable_laws = services.get_discoverable_service_laws("CITIZEN") | services.get_discoverable_service_laws(
        "BUSINESS"
    )
    available_services = list(discoverable_laws.keys())
    return RedirectResponse(f"/admin/{available_services[0]}")


@router.get("/reset")
async def reset(request: Request):
    return RedirectResponse("/admin/control")


@router.get("/control")
async def control(request: Request, services: EngineInterface = Depends(get_machine_service)):
    """Show a button to reset the state of the application"""
    providers, current_provider = get_llm_providers(request)
    feature_flags = FeatureFlags.get_all()

    # Get all discoverable laws for each type (without feature flag filtering for admin UI)
    citizen_laws = services.get_discoverable_service_laws("CITIZEN", filter_disabled=False)
    business_laws = services.get_discoverable_service_laws("BUSINESS", filter_disabled=False)
    delegation_laws = services.get_discoverable_service_laws("DELEGATION_PROVIDER", filter_disabled=False)

    # Get the feature flags for each law type
    law_flags = {
        "citizen": FeatureFlags.get_law_flags(citizen_laws),
        "business": FeatureFlags.get_law_flags(business_laws),
        "delegation": FeatureFlags.get_law_flags(delegation_laws),
    }

    return templates.TemplateResponse(
        "admin/control.html",
        {
            "request": request,
            "engines": config_loader.get_engines(),
            "current_engine_id": get_engine_id(),
            "providers": providers,
            "current_provider": current_provider,
            "feature_flags": feature_flags,
            "law_flags": law_flags,
            "demo_mode": is_demo_mode(request),
        },
    )


@router.post("/set-engine")
async def post_set_engine(
    request: Request, engine_id: str = Form(...), services: EngineInterface = Depends(get_machine_service)
):
    # Validate engine exists
    engine_exists = any(engine.id == engine_id for engine in config_loader.get_engines())
    if not engine_exists:
        raise HTTPException(status_code=404, detail="Selected engine not found")

    set_engine_id(engine_id)

    # Redirect back to admin dashboard
    return templates.TemplateResponse(
        "/admin/partials/engines.html",
        {"request": request, "engines": config_loader.get_engines(), "current_engine_id": get_engine_id()},
    )


@router.post("/set-llm-provider")
async def post_set_llm_provider(request: Request, provider_name: str = Form(...)):
    """Set the LLM provider to use for explanations"""

    # Validate provider exists
    available_providers = llm_factory.get_available_providers()
    if provider_name not in available_providers:
        raise HTTPException(status_code=404, detail="Selected LLM provider not found")

    # Set environment variable to change the provider
    os.environ["LLM_PROVIDER"] = provider_name

    # Get updated providers info for the template
    providers, current_provider = get_llm_providers(request)

    # Return the updated LLM providers partial template
    return templates.TemplateResponse(
        "/admin/partials/llm_providers.html",
        {"request": request, "providers": providers, "current_provider": current_provider},
    )


@router.post("/set-api-key")
async def post_set_api_key(request: Request, provider_name: str = Form(...), api_key: str = Form(...)):
    """Set the API key for a provider in the browser session"""
    # Validate provider exists
    available_providers = llm_factory.get_available_providers()
    if provider_name not in available_providers:
        raise HTTPException(status_code=404, detail="Selected LLM provider not found")

    # Try to set the API key in the session via factory
    success = llm_factory.set_session_key(request, provider_name, api_key)

    if not success:
        raise HTTPException(status_code=400, detail="Invalid API key")

    # Get updated providers info for the template
    providers, current_provider = get_llm_providers(request)

    # Return the updated LLM providers partial template
    return templates.TemplateResponse(
        "/admin/partials/llm_providers.html",
        {"request": request, "providers": providers, "current_provider": current_provider},
    )


@router.post("/clear-api-key")
async def post_clear_api_key(request: Request, provider_name: str = Form(...)):
    """Clear the API key for a provider from the browser session"""
    # Validate provider exists
    available_providers = llm_factory.get_available_providers()
    if provider_name not in available_providers:
        raise HTTPException(status_code=404, detail="Selected LLM provider not found")

    # Clear the session key via the factory
    llm_factory.clear_session_key(request, provider_name)

    # Get updated providers info for the template
    providers, current_provider = get_llm_providers(request)

    # Return the updated LLM providers partial template
    return templates.TemplateResponse(
        "/admin/partials/llm_providers.html",
        {"request": request, "providers": providers, "current_provider": current_provider},
    )


@router.post("/set-feature-flag")
async def post_set_feature_flag(
    request: Request,
    flag_name: str = Form(...),
    value: str = Form(...),
    source: str = Form(default="admin"),
    open_section: str = Form(default="citizen"),
    services: EngineInterface = Depends(get_machine_service),
):
    """Set the value of a feature flag and return updated partial"""
    try:
        # Convert string value to boolean
        bool_value = value.lower() in ("1", "true", "yes", "y")

        # Set the feature flag
        FeatureFlags.set(flag_name, bool_value)

        # Check if it's a law feature flag
        if flag_name.startswith(FeatureFlags.LAW_PREFIX):
            # Get all discoverable laws for each type (without feature flag filtering for admin UI)
            citizen_laws = services.get_discoverable_service_laws("CITIZEN", filter_disabled=False)
            business_laws = services.get_discoverable_service_laws("BUSINESS", filter_disabled=False)
            delegation_laws = services.get_discoverable_service_laws("DELEGATION_PROVIDER", filter_disabled=False)

            # Get the feature flags for each law type
            law_flags = {
                "citizen": FeatureFlags.get_law_flags(citizen_laws),
                "business": FeatureFlags.get_law_flags(business_laws),
                "delegation": FeatureFlags.get_law_flags(delegation_laws),
            }

            # Return only the law feature flags partial
            return templates.TemplateResponse(
                "/admin/partials/law_feature_flags.html",
                {"request": request, "law_flags": law_flags, "open_section": open_section},
            )
        elif source == "demo":
            # Return demo-specific partial for feature flags
            feature_flags = FeatureFlags.get_all()
            return templates.TemplateResponse(
                "demo/partials/feature_flags.html", {"request": request, "feature_flags": feature_flags}
            )
        else:
            # Regular feature flag from admin
            feature_flags = FeatureFlags.get_all()

            # Return only the feature flags partial
            return templates.TemplateResponse(
                "/admin/partials/feature_flags.html", {"request": request, "feature_flags": feature_flags}
            )
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Error setting feature flag: {str(e)}")


@router.post("/reset")
async def post_reset(request: Request, services: EngineInterface = Depends(get_machine_service)):
    """Reset the state of the application"""

    services.reset()


@router.get("/{service}")
async def admin_dashboard(
    request: Request,
    service: str,
    services: EngineInterface = Depends(get_machine_service),
    case_manager: CaseManagerInterface = Depends(get_case_manager),
):
    """Main admin dashboard view"""
    all_laws = rule_resolver.get_service_laws()
    available_services = list(all_laws.keys())

    # Get cases for selected service
    service_laws = all_laws.get(service, [])
    service_cases = {}
    for law in service_laws:
        cases = case_manager.get_cases_by_law(service, law)
        # Add person names to cases
        for case in cases:
            case.person_name = get_person_name(case.bsn, services)
        service_cases[law] = group_cases_by_status(cases)

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "current_service": service,
            "available_services": available_services,
            "service_laws": service_laws,
            "service_cases": service_cases,
            "demo_mode": is_demo_mode(request),
        },
    )


@router.post("/cases/{case_id}/move")
async def move_case(
    request: Request,
    case_id: str,
    new_status: str = Form(...),
    case_manager: CaseManagerInterface = Depends(get_case_manager),
    services: EngineInterface = Depends(get_machine_service),
):
    """Handle case movement between status lanes"""
    print(f"Moving case {case_id} to status {new_status}")  # Debug print
    try:
        try:
            new_status_enum = CaseStatus(new_status)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")

        try:
            case = case_manager.get_case_by_id(case_id)
        except AggregateNotFoundError:
            raise HTTPException(status_code=404, detail="Case not found")
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

        case_manager.save(case)

        # Add person name to case
        case.person_name = get_person_name(case.bsn, services)

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
    case_id: UUID,
    decision: bool = Form(...),
    reason: str = Form(...),  # Note: changed from reasoning to match form
    case_manager: CaseManagerInterface = Depends(get_case_manager),
    services: EngineInterface = Depends(get_machine_service),
):
    """Complete manual review of a case"""

    # Provide a fallback reason if none is provided
    if not reason:
        reason = "(No reason provided)"

    try:
        case_manager.complete_manual_review(case_id=case_id, verifier_id="ADMIN", approved=decision, reason=reason)

        # Get the updated case
        updated_case = case_manager.get_case_by_id(case_id)

        # Add person name to case
        updated_case.person_name = get_person_name(updated_case.bsn, services)

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
    try:
        case = case_manager.get_case_by_id(case_id)
    except AggregateNotFoundError:
        raise HTTPException(status_code=404, detail="Case not found")
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case.events = case_manager.get_events(case.id)
    law, result, parameters = evaluate_law(case.bsn, case.law, case.service, machine_service)
    value_tree = machine_service.extract_value_tree(result.path)
    claims = claim_manager.get_claims_by_bsn(case.bsn, include_rejected=True)
    claim_ids = {claim.id: claim for claim in claims}
    claim_map = {(claim.service, claim.law, claim.key): claim for claim in claims}
    person_name = get_person_name(case.bsn, machine_service)
    return templates.TemplateResponse(
        "admin/case_detail.html",
        {
            "request": request,
            "case": case,
            "path": value_tree,
            "claim_map": claim_map,
            "claim_ids": claim_ids,
            "person_name": person_name,
            "current_engine_id": get_engine_id(),
            "demo_mode": is_demo_mode(request),
        },
    )
