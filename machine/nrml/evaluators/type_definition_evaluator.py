from typing import Any

from ..context import NrmlRuleContext
from ..evaluation_result import FactItemEvaluationResult
from ..item_helper import NrmlItemHelper


class TypeDefinitionEvaluator:
    """Evaluator for type definition items"""

    def __init__(self):
        """Initialize stateless evaluator"""
        pass

    def evaluate(self, item_key: str, item: dict[str, Any], context: NrmlRuleContext) -> FactItemEvaluationResult:
        """Evaluate a type definition item"""
        active_version = NrmlItemHelper.get_active_version(item, context.calculation_date)

        # If active version already has a value, return it
        if "value" in active_version or "values" in active_version:
            value = active_version.get("value", active_version.get("values"))
            return FactItemEvaluationResult(Success=True, Value=value)

        source_item = context.get_target_source_item(item_key)
        if source_item:
            source_result = context.item_evaluator.evaluate_item(source_item, context)
            if source_result.Success:
                active_version = NrmlItemHelper.get_active_version(item, context.calculation_date)
                active_version["value"] = source_result.Value
                item["processed"] = True
                return FactItemEvaluationResult(Success=True, Value=source_result.Value)
            else:
                raise Exception(f"Processing dependencies failed: {source_result.Value}")

        # TODO: find way to match this on public names / ids, we dont want to use the fact/item keys outside of the document
        value = context.parameters[item_key]
        if value:
            # TODO: The item has a type (ex Text, boolean) check if this value is of the type?
            active_version = NrmlItemHelper.get_active_version(item, context.calculation_date)
            active_version["value"] = value
            item["processed"] = True
            return FactItemEvaluationResult(Success=True, Value=value)
        else:
            raise Exception(f"Processing item definition failed: no input value found for: {item_key}")
