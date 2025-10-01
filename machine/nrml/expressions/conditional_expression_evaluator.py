from typing import Any

from ..context import NrmlRuleContext
from .argument_resolver import ArgumentResolver
from ..conditions.condition_evaluator import ConditionEvaluator
from ..evaluation_result import failure_result, success_result, EvaluationResult, evaluation_result


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
            return failure_result(error_message="Failed to evaluate condition", source=self.__class__.__name__, sub_results=[condition_result])

        expression_result = self.resolve_expression_result(condition_result, context, expression)

        return evaluation_result(
            success=expression_result.Success,
            action=f"Processing conditional expression",
            value=expression_result.Value,
            source=self.__class__.__name__,
            sub_results=[condition_result, expression_result],
            node=expression)

    def resolve_expression_result(self, condition_result: EvaluationResult, context: NrmlRuleContext,
                                  expression: dict[str, Any]) -> EvaluationResult:

        clause_key = "then" if condition_result.Value else "else"
        clause = expression.get(clause_key)

        if clause:
            resolved_argument = self.argument_resolver.resolve_argument(clause, context)
            if resolved_argument.Success:
                return success_result(
                    action=f"Resolving {clause_key} clause argument",
                    value=resolved_argument.Value,
                    source=self.__class__.__name__,
                    sub_results=[resolved_argument],
                    node=expression)
            else:
                return failure_result(error_message=f"Failed to resolve {clause_key} clause argument", source=self.__class__.__name__, sub_results=[condition_result, resolved_argument], node=expression)



        else:
            return success_result(value=True, source=self.__class__.__name__,
                                  action="Default then result for condition expression")



