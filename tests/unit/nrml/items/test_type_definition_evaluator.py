from unittest.mock import Mock

import pytest

from machine.nrml.context import NrmlRuleContext
from machine.nrml.evaluation_result import create_result
from machine.nrml.items.type_definition_evaluator import TypeDefinitionEvaluator


class TestTypeDefinitionEvaluator:
    """Test cases for TypeDefinitionEvaluator"""

    @pytest.fixture
    def evaluator(self):
        """Create a type definition evaluator instance"""
        return TypeDefinitionEvaluator()

    @pytest.fixture
    def context(self):
        """Create a mock NRML rule context"""
        context = NrmlRuleContext()
        context.calculation_date = "2024-01-01"
        context.item_evaluator = Mock()
        return context

    def test_evaluate_with_value_in_definition(self, evaluator, context):
        """Test evaluation when value is in the item definition"""
        item = {"versions": [{"type": "Text", "value": "predefined_value"}]}

        result = evaluator.evaluate("test_item", item, context)

        assert result.Success is True
        assert result.Value == "predefined_value"
        assert "ITEM DEFINITION" in result.Action

    def test_evaluate_with_values_in_definition(self, evaluator, context):
        """Test evaluation when values (plural) is in the item definition"""
        item = {"versions": [{"type": "Text", "values": ["value1", "value2"]}]}

        result = evaluator.evaluate("test_item", item, context)

        assert result.Success is True
        assert result.Value == ["value1", "value2"]
        assert "ITEM DEFINITION" in result.Action

    def test_evaluate_from_target_source(self, evaluator, context):
        """Test evaluation when value comes from target source item"""
        item = {"versions": [{"type": "Text"}]}

        # Mock target source resolution
        context.get_target_source_item = Mock(return_value="source_item")
        source_result = create_result(success=True, value="source_value", source="ItemEvaluator")
        context.item_evaluator.evaluate_item = Mock(return_value=source_result)

        result = evaluator.evaluate("test_item", item, context)

        assert result.Success is True
        assert result.Value == "source_value"
        assert "target of source_item" in result.Action
        context.item_evaluator.evaluate_item.assert_called_once_with("source_item", context)

    def test_evaluate_from_parameter(self, evaluator, context):
        """Test evaluation when value comes from a parameter"""
        item = {"versions": [{"type": "Text"}]}

        # Mock input source and parameter value
        context.get_target_source_item = Mock(return_value=None)
        context.get_input_source = Mock(return_value="param_name")
        context.get_parameter_value = Mock(return_value="param_value")

        result = evaluator.evaluate("test_item", item, context)

        assert result.Success is True
        assert result.Value == "param_value"
        assert "PARAMETER" in result.Action

    def test_evaluate_from_value_provider(self, evaluator, context):
        """Test evaluation when value comes from a value provider"""
        item = {"versions": [{"type": "Text"}]}

        # Mock value provider
        mock_value_provider = Mock()
        provider_result = create_result(success=True, value="provider_value", source="ValueProvider")
        mock_value_provider.get_value = Mock(return_value=provider_result)

        context.get_target_source_item = Mock(return_value=None)
        context.get_input_source = Mock(return_value="input_name")
        context.get_parameter_value = Mock(return_value=None)
        context.get_value_provider_for = Mock(return_value=mock_value_provider)

        result = evaluator.evaluate("test_item", item, context)

        assert result.Success is True
        assert result.Value == "provider_value"
        assert "VALUE PROVIDER" in result.Action

    def test_evaluate_no_value_found(self, evaluator, context):
        """Test evaluation when no value can be resolved"""
        item = {"versions": [{"type": "Text"}]}

        # Mock all sources returning None/empty
        context.get_target_source_item = Mock(return_value=None)
        context.get_input_source = Mock(return_value=None)

        result = evaluator.evaluate("test_item", item, context)

        assert result.Success is False
        assert "no input value found" in result.Error

    def test_try_resolve_from_definition_with_value(self, evaluator, context):
        """Test _try_resolve_from_definition with value field"""
        item = {"versions": [{"validFrom": "2020-01-01", "value": "test_value"}]}
        result = evaluator._try_resolve_from_definition("item_key", item, context)

        assert result is not None
        assert result.Success is True
        assert result.Value == "test_value"

    def test_try_resolve_from_definition_with_values(self, evaluator, context):
        """Test _try_resolve_from_definition with values field"""
        item = {"versions": [{"validFrom": "2020-01-01", "values": ["val1", "val2"]}]}
        result = evaluator._try_resolve_from_definition("item_key", item, context)

        assert result is not None
        assert result.Success is True
        assert result.Value == ["val1", "val2"]

    def test_try_resolve_from_definition_no_value(self, evaluator, context):
        """Test _try_resolve_from_definition without value or values"""
        item = {"versions": [{"validFrom": "2020-01-01", "type": "Text"}]}
        result = evaluator._try_resolve_from_definition("item_key", item, context)

        assert result is None

    def test_try_resolve_from_target_source_success(self, evaluator, context):
        """Test _try_resolve_from_target_source with successful resolution"""
        item = {"versions": [{"type": "Text"}]}
        context.get_target_source_item = Mock(return_value="source_item")
        source_result = create_result(success=True, value="source_val", source="ItemEvaluator")
        context.item_evaluator.evaluate_item = Mock(return_value=source_result)

        result = evaluator._try_resolve_from_target_source("test_item", item, context)

        assert result is not None
        assert result.Success is True
        assert result.Value == "source_val"

    def test_try_resolve_from_target_source_no_source(self, evaluator, context):
        """Test _try_resolve_from_target_source when no source exists"""
        item = {"versions": [{"type": "Text"}]}
        context.get_target_source_item = Mock(return_value=None)

        result = evaluator._try_resolve_from_target_source("test_item", item, context)

        assert result is None

    def test_try_resolve_from_input_source_parameter(self, evaluator, context):
        """Test _try_resolve_from_input_source with parameter"""
        item = {"versions": [{"type": "Text"}]}
        context.get_input_source = Mock(return_value="param_name")
        context.get_parameter_value = Mock(return_value="param_val")

        result = evaluator._try_resolve_from_input_source("test_item", item, context)

        assert result is not None
        assert result.Success is True
        assert result.Value == "param_val"

    def test_try_resolve_from_input_source_value_provider(self, evaluator, context):
        """Test _try_resolve_from_input_source with value provider"""
        item = {"versions": [{"type": "Text"}]}
        mock_provider = Mock()
        provider_result = create_result(success=True, value="prov_val", source="Provider")
        mock_provider.get_value = Mock(return_value=provider_result)

        context.get_input_source = Mock(return_value="input_name")
        context.get_parameter_value = Mock(return_value=None)
        context.get_value_provider_for = Mock(return_value=mock_provider)

        result = evaluator._try_resolve_from_input_source("test_item", item, context)

        assert result is not None
        assert result.Success is True
        assert result.Value == "prov_val"

    def test_try_resolve_from_input_source_no_source(self, evaluator, context):
        """Test _try_resolve_from_input_source when no input source exists"""
        item = {"versions": [{"type": "Text"}]}
        context.get_input_source = Mock(return_value=None)

        result = evaluator._try_resolve_from_input_source("test_item", item, context)

        assert result is None

    def test_evaluation_priority_order(self, evaluator, context):
        """Test that evaluation follows the correct priority order"""
        # Definition has highest priority
        item = {"versions": [{"type": "Text", "value": "definition_value"}]}

        # Mock other sources that would return values
        context.get_target_source_item = Mock(return_value="source_item")
        context.get_input_source = Mock(return_value="param_name")
        context.get_parameter_value = Mock(return_value="param_value")

        result = evaluator.evaluate("test_item", item, context)

        # Should return definition value, not parameter value
        assert result.Value == "definition_value"
        # Should not have called item_evaluator since definition was found first
        context.item_evaluator.evaluate_item.assert_not_called()
