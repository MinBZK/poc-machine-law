from typing import Any

import httpx

from ..claim_manager_interface import ClaimManagerInterface
from .machine_client.law_as_code_client import Client
from .machine_client.law_as_code_client.api.claim import get_claims_bsn, get_claims_bsn_service_law


class ClaimManager(ClaimManagerInterface):
    """
    Implementation of ClaimManagerInterface that uses the embedded Python machine.service library.
    """

    def __init__(self, base_url: str = "http://localhost:8081/v0"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=self.base_url)

    async def get_claims_by_bsn(self, bsn: str, approved: bool = False, include_rejected: bool = False) -> Any | None:
        """
        Retrieves case information using the embedded Python machine.service library.

        Args:
            bsn: BSN identifier for the individual
            service: Service provider code (e.g., "TOESLAGEN")
            law: Law identifier (e.g., "zorgtoeslagwet")

        Returns:
            Case object if found, None otherwise
        """

        # Instantiate the API client
        client = Client(base_url=self.base_url)

        with client as client:
            response = get_claims_bsn.sync_detailed(
                client=client, bsn=bsn, approved=approved, include_rejected=include_rejected
            )
            content = response.parsed

            return content.data

    async def get_claim_by_bsn_service_law(
        self, bsn: str, service: str, law: str, approved: bool = False, include_rejected: bool = False
    ) -> Any | None:
        """
        Retrieves case information using the embedded Python machine.service library.

        Args:
            bsn: BSN identifier for the individual
            service: Service provider code (e.g., "TOESLAGEN")
            law: Law identifier (e.g., "zorgtoeslagwet")

        Returns:
            Case object if found, None otherwise
        """

        # Instantiate the API client
        client = Client(base_url=self.base_url)

        with client as client:
            response = get_claims_bsn_service_law.sync_detailed(
                client=client, bsn=bsn, service=service, law=law, approved=approved, include_rejected=include_rejected
            )
            content = response.parsed

            return content.data

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

        return self.claim_manager.reject_claim(
            claim_id,
            rejected_by,
            rejection_reason,
        )

    async def approve_claim(self, claim_id: str, verified_by: str, verified_value: str) -> None:
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
