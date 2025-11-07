import logging
from copy import copy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from machine.events.claim.aggregate import Claim
from machine.logging_config import IndentLogger

logger = IndentLogger(logging.getLogger("service"))


def clean_nan_value(value: Any, expected_type: str | None = None) -> Any:
    """
    Clean NaN values from pandas dataframes, converting them to appropriate defaults.

    Args:
        value: The value to clean (could be NaN, None, or a valid value)
        expected_type: Optional type hint ('int', 'bool', 'str', 'list')

    Returns:
        Cleaned value with NaN converted to appropriate default
    """
    # If it's a list or dict, recursively clean nested values first
    if isinstance(value, list):
        return [clean_nan_value(v, expected_type) for v in value]
    elif isinstance(value, dict):
        return {k: clean_nan_value(v, expected_type) for k, v in value.items()}

    # Check if value is NaN (pandas float NaN or numpy NaN) - only for scalars
    try:
        is_nan = pd.isna(value)
        # Handle case where pd.isna returns an array (shouldn't happen after list check, but be safe)
        if isinstance(is_nan, pd.Series | np.ndarray):
            # If it's an array, we can't check it in boolean context, just return the value
            return value
        if is_nan:
            if expected_type == "int" or expected_type == "eurocent":
                return 0
            elif expected_type == "bool":
                return False
            elif expected_type == "str":
                return ""
            elif expected_type == "list":
                return []
            else:
                # For unknown types, return None instead of NaN
                return None
    except (TypeError, ValueError):
        # If pd.isna fails for some reason, just return the value
        pass

    return value


