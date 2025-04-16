from typing import Any

import httpx

from ..case_manager import CaseManagerInterface


class CaseManager(CaseManagerInterface):
    """
    Implementation of CaseManagerInterface that uses HTTP calls to the Go backend service.
    """

    def __init__(self, base_url: str = "http://localhost:8081/v0"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=self.base_url)

    async def get_case(self, bsn: str, service: str, law: str) -> dict[str, Any] | None:
        """
        Retrieves case information using HTTP calls to the Go backend service.

        Args:
            bsn: BSN identifier for the individual
            service: Service provider code (e.g., "TOESLAGEN")
            law: Law identifier (e.g., "zorgtoeslagwet")

        Returns:
            Dictionary containing case data if found, None otherwise
        """
        try:
            # Construct the API endpoint based on your Go backend API structure
            endpoint = f"/cases/{bsn}"

            # Add query parameters for service and law
            params = {"service": service, "law": law}

            # Make the request to the Go backend
            response = await self.client.get(endpoint, params=params)

            # Handle response
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                # Log error and return None
                print(f"Error getting case: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            # Log the exception
            print(f"Exception getting case: {str(e)}")
            return None

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)
