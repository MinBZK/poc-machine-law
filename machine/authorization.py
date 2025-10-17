"""
Authorization Service - Determines who can act on behalf of whom

This module provides the core authorization logic for determining which roles
a person can assume (acting as themselves, as another person, or as an organization).

Architecture:
- YAML files contain ONLY real Dutch laws
- This Python service provides orchestration/convenience layer
- All authorization checks call individual law implementations
"""

import logging
from dataclasses import dataclass
from typing import Any, Literal

from .service import Services

logger = logging.getLogger(__name__)

# Type hint for engine interface (to avoid circular imports)
from typing import Protocol


class EngineProtocol(Protocol):
    """Protocol for engine interface with required methods"""

    def evaluate(
        self,
        service: str,
        law: str,
        parameters: dict[str, Any],
        reference_date: str | None = None,
        **kwargs: Any,
    ) -> Any: ...

    def get_profile_data(self, bsn: str) -> dict[str, Any]: ...

    def get_all_profiles(self) -> dict[str, dict[str, Any]]: ...


@dataclass
class Role:
    """A role that a person can assume"""

    type: Literal["SELF", "PERSON", "ORGANIZATION"]
    id: str  # BSN or RSIN
    name: str
    legal_ground: str | None = None
    legal_basis: str | None = None  # e.g., "BW 1:245"
    scope: str | None = None  # e.g., "financial", "volledig"
    restrictions: list[str] | None = None


# Configuration: Which laws check which authorization types
AUTHORIZATION_LAWS = {
    "person": [
        {
            "service": "RvIG",
            "law": "burgerlijk_wetboek/ouderlijk_gezag",
            "name": "Ouderlijk gezag",
            "legal_basis": "BW 1:245",
            "actor_param": "BSN_OUDER",
            "target_param": "BSN_KIND",
            "output_field": "mag_vertegenwoordigen",
            "scope_field": "vertegenwoordigings_grondslag",
        },
        {
            "service": "RECHTSPRAAK",
            "law": "burgerlijk_wetboek/curatele",
            "name": "Curatele",
            "legal_basis": "BW 1:378",
            "actor_param": "BSN_CURATOR",
            "target_param": "BSN_CURANDUS",
            "output_field": "mag_vertegenwoordigen",
            "scope_field": "type_curatele",
        },
        {
            "service": "ALGEMEEN",
            "law": "burgerlijk_wetboek/volmacht",
            "name": "Volmacht",
            "legal_basis": "BW 3:60",
            "actor_param": "BSN_GEVOLMACHTIGDE",
            "target_param": "BSN_VOLMACHTGEVER",
            "output_field": "mag_vertegenwoordigen",
            "scope_field": "type_volmacht",
        },
    ],
    "organization": [
        {
            "service": "KVK",
            "law": "handelsregisterwet/vertegenwoordiging",
            "name": "KVK Vertegenwoordiging",
            "legal_basis": "Handelsregisterwet Art. 10",
            "actor_param": "BSN_PERSOON",
            "target_param": "RSIN",
            "output_field": "mag_vertegenwoordigen",
            "scope_field": "functie",
        },
        {
            "service": "ALGEMEEN",
            "law": "burgerlijk_wetboek/volmacht",
            "name": "Bedrijfsvolmacht",
            "legal_basis": "BW 3:60",
            "actor_param": "BSN_GEVOLMACHTIGDE",
            "target_param": "RSIN_VOLMACHTGEVER",
            "output_field": "mag_vertegenwoordigen",
            "scope_field": "type_volmacht",
        },
    ],
}


