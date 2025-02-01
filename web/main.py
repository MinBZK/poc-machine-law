# web/main.py
import locale
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from machine.service import Services
from web.dependencies import FORMATTED_DATE, get_services
from web.routers import laws
from web.services.profiles import get_profile_data, get_all_profiles

# Set Dutch locale
locale.setlocale(locale.LC_TIME, 'nl_NL.UTF-8')

app = FastAPI(title="Burger.nl")

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Mount static directory if it exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include routers
app.include_router(laws.router)


@app.get("/")
async def root(request: Request, bsn: str = "999993653",
               services: Services = Depends(get_services)):
    """Render the main dashboard page"""
    profile = get_profile_data(bsn)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "profile": profile,
            "bsn": bsn,
            "formatted_date": FORMATTED_DATE,
            "all_profiles": get_all_profiles(),
            "discoverable_service_laws": services.get_discoverable_service_laws()
        }
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
