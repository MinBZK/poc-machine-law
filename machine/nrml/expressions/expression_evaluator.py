from typing import Any

from ..context import NrmlRuleContext


class ExpressionEvaluator:
    """Evaluator for NRML expressions"""

    def __init__(self, rules_engine, item_evaluator=None):
        """Initialize with reference to the rules engine and item evaluator"""
        self.rules_engine = rules_engine
        self.item_evaluator = item_evaluator

    def evaluate(self, expression: dict[str, Any], context: NrmlRuleContext) -> Any:
        """
        Evaluate an NRML expression.

        Args:
            expression: The expression dictionary to evaluate
            context: The NRML rule evaluation context

        Returns:
            The evaluated result
        """
        if not isinstance(expression, dict):
            return expression

        expr_type = expression.get("type")

        if expr_type == "conditional":
            return self._evaluate_conditional(expression, context)
        elif expr_type == "comparison":
            return self._evaluate_comparison(expression, context)
        else:
            raise ValueError(f"Unsupported expression type: {expr_type}")

    def _evaluate_conditional(self, expression: dict[str, Any], context: NrmlRuleContext) -> Any:
        """Evaluate a conditional expression"""
        condition = expression.get("condition")
        if not condition:
            raise ValueError("Conditional expression missing condition")

        # Evaluate the condition
        condition_result = self.evaluate(condition, context)

        # Handle then/else logic
        if condition_result:
            then_clause = expression.get("then")
            if then_clause:
                return self._resolve_argument(then_clause, context)
            else:
                return True  # Default to True if no then clause
        else:
            else_clause = expression.get("else")
            if else_clause:
                return self._resolve_argument(else_clause, context)
            else:
                return False  # Default to False if no else clause

    def _evaluate_comparison(self, expression: dict[str, Any], context: NrmlRuleContext) -> Any:
        """Evaluate a comparison expression"""
        operator = expression.get("operator")
        arguments = expression.get("arguments", [])

        if operator == "in":
            return self._evaluate_in_comparison(arguments, context)
        else:
            raise ValueError(f"Unsupported comparison operator: {operator}")

    def _evaluate_in_comparison(self, arguments: list[Any], context: NrmlRuleContext) -> bool:
        """Evaluate an 'in' comparison"""
        if len(arguments) != 2:
            raise ValueError(f"'in' operator expects 2 arguments, got {len(arguments)}")

        left_arg = arguments[0]
        right_arg = arguments[1]

        # Resolve the left argument (the value to check)
        left_value = self._resolve_argument(left_arg, context)

        # Resolve the right argument (the collection to check in)
        right_value = self._resolve_argument(right_arg, context)

        # Handle case where left_value is a list - check if any element is in right_value
        if isinstance(left_value, list):
            if len(left_value) == 1:
                left_value = left_value[0]  # Unwrap single-element list
            else:
                # For multi-element lists, check if any element is in right_value
                return any(self._check_in_collection(item, right_value) for item in left_value)

        return self._check_in_collection(left_value, right_value)

    def _check_in_collection(self, value: Any, collection: Any) -> bool:
        """Check if a value is in a collection"""
        try:
            if isinstance(collection, list | set | tuple):
                return value in collection
            elif isinstance(collection, dict):
                return value in collection.values() or value in collection
            else:
                # Try to convert to string and check
                return str(value) in str(collection)
        except TypeError:
            # Handle unhashable types by converting to string comparison
            str_value = str(value)
            if isinstance(collection, list | set | tuple):
                return any(str_value == str(item) for item in collection)
            elif isinstance(collection, dict):
                return any(str_value == str(item) for item in collection.values()) or \
                       any(str_value == str(item) for item in collection)
            else:
                return str_value in str(collection)

    def _resolve_argument(self, argument: Any, context: NrmlRuleContext) -> Any:
        """Resolve an argument which may contain references"""
        if isinstance(argument, list):
            # Handle list of arguments
            return [self._resolve_argument(item, context) for item in argument]
        elif isinstance(argument, dict):
            if "$ref" in argument:
                # Use full reference and evaluate
                ref = argument["$ref"]
                result = self.item_evaluator.evaluate_item(ref, context)
                if result.Success:
                    return result.Value
                else:
                    raise ValueError(f"Failed to evaluate reference {ref}: {result.Value}")
            elif "value" in argument:
                # Handle value objects directly
                return argument["value"]
            else:
                # Handle other dict structures
                return {k: self._resolve_argument(v, context) for k, v in argument.items()}
        else:
            # Return primitive values as-is
            return argument
