import urllib.parse

import httpx

from machine.events.case.aggregate import Case

from ..case_manager_interface import CaseManagerInterface
from .machine_client.law_as_code_client import Client
from .machine_client.law_as_code_client.api.case import get_cases_bsn_service_law, get_cases_service_law


class CaseManager(CaseManagerInterface):
    """
    Implementation of CaseManagerInterface that uses HTTP calls to the Go backend service.
    """

    def __init__(self, base_url: str = "http://localhost:8081/v0"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=self.base_url)

    async def get_case(self, bsn: str, service: str, law: str) -> Case | None:
        """
        Retrieves case information using HTTP calls to the Go backend service.

        Args:
            bsn: BSN identifier for the individual
            service: Service provider code (e.g., "TOESLAGEN")
            law: Law identifier (e.g., "zorgtoeslagwet")

        Returns:
            Dictionary containing case data if found, None otherwise
        """

        # Instantiate the API client
        client = Client(base_url=self.base_url)

        with client as client:
            response = get_cases_bsn_service_law.sync_detailed(
                client=client, bsn=bsn, service=service, law=urllib.parse.quote_plus(law)
            )
            if response.status_code == 404:
                return None

            content = response.parsed
            return content.data

    async def get_cases_by_law(self, service: str, law: str) -> list[Case]:
        """
        Retrieves case information using HTTP calls to the Go backend service.

        Args:
            bsn: BSN identifier for the individual
            service: Service provider code (e.g., "TOESLAGEN")
            law: Law identifier (e.g., "zorgtoeslagwet")

        Returns:
            Dictionary containing case data if found, None otherwise
        """

        # Instantiate the API client
        client = Client(base_url=self.base_url)

        with client as client:
            response = get_cases_service_law.sync_detailed(client=client, service=service, law=law)
            content = response.parsed

            return content.data

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)
