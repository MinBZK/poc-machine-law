"""Delegation manager for handling act-on-behalf-of scenarios.

This module provides the DelegationManager class which determines what entities
a user can act on behalf of by evaluating delegation provider laws via the RulesEngine.

The DelegationManager discovers and evaluates all laws with discoverable: "DELEGATION_PROVIDER"
and uses a standard interface to parse the results into Delegation objects.
"""

import logging
from datetime import date, datetime

from machine.delegation.models import Delegation, DelegationContext
from machine.service import Services

logger = logging.getLogger(__name__)


class DelegationManager:
    """Manager for determining and validating delegation relationships.

    This class discovers and evaluates all delegation provider laws to determine
    what entities a user can act on behalf of. The business logic for determining
    permissions is defined entirely in YAML law specifications.

    All delegation provider laws must implement the standard interface:
    - heeft_delegaties: boolean indicating if delegations exist
    - subject_ids: array of subject identifiers (KVK, BSN)
    - subject_names: array of display names
    - subject_types: array of types ("BUSINESS" or "CITIZEN")
    - delegation_types: array of delegation types (role/function)
    - permissions: array of permission arrays
    - valid_from_dates: array of start dates
    - valid_until_dates: array of end dates (null = unlimited)

    Attributes:
        services: The Services instance for rule evaluation
    """

    def __init__(self, services: Services):
        """Initialize the DelegationManager.

        Args:
            services: The Services instance for rule evaluation
        """
        self.services = services

    def get_delegations_for_user(self, bsn: str, reference_date: date | None = None) -> list[Delegation]:
        """Get all delegations available for a user.

        This method discovers all DELEGATION_PROVIDER laws and evaluates each one
        to find all entities the user can act on behalf of. This includes:
        - SELF delegation (from minderjarigheid law) representing the user acting as themselves
        - BUSINESS delegations (from machtigingenwet) for businesses the user can represent
        - CITIZEN delegations (from gezag law) for children the user has authority over

        Args:
            bsn: The BSN of the user to check delegations for
            reference_date: The date to check validity for. Defaults to today.

        Returns:
            List of Delegation objects representing valid delegations (SELF first, then others)
        """
        if reference_date is None:
            reference_date = date.today()

        delegations: list[Delegation] = []

        # Discover and evaluate all delegation provider laws
        delegation_laws = self.services.get_discoverable_service_laws("DELEGATION_PROVIDER")

        for service, laws in delegation_laws.items():
            for law in laws:
                law_delegations = self._evaluate_delegation_law(
                    service=service,
                    law=law,
                    bsn=bsn,
                    reference_date=reference_date,
                )
                delegations.extend(law_delegations)

        # Sort to put SELF delegation first
        delegations.sort(key=lambda d: (d.subject_type != "SELF", d.subject_name or ""))

        return delegations

    def _evaluate_delegation_law(self, service: str, law: str, bsn: str, reference_date: date) -> list[Delegation]:
        """Evaluate a delegation provider law using the standard interface.

        This method evaluates a single delegation law and parses its output
        using the standard delegation provider interface.

        Args:
            service: The service name (e.g., "KVK")
            law: The law name (e.g., "machtigingenwet")
            bsn: The BSN of the user
            reference_date: The reference date for validity checking

        Returns:
            List of Delegation objects from this law
        """
        delegations: list[Delegation] = []

        try:
            result = self.services.evaluate(
                service=service,
                law=law,
                parameters={"BSN": bsn},
                reference_date=reference_date.strftime("%Y-%m-%d"),
            )

            # Check if the person has any delegations using standard interface
            if not result.output.get("heeft_delegaties", False):
                return delegations

            subject_ids = result.output.get("subject_ids", [])
            subject_names = result.output.get("subject_names", [])
            subject_types = result.output.get("subject_types", [])
            delegation_types = result.output.get("delegation_types", [])
            permissions = result.output.get("permissions", [])
            valid_from_dates = result.output.get("valid_from_dates", [])
            valid_until_dates = result.output.get("valid_until_dates", [])

            for i, subject_id in enumerate(subject_ids):
                if subject_id is None:
                    continue

                delegation = Delegation(
                    subject_id=str(subject_id),
                    subject_type=subject_types[i],
                    subject_name=subject_names[i],
                    delegation_type=delegation_types[i],
                    permissions=list(permissions[i]) if permissions[i] else [],
                    valid_from=self._parse_date(valid_from_dates[i]),
                    valid_until=self._parse_date(valid_until_dates[i]),
                )
                delegations.append(delegation)

        except Exception as e:
            # If law evaluation fails, log and return empty list
            # This ensures the application continues to work even if a law is not available
            logger.warning(f"Failed to evaluate delegation law {service}/{law}: {e}")

        return delegations

    @staticmethod
    def _parse_date(date_value: str | date | None) -> date | None:
        """Parse a date value from various formats.

        Args:
            date_value: The date value (string, date, or None)

        Returns:
            A date object or None
        """
        if date_value is None:
            return None
        if isinstance(date_value, date):
            return date_value
        if isinstance(date_value, str):
            try:
                return datetime.strptime(date_value, "%Y-%m-%d").date()
            except ValueError:
                return None
        return None

    def get_user_permissions(self, bsn: str, reference_date: date | None = None) -> list[str]:
        """Get the permissions for a user acting as themselves.

        This method finds the SELF delegation for the user and returns its permissions.
        The SELF delegation is provided by the minderjarigheid law which determines
        permissions based on age and handlichting status.

        Args:
            bsn: The BSN of the user to check permissions for
            reference_date: The date to check for. Defaults to today.

        Returns:
            List of permission strings (e.g., ["LEZEN", "CLAIMS_INDIENEN"])
        """
        # Default to restricted permissions for safety - if we can't determine
        # the user's age/status, assume they're a minor
        restricted_permissions = ["LEZEN"]

        delegations = self.get_delegations_for_user(bsn, reference_date)

        # Find the SELF delegation
        for delegation in delegations:
            if delegation.subject_type == "SELF":
                # Use explicit None check - empty list means restricted, not default
                # If permissions is None (shouldn't happen), default to restricted for safety
                if delegation.permissions is not None:
                    return delegation.permissions if delegation.permissions else restricted_permissions
                logger.warning(f"SELF delegation for BSN {bsn} has None permissions, defaulting to restricted")
                return restricted_permissions

        # No SELF delegation found - default to restricted for safety
        logger.warning(f"No SELF delegation found for BSN {bsn}, defaulting to restricted permissions")
        return restricted_permissions

    def can_act_on_behalf(
        self,
        actor_bsn: str,
        subject_id: str,
        reference_date: date | None = None,
    ) -> bool:
        """Check if an actor can act on behalf of a subject.

        Args:
            actor_bsn: The BSN of the actor
            subject_id: The identifier of the subject (KVK or BSN)
            reference_date: The date to check validity for

        Returns:
            True if the actor can act on behalf of the subject
        """
        delegations = self.get_delegations_for_user(actor_bsn, reference_date)
        return any(d.subject_id == subject_id for d in delegations)

    def get_delegation_context(
        self,
        actor_bsn: str,
        subject_id: str,
        reference_date: date | None = None,
    ) -> DelegationContext | None:
        """Get the delegation context for acting on behalf of a subject.

        Args:
            actor_bsn: The BSN of the actor
            subject_id: The identifier of the subject
            reference_date: The date to check validity for

        Returns:
            DelegationContext if valid, None otherwise
        """
        delegations = self.get_delegations_for_user(actor_bsn, reference_date)

        for delegation in delegations:
            if delegation.subject_id == subject_id:
                return DelegationContext(
                    actor_bsn=actor_bsn,
                    subject_id=delegation.subject_id,
                    subject_type=delegation.subject_type,
                    subject_name=delegation.subject_name,
                    delegation_type=delegation.delegation_type,
                    permissions=delegation.permissions,
                )

        return None
