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
    what entities a user can act on behalf of. The business logic for determining
    permissions is defined in the machtigingenwet YAML law specification.

    Attributes:
        services: The Services instance for rule evaluation
    """

    def __init__(self, services: "Services"):
        """Initialize the DelegationManager.

        Args:
            services: The Services instance for rule evaluation
        """
        self.services = services

    def get_delegations_for_user(self, bsn: str, reference_date: date | None = None) -> list[Delegation]:
        """Get all delegations available for a user.

        This method evaluates the machtigingenwet law to find all entities
        the user can act on behalf of (e.g., businesses where they are a director/owner).

        Args:
            bsn: The BSN of the user to check delegations for
            reference_date: The date to check validity for. Defaults to today.

        Returns:
            List of Delegation objects representing valid delegations
        """
        if reference_date is None:
            reference_date = date.today()

        delegations: list[Delegation] = []

        # Get business delegations by evaluating the machtigingenwet law
        business_delegations = self._get_business_delegations_via_law(bsn, reference_date)
        delegations.extend(business_delegations)

        return delegations

    def _get_business_delegations_via_law(self, bsn: str, reference_date: date) -> list[Delegation]:
        """Get business delegations by evaluating the machtigingenwet law.

        This method evaluates KVK.machtigingenwet which implements Art. 2:240 BW
        (vertegenwoordigingsbevoegdheid) to determine which businesses the user
        can represent. The law outputs all necessary data including bevoegdheden.

        Args:
            bsn: The BSN of the user
            reference_date: The reference date for validity checking

        Returns:
            List of business Delegation objects
        """
        delegations: list[Delegation] = []

        try:
            # Evaluate the machtigingenwet law via the RulesEngine
            result = self.services.evaluate(
                service="KVK",
                law="machtigingenwet",
                parameters={"BSN": bsn},
                reference_date=reference_date.strftime("%Y-%m-%d"),
            )

            # Check if the person has any representation authority
            if not result.output.get("heeft_vertegenwoordigingsbevoegdheid", False):
                return delegations

            # Get the arrays directly from the law output - all business logic is in YAML
            # These are all parallel arrays with the same length
            kvk_nummers = result.output.get("kvk_nummers", [])
            handelsnamen = result.output.get("handelsnamen", [])
            functies = result.output.get("functies", [])
            rechten_per_bedrijf = result.output.get("rechten_per_bedrijf", [])

            # Create a delegation for each business
            for i, kvk_nummer in enumerate(kvk_nummers):
                if kvk_nummer is None:
                    continue

                delegation = Delegation(
                    subject_id=str(kvk_nummer),
                    subject_type="BUSINESS",
                    subject_name=(
                        handelsnamen[i] if i < len(handelsnamen) and handelsnamen[i] else f"Bedrijf {kvk_nummer}"
                    ),
                    delegation_type=functies[i] if i < len(functies) and functies[i] else "ONBEKEND",
                    permissions=(
                        list(rechten_per_bedrijf[i]) if i < len(rechten_per_bedrijf) and rechten_per_bedrijf[i] else []
                    ),
                    valid_from=date(2020, 1, 1),
                    valid_until=None,
                )
                delegations.append(delegation)

        except Exception:
            # If law evaluation fails, return empty list
            # This ensures the application continues to work even if the law is not available
            pass

        return delegations

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
