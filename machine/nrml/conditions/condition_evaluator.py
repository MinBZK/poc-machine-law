from typing import Any

from ..aggregation_context import AggregationContext
from ..context import NrmlRuleContext
from ..evaluation_result import EvaluationResult
from .comparison_evaluator import ComparisonEvaluator
from .exists_condition_evaluator import ExistsConditionEvaluator


class ConditionEvaluator:
    """Evaluator for NRML conditions"""

    def __init__(self):
        self.handlers = {
            "comparison": ComparisonEvaluator(),
            "exists": ExistsConditionEvaluator(),
        }

    def evaluate(
        self, condition: dict[str, Any], context: NrmlRuleContext, aggregation_context: AggregationContext | None = None
    ) -> EvaluationResult:
        """Evaluate a condition"""
        condition_type = condition.get("type")

        # Look up handler by condition type
        handler = self.handlers.get(condition_type)
        if handler is None:
            raise NotImplementedError(f"Condition type '{condition_type}' not yet implemented")

        return handler.evaluate(condition, context, aggregation_context)
