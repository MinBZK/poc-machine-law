from abc import ABC, abstractmethod
from typing import Any


class MachineInterface(ABC):
    """
    Interface for machine law evaluation services.
    Abstracts the underlying implementation (Python or Go).
    """

    @abstractmethod
    async def get_rule_spec(self, law: str, reference_date: str, service: str) -> dict[str, Any]:
        """
        Get the rule specification for a specific law.

        Args:
            law: Law identifier
            reference_date: Reference date for rule version (YYYY-MM-DD)
            service: Service provider code (e.g., "TOESLAGEN")

        Returns:
            Dictionary containing the rule specification
        """

    @abstractmethod
    async def get_profile_data(self, bsn: str) -> dict[str, Any]:
        """
        Get profile data for a specific BSN.

        Args:
            bsn: BSN identifier for the individual

        Returns:
            Dictionary containing profile data or None if not found
        """

    @abstractmethod
    async def get_all_profiles(self) -> dict[str, dict[str, Any]]:
        """
        Get all available profiles.

        Returns:
            Dictionary mapping BSNs to profile data
        """

    @abstractmethod
    async def evaluate(
        self,
        service: str,
        law: str,
        parameters: dict[str, Any],
        reference_date: str | None = None,
        overwrite_input: dict[str, Any] | None = None,
        requested_output: str | None = None,
        approved: bool = False,
    ) -> dict[str, Any]:
        """
        Evaluate rules for given law and reference date.

        Args:
            service: Service provider code (e.g., "TOESLAGEN")
            law: Name of the law (e.g., "zorgtoeslagwet")
            parameters: Context data for service provider
            reference_date: Reference date for rule version (YYYY-MM-DD)
            overwrite_input: Optional overrides for input values
            requested_output: Optional specific output field to calculate
            approved: Whether this evaluation is for an approved claim

        Returns:
            Dictionary containing evaluation results
        """

    @abstractmethod
    async def get_discoverable_service_laws(self, discoverable_by="CITIZEN") -> dict[str, list[str]]:
        """
        Get laws discoverable by citizens.

        Returns:
            Dictionary mapping service names to lists of law names
        """

    @abstractmethod
    async def get_sorted_discoverable_service_laws(self, bsn: str) -> list[dict[str, Any]]:
        """
        Return laws discoverable by citizens, sorted by impact for this specific person.

        Args:
            bsn: BSN identifier for the individual

        Returns:
            List of dictionaries containing service, law, and impact information
        """

    @abstractmethod
    def extract_value_tree(root) -> Any:
        """
        Return the extracted value tree

        Args:
            root: Root of the value tree

        Returns:
            A flattend list of all entries
        """
