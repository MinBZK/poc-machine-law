from typing import Any
from ..context import NrmlRuleContext
from ..evaluation_result import EvaluationResult, success_result, failure_result
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
            return success_result(value=value, source=self.__class__.__name__, node=item, action="Resolved from ITEM DEFINITION")

        source_item = context.get_target_source_item(item_key)
        if source_item:
            source_result = context.item_evaluator.evaluate_item(source_item, context)
            if source_result.Success:
                return success_result(
                    value=source_result.Value,
                    source=self.__class__.__name__,
                    node=item,
                    action="Assigned as target of expression",
                    sub_results=[source_result])
            else:
                # TODO: return a failure result
                raise Exception(f"Processing dependencies failed: {source_result.Value}")

        # TODO: find way to match this on public names / ids, we dont want to use the fact/item keys outside of the document
        value = context.parameters[item_key]
        if value:
            # TODO: The item has a type (ex Text, boolean) check if this value is of the type?
            return success_result(value=value, source=self.__class__.__name__, node=item, action=f"Resolved from PARAMETER {item_key}")
        else:
            return failure_result(
                error_message=f"Processing item definition failed: no input value found for: {item_key}",
                source=self.__class__.__name__,
                node=item)
