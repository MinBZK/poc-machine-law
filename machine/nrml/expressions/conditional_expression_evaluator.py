from typing import Any

from ..context import NrmlRuleContext
from .argument_resolver import ArgumentResolver
from ..conditions.condition_evaluator import ConditionEvaluator


class ConditionalExpressionEvaluator:
    """Evaluator for conditional expressions (type: 'conditional')"""

    def __init__(self):
        """Initialize evaluator with internal state"""
        self.condition_evaluator = ConditionEvaluator()
        self.argument_resolver = ArgumentResolver()

    def evaluate(self, expression: dict[str, Any], context: NrmlRuleContext) -> Any:
        """Evaluate a conditional expression"""
        condition = expression.get("condition")
        if not condition:
            raise ValueError("Conditional expression missing condition")

        # Evaluate the condition using condition evaluator
        condition_result = self.condition_evaluator.evaluate(condition, context)

        # Handle then/else logic
        if condition_result:
            then_clause = expression.get("then")
            if then_clause:
                return self.argument_resolver.resolve_argument(then_clause, context)
            else:
                return True  # Default to True if no then clause
        else:
            else_clause = expression.get("else")
            if else_clause:
                return self.argument_resolver.resolve_argument(else_clause, context)
            else:
                return False  # Default to False if no else clause
