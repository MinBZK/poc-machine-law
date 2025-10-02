from typing import Any

from ..context import NrmlRuleContext
from ..evaluation_result import EvaluationResult, create_result
from ..expressions.argument_resolver import ArgumentResolver


class ComparisonEvaluator:
    """Evaluator for comparison conditions"""

    def __init__(self):
        """Initialize evaluator with internal state"""
        self.argument_resolver = ArgumentResolver()

    def evaluate(self, expression: dict[str, Any], context: NrmlRuleContext) -> EvaluationResult:
        """Evaluate a comparison expression"""
        operator = expression.get("operator")
        arguments = expression.get("arguments", [])

        if operator == "in":
            return self._evaluate_in_comparison(arguments, context)
        else:
            raise ValueError(f"Unsupported comparison operator: {operator}")

    def _evaluate_in_comparison(self, arguments: list[Any], context: NrmlRuleContext) -> EvaluationResult:
        """Evaluate an 'in' comparison"""
        if len(arguments) != 2:
            return create_result(success=False, error=f"'in' operator expects 2 arguments, got {len(arguments)}", source=self.__class__.__name__)

        left_arg = arguments[0]
        right_arg = arguments[1]

        # Resolve the left argument (the value to check)
        left_value = self.argument_resolver.resolve_argument(left_arg, context)

        # Resolve the right argument (the collection to check in)
        right_value = self.argument_resolver.resolve_argument(right_arg, context)

        if left_value.Success and right_value.Success:
            comparison_result = self._check_in_collection(left_value.Value, right_value.Value)
            return create_result(success=True, value=comparison_result, source=self.__class__.__name__, sub_results=[left_value, right_value], action=f"Compare: {left_value.Value} IN {right_value.Value} : {comparison_result}")

        return create_result(success=False, error="Unable to resolve all arguments", source=self.__class__.__name__, sub_results=[left_value, right_value])

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
