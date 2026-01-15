from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from machine.service import Services


@dataclass
class PathNode:
    """Node for tracking evaluation path"""

    type: str
    name: str
    result: Any
    resolve_type: str = None
    required: bool = False
    details: dict[str, Any] = field(default_factory=dict)
    children: list["PathNode"] = field(default_factory=list)


@dataclass
class RuleResult:
    """Result from rule execution containing output values and metadata"""

    output: dict[str, Any]
    requirements_met: bool
    input: dict[str, Any]
    rulespec_uuid: str
    path: PathNode | None = None
    missing_required: bool = False


class EngineInterface(ABC):
    """
    Interface for machine law evaluation services.
    Abstracts the underlying implementation (Python or Go).
    """

    @abstractmethod
    def get_rule_spec(self, law: str, reference_date: str, service: str) -> dict[str, Any]:
        """
        Get the rule specification for a specific law.

        Args:
            law: Law identifier
            reference_date: Reference date for rule version (YYYY-MM-DD)
            service: Service provider code (e.g., "TOESLAGEN")

        Returns:
            Dictionary containing the rule specification
        """

    @abstractmethod
    def get_profile_data(self, bsn: str, effective_date: date | None = None) -> dict[str, Any]:
        """
        Get profile data for a specific BSN.

        Args:
            bsn: BSN identifier for the individual

        Returns:
            Dictionary containing profile data or None if not found
        """

    @abstractmethod
    def get_all_profiles(self, effective_date: date | None = None) -> dict[str, dict[str, Any]]:
        """
        Get all available profiles.

        Returns:
            Dictionary mapping BSNs to profile data
        """

    @abstractmethod
    def evaluate(
        self,
        service: str,
        law: str,
        parameters: dict[str, Any],
        reference_date: str | None = None,
        effective_date: str | None = None,
        overwrite_input: dict[str, Any] | None = None,
        requested_output: str | None = None,
        approved: bool = False,
    ) -> RuleResult:
        """
        Evaluate rules for given law and reference date.

        Args:
            service: Service provider code (e.g., "TOESLAGEN")
            law: Name of the law (e.g., "zorgtoeslagwet")
            parameters: Context data for service provider
            reference_date: Reference date for rule version (YYYY-MM-DD)
            effective_date: The temporal context of the input data being evaluated (YYYY-MM-DD)
            overwrite_input: Optional overrides for input values
            requested_output: Optional specific output field to calculate
            approved: Whether this evaluation is for an approved claim

        Returns:
            Dictionary containing evaluation results
        """

    @abstractmethod
    def get_discoverable_service_laws(self, discoverable_by="CITIZEN") -> dict[str, list[str]]:
        """
        Get laws discoverable by citizens.

        Returns:
            Dictionary mapping service names to lists of law names
        """

    @abstractmethod
    def set_source_dataframe(self, service: str, table: str, df: pd.DataFrame) -> None:
        """
        Set a dataframe in a table for a service
        """

    @abstractmethod
    def reset(self) -> None:
        """
        reset the engine data.
        """

    def get_services(self) -> "Services | None":
        """
        Get the underlying Services instance.

        This method allows access to the underlying Services for features
        that need direct access to service providers (e.g., delegation).

        Returns:
            Services instance if available (internal Python engine),
            None if not available (HTTP engine).
        """
        return None

    def get_sorted_discoverable_service_laws(self, bsn: str, discoverable_by: str = "CITIZEN") -> list[dict[str, Any]]:
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
                rule_spec = self.get_rule_spec(law, current_date, service=service)

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
                            print(f"Skipping non-numeric output {output_name}: {output_data}")

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
                print(f"Failed to calculate impact for {service}.{law}: {str(e)}")
                law_info["impact_value"] = 0

        # Sort by calculated impact (descending), then by name
        return sorted(law_infos, key=lambda x: (-x.get("impact_value", 0), x["law"]))

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
