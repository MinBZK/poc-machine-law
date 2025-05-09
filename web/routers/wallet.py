"""API endpoints for the wallet module."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from web.engines.py_engine.services.profiles import get_profile_data

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("/get-data")
async def get_wallet_data(bsn: str, request: Request, service: str = None, law: str = None):
    """Get data from user's wallet for the specified BSN, service and law.

    This is a generic endpoint that returns wallet data regardless of service or law.
    """

    # Debug information
    print(f"Retrieving wallet data for BSN={bsn}, service={service}, law={law}")

    profile = get_profile_data(bsn)

    if not profile:
        print(f"Profile not found for BSN={bsn}")
        return JSONResponse(content={"success": False, "message": "Profile not found"})

    # Get wallet data directly from the profile root
    if "wallet_data" in profile:
        wallet_data = profile["wallet_data"]
        print(f"Found wallet data: {wallet_data}")

        # If service/law are specified, filter the data
        if service and law and isinstance(wallet_data, dict):
            service_key = service.lower()
            law_key = law.lower().replace("-", "_")

            # Try to find matching service and law keys
            filtered_data = {}

            # First try exact match
            if service_key in wallet_data and law_key in wallet_data[service_key]:
                filtered_data = wallet_data[service_key][law_key]
            # Then try just the service
            elif service_key in wallet_data:
                filtered_data = wallet_data[service_key]

            if filtered_data:
                print(f"Returning filtered wallet data for {service}/{law}")
                return JSONResponse(content={"success": True, "data": filtered_data})

        # If no service/law specified or no match found, return all wallet data
        print("Returning all wallet data")
        return JSONResponse(content={"success": True, "data": wallet_data})

    # No wallet data found
    print(f"No wallet data found for BSN {bsn}")
    return JSONResponse(content={"success": False, "message": "No wallet data found"})