class AuthorizationService:
    """Service for checking authorization and determining available roles"""

    def __init__(self, engine: EngineProtocol | Services):
        """
        Initialize authorization service

        Args:
            engine: The engine instance (Services or EngineInterface) for evaluating laws and accessing data
        """
        self.engine = engine

    def get_available_roles(
        self, actor_bsn: str, reference_date: str | None = None
    ) -> list[Role]:
        """
        Get all roles that an actor can assume

        Args:
            actor_bsn: BSN of the person checking their roles
            reference_date: Optional reference date (defaults to today)

        Returns:
            List of Role objects, always starting with SELF role
        """
        roles: list[Role] = []

        # Always include SELF role
        actor_profile = self._get_profile(actor_bsn)
        if actor_profile:
            roles.append(
                Role(
                    type="SELF",
                    id=actor_bsn,
                    name=actor_profile.get("naam", f"BSN {actor_bsn}"),
                    legal_ground="Zelf",
                    legal_basis=None,
                    scope=None,
                )
            )

        # Check person-based authorizations
        all_profiles = self._get_all_profiles()
        for target_bsn, target_profile in all_profiles.items():
            if target_bsn == actor_bsn:
                continue  # Skip self

            for law_config in AUTHORIZATION_LAWS["person"]:
                role = self._check_person_authorization(
                    actor_bsn, target_bsn, target_profile, law_config, reference_date
                )
                if role:
                    roles.append(role)

        # Check organization-based authorizations
        all_organizations = self._get_all_organizations()
        for rsin, org_data in all_organizations.items():
            for law_config in AUTHORIZATION_LAWS["organization"]:
                role = self._check_organization_authorization(
                    actor_bsn, rsin, org_data, law_config, reference_date
                )
                if role:
                    roles.append(role)

        return roles

    def verify_authorization(
        self,
        actor_bsn: str,
        target_type: Literal["PERSON", "ORGANIZATION"],
        target_id: str,
        action: str | None = None,
        reference_date: str | None = None,
    ) -> tuple[bool, str | None]:
        """
        Verify if actor is authorized to act on behalf of target

        Args:
            actor_bsn: BSN of person wanting to act
            target_type: Type of target (PERSON or ORGANIZATION)
            target_id: BSN (if PERSON) or RSIN (if ORGANIZATION)
            action: Optional specific action to check
            reference_date: Optional reference date

        Returns:
            Tuple of (is_authorized: bool, legal_ground: str | None)
        """
        # Self authorization is always allowed
        if target_type == "PERSON" and target_id == actor_bsn:
            return (True, "Zelf")

        # Check relevant laws
        laws = AUTHORIZATION_LAWS.get(target_type.lower(), [])

        for law_config in laws:
            try:
                # Build parameters
                parameters = {
                    law_config["actor_param"]: actor_bsn,
                    law_config["target_param"]: target_id,
                }

                # Add action if volmacht and action specified
                if "volmacht" in law_config["law"] and action:
                    parameters["ACTIE"] = action

                # Evaluate the law
                result = self.engine.evaluate(
                    service=law_config["service"],
                    law=law_config["law"],
                    parameters=parameters,
                    reference_date=reference_date,
                )

                # Check if authorized
                output_field = law_config["output_field"]
                if result.output.get(output_field) is True:
                    return (True, law_config["name"])

            except Exception as e:
                logger.warning(
                    f"Error checking {law_config['name']} for {actor_bsn} -> {target_id}: {e}"
                )
                continue

        return (False, None)

    def _check_person_authorization(
        self,
        actor_bsn: str,
        target_bsn: str,
        target_profile: dict[str, Any],
        law_config: dict[str, Any],
        reference_date: str | None,
    ) -> Role | None:
        """Check if actor can act on behalf of a specific person"""
        try:
            parameters = {
                law_config["actor_param"]: actor_bsn,
                law_config["target_param"]: target_bsn,
            }

            # Add TARGET_TYPE for volmacht
            if "volmacht" in law_config["law"]:
                parameters["TARGET_TYPE"] = "PERSON"

            result = self.engine.evaluate(
                service=law_config["service"],
                law=law_config["law"],
                parameters=parameters,
                reference_date=reference_date,
            )

            # Check if authorized
            if result.output.get(law_config["output_field"]) is True:
                # Extract scope/restrictions
                scope = result.output.get(law_config.get("scope_field"))
                restrictions = result.output.get("beperkingen", [])

                return Role(
                    type="PERSON",
                    id=target_bsn,
                    name=target_profile.get("naam", f"BSN {target_bsn}"),
                    legal_ground=law_config["name"],
                    legal_basis=law_config["legal_basis"],
                    scope=scope,
                    restrictions=restrictions if restrictions else None,
                )

        except Exception as e:
            logger.debug(
                f"No {law_config['name']} authorization for {actor_bsn} -> {target_bsn}: {e}"
            )

        return None

    def _check_organization_authorization(
        self,
        actor_bsn: str,
        rsin: str,
        org_data: dict[str, Any],
        law_config: dict[str, Any],
        reference_date: str | None,
    ) -> Role | None:
        """Check if actor can act on behalf of a specific organization"""
        try:
            parameters = {
                law_config["actor_param"]: actor_bsn,
                law_config["target_param"]: rsin,
            }

            # Add TARGET_TYPE for volmacht
            if "volmacht" in law_config["law"]:
                parameters["TARGET_TYPE"] = "ORGANIZATION"

            result = self.engine.evaluate(
                service=law_config["service"],
                law=law_config["law"],
                parameters=parameters,
                reference_date=reference_date,
            )

            # Check if authorized
            if result.output.get(law_config["output_field"]) is True:
                # Extract scope/function
                scope = result.output.get(law_config.get("scope_field"))
                bevoegdheid = result.output.get("bevoegdheid")

                return Role(
                    type="ORGANIZATION",
                    id=rsin,
                    name=org_data.get("naam", f"RSIN {rsin}"),
                    legal_ground=law_config["name"],
                    legal_basis=law_config["legal_basis"],
                    scope=f"{scope} ({bevoegdheid})" if bevoegdheid else scope,
                )

        except Exception as e:
            logger.debug(
                f"No {law_config['name']} authorization for {actor_bsn} -> {rsin}: {e}"
            )

        return None

    def _get_profile(self, bsn: str) -> dict[str, Any] | None:
        """Get profile data for a BSN"""
        return self.engine.get_profile_data(bsn)

    def _get_all_profiles(self) -> dict[str, dict[str, Any]]:
        """Get all citizen profiles"""
        return self.engine.get_all_profiles()

    def _get_all_organizations(self) -> dict[str, dict[str, Any]]:
        """Get all organizations (from KVK data)"""
        # TODO: Need to add get_all_organizations() to EngineInterface
        # For now, extract from sources or return empty
        try:
            # Try to get from RuleService if available
            if hasattr(self.engine, 'services') and 'KVK' in self.engine.services:
                kvk_service = self.engine.services['KVK']
                if hasattr(kvk_service, 'source_dataframes') and 'bedrijven' in kvk_service.source_dataframes:
                    df = kvk_service.source_dataframes['bedrijven']
                    # Convert DataFrame to dict keyed by RSIN
                    orgs = {}
                    for _, row in df.iterrows():
                        rsin = row.get('rsin')
                        if rsin:
                            orgs[rsin] = row.to_dict()
                    return orgs
        except Exception as e:
            logger.debug(f"Could not load organizations: {e}")

        return {}
