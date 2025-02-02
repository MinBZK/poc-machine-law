from fastapi import APIRouter, Request, Depends, HTTPException
from urllib.parse import unquote
import pandas as pd
from pathlib import Path

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

    # We'll let Jinja handle the template existence check
    # If the specific template doesn't exist, it will raise a TemplateNotFound exception
    try:
        templates.get_template(specific_template)
        return specific_template
    except:
        return "partials/tiles/fallback_tile.html"


@router.get("/profile/")
async def switch_profile(request: Request, bsn: str = "999993653"):
    """Handle profile switching"""
    profile = get_profile_data(bsn)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return templates.TemplateResponse(
        "partials/dashboard.html",
        {
            "request": request,
            "profile": profile,
            "bsn": bsn,
            "formatted_date": FORMATTED_DATE
        }
    )


async def evaluate_law(bsn, law, service, services):
    # Decode the law path
    law = unquote(law)

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
    result = await services.evaluate(
        service,
        law=law,
        reference_date=TODAY,
        parameters={"BSN": bsn}
    )
    return law, result, rule_spec


@router.get("/execute")
async def execute_law(
        request: Request,
        service: str,
        law: str,
        bsn: str,
        services: Services = Depends(get_services)
):
    """Execute a law and render its result using the appropriate template"""
    try:
        law, result, rule_spec = await evaluate_law(bsn, law, service, services)
    except Exception as e:
        # Return error state using the same template
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

    # Check if there's an existing claim
    existing_claims = services.manager.get_claim(law, service, bsn)

    # Get the appropriate template for this law
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
            "current_claim": existing_claims
        }
    )


@router.post("/submit-claim")
async def submit_claim(
        request: Request,
        service: str,
        law: str,
        bsn: str,
        services: Services = Depends(get_services)
):
    """Submit a new claim for a law"""
    law, result, rule_spec = await evaluate_law(bsn, law, service, services)

    # Create a new claim
    claim_id = services.manager.submit_claim(
        subject_id=bsn,
        law=law,
        service=service,
        rulespec_uuid=rule_spec.get('uuid'),
        details={
            "calculation_date": TODAY,
            "calculated_amount": result.output.get("hoogte_toeslag") if "hoogte_toeslag" in result.output else None,
            "requirements_met": result.requirements_met,
            "input_parameters": result.input
        }
    )

    # Get the appropriate template for this law
    template_path = get_tile_template(service, law)

    # Return the updated law result with the new claim
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
            "current_claim": services.manager.repository.get(claim_id)
        }
    )
