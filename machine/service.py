import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd
from eventsourcing.system import SingleThreadedRunner, System

from .events.case.application import CaseManager
from .events.case.processor import CaseProcessor
from .events.claim.application import ClaimManager
from .events.claim.processor import ClaimProcessor
from .logging_config import IndentLogger
from .utils import RuleResolver

logger = IndentLogger(logging.getLogger("service"))


@dataclass
class RuleResult:
    """Result from rule execution containing output values and metadata"""

    output: dict[str, Any]
    requirements_met: bool
    input: dict[str, Any]
    rulespec_uuid: str
    path: Any | None = None
    missing_required: bool = False

    @classmethod
    def from_engine_result(cls, result: dict[str, Any], rulespec_uuid: str) -> "RuleResult":
        """Create RuleResult from engine evaluation result"""
        return cls(
            output={name: data.get("value") for name, data in result.get("output", {}).items()},
            requirements_met=result.get("requirements_met", False),
            input=result.get("input", {}),
            rulespec_uuid=rulespec_uuid,
            path=result.get("path"),
            missing_required=result.get("missing_required", False),
        )


class RuleService:
    """Interface for executing business rules for a specific service"""

    def __init__(self, service_name: str, services) -> None:
        """
        Initialize service for specific business rules

        Args:
            service_name: Name of the service (e.g. "TOESLAGEN")
            services: parent services
        """
        self.service_name = service_name
        self.services = services
        self.resolver = RuleResolver()
        self.source_dataframes: dict[str, pd.DataFrame] = {}

    def get_rule_info(self, law: str, reference_date: str) -> dict[str, Any] | None:
        """
        Get metadata about the rule that would be applied for given law and date

        Returns dict with uuid, name, valid_from if rule is found
        """
        try:
            rule = self.resolver.find_rule(law, reference_date)
            if rule:
                return {
                    "uuid": rule.uuid,
                    "name": rule.name,
                    "valid_from": rule.valid_from.strftime("%Y-%m-%d"),
                }
        except ValueError:
            return None
        return None

    def set_source_dataframe(self, table: str, df: pd.DataFrame) -> None:
        """Set a source DataFrame"""
        self.source_dataframes[table] = df


