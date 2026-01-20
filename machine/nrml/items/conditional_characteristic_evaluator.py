from typing import Any

from ..conditions.condition_evaluator import ConditionEvaluator
from ..context import NrmlRuleContext
from ..evaluation_result import EvaluationResult, create_result
from ..item_helper import NrmlItemHelper
from ..item_type_analyzer import NrmlItemType


class ConditionalCharacteristicEvaluator:
    """Evaluator for conditional characteristic items"""

    ITEM_TYPE = NrmlItemType.CONDITIONAL_CHARACTERISTIC

    def __init__(self):
        """Initialize with condition evaluator"""
        self.condition_evaluator = ConditionEvaluator()

    def evaluate(self, item_key: str, item: dict[str, Any], context: NrmlRuleContext) -> EvaluationResult:
        """Evaluate a conditional characteristic item

        When the condition evaluates to True, the characteristic is considered present.
        The characteristic presence is indicated by returning True as the value.
        """
        # Get the active version
        active_version = NrmlItemHelper.get_active_version(item, context.calculation_date)
        if not active_version:
            return create_result(
                success=False,
                error="No active version found in conditional characteristic item",
                source=self.__class__.__name__,
            )

        condition = active_version.get("condition")
        target = active_version.get("target")

        if not condition:
            return create_result(
                success=False,
                error="No condition found in conditional characteristic item",
                source=self.__class__.__name__,
            )

        if not target:
            return create_result(
                success=False,
                error="No target found in conditional characteristic item",
                source=self.__class__.__name__,
            )

        try:
            # Evaluate the condition
            condition_result = self.condition_evaluator.evaluate(condition, context)

            if not condition_result.Success:
                return create_result(
                    success=False,
                    error=f"Condition evaluation failed: {condition_result.Error}",
                    source=self.__class__.__name__,
                    dependencies=[condition_result],
                )

            characteristic_present = bool(condition_result.Value)

            return create_result(
                success=True,
                value=characteristic_present,
                source=self.__class__.__name__,
                dependencies=[condition_result],
                node=item,
                action=f"Conditional characteristic {item_key}: condition evaluated to {characteristic_present}",
            )

        except Exception as e:
            return create_result(
                success=False,
                error=f"Error evaluating conditional characteristic: {str(e)}",
                source=self.__class__.__name__,
            )
