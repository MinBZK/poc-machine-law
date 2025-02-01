# web/routers/laws.py

from pathlib import Path
from urllib.parse import unquote

import pandas as pd
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates

from machine.service import Services
from web.dependencies import TODAY, FORMATTED_DATE, get_services
from web.services.profiles import get_profile_data

router = APIRouter(prefix="/laws", tags=["laws"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


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


@router.get("/execute")
async def execute_law(
        request: Request,
        service: str,
        law: str,
        bsn: str,
        services: Services = Depends(get_services)
):
    # try:
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

    if law == "kieswet":
        pass

    return templates.TemplateResponse(
        "partials/law_result.html",
        {
            "request": request,
            "law": law,
            "service": service,
            "rule_spec": rule_spec,
            "result": result.output,
            "requirements_met": result.requirements_met
        }
    )

    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))
