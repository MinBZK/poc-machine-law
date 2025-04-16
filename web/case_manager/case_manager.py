from abc import ABC, abstractmethod
from typing import Any


class CaseManagerInterface(ABC):
    """
    Interface defining case management functionality.
    """

    @abstractmethod
    async def get_case(self, bsn: str, service: str, law: str) -> Any | None:
        """
        Retrieves case information based on provided parameters.

        Args:
            bsn: String identifier for the specific case
            service: String identifier for the user requesting the case
            law: String providing additional context for the request

        Returns:
            A Case containing the case information
        """
