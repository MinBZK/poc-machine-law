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

        if operator == "in":
            return self._evaluate_in_comparison(left_value, right_value, context)
        elif operator == "lessThanOrEqual":
            return self._evaluate_less_than_or_equal(left_value, right_value, context)
        else:
            raise ValueError(f"Unsupported comparison operator: {operator}")

    def _evaluate_in_comparison(
        self, left_value: EvaluationResult, right_value: EvaluationResult, context: NrmlRuleContext
    ) -> EvaluationResult:
        """Evaluate an 'in' comparison"""

        if left_value.Success and right_value.Success:
            comparison_result = self._check_in_collection(left_value.Value, right_value.Value)
            return create_result(
                success=True,
                value=comparison_result,
                source=self.__class__.__name__,
                sub_results=[left_value, right_value],
                action=f"Compare: {left_value.Value} IN {right_value.Value} : {comparison_result}",
            )

        return create_result(
            success=False,
            error="Unable to resolve all arguments",
            source=self.__class__.__name__,
            sub_results=[left_value, right_value],
        )

    def _evaluate_less_than_or_equal(
        self, left_value: EvaluationResult, right_value: EvaluationResult, context: NrmlRuleContext
    ) -> EvaluationResult:
        """Evaluate a 'lessThanOrEqual' comparison"""

        if left_value.Success and right_value.Success:
            comparison_result = left_value.Value <= right_value.Value
            return create_result(
                success=True,
                value=comparison_result,
                source=self.__class__.__name__,
                sub_results=[left_value, right_value],
                action=f"Compare: {left_value.Value} <= {right_value.Value} : {comparison_result}",
            )

        return create_result(
            success=False,
            error="Unable to resolve all arguments",
            source=self.__class__.__name__,
            sub_results=[left_value, right_value],
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
