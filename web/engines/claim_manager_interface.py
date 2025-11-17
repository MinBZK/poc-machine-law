from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from .models import Claim


class ClaimManagerInterface(ABC):
    """
    Interface defining case management functionality.
    """

    @abstractmethod
    def get_claims_by_bsn(self, bsn: str, approved: bool = False, include_rejected: bool = False, effective_date: str | None = None) -> list[Claim]:
        """
        Retrieves case information based on bsn.

        Args:
            bsn: Citizen identifier
            include_rejected: include rejected claims
            effective_date: Optional effective date in YYYY-MM-DD format

        Returns:
            A Case containing the case information
        """

    @abstractmethod
    def get_claim_by_bsn_service_law(
        self, bsn: str, service: str, law: str, approved: bool = False, include_rejected: bool = False, effective_date: str | None = None
    ) -> dict[UUID:Claim]:
        """
        Retrieves case information based on provided parameters.

        Args:
            bsn: Citizen identifier
            service: Service provider code (e.g., "TOESLAGEN")
            law: Law identifier (e.g., "zorgtoeslagwet")
            include_rejected: include rejected claims
            effective_date: Optional effective date in YYYY-MM-DD format

        Returns:
            A Case containing the case information
        """

    @abstractmethod
    def submit_claim(
        self,
        service: str,
        key: str,
        new_value: Any,
        reason: str,
        claimant: str,
        law: str,
        bsn: str,
        case_id: UUID | None = None,
        old_value: Any | None = None,
        evidence_path: str | None = None,
        auto_approve: bool = False,  # Add this parameter
    ) -> UUID:
        """
        Submit a new claim. Can be linked to an existing case or standalone.
        If auto_approve is True, the claim will be automatically approved.

        Args:
            service:

        Returns:
            A ClaimID

        """

    @abstractmethod
    def reject_claim(self, claim_id: UUID, rejected_by: str, rejection_reason: str) -> None:
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
    def approve_claim(
        self,
        claim_id: UUID,
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
