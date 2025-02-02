# web/main.py

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles

from machine.service import Services
from web.dependencies import FORMATTED_DATE, get_services, STATIC_DIR, templates
from web.routers import admin
from web.routers import laws
from web.services.profiles import get_profile_data, get_all_profiles

app = FastAPI(title="Burger.nl")

# Mount static directory if it exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include routers
app.include_router(laws.router)
app.include_router(admin.router)


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
    import uvicorn
    from multiprocessing import cpu_count

    # Use half the available CPU cores (a common practice)
    n_workers = cpu_count() // 2

    # Ensure at least 1 worker
    n_workers = max(n_workers, 1)

    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        workers=n_workers,
        reload=True,
    )
    server = uvicorn.Server(config)
    server.run()
