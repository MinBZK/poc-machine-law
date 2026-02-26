import json
import logging
import os
from typing import Any
from urllib.parse import unquote

import pandas as pd
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse
from jinja2 import TemplateNotFound

from explain.llm_factory import llm_factory
from web.demo_profiles import DemoProfiles
from web.dependencies import TODAY, get_case_manager, get_claim_manager, get_engine_id, get_machine_service, templates
from web.engines import CaseManagerInterface, ClaimManagerInterface, EngineInterface, RuleResult
from web.feature_flags import is_wallet_enabled

router = APIRouter(prefix="/laws", tags=["laws"])

logger = logging.getLogger(__name__)

# In-memory profile data overrides (keyed by (service, table, kvk))
_profile_data_overrides: dict[tuple[str, str, str], list[dict]] = {}


def _apply_profile_overrides(profile_data: dict, service: str, kvk: str) -> dict:
    """Merge any in-memory profile data overrides into the profile data dict."""
    if not profile_data or not kvk:
        return profile_data
    for (svc, table, k), rows in _profile_data_overrides.items():
        if svc == service and k == kvk and table in profile_data:
            profile_data[table] = rows
    return profile_data


def get_tile_template(service: str, law: str) -> str:
    """
    Get the appropriate tile template for the service and law.
    Falls back to a generic template if no specific template exists.
    """
    specific_template = f"partials/tiles/law/{law}/{service}.html"

    try:
        templates.get_template(specific_template)
        return specific_template
    except TemplateNotFound:
        return "partials/tiles/fallback_tile.html"


def evaluate_law(
    bsn: str,
    law: str,
    service: str,
    machine_service: EngineInterface,
    approved: bool = True,
    claim_manager: ClaimManagerInterface | None = None,
    effective_date: str | None = None,
    kvk_nummer: str | None = None,
) -> tuple[str, RuleResult, dict[str, Any]]:
    """Evaluate a law for a given BSN or KVK_NUMMER"""

    logger.warn(f"evalute law {service} {law} for {bsn} (kvk={kvk_nummer})")

    # Determine parameters based on law type
    # Business laws may need KVK_NUMMER as the primary parameter
    parameters = {"BSN": bsn}
    if kvk_nummer:
        parameters["KVK_NUMMER"] = kvk_nummer
    overwrite_input = None

    # If not approved (i.e., showing pending changes), get claims and apply them as overwrites
    if not approved and claim_manager:
        claims = claim_manager.get_claims_by_bsn(bsn, include_rejected=False)
        # Filter claims for this service and law that are pending or approved
        relevant_claims = [
            claim
            for claim in claims
            if claim.service == service and claim.law == law and claim.status in ["PENDING", "APPROVED"]
        ]

        # Build overwrite_input from claims, but route parameter claims to parameters dict
        if relevant_claims:
            overwrite_input = {}
            # Get declared parameter names to distinguish parameter claims from source claims
            rule_spec = machine_service.get_rule_spec(law, TODAY, service)
            param_names = {p["name"] for p in rule_spec.get("properties", {}).get("parameters", [])}

            for claim in relevant_claims:
                if claim.key in param_names:
                    # User-input parameter (e.g., ACTIVITEITSDATUM) — add to parameters dict
                    parameters[claim.key] = claim.new_value
                else:
                    overwrite_input[claim.key] = claim.new_value

            if not overwrite_input:
                overwrite_input = None

    # Execute the law using EngineInterface
    result = machine_service.evaluate(
        service=service,
        law=law,
        parameters=parameters,
        reference_date=TODAY,
        effective_date=effective_date,
        approved=approved,
        overwrite_input=overwrite_input,
    )

    return law, result, parameters


@router.get("/list")
async def list_laws():
    """List all available law files"""

    laws_dir = os.path.join(os.path.dirname(__file__), "../../laws")
    law_files = []
    for root, _, files in os.walk(laws_dir):
        for file in files:
            if file.endswith(".yaml"):  # Return only YAML files
                law_files.append(os.path.relpath(os.path.join(root, file), laws_dir))

    return JSONResponse(content=law_files)


