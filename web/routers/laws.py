# web/routers/laws.py
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from pathlib import Path
import pandas as pd

from machine.service import Services
from web.services.profiles import get_profile_data, get_all_profiles

router = APIRouter(prefix="/laws", tags=["laws"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


async def get_services():
    """Dependency to get Services instance"""
    return Services("2025-01-31")  # Current date


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
            "bsn": bsn
        }
    )
    """Handle profile switching"""
    profile = get_profile_data(bsn)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return templates.TemplateResponse(
        "partials/dashboard.html",
        {
            "request": request,
            "profile": profile,
            "bsn": bsn
        }
    )


@router.get("/execute/{law}")
async def execute_law(
        request: Request,
        law: str,
        bsn: str,
        services: Services = Depends(get_services)
):
    """Execute a specific law for a user"""
    try:
        # Get profile data for the BSN
        profile_data = get_profile_data(bsn)
        if not profile_data:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Load source data into services
        for service_name, tables in profile_data["sources"].items():
            for table_name, data in tables.items():
                df = pd.DataFrame(data)
                services.set_source_dataframe(service_name, table_name, df)

        # Map law name to service and actual law name
        law_mapping = {
            "zorgtoeslag": ("TOESLAGEN", "zorgtoeslagwet"),
            "aow": ("SVB", "algemene_ouderdomswet"),
            "bijstand": ("GEMEENTE_AMSTERDAM", "participatiewet/bijstand"),
        }

        if law not in law_mapping:
            raise HTTPException(status_code=400, detail="Invalid law specified")

        service_name, law_name = law_mapping[law]

        # Execute the law
        result = await services.evaluate(
            service_name,
            law=law_name,
            reference_date="2025-01-31",
            parameters={"BSN": bsn}
        )

        return templates.TemplateResponse(
            "partials/law_result.html",
            {
                "request": request,
                "law": law,
                "result": result.output,
                "requirements_met": result.requirements_met
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
