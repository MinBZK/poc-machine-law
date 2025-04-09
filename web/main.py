import sys
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles

sys.path.append(str(Path(__file__).parent.parent))

from machine.service import Services
from web.dependencies import FORMATTED_DATE, STATIC_DIR, get_services, templates
from web.routers import admin, chat, edit, importer, laws
from web.services.profiles import get_all_profiles, get_profile_data

app = FastAPI(title="Burger.nl")

# Mount static directory if it exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include routers
app.include_router(laws.router)
app.include_router(admin.router)
app.include_router(edit.router)
app.include_router(chat.router)
app.include_router(importer.router)
app.mount("/analysis/graph/law", StaticFiles(directory="law"))
app.mount(
    "/analysis/graph",
    StaticFiles(
        # directory=f"{os.path.dirname(os.path.realpath(__file__))}/../analysis/graph/build",  # Note: absolute path is required when follow_symlink=True
        directory="analysis/graph/build",
        html=True,
    ),
)
app.mount(
    "/importer",
    StaticFiles(
        directory="importer/build",
        html=True,
    ),
)


@app.get("/")
async def root(
    request: Request,
    bsn: str = "100000001",
    acting_as: str = None,
    acting_as_bsn: str = None,
    relationship_type: str = None,
    services: Services = Depends(get_services),
):
    """Render the main dashboard page"""
    profile = get_profile_data(bsn)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Load representative information if needed
    representative_info = None
    if acting_as and acting_as_bsn:
        representative_profile = get_profile_data(acting_as_bsn)
        if representative_profile:
            representative_info = {
                "name": acting_as,
                "bsn": acting_as_bsn,
                "relationship_type": relationship_type,
            }

    await laws.set_profile_data(bsn, services)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "profile": profile,
            "bsn": bsn,
            "formatted_date": FORMATTED_DATE,
            "all_profiles": get_all_profiles(),
            "discoverable_service_laws": await services.get_sorted_discoverable_service_laws(bsn),
            "representative_info": representative_info,
        },
    )


if __name__ == "__main__":
    from multiprocessing import cpu_count

    import uvicorn

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
