from typing import Any

from ...context import NrmlRuleContext
from .comparison_evaluator import ComparisonEvaluator


class ConditionEvaluator:
    """Evaluator for NRML conditions"""

    def __init__(self, expression_evaluator):
        """Initialize with reference to the main expression evaluator"""
        self.expression_evaluator = expression_evaluator
        self.comparison_evaluator = ComparisonEvaluator(expression_evaluator)

    def evaluate(self, condition: dict[str, Any], context: NrmlRuleContext) -> Any:
        """Evaluate a condition"""
        if not isinstance(condition, dict):
            return condition

        condition_type = condition.get("type")

        if condition_type == "comparison":
            return self.comparison_evaluator.evaluate(condition, context)
        else:
            raise ValueError(f"Unsupported condition type: {condition_type}")