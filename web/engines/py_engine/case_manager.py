from machine.events.case.aggregate import Case
from machine.service import Services

from ..case_manager_interface import CaseManagerInterface


class CaseManager(CaseManagerInterface):
    """
    Implementation of CaseManagerInterface that uses the embedded Python machine.service library.
    """

    def __init__(self, services: Services):
        self.services = services
        self.case_manager = services.case_manager

    async def get_case(self, bsn: str, service: str, law: str) -> Case | None:
        """
        Retrieves case information using the embedded Python machine.service library.

        Args:
            bsn: BSN identifier for the individual
            service: Service provider code (e.g., "TOESLAGEN")
            law: Law identifier (e.g., "zorgtoeslagwet")

        Returns:
            Case object if found, None otherwise
        """
        return self.case_manager.get_case(bsn, service, law)

    async def get_cases_by_law(self, service: str, law: str) -> list[Case]:
        return self.case_manager.get_cases_by_law(service, law)
