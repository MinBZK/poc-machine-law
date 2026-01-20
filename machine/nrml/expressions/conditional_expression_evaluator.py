from typing import Any

from ..conditions.condition_evaluator import ConditionEvaluator
from ..context import NrmlRuleContext
from ..evaluation_result import EvaluationResult, create_result, nested_result
from .argument_resolver import ArgumentResolver


class ConditionalExpressionEvaluator:
    """Evaluator for conditional expressions (type: 'conditional')"""

    def __init__(self):
        """Initialize evaluator with internal state"""
        self.condition_evaluator = ConditionEvaluator()
        self.argument_resolver = ArgumentResolver()

    def evaluate(self, expression: dict[str, Any], context: NrmlRuleContext) -> EvaluationResult:
        """Evaluate a conditional expression"""
        condition = expression.get("condition")
        if not condition:
            raise ValueError("Conditional expression missing condition")

        # Evaluate the condition using condition evaluator
        condition_result = self.condition_evaluator.evaluate(condition, context)

        if not condition_result.Success:
            return create_result(
                success=False,
                error="Failed to evaluate condition",
                source=self.__class__.__name__,
                dependencies=[condition_result],
            )

        expression_result = self.resolve_expression_result(condition_result, context, expression)

        return create_result(
            success=expression_result.Success,
            action="Processing conditional expression",
            value=expression_result.Value,
            source=self.__class__.__name__,
            dependencies=[condition_result, expression_result],
            node=expression,
        )

    def resolve_expression_result(
        self, condition_result: EvaluationResult, context: NrmlRuleContext, expression: dict[str, Any]
    ) -> EvaluationResult:
        clause_key = "then" if condition_result.Value else "else"
        clause = expression.get(clause_key)

        if clause:
            resolved_argument = self.argument_resolver.resolve_argument(clause, context)
            return nested_result(
                source=self.__class__.__name__,
                child_result=resolved_argument,
                node=expression,
                action=f"Resolving {clause_key} clause argument",
                error=f"Failed to resolve {clause_key} clause argument",
            )

        else:
            return create_result(
                success=True,
                value=condition_result.Value,
                source=self.__class__.__name__,
                action=f"No {clause_key} clause found, returning condition result",
            )
