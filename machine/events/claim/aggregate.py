from datetime import datetime
from enum import Enum
from typing import Any

from eventsourcing.domain import Aggregate, event
from eventsourcing.persistence import Transcoding


class ClaimStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ClaimStatusTranscoding(Transcoding):
    @staticmethod
    def can_handle(obj: object) -> bool:
        return isinstance(obj, ClaimStatus)

    @staticmethod
    def encode(obj: ClaimStatus) -> str:
        return obj.value

    @staticmethod
    def decode(data: str) -> ClaimStatus:
        return ClaimStatus(data)


Transcoding.register(ClaimStatusTranscoding)


class Claim(Aggregate):
    @event("Created")
    def __init__(
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
    ) -> None:
        self.service = service
        self.key = key
        self.old_value = old_value
        self.new_value = new_value
        self.reason = reason
        self.evidence_path = evidence_path
        self.claimant = claimant
        self.case_id = case_id
        self.law = law
        self.bsn = bsn
        self.status = ClaimStatus.PENDING
        self.created_at = datetime.now()

    @event("Approved")
    def approve(self, verified_by: str, verified_value: Any) -> None:
        """Approve the claim with potentially adjusted value"""
        self.status = ClaimStatus.APPROVED
        self.verified_by = verified_by
        self.verified_value = verified_value
        self.verified_at = datetime.now()

    @event("Rejected")
    def reject(self, rejected_by: str, rejection_reason: str) -> None:
        """Reject the claim with a reason"""
        self.status = ClaimStatus.REJECTED
        self.rejected_by = rejected_by
        self.rejection_reason = rejection_reason
        self.rejected_at = datetime.now()

    @event("CaseLinked")
    def link_case(self, case_id: str) -> None:
        """Link this claim to a case"""
        if self.case_id is not None:
            raise ValueError("Claim is already linked to a case")
        self.case_id = case_id

    @event("EvidenceAdded")
    def add_evidence(self, evidence_path: str) -> None:
        """Add evidence to the claim"""
        if self.status != ClaimStatus.PENDING:
            raise ValueError("Can only add evidence to pending claims")
        self.evidence_path = evidence_path
