import math
from collections.abc import Callable
from typing import Any

from ..context import NrmlRuleContext
from ..evaluation_result import EvaluationResult, create_result
from .argument_resolver import ArgumentResolver


class ArithmeticExpressionEvaluator:
    """Evaluator for arithmetic expressions (type: 'arithmetic')"""

    def __init__(self):
        """Initialize evaluator with internal state"""
        self.argument_resolver = ArgumentResolver()
        self.operators: dict[str, Callable[[list[EvaluationResult]], Any]] = {
            "add": self._evaluate_add,
            "subtract": self._evaluate_subtract,
            "multiply": self._evaluate_multiply,
            "divide": self._evaluate_divide,
            "min": self._evaluate_min,
            "max": self._evaluate_max,
        }

    def evaluate(self, expression: dict[str, Any], context: NrmlRuleContext) -> EvaluationResult:
        """Evaluate an arithmetic expression"""
        operator = expression.get("operator")
        arguments = expression.get("arguments", [])

        # Validate we have arguments
        if not arguments:
            return create_result(
                success=False,
                error=f"Arithmetic operator '{operator}' requires at least 1 argument",
                source=self.__class__.__name__,
            )

        # Resolve all arguments
        resolved_args = []
        for arg in arguments:
            resolved = self.argument_resolver.resolve_argument(arg, context)
            resolved_args.append(resolved)

        # Check if all arguments resolved successfully
        if not all(arg.Success for arg in resolved_args):
            return create_result(
                success=False,
                error="Unable to resolve all arguments",
                source=self.__class__.__name__,
                dependencies=resolved_args,
            )

        # Look up operator handler
        handler = self.operators.get(operator)
        if handler is None:
            raise ValueError(f"Unsupported arithmetic operator: {operator}")

        # Apply the operator
        result_value = handler(resolved_args)

        return create_result(
            success=True,
            value=result_value,
            source=self.__class__.__name__,
            dependencies=resolved_args,
            action=f"Arithmetic: {operator}({', '.join(str(arg.Value) for arg in resolved_args)}) = {result_value}",
        )

    def _evaluate_add(self, resolved_args: list[EvaluationResult]) -> Any:
        """Evaluate addition using sum"""
        values = [arg.Value for arg in resolved_args]
        return sum(values)

    def _evaluate_subtract(self, resolved_args: list[EvaluationResult]) -> Any:
        """Evaluate subtraction (sequential: first - second - third...)"""
        values = [arg.Value for arg in resolved_args]
        if len(values) == 1:
            return values[0]
        result = values[0]
        for value in values[1:]:
            result -= value
        return result

    def _evaluate_multiply(self, resolved_args: list[EvaluationResult]) -> Any:
        """Evaluate multiplication using math.prod"""
        values = [arg.Value for arg in resolved_args]
        return math.prod(values)

    def _evaluate_divide(self, resolved_args: list[EvaluationResult]) -> Any:
        """Evaluate division (sequential: first / second / third...)"""
        values = [arg.Value for arg in resolved_args]
        if len(values) == 1:
            return values[0]
        result = values[0]
        for value in values[1:]:
            if value == 0:
                raise ZeroDivisionError("Division by zero")
            result /= value
        return result

    def _evaluate_min(self, resolved_args: list[EvaluationResult]) -> Any:
        """Evaluate minimum value"""
        values = [arg.Value for arg in resolved_args]
        return min(values)

    def _evaluate_max(self, resolved_args: list[EvaluationResult]) -> Any:
        """Evaluate maximum value"""
        values = [arg.Value for arg in resolved_args]
        return max(values)
