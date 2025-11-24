import json
import logging
import os
from typing import Any
from urllib.parse import unquote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse
from jinja2 import TemplateNotFound

from explain.llm_factory import llm_factory
from web.dependencies import TODAY, get_case_manager, get_claim_manager, get_engine_id, get_machine_service, templates
from web.engines import CaseManagerInterface, ClaimManagerInterface, EngineInterface, RuleResult
from web.feature_flags import is_wallet_enabled
import requests


router = APIRouter(prefix="/laws", tags=["laws"])

logger = logging.getLogger(__name__)


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
) -> tuple[str, RuleResult, dict[str, Any]]:
    """Evaluate a law for a given BSN"""

    logger.warn(f"evalute law {service} {law} for {bsn}")

    parameters = {"BSN": bsn}
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

        # Build overwrite_input from claims
        if relevant_claims:
            overwrite_input = {}
            for claim in relevant_claims:
                overwrite_input[claim.key] = claim.new_value

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
    date: str = None,
    case_manager: CaseManagerInterface = Depends(get_case_manager),
    claim_manager: ClaimManagerInterface = Depends(get_claim_manager),
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """Execute a law and render its result"""

    logger.warn(f"[LAWS] execute {service} {law}")

    try:
        law = unquote(law)
        law, result, parameters = evaluate_law(
            bsn, law, service, machine_service, approved=False, claim_manager=claim_manager, effective_date=date
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
        },
    )


@router.post("/submit-case")
async def submit_case(
    request: Request,
    service: str,
    law: str,
    bsn: str,
    approved: bool = False,
    case_manager: CaseManagerInterface = Depends(get_case_manager),
    claim_manager: ClaimManagerInterface = Depends(get_claim_manager),
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """Submit a new case"""
    law = unquote(law)

    law, result, parameters = evaluate_law(
        bsn,
        law,
        service,
        machine_service,
        approved=approved,
        claim_manager=claim_manager,
        effective_date=request.query_params.get("date"),
    )

    case_id = case_manager.submit_case(
        bsn=bsn,
        service=service,
        law=law,
        parameters=parameters,
        claimed_result=result.output,
        approved_claims_only=approved,
    )

    case = case_manager.get_case_by_id(case_id)

    rule_spec = machine_service.get_rule_spec(law, TODAY, service)

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
    case_manager: CaseManagerInterface = Depends(get_case_manager),
    claim_manager: ClaimManagerInterface = Depends(get_claim_manager),
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """Submit an objection for an existing case"""
    # First calculate the new result with disputed parameters
    law = unquote(law)

    # Submit the objection with new claimed result
    case_manager.objection(
        case_id=case_id,
        reason=reason,
    )

    law, result, parameters = evaluate_law(
        bsn, law, service, machine_service, claim_manager=claim_manager, effective_date=request.query_params.get("date")
    )

    template_path = get_tile_template(service, law)

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
        )

        value_tree = machine_service.extract_value_tree(result.path)
        existing_case = case_manager.get_case(bsn, service, law)

        claims = claim_manager.get_claims_by_bsn(bsn, include_rejected=True)
        claim_map = {(claim.service, claim.law, claim.key): claim for claim in claims}

        rule_spec = machine_service.get_rule_spec(law, TODAY, service)

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
                "current_engine_id": get_engine_id(),
            },
        )
    except Exception as e:
        print(f"Error in application panel: {e}")
        return templates.TemplateResponse(
            "partials/tiles/components/application_panel.html",
            {
                "request": request,
                "error": (
                    "Er is een fout opgetreden bij het genereren van het aanvraagformulier. Probeer het later opnieuw."
                ),
                "service": service,
                "law": law,
                "current_engine_id": get_engine_id(),
            },
        )