class Services:
    def __init__(self, reference_date: str, rules_engine: Any = None) -> None:
        self._impact_cache = None
        self.resolver = RuleResolver()
        self.services = {service: RuleService(service, self) for service in self.resolver.get_service_laws()}
        self.root_reference_date = reference_date

        # The rules_engine passed into the case/claim managers is whatever object
        # exposes .evaluate(service, law, parameters, ...). When Services is wrapped
        # by RegelrechtServices, we route it back to the wrapper so the Rust engine
        # is used; otherwise self is used (legacy callers without an engine wrapper).
        engine_ref = rules_engine if rules_engine is not None else self

        class WrappedCaseProcessor(CaseProcessor):
            def __init__(self, env=None, **kwargs) -> None:
                super().__init__(rules_engine=engine_ref, env=env, **kwargs)

        class WrappedCaseManager(CaseManager):
            def __init__(self, env=None, **kwargs) -> None:
                super().__init__(rules_engine=engine_ref, env=env, **kwargs)

        class WrappedClaimManager(ClaimManager):
            def __init__(self, env=None, **kwargs) -> None:
                super().__init__(rules_engine=engine_ref, env=env, **kwargs)

        class WrappedClaimProcessor(ClaimProcessor):
            def __init__(self, env=None, **kwargs) -> None:
                super().__init__(rules_engine=engine_ref, env=env, **kwargs)

        system = System(
            pipes=[[WrappedCaseManager, WrappedCaseProcessor], [WrappedClaimManager, WrappedClaimProcessor]]
        )

        self.runner = SingleThreadedRunner(system)
        self.runner.start()

        self.case_manager = self.runner.get(WrappedCaseManager)
        self.claim_manager = self.runner.get(WrappedClaimManager)

        self.claim_manager._case_manager = self.case_manager

    def __exit__(self):
        self.runner.stop()

    def get_discoverable_service_laws(self, discoverable_by="CITIZEN"):
        return self.resolver.get_discoverable_service_laws(discoverable_by)

    def get_sorted_discoverable_service_laws(self, bsn, discoverable_by="CITIZEN"):
        """
        Return laws discoverable by citizens or businesses, sorted by actual calculated impact.
        Uses simple caching to improve performance and stability.

        Args:
            bsn: The BSN of the person (or KVK number when acting on behalf of a business)
            discoverable_by: Either "CITIZEN" or "BUSINESS" to filter which laws to show

        Laws will be sorted by their calculated financial impact for this person
        based on outputs marked with citizen_relevance: primary in their YAML definitions.
        """
        # Get basic discoverable laws from the resolver
        discoverable_laws = self.get_discoverable_service_laws(discoverable_by=discoverable_by)

        # Initialize cache if it doesn't exist
        if not hasattr(self, "_impact_cache") or not self._impact_cache:
            self._impact_cache = {}

        # Current date for cache key and evaluation
        current_date = datetime.now().strftime("%Y-%m-%d")

        law_infos = [
            {"service": service, "law": law} for service in discoverable_laws for law in discoverable_laws[service]
        ]
        for law_info in law_infos:
            service = law_info["service"]
            law = law_info["law"]

            # Create cache key
            cache_key = f"{bsn}:{service}:{law}:{current_date}"

            # Check cache first
            if cache_key in self._impact_cache:
                law_info["impact_value"] = self._impact_cache[cache_key]
                continue

            try:
                # Get the rule spec to check for citizen_relevance markings
                rule_spec = self.resolver.get_rule_spec(law, current_date, service=service)

                # Run the law for this person and get results
                result = self.evaluate(service=service, law=law, parameters={"bsn": bsn}, reference_date=current_date)

                # Extract financial impact from result based on citizen_relevance
                impact_value = 0
                if result and result.output and rule_spec:
                    # Create mapping of output names to their output definitions
                    output_definitions = {}
                    for output_def in rule_spec.get("properties", {}).get("output", []):
                        output_name = output_def.get("name")
                        if output_name:
                            output_definitions[output_name] = output_def

                    # Track all primary numeric outputs to potentially sum them
                    primary_numeric_outputs = []

                    # Process outputs according to their relevance
                    for output_name, output_data in result.output.items():
                        # Get the output definition if available
                        output_def = output_definitions.get(output_name)

                        # Skip if no definition found or not marked as primary
                        if not output_def or output_def.get("citizen_relevance") != "primary":
                            continue

                        try:
                            # Use the type from the definition instead of inferring
                            output_type = output_def.get("type", "")

                            # Handle numeric types (amount, number)
                            if output_type in ["amount", "number"]:
                                numeric_value = float(output_data)

                                # Normalize to yearly values based on temporal definition
                                temporal = output_def.get("temporal", {})
                                if temporal.get("type") == "period" and temporal.get("period_type") == "month":
                                    # If monthly, multiply by 12 to get yearly equivalent
                                    numeric_value *= 12

                                primary_numeric_outputs.append(abs(numeric_value))

                            # Handle boolean types with standard importance for eligibility
                            elif output_type == "boolean" and output_data is True:
                                impact_value = max(impact_value, 50000)  # Assign importance to eligibility

                        except (ValueError, TypeError):
                            # If not convertible to number, skip
                            logger.debug(f"Skipping non-numeric output {output_name}: {output_data}")

                    # If we have multiple primary numeric outputs, sum them
                    if len(primary_numeric_outputs) > 0:
                        impact_value = max(impact_value, sum(primary_numeric_outputs))

                # Assign importance to missing required value
                if result.missing_required:
                    impact_value = max(impact_value, 100000)

                # Store in cache
                self._impact_cache[cache_key] = impact_value

                # Set the impact value in the law info
                law_info["impact_value"] = impact_value

            except Exception as e:
                # If evaluation fails, set impact to 0 and log
                logger.warning(f"Failed to calculate impact for {service}.{law}: {str(e)}")
                law_info["impact_value"] = 0

        # Sort by calculated impact (descending), then by name
        return sorted(law_infos, key=lambda x: (-x.get("impact_value", 0), x["law"]))

    def set_source_dataframe(self, service: str, table: str, df: pd.DataFrame) -> None:
        """Set a source DataFrame for a service"""
        self.services[service].set_source_dataframe(table, df)

    def get_law(self, service: str, law: str, reference_date: str | None = None) -> dict[str, Any] | None:
        """Get the law specification for a given service and law.

        Args:
            service: Name of the service (e.g., "KVK")
            law: Name of the law (e.g., "machtigingenwet")
            reference_date: Reference date for rule version (YYYY-MM-DD)

        Returns:
            The law specification dictionary, or None if not found
        """
        reference_date = reference_date or self.root_reference_date
        return self.resolver.get_rule_spec(law, reference_date, service=service)
