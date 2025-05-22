import json
import os
from typing import Any
from urllib.parse import unquote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse
from jinja2 import TemplateNotFound

from explain.llm_factory import llm_factory
from web.dependencies import TODAY, get_case_manager, get_claim_manager, get_machine_service, templates
from web.engines import CaseManagerInterface, ClaimManagerInterface, EngineInterface, RuleResult
from web.feature_flags import is_vertegenwoordiging_enabled, is_wallet_enabled

router = APIRouter(prefix="/laws", tags=["laws"])


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
    bsn: str, law: str, service: str, machine_service: EngineInterface, approved: bool = True
) -> tuple[str, RuleResult, dict[str, Any]]:
    """Evaluate a law for a given BSN"""

    parameters = {"BSN": bsn}

    # Execute the law using EngineInterface
    result = machine_service.evaluate(
        service=service, law=law, parameters=parameters, reference_date=TODAY, approved=approved
    )

    return law, result, parameters


@router.get("/list")
async def list_laws():
    """List all available law files"""

    laws_dir = os.path.join(os.path.dirname(__file__), "../../law")
    law_files = []
    for root, _, files in os.walk(laws_dir):
        for file in files:
            if file.endswith(".yaml"):  # Return only YAML files
                law_files.append(os.path.relpath(os.path.join(root, file), laws_dir))

    return JSONResponse(content=law_files)


@router.get("/execute")
async def execute_law(
    request: Request,
    service: str,
    law: str,
    bsn: str,
    acting_as: str = None,
    acting_as_bsn: str = None,
    relationship_type: str = None,
    case_manager: CaseManagerInterface = Depends(get_case_manager),
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """Execute a law and render its result"""
    # Only allow representation if the feature flag is enabled
    if (acting_as or acting_as_bsn or relationship_type) and not is_vertegenwoordiging_enabled():
        acting_as = None
        acting_as_bsn = None
        relationship_type = None
    try:
        law = unquote(law)
        law, result, parameters = evaluate_law(bsn, law, service, machine_service, approved=False)

    except Exception as e:
        print(e)
        # Get profile data for context
        profile = None
        try:
            profile = machine_service.get_profile_data(bsn)
        except:
            pass  # Ignore errors when getting profile in the error handler

        # Create representative info if possible
        representative_info = None
        if acting_as and acting_as_bsn:
            try:
                representative_profile = machine_service.get_profile_data(acting_as_bsn)
                if representative_profile:
                    representative_info = {
                        "name": acting_as,
                        "bsn": acting_as_bsn,
                        "relationship_type": relationship_type,
                    }
            except:
                pass  # Ignore errors when getting representative in the error handler

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
                "profile": profile,
                "representative_info": representative_info,
            },
        )

    # Check if there's an existing case
    existing_case = case_manager.get_case(bsn, service, law)

    # Load representative information if needed
    representative_info = None
    if acting_as and acting_as_bsn:
        representative_profile = machine_service.get_profile_data(acting_as_bsn)
        if representative_profile:
            representative_info = {
                "name": acting_as,
                "bsn": acting_as_bsn,
                "relationship_type": relationship_type,
            }

    # Get the appropriate template
    template_path = get_tile_template(service, law)

    # Get profile data for context
    profile = machine_service.get_profile_data(bsn)

    rule_spec = machine_service.get_rule_spec(law, TODAY, service)

    return templates.TemplateResponse(
        template_path,
        {
            "bsn": bsn,
            "request": request,
            "law": law,
            "service": service,
            "rule_spec": rule_spec,
            "result": result.output,
            "input": result.input,
            "requirements_met": result.requirements_met,
            "missing_required": result.missing_required,
            "current_case": existing_case,
            "representative_info": representative_info,
            "profile": profile,  # Add profile data to the context
        },
    )


