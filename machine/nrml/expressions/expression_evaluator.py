from typing import Any

from ..context import NrmlRuleContext
from .argument_resolver import ArgumentResolver
from .conditions.condition_evaluator import ConditionEvaluator
from .conditional_expression_evaluator import ConditionalExpressionEvaluator


class ExpressionEvaluator:
    """Evaluator for NRML expressions"""

    def __init__(self, item_evaluator=None):
        """Initialize with reference to the rules engine and item evaluator"""
        self.item_evaluator = item_evaluator
        self.argument_resolver = ArgumentResolver(item_evaluator)
        self.condition_evaluator = ConditionEvaluator(self)
        self.conditional_expression_evaluator = ConditionalExpressionEvaluator(self, self.argument_resolver)

    def evaluate(self, expression: dict[str, Any], context: NrmlRuleContext) -> Any:
        """
        Evaluate an NRML expression.

        Args:
            expression: The expression dictionary to evaluate
            context: The NRML rule evaluation context

        Returns:
            The evaluated result
        """
        if not isinstance(expression, dict):
            return expression

        expr_type = expression.get("type")

        # Schema-based expression type mapping
        if expr_type == "conditional":
            return self.conditional_expression_evaluator.evaluate(expression, context)
        elif expr_type in ["arithmetic", "aggregation", "distribution", "function"]:
            raise NotImplementedError(f"Expression type '{expr_type}' not yet implemented")
        else:
            raise ValueError(f"Unsupported expression type: {expr_type}")

