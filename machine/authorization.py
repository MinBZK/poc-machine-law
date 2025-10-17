"""
Authorization Service - Determines who can act on behalf of whom

This module provides the core authorization logic for determining which roles
a person can assume (acting as themselves, as another person, or as an organization).

Architecture:
- YAML files contain ONLY real Dutch laws (including discovery metadata)
- This Python service provides orchestration/convenience layer
- All authorization checks call individual law implementations
- Laws are discovered dynamically via discovery metadata in YAML
"""

import logging
from dataclasses import dataclass
from typing import Any, Literal

from .service import Services
from .utils import RuleResolver

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


class AuthorizationService:
    """Service for checking authorization and determining available roles"""

    def __init__(self, engine: EngineProtocol | Services):
        """
        Initialize authorization service

        Args:
            engine: The engine instance (Services or EngineInterface) for evaluating laws and accessing data
        """
        self.engine = engine
        self.resolver = RuleResolver()
        # Cache discovered laws to avoid repeated filesystem scans
        self._authorization_laws_cache: dict[str, list[dict[str, Any]]] = {}

    def _discover_authorization_laws(self, target_type: str) -> list[dict[str, Any]]:
        """
        Discover authorization laws from YAML discovery metadata

        Args:
            target_type: Type of target ("PERSON" or "ORGANIZATION")

        Returns:
            List of law configurations with discovery metadata
        """
        # Check cache first
        cache_key = target_type.lower()
        if cache_key in self._authorization_laws_cache:
            return self._authorization_laws_cache[cache_key]

        # Discover laws with purpose="authorization" and matching target_type
        laws = self.resolver.get_laws_by_discovery(
            purpose="authorization",
            target_type=target_type.upper()
        )

        # Cache the result
        self._authorization_laws_cache[cache_key] = laws

        return laws

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
        # Fallback to BSN if no profile found
        actor_name = f"BSN {actor_bsn}"
        if actor_profile:
            actor_name = actor_profile.get("naam") or actor_profile.get("name") or actor_name

        roles.append(
            Role(
                type="SELF",
                id=actor_bsn,
                name=actor_name,
                legal_ground="Zelf",
                legal_basis=None,
                scope=None,
            )
        )

        # Check person-based authorizations
        person_laws = self._discover_authorization_laws("PERSON")
        all_profiles = self._get_all_profiles()
        for target_bsn, target_profile in all_profiles.items():
            if target_bsn == actor_bsn:
                continue  # Skip self

            for law_config in person_laws:
                role = self._check_person_authorization(
                    actor_bsn, target_bsn, target_profile, law_config, reference_date
                )
                if role:
                    roles.append(role)

        # Check organization-based authorizations
        org_laws = self._discover_authorization_laws("ORGANIZATION")
        all_organizations = self._get_all_organizations()
        for rsin, org_data in all_organizations.items():
            for law_config in org_laws:
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

        # Discover relevant authorization laws
        laws = self._discover_authorization_laws(target_type)

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

                # Get name from brp_personen or target_profile
                name = target_profile.get("naam") or target_profile.get("name")
                if not name:
                    # Try to get from RvIG brp_personen
                    name = self._get_person_name(target_bsn)
                if not name:
                    name = f"BSN {target_bsn}"

                return Role(
                    type="PERSON",
                    id=target_bsn,
                    name=name,
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

    def _get_person_name(self, bsn: str) -> str | None:
        """Get person name from RvIG brp_personen table"""
        try:
            # Access RvIG service for brp_personen
            if hasattr(self.engine, 'services'):
                services_obj = self.engine.services

                # Get RvIG service (handle both raw and wrapped)
                rvig_service = None
                if isinstance(services_obj, dict):
                    rvig_service = services_obj.get('RvIG')
                elif hasattr(services_obj, 'services') and isinstance(services_obj.services, dict):
                    rvig_service = services_obj.services.get('RvIG')

                if rvig_service and hasattr(rvig_service, 'source_dataframes'):
                    if 'brp_personen' in rvig_service.source_dataframes:
                        df = rvig_service.source_dataframes['brp_personen']
                        # Find person by BSN
                        matches = df[df['bsn'] == bsn]
                        if not matches.empty:
                            return matches.iloc[0].get('naam')
        except Exception as e:
            logger.debug(f"Could not get name for BSN {bsn}: {e}")

        return None

    def _get_all_organizations(self) -> dict[str, dict[str, Any]]:
        """Get all organizations (from KVK data)"""
        orgs = {}

        try:
            # Access KVK service - handle both raw Services and wrapped PythonMachineService
            kvk_service = None

            if hasattr(self.engine, 'services'):
                services_obj = self.engine.services

                # Case 1: services is a dict (raw Services.services)
                if isinstance(services_obj, dict):
                    kvk_service = services_obj.get('KVK')
                # Case 2: services is a Services object (PythonMachineService.services)
                elif hasattr(services_obj, 'services') and isinstance(services_obj.services, dict):
                    kvk_service = services_obj.services.get('KVK')

            if kvk_service and hasattr(kvk_service, 'source_dataframes'):
                # Try bedrijven table first
                if 'bedrijven' in kvk_service.source_dataframes:
                    df = kvk_service.source_dataframes['bedrijven']
                    for _, row in df.iterrows():
                        rsin = row.get('rsin')
                        if rsin:
                            orgs[rsin] = {
                                'rsin': rsin,
                                'naam': row.get('naam', f'RSIN {rsin}'),
                                'rechtsvorm': row.get('rechtsvorm'),
                                'status': row.get('status'),
                            }

                # If no bedrijven table, try to extract from functionarissen
                elif 'functionarissen' in kvk_service.source_dataframes:
                    df = kvk_service.source_dataframes['functionarissen']
                    for _, row in df.iterrows():
                        rsin = row.get('rsin')
                        if rsin and rsin not in orgs:
                            orgs[rsin] = {
                                'rsin': rsin,
                                'naam': row.get('naam_bedrijf', f'RSIN {rsin}'),
                            }

            logger.debug(f"Found {len(orgs)} organizations from KVK data")

        except Exception as e:
            logger.warning(f"Could not load organizations: {e}")

        return orgs
