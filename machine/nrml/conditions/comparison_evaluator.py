from collections.abc import Callable
from typing import Any

from ..aggregation_context import AggregationContext
from ..context import NrmlRuleContext
from ..evaluation_result import EvaluationResult, create_result
from ..expressions.argument_resolver import ArgumentResolver


class ComparisonEvaluator:
    """Evaluator for comparison conditions"""

    def __init__(self):
        """Initialize evaluator with internal state"""
        self.argument_resolver = ArgumentResolver()
        self.operators: dict[str, Callable[[EvaluationResult, EvaluationResult, NrmlRuleContext], EvaluationResult]] = {
            "in": self._evaluate_in_comparison,
            "lessThanOrEqual": self._evaluate_less_than_or_equal,
        }

    def evaluate(
        self,
        expression: dict[str, Any],
        context: NrmlRuleContext,
        aggregation_context: AggregationContext | None = None,
    ) -> EvaluationResult:
        """Evaluate a comparison expression"""
        operator = expression.get("operator")
        arguments = expression.get("arguments", [])

        # Validate argument count
        if len(arguments) != 2:
            return create_result(
                success=False,
                error=f"Comparison operator '{operator}' expects 2 arguments, got {len(arguments)}",
                source=self.__class__.__name__,
            )

        # Unpack arguments
        left_arg, right_arg = arguments

        # Resolve arguments
        left_value = self.argument_resolver.resolve_argument(left_arg, context, aggregation_context)
        right_value = self.argument_resolver.resolve_argument(right_arg, context, aggregation_context)

        # Check if both arguments resolved successfully
        if not (left_value.Success and right_value.Success):
            return create_result(
                success=False,
                error="Unable to resolve all arguments",
                source=self.__class__.__name__,
                dependencies=[left_value, right_value],
            )

        # Look up operator handler
        handler = self.operators.get(operator)
        if handler is None:
            raise ValueError(f"Unsupported comparison operator: {operator}")

        return handler(left_value, right_value, context)

    def _evaluate_in_comparison(
        self, left_value: EvaluationResult, right_value: EvaluationResult, context: NrmlRuleContext
    ) -> EvaluationResult:
        """Evaluate an 'in' comparison"""
        comparison_result = self._check_in_collection(left_value.Value, right_value.Value)
        return create_result(
            success=True,
            value=comparison_result,
            source=self.__class__.__name__,
            dependencies=[left_value, right_value],
            action=f"Compare: {left_value.Value} IN {right_value.Value} : {comparison_result}",
        )

    def _evaluate_less_than_or_equal(
        self, left_value: EvaluationResult, right_value: EvaluationResult, context: NrmlRuleContext
    ) -> EvaluationResult:
        """Evaluate a 'lessThanOrEqual' comparison"""
        comparison_result = left_value.Value <= right_value.Value
        return create_result(
            success=True,
            value=comparison_result,
            source=self.__class__.__name__,
            dependencies=[left_value, right_value],
            action=f"Compare: {left_value.Value} <= {right_value.Value} : {comparison_result}",
        )

    def _check_in_collection(self, value: Any, collection: Any) -> bool:
        """Check if a value is in a collection"""
        if isinstance(collection, list | set | tuple):
            try:
                return value in collection
            except TypeError:
                # Handle unhashable types by converting to string comparison
                str_value = str(value)
                return any(str_value == str(item) for item in collection)
        else:
            raise ValueError(f"Expected collection (list, set, or tuple), got {type(collection)}")
