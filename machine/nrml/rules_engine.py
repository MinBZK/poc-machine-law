import functools
import operator
from collections import defaultdict
from copy import copy
from datetime import date, datetime
from typing import Any

import pandas as pd

from ..context import PathNode, RuleContext, TypeSpec, logger


class NrmlRulesEngine:
    """Rules engine for evaluating business rules"""

    def __init__(self, spec: dict[str, Any], service_provider: Any | None = None) -> None:
        self.spec = spec
        self.facts = spec.get("facts", {})
        self.items = {}
        self.law = spec.get("metadata", {}).get("description", {})

        # Fill items dictionary with JSON Pointer references
        for fact_id, fact in self.facts.items():
            items = fact.get("items", {})
            for item_id, item in items.items():
                ref_key = f"#/facts/{fact_id}/items/{item_id}"
                self.items[ref_key] = item

        self.service_name = "NRML"
        self.service_provider = service_provider


    @staticmethod
    def topological_sort(dependencies: dict[str, set]) -> list[str]:
        """
        Perform topological sort on dependencies.
        Returns outputs in order they should be calculated.
        """
        # First create complete set of all nodes including leaf nodes
        all_nodes = set(dependencies.keys())
        for deps in dependencies.values():
            all_nodes.update(deps)

        # Initialize complete dependency map
        complete_dependencies = {node: set() for node in all_nodes}
        complete_dependencies.update(dependencies)

        # Build adjacency list
        graph = defaultdict(set)
        for output, deps in complete_dependencies.items():
            for dep in deps:
                graph[dep].add(output)

        # Find nodes with no dependencies
        ready = [node for node, deps in complete_dependencies.items() if not deps]
        sorted_outputs = []

        while ready:
            node = ready.pop(0)
            sorted_outputs.append(node)

            # Remove this node as dependency
            dependents = graph[node]
            for dependent in list(dependents):
                complete_dependencies[dependent].remove(node)
                # If no more dependencies, add to ready
                if not complete_dependencies[dependent]:
                    ready.append(dependent)
                dependents.remove(dependent)

        if any(deps for deps in complete_dependencies.values()):
            raise ValueError("Circular dependency detected")

        return sorted_outputs

    @staticmethod
    def analyze_dependencies(action):
        """Find all outputs this action depends on"""
        deps = set()

        def traverse(obj) -> None:
            if isinstance(obj, str):
                if obj.startswith("$"):
                    value = obj[1:]  # Remove $ prefix
                    if value.islower():  # Output reference
                        deps.add(value)
            elif isinstance(obj, dict):
                for v in obj.values():
                    traverse(v)
            elif isinstance(obj, list):
                for item in obj:
                    traverse(item)

        traverse(action)
        return deps

    @staticmethod
    def get_required_actions(requested_output: list[str], items: dict[str, Any]) -> list:
        """Get all actions needed to compute requested output in dependency order"""
        if not requested_output:
            return items

        to_process = set(requested_output)
        while to_process:
            output = to_process.pop()
            item = items.get(output)
            # what if item is missing?

            # TODO: recursively find where this item is used


        # old stuff
        # Build dependency graph
        dependencies = {}
        action_by_output = {}
        for action in items:
            output = action["output"]
            action_by_output[output] = action
            dependencies[output] = NrmlRulesEngine.analyze_dependencies(action)

        # Find all required outputs
        required = set()
        to_process = set(requested_output)

        while to_process:
            output = to_process.pop()
            required.add(output)
            # Add dependencies to processing queue
            deps = dependencies.get(output, set())
            to_process.update(deps - required)

        # Get execution order via topological sort
        ordered_outputs = NrmlRulesEngine.topological_sort(
            {output: deps for output, deps in dependencies.items() if output in required}
        )

        # Return actions in dependency order
        return [action_by_output[output] for output in ordered_outputs if output in action_by_output]

    def evaluate(
        self,
        parameters: dict[str, Any] | None = None,
        overwrite_input: dict[str, Any] | None = None,
        sources: dict[str, pd.DataFrame] | None = None,
        calculation_date=None,
        requested_output: str | None = None,
        approved: bool = False,
    ) -> dict[str, Any]:
        """Evaluate rules using service context and sources"""
        parameters = parameters or {}

        # TODO: temp reference to result item in brp
        requested_output = "#/facts/f1e2d3c4-5b6a-7c8d-9e0f-1a2b3c4d5e6f/items/a2f3e4d5-6c7b-8d9e-0f1a-2b3c4d5e6f78"

        logger.debug(f"Evaluating rules for {self.service_name} {self.law} ({calculation_date} {requested_output})")

        claims = None
        if "BSN" in parameters:
            bsn = parameters["BSN"]
            claims = self.service_provider.claim_manager.get_claim_by_bsn_service_law(
                bsn, self.service_name, self.law, approved=approved
            )

        context = RuleContext(
            definitions=self.facts,
            service_provider="NRML",
            parameters=parameters,
            property_specs={},
            output_specs={},
            sources=sources or {},
            overwrite_input=overwrite_input or {},
            calculation_date=calculation_date,
            service_name=self.service_name,
            claims=claims,
            approved=approved,
        )

        output_values = {}
        requirements_met = True


        # Get required actions including dependencies in order
        required_actions = self.get_required_actions(requested_output, self.items)

        for action in required_actions:
            output_def, output_name = self._evaluate_action(action, context)
            context.outputs[output_name] = output_def["value"]
            output_values[output_name] = output_def
            if context.missing_required:
                logger.warning("Missing required values, breaking")
                break

        if context.missing_required:
            logger.warning("Missing required values, requirements not met, setting outputs to empty.")
            output_values = {}
            requirements_met = False

        if not output_values:
            logger.warning(f"No output values computed for {calculation_date} {requested_output}")

        return {
            "input": context.resolved_paths,
            "output": output_values,
            "requirements_met": requirements_met,
            "missing_required": context.missing_required,
        }

    def _evaluate_action(self, action, context):
        with logger.indent_block(f"Computing {action.get('output', '')}"):
            if action["output"] == "partner_bsn":
                pass
            action_node = PathNode(
                type="action",
                name=f"Evaluate action for {action.get('output', '')}",
                result=None,
            )
            context.add_to_path(action_node)
            output_name = action["output"]
            # Find output specification
            output_spec = next(
                (spec for spec in self.spec.get("properties", {}).get("output", []) if spec.get("name") == output_name),
                {},
            )

            if (
                self.service_name in context.overwrite_input
                and output_name in context.overwrite_input[self.service_name]
            ):
                raw_result = context.overwrite_input[self.service_name][output_name]
                logger.debug(f"Resolving value {self.service_name}/{output_name} from OVERWRITE {raw_result}")
            elif "operation" in action:
                raw_result = self._evaluate_operation(action, context)
            elif "value" in action:
                raw_result = self._evaluate_value(action["value"], context)
            else:
                raw_result = None

            result = self._enforce_output_type(output_name, raw_result)
        action_node.result = result
        logger.debug(f"Result of {action.get('output', '')}: {result}")
        # Build output with metadata
        output_def = {
            "value": result,
            "type": output_spec.get("type", "unknown"),
            "description": output_spec.get("description", ""),
        }
        # Add type_spec if present
        if "type_spec" in output_spec:
            output_def["type_spec"] = output_spec["type_spec"]
        # Add temporal if present
        if "temporal" in output_spec:
            output_def["temporal"] = output_spec["temporal"]
        return output_def, output_name

    def _evaluate_requirements(self, requirements: list, context: RuleContext) -> bool:
        """Evaluate all requirements"""
        if not requirements:
            logger.debug("No requirements found")
            return True

        for req in requirements:
            with logger.indent_block(f"Requirements {req}"):
                node = PathNode(
                    type="requirement",
                    name="Check ALL conditions"
                    if "all" in req
                    else "Check OR conditions"
                    if "or" in req
                    else "Test condition",
                    result=None,
                )
                context.add_to_path(node)

                if "all" in req:
                    results = []
                    for r in req["all"]:
                        result = self._evaluate_requirements([r], context)
                        results.append(result)
                        if not bool(result):
                            logger.debug("False value found in an ALL, no need to compute the rest, breaking.")
                            break
                    result = all(results)
                elif "or" in req:
                    results = []
                    for r in req["or"]:
                        result = self._evaluate_requirements([r], context)
                        results.append(result)
                        if bool(result):
                            logger.debug("True value found in an OR, no need to compute the rest, breaking.")
                            break
                    result = any(results)
                else:
                    result = self._evaluate_operation(req, context)

            logger.debug("Requirement met" if result else "Requirement NOT met")

            node.result = result
            context.pop_path()

            if not result:
                return False

        return True

    def _evaluate_if_operation(self, operation: dict[str, Any], context: RuleContext) -> Any:
        """Evaluate an IF operation"""
        with logger.indent_block("Evaluating IF"):
            if_node = PathNode(
                type="operation",
                name="IF conditions",
                result=None,
                details={"condition_results": []},
            )
            context.add_to_path(if_node)

            result = 0
            conditions = operation.get("conditions", [])

            for i, condition in enumerate(conditions):
                condition_result = {
                    "condition_index": i,
                    "type": "test" if "test" in condition else "else",
                }

                if "test" in condition:
                    test_result = self._evaluate_operation(condition["test"], context)
                    condition_result["test_result"] = test_result
                    if test_result:
                        result = self._evaluate_value(condition["then"], context)
                        if_node.details["condition_results"].append(condition_result)
                        logger.debug(f"THEN condition: {result}")
                        break
                elif "else" in condition:
                    result = self._evaluate_value(condition["else"], context)
                    condition_result["else_value"] = result
                    if_node.details["condition_results"].append(condition_result)
                    logger.debug(f"ELSE condition: {result}")
                    break

                if_node.details["condition_results"].append(condition_result)

            if_node.result = result
            context.pop_path()
            return result

    def _evaluate_foreach(self, operation, context):
        """Handle FOREACH operation"""
        logger.debug("For each condition")

        combine = operation.get("combine")

        array_data = self._evaluate_value(operation["subject"], context)
        if "DECLARED_HOURS" in operation["subject"]:
            pass
        if not array_data:
            logger.warning("No data found to run FOREACH on")
            return self._evaluate_aggregate_ops(combine, [])

        if not isinstance(array_data, list):
            array_data = [array_data]

        with logger.indent_block(f"Foreach({combine})"):
            values = []
            for item in array_data:
                with logger.indent_block(f"Item {item}"):
                    item_context = copy(context)
                    if isinstance(item, dict):
                        item_context.local.update(item)
                    for i in range(100):
                        if f"current_{i}" not in item_context.local:
                            item_context.local[f"current_{i}"] = item
                            break
                    value_to_evaluate = (
                        operation["value"][0] if isinstance(operation["value"], list) else operation["value"]
                    )
                    result = self._evaluate_value(value_to_evaluate, item_context)
                    context.missing_required = context.missing_required or item_context.missing_required
                    context.path = item_context.path
                    values.extend(result if isinstance(result, list) else [result])
            logger.debug(f"Foreach values: {values}")
            result = self._evaluate_aggregate_ops(combine, values) if combine else values
            logger.debug(f"Foreach result: {result}")
        return result

    COMPARISON_OPS = {
        "EQUALS": operator.eq,
        "NOT_EQUALS": operator.ne,
        "GREATER_THAN": operator.gt,
        "LESS_THAN": operator.lt,
        "GREATER_OR_EQUAL": operator.ge,
        "LESS_OR_EQUAL": operator.le,
    }

    AGGREGATE_OPS = {
        "OR": any,
        "AND": all,
        "MIN": min,
        "MAX": max,
        "ADD": sum,
        "CONCAT": lambda vals: "".join(str(x) for x in vals),
        "MULTIPLY": lambda vals: functools.reduce(
            lambda x, y: int(x * y) if isinstance(y, int) and y < 1 else x * y,
            vals[1:],
            vals[0],
        ),
        "SUBTRACT": lambda vals: functools.reduce(operator.sub, vals[1:], vals[0]),
        "DIVIDE": lambda vals: (
            functools.reduce(lambda x, y: x / y if y != 0 else 0, vals[1:], float(vals[0])) if 0 not in vals[1:] else 0
        ),
    }

    @staticmethod
    def _evaluate_aggregate_ops(op: str, values: list[Any]) -> int | float | bool:
        """Handle aggregate operations"""
        filtered_values = [v for v in values if v is not None]

        if not filtered_values:
            logger.warning(f"No values found (or they where None), returning 0 for {op}({values})")
            return 0
        elif len(filtered_values) < len(values):
            logger.warning(f"Dropped {len(values) - len(filtered_values)} values because they where None")

        result = NrmlRulesEngine.AGGREGATE_OPS[op](filtered_values)
        logger.debug(f"Compute {op}({filtered_values}) = {result}")
        return result

    @staticmethod
    def _evaluate_comparison(op: str, left: Any, right: Any) -> bool | None:
        """Handle comparison operations"""
        if isinstance(left, date) and isinstance(right, str):
            right = datetime.strptime(right, "%Y-%m-%d").date()
        elif isinstance(right, date) and isinstance(left, str):
            left = datetime.strptime(left, "%Y-%m-%d").date()

        try:
            result = NrmlRulesEngine.COMPARISON_OPS[op](left, right)
            logger.debug(f"Compute {op}({left}, {right}) = {result}")
        except TypeError as e:
            logger.warning(f"Error computing {op}({left}, {right}): {e}")
            result = None

        return result

    @staticmethod
    def _evaluate_date_operation(op: str, values: list[Any], unit: str, context: RuleContext) -> int | None:
        """Handle date-specific operations with comprehensive validation"""

        def validate_and_convert_date(date_val: Any, name: str) -> datetime | None:
            """Validate and convert a date value to datetime with comprehensive error handling"""
            if date_val is None:
                context.missing_required = True
                logger.warning(f"Missing date value for {name} in {op} operation")
                return None

            if isinstance(date_val, datetime):
                return date_val

            # Check for empty or invalid string types
            if isinstance(date_val, str):
                if not date_val.strip():
                    context.missing_required = True
                    logger.warning(f"Empty date string for {name} in {op} operation")
                    return None
            elif not isinstance(date_val, str | int | float):
                # Invalid type that can't be converted to string
                context.missing_required = True
                logger.warning(f"Invalid date type for {name}: {type(date_val)} = {date_val}")
                return None

            try:
                return datetime.fromisoformat(str(date_val))
            except (ValueError, TypeError) as e:
                context.missing_required = True
                logger.warning(f"Cannot parse date for {name}: {date_val} ({e})")
                return None

        if op == "SUBTRACT_DATE":
            # Validate quantity
            if len(values) != 2:
                context.missing_required = True
                logger.warning(f"SUBTRACT_DATE requires exactly 2 values, got {len(values)}")
                return None

            end_date, start_date = values

            # Apply default for end_date if falsy (but not None, which is handled in validation)
            if not end_date and end_date is not None:
                end_date = context.calculation_date

            # Validate and convert both dates
            end_date_converted = validate_and_convert_date(end_date, "end_date")
            start_date_converted = validate_and_convert_date(start_date, "start_date")

            # Return None if either date is invalid
            if end_date_converted is None or start_date_converted is None:
                return None

            # Calculate the difference
            delta = end_date_converted - start_date_converted

            # Convert to requested unit
            if unit == "days":
                result = delta.days
            elif unit == "years":
                result = (
                    end_date_converted.year
                    - start_date_converted.year
                    - (
                        (end_date_converted.month, end_date_converted.day)
                        < (start_date_converted.month, start_date_converted.day)
                    )
                )
            elif unit == "months":
                result = (
                    (end_date_converted.year - start_date_converted.year) * 12
                    + end_date_converted.month
                    - start_date_converted.month
                )
            else:
                logger.warning(f"Unknown date unit '{unit}', defaulting to days")
                result = delta.days

            logger.debug(f"Compute {op}({values}, {unit}) = {result}")
            return result

        # Handle other date operations if added in the future
        logger.warning(f"Unknown date operation: {op}")
        return None

    def _evaluate_operation(self, operation: dict[str, Any], context: RuleContext) -> Any:
        """Evaluate an operation or condition"""

        if not isinstance(operation, dict):
            node = PathNode(
                type="value",
                name="Direct value evaluation",
                result=None,
                details={"raw_value": operation},
            )
            context.add_to_path(node)
            result = self._evaluate_value(operation, context)
            node.result = result
            context.pop_path()
            return result

        # Direct value assignment - no operation needed
        if "value" in operation and not operation.get("operation"):
            node = PathNode(
                type="direct_value",
                name="Direct value assignment",
                result=None,
                details={"raw_value": operation["value"]},
            )
            context.add_to_path(node)
            result = self._evaluate_value(operation["value"], context)
            node.result = result
            context.pop_path()
            return result

        op_type = operation.get("operation")
        node = PathNode(
            type="operation",
            name=f"Operation: {op_type}",
            result=None,
            details={"operation_type": op_type},
        )
        context.add_to_path(node)

        if op_type is None:
            logger.warning("Operation type is None (or missing).")
            result = None

        elif op_type == "IF":
            result = self._evaluate_if_operation(operation, context)

        elif op_type == "FOREACH":
            result = self._evaluate_foreach(operation, context)
            node.details.update({"raw_values": operation["value"], "arithmetic_type": op_type})

        elif op_type in ["IN", "NOT_IN"]:
            with logger.indent_block(op_type):
                subject = self._evaluate_value(operation["subject"], context)
                allowed_values = self._evaluate_value(operation.get("values", []), context)

                result = subject in (
                    allowed_values if isinstance(allowed_values, list | dict | set) else [allowed_values]
                )
                if op_type == "NOT_IN":
                    result = not result

            node.details.update({"subject_value": subject, "allowed_values": allowed_values})
            logger.debug(f"Result {subject} {op_type} {allowed_values}: {result}")

        elif op_type == "NOT_NULL":
            subject = self._evaluate_value(operation["subject"], context)
            result = subject is not None
            node.details["subject_value"] = subject
            logger.debug(f"NOT_NULL result: {result}")

        elif op_type == "IS_NULL":
            subject = self._evaluate_value(operation["subject"], context)
            result = subject is None
            node.details["subject_value"] = subject
            logger.debug(f"IS_NULL result: {result}")

        elif op_type == "AND":
            with logger.indent_block("AND"):
                values = []
                for v in operation["values"]:
                    r = self._evaluate_value(v, context)
                    values.append(r)
                    if not bool(r):
                        logger.debug("False value found in an AND, no need to compute the rest, breaking.")
                        break
                result = all(bool(v) for v in values)

            node.details["evaluated_values"] = values
            logger.debug(f"Result {list(values)} AND: {result}")

        elif op_type == "OR":
            with logger.indent_block("OR"):
                values = []
                for v in operation["values"]:
                    r = self._evaluate_value(v, context)
                    values.append(r)
                    if bool(r):
                        logger.debug("True value found in an OR, no need to compute the other, breaking.")
                        break
                result = any(bool(v) for v in values)
            node.details["evaluated_values"] = values
            logger.debug(f"Result {list(values)} OR: {result}")

        elif "_DATE" in op_type:
            values = [self._evaluate_value(v, context) for v in operation["values"]]
            unit = operation.get("unit", "days")
            result = self._evaluate_date_operation(op_type, values, unit, context)
            node.details.update({"evaluated_values": values, "unit": unit})

        elif op_type in self.COMPARISON_OPS:
            subject = None
            value = None

            if "subject" in operation:
                subject = self._evaluate_value(operation["subject"], context)
                value = self._evaluate_value(operation["value"], context)

            elif "values" in operation:
                values = [self._evaluate_value(v, context) for v in operation["values"]]
                subject = values[0]
                value = values[1]
            else:
                logger.warning("Comparison operation expects two values or subject/value.")

            result = self._evaluate_comparison(op_type, subject, value)

            node.details.update(
                {
                    "subject_value": subject,
                    "comparison_value": value,
                    "comparison_type": op_type,
                }
            )

        elif op_type in self.AGGREGATE_OPS and "values" in operation:
            # The operation dict has legal_basis as metadata alongside operation/values
            # but we only need to evaluate the 'values' list, ignoring legal_basis metadata
            values = [self._evaluate_value(v, context) for v in operation["values"]]
            result = self._evaluate_aggregate_ops(op_type, values)
            node.details.update(
                {
                    "raw_values": operation["values"],
                    "evaluated_values": values,
                    "arithmetic_type": op_type,
                }
            )

        elif op_type == "GET":
            subject = self._evaluate_value(operation["subject"], context)
            values = self._evaluate_value(operation.get("values", []), context)
            result = values.get(subject)
            node.details.update({"subject_value": subject, "allowed_values": values})
            logger.debug(f"GET {subject} from {values}: {result}")

        else:
            result = None
            node.details["error"] = "Invalid operation format"
            logger.warning(f"Not matched to any operation {op_type}")

        node.result = result
        context.pop_path()
        return result

    def _evaluate_value(self, value: Any, context: RuleContext) -> Any:
        """Evaluate a value which might be a number, operation, or reference"""
        if isinstance(value, int | float | bool | date | datetime) or value is None:
            return value
        elif isinstance(value, dict) and "operation" in value:
            return self._evaluate_operation(value, context)
        else:
            return context.resolve_value(value)
