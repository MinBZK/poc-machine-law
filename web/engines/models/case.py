from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID


class CaseStatus(str, Enum):
    # Application review states
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    DECIDED = "DECIDED"
    OBJECTED = "OBJECTED"

    # Toeslag lifecycle states (AWIR process)
    BEREKEND = "BEREKEND"  # Aanspraak berekend (AWIR Art. 16 lid 1)
    VOORSCHOT = "VOORSCHOT"  # Voorschotbeschikking vastgesteld (AWIR Art. 16)
    LOPEND = "LOPEND"  # Maandelijkse cyclus actief
    DEFINITIEF = "DEFINITIEF"  # Definitieve beschikking (AWIR Art. 19)
    VEREFFEND = "VEREFFEND"  # Vereffening uitgevoerd (AWIR Art. 24, 26a)
    AFGEWEZEN = "AFGEWEZEN"  # Aanvraag afgewezen (AWIR Art. 16 lid 4)
    BEEINDIGD = "BEEINDIGD"  # Toeslag beëindigd


@dataclass
class CaseObjectionStatus:
    """CaseObjectionStatus"""

    possible: bool | None = None
    not_possible_reason: str | None = None
    objection_period: int | None = None
    decision_period: int | None = None
    extension_period: int | None = None
    admissable: bool | None = None


@dataclass
class Case:
    """Case"""

    id: UUID
    bsn: str
    service: str
    law: str
    rulespec_uuid: UUID
    approved_claims_only: bool
    status: CaseStatus
    parameters: dict[str, Any] = field(default_factory=dict)
    claimed_result: dict[str, Any] = field(default_factory=dict)
    verified_result: dict[str, Any] = field(default_factory=dict)
    objection_status: CaseObjectionStatus | None = None
    appeal_status: dict[str, Any] = field(default_factory=dict)
    approved: bool | None = None

    def can_object(self) -> bool:  # TODO: FIX
        if self.objection_status is None:
            return False

        return self.objection_status.possible

    def can_appeal(self) -> bool:
        if self.appeal_status is None:
            return False

        return self.appeal_status.get("possible", False)
