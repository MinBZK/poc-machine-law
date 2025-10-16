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
class RuleContext:
    """Context for rule evaluation"""

    definitions: dict[str, Any]
    service_provider: Any | None
    parameters: dict[str, Any]
    property_specs: dict[str, dict[str, Any]]
    output_specs: dict[str, TypeSpec]
    sources: dict[str, pd.DataFrame]
    local: dict[str, Any] = field(default_factory=dict)
    accessed_paths: set[str] = field(default_factory=set)
    values_cache: dict[str, Any] = field(default_factory=dict)
    path: list[PathNode] = field(default_factory=list)
    overwrite_input: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    calculation_date: str | None = None
    resolved_paths: dict[str, Any] = field(default_factory=dict)
    service_name: str | None = None
    claims: dict[str:Claim] = None
    approved: bool | None = True
    missing_required: bool | None = False

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

                # Check definitions
                logger.debug(f"Checking definitions for path '{path}'. Available definitions: {list(self.definitions.keys())}")
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

                # Check overwrite data
                if path in self.property_specs:
                    spec = self.property_specs[path]
                    service_ref = spec.get("service_reference", {})
                    if (
                        service_ref
                        and service_ref["service"] in self.overwrite_input
                        and service_ref["field"] in self.overwrite_input[service_ref["service"]]
                    ):
                        value = self.overwrite_input[service_ref["service"]][service_ref["field"]]
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
                            df = self.service_provider.resolver.rules_dataframe()
                        if source_ref.get("source_type") == "events":
                            table = "events"
                            events = self.service_provider.case_manager.get_events()
                            df = pd.DataFrame(events)
                        elif self.sources and "table" in source_ref:
                            table = source_ref.get("table")
                            logger.debug(f"Looking for table '{table}' in sources. Available keys: {list(self.sources.keys())}")
                            if table in self.sources:
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

                # Check services
                if path in self.property_specs:
                    spec = self.property_specs[path]
                    service_ref = spec.get("service_reference", {})
                    if service_ref and self.service_provider:
                        value = self._resolve_from_service(path, service_ref, spec)
                        logger.debug(
                            f"Result for ${path} from {service_ref['service']} field {service_ref['field']}: {value}"
                        )
                        node.result = value
                        node.resolve_type = "SERVICE"
                        node.required = bool(spec.get("required", False))

                        # Add type information to the node
                        if "type" in spec:
                            node.details["type"] = spec["type"]
                        if "type_spec" in spec:
                            # Gebruik helper-methode om enum-referenties op te lossen
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
                        if isinstance(enum_value, (list, tuple)):
                            field["enum_values"] = enum_value
                            logger.debug(f"Resolved enum reference {field['enum']} to {field['enum_values']}")
                        else:
                            logger.warning(
                                f"Enum reference {field['enum']} resolved to non-iterable type {type(enum_value).__name__}: {enum_value}. Skipping."
                            )

        return type_spec_copy

    def _resolve_from_source(self, source_ref, table, df):
        logger.debug(f"_resolve_from_source called with table={table}, df shape={df.shape if df is not None else 'None'}")
        if "select_on" in source_ref:
            for select_on in source_ref["select_on"]:
                value = self.resolve_value(select_on["value"])
                col_name = select_on["name"]

                # Skip filtering if value is None (optional parameter not provided)
                if value is None:
                    logger.debug(f"Skipping filter on {col_name} (value is None)")
                    continue

                # Convert value to match the DataFrame column dtype
                if col_name in df.columns:
                    col_dtype = df[col_name].dtype
                    # Convert string to int if column is numeric
                    if pd.api.types.is_numeric_dtype(col_dtype) and isinstance(value, str):
                        try:
                            value = int(value)
                        except (ValueError, TypeError):
                            pass
                    # Convert int to string if column is object/string
                    elif pd.api.types.is_object_dtype(col_dtype) and isinstance(value, int | float):
                        value = str(value)

                if isinstance(value, dict) and "operation" in value and value["operation"] == "IN":
                    allowed_values = self.resolve_value(value["values"])
                    df = df[df[col_name].isin(allowed_values)]
                else:
                    df = df[df[col_name] == value]

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
                # Field doesn't exist - return the entire record as a dict instead
                logger.debug(f"Field {field} not found in source for table {table}, returning entire record")
                result = df.to_dict("records")
            else:
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
