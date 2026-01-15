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

            # Get the arrays from the law output
            # These are all parallel arrays with the same length
            kvk_nummers = result.output.get("kvk_nummers", [])
            handelsnamen = result.output.get("handelsnamen", [])
            functies = result.output.get("functies", [])
            bevoegdheden = result.output.get("bevoegdheden", [])

            # Get the permission definitions from the law specification
            # These are defined in the YAML under properties.definitions
            law_spec = self.services.get_law("KVK", "machtigingenwet")
            definitions = law_spec.get("properties", {}).get("definitions", {}) if law_spec else {}

            # Permission mappings from the law (Art. 2:1 Awb, Art. 2:240 lid 3 BW)
            volledige_rechten = definitions.get(
                "VOLLEDIGE_BEVOEGDHEID_RECHTEN", ["LEZEN", "CLAIMS_INDIENEN", "BESLUITEN_ONTVANGEN"]
            )
            beperkte_rechten = definitions.get("BEPERKTE_BEVOEGDHEID_RECHTEN", ["LEZEN"])

            # Create a delegation for each business
            for i, kvk_nummer in enumerate(kvk_nummers):
                if kvk_nummer is None:
                    continue

                # Get business name (fallback to KVK number if not available)
                business_name = (
                    handelsnamen[i] if i < len(handelsnamen) and handelsnamen[i] else f"Bedrijf {kvk_nummer}"
                )

                # Get function (fallback to ONBEKEND if not available)
                functie = functies[i] if i < len(functies) and functies[i] else "ONBEKEND"

                # Get bevoegdheid and determine permissions based on law definitions
                # Art. 2:240 lid 3 BW: VOLLEDIG = onbeperkt, BEPERKT = statutaire beperkingen
                bevoegdheid = bevoegdheden[i] if i < len(bevoegdheden) and bevoegdheden[i] else "BEPERKT"
                permissions = volledige_rechten if bevoegdheid == "VOLLEDIG" else beperkte_rechten

                delegation = Delegation(
                    subject_id=str(kvk_nummer),
                    subject_type="BUSINESS",
                    subject_name=business_name,
                    delegation_type=functie,
                    permissions=list(permissions),  # Ensure it's a new list
                    valid_from=date(2020, 1, 1),  # Default - could be from law output
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
