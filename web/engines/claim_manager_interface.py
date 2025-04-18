from abc import ABC, abstractmethod
from typing import Any


class ClaimManagerInterface(ABC):
    """
    Interface defining case management functionality.
    """

    @abstractmethod
    async def get_claims_by_bsn(self, bsn: str, approved: bool = False, include_rejected: bool = False) -> Any | None:
        """
        Retrieves case information based on bsn.

        Args:
            bsn: Citizen identifier
            include_rejected: include rejected claims

        Returns:
            A Case containing the case information
        """

    @abstractmethod
    async def get_claim_by_bsn_service_law(
        self, bsn: str, service: str, law: str, approved: bool = False, include_rejected: bool = False
    ) -> Any | None:
        """
        Retrieves case information based on provided parameters.

        Args:
            bsn: Citizen identifier
            service: Service provider code (e.g., "TOESLAGEN")
            law: Law identifier (e.g., "zorgtoeslagwet")
            include_rejected: include rejected claims

        Returns:
            A Case containing the case information
        """

    @abstractmethod
    async def submit_claim(
        self,
        service: str,
        key: str,
        new_value: Any,
        reason: str,
        claimant: str,
        law: str,
        bsn: str,
        case_id: str | None = None,
        old_value: Any | None = None,
        evidence_path: str | None = None,
        auto_approve: bool = False,  # Add this parameter
    ) -> str:
        """
        Submit a new claim. Can be linked to an existing case or standalone.
        If auto_approve is True, the claim will be automatically approved.

        Args:
            service:

        Returns:
            A ClaimID

        """

    @abstractmethod
    async def reject_claim(self, claim_id: str, rejected_by: str, rejection_reason: str) -> None:
        """
        Reject a claim with reason

        Args:
            claim_id: Identifier of the claim
            rejected_by: User that rejected the claim
            rejection_reason: Reason of the rejection

        Returns:
            None
        """

    @abstractmethod
    async def approve_claim(
        self,
        claim_id: str,
        verified_by: str,
        verified_value: Any,
    ) -> None:
        """
        Approve a claim with verified value

        Args:
            claim_id: Identifier of the claim
            verified_by: User that verified the claim
            verified_value: Verified value

        Returns:
            None
        """
