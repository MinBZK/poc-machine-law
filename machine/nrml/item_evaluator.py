from dataclasses import dataclass
from typing import Any

from ..context import PathNode, RuleContext, logger
from .context import NrmlRuleContext
from .expressions.expression_evaluator import ExpressionEvaluator
from .item_helper import NrmlItemHelper
from .item_type_analyzer import NrmlItemType, determine_item_type


@dataclass
class FactItemEvaluationResult:
    """Result of evaluating an NRML item"""

    Success: bool
    Value: Any


class NrmlItemEvaluator:
    """Evaluator for different NRML item types"""

    def __init__(self, rules_engine):
        """Initialize with reference to the rules engine for context"""
        self.rules_engine = rules_engine
        self.expression_evaluator = ExpressionEvaluator(rules_engine, self)


    def evaluate_item(self, item_key: str, context: NrmlRuleContext) -> FactItemEvaluationResult:
        """
        Evaluate an NRML item based on its type

        Args:
            item_key: The NRML item dictionary key
            context: The rule evaluation context

        Returns:
            The evaluation result
        """

        # Determine the item type
        item = context.items[item_key]
        item_type = determine_item_type(item)

        # TODO: we could just process the items in topologically sorted order, but then we dont know the indentation
        #  or the optionality of any relations (ex in case of x OR y)

        with logger.indent_block("Evaluating item"):
            item_node = PathNode(
                type="item",
                name=f"Evaluate item: {item_type.value}",
                result=None
            )
            context.add_to_path(item_node)

            try:
                # Handle different item types
                if item_type == NrmlItemType.TYPE_DEFINITION:
                    result = self._evaluate_type_definition(item_key, item, context)
                elif item_type == NrmlItemType.CALCULATED_VALUE:
                    result = self._evaluate_calculated_value(item, context)
                elif item_type == NrmlItemType.CONDITIONAL_VALUE:
                    result = self._evaluate_conditional_value(item, context)
                elif item_type == NrmlItemType.VALUE_INITIALIZATION:
                    result = self._evaluate_value_initialization(item, context)
                elif item_type == NrmlItemType.CONDITIONAL_CHARACTERISTIC:
                    result = self._evaluate_conditional_characteristic(item, context)
                elif item_type == NrmlItemType.CONDITIONAL_CALCULATED_VALUE:
                    result = self._evaluate_conditional_calculated_value(item, context)
                elif item_type == NrmlItemType.RELATION_DEFINITION:
                    result = self._evaluate_relation_definition(item, context)
                else:
                    logger.warning(f"Unsupported item type: {item_type.value}")
                    result = FactItemEvaluationResult(Success=False, Value=f"Unsupported item type: {item_type.value}")

                item_node.result = result
                return result
            finally:
                context.pop_path()

    def _evaluate_type_definition(self, item_key: str,  item: dict[str, Any], context: NrmlRuleContext) -> FactItemEvaluationResult:
        """Evaluate a type definition item"""
        active_version = NrmlItemHelper.get_active_version(item, context.calculation_date)

        # If active version already has a value, return it
        if "value" in active_version or "values" in active_version:
            value = active_version.get("value", active_version.get("values"))
            return FactItemEvaluationResult(Success=True, Value=value)

        source_item = context.get_target_source_item(item_key)
        if source_item:
            source_result = self.evaluate_item(source_item, context)
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

    def _evaluate_calculated_value(self, item: dict[str, Any], context: NrmlRuleContext) -> FactItemEvaluationResult:
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

    def _evaluate_conditional_value(self, item: dict[str, Any], context: RuleContext) -> FactItemEvaluationResult:
        """Evaluate a conditional value item with target, value, and condition"""
        return FactItemEvaluationResult(Success=False, Value="Conditional value evaluation not yet implemented")

    def _evaluate_value_initialization(self, item: dict[str, Any], context: RuleContext) -> FactItemEvaluationResult:
        """Evaluate a value initialization item with target and value"""
        return FactItemEvaluationResult(Success=False, Value="Value initialization evaluation not yet implemented")

    def _evaluate_conditional_characteristic(self, item: dict[str, Any], context: RuleContext) -> FactItemEvaluationResult:
        """Evaluate a conditional characteristic item with target and condition"""
        return FactItemEvaluationResult(Success=False, Value="Conditional characteristic evaluation not yet implemented")

    def _evaluate_conditional_calculated_value(self, item: dict[str, Any], context: RuleContext) -> FactItemEvaluationResult:
        """Evaluate a conditional calculated value item with target, expression, and condition"""
        return FactItemEvaluationResult(Success=False, Value="Conditional calculated value evaluation not yet implemented")

    def _evaluate_relation_definition(self, item: dict[str, Any], context: RuleContext) -> FactItemEvaluationResult:
        """Evaluate a relation definition item with a and b roles"""
        return FactItemEvaluationResult(Success=False, Value="Relation definition evaluation not yet implemented")

