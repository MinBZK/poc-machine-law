"""API endpoints for the wallet module."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from web.feature_flags import is_wallet_enabled
from web.services.wallet import get_wallet_data

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("/get-data")
async def get_data(bsn: str, request: Request, service: str = None, law: str = None):
    """Get data from user's wallet for the specified BSN, service and law.

    This endpoint returns wallet data for the specified BSN, optionally filtered by service and law.
    """
    # Check if wallet feature is enabled
    if not is_wallet_enabled():
        return JSONResponse(
            status_code=403, content={"success": False, "message": "Wallet feature is currently disabled"}
        )

    # Get wallet data from our mock wallet data service
    wallet_data = get_wallet_data(bsn, service, law)

    if wallet_data:
        return JSONResponse(content={"success": True, "data": wallet_data})

    return JSONResponse(content={"success": False, "message": "No wallet data found for this BSN"})
