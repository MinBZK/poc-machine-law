from typing import Any

from ..context import RuleContext, logger
from .item_type_analyzer import NrmlItemType


class NrmlItemEvaluator:
    """Evaluator for different NRML item types"""

    def __init__(self, rules_engine):
        """Initialize with reference to the rules engine for context"""
        self.rules_engine = rules_engine

    def evaluate_item(self, item: dict[str, Any], item_type: NrmlItemType, context: RuleContext) -> Any:
        """
        Evaluate an NRML item based on its type

        Args:
            item: The NRML item dictionary
            item_type: The determined item type
            context: The rule evaluation context

        Returns:
            The evaluation result
        """
        # Handle different item types
        if item_type == NrmlItemType.TYPE_DEFINITION:
            return self._evaluate_type_definition(item, context)
        elif item_type == NrmlItemType.CALCULATED_VALUE:
            return self._evaluate_calculated_value(item, context)
        elif item_type == NrmlItemType.CONDITIONAL_VALUE:
            return self._evaluate_conditional_value(item, context)
        elif item_type == NrmlItemType.VALUE_INITIALIZATION:
            return self._evaluate_value_initialization(item, context)
        elif item_type == NrmlItemType.CONDITIONAL_CHARACTERISTIC:
            return self._evaluate_conditional_characteristic(item, context)
        elif item_type == NrmlItemType.CONDITIONAL_CALCULATED_VALUE:
            return self._evaluate_conditional_calculated_value(item, context)
        elif item_type == NrmlItemType.RELATION_DEFINITION:
            return self._evaluate_relation_definition(item, context)
        else:
            logger.warning(f"Unsupported item type: {item_type.value}")
            return None

    def _evaluate_type_definition(self, item: dict[str, Any], context: RuleContext) -> Any:
        """Evaluate a type definition item"""
        raise NotImplementedError("Type definition evaluation not yet implemented")

    def _evaluate_calculated_value(self, item: dict[str, Any], context: RuleContext) -> Any:
        """Evaluate a calculated value item with target and expression"""
        logger.debug("Evaluating calculated value")
        version = item.get("versions", [{}])[0]

        # Get the expression and evaluate it
        expression = version.get("expression")
        if expression:
            return self.rules_engine._evaluate_operation(expression, context)

        logger.warning("Calculated value item missing expression")
        return None

    def _evaluate_conditional_value(self, item: dict[str, Any], context: RuleContext) -> Any:
        """Evaluate a conditional value item with target, value, and condition"""
        logger.debug("Evaluating conditional value")
        version = item.get("versions", [{}])[0]

        # Evaluate condition first
        condition = version.get("condition")
        if condition:
            condition_result = self.rules_engine._evaluate_operation(condition, context)
            if condition_result:
                # Return the specified value if condition is true
                value = version.get("value")
                return self.rules_engine._evaluate_value(value, context)

        logger.debug("Conditional value condition not met")
        return None

    def _evaluate_value_initialization(self, item: dict[str, Any], context: RuleContext) -> Any:
        """Evaluate a value initialization item with target and value"""
        logger.debug("Evaluating value initialization")
        version = item.get("versions", [{}])[0]

        # Simply return the initialized value
        value = version.get("value")
        if value:
            return self.rules_engine._evaluate_value(value, context)

        logger.warning("Value initialization item missing value")
        return None

    def _evaluate_conditional_characteristic(self, item: dict[str, Any], context: RuleContext) -> Any:
        """Evaluate a conditional characteristic item with target and condition"""
        logger.debug("Evaluating conditional characteristic")
        version = item.get("versions", [{}])[0]

        # Evaluate the condition and return boolean result
        condition = version.get("condition")
        if condition:
            return self.rules_engine._evaluate_operation(condition, context)

        logger.warning("Conditional characteristic item missing condition")
        return None

    def _evaluate_conditional_calculated_value(self, item: dict[str, Any], context: RuleContext) -> Any:
        """Evaluate a conditional calculated value item with target, expression, and condition"""
        logger.debug("Evaluating conditional calculated value")
        version = item.get("versions", [{}])[0]

        # Evaluate condition first
        condition = version.get("condition")
        if condition:
            condition_result = self.rules_engine._evaluate_operation(condition, context)
            if condition_result:
                # Evaluate expression if condition is true
                expression = version.get("expression")
                if expression:
                    return self.rules_engine._evaluate_operation(expression, context)

        logger.debug("Conditional calculated value condition not met")
        return None

    def _evaluate_relation_definition(self, item: dict[str, Any], context: RuleContext) -> Any:
        """Evaluate a relation definition item with a and b roles"""
        logger.debug("Evaluating relation definition")
        version = item.get("versions", [{}])[0]

        # Relation definitions typically define structure, not computed values
        return {
            "a": version.get("a"),
            "b": version.get("b"),
            "relation_type": "definition"
        }