"""
Engine adapter that bridges MCP server to the core Python law engine.
This is a thin layer that translates MCP requests to engine calls.
"""

import logging
import sys
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from law_mcp.cache import generate_cache_key, law_cache
from law_mcp.config import get_config
from law_mcp.exceptions import (
    BSNValidationError,
    LawExecutionError,
    LawNotFoundError,
    ServiceNotFoundError,
)
from law_mcp.mock_data import get_mock_profile_data
from law_mcp.models import AvailableLaw, LawExecutionResult, LawSpec, ProfileData
from law_mcp.utils import get_current_date, sanitize_input, validate_bsn
from machine.service import Services

logger = logging.getLogger(__name__)


class LawEngineAdapter:
    """Adapter that connects MCP server to the core Python law engine"""

    def __init__(self):
        """Initialize the law engine adapter"""
        try:
            # Get configuration
            self.config = get_config()

            # Get current date as reference
            reference_date = get_current_date()

            # Initialize the main services object
            self.services = Services(reference_date)

            # Get the rule resolver
            self.rule_resolver = self.services.resolver

            logger.info("Law engine adapter initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize law engine adapter: {e}")
            raise

    def _get_rule_service(self, service_name: str):
        """Get rule service for the given service name"""
        if service_name not in self.services.services:
            raise ServiceNotFoundError(service_name, available_services=list(self.services.services.keys()))
        return self.services.services[service_name]

    async def execute_law(
        self,
        bsn: str,
        service: str,
        law: str,
        reference_date: str | None = None,
        overrides: dict[str, Any] | None = None,
        requested_output: str | None = None,
        approved: bool = False,
    ) -> LawExecutionResult:
        """Execute a law for a specific person"""
        try:
            # Validate BSN
            if not validate_bsn(bsn):
                raise BSNValidationError(bsn)

            # Use current date if no reference date provided
            if reference_date is None:
                reference_date = get_current_date()

            # Sanitize overrides if provided
            if overrides:
                overrides = sanitize_input(overrides, self.config.security.max_input_length)

            # Check cache first
            cache_key = generate_cache_key(
                "law_execution",
                bsn=bsn,
                service=service,
                law=law,
                reference_date=reference_date,
                overrides=overrides,
                requested_output=requested_output,
                approved=approved,
            )

            if self.config.cache.enabled:
                cached_result = await law_cache.get(cache_key)
                if cached_result:
                    logger.debug(f"Cache hit for law execution: {service}.{law}")
                    return cached_result

            logger.info(f"Executing law {service}.{law} for BSN {bsn} on {reference_date}")

            # Get the rule service
            rule_service = self._get_rule_service(service)

            # Get rule specification
            spec = self.rule_resolver.get_rule_spec(law, reference_date, service=service)
            if not spec:
                raise LawNotFoundError(service, law)

            # Execute the rule
            parameters = {"BSN": bsn}
            if overrides:
                parameters.update(overrides)

            result = rule_service.evaluate(
                law=law,
                reference_date=reference_date,
                parameters=parameters,
                overwrite_input=overrides,
                requested_output=requested_output,
                approved=approved,
            )

            # Extract execution path if available
            execution_path = None
            if result.path:
                try:
                    execution_path = self.services.extract_value_tree(result.path)
                except Exception as e:
                    logger.warning(f"Failed to extract execution path: {e}")
                    execution_path = {"error": "Could not serialize execution path"}

            law_result = LawExecutionResult(
                output=result.output,
                requirements_met=result.requirements_met,
                input_data=result.input,
                rulespec_uuid=result.rulespec_uuid,
                missing_required=result.missing_required,
                execution_path=execution_path,
            )

            # Cache the result
            if self.config.cache.enabled:
                await law_cache.set(cache_key, law_result, self.config.cache.law_execution_ttl)

            return law_result

        except Exception as e:
            if not isinstance(e, BSNValidationError | LawNotFoundError | ServiceNotFoundError):
                e = LawExecutionError(service, law, str(e))
            logger.error(f"Failed to execute law {service}.{law} for BSN {bsn}: {e}")
            raise e

    def get_law_specification(self, service: str, law: str, reference_date: str | None = None) -> LawSpec:
        """Get the specification for a specific law"""
        try:
            if reference_date is None:
                reference_date = get_current_date()

            spec = self.rule_resolver.get_rule_spec(law, reference_date, service=service)
            if not spec:
                raise ValueError(f"Rule specification not found for {service}.{law}")

            return LawSpec(
                uuid=spec.get("uuid", ""),
                name=spec.get("name", law),
                law=spec.get("law", law),
                service=spec.get("service", service),
                description=spec.get("description", ""),
                valid_from=spec.get("valid_from", reference_date),
                references=spec.get("references", []),
                parameters=spec.get("properties", {}).get("parameters", []),
                outputs=spec.get("properties", {}).get("output", []),
            )

        except Exception as e:
            logger.error(f"Failed to get law specification for {service}.{law}: {e}")
            raise

    def get_profile_data(self, bsn: str) -> ProfileData:
        """Get profile data for a specific BSN"""
        try:
            # Validate BSN
            if not validate_bsn(bsn):
                raise ValueError(f"Invalid BSN format: {bsn}")

            # Use mock data for now
            # In production, this would fetch from RvIG/BRP or other sources
            profile_data = get_mock_profile_data(bsn)

            return ProfileData(bsn=bsn, data=profile_data)

        except Exception as e:
            logger.error(f"Failed to get profile data for BSN {bsn}: {e}")
            raise

    def get_available_laws(self, discoverable_only: bool = True) -> list[AvailableLaw]:
        """Get list of available laws"""
        try:
            laws = []

            # Get discoverable laws from rule resolver
            discoverable_laws = self.rule_resolver.get_discoverable_service_laws(
                "CITIZEN" if discoverable_only else None
            )

            for service in discoverable_laws:
                for law in discoverable_laws[service]:
                    try:
                        # Try to get law specification for additional details
                        spec = self.get_law_specification(service, law)
                        laws.append(
                            AvailableLaw(
                                service=service,
                                law=law,
                                name=spec.name,
                                description=spec.description,
                                discoverable=True,
                            )
                        )
                    except Exception:
                        # If spec retrieval fails, add basic info
                        laws.append(AvailableLaw(service=service, law=law, discoverable=True))

            return sorted(laws, key=lambda x: (x.service, x.law))

        except Exception as e:
            logger.error(f"Failed to get available laws: {e}")
            raise

    async def check_eligibility(self, bsn: str, service: str, law: str, reference_date: str | None = None) -> bool:
        """Check if a person is eligible for a specific benefit/law"""
        try:
            result = await self.execute_law(bsn, service, law, reference_date)
            return result.requirements_met and not result.missing_required
        except Exception as e:
            logger.error(f"Failed to check eligibility for {service}.{law} for BSN {bsn}: {e}")
            return False

    async def calculate_benefit_amount(
        self, bsn: str, service: str, law: str, output_field: str, reference_date: str | None = None
    ) -> float | None:
        """Calculate a specific benefit amount for a person"""
        try:
            result = await self.execute_law(bsn, service, law, reference_date, requested_output=output_field)

            if output_field in result.output:
                value = result.output[output_field]
                if isinstance(value, int | float):
                    return float(value)

            return None

        except Exception as e:
            logger.error(f"Failed to calculate benefit amount for {service}.{law}.{output_field} for BSN {bsn}: {e}")
            return None

    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            # Future cleanup tasks can be added here
            logger.debug("Cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()
