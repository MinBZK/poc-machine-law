from urllib.parse import unquote
import pandas as pd
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from typing import Optional

from machine.service import Services
from web.dependencies import TODAY, FORMATTED_DATE, get_services, templates
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
    except:
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
        services: Services = Depends(get_services)
):
    """Execute a law and render its result"""
    try:
        law = unquote(law)
        law, result, rule_spec = await evaluate_law(bsn, law, service, services)
    except Exception as e:
        return templates.TemplateResponse(
            get_tile_template(service, law),
            {
                "request": request,
                "bsn": bsn,
                "law": law,
                "service": service,
                "rule_spec": {"name": law.split('/')[-1].replace('_', ' ').title()},
                "error": True
            }
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
            "current_case": existing_case
        }
    )


@router.post("/submit-case")
async def submit_case(
        request: Request,
        service: str,
        law: str,
        bsn: str,
        services: Services = Depends(get_services)
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
        claimed_result=result.output  # The citizen claims the calculated result
    )

    template_path = get_tile_template(service, law)

    # Return the updated law result with the new case
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
            "current_case": services.manager.get_case_by_id(case_id)
        }
    )


@router.post("/appeal-case")
async def appeal_case(
        request: Request,
        case_id: str,
        service: str,
        law: str,
        bsn: str,
        disputed_parameters: dict,
        evidence: list,
        reasoning: str,
        services: Services = Depends(get_services)
):
    """Submit an appeal for an existing case"""
    # First calculate the new result with disputed parameters
    law = unquote(law)
    disputed_parameters.update({"BSN": bsn})  # Ensure BSN is included
    result = await services.evaluate(service, law, disputed_parameters, TODAY)

    # Submit the appeal with new claimed result
    case_id = services.manager.appeal_case(
        case_id=case_id,
        disputed_parameters=disputed_parameters,
        evidence=evidence,
        reasoning=reasoning,
        claimed_result=result.output
    )

    template_path = get_tile_template(service, law)

    return templates.TemplateResponse(
        template_path,
        {
            "bsn": bsn,
            "request": request,
            "law": law,
            "service": service,
            "current_case": services.manager.get_case_by_id(case_id)
        }
    )
