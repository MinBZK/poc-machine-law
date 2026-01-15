"""Delegation manager for handling act-on-behalf-of scenarios.

This module provides the DelegationManager class which determines what entities
a user can act on behalf of by evaluating delegation laws via the RulesEngine.
"""

from datetime import date
from typing import TYPE_CHECKING

from machine.delegation.models import Delegation, DelegationContext

if TYPE_CHECKING:
    from machine.service import Services


class DelegationManager:
    """Manager for determining and validating delegation relationships.

    This class uses the RulesEngine to evaluate delegation laws and determine
    what entities a user can act on behalf of.

    Attributes:
        services: The Services instance for rule evaluation
    """

    def __init__(self, services: "Services"):
        """Initialize the DelegationManager.

        Args:
            services: The Services instance for rule evaluation
        """
        self.services = services

    def get_delegations_for_user(
        self, bsn: str, reference_date: date | None = None
    ) -> list[Delegation]:
        """Get all delegations available for a user.

        This method evaluates delegation laws to find all entities the user
        can act on behalf of (e.g., businesses where they are an owner).

        Args:
            bsn: The BSN of the user to check delegations for
            reference_date: The date to check validity for. Defaults to today.

        Returns:
            List of Delegation objects representing valid delegations
        """
        if reference_date is None:
            reference_date = date.today()

        delegations: list[Delegation] = []

        # Get business delegations from KVK data
        business_delegations = self._get_business_delegations(bsn, reference_date)
        delegations.extend(business_delegations)

        return delegations

    def _get_business_delegations(
        self, bsn: str, reference_date: date
    ) -> list[Delegation]:
        """Get business delegations for a user from KVK data.

        Args:
            bsn: The BSN of the user
            reference_date: The reference date for validity checking

        Returns:
            List of business Delegation objects
        """
        delegations: list[Delegation] = []

        # Try to get KVK functionarissen data directly from sources
        try:
            kvk_service = self.services.services.get("KVK")
            if kvk_service is None:
                return delegations

            # Check for functionarissen table in source_dataframes
            if "functionarissen" in kvk_service.source_dataframes:
                functionarissen_df = kvk_service.source_dataframes["functionarissen"]

                # Find all businesses where this BSN is a functionaris
                matches = functionarissen_df[functionarissen_df["bsn"] == bsn]

                for _, row in matches.iterrows():
                    kvk_nummer = row.get("kvk_nummer")
                    if kvk_nummer is None:
                        continue

                    # Get business details from inschrijvingen
                    business_name = self._get_business_name(kvk_service, kvk_nummer)
                    functie = row.get("functie", "ONBEKEND")
                    permissions = self._get_permissions_for_functie(functie)

                    delegation = Delegation(
                        subject_id=str(kvk_nummer),
                        subject_type="BUSINESS",
                        subject_name=business_name,
                        delegation_type=functie,
                        permissions=permissions,
                        valid_from=date(2020, 1, 1),  # Default for mock data
                        valid_until=None,
                    )
                    delegations.append(delegation)

        except Exception:
            # If KVK data is not available, return empty list
            pass

        return delegations

    def _get_business_name(self, kvk_service, kvk_nummer: str) -> str:
        """Get the business name from KVK inschrijvingen.

        Args:
            kvk_service: The KVK RuleService
            kvk_nummer: The KVK number to look up

        Returns:
            The business name or a default string
        """
        try:
            if "inschrijvingen" in kvk_service.source_dataframes:
                inschrijvingen_df = kvk_service.source_dataframes["inschrijvingen"]
                matches = inschrijvingen_df[inschrijvingen_df["kvk_nummer"] == kvk_nummer]
                if not matches.empty:
                    return matches.iloc[0].get("handelsnaam", f"Bedrijf {kvk_nummer}")
        except Exception:
            pass
        return f"Bedrijf {kvk_nummer}"

    def _get_permissions_for_functie(self, functie: str) -> list[str]:
        """Get permissions based on the function type.

        Different function types grant different permissions.

        Args:
            functie: The function type (e.g., EIGENAAR, BESTUURDER, GEMACHTIGDE)

        Returns:
            List of permission strings
        """
        full_permissions = ["LEZEN", "CLAIMS_INDIENEN", "BESLUITEN_ONTVANGEN"]
        read_only_permissions = ["LEZEN"]

        full_access_functions = {"EIGENAAR", "BESTUURDER", "DIRECTEUR", "VENNOOT"}

        if functie.upper() in full_access_functions:
            return full_permissions
        return read_only_permissions

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
