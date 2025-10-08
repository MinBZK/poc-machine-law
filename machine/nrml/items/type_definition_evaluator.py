from collections.abc import Callable
from typing import Any

from ..context import NrmlRuleContext
from ..evaluation_result import EvaluationResult, create_result, nested_result
from ..item_helper import NrmlItemHelper
from ..item_type_analyzer import NrmlItemType


class TypeDefinitionEvaluator:
    """Evaluator for type definition items"""

    ITEM_TYPE = NrmlItemType.TYPE_DEFINITION

    def __init__(self):
        """Initialize evaluator with resolvers"""
        self.resolvers: list[Callable[[str, dict[str, Any], NrmlRuleContext], EvaluationResult | None]] = [
            self._try_resolve_from_definition,
            self._try_resolve_from_target_source,
            self._try_resolve_from_input_source,
        ]

    def _try_resolve_from_definition(
        self, item_key: str, item: dict[str, Any], context: NrmlRuleContext
    ) -> EvaluationResult | None:
        """Try to resolve value from item definition"""
        active_version = NrmlItemHelper.get_active_version(item, context.calculation_date)
        if "value" in active_version or "values" in active_version:
            value = active_version.get("value", active_version.get("values"))
            return create_result(
                success=True,
                value=value,
                source=self.__class__.__name__,
                node=item,
                action=f"Item {item_key} resolved from ITEM DEFINITION",
            )
        return None

    def _try_resolve_from_target_source(
        self, item_key: str, item: dict[str, Any], context: NrmlRuleContext
    ) -> EvaluationResult | None:
        """Try to resolve value from target source item"""
        source_item = context.get_target_source_item(item_key)
        if source_item:
            source_result = context.item_evaluator.evaluate_item(source_item, context)
            return nested_result(
                source=self.__class__.__name__,
                child_result=source_result,
                node=item,
                action=f"Item {item_key} is target of {source_item}",
            )
        return None

    def _try_resolve_from_input_source(
        self, item_key: str, item: dict[str, Any], context: NrmlRuleContext
    ) -> EvaluationResult | None:
        """Try to resolve value from input source (parameter or value provider)"""
        input_source = context.get_input_source(item_key)
        if input_source:
            value = context.get_parameter_value(input_source)
            if value:
                # TODO: The item has a type (ex Text, boolean) check if this value is of the type?
                return create_result(
                    success=True,
                    value=value,
                    source=self.__class__.__name__,
                    node=item,
                    action=f"Item {item_key} resolved from PARAMETER",
                )

            # Try to get value from value providers
            value_provider = context.get_value_provider_for(input_source)
            if value_provider:
                result = value_provider.get_value(input_source, context)
                return nested_result(
                    source=self.__class__.__name__,
                    child_result=result,
                    node=item,
                    action=f"Item {item_key} resolved from VALUE PROVIDER",
                )
        return None

    def evaluate(self, item_key: str, item: dict[str, Any], context: NrmlRuleContext) -> EvaluationResult:
        """Evaluate a type definition item"""
        for resolver in self.resolvers:
            result = resolver(item_key, item, context)
            if result:
                return result

        return create_result(
            success=False,
            error=f"Processing item definition failed: no input value found for: {item_key}",
            source=self.__class__.__name__,
            node=item,
        )
