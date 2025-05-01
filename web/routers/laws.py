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


async def evaluate_law(
    bsn: str, law: str, service: str, machine_service: EngineInterface, approved: bool = True
) -> tuple[str, RuleResult, dict[str, Any]]:
    """Evaluate a law for a given BSN"""

    parameters = {"BSN": bsn}

    # Execute the law using EngineInterface
    result = await machine_service.evaluate(
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
    case_manager: CaseManagerInterface = Depends(get_case_manager),
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """Execute a law and render its result"""
    try:
        law = unquote(law)
        law, result, parameters = await evaluate_law(bsn, law, service, machine_service, approved=False)

    except Exception as e:
        print(e)
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
    existing_case = await case_manager.get_case(bsn, service, law)

    # Get the appropriate template
    template_path = get_tile_template(service, law)

    rule_spec = await machine_service.get_rule_spec(law, TODAY, service)

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
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """Submit a new case"""
    law = unquote(law)

    law, result, parameters = await evaluate_law(bsn, law, service, machine_service, approved=approved)

    case_id = await case_manager.submit_case(
        bsn=bsn,
        service=service,
        law=law,
        parameters=parameters,
        claimed_result=result.output,
        approved_claims_only=approved,
    )

    case = await case_manager.get_case_by_id(case_id)

    rule_spec = await machine_service.get_rule_spec(law, TODAY, service)

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
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """Submit an objection for an existing case"""
    # First calculate the new result with disputed parameters
    law = unquote(law)

    # Submit the objection with new claimed result
    case_id = await case_manager.objection_case(
        case_id=case_id,
        reason=reason,
    )

    law, result, parameters = await evaluate_law(bsn, law, service, machine_service)

    template_path = get_tile_template(service, law)

    return templates.TemplateResponse(
        template_path,
        {
            "bsn": bsn,
            "request": request,
            "law": law,
            "service": service,
            "rule_spec": await machine_service.get_rule_spec(law, TODAY, service),
            "result": result.output,
            "input": result.input,
            "requirements_met": result.requirements_met,
            "current_case": await case_manager.get_case_by_id(case_id),
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
    approved: bool = False,  # Add this parameter
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """Get a citizen-friendly explanation of the rule evaluation path"""
    try:
        law = unquote(law)
        law, result, parameters = await evaluate_law(bsn, law, service, machine_service, approved=approved)

        # Convert path and rule_spec to JSON strings
        path_dict = node_to_dict(result.path, skip_services=True)
        path_json = json.dumps(path_dict, ensure_ascii=False, indent=2)

        rule_spec = await machine_service.get_rule_spec(law, TODAY, service)

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

        # Get explanation from LLM using factory to select the configured provider
        llm_service = llm_factory.get_service()
        explanation = llm_service.generate_explanation(path_json, rule_spec_json)

        return templates.TemplateResponse(
            "partials/tiles/components/explanation.html",
            {
                "request": request,
                "explanation": explanation,
            },
        )
    except Exception as e:
        print(f"Error in explain_path: {e}")
        return templates.TemplateResponse(
            "partials/tiles/components/explanation.html",
            {
                "request": request,
                "error": "Er is een fout opgetreden bij het genereren van de uitleg. Probeer het later opnieuw.",
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
        law, result, parameters = await evaluate_law(bsn, law, service, machine_service, approved=approved)

        value_tree = machine_service.extract_value_tree(result.path)
        existing_case = await case_manager.get_case(bsn, service, law)

        claims = await claim_manager.get_claims_by_bsn(bsn, include_rejected=True)
        claim_map = {(claim.service, claim.law, claim.key): claim for claim in claims}

        rule_spec = await machine_service.get_rule_spec(law, TODAY, service)

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
            },
        )