@dataclass
class TypeSpec:
    """Specification for value types"""

    type: str | None = None
    unit: str | None = None
    precision: int | None = None
    min: int | float | None = None
    max: int | float | None = None

    def enforce(self, value: Any) -> Any:
        """Enforce type specifications on a value"""
        # Clean NaN values first
        value = clean_nan_value(value, self.unit or self.type)

        if value is None:
            return value

        if self.type == "string":
            return str(value)

        # Convert to numeric if needed
        if isinstance(value, str):
            try:
                value = float(value)
            except ValueError:
                return value

        if not isinstance(value, int | float):
            return value

        # Apply min/max constraints
        if self.min is not None:
            value = max(value, self.min)
        if self.max is not None:
            value = min(value, self.max)

        # Apply precision
        if self.precision is not None:
            value = round(value, self.precision)

        # Convert to int for cent units
        if self.unit == "eurocent":
            value = int(value)

        return value


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
class ExecutionContext:
    """
    Context for law execution.

    Manages state for a single law evaluation, including value resolution,
    caching, and execution path tracking.
    """

    definitions: dict[str, Any]
    law_evaluator: Any | None  # Reference to LawEvaluator for external law calls
    data_context: Any | None  # Reference to DataContext for data access
    parameters: dict[str, Any]
    property_specs: dict[str, dict[str, Any]]
    output_specs: dict[str, TypeSpec]
    sources: dict[str, pd.DataFrame]  # Local sources (deprecated, use data_context)
    local: dict[str, Any] = field(default_factory=dict)
    accessed_paths: set[str] = field(default_factory=set)
    values_cache: dict[str, Any] = field(default_factory=dict)
    path: list[PathNode] = field(default_factory=list)
    overwrite_input: dict[str, Any] = field(default_factory=dict)
    overwrite_definitions: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    calculation_date: str | None = None
    resolved_paths: dict[str, Any] = field(default_factory=dict)
    claims: dict[str:Claim] = None
    approved: bool | None = True
    missing_required: bool | None = False

    @property
    def service_provider(self):
        """Backward compatibility: service_provider now points to law_evaluator"""
        return self.law_evaluator

    @service_provider.setter
    def service_provider(self, value):
        """Backward compatibility: setting service_provider sets law_evaluator"""
        self.law_evaluator = value

    def track_access(self, path: str) -> None:
        """Track accessed data paths"""
        self.accessed_paths.add(path)

    def add_to_path(self, node: PathNode) -> None:
        """Add node to evaluation path"""
        if self.path:
            self.path[-1].children.append(node)
        self.path.append(node)

    def pop_path(self) -> None:
        """Remove last node from path"""
        if self.path:
            self.path.pop()

    def resolve_value(self, path: str) -> Any:
        value = self._resolve_value(path)
        if isinstance(path, str):
            self.resolved_paths[path] = value
        return value

    def _resolve_value(self, path: str) -> Any:
        """Resolve a value from definitions, services, or sources"""
        node = PathNode(
            type="resolve",
            name=f"Resolving value: {path}",
            result=None,
            details={"path": path},
        )
        self.add_to_path(node)

        try:
            with logger.indent_block(f"Resolving {path}"):
                if not isinstance(path, str) or not path.startswith("$"):
                    node.result = path
                    return path

                path = path[1:]  # Remove $ prefix
                self.track_access(path)

                # Resolve dates
                value = self._resolve_date(path)
                if value is not None:
                    logger.debug(f"Resolved date ${path}: {value}")
                    node.result = value
                    return value

                if "." in path:
                    root, rest = path.split(".", 1)
                    value = self.resolve_value(f"${root}")
                    for p in rest.split("."):
                        if value is None:
                            logger.warning(f"Value is None, could not resolve value ${path}: None")
                            node.result = None
                            return None
                        if isinstance(value, dict):
                            value = value.get(p)
                        elif hasattr(value, p):
                            value = getattr(value, p)
                        else:
                            logger.warning(f"Value is not dict or not object, could not resolve value ${path}: None")
                            node.result = None
                            return None

                    logger.debug(f"Resolved value ${path}: {value}")
                    node.result = value
                    return value

                # Claims first
                if isinstance(self.claims, dict) and path in self.claims:
                    claim = self.claims.get(path)
                    value = claim.new_value
                    logger.debug(f"Resolving from CLAIM: {value}")
                    node.result = value
                    node.resolve_type = "CLAIM"

                    # Add type information for claims as well
                    if path in self.property_specs:
                        spec = self.property_specs[path]
                        if "type" in spec:
                            node.details["type"] = spec["type"]
                        if "type_spec" in spec:
                            node.details["type_spec"] = spec["type_spec"]
                        node.required = bool(spec.get("required", False))

                    return value

                # Check local scope
                if path in self.local:
                    logger.debug(f"Resolving from LOCAL: {self.local[path]}")
                    node.result = self.local[path]
                    node.resolve_type = "LOCAL"
                    return self.local[path]

                # Check overwrite_definitions BEFORE regular definitions
                if path in self.overwrite_definitions:
                    logger.debug(f"Resolving from OVERRIDE DEFINITION: {self.overwrite_definitions[path]}")
                    node.result = self.overwrite_definitions[path]
                    node.resolve_type = "OVERRIDE_DEFINITION"
                    return self.overwrite_definitions[path]

                # Check definitions
                if path in self.definitions:
                    definition_value = self.definitions[path]
                    # If definition contains both 'value' and 'legal_basis', extract only the value
                    if (
                        isinstance(definition_value, dict)
                        and "value" in definition_value
                        and "legal_basis" in definition_value
                    ):
                        actual_value = definition_value["value"]
                        logger.debug(f"Resolving from DEFINITION (extracted value): {actual_value}")
                        node.result = actual_value
                        node.resolve_type = "DEFINITION"
                        return actual_value
                    else:
                        logger.debug(f"Resolving from DEFINITION: {definition_value}")
                        node.result = definition_value
                        node.resolve_type = "DEFINITION"
                        return definition_value

                # Check parameters
                if path in self.parameters:
                    logger.debug(f"Resolving from PARAMETERS: {self.parameters[path]}")
                    node.result = self.parameters[path]
                    node.resolve_type = "PARAMETER"
                    return self.parameters[path]

                # Check outputs
                if path in self.outputs:
                    logger.debug(f"Resolving from previous OUTPUT: {self.outputs[path]}")
                    node.result = self.outputs[path]
                    node.resolve_type = "OUTPUT"
                    return self.outputs[path]

                # Check overwrite data (support both old service_reference and new external_reference)
                if path in self.property_specs:
                    spec = self.property_specs[path]
                    # Support old service_reference format for backward compatibility
                    service_ref = spec.get("service_reference", {})
                    external_ref = spec.get("external_reference", {})

                    # Use external_reference if present, otherwise fall back to service_reference
                    ref = external_ref if external_ref else service_ref

                    if ref:
                        # Old format: check service-based overwrite
                        if service_ref and "service" in service_ref:
                            if (
                                service_ref["service"] in self.overwrite_input
                                and service_ref["field"] in self.overwrite_input[service_ref["service"]]
                            ):
                                value = self.overwrite_input[service_ref["service"]][service_ref["field"]]
                                logger.debug(f"Resolving from OVERWRITE: {value}")
                                node.result = value
                                node.resolve_type = "OVERWRITE"
                                return value
                        # New format: check law-based overwrite
                        elif external_ref and "law" in external_ref:
                            if (
                                external_ref["law"] in self.overwrite_input
                                and external_ref["field"] in self.overwrite_input[external_ref["law"]]
                            ):
                                value = self.overwrite_input[external_ref["law"]][external_ref["field"]]
                                logger.debug(f"Resolving from OVERWRITE: {value}")
                                node.result = value
                                node.resolve_type = "OVERWRITE"
                                return value

                # Check sources
                if path in self.property_specs:
                    spec = self.property_specs[path]
                    source_ref = spec.get("source_reference", {})
                    if source_ref:
                        # Check source overwrite data first
                        if (
                            source_ref.get("source_type") in self.overwrite_input
                            and path in self.overwrite_input[source_ref["source_type"]]
                        ):
                            value = self.overwrite_input[source_ref["source_type"]][path]
                            logger.debug(f"Resolving from SOURCE OVERRIDE: {value}")
                            node.result = value
                            node.resolve_type = "SOURCE_OVERRIDE"
                            node.required = bool(spec.get("required", False))

                            # Add type information to the node
                            if "type" in spec:
                                node.details["type"] = spec["type"]
                            if "type_spec" in spec:
                                resolved_type_spec = self._resolve_type_spec_enums(spec, spec["type_spec"])
                                node.details["type_spec"] = resolved_type_spec

                            return value
                        df = None
                        table = None
                        if source_ref.get("source_type") == "laws":
                            table = "laws"
                            # Use law_evaluator if available, otherwise fall back to old service_provider
                            if self.law_evaluator:
                                df = self.law_evaluator.resolver.rules_dataframe()
                            elif self.service_provider:
                                df = self.service_provider.resolver.rules_dataframe()
                        elif source_ref.get("source_type") == "events":
                            table = "events"
                            # Use law_evaluator if available, otherwise fall back to old service_provider
                            if self.law_evaluator:
                                events = self.law_evaluator.case_manager.get_events()
                            elif self.service_provider:
                                events = self.service_provider.case_manager.get_events()
                            else:
                                events = []
                            df = pd.DataFrame(events)
                        elif "table" in source_ref:
                            table = source_ref.get("table")
                            # Try data_context first (new approach)
                            if self.data_context:
                                # In new architecture, sources are organized by source_name/table_name
                                # For now, check all source names for the table
                                for source_name in self.data_context.sources:
                                    if table in self.data_context.sources[source_name]:
                                        df = self.data_context.get_source(source_name, table)
                                        break
                            # Fall back to local sources (old approach)
                            elif self.sources and table in self.sources:
                                df = self.sources[table]

                        if df is not None:
                            result = self._resolve_from_source(source_ref, table, df)
                            logger.debug(f"Resolving from SOURCE {table}: {result}")
                            node.result = result
                            node.resolve_type = "SOURCE"
                            node.required = bool(spec.get("required", False))

                            # Add type information to the node
                            if "type" in spec:
                                node.details["type"] = spec["type"]
                            if "type_spec" in spec:
                                # Gebruik helper-methode om enum-referenties op te lossen
                                resolved_type_spec = self._resolve_type_spec_enums(spec, spec["type_spec"])
                                node.details["type_spec"] = resolved_type_spec

                            return result

                # Check external references (new) or service references (old)
                if path in self.property_specs:
                    spec = self.property_specs[path]
                    external_ref = spec.get("external_reference", {})
                    service_ref = spec.get("service_reference", {})

                    # Prefer external_reference (new format)
                    if external_ref and self.law_evaluator:
                        value = self._resolve_from_external(path, external_ref, spec)
                        logger.debug(
                            f"Result for ${path} from law {external_ref['law']} field {external_ref['field']}: {value}"
                        )
                        node.result = value
                        node.resolve_type = "EXTERNAL"
                        node.required = bool(spec.get("required", False))

                        # Add type information to the node
                        if "type" in spec:
                            node.details["type"] = spec["type"]
                        if "type_spec" in spec:
                            resolved_type_spec = self._resolve_type_spec_enums(spec, spec["type_spec"])
                            node.details["type_spec"] = resolved_type_spec

                        return value
                    # Fall back to service_reference (old format)
                    elif service_ref:
                        # Try new law_evaluator first
                        if self.law_evaluator:
                            value = self._resolve_from_service_via_evaluator(path, service_ref, spec)
                        # Fall back to old service_provider
                        elif self.service_provider:
                            value = self._resolve_from_service(path, service_ref, spec)
                        else:
                            value = None

                        if value is not None:
                            logger.debug(
                                f"Result for ${path} from {service_ref.get('service', service_ref.get('law'))} "
                                f"field {service_ref['field']}: {value}"
                            )
                            node.result = value
                            node.resolve_type = "SERVICE"
                            node.required = bool(spec.get("required", False))

                            # Add type information to the node
                            if "type" in spec:
                                node.details["type"] = spec["type"]
                            if "type_spec" in spec:
                                resolved_type_spec = self._resolve_type_spec_enums(spec, spec["type_spec"])
                                node.details["type_spec"] = resolved_type_spec

                            return value

                logger.warning(f"Could not resolve value for {path}")
                node.result = None
                node.resolve_type = "NONE"

                if path in self.property_specs:
                    spec = self.property_specs[path]
                    node.required = bool(spec.get("required", False))
                    if node.required:
                        self.missing_required = True
                        logger.warning(f"This is a missing required value: {path}")

                    if "type" in spec:
                        node.details["type"] = spec["type"]
                    if "type_spec" in spec:
                        # Gebruik helper-methode om enum-referenties op te lossen
                        resolved_type_spec = self._resolve_type_spec_enums(spec, spec["type_spec"])
                        node.details["type_spec"] = resolved_type_spec

                return None
        finally:
            self.pop_path()

    def _resolve_date(self, path):
        if path == "calculation_date":
            return self.calculation_date
        if path == "january_first":
            calc_date = datetime.strptime(self.calculation_date, "%Y-%m-%d").date()
            return calc_date.replace(month=1, day=1).isoformat()
        if path == "prev_january_first":
            calc_date = datetime.strptime(self.calculation_date, "%Y-%m-%d").date()
            return calc_date.replace(month=1, day=1, year=calc_date.year - 1).isoformat()
        if path == "year":
            return self.calculation_date[:4]
        return None

    def _resolve_from_service(self, path, service_ref, spec):
        parameters = copy(self.parameters)
        if "parameters" in service_ref:
            parameters.update({p["name"]: self.resolve_value(p["reference"]) for p in service_ref["parameters"]})

        reference_date = self.calculation_date
        if "temporal" in spec and "reference" in spec["temporal"]:
            reference_date = self.resolve_value(spec["temporal"]["reference"])

        # Check cache - convert list values to strings for cache key
        def param_to_str(v):
            """Convert parameter value to string for cache key, handling lists and dicts"""
            if isinstance(v, list | dict):
                return str(v)
            return v

        cache_key = (
            f"{path}({','.join([f'{k}:{param_to_str(v)}' for k, v in sorted(parameters.items())])},{reference_date})"
        )
        if cache_key in self.values_cache:
            logger.debug(f"Resolving from CACHE with key '{cache_key}': {self.values_cache[cache_key]}")
            return self.values_cache[cache_key]

        logger.debug(f"Resolving from {service_ref['service']} field {service_ref['field']} ({parameters})")

        # Create service evaluation node
        details = {
            "service": service_ref["service"],
            "law": service_ref["law"],
            "field": service_ref["field"],
            "reference_date": reference_date,
            "parameters": parameters,
            "path": path,
        }

        # Copy type information from spec to details
        if "type" in spec:
            details["type"] = spec["type"]
        if "type_spec" in spec:
            details["type_spec"] = spec["type_spec"]

        service_node = PathNode(
            type="service_evaluation",
            name=f"Service call: {service_ref['service']}.{service_ref['law']}",
            result=None,
            details=details,
        )
        self.add_to_path(service_node)

        try:
            result = self.service_provider.evaluate(
                service_ref["service"],
                service_ref["law"],
                parameters,
                reference_date,
                self.overwrite_input,
                requested_output=service_ref["field"],
                approved=self.approved,
            )

            value = result.output.get(service_ref["field"])
            self.values_cache[cache_key] = value

            # Update the service node with the result and add child path
            service_node.result = value
            service_node.children.append(result.path)

            self.missing_required = self.missing_required or result.missing_required

            return value
        finally:
            self.pop_path()

    def _resolve_from_external(self, path, external_ref, spec):
        """
        Resolve a value from an external law reference (new architecture).

        Args:
            path: Variable path
            external_ref: External reference dict with 'law', 'field', 'parameters'
            spec: Property specification

        Returns:
            Resolved value from the external law
        """
        parameters = copy(self.parameters)
        if "parameters" in external_ref:
            parameters.update({p["name"]: self.resolve_value(p["reference"]) for p in external_ref["parameters"]})

        reference_date = self.calculation_date
        if "temporal" in spec and "reference" in spec["temporal"]:
            reference_date = self.resolve_value(spec["temporal"]["reference"])

        # Check cache
        def param_to_str(v):
            """Convert parameter value to string for cache key, handling lists and dicts"""
            if isinstance(v, list | dict):
                return str(v)
            return v

        cache_key = (
            f"{path}({','.join([f'{k}:{param_to_str(v)}' for k, v in sorted(parameters.items())])},{reference_date})"
        )
        if cache_key in self.values_cache:
            logger.debug(f"Resolving from CACHE with key '{cache_key}': {self.values_cache[cache_key]}")
            return self.values_cache[cache_key]

        logger.debug(f"Resolving from law {external_ref['law']} field {external_ref['field']} ({parameters})")

        # Create external evaluation node
        details = {
            "law": external_ref["law"],
            "field": external_ref["field"],
            "reference_date": reference_date,
            "parameters": parameters,
            "path": path,
        }

        # Copy type information from spec to details
        if "type" in spec:
            details["type"] = spec["type"]
        if "type_spec" in spec:
            details["type_spec"] = spec["type_spec"]

        external_node = PathNode(
            type="external_evaluation",
            name=f"External law call: {external_ref['law']}",
            result=None,
            details=details,
        )
        self.add_to_path(external_node)

        try:
            result = self.law_evaluator.evaluate_law(
                law=external_ref["law"],
                parameters=parameters,
                reference_date=reference_date,
                overwrite_input=self.overwrite_input,
                requested_output=external_ref["field"],
                approved=self.approved,
            )

            value = result.output.get(external_ref["field"])
            self.values_cache[cache_key] = value

            # Update the external node with the result and add child path
            external_node.result = value
            external_node.children.append(result.path)

            self.missing_required = self.missing_required or result.missing_required

            return value
        finally:
            self.pop_path()

    def _resolve_from_service_via_evaluator(self, path, service_ref, spec):
        """
        Resolve a value from a service_reference using the new law_evaluator (backward compatibility).

        This method handles old service_reference format but uses the new law_evaluator.
        The service parameter is ignored - only the law is used.

        Args:
            path: Variable path
            service_ref: Service reference dict with 'service' (ignored), 'law', 'field', 'parameters'
            spec: Property specification

        Returns:
            Resolved value from the law
        """
        # Convert service_reference to external_reference format
        external_ref = {
            "law": service_ref["law"],
            "field": service_ref["field"],
        }
        if "parameters" in service_ref:
            external_ref["parameters"] = service_ref["parameters"]

        # Log that we're ignoring the service parameter
        if "service" in service_ref:
            logger.debug(f"Ignoring service '{service_ref['service']}' (deprecated in new architecture)")

        # Use the external reference resolution
        return self._resolve_from_external(path, external_ref, spec)

    def _resolve_type_spec_enums(self, spec: dict[str, Any], type_spec: dict[str, Any]) -> dict[str, Any]:
        """
        Resolve enum references in type_spec voor arrays

        Args:
            spec: De volledige property specificatie
            type_spec: De type specificatie object

        Returns:
            Een kopie van de type_spec met opgeloste enum-referenties
        """
        # Maak een kopie van de type_spec om te voorkomen dat we het origineel wijzigen
        type_spec_copy = copy(type_spec)

        # Resolve enum references in type_spec voor arrays
        if "type" in spec and spec["type"] == "array" and "fields" in type_spec_copy:
            for field in type_spec_copy["fields"]:
                if "enum" in field and isinstance(field["enum"], str) and field["enum"].startswith("$"):
                    # Gebruik resolve_value om de enum-referentie op te lossen
                    enum_value = self.resolve_value(field["enum"])
                    if enum_value is not None:
                        # Ensure enum_value is a list
                        if isinstance(enum_value, list | tuple):
                            field["enum_values"] = enum_value
                            logger.debug(f"Resolved enum reference {field['enum']} to {field['enum_values']}")
                        else:
                            logger.warning(
                                f"Enum reference {field['enum']} resolved to non-iterable type {type(enum_value).__name__}: {enum_value}. Skipping."
                            )

        return type_spec_copy

    def _resolve_from_source(self, source_ref, table, df):
        if "select_on" in source_ref:
            for select_on in source_ref["select_on"]:
                value = self.resolve_value(select_on["value"])

                if isinstance(value, dict) and "operation" in value and value["operation"] == "IN":
                    allowed_values = self.resolve_value(value["values"])
                    df = df[df[select_on["name"]].isin(allowed_values)]
                else:
                    df = df[df[select_on["name"]] == value]

        # Get specified fields
        fields = source_ref.get("fields", [])
        field = source_ref.get("field")

        if fields:
            missing_fields = [f for f in fields if f not in df.columns]
            if missing_fields:
                logger.warning(f"Fields {missing_fields} not found in source for table {table}")
            existing_fields = [f for f in fields if f in df.columns]
            result = df[existing_fields].to_dict("records")
        elif field:
            if field not in df.columns:
                logger.warning(f"Field {field} not found in source for table {table}")
                return None
            result = df[field].tolist()
        else:
            result = df.to_dict("records")

        if result is None:
            return None
        if len(result) == 0:
            return None

        # Clean NaN values from the result
        result = clean_nan_value(result)

        # Check if result became None after cleaning
        if result is None:
            return None

        # Smart deduplication: if all values are identical (e.g., global data duplicated per profile),
        # deduplicate to a single value
        if (
            isinstance(result, list)
            and len(result) > 1
            and all(isinstance(v, str | int | float | bool | type(None)) for v in result)
            and len(set(str(v) for v in result)) == 1
        ):
            # All values are identical, return just one
            return result[0]

        if len(result) == 1:
            return result[0]
        return result


# Backward compatibility: RuleContext is now ExecutionContext
RuleContext = ExecutionContext
