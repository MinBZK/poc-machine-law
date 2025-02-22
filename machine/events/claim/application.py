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
        self._bsn_index: dict[str, list[str]] = {}  # claimant -> [claim_ids]
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

        # BSN index
        if claim.bsn not in self._bsn_index:
            self._bsn_index[claim.bsn] = []
        self._bsn_index[claim.bsn].append(claim_id)

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

    @staticmethod
    def _filter_claims_by_approved(claims: list[Claim], approved: bool) -> list[Claim]:
        """
        Helper method to filter claims based on approved parameter.

        Args:
            claims: List of claims to filter
            approved: If True, only return approved claims. If False, return approved and submitted claims.
        """
        if approved:
            return [claim for claim in claims if claim.status == ClaimStatus.APPROVED]
        return [claim for claim in claims if claim.status in (ClaimStatus.APPROVED, ClaimStatus.PENDING)]

    def get_claims_by_service(self, service: str, approved: bool = False) -> list[Claim]:
        """Get all claims for a service, filtered by status"""
        claims = [self.get_claim(claim_id) for claim_id in self._service_index.get(service, [])]
        return self._filter_claims_by_approved(claims, approved)

    def get_claims_by_case(self, case_id: str, approved: bool = False) -> list[Claim]:
        """Get all claims for a case, filtered by status"""
        claims = [self.get_claim(claim_id) for claim_id in self._case_index.get(case_id, [])]
        return self._filter_claims_by_approved(claims, approved)

    def get_claims_by_claimant(self, claimant: str, approved: bool = False) -> list[Claim]:
        """Get all claims made by a claimant, filtered by status"""
        claims = [self.get_claim(claim_id) for claim_id in self._claimant_index.get(claimant, [])]
        return self._filter_claims_by_approved(claims, approved)

    def get_claims_by_bsn(self, bsn: str, approved: bool = False) -> list[Claim]:
        """Get all claims for a BSN, filtered by status"""
        claims = [self.get_claim(claim_id) for claim_id in self._bsn_index.get(bsn, [])]
        return self._filter_claims_by_approved(claims, approved)

    def get_claim_by_bsn_service_law(
        self, bsn: str, service: str, law: str, approved: bool = False
    ) -> dict[str:Claim] | None:
        """Get a dictionary with claims filtered by status"""
        key_index = self._bsn_service_law_index.get((bsn, service, law))
        if not key_index:
            return None
        claims = {key: self.get_claim(claim_id) for key, claim_id in key_index.items()}
        filtered_claims = {
            key: claim for key, claim in claims.items() if claim in self._filter_claims_by_approved([claim], approved)
        }
        return filtered_claims if filtered_claims else None
