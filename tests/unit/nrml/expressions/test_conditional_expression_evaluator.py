from unittest.mock import Mock

import pytest

from machine.nrml.context import NrmlRuleContext
from machine.nrml.evaluation_result import create_result
from machine.nrml.expressions.conditional_expression_evaluator import ConditionalExpressionEvaluator


class TestConditionalExpressionEvaluator:
    """Test cases for ConditionalExpressionEvaluator"""

    @pytest.fixture
    def evaluator(self):
        """Create a conditional expression evaluator instance"""
        return ConditionalExpressionEvaluator()

    @pytest.fixture
    def context(self):
        """Create a mock NRML rule context"""
        return NrmlRuleContext()

    def test_evaluate_conditional_with_true_condition_and_then_clause(self, evaluator, context):
        """Test conditional expression with true condition and then clause"""
        # Mock condition evaluator to return True
        condition_result = create_result(success=True, value=True, source="ConditionEvaluator")
        evaluator.condition_evaluator.evaluate = Mock(return_value=condition_result)

        # Mock argument resolver for then clause
        then_result = create_result(success=True, value="then_value", source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(return_value=then_result)

        expression = {"condition": {"type": "comparison"}, "then": {"value": "then_value"}}

        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == "then_value"
        assert len(result.Dependencies) == 2
        evaluator.argument_resolver.resolve_argument.assert_called_once()

    def test_evaluate_conditional_with_false_condition_and_else_clause(self, evaluator, context):
        """Test conditional expression with false condition and else clause"""
        # Mock condition evaluator to return False
        condition_result = create_result(success=True, value=False, source="ConditionEvaluator")
        evaluator.condition_evaluator.evaluate = Mock(return_value=condition_result)

        # Mock argument resolver for else clause
        else_result = create_result(success=True, value="else_value", source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(return_value=else_result)

        expression = {"condition": {"type": "comparison"}, "else": {"value": "else_value"}}

        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == "else_value"
        evaluator.argument_resolver.resolve_argument.assert_called_once()

    def test_evaluate_conditional_with_true_condition_no_then_clause(self, evaluator, context):
        """Test conditional expression with true condition but no then clause"""
        condition_result = create_result(success=True, value=True, source="ConditionEvaluator")
        evaluator.condition_evaluator.evaluate = Mock(return_value=condition_result)

        expression = {"condition": {"type": "comparison"}}

        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value is True

    def test_evaluate_conditional_with_false_condition_no_else_clause(self, evaluator, context):
        """Test conditional expression with false condition but no else clause"""
        condition_result = create_result(success=True, value=False, source="ConditionEvaluator")
        evaluator.condition_evaluator.evaluate = Mock(return_value=condition_result)

        expression = {"condition": {"type": "comparison"}}

        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value is False

    def test_evaluate_conditional_with_condition_evaluation_failure(self, evaluator, context):
        """Test conditional expression when condition evaluation fails"""
        condition_result = create_result(success=False, error="Condition failed", source="ConditionEvaluator")
        evaluator.condition_evaluator.evaluate = Mock(return_value=condition_result)

        expression = {"condition": {"type": "comparison"}}

        result = evaluator.evaluate(expression, context)

        assert result.Success is False
        assert "Failed to evaluate condition" in result.Error
        assert len(result.Dependencies) == 1

    def test_evaluate_conditional_with_missing_condition(self, evaluator, context):
        """Test conditional expression without a condition field"""
        expression = {}

        with pytest.raises(ValueError, match="Conditional expression missing condition"):
            evaluator.evaluate(expression, context)

    def test_evaluate_conditional_with_failed_then_clause_resolution(self, evaluator, context):
        """Test conditional expression when then clause resolution fails"""
        condition_result = create_result(success=True, value=True, source="ConditionEvaluator")
        evaluator.condition_evaluator.evaluate = Mock(return_value=condition_result)

        then_result = create_result(success=False, error="Resolution failed", source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(return_value=then_result)

        expression = {"condition": {"type": "comparison"}, "then": {"$ref": "unknown"}}

        result = evaluator.evaluate(expression, context)

        assert result.Success is False
        assert result.Value is None

    def test_resolve_expression_result_then_clause(self, evaluator, context):
        """Test resolve_expression_result with then clause"""
        condition_result = create_result(success=True, value=True, source="ConditionEvaluator")
        then_result = create_result(success=True, value="then_value", source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(return_value=then_result)

        expression = {"then": {"value": "then_value"}}

        result = evaluator.resolve_expression_result(condition_result, context, expression)

        assert result.Success is True
        assert result.Value == "then_value"

    def test_resolve_expression_result_else_clause(self, evaluator, context):
        """Test resolve_expression_result with else clause"""
        condition_result = create_result(success=True, value=False, source="ConditionEvaluator")
        else_result = create_result(success=True, value="else_value", source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(return_value=else_result)

        expression = {"else": {"value": "else_value"}}

        result = evaluator.resolve_expression_result(condition_result, context, expression)

        assert result.Success is True
        assert result.Value == "else_value"
