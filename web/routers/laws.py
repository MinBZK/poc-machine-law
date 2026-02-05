import json
import logging
import os
from typing import Any
from urllib.parse import unquote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse
from jinja2 import TemplateNotFound

from explain.llm_factory import llm_factory
from web.dependencies import (
    TODAY,
    get_case_manager,
    get_claim_manager,
    get_engine_id,
    get_machine_service,
    get_simulated_date,
    templates,
)
from web.engines import CaseManagerInterface, ClaimManagerInterface, EngineInterface, RuleResult
from web.feature_flags import is_wallet_enabled

router = APIRouter(prefix="/laws", tags=["laws"])

logger = logging.getLogger(__name__)


def _check_awir_needs_review(
    case,
    current_jaarbedrag: int,
    case_manager: CaseManagerInterface,
    has_claims: bool = False,
    claim_manager: ClaimManagerInterface | None = None,
    bsn: str | None = None,
    service: str | None = None,
    law: str | None = None,
) -> dict | None:
    """
    Check of een AWIR case handmatige review nodig heeft.
    Bij ELK verschil t.o.v. vorig jaar OF claims (wijzigingen) → IN_REVIEW.

    Args:
        case: Het huidige Case object
        current_jaarbedrag: Het berekende jaarbedrag voor dit jaar
        case_manager: De CaseManager voor opvragen vorig jaar case
        has_claims: Of er claims (wijzigingen door burger) zijn
        claim_manager: De ClaimManager voor opvragen claims
        bsn: BSN van de burger
        service: Service type
        law: Law identifier

    Returns:
        None als geen review nodig, anders dict met previous_result en reason
    """
    # Check 1: Zijn er claims (wijzigingen door de burger)?
    if has_claims and claim_manager and bsn and service and law:
        claims = claim_manager.get_claims_by_bsn(bsn, include_rejected=False)
        relevant_claims = [
            claim
            for claim in claims
            if claim.service == service and claim.law == law and claim.status in ["PENDING", "APPROVED"]
        ]
        if relevant_claims:
            # Er zijn wijzigingen door de burger - naar review
            claim_details = {claim.key: claim.new_value for claim in relevant_claims}
            return {
                "previous_result": {"wijzigingen": "brongegevens"},
                "current_result": {"wijzigingen": claim_details},
                "reason": "Wijziging in gegevens door burger doorgegeven",
            }

    # Check 2: Is er een vorig jaar case om mee te vergelijken?
    vorig_jaar_case_id = getattr(case, "vorig_jaar_case_id", None)
    if vorig_jaar_case_id:
        vorig_jaar_case = case_manager.get_case_by_id(vorig_jaar_case_id)
        if vorig_jaar_case:
            # Vergelijk berekend jaarbedrag met vorig jaar
            vorig_jaarbedrag = vorig_jaar_case.berekend_jaarbedrag or 0

            # Bij ELK verschil → naar review
            if current_jaarbedrag != vorig_jaarbedrag:
                return {
                    "previous_result": {"jaarbedrag": vorig_jaarbedrag},
                    "current_result": {"jaarbedrag": current_jaarbedrag},
                    "reason": "Wijziging in gegevens gedetecteerd t.o.v. vorig jaar",
                }

    return None


