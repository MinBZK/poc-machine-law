from enum import Enum
from enum import Enum
from typing import Dict, List, Optional

from eventsourcing.domain import Aggregate, event
from eventsourcing.persistence import Transcoding


class CaseStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    DECIDED = "DECIDED"
    IN_REVIEW = "IN_REVIEW"
    OBJECTED = "OBJECTED"


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
        self.objection_status = None

        self.approved = None
        self.status = CaseStatus.SUBMITTED

    @event('AutomaticallyDecided')
    def decide_automatically(self,
                             verified_result: Dict,
                             parameters: Dict,
                             approved: bool):
        if self.status not in [CaseStatus.SUBMITTED, CaseStatus.OBJECTED]:
            raise ValueError("Can only automatically decide on submitted cases or objections")
        self.verified_result = verified_result
        self.parameters = parameters
        self.status = CaseStatus.DECIDED
        self.approved = approved

    @event('AddedToManualReview')
    def select_for_manual_review(self,
                                 verifier_id: str,
                                 reason: str,
                                 claimed_result: Dict,
                                 verified_result: Dict):
        if self.status not in [CaseStatus.SUBMITTED, CaseStatus.OBJECTED]:
            raise ValueError("Can only add to review from submitted status or objection")
        self.status = CaseStatus.IN_REVIEW
        self.verified_result = verified_result
        self.claimed_result = claimed_result
        self.reason = reason
        self.verifier_id = verifier_id

    @event('Decided')
    def decide(self,
               verified_result: Dict,
               reason: str,
               verifier_id: str, approved: bool):
        if self.status not in [CaseStatus.IN_REVIEW, CaseStatus.OBJECTED]:
            raise ValueError("Can only manually decide on cases in review or objections")
        self.status = CaseStatus.DECIDED
        self.approved = approved
        self.reason = reason
        self.verified_result = verified_result
        self.verifier_id = verifier_id

    @event('Objected')
    def object(self,
               reason: str):
        if self.status != CaseStatus.DECIDED:
            raise ValueError("Can only objection decided cases")
        self.status = CaseStatus.OBJECTED
        self.reason = reason

    @event('ObjectionStatusDetermined')
    def determine_objection_status(self,
                                   possible: Optional[bool] = None,  # bezwaar_mogelijk
                                   not_possible_reason: Optional[str] = None,  # reden_niet_mogelijk
                                   objection_period: Optional[int] = None,  # bezwaartermijn in weeks
                                   decision_period: Optional[int] = None,  # beslistermijn in weeks
                                   extension_period: Optional[int] = None):  # verdagingstermijn in weeks
        """Determine the objection status and periods"""
        if not hasattr(self, 'objection_status') or self.objection_status is None:
            self.objection_status = {}

        updates = {}
        if possible is not None:
            updates["possible"] = possible
        if not_possible_reason is not None:
            updates["not_possible_reason"] = not_possible_reason
        if objection_period is not None:
            updates["objection_period"] = objection_period
        if decision_period is not None:
            updates["decision_period"] = decision_period
        if extension_period is not None:
            updates["extension_period"] = extension_period

        self.objection_status.update(updates)

    @event('ObjectionAdmissibilityDetermined')
    def determine_objection_admissibility(self, admissible: Optional[bool] = None):
        """Determine whether an objection is admissible (ontvankelijk)"""
        if not hasattr(self, 'objection_status') or self.objection_status is None:
            self.objection_status = {}

        if admissible is not None:
            self.objection_status["admissible"] = admissible

    def can_object(self) -> bool:
        """
        Check if objection is possible for this case.
        Returns False if:
        - objection_status is not set
        - possible flag is not set
        - possible flag is explicitly set to False
        """
        if not hasattr(self, 'objection_status') or self.objection_status is None:
            return False
        return bool(self.objection_status.get('possible', False))
