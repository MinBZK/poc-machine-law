from unittest.mock import Mock

import pytest

from machine.nrml.context import NrmlRuleContext
from machine.nrml.evaluation_result import create_result
from machine.nrml.expressions.argument_resolver import ArgumentResolver


class TestArgumentResolver:
    """Test cases for ArgumentResolver"""

    @pytest.fixture
    def resolver(self):
        """Create an argument resolver instance"""
        return ArgumentResolver()

    @pytest.fixture
    def context(self):
        """Create a mock NRML rule context with item evaluator"""
        context = NrmlRuleContext()
        context.item_evaluator = Mock()
        return context

    def test_resolve_argument_with_ref(self, resolver, context):
        """Test resolving an argument with $ref"""
        # Setup
        ref_value = "item1"
        argument = {"$ref": ref_value}
        expected_value = 42
        mock_result = create_result(success=True, value=expected_value, source="ItemEvaluator")
        context.item_evaluator.evaluate_item = Mock(return_value=mock_result)

        # Execute
        result = resolver.resolve_argument(argument, context)

        # Verify
        assert result.Success is True
        assert result.Value == expected_value
        assert result.Source == "ArgumentResolver"
        assert result.Action == f"Resolving argument $ref {ref_value}"
        assert len(result.Dependencies) == 1
        assert result.Dependencies[0] == mock_result
        context.item_evaluator.evaluate_item.assert_called_once_with(ref_value, context)

    def test_resolve_argument_with_ref_failure(self, resolver, context):
        """Test resolving an argument with $ref that fails"""
        # Setup
        ref_value = "invalid_item"
        argument = {"$ref": ref_value}
        mock_result = create_result(success=False, error="Item not found", source="ItemEvaluator")
        context.item_evaluator.evaluate_item = Mock(return_value=mock_result)

        # Execute
        result = resolver.resolve_argument(argument, context)

        # Verify
        assert result.Success is False
        assert result.Value is None
        assert result.Source == "ArgumentResolver"
        assert len(result.Dependencies) == 1
        assert result.Dependencies[0] == mock_result
        context.item_evaluator.evaluate_item.assert_called_once_with(ref_value, context)

    def test_resolve_argument_with_value(self, resolver, context):
        """Test resolving an argument with direct value"""
        # Setup
        value = 100
        argument = {"value": value}

        # Execute
        result = resolver.resolve_argument(argument, context)

        # Verify
        assert result.Success is True
        assert result.Value == value
        assert result.Source == "ArgumentResolver"
        assert result.Node == argument
        assert result.Action == "Resolved from argument value"
        assert len(result.Dependencies) == 0

    def test_resolve_argument_with_string_value(self, resolver, context):
        """Test resolving an argument with string value"""
        # Setup
        value = "test_string"
        argument = {"value": value}

        # Execute
        result = resolver.resolve_argument(argument, context)

        # Verify
        assert result.Success is True
        assert result.Value == value

    def test_resolve_argument_with_boolean_value(self, resolver, context):
        """Test resolving an argument with boolean value"""
        # Setup
        argument = {"value": True}

        # Execute
        result = resolver.resolve_argument(argument, context)

        # Verify
        assert result.Success is True
        assert result.Value is True

    def test_resolve_argument_with_null_value(self, resolver, context):
        """Test resolving an argument with null/None value"""
        # Setup
        argument = {"value": None}

        # Execute
        result = resolver.resolve_argument(argument, context)

        # Verify
        assert result.Success is True
        assert result.Value is None

    def test_resolve_argument_with_complex_value(self, resolver, context):
        """Test resolving an argument with complex data structure"""
        # Setup
        value = {"nested": {"key": "value"}, "list": [1, 2, 3]}
        argument = {"value": value}

        # Execute
        result = resolver.resolve_argument(argument, context)

        # Verify
        assert result.Success is True
        assert result.Value == value

    def test_resolve_argument_without_ref_or_value(self, resolver, context):
        """Test resolving an argument without $ref or value raises ValueError"""
        # Setup
        argument = {"other_key": "other_value"}

        # Execute & Verify
        with pytest.raises(ValueError, match="Failed to resolve argument reference"):
            resolver.resolve_argument(argument, context)

    def test_resolve_argument_empty_dict(self, resolver, context):
        """Test resolving an empty argument dict raises ValueError"""
        # Setup
        argument = {}

        # Execute & Verify
        with pytest.raises(ValueError, match="Failed to resolve argument reference"):
            resolver.resolve_argument(argument, context)

    def test_resolve_argument_with_both_ref_and_value(self, resolver, context):
        """Test resolving an argument with both $ref and value prioritizes $ref"""
        # Setup
        ref_value = "item1"
        argument = {"$ref": ref_value, "value": 999}
        expected_value = 42
        mock_result = create_result(success=True, value=expected_value, source="ItemEvaluator")
        context.item_evaluator.evaluate_item = Mock(return_value=mock_result)

        # Execute
        result = resolver.resolve_argument(argument, context)

        # Verify - $ref should be processed, value should be ignored
        assert result.Success is True
        assert result.Value == expected_value  # Value from $ref, not from "value" field
        context.item_evaluator.evaluate_item.assert_called_once_with(ref_value, context)

    def test_resolver_is_stateless(self, resolver):
        """Test that ArgumentResolver is stateless and can be reused"""
        # Create a fresh context for each call
        context1 = NrmlRuleContext()
        context1.item_evaluator = Mock()
        context1.item_evaluator.evaluate_item = Mock(
            return_value=create_result(success=True, value=10, source="ItemEvaluator")
        )

        context2 = NrmlRuleContext()
        context2.item_evaluator = Mock()
        context2.item_evaluator.evaluate_item = Mock(
            return_value=create_result(success=True, value=20, source="ItemEvaluator")
        )

        # Execute multiple resolutions
        result1 = resolver.resolve_argument({"$ref": "item1"}, context1)
        result2 = resolver.resolve_argument({"value": 30}, context2)
        result3 = resolver.resolve_argument({"$ref": "item2"}, context1)

        # Verify each result is independent
        assert result1.Value == 10
        assert result2.Value == 30
        assert result3.Value == 10  # Same as result1 due to mock setup
