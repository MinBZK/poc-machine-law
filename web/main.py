import sys
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

sys.path.append(str(Path(__file__).parent.parent))

from web.dependencies import (
    FORMATTED_DATE,
    STATIC_DIR,
    get_case_manager,
    get_claim_manager,
    get_machine_service,
    templates,
)
from web.engines import CaseManagerInterface, ClaimManagerInterface, EngineInterface
from web.feature_flags import is_chat_enabled, is_wallet_enabled
from web.routers import admin, chat, edit, importer, laws, mcp, simulation, wallet

app = FastAPI(title="Burger.nl")

# Add session middleware with a secure secret key and max age of 7 days
# In production, this should be stored securely and not in the code
app.add_middleware(
    SessionMiddleware,
    secret_key="machine-law-session-secret-key",
    max_age=7 * 24 * 60 * 60,  # 7 days in seconds
    same_site="lax",  # Allow cookies to be sent in first-party context
    https_only=False,  # Allow HTTP for development
)

# Mount static directory if it exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include routers
app.include_router(laws.router)
app.include_router(admin.router)
app.include_router(edit.router)
app.include_router(chat.router)
app.include_router(importer.router)
app.include_router(mcp.router)
app.include_router(wallet.router)
app.include_router(simulation.router)

app.mount("/analysis/laws/law", StaticFiles(directory="law"))
# app.mount(
#     "/analysis/laws",
#     StaticFiles(
#         # directory=f"{os.path.dirname(os.path.realpath(__file__))}/../analysis/laws/build",  # Note: absolute path is required when follow_symlink=True
#         directory="analysis/laws/build",
#         html=True,
#     ),
# )


@app.get("/analysis/laws/", response_class=FileResponse)
def analysis_laws_index():
    return FileResponse("analysis/laws/build/index.html")


@app.get("/analysis/laws/{catchall:path}", response_class=FileResponse)
def analysis_laws_fallback(request: Request):
    # Prevent path traversal by resolving the absolute path and checking its parent
    base_dir = Path("analysis/laws/build").resolve()
    requested_path = (base_dir / request.path_params["catchall"]).resolve()

    if base_dir in requested_path.parents and requested_path.exists():
        return FileResponse(str(requested_path))

    # Fallback to the index file
    return FileResponse(str(base_dir / "index.html"))


app.mount("/analysis/graph/law", StaticFiles(directory="law"))
app.mount(
    "/analysis/graph",
    StaticFiles(
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
    services: EngineInterface = Depends(get_machine_service),
    case_manager: CaseManagerInterface = Depends(get_case_manager),
    claim_manager: ClaimManagerInterface = Depends(get_claim_manager),
):
    """Render the main dashboard page"""
    profile = services.get_profile_data(bsn)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Get accepted cases for this BSN
    all_cases = case_manager.get_cases_by_bsn(bsn)
    accepted_cases = [case for case in all_cases if case.status.value == "DECIDED" and case.approved is True]

    # Build accepted_claims: {key: new_value} for claims belonging to accepted cases only
    accepted_claims = {}
    for case in accepted_cases:
        claims = claim_manager.get_claim_by_bsn_service_law(
            bsn, case.service, case.law, approved=False
        )  # IMPROVE: use approved=True?
        if claims:
            for key, claim in claims.items():
                accepted_claims[key] = claim.new_value

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "profile": profile,
            "bsn": bsn,
            "formatted_date": FORMATTED_DATE,
            "all_profiles": services.get_all_profiles(),
            "discoverable_service_laws": services.get_sorted_discoverable_service_laws(bsn),
            "wallet_enabled": is_wallet_enabled(),
            "chat_enabled": is_chat_enabled(),
            "accepted_claims": accepted_claims,
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
