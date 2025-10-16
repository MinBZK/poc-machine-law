import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd
from eventsourcing.system import SingleThreadedRunner, System

from .context import PathNode
from .engine import RulesEngine
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
    path: PathNode | None = None
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
        self._engines: dict[str, dict[str, RulesEngine]] = {}
        self.source_dataframes: dict[str, pd.DataFrame] = {}

    def _get_engine(self, law: str, reference_date: str) -> RulesEngine:
        """Get or create RulesEngine instance for given law and date"""
        # Use a single dictionary with tuple keys for more efficient lookup
        cache_key = (law, reference_date)

        # Flatten the nested dictionaries into a single lookup
        engines_cache = getattr(self, "_engines_cache", {})
        if not hasattr(self, "_engines_cache"):
            self._engines_cache = engines_cache

        if cache_key in engines_cache:
            return engines_cache[cache_key]

        # If we need to create a new engine, keep the law dictionary for backward compatibility
        if law not in self._engines:
            self._engines[law] = {}

        if reference_date not in self._engines[law]:
            spec = self.resolver.get_rule_spec(law, reference_date, service=self.service_name)
            if not spec:
                raise ValueError(f"No rules found for law '{law}' at date '{reference_date}'")
            if spec.get("service") != self.service_name:
                raise ValueError(
                    f"Rule spec service '{spec.get('service')}' does not match service '{self.service_name}'"
                )
            engine = RulesEngine(spec=spec, service_provider=self.services)
            self._engines[law][reference_date] = engine
            engines_cache[cache_key] = engine

        return engines_cache[cache_key]

    def evaluate(
        self,
        law: str,
        reference_date: str,
        parameters: dict[str, Any],
        overwrite_input: dict[str, Any] | None = None,
        requested_output: str | None = None,
        approved: bool = False,
    ) -> RuleResult:
        """
        Evaluate rules for given law and reference date

        Args:
            law: Name of the law (e.g. "zorgtoeslagwet")
            reference_date: Reference date for rule version (YYYY-MM-DD)
            parameters: Context data for service provider
            overwrite_input: Optional overrides for input values
            requested_output: Optional specific output field to calculate

        Returns:
            RuleResult containing outputs and metadata
        """
        engine = self._get_engine(law, reference_date)

        # Gather sources from all services for cross-service lookups
        all_sources = {}
        if self.services and hasattr(self.services, 'services'):
            for service_name, service in self.services.services.items():
                all_sources.update(service.source_dataframes)
        else:
            # Fallback to just this service's sources
            all_sources = self.source_dataframes

        result = engine.evaluate(
            parameters=parameters,
            overwrite_input=overwrite_input,
            sources=all_sources,
            calculation_date=reference_date,
            requested_output=requested_output,
            approved=approved,
        )
        return RuleResult.from_engine_result(result, engine.spec.get("uuid"))

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
    def __init__(self, reference_date: str) -> None:
        self._impact_cache = None
        self.resolver = RuleResolver()
        self.services = {service: RuleService(service, self) for service in self.resolver.get_service_laws()}
        self.root_reference_date = reference_date

        outer_self = self

        class WrappedCaseProcessor(CaseProcessor):
            def __init__(self, env=None, **kwargs) -> None:
                super().__init__(rules_engine=outer_self, env=env, **kwargs)

        class WrappedCaseManager(CaseManager):
            def __init__(self, env=None, **kwargs) -> None:
                super().__init__(rules_engine=outer_self, env=env, **kwargs)

        class WrappedClaimManager(ClaimManager):
            def __init__(self, env=None, **kwargs) -> None:
                super().__init__(rules_engine=outer_self, env=env, **kwargs)

        class WrappedClaimProcessor(ClaimProcessor):
            def __init__(self, env=None, **kwargs) -> None:
                super().__init__(rules_engine=outer_self, env=env, **kwargs)

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

    @staticmethod
    def extract_value_tree(root: PathNode):
        flattened = {}
        stack = [(root, None)]

        while stack:
            node, service_parent = stack.pop()

            if not isinstance(node, PathNode):
                continue

            path = node.details.get("path")
            if isinstance(path, str) and path.startswith("$"):
                path = path[1:]

            # Handle resolve nodes
            if (
                node.type == "resolve"
                and node.resolve_type in {"SERVICE", "SOURCE", "CLAIM", "NONE"}
                and path
                and isinstance(path, str)
            ):
                resolve_entry = {"result": node.result, "required": node.required, "details": node.details}

                if service_parent and path not in service_parent.setdefault("children", {}):
                    service_parent.setdefault("children", {})[path] = resolve_entry
                elif path not in flattened:
                    flattened[path] = resolve_entry

            # Handle service_evaluation nodes
            elif node.type == "service_evaluation" and path and isinstance(path, str):
                service_entry = {
                    "result": node.result,
                    "required": node.required,
                    "service": node.details.get("service"),
                    "law": node.details.get("law"),
                    "children": {},
                    "details": node.details,
                }

                if service_parent:
                    service_parent.setdefault("children", {})[path] = service_entry
                else:
                    flattened[path] = service_entry

                # Prepare to process children with this service_evaluation as parent
                for child in reversed(node.children):
                    stack.append((child, service_entry))
                continue

            # Add children to the stack for further processing
            for child in reversed(node.children):
                stack.append((child, service_parent))

        return flattened

    def get_discoverable_service_laws(self, discoverable_by="CITIZEN"):
        return self.resolver.get_discoverable_service_laws(discoverable_by)

    def get_sorted_discoverable_service_laws(self, bsn):
        """
        Return laws discoverable by citizens, sorted by actual calculated impact for this specific person.
        Uses simple caching to improve performance and stability.

        Laws will be sorted by their calculated financial impact for this person
        based on outputs marked with citizen_relevance: primary in their YAML definitions.
        """
        # Get basic discoverable laws from the resolver
        discoverable_laws = self.get_discoverable_service_laws()

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
                result = self.evaluate(service=service, law=law, parameters={"BSN": bsn}, reference_date=current_date)

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

    def evaluate(
        self,
        service: str,
        law: str,
        parameters: dict[str, Any],
        reference_date: str | None = None,
        overwrite_input: dict[str, Any] | None = None,
        requested_output: str | None = None,
        approved: bool = False,
    ) -> RuleResult:
        reference_date = reference_date or self.root_reference_date
        with logger.indent_block(
            f"{service}: {law} ({reference_date} {parameters} {requested_output})",
            double_line=True,
        ):
            return self.services[service].evaluate(
                law=law,
                reference_date=reference_date,
                parameters=parameters,
                overwrite_input=overwrite_input,
                requested_output=requested_output,
                approved=approved,
            )

    def apply_rules(self, event) -> None:
        for rule in self.resolver.rules:
            applies = rule.properties.get("applies", [])

            for apply in applies:
                if self._matches_event(event, apply):
                    aggregate_id = str(event.originator_id)
                    aggregate = self.case_manager.get_case_by_id(aggregate_id)
                    parameters = {apply["name"]: aggregate}
                    result = self.evaluate(rule.service, rule.law, parameters)

                    # Apply updates back to aggregate
                    for update in apply.get("update", []):
                        mapping = {
                            name: result.output.get(value[1:])  # Strip $ from value
                            for name, value in update["mapping"].items()
                        }
                        # Apply directly on the event via method
                        method = getattr(self.case_manager, update["method"])
                        method(aggregate_id, **mapping)

    @staticmethod
    def _matches_event(event, applies) -> bool:
        """Check if event matches the applies spec"""
        if applies["aggregate"] != event.__class__.__qualname__.split(".")[0]:
            return False

        event_type = event.__class__.__name__

        for event_spec in applies["events"]:
            if event_spec["type"].lower() == event_type.lower():
                for key, filter_value in event_spec.get("filter", {}).items():
                    value = getattr(event, key)
                    if value != filter_value:
                        return False
                return True
        return False
