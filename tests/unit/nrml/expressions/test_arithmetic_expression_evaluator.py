from unittest.mock import Mock

import pytest

from machine.nrml.context import NrmlRuleContext
from machine.nrml.evaluation_result import create_result
from machine.nrml.expressions.arithmetic_expression_evaluator import ArithmeticExpressionEvaluator


class TestArithmeticExpressionEvaluator:
    """Test cases for ArithmeticExpressionEvaluator"""

    @pytest.fixture
    def evaluator(self):
        """Create an arithmetic expression evaluator instance"""
        return ArithmeticExpressionEvaluator()

    @pytest.fixture
    def context(self):
        """Create a mock NRML rule context"""
        return NrmlRuleContext()

    def test_multiply_two_numbers(self, evaluator, context):
        """Test multiplying two numbers"""
        # Mock argument resolver to return two numbers
        arg1_result = create_result(success=True, value=5, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=10, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result])

        expression = {"operator": "multiply", "arguments": [{"value": 5}, {"value": 10}]}

        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 50
        assert len(result.Dependencies) == 2
        assert "multiply(5, 10) = 50" in result.Action

    def test_multiply_decimal_numbers(self, evaluator, context):
        """Test multiplying decimal numbers"""
        # Mock argument resolver to return decimal numbers
        arg1_result = create_result(success=True, value=250.50, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=2, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result])

        expression = {"operator": "multiply", "arguments": [{"value": 250.50}, {"value": 2}]}

        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 501.00
        assert len(result.Dependencies) == 2

    def test_multiply_multiple_numbers(self, evaluator, context):
        """Test multiplying more than two numbers"""
        # Mock argument resolver to return multiple numbers
        arg1_result = create_result(success=True, value=2, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=3, source="ArgumentResolver")
        arg3_result = create_result(success=True, value=4, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result, arg3_result])

        expression = {"operator": "multiply", "arguments": [{"value": 2}, {"value": 3}, {"value": 4}]}

        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 24
        assert len(result.Dependencies) == 3

    def test_multiply_with_zero(self, evaluator, context):
        """Test multiplying with zero returns zero"""
        # Mock argument resolver to return zero
        arg1_result = create_result(success=True, value=0, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=100, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result])

        expression = {"operator": "multiply", "arguments": [{"value": 0}, {"value": 100}]}

        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 0

    def test_multiply_with_one(self, evaluator, context):
        """Test multiplying with one returns the other value"""
        # Mock argument resolver
        arg1_result = create_result(success=True, value=1, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=42, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result])

        expression = {"operator": "multiply", "arguments": [{"value": 1}, {"value": 42}]}

        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 42

    def test_multiply_single_argument(self, evaluator, context):
        """Test multiplying with single argument returns that value"""
        # Mock argument resolver
        arg_result = create_result(success=True, value=7, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(return_value=arg_result)

        expression = {"operator": "multiply", "arguments": [{"value": 7}]}

        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 7

    def test_multiply_negative_numbers(self, evaluator, context):
        """Test multiplying negative numbers"""
        # Mock argument resolver
        arg1_result = create_result(success=True, value=-5, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=10, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result])

        expression = {"operator": "multiply", "arguments": [{"value": -5}, {"value": 10}]}

        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == -50

    def test_missing_arguments(self, evaluator, context):
        """Test error when no arguments provided"""
        expression = {"operator": "multiply", "arguments": []}

        result = evaluator.evaluate(expression, context)

        assert result.Success is False
        assert "requires at least 1 argument" in result.Error

    def test_argument_resolution_failure(self, evaluator, context):
        """Test error when argument resolution fails"""
        # Mock argument resolver to fail
        arg1_result = create_result(success=True, value=5, source="ArgumentResolver")
        arg2_result = create_result(success=False, error="Failed to resolve", source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result])

        expression = {"operator": "multiply", "arguments": [{"$ref": "#/facts/item1"}, {"$ref": "#/facts/item2"}]}

        result = evaluator.evaluate(expression, context)

        assert result.Success is False
        assert "Unable to resolve all arguments" in result.Error
        assert len(result.Dependencies) == 2

    def test_unsupported_operator(self, evaluator, context):
        """Test error for unsupported operator"""
        expression = {"operator": "modulo", "arguments": [{"value": 10}, {"value": 2}]}

        with pytest.raises(ValueError, match="Unsupported arithmetic operator: modulo"):
            evaluator.evaluate(expression, context)

    def test_multiply_with_references(self, evaluator, context):
        """Test multiplying values from references"""
        # Mock argument resolver to resolve references
        arg1_result = create_result(success=True, value=3, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=7, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result])

        expression = {
            "operator": "multiply",
            "arguments": [{"$ref": "#/facts/constant1"}, {"$ref": "#/facts/constant2"}],
        }

        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 21
        assert len(result.Dependencies) == 2

    def test_evaluator_is_stateless(self, evaluator, context):
        """Test that evaluator doesn't maintain state between calls"""
        # First evaluation
        arg1_result = create_result(success=True, value=2, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=3, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result])

        expression1 = {"operator": "multiply", "arguments": [{"value": 2}, {"value": 3}]}
        result1 = evaluator.evaluate(expression1, context)

        # Second evaluation with different values
        arg3_result = create_result(success=True, value=5, source="ArgumentResolver")
        arg4_result = create_result(success=True, value=7, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg3_result, arg4_result])

        expression2 = {"operator": "multiply", "arguments": [{"value": 5}, {"value": 7}]}
        result2 = evaluator.evaluate(expression2, context)

        # Results should be independent
        assert result1.Value == 6
        assert result2.Value == 35

    # Tests for add operator
    def test_add_two_numbers(self, evaluator, context):
        """Test adding two numbers"""
        arg1_result = create_result(success=True, value=5, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=10, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result])

        expression = {"operator": "add", "arguments": [{"value": 5}, {"value": 10}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 15
        assert "add(5, 10) = 15" in result.Action

    def test_add_multiple_numbers(self, evaluator, context):
        """Test adding more than two numbers"""
        arg1_result = create_result(success=True, value=2, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=3, source="ArgumentResolver")
        arg3_result = create_result(success=True, value=4, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result, arg3_result])

        expression = {"operator": "add", "arguments": [{"value": 2}, {"value": 3}, {"value": 4}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 9

    def test_add_decimal_numbers(self, evaluator, context):
        """Test adding decimal numbers"""
        arg1_result = create_result(success=True, value=10.5, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=20.3, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result])

        expression = {"operator": "add", "arguments": [{"value": 10.5}, {"value": 20.3}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 30.8

    def test_add_negative_numbers(self, evaluator, context):
        """Test adding negative numbers"""
        arg1_result = create_result(success=True, value=-5, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=10, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result])

        expression = {"operator": "add", "arguments": [{"value": -5}, {"value": 10}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 5

    def test_add_single_argument(self, evaluator, context):
        """Test adding with single argument returns that value"""
        arg_result = create_result(success=True, value=7, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(return_value=arg_result)

        expression = {"operator": "add", "arguments": [{"value": 7}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 7

    # Tests for subtract operator
    def test_subtract_two_numbers(self, evaluator, context):
        """Test subtracting two numbers"""
        arg1_result = create_result(success=True, value=10, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=3, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result])

        expression = {"operator": "subtract", "arguments": [{"value": 10}, {"value": 3}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 7
        assert "subtract(10, 3) = 7" in result.Action

    def test_subtract_multiple_numbers(self, evaluator, context):
        """Test subtracting multiple numbers sequentially"""
        arg1_result = create_result(success=True, value=20, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=5, source="ArgumentResolver")
        arg3_result = create_result(success=True, value=3, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result, arg3_result])

        expression = {"operator": "subtract", "arguments": [{"value": 20}, {"value": 5}, {"value": 3}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 12  # 20 - 5 - 3

    def test_subtract_decimal_numbers(self, evaluator, context):
        """Test subtracting decimal numbers"""
        arg1_result = create_result(success=True, value=30.8, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=10.3, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result])

        expression = {"operator": "subtract", "arguments": [{"value": 30.8}, {"value": 10.3}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 20.5

    def test_subtract_negative_numbers(self, evaluator, context):
        """Test subtracting negative numbers"""
        arg1_result = create_result(success=True, value=10, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=-5, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result])

        expression = {"operator": "subtract", "arguments": [{"value": 10}, {"value": -5}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 15  # 10 - (-5) = 15

    def test_subtract_single_argument(self, evaluator, context):
        """Test subtracting with single argument returns that value"""
        arg_result = create_result(success=True, value=7, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(return_value=arg_result)

        expression = {"operator": "subtract", "arguments": [{"value": 7}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 7

    # Tests for divide operator
    def test_divide_two_numbers(self, evaluator, context):
        """Test dividing two numbers"""
        arg1_result = create_result(success=True, value=10, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=2, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result])

        expression = {"operator": "divide", "arguments": [{"value": 10}, {"value": 2}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 5
        assert "divide(10, 2) = 5" in result.Action

    def test_divide_multiple_numbers(self, evaluator, context):
        """Test dividing multiple numbers sequentially"""
        arg1_result = create_result(success=True, value=100, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=5, source="ArgumentResolver")
        arg3_result = create_result(success=True, value=2, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result, arg3_result])

        expression = {"operator": "divide", "arguments": [{"value": 100}, {"value": 5}, {"value": 2}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 10  # 100 / 5 / 2

    def test_divide_decimal_numbers(self, evaluator, context):
        """Test dividing decimal numbers"""
        arg1_result = create_result(success=True, value=10.5, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=2, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result])

        expression = {"operator": "divide", "arguments": [{"value": 10.5}, {"value": 2}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 5.25

    def test_divide_by_zero_raises_error(self, evaluator, context):
        """Test that dividing by zero raises ZeroDivisionError"""
        arg1_result = create_result(success=True, value=10, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=0, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result])

        expression = {"operator": "divide", "arguments": [{"value": 10}, {"value": 0}]}

        with pytest.raises(ZeroDivisionError, match="Division by zero"):
            evaluator.evaluate(expression, context)

    def test_divide_single_argument(self, evaluator, context):
        """Test dividing with single argument returns that value"""
        arg_result = create_result(success=True, value=7, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(return_value=arg_result)

        expression = {"operator": "divide", "arguments": [{"value": 7}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 7

    # Tests for min operator
    def test_min_two_numbers(self, evaluator, context):
        """Test finding minimum of two numbers"""
        arg1_result = create_result(success=True, value=5, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=10, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result])

        expression = {"operator": "min", "arguments": [{"value": 5}, {"value": 10}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 5
        assert "min(5, 10) = 5" in result.Action

    def test_min_multiple_numbers(self, evaluator, context):
        """Test finding minimum of multiple numbers"""
        arg1_result = create_result(success=True, value=8, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=3, source="ArgumentResolver")
        arg3_result = create_result(success=True, value=12, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result, arg3_result])

        expression = {"operator": "min", "arguments": [{"value": 8}, {"value": 3}, {"value": 12}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 3

    def test_min_decimal_numbers(self, evaluator, context):
        """Test finding minimum of decimal numbers"""
        arg1_result = create_result(success=True, value=10.5, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=10.3, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result])

        expression = {"operator": "min", "arguments": [{"value": 10.5}, {"value": 10.3}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 10.3

    def test_min_negative_numbers(self, evaluator, context):
        """Test finding minimum with negative numbers"""
        arg1_result = create_result(success=True, value=-5, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=10, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result])

        expression = {"operator": "min", "arguments": [{"value": -5}, {"value": 10}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == -5

    def test_min_single_argument(self, evaluator, context):
        """Test minimum with single argument returns that value"""
        arg_result = create_result(success=True, value=7, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(return_value=arg_result)

        expression = {"operator": "min", "arguments": [{"value": 7}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 7

    # Tests for max operator
    def test_max_two_numbers(self, evaluator, context):
        """Test finding maximum of two numbers"""
        arg1_result = create_result(success=True, value=5, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=10, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result])

        expression = {"operator": "max", "arguments": [{"value": 5}, {"value": 10}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 10
        assert "max(5, 10) = 10" in result.Action

    def test_max_multiple_numbers(self, evaluator, context):
        """Test finding maximum of multiple numbers"""
        arg1_result = create_result(success=True, value=8, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=15, source="ArgumentResolver")
        arg3_result = create_result(success=True, value=12, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result, arg3_result])

        expression = {"operator": "max", "arguments": [{"value": 8}, {"value": 15}, {"value": 12}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 15

    def test_max_decimal_numbers(self, evaluator, context):
        """Test finding maximum of decimal numbers"""
        arg1_result = create_result(success=True, value=10.5, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=10.3, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result])

        expression = {"operator": "max", "arguments": [{"value": 10.5}, {"value": 10.3}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 10.5

    def test_max_negative_numbers(self, evaluator, context):
        """Test finding maximum with negative numbers"""
        arg1_result = create_result(success=True, value=-5, source="ArgumentResolver")
        arg2_result = create_result(success=True, value=-10, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[arg1_result, arg2_result])

        expression = {"operator": "max", "arguments": [{"value": -5}, {"value": -10}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == -5

    def test_max_single_argument(self, evaluator, context):
        """Test maximum with single argument returns that value"""
        arg_result = create_result(success=True, value=7, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(return_value=arg_result)

        expression = {"operator": "max", "arguments": [{"value": 7}]}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 7
