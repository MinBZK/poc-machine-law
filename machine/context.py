import logging
from copy import copy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pandas as pd

from machine.events.claim.aggregate import Claim
from machine.logging_config import IndentLogger

logger = IndentLogger(logging.getLogger("service"))


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
        if self.type == "string":
            return str(value)

        if value is None:
            if self.type == "int":
                return 0
            if self.type == "float":
                return 0.0
            return value

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

    async def resolve_value(self, path: str) -> Any:
        value = await self._resolve_value(path)
        if isinstance(path, str):
            self.resolved_paths[path] = value
        return value

    async def _resolve_value(self, path: str) -> Any:
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
                value = await self._resolve_date(path)
                if value is not None:
                    logger.debug(f"Resolved date ${path}: {value}")
                    node.result = value
                    return value

                if "." in path:
                    root, rest = path.split(".", 1)
                    value = await self.resolve_value(f"${root}")
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
                if path in self.definitions:
                    logger.debug(f"Resolving from DEFINITION: {self.definitions[path]}")
                    node.result = self.definitions[path]
                    node.resolve_type = "DEFINITION"
                    return self.definitions[path]

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
                            if table in self.sources:
                                df = self.sources[table]

                        if df is not None:
                            result = await self._resolve_from_source(source_ref, table, df)
                            logger.debug(f"Resolving from SOURCE {table}: {result}")
                            node.result = result
                            node.resolve_type = "SOURCE"
                            node.required = bool(spec.get("required", False))

                            # Add type information to the node
                            if "type" in spec:
                                node.details["type"] = spec["type"]
                            if "type_spec" in spec:
                                node.details["type_spec"] = spec["type_spec"]

                            return result

                # Check services
                if path in self.property_specs:
                    spec = self.property_specs[path]
                    service_ref = spec.get("service_reference", {})
                    if service_ref and self.service_provider:
                        value = await self._resolve_from_service(path, service_ref, spec)
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
                            node.details["type_spec"] = spec["type_spec"]

                        return value

                logger.warning(f"Could not resolve value for {path}")
                node.result = None
                node.resolve_type = "NONE"

                if path in self.property_specs:
                    spec = self.property_specs[path]
                    node.required = bool(spec.get("required", False))
                    if "type" in spec:
                        node.details["type"] = spec["type"]
                    if "type_spec" in spec:
                        node.details["type_spec"] = spec["type_spec"]

                return None
        finally:
            self.pop_path()

    async def _resolve_date(self, path):
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

    async def _resolve_from_service(self, path, service_ref, spec):
        parameters = copy(self.parameters)
        if "parameters" in service_ref:
            parameters.update({p["name"]: await self.resolve_value(p["reference"]) for p in service_ref["parameters"]})

        reference_date = self.calculation_date
        if "temporal" in spec and "reference" in spec["temporal"]:
            reference_date = await self.resolve_value(spec["temporal"]["reference"])

        # Check cache
        cache_key = f"{path}({','.join([f'{k}:{v}' for k, v in sorted(parameters.items())])},{reference_date})"
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
            result = await self.service_provider.evaluate(
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

            return value
        finally:
            self.pop_path()

    async def _resolve_from_source(self, source_ref, table, df):
        if "select_on" in source_ref:
            for select_on in source_ref["select_on"]:
                value = await self.resolve_value(select_on["value"])

                if isinstance(value, dict) and "operation" in value and value["operation"] == "IN":
                    allowed_values = await self.resolve_value(value["values"])
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
        if len(result) == 1:
            return result[0]
        return result
