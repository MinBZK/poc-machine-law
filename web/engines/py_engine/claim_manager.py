from typing import Any
from uuid import UUID

from machine.regelrecht_services import RegelrechtServices

from ..claim_manager_interface import ClaimManagerInterface
from ..models import Claim


class ClaimManager(ClaimManagerInterface):
    """
    Implementation of ClaimManagerInterface that uses the embedded Python machine.service library.
    """

    def __init__(self, services: RegelrechtServices):
        self.claim_manager = services.claim_manager

    def get_claims_by_bsn(self, bsn: str, approved: bool = False, include_rejected: bool = False) -> list[Claim]:
        """
        Retrieves case information using the embedded Python machine.service library.

        Args:
            bsn: BSN identifier for the individual
            approved: If True, only return approved claims
            include_rejected: If True, also include rejected claims

        Returns:
            List of claims matching the criteria
        """
        claims = self.claim_manager.get_claims_by_bsn(bsn, approved, include_rejected)
        return claims

    def get_claim_by_bsn_service_law(
        self, bsn: str, service: str, law: str, approved: bool = False, include_rejected: bool = False
    ) -> dict[UUID:Claim]:
        """
        Retrieves claims filtered by BSN, service, and law.

        Args:
            bsn: BSN identifier for the individual
            service: Service provider code (e.g., "TOESLAGEN")
            law: Law identifier (e.g., "zorgtoeslagwet")
            approved: If True, only return approved claims
            include_rejected: If True, also include rejected claims

        Returns:
            Dictionary of claims keyed by claim key
        """
        return self.claim_manager.get_claim_by_bsn_service_law(bsn, service, law, approved, include_rejected)

    def submit_claim(
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
    ) -> UUID:
        """
        Submit a new claim. Can be linked to an existing case or standalone.
        If auto_approve is True, the claim will be automatically approved.

        Args:
            service:

        Returns:
            A ClaimID
        """
        return self.claim_manager.submit_claim(
            service,
            key,
            new_value,
            reason,
            claimant,
            law,
            bsn,
            case_id,
            old_value,
            evidence_path,
            auto_approve,
        )

    def reject_claim(self, claim_id: str, rejected_by: str, rejection_reason: str) -> None:
        """
        Reject a claim with reason

        Args:
            claim_id: Identifier of the claim
            rejected_by: User that rejected the claim
            rejection_reason: Reason of the rejection

        Returns:
            None
        """

        return self.claim_manager.reject_claim(
            claim_id,
            rejected_by,
            rejection_reason,
        )

    def approve_claim(self, claim_id: str, verified_by: str, verified_value: str) -> None:
        """
        Approve a claim with verified value

        Args:
            claim_id: Identifier of the claim
            verified_by: User that verified the claim
            verified_value: Verified value

        Returns:
            None
        """

        return self.claim_manager.approve_claim(
            claim_id,
            verified_by,
            verified_value,
        )


def to_claim(claim) -> Claim:
    return Claim(
        id=claim.id,
        service=claim.service,
        key=claim.key,
        new_value=claim.new_value,
        reason=claim.reason,
        claimant=claim.claimant,
        law=claim.law,
        bsn=claim.bsn,
        status=claim.status,
        case_id=claim.case_id,
        old_value=claim.old_value,
        evidence_path=claim.evidence_path,
    )


def to_claims(claims: list[Any]) -> list[Claim]:
    return [to_claim(item) for item in claims]


def to_dict_claims(claims: dict[UUID:Any]) -> dict[UUID:Claim]:
    return {k: to_claim(item) for k, item in claims.items()}
