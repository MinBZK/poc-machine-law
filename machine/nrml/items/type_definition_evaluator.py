from typing import Any
from ..context import NrmlRuleContext
from ..evaluation_result import EvaluationResult, create_result, nested_result
from ..item_helper import NrmlItemHelper
from ...context import logger


class TypeDefinitionEvaluator:
    """Evaluator for type definition items"""

    def __init__(self):
        """Initialize stateless evaluator"""
        pass

    def evaluate(self, item_key: str, item: dict[str, Any], context: NrmlRuleContext) -> EvaluationResult:
        """Evaluate a type definition item"""
        active_version = NrmlItemHelper.get_active_version(item, context.calculation_date)

        # If active version has a value, return it
        if "value" in active_version or "values" in active_version:
            value = active_version.get("value", active_version.get("values"))
            return create_result(success=True, value=value, source=self.__class__.__name__, node=item, action="Resolved from ITEM DEFINITION")

        source_item = context.get_target_source_item(item_key)
        if source_item:
            source_result = context.item_evaluator.evaluate_item(source_item, context)
            return nested_result(
                source=self.__class__.__name__,
                child_result=source_result,
                node=item,
                action="Assigned as target of expression")

        # TODO: find way to match this on public names / ids, we dont want to use the fact/item keys outside of the document
        value = context.get_parameter_value(item_key)
        if value:
            # TODO: The item has a type (ex Text, boolean) check if this value is of the type?
            return create_result(success=True, value=value, source=self.__class__.__name__, node=item, action=f"Resolved from PARAMETER {item_key}")
        else:
            return create_result(
                success=False,
                error=f"Processing item definition failed: no input value found for: {item_key}",
                source=self.__class__.__name__,
                node=item)
