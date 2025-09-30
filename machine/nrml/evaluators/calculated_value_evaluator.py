from typing import Any

from ..context import NrmlRuleContext
from ..evaluation_result import FactItemEvaluationResult


class CalculatedValueEvaluator:
    """Evaluator for calculated value items"""

    def __init__(self, expression_evaluator):
        """Initialize with reference to the expression evaluator"""
        self.expression_evaluator = expression_evaluator

    def evaluate(self, item_key: str, item: dict[str, Any], context: NrmlRuleContext) -> FactItemEvaluationResult:
        """Evaluate a calculated value item with target and expression"""
        # Get the first version (assuming all versions have the same structure)
        versions = item.get("versions", [])
        if not versions:
            return FactItemEvaluationResult(Success=False, Value="No versions found in calculated value item")

        version = versions[0]
        expression = version.get("expression")
        target = version.get("target")

        if not expression:
            return FactItemEvaluationResult(Success=False, Value="No expression found in calculated value item")

        if not target:
            return FactItemEvaluationResult(Success=False, Value="No target found in calculated value item")

        try:
            # Evaluate the expression using the new expression evaluator
            result = self.expression_evaluator.evaluate(expression, context)
            return FactItemEvaluationResult(Success=True, Value=result)
        except Exception as e:
            return FactItemEvaluationResult(Success=False, Value=f"Error evaluating expression: {str(e)}")