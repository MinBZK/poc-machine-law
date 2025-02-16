import json
from urllib.parse import unquote

import pandas as pd
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from jinja2 import TemplateNotFound

from explain.llm_service import llm_service
from machine.context import flatten_path_nodes
from machine.service import Services
from web.dependencies import TODAY, get_services, templates
from web.services.profiles import get_profile_data

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


async def evaluate_law(bsn: str, law: str, service: str, services: Services):
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

    # Execute the law
    result = await services.evaluate(service, law=law, parameters={"BSN": bsn}, reference_date=TODAY)
    return law, result, rule_spec


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
        law, result, rule_spec = await evaluate_law(bsn, law, service, services)
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
    existing_case = services.manager.get_case(bsn, service, law)

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
            "current_case": existing_case,
        },
    )


@router.post("/submit-case")
async def submit_case(
    request: Request,
    service: str,
    law: str,
    bsn: str,
    services: Services = Depends(get_services),
):
    """Submit a new case"""
    law = unquote(law)

    law, result, rule_spec = await evaluate_law(bsn, law, service, services)

    # Submit the case with citizen's claimed result (from execution)
    case_id = await services.manager.submit_case(
        bsn=bsn,
        service_type=service,
        law=law,
        parameters=result.input,
        claimed_result=result.output,  # The citizen claims the calculated result
    )
    case = services.manager.get_case_by_id(case_id)

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
    case_id = services.manager.objection_case(
        case_id=case_id,
        reason=reason,
    )

    law, result, rule_spec = await evaluate_law(bsn, law, service, services)

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
            "current_case": services.manager.get_case_by_id(case_id),
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


@router.get("/explain-panel")
async def explain_panel(
    request: Request,
    service: str,
    law: str,
    bsn: str,
    services: Services = Depends(get_services),
):
    """Get an explanation panel"""
    try:
        law = unquote(law)
        law, result, rule_spec = await evaluate_law(bsn, law, service, services)
        flat_path = flatten_path_nodes(result.path)
        return templates.TemplateResponse(
            "partials/tiles/components/explanation_panel.html",
            {
                "request": request,
                "service": service,
                "law": law,
                "rule_spec": rule_spec,
                "input": result.input,
                "result": result.output,
                "requirements_met": result.requirements_met,
                "path": flat_path,
                "bsn": bsn,
            },
        )
    except Exception as e:
        print(f"Error in explain_path: {e}")
        return templates.TemplateResponse(
            "partials/tiles/components/explanation_panel.html",
            {
                "request": request,
                "error": "Er is een fout opgetreden bij het genereren van de uitleg. Probeer het later opnieuw.",
                "service": service,
                "law": law,
            },
        )


@router.get("/explanation")
async def explanation(
    request: Request,
    service: str,
    law: str,
    bsn: str,
    services: Services = Depends(get_services),
):
    """Get a citizen-friendly explanation of the rule evaluation path"""
    try:
        law = unquote(law)
        law, result, rule_spec = await evaluate_law(bsn, law, service, services)

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
