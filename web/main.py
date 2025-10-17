import logging
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
from web.feature_flags import (
    is_change_wizard_enabled,
    is_chat_enabled,
    is_total_income_widget_enabled,
    is_wallet_enabled,
)
from web.routers import admin, chat, dashboard, edit, importer, laws, mcp, session, simulation, wallet

logger = logging.getLogger(__name__)

app = FastAPI(title="RegelRecht")

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
app.include_router(dashboard.router)
app.include_router(edit.router)
app.include_router(chat.router)
app.include_router(importer.router)
app.include_router(mcp.router)
app.include_router(session.router)
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
    # Store actor BSN in session for role management
    request.session["bsn"] = bsn

    # Determine which profile to show based on acting_as role
    acting_as = request.session.get("acting_as")
    if acting_as and acting_as.get("type") == "PERSON":
        # Acting as another person - show their profile
        display_bsn = acting_as["id"]
        profile = services.get_profile_data(display_bsn)
    elif acting_as and acting_as.get("type") == "ORGANIZATION":
        # Acting as organization - create organization profile with identifiers
        display_bsn = None
        rsin = acting_as["id"]

        # Get organization data from KVK services to find KVK_NUMMER
        org_data = None
        try:
            # Access KVK service - handle both raw dict and Services object
            kvk_service = None
            if hasattr(services, "services"):
                services_obj = services.services
                # Check if it's a Services object with nested services dict
                if hasattr(services_obj, "services") and isinstance(services_obj.services, dict):
                    kvk_service = services_obj.services.get("KVK")
                # Or if it's already a dict
                elif isinstance(services_obj, dict):
                    kvk_service = services_obj.get("KVK")

            if kvk_service and hasattr(kvk_service, "source_dataframes"):
                # Access bedrijven dataframe
                if "bedrijven" in kvk_service.source_dataframes:
                    df = kvk_service.source_dataframes["bedrijven"]
                    # Find organization by RSIN
                    matching_rows = df[df["rsin"] == rsin]
                    if not matching_rows.empty:
                        org_row = matching_rows.iloc[0]
                        org_data = org_row.to_dict()
        except Exception as e:
            logger.warning(f"Could not fetch organization data: {e}", exc_info=True)

        profile = {
            "naam": org_data.get("naam") if org_data else acting_as["name"],
            "rsin": rsin,
            "kvk_nummer": org_data.get("kvk_nummer") if org_data else None,
            "rechtsvorm": org_data.get("rechtsvorm") if org_data else None,
            "status": org_data.get("status") if org_data else None,
            "type": "ORGANIZATION",
        }
    else:
        # Acting as self
        display_bsn = bsn
        profile = services.get_profile_data(bsn)

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Get accepted cases for the display BSN (or skip for organizations)
    accepted_cases = []
    accepted_claims = {}
    if display_bsn:
        all_cases = case_manager.get_cases_by_bsn(display_bsn)
        accepted_cases = [case for case in all_cases if case.status.value == "DECIDED" and case.approved is True]

        # Build accepted_claims: {key: new_value} for claims belonging to accepted cases only
        for case in accepted_cases:
            claims = claim_manager.get_claim_by_bsn_service_law(
                display_bsn, case.service, case.law, approved=False
            )  # IMPROVE: use approved=True?
            if claims:
                for key, claim in claims.items():
                    accepted_claims[key] = claim.new_value

    # Get discoverable laws based on acting_as context
    if display_bsn:
        # Person context - show citizen laws sorted by impact
        discoverable_laws = services.get_sorted_discoverable_service_laws(display_bsn)
    else:
        # Organization context - show business laws (unsorted for now)
        business_laws_dict = services.get_discoverable_service_laws(discoverable_by="BUSINESS")
        # Flatten dict format {service: [laws]} to list format [{service: ..., law: ...}]
        discoverable_laws = [
            {"service": service, "law": law}
            for service in business_laws_dict
            for law in business_laws_dict[service]
        ]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "profile": profile,
            "bsn": display_bsn or bsn,  # BSN of the person whose data is shown
            "actor_bsn": bsn,  # BSN of the logged-in user (for DigiD profile selector)
            "formatted_date": FORMATTED_DATE,
            "all_profiles": services.get_all_profiles(),
            "discoverable_service_laws": discoverable_laws,
            "wallet_enabled": is_wallet_enabled(),
            "chat_enabled": is_chat_enabled(),
            "change_wizard_enabled": is_change_wizard_enabled(),
            "total_income_widget_enabled": is_total_income_widget_enabled(),
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