def get_primary_amount_value(rule_spec: dict, output: dict) -> int:
    """
    Haal de som van primary output waarden op basis van citizen_relevance: primary.

    Vervangt hardcoded veldnaam checks (hoogte_toeslag, subsidiebedrag)
    met dynamische lookup uit de rule specification.

    Args:
        rule_spec: De rule specification dictionary uit YAML
        output: De output dictionary van het evaluatie resultaat

    Returns:
        Som van primary amount/number output waarden, of 0 als geen gevonden
    """
    total = 0
    output_definitions = rule_spec.get("properties", {}).get("output", [])

    for output_def in output_definitions:
        if output_def.get("citizen_relevance") != "primary":
            continue

        output_name = output_def.get("name")
        output_type = output_def.get("type", "")

        # Alleen numerieke types voor bedragberekening
        if output_type not in ["amount", "number"]:
            continue

        value = output.get(output_name)
        if value is not None:
            try:
                total += int(value)
            except (ValueError, TypeError):
                pass

    return total


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

    laws_dir = os.path.join(os.path.dirname(__file__), "../../laws")
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
    can_submit_claims: bool = True,
    case_manager: CaseManagerInterface = Depends(get_case_manager),
    claim_manager: ClaimManagerInterface = Depends(get_claim_manager),
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """Execute a law and render its result"""

    logger.warn(f"[LAWS] execute {service} {law} (can_submit_claims={can_submit_claims})")

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

    # Check if there's an existing case for the current simulated year
    simulated_date = get_simulated_date(request)
    simulated_year = simulated_date.year

    # Get all cases for this BSN/service/law combination and find the most relevant one
    all_cases = case_manager.get_cases_by_bsn(bsn)
    relevant_cases = [c for c in all_cases if c.service == service and c.law == law]

    # Find the case for the current year, or the most recent one
    existing_case = None
    for case in relevant_cases:
        if getattr(case, "berekeningsjaar", None) == simulated_year:
            existing_case = case
            break
    if not existing_case and relevant_cases:
        # Fallback to most recent case (by berekeningsjaar or created_at)
        relevant_cases.sort(
            key=lambda c: c.berekeningsjaar if c.berekeningsjaar else (c.created_at.year if c.created_at else 0),
            reverse=True,
        )
        existing_case = relevant_cases[0]

    # Get the appropriate template
    template_path = get_tile_template(service, law)

    rule_spec = machine_service.get_rule_spec(law, TODAY, service)

    logger.warn(f"[LAWS] result {result}")

    return templates.TemplateResponse(
        template_path,
        {
            "bsn": bsn,
            "effective_bsn": bsn,  # For tile templates
            "request": request,
            "law": law,
            "service": service,
            "rule_spec": rule_spec,
            "result": result.output,
            "input": result.input,
            "requirements_met": result.requirements_met,
            "missing_required": result.missing_required,
            "current_case": existing_case,
            "can_submit_claims": can_submit_claims,
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

    # Get simulated date for time-based workflows
    simulated_date = get_simulated_date(request)

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
        effective_date=simulated_date,
    )

    # Get rule_spec for dynamic field detection in AWIR workflow
    rule_spec = machine_service.get_rule_spec(law, TODAY, service)

    # AWIR workflow for toeslagen: calculate eligibility and set voorschot/afwijzing
    # This triggers events that will create messages via CaseProcessor
    if service == "TOESLAGEN":
        # Dynamically determine benefit amount using citizen_relevance: primary
        # instead of hardcoded field names (hoogte_toeslag, subsidiebedrag, etc.)
        berekend_jaarbedrag = get_primary_amount_value(rule_spec, result.output)
        heeft_aanspraak = berekend_jaarbedrag > 0

        # Calculate eligibility (AWIR Art. 16 lid 1)
        case_manager.bereken_aanspraak(
            case_id=case_id,
            heeft_aanspraak=heeft_aanspraak,
            berekend_jaarbedrag=berekend_jaarbedrag,
            berekening_datum=simulated_date,
        )

        # Get the case to check for review requirements
        case = case_manager.get_case_by_id(case_id)

        # Check if manual review is needed due to changes vs previous year OR claims
        # approved=False means claims were applied (burger has made changes)
        has_claims = not approved
        needs_review = _check_awir_needs_review(
            case=case,
            current_jaarbedrag=berekend_jaarbedrag,
            case_manager=case_manager,
            has_claims=has_claims,
            claim_manager=claim_manager,
            bsn=bsn,
            service=service,
            law=law,
        )

        if needs_review:
            # Changes detected - route to manual review (IN_REVIEW)
            reason = needs_review.get("reason", "Wijziging in gegevens gedetecteerd")
            case_manager.select_for_manual_review(
                case_id=case_id,
                verifier_id="SYSTEM",
                reason=reason,
                claimed_result=needs_review.get("current_result", {}),
                verified_result=needs_review.get("previous_result", {}),
            )
        elif heeft_aanspraak:
            # No review needed and has entitlement - proceed to voorschot
            has_voorschot = any(b.get("type") == "VOORSCHOT" for b in (case.beschikkingen or []))
            if not has_voorschot:
                # Set voorschot (AWIR Art. 16) - triggers VoorschotBeschikkingVastgesteld event
                case_manager.stel_voorschot_vast(case_id=case_id, beschikking_datum=simulated_date)
        else:
            # No entitlement - reject (AWIR Art. 16 lid 4)
            case_manager.wijs_af(case_id=case_id, reden="Geen aanspraak op basis van berekening")

    case = case_manager.get_case_by_id(case_id)

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
                "error": "Er is een fout opgetreden bij het genereren van het aanvraagformulier. Probeer het later opnieuw.",
                "service": service,
                "law": law,
                "current_engine_id": get_engine_id(),
            },
        )
