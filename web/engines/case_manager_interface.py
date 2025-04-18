from abc import ABC, abstractmethod

from machine.events.case.aggregate import Case


class CaseManagerInterface(ABC):
    """
    Interface defining case management functionality.
    """

    @abstractmethod
    async def get_case(self, bsn: str, service: str, law: str) -> Case | None:
        """
        Retrieves case information based on provided parameters.

        Args:
            bsn: String identifier for the specific case
            service: String identifier for the service where the case is applicable
            law: String identifier for the law where the case is applicable

        Returns:
            A Case containing the case information
        """

    async def get_cases_by_law(self, service: str, law: str) -> list[Case]:
        """
        Retrieves case information based on provided parameters.

        Args:
            service: String identifier for the service where the case is applicable
            law: String identifier for the law where the case is applicable

        Returns:
            All Cases containing the case information filtered on service & law
        """
