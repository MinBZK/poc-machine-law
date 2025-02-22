from enum import Enum

from eventsourcing.domain import Aggregate, event
from eventsourcing.persistence import Transcoding


class CaseStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    DECIDED = "DECIDED"
    IN_REVIEW = "IN_REVIEW"
    OBJECTED = "OBJECTED"


class CaseStatusTranscoding(Transcoding):
    @staticmethod
    def can_handle(obj: object) -> bool:
        return isinstance(obj, CaseStatus | str)

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


Transcoding.register(CaseStatusTranscoding)


class Case(Aggregate):
    @event("Submitted")
    def __init__(
        self,
        bsn: str,
        service_type: str,
        law: str,
        parameters: dict,
        claimed_result: dict,
        rulespec_uuid: str,
    ) -> None:
        self.claim_ids = None
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

    @event("AutomaticallyDecided")
    def decide_automatically(self, verified_result: dict, parameters: dict, approved: bool) -> None:
        if self.status not in [CaseStatus.SUBMITTED, CaseStatus.OBJECTED]:
            raise ValueError("Can only automatically decide on submitted cases or objections")
        self.verified_result = verified_result
        self.parameters = parameters
        self.status = CaseStatus.DECIDED
        self.approved = approved

    @event("AddedToManualReview")
    def select_for_manual_review(
        self, verifier_id: str, reason: str, claimed_result: dict, verified_result: dict
    ) -> None:
        if self.status not in [CaseStatus.SUBMITTED, CaseStatus.OBJECTED]:
            raise ValueError("Can only add to review from submitted status or objection")
        self.status = CaseStatus.IN_REVIEW
        self.verified_result = verified_result
        self.claimed_result = claimed_result
        self.reason = reason
        self.verifier_id = verifier_id

    @event("Decided")
    def decide(self, verified_result: dict, reason: str, verifier_id: str, approved: bool) -> None:
        if self.status not in [CaseStatus.IN_REVIEW, CaseStatus.OBJECTED]:
            raise ValueError("Can only manually decide on cases in review or objections")
        self.status = CaseStatus.DECIDED
        self.approved = approved
        self.reason = reason
        self.verified_result = verified_result
        self.verifier_id = verifier_id

    @event("Objected")
    def object(self, reason: str) -> None:
        if self.status != CaseStatus.DECIDED:
            raise ValueError("Can only objection decided cases")
        self.status = CaseStatus.OBJECTED
        self.reason = reason

    @event("ObjectionStatusDetermined")
    def determine_objection_status(
        self,
        possible: bool | None = None,  # bezwaar_mogelijk
        not_possible_reason: str | None = None,  # reden_niet_mogelijk
        objection_period: int | None = None,  # bezwaartermijn in weeks
        decision_period: int | None = None,  # beslistermijn in weeks
        extension_period: int | None = None,
    ) -> None:  # verdagingstermijn in weeks
        """Determine the objection status and periods"""
        if not hasattr(self, "objection_status") or self.objection_status is None:
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

    @event("ObjectionAdmissibilityDetermined")
    def determine_objection_admissibility(self, admissible: bool | None = None) -> None:
        """Determine whether an objection is admissible (ontvankelijk)"""
        if not hasattr(self, "objection_status") or self.objection_status is None:
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
        if not hasattr(self, "objection_status") or self.objection_status is None:
            return False
        return bool(self.objection_status.get("possible", False))

    @event("AppealStatusDetermined")
    def determine_appeal_status(
        self,
        possible: bool | None = None,  # beroep_mogelijk
        not_possible_reason: str | None = None,  # reden_niet_mogelijk
        appeal_period: int | None = None,  # beroepstermijn in weeks
        direct_appeal: bool | None = None,  # direct beroep mogelijk
        direct_appeal_reason: str | None = None,  # reden voor direct beroep
        competent_court: str | None = None,  # bevoegde rechtbank
        court_type: str | None = None,  # type rechter
    ) -> None:
        """Determine the appeal status and periods for a case"""
        if not hasattr(self, "appeal_status") or self.appeal_status is None:
            self.appeal_status = {}

        updates = {}
        if possible is not None:
            updates["possible"] = possible
        if not_possible_reason is not None:
            updates["not_possible_reason"] = not_possible_reason
        if appeal_period is not None:
            updates["appeal_period"] = appeal_period
        if direct_appeal is not None:
            updates["direct_appeal"] = direct_appeal
        if direct_appeal_reason is not None:
            updates["direct_appeal_reason"] = direct_appeal_reason
        if competent_court is not None:
            updates["competent_court"] = competent_court
        if court_type is not None:
            updates["court_type"] = court_type

        self.appeal_status.update(updates)

    def can_appeal(self) -> bool:
        """
        Check if appeal is possible for this case.
        Returns False if:
        - appeal_status is not set
        - possible flag is not set
        - possible flag is explicitly set to False
        """
        if not hasattr(self, "appeal_status") or self.appeal_status is None:
            return False
        return bool(self.appeal_status.get("possible", False))

    @event("ClaimCreated")
    def add_claim(self, claim_id: str) -> None:
        """Record when a new claim is created for this case"""
        if not hasattr(self, "claim_ids") or self.claim_ids is None:
            self.claim_ids = set()
        self.claim_ids.add(claim_id)

    @event("ClaimApproved")
    def approve_claim(self, claim_id: str) -> None:
        """Record when a claim is approved"""
        if not hasattr(self, "claim_ids") or self.claim_ids is None:
            self.claim_ids = set()
        if claim_id not in self.claim_ids:
            self.claim_ids.add(claim_id)

    @event("ClaimRejected")
    def reject_claim(self, claim_id: str) -> None:
        """Record when a claim is rejected"""
        if not hasattr(self, "claim_ids") or self.claim_ids is None:
            self.claim_ids = set()
        if claim_id not in self.claim_ids:
            self.claim_ids.add(claim_id)
