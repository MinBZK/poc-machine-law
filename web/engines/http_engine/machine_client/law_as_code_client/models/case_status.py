from enum import Enum


class CaseStatus(str, Enum):
    DECIDED = "DECIDED"
    IN_REVIEW = "IN_REVIEW"
    OBJECTED = "OBJECTED"
    SUBMITTED = "SUBMITTED"

    def __str__(self) -> str:
        return str(self.value)
