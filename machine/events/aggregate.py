from enum import Enum
from enum import Enum
from typing import Dict, List

from eventsourcing.domain import Aggregate, event
from eventsourcing.persistence import Transcoding


class CaseStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    DECIDED = "DECIDED"
    IN_REVIEW = "IN_REVIEW"
    APPEALED = "APPEALED"


class ClaimStatusTranscoding(Transcoding):
    @staticmethod
    def can_handle(obj: object) -> bool:
        return isinstance(obj, (CaseStatus, str))

    @staticmethod
    def encode(obj: CaseStatus) -> str:
        if isinstance(obj, str):
            return obj
        return obj.value

    @staticmethod
    def decode(data: str) -> str:
        if isinstance(data, CaseStatus):
            return data.value
        return data  # Keep it as a string


Transcoding.register(ClaimStatusTranscoding)


# Helper function for consistent status access
def get_status_value(status) -> str:
    """Get string value of status regardless of type"""
    if isinstance(status, CaseStatus):
        return status.value
    return status


class ServiceCase(Aggregate):
    @event('Submitted')
    def __init__(self,
                 bsn: str,
                 service_type: str,
                 law: str,
                 parameters: Dict,
                 claimed_result: Dict,
                 rulespec_uuid: str):
        self.bsn = bsn
        self.service = service_type
        self.law = law
        self.rulespec_uuid = rulespec_uuid

        self.claimed_result = claimed_result
        self.verified_result = None
        self.parameters = parameters
        self.disputed_parameters = None
        self.evidence = None
        self.reason = None
        self.verifier_id = None

        self.approved = None
        self.status = CaseStatus.SUBMITTED

    @event('AutomaticallyDecided')
    def add_automatic_decision(self,
                               verified_result: Dict,
                               parameters: Dict,
                               approved: bool):
        if self.status not in [CaseStatus.SUBMITTED, CaseStatus.APPEALED]:
            raise ValueError("Can only automatically decide on submitted cases or appeals")
        self.verified_result = verified_result
        self.parameters = parameters
        self.status = CaseStatus.DECIDED
        self.approved = approved

    @event('AddedToManualReview')
    def add_to_manual_review(self,
                             verifier_id: str,
                             reason: str,
                             claimed_result: Dict,
                             verified_result: Dict):
        if self.status not in [CaseStatus.SUBMITTED, CaseStatus.APPEALED]:
            raise ValueError("Can only add to review from submitted status or appeal")
        self.status = CaseStatus.IN_REVIEW
        self.verified_result = verified_result
        self.claimed_result = claimed_result
        self.reason = reason
        self.verifier_id = verifier_id

    @event('Decided')
    def add_manual_decision(self,
                            verified_result: Dict,
                            reason: str,
                            verifier_id: str, approved: bool):
        if self.status not in [CaseStatus.IN_REVIEW, CaseStatus.APPEALED]:
            raise ValueError("Can only manually decide on cases in review or appeals")
        self.status = CaseStatus.DECIDED
        self.approved = approved
        self.reason = reason
        self.verified_result = verified_result
        self.verifier_id = verifier_id

    @event('Appealed')
    def add_appeal(self,
                   reason: str):
        if self.status != CaseStatus.DECIDED:
            raise ValueError("Can only appeal decided cases")
        self.status = CaseStatus.APPEALED
        self.reason = reason
