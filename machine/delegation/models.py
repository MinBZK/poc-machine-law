"""Data models for the delegation system.

This module defines the core data structures used to represent delegation
relationships and active delegation contexts.
"""

from dataclasses import dataclass
from datetime import date
from typing import Literal


@dataclass
class Delegation:
    """A delegation relationship between an actor and a subject.

    Represents the permission for one entity (actor) to act on behalf of
    another entity (subject), such as an entrepreneur acting for their business.

    Attributes:
        subject_id: The identifier of the subject (KVK number or BSN)
        subject_type: Whether the subject is a citizen or business
        subject_name: Human-readable name of the subject (company or person name)
        delegation_type: The type of delegation (e.g., EIGENAAR, BESTUURDER)
        permissions: List of permissions granted (e.g., LEZEN, CLAIMS_INDIENEN)
        valid_from: Date from which the delegation is valid
        valid_until: Optional end date for the delegation
    """

    subject_id: str
    subject_type: Literal["CITIZEN", "BUSINESS"]
    subject_name: str
    delegation_type: str
    permissions: list[str]
    valid_from: date
    valid_until: date | None = None

    def is_valid(self, reference_date: date | None = None) -> bool:
        """Check if the delegation is valid on the given date.

        Args:
            reference_date: The date to check validity for. Defaults to today.

        Returns:
            True if the delegation is valid on the reference date.
        """
        if reference_date is None:
            reference_date = date.today()

        if reference_date < self.valid_from:
            return False

        return not (self.valid_until is not None and reference_date > self.valid_until)


@dataclass
class DelegationContext:
    """Active context when a user is acting on behalf of another entity.

    This context is stored in the session when a user switches to acting
    on behalf of a business or another person.

    Attributes:
        actor_bsn: BSN of the logged-in user
        subject_id: Identifier of the entity being acted for (KVK or BSN)
        subject_type: Whether the subject is a citizen or business
        subject_name: Human-readable name for display in UI
        delegation_type: The type of delegation (e.g., EIGENAAR, BESTUURDER)
        permissions: List of permissions the actor has
    """

    actor_bsn: str
    subject_id: str
    subject_type: Literal["CITIZEN", "BUSINESS"]
    subject_name: str
    delegation_type: str
    permissions: list[str]

    def can_read(self) -> bool:
        """Check if the actor has read permission."""
        return "LEZEN" in self.permissions

    def can_submit_claims(self) -> bool:
        """Check if the actor can submit claims on behalf of the subject."""
        return "CLAIMS_INDIENEN" in self.permissions

    def can_receive_decisions(self) -> bool:
        """Check if the actor can receive decisions on behalf of the subject."""
        return "BESLUITEN_ONTVANGEN" in self.permissions

    def to_dict(self) -> dict:
        """Convert to dictionary for session storage."""
        return {
            "actor_bsn": self.actor_bsn,
            "subject_id": self.subject_id,
            "subject_type": self.subject_type,
            "subject_name": self.subject_name,
            "delegation_type": self.delegation_type,
            "permissions": self.permissions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DelegationContext":
        """Create a DelegationContext from a dictionary.

        Args:
            data: Dictionary with delegation context data

        Returns:
            A new DelegationContext instance
        """
        return cls(
            actor_bsn=data["actor_bsn"],
            subject_id=data["subject_id"],
            subject_type=data["subject_type"],
            subject_name=data["subject_name"],
            delegation_type=data["delegation_type"],
            permissions=data["permissions"],
        )
