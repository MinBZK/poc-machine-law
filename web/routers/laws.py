import json
from urllib.parse import unquote

import pandas as pd
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from jinja2 import TemplateNotFound

from explain.llm_service import llm_service
from machine.service import Services
from web.dependencies import TODAY, get_services, templates
from web.services.profiles import get_profile_data
import os
from fastapi.responses import JSONResponse

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


async def evaluate_law(bsn: str, law: str, service: str, services: Services, approved: bool = True):
    """Evaluate a law for a given BSN"""
    # Get the rule specification
    rule_spec = services.resolver.get_rule_spec(law, TODAY, service)
    if not rule_spec:
        raise HTTPException(status_code=400, detail="Invalid law specified")

    # Get profile data for the BSN
    profile_data = get_profile_data(bsn)
    if not profile_data:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Load source data into services
    for service_name, tables in profile_data["sources"].items():
        for table_name, data in tables.items():
            df = pd.DataFrame(data)
            services.set_source_dataframe(service_name, table_name, df)

    parameters = {"BSN": bsn}

    # Execute the law
    result = await services.evaluate(service, law=law, parameters=parameters, reference_date=TODAY, approved=approved)
    return law, result, rule_spec, parameters

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
    services: Services = Depends(get_services),
):
    """Execute a law and render its result"""
    try:
        law = unquote(law)
        law, result, rule_spec, parameters = await evaluate_law(bsn, law, service, services, approved=False)
    except Exception:
        return templates.TemplateResponse(
            get_tile_template(service, law),
            {
                "request": request,
                "bsn": bsn,
                "law": law,
                "service": service,
                "rule_spec": {"name": law.split("/")[-1].replace("_", " ").title()},
                "error": True,
            },
        )

    # Check if there's an existing case
    existing_case = services.case_manager.get_case(bsn, service, law)

    # Get the appropriate template
    template_path = get_tile_template(service, law)

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
    services: Services = Depends(get_services),
):
    """Submit a new case"""
    law = unquote(law)

    law, result, rule_spec, parameters = await evaluate_law(bsn, law, service, services, approved=approved)

    case_id = await services.case_manager.submit_case(
        bsn=bsn,
        service_type=service,
        law=law,
        parameters=parameters,
        claimed_result=result.output,
        approved_claims_only=approved,
    )
    case = services.case_manager.get_case_by_id(case_id)

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
    services: Services = Depends(get_services),
):
    """Submit an objection for an existing case"""
    # First calculate the new result with disputed parameters
    law = unquote(law)

    # Submit the objection with new claimed result
    case_id = services.case_manager.objection_case(
        case_id=case_id,
        reason=reason,
    )

    law, result, rule_spec, parameters = await evaluate_law(bsn, law, service, services)

    template_path = get_tile_template(service, law)

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
            "current_case": services.case_manager.get_case_by_id(case_id),
        },
    )


def node_to_dict(node):
    """Convert PathNode to serializable dict"""
    if node is None:
        return None
    return {
        "type": node.type,
        "name": node.name,
        "result": str(node.result),
        "details": {k: str(v) for k, v in node.details.items()},
        "children": [node_to_dict(child) for child in node.children],
    }


@router.get("/explanation")
async def explanation(
    request: Request,
    service: str,
    law: str,
    bsn: str,
    approved: bool = False,  # Add this parameter
    services: Services = Depends(get_services),
):
    """Get a citizen-friendly explanation of the rule evaluation path"""
    try:
        law = unquote(law)
        law, result, rule_spec, parameters = await evaluate_law(bsn, law, service, services, approved=approved)

        # Convert path and rule_spec to JSON strings
        path_dict = node_to_dict(result.path)
        path_json = json.dumps(path_dict, ensure_ascii=False, indent=2)

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

        # Get explanation from LLM
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
    services: Services = Depends(get_services),
):
    """Get the application panel with tabs"""
    try:
        law = unquote(law)
        law, result, rule_spec, parameters = await evaluate_law(bsn, law, service, services, approved=approved)
        value_tree = services.extract_value_tree(result.path)
        existing_case = services.case_manager.get_case(bsn, service, law)

        claims = services.claim_manager.get_claims_by_bsn(bsn, include_rejected=True)
        claim_map = {(claim.service, claim.law, claim.key): claim for claim in claims}

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
