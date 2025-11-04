"""
DMN execution engine.

Evaluates DMN decisions using the parsed DMN model.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from machine.context import PathNode

from .context import DMNContext
from .exceptions import (
    CircularDependencyError,
    DecisionNotFoundError,
    DMNExecutionError,
    FEELEvaluationError,
)
from .feel_evaluator import FEELEvaluator
from .models import (
    BusinessKnowledgeModel,
    DecisionService,
    DecisionTable,
    DecisionTableRule,
    DMNDecision,
    DMNResult,
    DMNSpec,
    ExpressionType,
    HitPolicy,
    LiteralExpression,
)
from .xml_parser import DMNXMLParser


class DMNEngine:
    """Main DMN execution engine."""

    def __init__(self):
        self.xml_parser = DMNXMLParser()
        self.feel_evaluator = FEELEvaluator()
        self.loaded_specs: Dict[str, DMNSpec] = {}
        self.imported_specs: Dict[str, Dict[str, DMNSpec]] = {}  # {parent_spec_id: {namespace: imported_spec}}

    def load_dmn(self, file_path: Path) -> DMNSpec:
        """
        Load and parse a DMN file.

        Args:
            file_path: Path to DMN XML file

        Returns:
            Parsed DMNSpec

        Raises:
            DMNParseError: If parsing fails
        """
        file_path = Path(file_path)
        cache_key = str(file_path.absolute())

        if cache_key in self.loaded_specs:
            return self.loaded_specs[cache_key]

        spec = self.xml_parser.parse(file_path)
        self.loaded_specs[cache_key] = spec

        # Load imported DMN specs
        self._load_imports(spec)

        return spec

    def _load_imports(self, dmn_spec: DMNSpec):
        """Load all imported DMN specifications."""
        if dmn_spec.id not in self.imported_specs:
            self.imported_specs[dmn_spec.id] = {}

        for dmn_import in dmn_spec.imports:
            # Skip if already loaded
            if dmn_import.namespace in self.imported_specs[dmn_spec.id]:
                continue

            # Resolve import path relative to parent DMN file
            import_path = dmn_spec.file_path.parent / dmn_import.location_uri

            # Load the imported spec
            imported_spec = self.load_dmn(import_path)
            self.imported_specs[dmn_spec.id][dmn_import.namespace] = imported_spec

    def evaluate(
        self,
        dmn_spec: DMNSpec,
        decision_id: str,
        parameters: Dict[str, Any],
    ) -> DMNResult:
        """
        Evaluate a specific decision in a DMN model.

        Args:
            dmn_spec: Parsed DMN specification
            decision_id: ID of the decision to evaluate
            parameters: Input parameters

        Returns:
            DMNResult with output and trace

        Raises:
            DecisionNotFoundError: If decision doesn't exist
            DMNExecutionError: If evaluation fails
        """
        # Find decision
        if decision_id not in dmn_spec.decisions:
            raise DecisionNotFoundError(f"Decision not found: {decision_id}")

        decision = dmn_spec.decisions[decision_id]

        # Create execution context
        context = DMNContext(parameters=parameters)

        # Create root path node
        root_path = PathNode(
            type="dmn_evaluation",
            name=decision.name,
            result=None,
            details={"decision_id": decision_id, "decision_name": decision.name},
            children=[],
        )
        context.path = root_path
        context.current_path = root_path

        # Evaluate decision
        try:
            result = self._evaluate_decision(dmn_spec, decision, context)

            return DMNResult(
                output={decision.variable_name: result},
                decision_id=decision_id,
                requirements_met=True,
                input=parameters,
                dmn_spec_id=dmn_spec.id,
                path=context.path,
                missing_required=False,
                errors=context.errors,
            )

        except Exception as e:
            context.add_error(str(e))
            return DMNResult(
                output={},
                decision_id=decision_id,
                requirements_met=False,
                input=parameters,
                dmn_spec_id=dmn_spec.id,
                path=context.path,
                missing_required=True,
                errors=context.errors,
            )

    def _evaluate_decision(
        self,
        dmn_spec: DMNSpec,
        decision: DMNDecision,
        context: DMNContext,
    ) -> Any:
        """Evaluate a single decision."""
        # Check if already evaluated (caching)
        if context.has_decision_result(decision.id):
            return context.get_decision_result(decision.id)

        # Create path node for this decision
        decision_path = PathNode(
            type="decision",
            name=decision.name,
            result=None,
            details={"decision_id": decision.id, "decision_name": decision.name},
            children=[],
        )
        context.push_path(decision_path)

        try:
            # Evaluate required decisions first (dependencies)
            for req_decision_id in decision.required_decisions:
                if req_decision_id not in dmn_spec.decisions:
                    raise DecisionNotFoundError(f"Required decision not found: {req_decision_id}")

                req_decision = dmn_spec.decisions[req_decision_id]
                req_result = self._evaluate_decision(dmn_spec, req_decision, context)

                # Add to context for use in expressions
                # Store by both ID (for caching) and variable_name (for FEEL access)
                context.add_decision_result(req_decision_id, req_result)
                context.add_decision_result(req_decision.variable_name, req_result)

            # Evaluate expression based on type
            if decision.expression_type == ExpressionType.LITERAL:
                result = self._evaluate_literal_expression(
                    decision.expression, context, dmn_spec
                )
            elif decision.expression_type == ExpressionType.DECISION_TABLE:
                result = self._evaluate_decision_table(
                    decision.expression, context, dmn_spec
                )
            else:
                raise DMNExecutionError(
                    f"Unsupported expression type: {decision.expression_type}"
                )

            # Cache result
            context.add_decision_result(decision.id, result)

            # Set result in path
            context.pop_path(result)

            return result

        except Exception as e:
            context.add_error(f"Error evaluating decision {decision.name}: {e}")
            raise

    def _evaluate_literal_expression(
        self,
        expression: LiteralExpression,
        context: DMNContext,
        dmn_spec: DMNSpec,
    ) -> Any:
        """Evaluate a literal FEEL expression."""
        if not expression or not expression.text:
            return None

        # Build FEEL context from all available values
        feel_context = context.get_all_values()

        # Add BKMs as callable functions
        # Use BKM ID without "bkm_" prefix as function name, or fall back to variable_name
        for bkm_id, bkm in dmn_spec.bkms.items():
            if bkm_id.startswith('bkm_'):
                func_name = bkm_id[4:]  # Remove "bkm_" prefix
            else:
                func_name = bkm.variable_name
            feel_context[func_name] = lambda *args, b=bkm: self._invoke_bkm(
                b, args, context, dmn_spec
            )

        # Add decision services from imported DMN specs as callable functions
        if dmn_spec.id in self.imported_specs:
            for namespace, imported_spec in self.imported_specs[dmn_spec.id].items():
                for ds_id, decision_service in imported_spec.decision_services.items():
                    # Use decision service ID converted to snake_case as function name
                    # e.g., "decisionService_brp" from "decisionService_brp"
                    func_name = ds_id
                    feel_context[func_name] = lambda *args, ds=decision_service, spec=imported_spec: self._invoke_decision_service(
                        spec, ds, args, context
                    )

        try:
            result = self.feel_evaluator.evaluate(expression.text, feel_context)
            return result
        except FEELEvaluationError as e:
            raise DMNExecutionError(f"FEEL evaluation failed: {e}") from e

    def _evaluate_decision_table(
        self,
        table: DecisionTable,
        context: DMNContext,
        dmn_spec: DMNSpec,
    ) -> Any:
        """Evaluate a decision table."""
        # Build FEEL context
        feel_context = context.get_all_values()

        # Evaluate each rule
        matching_rules = []

        for rule in table.rules:
            # Check if all input conditions match
            matches = True

            for i, input_col in enumerate(table.inputs):
                if i >= len(rule.input_entries):
                    continue

                input_entry = rule.input_entries[i]

                # '-' means "any value" (always matches)
                if input_entry == '-':
                    continue

                # Evaluate input expression
                try:
                    input_value = self.feel_evaluator.evaluate(
                        input_col.input_expression, feel_context
                    )
                except FEELEvaluationError:
                    matches = False
                    break

                # Evaluate condition
                try:
                    # Check for comma-separated list FIRST (before quote check)
                    if ',' in input_entry:
                        # List of values: "value1", "value2"
                        allowed_values = [
                            self.feel_evaluator.evaluate(v.strip(), feel_context)
                            for v in input_entry.split(',')
                        ]
                        if input_value not in allowed_values:
                            matches = False
                            break
                    elif input_entry.startswith('"') or input_entry.startswith("'"):
                        # Literal string comparison
                        condition_value = self.feel_evaluator.evaluate(
                            input_entry, feel_context
                        )
                        if input_value != condition_value:
                            matches = False
                            break
                    else:
                        # Expression that should evaluate to boolean or value to compare
                        # Create temporary context with input value
                        temp_context = feel_context.copy()
                        temp_context['?'] = input_value  # DMN uses ? for input value

                        condition_result = self.feel_evaluator.evaluate(
                            input_entry, temp_context
                        )

                        # Distinguish between predicate expressions and literal values
                        if '?' in input_entry:
                            # Predicate expression (e.g., "? > 5") - result is match/no-match
                            if isinstance(condition_result, bool):
                                if not condition_result:
                                    matches = False
                                    break
                            else:
                                # Predicate should return boolean
                                if condition_result != input_value:
                                    matches = False
                                    break
                        else:
                            # Literal value (e.g., "true", "5") - compare with input_value
                            if condition_result != input_value:
                                matches = False
                                break

                except FEELEvaluationError:
                    matches = False
                    break

            if matches:
                matching_rules.append(rule)

        # Apply hit policy
        if not matching_rules:
            return None

        if table.hit_policy == HitPolicy.UNIQUE or table.hit_policy == HitPolicy.FIRST:
            # Return first matching rule's output
            rule = matching_rules[0]
            return self._evaluate_rule_output(rule, table, feel_context)

        elif table.hit_policy == HitPolicy.ANY:
            # Return first (all should be same)
            rule = matching_rules[0]
            return self._evaluate_rule_output(rule, table, feel_context)

        elif table.hit_policy == HitPolicy.COLLECT:
            # Return list of all outputs
            results = []
            for rule in matching_rules:
                output = self._evaluate_rule_output(rule, table, feel_context)
                results.append(output)
            return results

        else:
            raise DMNExecutionError(
                f"Unsupported hit policy: {table.hit_policy}"
            )

    def _evaluate_rule_output(
        self,
        rule: DecisionTableRule,
        table: DecisionTable,
        feel_context: Dict[str, Any],
    ) -> Any:
        """Evaluate the output of a matching rule."""
        if len(table.outputs) == 1:
            # Single output
            output_entry = rule.output_entries[0]
            return self.feel_evaluator.evaluate(output_entry, feel_context)
        else:
            # Multiple outputs - return as dict
            result = {}
            for i, output_col in enumerate(table.outputs):
                if i < len(rule.output_entries):
                    output_entry = rule.output_entries[i]
                    value = self.feel_evaluator.evaluate(output_entry, feel_context)
                    result[output_col.name] = value
            return result

    def _invoke_bkm(
        self,
        bkm: BusinessKnowledgeModel,
        args: tuple,
        context: DMNContext,
        dmn_spec: DMNSpec,
    ) -> Any:
        """Invoke a Business Knowledge Model."""
        # Build context with parameter bindings
        param_context = context.get_all_values().copy()

        for i, param in enumerate(bkm.parameters):
            if i < len(args):
                param_context[param.variable_name] = args[i]

        # Evaluate BKM expression
        if isinstance(bkm.expression, LiteralExpression):
            result = self.feel_evaluator.evaluate(bkm.expression.text, param_context)
            return result
        else:
            raise DMNExecutionError(f"Unsupported BKM expression type for {bkm.name}")

    def _invoke_decision_service(
        self,
        imported_spec: DMNSpec,
        decision_service: DecisionService,
        args: tuple,
        parent_context: DMNContext,
    ) -> Dict[str, Any]:
        """
        Invoke a decision service from an imported DMN spec.

        Args:
            imported_spec: The imported DMN specification
            decision_service: The decision service to invoke
            args: Arguments passed to the decision service
            parent_context: The parent execution context

        Returns:
            Dict with output decision results
        """
        # Build parameters dict from args
        # Match args to input data based on order in decision_service.input_data
        parameters = {}
        for i, input_id in enumerate(decision_service.input_data):
            if i < len(args):
                # Get input variable name from imported spec
                if input_id in imported_spec.inputs:
                    var_name = imported_spec.inputs[input_id].variable_name
                    parameters[var_name] = args[i]

        # Create new context for the decision service evaluation
        service_context = DMNContext(parameters=parameters)

        # Evaluate all output decisions
        results = {}
        for decision_id in decision_service.output_decisions:
            if decision_id in imported_spec.decisions:
                decision = imported_spec.decisions[decision_id]
                result = self._evaluate_decision(imported_spec, decision, service_context)
                results[decision.variable_name] = result

        # If only one output decision, return just the value instead of a dict
        if len(results) == 1:
            return list(results.values())[0]

        return results
