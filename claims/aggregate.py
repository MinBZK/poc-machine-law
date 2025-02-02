from eventsourcing.domain import Aggregate, event
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, List
from dataclasses import dataclass
from uuid import UUID


class ClaimStatus(Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    APPEALED = "APPEALED"
    APPEAL_APPROVED = "APPEAL_APPROVED"
    APPEAL_DENIED = "APPEAL_DENIED"


@dataclass
class Evidence:
    document_id: str
    document_type: str
    uploaded_at: datetime
    description: str


class Claim(Aggregate):
    @event('ClaimSubmitted')
    def __init__(self, subject_id: str, law: str, service: str, rulespec_uuid: UUID, details: Dict):
        self.subject_id = subject_id
        self.law = law
        self.service = service
        self.rulespec_uuid = rulespec_uuid
        self.details = details
        self.status = ClaimStatus.SUBMITTED
        self.submitted_at = datetime.now()
        self.decisions = []
        self.appeals = []
        self.meta_claims = {}
        self.evidence = []

    @event('ClaimVerified')
    def verify(self, verifier_id: str, decision: bool, reason: str):
        self.status = ClaimStatus.APPROVED if decision else ClaimStatus.DENIED
        self.decisions.append({
            'verifier_id': verifier_id,
            'decision': decision,
            'reason': reason,
            'verified_at': datetime.now()
        })

    @event('AppealSubmitted')
    def submit_appeal(self, reason: str, new_evidence: Optional[Dict] = None):
        if self.status != ClaimStatus.DENIED:
            raise ValueError("Can only appeal denied claims")

        if not self.can_appeal():
            raise ValueError("Appeal window has expired")

        self.status = ClaimStatus.APPEALED
        self.appeals.append({
            'reason': reason,
            'new_evidence': new_evidence,
            'submitted_at': datetime.now()
        })

    @event('AppealVerified')
    def verify_appeal(self, verifier_id: str, decision: bool, reason: str):
        self.status = ClaimStatus.APPEAL_APPROVED if decision else ClaimStatus.APPEAL_DENIED
        self.appeals[-1].update({
            'verifier_id': verifier_id,
            'decision': decision,
            'reason': reason,
            'verified_at': datetime.now()
        })

    @event('MetaClaimAdded')
    def add_meta_claim(self, claim_type: str, value: any, authority: str, additional_info: Optional[Dict] = None):
        self.meta_claims[claim_type] = {
            'type': claim_type,
            'value': value,
            'authority': authority,
            'created_at': datetime.now(),
            **(additional_info if additional_info else {})
        }

    @event('EvidenceAdded')
    def add_evidence(self, document_id: str, document_type: str, description: str):
        evidence = Evidence(
            document_id=document_id,
            document_type=document_type,
            uploaded_at=datetime.now(),
            description=description
        )
        self.evidence.append(evidence)

    def can_appeal(self) -> bool:
        if self.status != ClaimStatus.DENIED:
            return False

        if 'appeal_window' not in self.meta_claims:
            return True  # No window specified means always possible

        last_decision = self.decisions[-1]
        appeal_window = self.meta_claims['appeal_window']
        deadline = last_decision['verified_at'] + timedelta(days=appeal_window['value'])
        return datetime.now() <= deadline
