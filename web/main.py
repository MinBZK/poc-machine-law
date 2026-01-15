import sys
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

sys.path.append(str(Path(__file__).parent.parent))

from web.dependencies import (
    STATIC_DIR,
    get_case_manager,
    get_claim_manager,
    get_machine_service,
    templates,
)
from web.engines import CaseManagerInterface, ClaimManagerInterface, EngineInterface
from web.engines.http_engine.machine_client.regel_recht_engine_api_client.errors import UnexpectedStatus
from web.feature_flags import (
    is_change_wizard_enabled,
    is_chat_enabled,
    is_delegation_enabled,
    is_effective_date_adjustment_enabled,
    is_total_income_widget_enabled,
    is_wallet_enabled,
)
from web.routers import admin, chat, dashboard, delegation, demo, edit, importer, laws, mcp, simulation, wallet

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
app.include_router(demo.router)
app.include_router(edit.router)
app.include_router(chat.router)
app.include_router(importer.router)
app.include_router(mcp.router)
app.include_router(wallet.router)
app.include_router(simulation.router)
app.include_router(delegation.router)

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
app.mount(
    "/nl-wallet-files",
    StaticFiles(
        directory="nl-wallet-files",
        html=True,
    ),
)


@app.get("/")
async def root(
    request: Request,
    bsn: str = "100000001",
    date: str = None,
    services: EngineInterface = Depends(get_machine_service),
    case_manager: CaseManagerInterface = Depends(get_case_manager),
    claim_manager: ClaimManagerInterface = Depends(get_claim_manager),
):
    """Render the main dashboard page"""
    # Get the profile
    try:
        effective_date = datetime.strptime(date, "%Y-%m-%d") if date else datetime.now()
    except ValueError:
        effective_date = datetime.now()

    try:
        profile = services.get_profile_data(bsn, effective_date=effective_date.date())
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
    except UnexpectedStatus as e:
        error_message = e.content.decode("utf-8") if e.content else "No response content"
        # Log the exception for debugging
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"UnexpectedStatus caught in main.py: status_code={e.status_code}, content={error_message}")

        # Instead of raising HTTPException, return an error template
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_title": "Verbindingsfout",
                "error_message": f"Kan geen verbinding maken met de server: {error_message}",
                "error_details": "Controleer of de backend service actief is en probeer het opnieuw.",
                "bsn": bsn,
            },
            status_code=500,
        )
    except Exception as e:
        # Catch any other exceptions for debugging
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected exception in main.py: {type(e).__name__}: {e}", exc_info=True)

        # Return error template for any exception
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_title": "Onverwachte fout",
                "error_message": f"Er is een onverwachte fout opgetreden: {str(e)}",
                "error_details": "Probeer het later opnieuw of neem contact op met de beheerder.",
                "bsn": bsn,
            },
            status_code=500,
        )

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

    # Get delegation context from session
    delegation_context = None
    delegations = []
    if is_delegation_enabled():
        from machine.delegation.manager import DelegationManager
        from web.routers.delegation import DELEGATION_SESSION_KEY

        session_data = request.session.get(DELEGATION_SESSION_KEY)
        if session_data:
            from machine.delegation.models import DelegationContext

            delegation_context = DelegationContext.from_dict(session_data)

        # Get available delegations for the user
        try:
            delegation_manager = DelegationManager(services.get_services())
            delegations = delegation_manager.get_delegations_for_user(bsn)
        except Exception:
            pass  # Delegation service not available

    # Determine discoverable type based on delegation context
    discoverable_by = "CITIZEN"
    if delegation_context and delegation_context.subject_type == "BUSINESS":
        discoverable_by = "BUSINESS"

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "profile": profile,
            "bsn": bsn,
            "all_profiles": services.get_all_profiles(),
            "discoverable_service_laws": services.get_sorted_discoverable_service_laws(
                bsn, discoverable_by=discoverable_by
            ),
            "wallet_enabled": is_wallet_enabled(),
            "chat_enabled": is_chat_enabled(),
            "change_wizard_enabled": is_change_wizard_enabled(),
            "adjustable_effective_date_enabled": is_effective_date_adjustment_enabled(),
            "total_income_widget_enabled": is_total_income_widget_enabled(),
            "delegation_enabled": is_delegation_enabled(),
            "delegation_context": delegation_context,
            "delegations": delegations,
            "accepted_claims": accepted_claims,
            "now": datetime.now(),
            "effective_date": effective_date,  # Pass the parsed date parameter to the template
        },
    )


if __name__ == "__main__":
    import uvicorn

    # Use single worker for demo mode to maintain in-memory state
    # Multiple workers would have separate memory spaces, breaking the _test_runs dictionary
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        workers=1,
        reload=False,
    )
    server = uvicorn.Server(config)
    server.run()