@router.get("/demo-selection")
async def demo_selection():
    """Return the graph_selected_laws UUIDs for the active demo profile.

    An empty array means 'select all laws'.
    """
    profile = DemoProfiles.get_active_profile()
    return JSONResponse(content=profile.get("graph_selected_laws", []))


@router.get("/execute")
async def execute_law(
    request: Request,
    service: str,
    law: str,
    bsn: str,
    date: str = None,
    kvk: str = None,
    can_submit_claims: bool = True,
    case_manager: CaseManagerInterface = Depends(get_case_manager),
    claim_manager: ClaimManagerInterface = Depends(get_claim_manager),
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """Execute a law and render its result"""

    logger.warn(f"[LAWS] execute {service} {law} (can_submit_claims={can_submit_claims}, kvk={kvk})")

    try:
        law = unquote(law)
        law, result, parameters = evaluate_law(
            bsn,
            law,
            service,
            machine_service,
            approved=False,
            claim_manager=claim_manager,
            effective_date=date,
            kvk_nummer=kvk,
        )

    except Exception as e:
        logger.error(f"[LAWS] EXCEPTION in execute_law(): {type(e).__name__}: {e}", exc_info=True)
        return templates.TemplateResponse(
            get_tile_template(service, law),
            {
                "request": request,
                "bsn": bsn,
                "law": law,
                "service": service,
                "rule_spec": {"name": law.split("/")[-1].replace("_", " ").title()},
                "error": True,
                "message": str(e),
            },
        )

    # Check if there's an existing case
    existing_case = case_manager.get_case(bsn, service, law)

    # Get the appropriate template
    template_path = get_tile_template(service, law)

    rule_spec = machine_service.get_rule_spec(law, TODAY, service)

    logger.warn(f"[LAWS] result {result}")

    # For business laws, get profile data to check existing vergunning status
    profile_data = None
    if kvk:
        try:
            profile = machine_service.get_profile_data(bsn)
            if profile and "sources" in profile:
                profile_data = _apply_profile_overrides(profile["sources"].get(service, {}), service, kvk)
        except Exception as e:
            logger.warning(f"Failed to get profile data for {bsn}: {e}")

    # Extract value tree from path for templates to access resolved values
    value_tree = machine_service.extract_value_tree(result.path)

    return templates.TemplateResponse(
        template_path,
        {
            "bsn": bsn,
            "effective_bsn": bsn,  # For tile templates
            "kvk": kvk,
            "request": request,
            "law": law,
            "service": service,
            "rule_spec": rule_spec,
            "result": result.output,
            "input": result.input,
            "path": value_tree,
            "requirements_met": result.requirements_met,
            "missing_required": result.missing_required,
            "current_case": existing_case,
            "can_submit_claims": can_submit_claims,
            "profile_data": profile_data,
        },
    )


@router.post("/submit-case")
async def submit_case(
    request: Request,
    service: str,
    law: str,
    bsn: str,
    approved: bool = False,
    kvk: str = None,
    case_manager: CaseManagerInterface = Depends(get_case_manager),
    claim_manager: ClaimManagerInterface = Depends(get_claim_manager),
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """Submit a new case"""
    law = unquote(law)

    # Get kvk from query params if not provided directly
    if not kvk:
        kvk = request.query_params.get("kvk")

    law, result, parameters = evaluate_law(
        bsn,
        law,
        service,
        machine_service,
        approved=approved,
        claim_manager=claim_manager,
        effective_date=request.query_params.get("date"),
        kvk_nummer=kvk,
    )

    # Get user-provided parameter names from rule spec and merge their values
    rule_spec = machine_service.get_rule_spec(law, TODAY, service)
    param_names = {p["name"] for p in rule_spec.get("properties", {}).get("parameters", [])}
    user_params = {
        k.lstrip("$"): v for k, v in (result.input or {}).items() if k.lstrip("$") in param_names and v is not None
    }

    # Check if this law requires manual approval (from YAML metadata)
    requires_manual_approval = rule_spec.get("requires_manual_approval", False)

    case_id = case_manager.submit_case(
        bsn=bsn,
        service=service,
        law=law,
        parameters={**parameters, **user_params},
        claimed_result=result.output,
        approved_claims_only=approved,
        force_manual_review=requires_manual_approval,
    )

    case = case_manager.get_case_by_id(case_id)

    # Cross-law updates: alcoholwet approval affects exploitatievergunning
    # TODO: need to remove this hard-coded part
    # Creates a PENDING claim so Claudia can review and confirm the change
    if law == "alcoholwet/vergunning" and kvk and result.output.get("heeft_recht_op_vergunning"):
        exploitatie_law = "algemene_plaatselijke_verordening/exploitatievergunning"
        try:
            profile = machine_service.get_profile_data(bsn)
            if profile and "sources" in profile:
                profile_service_data = profile["sources"].get(service, {})
                vergunningen = profile_service_data.get("vergunningen", [])
                for v in vergunningen:
                    if v.get("kvk_nummer") == kvk and v.get("heeft_exploitatievergunning"):
                        # Create pending claim for VERSTREKT_ALCOHOL so the
                        # exploitatievergunning tile shows a data change warning
                        if not v.get("heeft_alcoholvergunning"):
                            claim_manager.submit_claim(
                                service=service,
                                key="VERSTREKT_ALCOHOL",
                                old_value=False,
                                new_value=True,
                                reason="Alcoholwetvergunning toegekend",
                                claimant="CITIZEN",
                                law=exploitatie_law,
                                bsn=bsn,
                                case_id=case_id,
                                auto_approve=False,
                            )
                        break
        except Exception as e:
            logger.warning(f"Failed to create claim for exploitatievergunning: {e}")

    # Re-evaluate the law AFTER the case is submitted so counts include the new case
    _, result, _ = evaluate_law(
        bsn,
        law,
        service,
        machine_service,
        approved=approved,
        claim_manager=claim_manager,
        effective_date=request.query_params.get("date"),
        kvk_nummer=kvk,
    )

    # For business laws, get profile data to display after submission
    profile_data = None
    if kvk:
        try:
            profile = machine_service.get_profile_data(bsn)
            if profile and "sources" in profile:
                profile_data = _apply_profile_overrides(profile["sources"].get(service, {}), service, kvk)
        except Exception as e:
            logger.warning(f"Failed to get profile data for {bsn}: {e}")

    # Extract value tree from the re-evaluated result (includes the new case in counts)
    value_tree = machine_service.extract_value_tree(result.path)

    # Return the updated law result with the new case
    return templates.TemplateResponse(
        get_tile_template(service, law),
        {
            "bsn": bsn,
            "effective_bsn": bsn,
            "kvk": kvk,
            "request": request,
            "law": law,
            "service": service,
            "rule_spec": rule_spec,
            "result": result.output,
            "input": result.input,
            "path": value_tree,
            "requirements_met": result.requirements_met,
            "missing_required": result.missing_required,
            "current_case": case,
            "profile_data": profile_data,
        },
    )


@router.post("/objection-case")
async def objection_case(
    request: Request,
    case_id: str,
    service: str,
    law: str,
    bsn: str,
    kvk: str = None,
    reason: str = Form(...),
    case_manager: CaseManagerInterface = Depends(get_case_manager),
    claim_manager: ClaimManagerInterface = Depends(get_claim_manager),
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """Submit an objection for an existing case"""
    law = unquote(law)

    if not kvk:
        kvk = request.query_params.get("kvk")

    # Submit the objection with new claimed result
    case_manager.objection(
        case_id=case_id,
        reason=reason,
    )

    law, result, parameters = evaluate_law(
        bsn,
        law,
        service,
        machine_service,
        claim_manager=claim_manager,
        effective_date=request.query_params.get("date"),
        kvk_nummer=kvk,
    )

    template_path = get_tile_template(service, law)

    return templates.TemplateResponse(
        template_path,
        {
            "bsn": bsn,
            "effective_bsn": bsn,
            "kvk": kvk,
            "request": request,
            "law": law,
            "service": service,
            "rule_spec": machine_service.get_rule_spec(law, TODAY, service),
            "result": result.output,
            "input": result.input,
            "requirements_met": result.requirements_met,
            "current_case": case_manager.get_case_by_id(case_id),
        },
    )


def node_to_dict(node, skip_services=False):
    """Convert PathNode to serializable dict"""
    if node is None:
        return None
    return {
        "type": node.type,
        "name": node.name,
        "result": str(node.result),
        "details": {k: str(v) for k, v in node.details.items()},
        "children": []
        if skip_services and node.type == "service_evaluation"
        else [node_to_dict(child, skip_services=skip_services) for child in node.children],
    }


@router.get("/explanation")
async def explanation(
    request: Request,
    service: str,
    law: str,
    bsn: str,
    kvk: str = None,
    provider: str = None,  # Add provider parameter
    approved: bool = False,
    claim_manager: ClaimManagerInterface = Depends(get_claim_manager),
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """Get a citizen-friendly explanation of the rule evaluation path"""
    try:
        print(f"Explanation requested for {service}, {law}, with provider: {provider}")
        law = unquote(law)
        law, result, parameters = evaluate_law(
            bsn,
            law,
            service,
            machine_service,
            approved=approved,
            claim_manager=claim_manager,
            effective_date=request.query_params.get("date"),
            kvk_nummer=kvk,
        )

        # Convert path and rule_spec to JSON strings
        path_dict = node_to_dict(result.path, skip_services=True)
        path_json = json.dumps(path_dict, ensure_ascii=False, indent=2)

        rule_spec = machine_service.get_rule_spec(law, TODAY, service)

        # Filter relevant parts of rule_spec
        relevant_spec = {
            "name": rule_spec.get("name"),
            "description": rule_spec.get("description"),
            "properties": {
                "input": rule_spec.get("properties", {}).get("input", []),
                "output": rule_spec.get("properties", {}).get("output", []),
                "parameters": rule_spec.get("properties", {}).get("parameters", []),
                "definitions": rule_spec.get("properties", {}).get("definitions", []),
            },
            "requirements": rule_spec.get("requirements"),
            "actions": rule_spec.get("actions"),
        }

        rule_spec_json = json.dumps(relevant_spec, ensure_ascii=False, indent=2)

        # Get available and configured LLM providers
        available_providers = llm_factory.get_available_providers()
        configured_providers = llm_factory.get_configured_providers(request)

        # Get the provider to use (first from parameter, then from session, then default)
        current_provider = None
        if provider and provider in configured_providers:
            # If provider is specified and configured, use and store it
            current_provider = provider
            request.session["preferred_llm_provider"] = provider
            print(f"Using and storing provider from parameter: {provider}")
        elif (
            "preferred_llm_provider" in request.session
            and request.session["preferred_llm_provider"] in configured_providers
        ):
            # If provider is in session and configured, use it
            current_provider = request.session["preferred_llm_provider"]
            print(f"Using provider from session: {current_provider}")
        else:
            # Otherwise use default provider
            current_provider = llm_factory.get_provider(request)
            print(f"Using default provider: {current_provider}")

        # Get explanation from the selected LLM provider
        llm_service = llm_factory.get_service(current_provider)
        explanation_text = llm_service.generate_explanation(path_json, rule_spec_json)
        print(f"Generated explanation using provider: {current_provider}")

        # Format provider info for the template
        providers = [{"name": p, "is_configured": p in configured_providers} for p in available_providers]

        # Create a response
        response = templates.TemplateResponse(
            "partials/tiles/components/explanation.html",
            {
                "request": request,
                "explanation": explanation_text,
                "service": service,
                "law": law,
                "bsn": bsn,
                "providers": providers,
                "current_provider": current_provider,
                "id": "explanation-panel",  # needed for HTMX targeting
            },
        )

        return response
    except Exception as e:
        print(f"Error in explain_path: {e}")
        return templates.TemplateResponse(
            "partials/tiles/components/explanation.html",
            {
                "request": request,
                "error": "Er is een fout opgetreden bij het genereren van de uitleg. Probeer het later opnieuw.",
                "service": service,
                "law": law,
                "bsn": bsn,
                "providers": [],  # Empty list to avoid further errors
                "id": "explanation-panel",  # needed for HTMX targeting
            },
        )


@router.get("/application-panel")
async def application_panel(
    request: Request,
    service: str,
    law: str,
    bsn: str,
    kvk: str = None,
    approved: bool = False,
    case_manager: CaseManagerInterface = Depends(get_case_manager),
    claim_manager: ClaimManagerInterface = Depends(get_claim_manager),
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """Get the application panel with tabs"""
    try:
        law = unquote(law)
        law, result, parameters = evaluate_law(
            bsn,
            law,
            service,
            machine_service,
            approved=approved,
            claim_manager=claim_manager,
            effective_date=request.query_params.get("date"),
            kvk_nummer=kvk,
        )

        value_tree = machine_service.extract_value_tree(result.path)
        existing_case = case_manager.get_case(bsn, service, law)

        claims = claim_manager.get_claims_by_bsn(bsn, include_rejected=True)
        claim_map = {(claim.service, claim.law, claim.key): claim for claim in claims}

        rule_spec = machine_service.get_rule_spec(law, TODAY, service)

        # For business laws, get profile data (used in templates for display purposes)
        profile_data = None
        if kvk:
            try:
                profile = machine_service.get_profile_data(bsn)
                if profile and "sources" in profile:
                    profile_data = _apply_profile_overrides(profile["sources"].get(service, {}), service, kvk)
            except Exception as e:
                logger.warning(f"Failed to get profile data for {bsn}: {e}")

        return templates.TemplateResponse(
            "partials/tiles/components/application_panel.html",
            {
                "request": request,
                "service": service,
                "law": law,
                "rule_spec": rule_spec,
                "input": result.input,
                "result": result.output,
                "requirements_met": result.requirements_met,
                "path": value_tree,
                "bsn": bsn,
                "effective_bsn": bsn,
                "kvk": kvk,
                "current_case": existing_case,
                "claim_map": claim_map,
                "missing_required": result.missing_required,
                "wallet_enabled": is_wallet_enabled(),
                "current_engine_id": get_engine_id(),
                "profile_data": profile_data,
            },
        )
    except Exception as e:
        logger.error(f"Error in application panel: {e}")
        return templates.TemplateResponse(
            "partials/tiles/components/application_panel.html",
            {
                "request": request,
                "error": "Er is een fout opgetreden bij het genereren van het aanvraagformulier. Probeer het later opnieuw.",
                "service": service,
                "law": law,
                "current_engine_id": get_engine_id(),
            },
        )


@router.post("/update-profile-table")
async def update_profile_table(
    request: Request,
    service: str,
    table: str,
    kvk: str,
    bsn: str,
    law: str,
    machine_service: EngineInterface = Depends(get_machine_service),
    case_manager: CaseManagerInterface = Depends(get_case_manager),
) -> JSONResponse:
    """Update a profile data table in memory (for editable profile data like energy measures)."""
    law = unquote(law)
    body = await request.json()
    rows = body.get("rows", [])

    # Store override for profile_data rendering
    _profile_data_overrides[(service, table, kvk)] = rows

    # Also update the source DataFrame so law evaluation reflects changes
    df = pd.DataFrame(rows)
    machine_service.set_source_dataframe(service, table, df)

    # Re-evaluate the law and return the updated tile
    parameters = {"BSN": bsn}
    if kvk:
        parameters["KVK_NUMMER"] = kvk
    result = machine_service.evaluate(
        service=service,
        law=law,
        parameters=parameters,
        reference_date=TODAY,
    )

    existing_case = case_manager.get_case(bsn, service, law)
    template_path = get_tile_template(service, law)
    rule_spec = machine_service.get_rule_spec(law, TODAY, service)

    profile_data = None
    try:
        profile = machine_service.get_profile_data(bsn)
        if profile and "sources" in profile:
            profile_data = _apply_profile_overrides(profile["sources"].get(service, {}), service, kvk)
    except Exception as e:
        logger.warning(f"Failed to get profile data for {bsn}: {e}")

    return templates.TemplateResponse(
        template_path,
        {
            "bsn": bsn,
            "effective_bsn": bsn,
            "kvk": kvk,
            "request": request,
            "law": law,
            "service": service,
            "rule_spec": rule_spec,
            "result": result.output,
            "input": result.input,
            "requirements_met": result.requirements_met,
            "missing_required": result.missing_required,
            "current_case": existing_case,
            "profile_data": profile_data,
        },
    )
