from eventsourcing.application import Application
from eventsourcing.domain import Aggregate, event
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from uuid import UUID

from claims.aggregate import Claim, ClaimStatus


class ClaimsManager(Application):
    def __init__(self):
        super().__init__()
        self.ruleset_rules = {}  # Default rules by ruleset
        # Enkele index voor (law, service, bsn) -> claim_id
        self._claim_index: Dict[Tuple[str, str, str], str] = {}

    def _index_key(self, law: str, service: str, subject_id: str) -> Tuple[str, str, str]:
        """Genereer een index key voor de combinatie van law, service en subject_id"""
        return (law, service, subject_id)

    def _index_claim(self, claim: Claim):
        """Voeg een claim toe aan de index"""
        key = self._index_key(claim.law, claim.service, claim.subject_id)
        self._claim_index[key] = claim.id

    def submit_claim(self, subject_id: str, law: str, service: str,
                     ruleset_uuid: UUID, details: Dict) -> str:
        """Submit a new claim"""
        claim = Claim(subject_id, law, service, ruleset_uuid, details)
        self.save(claim)
        self._index_claim(claim)
        return claim.id

    def verify_claim(self, claim_id: str, verifier_id: str, decision: bool,
                     reason: str, appeal_window_days: Optional[int] = None):
        """Verify a claim and optionally set appeal window"""
        claim = self.repository.get(claim_id)
        claim.verify(verifier_id, decision, reason)

        if not decision and appeal_window_days is not None:
            claim.add_meta_claim('appeal_window', appeal_window_days, verifier_id)
        elif not decision and str(claim.ruleset_uuid) in self.ruleset_rules:
            rule = self.ruleset_rules[str(claim.ruleset_uuid)].get('appeal_window')
            if rule:
                claim.add_meta_claim('appeal_window', rule['value'], rule['authority'])

        self.save(claim)

    def get_claim(self, law: str, service: str, subject_id: str) -> Optional[Claim]:
        """Get claim for specific law, service and subject combination"""
        key = self._index_key(law, service, subject_id)
        claim_id = self._claim_index.get(key)
        return self.repository.get(claim_id) if claim_id else None

    def submit_appeal(self, claim_id: str, reason: str, new_evidence: Optional[Dict] = None):
        """Submit an appeal for a denied claim"""
        claim = self.repository.get(claim_id)
        claim.submit_appeal(reason, new_evidence)
        self.save(claim)

    def verify_appeal(self, claim_id: str, verifier_id: str, decision: bool, reason: str):
        """Verify an appeal"""
        claim = self.repository.get(claim_id)
        claim.verify_appeal(verifier_id, decision, reason)
        self.save(claim)

    def add_meta_claim(self, claim_id: str, claim_type: str, value: any,
                       authority: str, additional_info: Optional[Dict] = None):
        """Add a meta claim to a specific claim"""
        claim = self.repository.get(claim_id)
        claim.add_meta_claim(claim_type, value, authority, additional_info)
        self.save(claim)

    def add_evidence(self, claim_id: str, document_id: str,
                     document_type: str, description: str):
        """Add evidence to a claim"""
        claim = self.repository.get(claim_id)
        claim.add_evidence(document_id, document_type, description)
        self.save(claim)

    def check_appeal_eligibility(self, claim_id: str) -> Dict:
        """Check if a claim can be appealed"""
        claim = self.repository.get(claim_id)
        return {
            'eligible': claim.can_appeal(),
            'status': claim.status
        }


# Usage example:
def main():
    from uuid import uuid4

    manager = ClaimsManager()

    # Set default appeal window for a ruleset
    ruleset_id = uuid4()

    # Submit a new claim
    claim_id = manager.submit_claim(
        subject_id="123456789",
        law="housing_act_2024",
        service="housing_assistance",
        ruleset_uuid=ruleset_id,
        details={
            "monthly_income": 2500,
            "rent_amount": 1200,
            "household_size": 3,
            "address": "123 Main St"
        }
    )

    # Add supporting evidence
    manager.add_evidence(
        claim_id=claim_id,
        document_id="doc123",
        document_type="income_statement",
        description="Latest pay stubs"
    )

    # Add priority meta-claim
    manager.add_meta_claim(
        claim_id=claim_id,
        claim_type="priority",
        value="high",
        authority="CLAIMS_DEPT",
        additional_info={"reason": "Hardship case"}
    )

    # Deny the claim
    manager.verify_claim(
        claim_id=claim_id,
        verifier_id="VERIFIER_001",
        decision=False,
        reason="Income exceeds threshold for household size"
    )

    # Check appeal eligibility
    eligibility = manager.check_appeal_eligibility(claim_id)
    if eligibility['eligible']:
        # Submit appeal
        manager.submit_appeal(
            claim_id=claim_id,
            reason="Recent job loss affects income calculation",
            new_evidence={
                "termination_letter": "doc456",
                "new_income_statement": "doc789"
            }
        )

        # Verify appeal
        manager.verify_appeal(
            claim_id=claim_id,
            verifier_id="APPEALS_001",
            decision=True,
            reason="New circumstances warrant approval"
        )


if __name__ == "__main__":
    main()
