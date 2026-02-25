from enum import StrEnum


class CaseStatus(StrEnum):
    DECIDED = "DECIDED"
    IN_REVIEW = "IN_REVIEW"
    OBJECTED = "OBJECTED"
    SUBMITTED = "SUBMITTED"

    def __str__(self) -> str:
        return str(self.value)
