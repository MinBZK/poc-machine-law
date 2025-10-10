from typing import Any

from ..context import NrmlRuleContext
from ..evaluation_result import EvaluationResult
from .aggregation_expression_evaluator import AggregationExpressionEvaluator
from .arithmetic_expression_evaluator import ArithmeticExpressionEvaluator
from .conditional_expression_evaluator import ConditionalExpressionEvaluator


class ExpressionEvaluator:
    """Evaluator for NRML expressions"""

    def __init__(self):
        self.handlers = {
            "conditional": ConditionalExpressionEvaluator(),
            "aggregation": AggregationExpressionEvaluator(),
            "arithmetic": ArithmeticExpressionEvaluator(),
        }

    def evaluate(self, expression: dict[str, Any], context: NrmlRuleContext) -> EvaluationResult:
        """
        Evaluate an NRML expression.

        Args:
            expression: The expression dictionary to evaluate
            context: The NRML rule evaluation context

        Returns:
            The evaluated result
        """
        expr_type = expression.get("type")

        # Look up handler by expression type
        handler = self.handlers.get(expr_type)
        if handler is None:
            raise NotImplementedError(f"Expression type '{expr_type}' not yet implemented")

        return handler.evaluate(expression, context)
