from typing import Any

from ..context import NrmlRuleContext
from ..evaluation_result import EvaluationResult, create_result
from ..expressions.expression_evaluator import ExpressionEvaluator
from ..item_type_analyzer import NrmlItemType


class CalculatedValueEvaluator:
    """Evaluator for calculated value items"""

    ITEM_TYPE = NrmlItemType.CALCULATED_VALUE

    def __init__(self):
        """Initialize with expression evaluator"""
        self.expression_evaluator = ExpressionEvaluator()

    def evaluate(self, item_key: str, item: dict[str, Any], context: NrmlRuleContext) -> EvaluationResult:
        """Evaluate a calculated value item with target and expression"""
        # Get the first version (assuming all versions have the same structure)
        versions = item.get("versions", [])
        if not versions:
            return create_result(
                success=False, error="No versions found in calculated value item", source=self.__class__.__name__
            )

        version = versions[0]
        expression = version.get("expression")
        target = version.get("target")

        if not expression:
            return create_result(
                success=False, error="No expression found in calculated value item", source=self.__class__.__name__
            )

        if not target:
            return create_result(
                success=False, error="No target found in calculated value item", source=self.__class__.__name__
            )

        try:
            # Evaluate the expression using the expression evaluator
            expression_result = self.expression_evaluator.evaluate(expression, context)
            return create_result(
                success=True,
                value=expression_result.Value,
                source=self.__class__.__name__,
                dependencies=[expression_result],
                node=item,
                action=f"Determining Calculated value for item {item_key}",
            )

        except Exception as e:
            return create_result(
                success=False, error=f"Error evaluating expression: {str(e)}", source=self.__class__.__name__
            )
