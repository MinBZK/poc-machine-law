import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from dateutil.relativedelta import relativedelta

from machine.regelrecht_services import RegelrechtServices


def _load_dashboard_primary_outputs() -> dict[str, str]:
    """Load the ``(service/law) -> primary output`` map used for dashboard sorting.

    Laws in this map rank by the value of their declared primary output
    only. Laws not in the map fall back to the sum of all numeric outputs.
    The map lives in ``web/config/dashboard_outputs.json`` so it can be
    edited without touching engine YAMLs.
    """
    path = Path(__file__).resolve().parent.parent / "config" / "dashboard_outputs.json"
    try:
        data = json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return {k: v for k, v in data.items() if not k.startswith("_")}


_DASHBOARD_PRIMARY_OUTPUTS = _load_dashboard_primary_outputs()


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

    def get_profile_properties(self, profile: dict) -> list[str]:
        """Extract key properties from a profile with emoji representations"""
        properties = []

        # Check if sources and RvIG data exist
        if not profile.get("sources") or not profile["sources"].get("RvIG"):
            return properties

        rvig_data = profile["sources"]["RvIG"]

        # Extract person data
        person_data = next(iter(rvig_data.get("personen", [])), {})
        if not person_data:
            return properties

        # Add nationality
        nationality = person_data.get("nationaliteit")
        if nationality:
            if nationality == "NEDERLANDS":
                properties.append("🇳🇱 Nederlands")
            elif nationality == "DUITS":
                properties.append("🇩🇪 Duits")
            elif nationality == "MAROKKAANS":
                properties.append("🇲🇦 Marokkaans")
            else:
                properties.append(f"🌍 {nationality}")

        # Add age
        if "geboortedatum" in person_data:
            birth_date_str = person_data["geboortedatum"]
            birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
            current_date = datetime.now()
            age = relativedelta(current_date, birth_date).years
            properties.append(f"🗓️ {age} jaar")

        # Add children
        children_data = rvig_data.get("children_data", [])
        for child_entry in children_data:
            if "kinderen" in child_entry:
                num_children = len(child_entry["kinderen"])
                if num_children == 1:
                    properties.append("👶 1 kind")
                elif num_children > 1:
                    properties.append(f"👨‍👩‍👧‍👦 {num_children} kinderen")

        # Add housing status
        address_data = next(iter(rvig_data.get("verblijfplaats", [])), {})
        if address_data:
            address_type = address_data.get("type")
            if address_type == "WOONADRES":
                properties.append("🏠 Vast woonadres")
            elif address_type == "BRIEFADRES":
                properties.append("📫 Briefadres")

        # Add work status
        is_entrepreneur = False
        if "KVK" in profile["sources"]:
            kvk_data = profile["sources"]["KVK"]
            if any(entry.get("waarde") for entry in kvk_data.get("is_entrepreneur", [])):
                is_entrepreneur = True
                properties.append("💼 ZZP'er")

        if "UWV" in profile["sources"]:
            uwv_data = profile["sources"]["UWV"]
            if "arbeidsverhoudingen" in uwv_data:
                for relation in uwv_data["arbeidsverhoudingen"]:
                    if relation.get("dienstverband_type") != "GEEN" and not is_entrepreneur:
                        properties.append("👔 In loondienst")

        # Add student status
        if "DUO" in profile["sources"]:
            duo_data = profile["sources"]["DUO"]
            if "inschrijvingen" in duo_data:
                for enrollment in duo_data["inschrijvingen"]:
                    if enrollment.get("onderwijssoort") != "GEEN":
                        properties.append("🎓 Student")

        # Add disability status
        if "UWV" in profile["sources"] and "arbeidsongeschiktheid" in profile["sources"]["UWV"]:
            for disability in profile["sources"]["UWV"]["arbeidsongeschiktheid"]:
                percentage = disability.get("percentage")
                if percentage:
                    properties.append(f"♿ {percentage}% arbeidsongeschikt")

        return properties

    @abstractmethod
    def get_business_profile(self, kvk_nummer: str) -> dict[str, Any] | None:
        """
        Get business profile data for a specific KVK number.

        Args:
            kvk_nummer: KVK registration number for the business

        Returns:
            Dictionary containing business data (handelsnaam, rechtsvorm, activiteit, status)
            or None if not found
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

    def get_services(self) -> RegelrechtServices | None:
        """Return the underlying RegelrechtServices instance, if any.

        Used by features like delegation that need direct access to the
        underlying law engine and registered data sources.
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

                # Extract the primary output value as the ranking impact.
                #
                # Laws listed in web/config/dashboard_outputs.json declare which
                # output represents the "real" result for the citizen; we use
                # that value as the score. Laws not in the map fall back to the
                # sum of all numeric outputs (less precise but usually OK).
                impact_value = 0
                if result and result.output:
                    key = f"{service}/{law}"
                    primary_name = _DASHBOARD_PRIMARY_OUTPUTS.get(key)

                    output_definitions: dict[str, dict] = {}
                    if rule_spec:
                        for output_def in rule_spec.get("properties", {}).get("output", []):
                            output_name = output_def.get("name")
                            if output_name:
                                output_definitions[output_name] = output_def

                    def _score(name: str, data: Any) -> float:
                        """Score a single output value for dashboard ranking."""
                        output_def = output_definitions.get(name) or {}
                        output_type = output_def.get("type", "")
                        if not output_type:
                            if isinstance(data, bool):
                                output_type = "boolean"
                            elif isinstance(data, (int, float)):
                                output_type = "amount"
                        if output_type in ("amount", "number") and isinstance(data, (int, float)):
                            value = float(data)
                            temporal = output_def.get("temporal", {})
                            if temporal.get("type") == "period" and temporal.get("period_type") == "month":
                                value *= 12
                            return abs(value)
                        if output_type == "boolean" and data is True:
                            return 50000.0
                        return 0.0

                    if primary_name and primary_name in result.output:
                        # Explicit primary output — use its value directly.
                        impact_value = _score(primary_name, result.output[primary_name])
                    else:
                        # Fallback: sum every numeric output we can score.
                        total = 0.0
                        has_positive_bool = False
                        for name, data in result.output.items():
                            if name in ("voldoet_aan_voorwaarden",):
                                continue
                            score = _score(name, data)
                            if score == 50000.0:
                                has_positive_bool = True
                            else:
                                total += score
                        if total > 0:
                            impact_value = total
                        elif has_positive_bool:
                            impact_value = 50000

                # Missing-required laws get a mid-range score so they stay
                # visible but don't push all working laws off the top.
                if result.missing_required:
                    impact_value = max(impact_value, 10000)

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
