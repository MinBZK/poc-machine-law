# web/main.py
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from datetime import datetime

from web.routers import laws
from web.services.profiles import get_profile_data

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
async def root(request: Request):
    """Render the main dashboard page"""
    initial_bsn = "999993653"
    profile = get_profile_data(initial_bsn)
    formatted_date = datetime.today().strftime("%-d %B %Y")  # e.g. "31 januari 2025"
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "profile": profile,
            "bsn": initial_bsn,
            "formatted_date": formatted_date
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
