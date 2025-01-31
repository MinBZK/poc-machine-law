# web/main.py
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from web.routers import laws

app = FastAPI(title="Machine Law Demo")

# Setup static and template directories
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Include routers
app.include_router(laws.router)

@app.get("/")
async def root(request: Request):
    """Render the main dashboard page"""
    return templates.TemplateResponse("index.html", {"request": request})
