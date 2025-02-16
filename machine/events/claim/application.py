from typing import Any
from uuid import UUID

from eventsourcing.application import Application

from .aggregate import Claim, ClaimStatus


class ClaimManager(Application):
    """
    Application service for managing claims.
    Claims can be made against services, with optional case references.
    """

    def __init__(self, rules_engine, **kwargs) -> None:
        super().__init__(**kwargs)
        self.rules_engine = rules_engine
        # Various indexes for quick lookups
        self._service_index: dict[str, list[str]] = {}  # service -> [claim_ids]
        self._case_index: dict[str, list[str]] = {}  # case_id -> [claim_ids]
        self._claimant_index: dict[str, list[str]] = {}  # claimant -> [claim_ids]
        self._status_index: dict[ClaimStatus, list[str]] = {status: [] for status in ClaimStatus}
        self._bsn_service_law_index: dict[tuple[str, str, str], dict[str, str]] = {}  # (service, key) -> claim_id

    def _index_claim(self, claim: Claim) -> None:
        """Add claim to all indexes"""
        claim_id = str(claim.id)

        # Service index
        if claim.service not in self._service_index:
            self._service_index[claim.service] = []
        self._service_index[claim.service].append(claim_id)

        # Case index (if applicable)
        if claim.case_id:
            if claim.case_id not in self._case_index:
                self._case_index[claim.case_id] = []
            self._case_index[claim.case_id].append(claim_id)

        # Claimant index
        if claim.claimant not in self._claimant_index:
            self._claimant_index[claim.claimant] = []
        self._claimant_index[claim.claimant].append(claim_id)

        # Status index
        self._status_index[claim.status].append(claim_id)

        # Service-Key index
        if (claim.bsn, claim.service, claim.law) not in self._bsn_service_law_index:
            self._bsn_service_law_index[(claim.bsn, claim.service, claim.law)] = {}
        self._bsn_service_law_index[(claim.bsn, claim.service, claim.law)][claim.key] = claim_id

    def _update_status_index(self, claim: Claim, old_status: ClaimStatus) -> None:
        """Update status index when claim status changes"""
        claim_id = str(claim.id)
        self._status_index[old_status].remove(claim_id)
        self._status_index[claim.status].append(claim_id)

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
    ) -> str:
        """
        Submit a new claim. Can be linked to an existing case or standalone.
        """
        claim = Claim(
            service=service,
            key=key,
            new_value=new_value,
            reason=reason,
            claimant=claimant,
            case_id=case_id,
            old_value=old_value,
            evidence_path=evidence_path,
            law=law,
            bsn=bsn,
        )

        self.save(claim)
        self._index_claim(claim)
        return str(claim.id)

    def approve_claim(self, claim_id: str, verified_by: str, verified_value: Any) -> None:
        """Approve a claim with verified value"""
        claim = self.get_claim(claim_id)
        old_status = claim.status
        claim.approve(verified_by, verified_value)
        self.save(claim)
        self._update_status_index(claim, old_status)

    def reject_claim(self, claim_id: str, rejected_by: str, rejection_reason: str) -> None:
        """Reject a claim with reason"""
        claim = self.get_claim(claim_id)
        old_status = claim.status
        claim.reject(rejected_by, rejection_reason)
        self.save(claim)
        self._update_status_index(claim, old_status)

    def link_case(self, claim_id: str, case_id: str) -> None:
        """Link an existing claim to a case"""
        claim = self.get_claim(claim_id)
        claim.link_case(case_id)
        self.save(claim)

        # Update case index
        if case_id not in self._case_index:
            self._case_index[case_id] = []
        self._case_index[case_id].append(str(claim.id))

    def add_evidence(self, claim_id: str, evidence_path: str) -> None:
        """Add evidence to an existing claim"""
        claim = self.get_claim(claim_id)
        claim.add_evidence(evidence_path)
        self.save(claim)

    # Query methods
    def get_claim(self, claim_id: str) -> Claim:
        """Get claim by ID"""
        return self.repository.get(UUID(claim_id))

    def get_claims_by_service(self, service: str) -> list[Claim]:
        """Get all claims for a service"""
        return [self.get_claim(claim_id) for claim_id in self._service_index.get(service, [])]

    def get_claims_by_case(self, case_id: str) -> list[Claim]:
        """Get all claims for a case"""
        return [self.get_claim(claim_id) for claim_id in self._case_index.get(case_id, [])]

    def get_claims_by_claimant(self, claimant: str) -> list[Claim]:
        """Get all claims made by a claimant"""
        return [self.get_claim(claim_id) for claim_id in self._claimant_index.get(claimant, [])]

    def get_claims_by_status(self, status: ClaimStatus) -> list[Claim]:
        """Get all claims with a specific status"""
        return [self.get_claim(claim_id) for claim_id in self._status_index.get(status, [])]

    def get_claim_by_bsn_service_law(self, bsn: str, service: str, law: str) -> dict[str:Claim] | None:
        """
        Get a dictionary with claims
        """
        key_index = self._bsn_service_law_index.get((bsn, service, law))
        if key_index:
            return {key: self.get_claim(claim_id) for key, claim_id in key_index.items()}
        return None