def extract_thresholds_from_spec(rule_spec: dict[str, Any], input_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract income thresholds from rule specification requirements.
    This helps identify critical boundaries where benefits change.

    Args:
        rule_spec: The rule specification dictionary
        input_data: The input data used for evaluation

    Returns:
        List of threshold information dictionaries
    """
    thresholds = []

    # Calculate total income from input
    total_income = 0
    income_fields = [
        "loon_uit_dienstbetrekking",
        "uitkeringen_en_pensioenen",
        "winst_uit_onderneming",
        "resultaat_overige_werkzaamheden",
        "reguliere_voordelen",
        "vervreemdingsvoordelen",
        "voordeel_sparen_beleggen",
    ]

    for field in income_fields:
        if input_data and field in input_data and isinstance(input_data[field], (int, float)):
            total_income += input_data[field]

    # Try to extract thresholds from requirements
    # TODO: Parse requirements to extract actual threshold values from law specifications
    # requirements = rule_spec.get("requirements", [])
    # This is a PLACEHOLDER - real implementation would parse the requirement logic
    # to extract thresholds dynamically from expressions like "toetsingsinkomen < 43651"

    # For now, use common Dutch benefit thresholds as fallback
    # TODO: Extract these dynamically from the law specifications
    common_thresholds = [
        {
            "name": "Zorgtoeslag maximum inkomen (alleenstaand)",
            "value": 4365100,  # €43,651 (2024)
            "type": "income_limit",
            "description": "Boven dit inkomen komt u niet meer in aanmerking voor zorgtoeslag",
        },
        {
            "name": "Huurtoeslag maximum inkomen (alleenstaand)",
            "value": 3067400,  # €30,674 (2024)
            "type": "income_limit",
            "description": "Boven dit inkomen komt u niet meer in aanmerking voor huurtoeslag",
        },
        {
            "name": "Kindgebonden budget afbouwgrens",
            "value": 2400000,  # €24,000
            "type": "income_limit",
            "description": "Vanaf dit inkomen wordt het kindgebonden budget afgebouwd",
        },
    ]

    # Only include thresholds that are relevant (within reasonable range of current income)
    for threshold in common_thresholds:
        if total_income > 0 and abs(total_income - threshold["value"]) < threshold["value"] * 0.6:
            thresholds.append(
                {
                    "name": threshold["name"],
                    "threshold_value": threshold["value"],
                    "current_value": total_income,
                    "type": threshold["type"],
                    "description": threshold["description"],
                    "distance": abs(total_income - threshold["value"]),
                    "is_close": abs(total_income - threshold["value"]) < 500000,  # Within €5000
                }
            )

    return thresholds

@router.post("/test")
async def test_post_request(
    request: Request
):
    return {"hoi": "hey"}

@router.post("/simulate")
async def simulate_scenario(
    request: Request,
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """
    Simulate a scenario with fictional data without creating cases or claims.
    This allows citizens to perform 'what-if' calculations (proefberekening).
    """
    try:
        # Get the request body
        body = await request.json()

        bsn = body.get("bsn")
        scenario_data = body.get("scenario_data", {})
        effective_date = body.get("effective_date")

        if not bsn:
            return JSONResponse(
                {"status": "error", "message": "BSN is required"},
                status_code=400,
            )

        # Get all discoverable service laws
        discoverable_service_laws = machine_service.get_sorted_discoverable_service_laws(bsn)

        # Evaluate all laws with the scenario data
        results = []
        for service_law in discoverable_service_laws:
            service = service_law["service"]
            law = service_law["law"]

            try:

                # Evaluate the law with scenario data as overwrite_input
                result = machine_service.evaluate(
                    service=service,
                    law=law,
                    parameters={"BSN": bsn},
                    reference_date=TODAY,
                    effective_date=effective_date,
                    approved=False,
                    overwrite_input=scenario_data,
                ) 

                if (law == "zorgtoeslagwet"):
                    print("-----------------------------")
                    print("INPUT:")
                    for key, value in result.input.items() :
                        print(f"    {key}: {value}")

                    print("OVERWRITE:")
                    print(scenario_data)

                    print("LAW")
                    print(law)
                    print(service)

                    print("OUTPUT")
                    for key, value in result.output.items() :
                        print(f"    {key}: {value}")

                    result.output["hoogte_toeslag"] = 0
                    result.output["is_verzekerde_zorgtoeslag"] = False

                    print("-----------------------------")

                    data = {'name': 'Suzan', 'email': 'suzan@example.com'}
                    response = requests.post('http://localhost:8000/laws/test', json=data)
                    print(response.json())


                rule_spec = machine_service.get_rule_spec(law, TODAY, service)

                # Extract thresholds from requirements (if any)
                thresholds = extract_thresholds_from_spec(rule_spec, result.input)

                results.append(
                    {
                        "service": service,
                        "law": law,
                        "law_name": rule_spec.get("name", law),
                        "output": result.output,
                        "input": result.input,
                        "requirements_met": result.requirements_met,
                        "missing_required": result.missing_required,
                        "thresholds": thresholds,  # Add threshold information
                    }
                )
            except Exception as e:
                logger.error(f"Error evaluating {service}/{law} for simulation: {e}")
                results.append(
                    {
                        "service": service,
                        "law": law,
                        "error": str(e),
                    }
                )

        return JSONResponse(
            {
                "status": "ok",
                "results": results,
                "scenario_data": scenario_data,
            }
        )

    except Exception as e:
        logger.error(f"Error in simulate_scenario: {e}")
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500,
        )