@router.post("/submit-case")
async def submit_case(
    request: Request,
    service: str,
    law: str,
    bsn: str,
    approved: bool = False,
    acting_as: str = None,
    acting_as_bsn: str = None,
    relationship_type: str = None,
    case_manager: CaseManagerInterface = Depends(get_case_manager),
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """Submit a new case"""
    # Only allow representation if the feature flag is enabled
    if (acting_as or acting_as_bsn or relationship_type) and not is_vertegenwoordiging_enabled():
        acting_as = None
        acting_as_bsn = None
        relationship_type = None
    law = unquote(law)

    law, result, parameters = evaluate_law(bsn, law, service, machine_service, approved=approved)

    # Add a note that this was submitted by a representative if applicable
    representative_note = ""
    if acting_as and acting_as_bsn:
        representative_note = f"Ingediend door {acting_as} (BSN: {acting_as_bsn}) als {relationship_type}."
        parameters["REPRESENTATIVE_BSN"] = acting_as_bsn
        parameters["REPRESENTATIVE_NAME"] = acting_as
        parameters["REPRESENTATIVE_TYPE"] = relationship_type

    case_id = case_manager.submit_case(
        bsn=bsn,
        service=service,
        law=law,
        parameters=parameters,
        claimed_result=result.output,
        approved_claims_only=approved,
        note=representative_note,
    )

    case = case_manager.get_case_by_id(case_id)

    # Load representative information if needed
    representative_info = None
    if acting_as and acting_as_bsn:
        representative_profile = machine_service.get_profile_data(acting_as_bsn)
        if representative_profile:
            representative_info = {
                "name": acting_as,
                "bsn": acting_as_bsn,
                "relationship_type": relationship_type,
            }

    rule_spec = machine_service.get_rule_spec(law, TODAY, service)

    # Get profile data for context
    profile = machine_service.get_profile_data(bsn)

    # Return the updated law result with the new case
    return templates.TemplateResponse(
        get_tile_template(service, law),
        {
            "bsn": bsn,
            "request": request,
            "law": law,
            "service": service,
            "rule_spec": rule_spec,
            "result": result.output,
            "input": result.input,
            "requirements_met": result.requirements_met,
            "current_case": case,
            "representative_info": representative_info,
            "profile": profile,  # Add profile data to the context
        },
    )


@router.post("/objection-case")
async def objection_case(
    request: Request,
    case_id: str,
    service: str,
    law: str,
    bsn: str,
    reason: str = Form(...),  # Changed this line to use Form
    acting_as: str = None,
    acting_as_bsn: str = None,
    relationship_type: str = None,
    case_manager: CaseManagerInterface = Depends(get_case_manager),
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """Submit an objection for an existing case"""
    # Only allow representation if the feature flag is enabled
    if (acting_as or acting_as_bsn or relationship_type) and not is_vertegenwoordiging_enabled():
        acting_as = None
        acting_as_bsn = None
        relationship_type = None
    # First calculate the new result with disputed parameters
    law = unquote(law)

    # Add a note if submitted by a representative
    formatted_reason = reason
    if acting_as and acting_as_bsn:
        formatted_reason = (
            f"{reason}\n\nBezwaar ingediend door {acting_as} (BSN: {acting_as_bsn}) als {relationship_type}."
        )

    # Submit the objection with new claimed result
    case_manager.objection(
        case_id=case_id,
        reason=formatted_reason,
    )

    law, result, parameters = evaluate_law(bsn, law, service, machine_service)

    template_path = get_tile_template(service, law)

    # Load representative information if needed
    representative_info = None
    if acting_as and acting_as_bsn:
        representative_profile = machine_service.get_profile_data(acting_as_bsn)
        if representative_profile:
            representative_info = {
                "name": acting_as,
                "bsn": acting_as_bsn,
                "relationship_type": relationship_type,
            }

    # Get profile data for context
    profile = machine_service.get_profile_data(bsn)

    return templates.TemplateResponse(
        template_path,
        {
            "bsn": bsn,
            "request": request,
            "law": law,
            "service": service,
            "rule_spec": machine_service.get_rule_spec(law, TODAY, service),
            "result": result.output,
            "input": result.input,
            "requirements_met": result.requirements_met,
            "current_case": case_manager.get_case_by_id(case_id),
            "representative_info": representative_info,
            "profile": profile,  # Add profile data to the context
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
    provider: str = None,  # Add provider parameter
    approved: bool = False,
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """Get a citizen-friendly explanation of the rule evaluation path"""
    try:
        print(f"Explanation requested for {service}, {law}, with provider: {provider}")
        law = unquote(law)
        law, result, parameters = evaluate_law(bsn, law, service, machine_service, approved=approved)

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
    approved: bool = False,
    acting_as: str = None,
    acting_as_bsn: str = None,
    relationship_type: str = None,
    case_manager: CaseManagerInterface = Depends(get_case_manager),
    claim_manager: ClaimManagerInterface = Depends(get_claim_manager),
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """Get the application panel with tabs"""
    # Only allow representation if the feature flag is enabled
    if (acting_as or acting_as_bsn or relationship_type) and not is_vertegenwoordiging_enabled():
        acting_as = None
        acting_as_bsn = None
        relationship_type = None
    try:
        law = unquote(law)
        law, result, parameters = evaluate_law(bsn, law, service, machine_service, approved=approved)

        value_tree = machine_service.extract_value_tree(result.path)
        existing_case = case_manager.get_case(bsn, service, law)

        claims = claim_manager.get_claims_by_bsn(bsn, include_rejected=True)
        claim_map = {(claim.service, claim.law, claim.key): claim for claim in claims}

        rule_spec = machine_service.get_rule_spec(law, TODAY, service)

        # Get profile data for context
        profile = machine_service.get_profile_data(bsn)

        # Load representative information if needed
        representative_info = None
        if acting_as and acting_as_bsn:
            representative_profile = machine_service.get_profile_data(acting_as_bsn)
            if representative_profile:
                representative_info = {
                    "name": acting_as,
                    "bsn": acting_as_bsn,
                    "relationship_type": relationship_type,
                }

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
                "current_case": existing_case,
                "claim_map": claim_map,
                "missing_required": result.missing_required,
                "wallet_enabled": is_wallet_enabled(),
                "profile": profile,  # Add profile data to the context
                "representative_info": representative_info,  # Add representative info
            },
        )
    except Exception as e:
        print(f"Error in application panel: {e}")
        # Get profile data for context
        profile = None
        try:
            profile = machine_service.get_profile_data(bsn)
        except:
            pass  # Ignore errors when getting profile in the error handler

        # Create representative info if possible
        representative_info = None
        if acting_as and acting_as_bsn:
            try:
                representative_profile = machine_service.get_profile_data(acting_as_bsn)
                if representative_profile:
                    representative_info = {
                        "name": acting_as,
                        "bsn": acting_as_bsn,
                        "relationship_type": relationship_type,
                    }
            except:
                pass  # Ignore errors when getting representative in the error handler

        return templates.TemplateResponse(
            "partials/tiles/components/application_panel.html",
            {
                "request": request,
                "error": "Er is een fout opgetreden bij het genereren van het aanvraagformulier. Probeer het later opnieuw.",
                "service": service,
                "law": law,
                "bsn": bsn,
                "profile": profile,
                "representative_info": representative_info,
            },
        )
