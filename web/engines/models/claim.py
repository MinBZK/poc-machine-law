from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import UUID


@dataclass
class ClaimStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass
class Claim:
    """Claim"""

    id: UUID
    service: str
    key: str
    new_value: Any
    reason: str
    claimant: str
    law: str
    bsn: str
    status: ClaimStatus
    case_id: str | None = None
    old_value: Any | None = None
    evidence_path: str | None = None
