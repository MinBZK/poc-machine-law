from unittest.mock import Mock

import pytest

from machine.context import PathNode
from machine.nrml.context import NrmlRuleContext
from machine.nrml.evaluation_result import create_result


class TestNrmlRuleContext:
    """Test cases for NrmlRuleContext"""

    @pytest.fixture
    def context(self):
        """Create a basic NrmlRuleContext instance"""
        return NrmlRuleContext(
            calculation_date="2024-01-01",
            parameters={"param1": "value1"},
            nrml_spec={"metadata": {"description": "test"}},
            items={"item1": {"name": "Test Item"}},
            target_references={"#/facts/target1": "item1"},
            inputs={"#/facts/input1": "param1"},
        )

    def test_get_value_provider_for_with_match(self, context):
        """Test getting value provider that can provide the value"""
        # Create mock value providers
        provider1 = Mock()
        provider1.can_provide_value.return_value = False

        provider2 = Mock()
        provider2.can_provide_value.return_value = True

        context.value_providers = [provider1, provider2]

        result = context.get_value_provider_for("test_value")

        assert result == provider2
        provider1.can_provide_value.assert_called_once_with("test_value")
        provider2.can_provide_value.assert_called_once_with("test_value")

    def test_get_value_provider_for_no_match(self, context):
        """Test getting value provider when none can provide"""
        # Create mock value provider that can't provide
        provider = Mock()
        provider.can_provide_value.return_value = False

        context.value_providers = [provider]

        result = context.get_value_provider_for("test_value")

        assert result is None

    def test_get_value_provider_for_empty_providers(self, context):
        """Test getting value provider with no providers"""
        context.value_providers = []

        result = context.get_value_provider_for("test_value")

        assert result is None

    def test_add_to_path_first_node(self, context):
        """Test adding first node to path"""
        node = PathNode(type="test", name="Node1", result=None)

        context.add_to_path(node)

        assert len(context.path) == 1
        assert context.path[0] == node

    def test_add_to_path_child_node(self, context):
        """Test adding child node to existing path"""
        parent_node = PathNode(type="test", name="Parent", result=None)
        child_node = PathNode(type="test", name="Child", result=None)

        context.add_to_path(parent_node)
        context.add_to_path(child_node)

        assert len(context.path) == 2
        assert context.path[0] == parent_node
        assert context.path[1] == child_node
        assert child_node in parent_node.children

    def test_pop_path(self, context):
        """Test removing node from path"""
        node1 = PathNode(type="test", name="Node1", result=None)
        node2 = PathNode(type="test", name="Node2", result=None)

        context.add_to_path(node1)
        context.add_to_path(node2)
        context.pop_path()

        assert len(context.path) == 1
        assert context.path[0] == node1

    def test_pop_path_empty(self, context):
        """Test popping from empty path does not error"""
        context.path = []

        context.pop_path()  # Should not raise error

        assert len(context.path) == 0

    def test_get_evaluation_result_exists(self, context):
        """Test getting evaluation result that exists"""
        result = create_result(success=True, value=42, source="Test")
        context.evaluation_results["item_key"] = result

        retrieved = context.get_evaluation_result("item_key")

        assert retrieved == result

    def test_get_evaluation_result_not_exists(self, context):
        """Test getting evaluation result that doesn't exist"""
        result = context.get_evaluation_result("nonexistent")

        assert result is None

    def test_add_evaluation_result(self, context):
        """Test adding evaluation result"""
        result = create_result(success=True, value=42, source="Test")

        context.add_evaluation_result("item_key", result)

        assert "item_key" in context.evaluation_results
        assert context.evaluation_results["item_key"] == result

    def test_add_evaluation_result_duplicate_raises(self, context):
        """Test adding duplicate evaluation result raises error"""
        result1 = create_result(success=True, value=42, source="Test")
        result2 = create_result(success=True, value=99, source="Test")

        context.add_evaluation_result("item_key", result1)

        with pytest.raises(ValueError, match="Evaluation result for item 'item_key' already exists"):
            context.add_evaluation_result("item_key", result2)

    def test_get_target_source_item_exists(self, context):
        """Test getting target source item that exists"""
        result = context.get_target_source_item("#/facts/target1")

        assert result == "item1"

    def test_get_target_source_item_not_exists(self, context):
        """Test getting target source item that doesn't exist"""
        result = context.get_target_source_item("#/facts/nonexistent")

        assert result is None

    def test_get_parameter_value_exists(self, context):
        """Test getting parameter value that exists"""
        result = context.get_parameter_value("param1")

        assert result == "value1"

    def test_get_parameter_value_not_exists(self, context):
        """Test getting parameter value that doesn't exist"""
        result = context.get_parameter_value("nonexistent")

        assert result is None

    def test_get_input_source_exists(self, context):
        """Test getting input source that exists"""
        result = context.get_input_source("#/facts/input1")

        assert result == "param1"

    def test_get_input_source_not_exists(self, context):
        """Test getting input source that doesn't exist"""
        result = context.get_input_source("#/facts/nonexistent")

        assert result is None

    def test_from_nrml_engine(self):
        """Test creating context from NRML engine"""
        # Create mock engine
        mock_engine = Mock()
        mock_engine.spec = {"metadata": {"description": "test_spec"}}
        mock_engine.items = {"item1": {"type": "test"}}

        parameters = {"param1": "value1"}
        target_references = {"#/facts/target1": "item1"}
        inputs = {"#/facts/input1": "param1"}

        context = NrmlRuleContext.from_nrml_engine(
            nrml_engine=mock_engine,
            parameters=parameters,
            target_references=target_references,
            inputs=inputs,
            calculation_date="2024-01-01",
        )

        assert context.calculation_date == "2024-01-01"
        assert context.parameters == parameters
        assert context.nrml_spec == mock_engine.spec
        assert context.items == mock_engine.items
        assert context.target_references == target_references
        assert context.inputs == inputs
        assert context.item_evaluator is not None

    def test_from_nrml_engine_with_table_value_providers(self):
        """Test creating context with table value providers"""
        mock_engine = Mock()
        mock_engine.spec = {}
        mock_engine.items = {}

        provider = Mock()
        providers = [provider]

        context = NrmlRuleContext.from_nrml_engine(
            nrml_engine=mock_engine,
            parameters={},
            target_references={},
            inputs={},
            table_value_providers=providers,
        )

        assert context.value_providers == providers

    def test_default_values(self):
        """Test context with default values"""
        context = NrmlRuleContext()

        assert context.calculation_date is None
        assert context.parameters == {}
        assert context.resolved_paths == {}
        assert context.path == []
        assert context.nrml_spec == {}
        assert context.items == {}
        assert context.target_references == {}
        assert context.inputs == {}
        assert context.item_evaluator is None
        assert context.evaluation_results == {}
        assert context.language == "nl"
        assert context.value_providers == []

    def test_custom_language(self):
        """Test creating context with custom language"""
        context = NrmlRuleContext(language="en")

        assert context.language == "en"

    def test_path_building_sequence(self, context):
        """Test building and unwinding a path sequence"""
        node1 = PathNode(type="test", name="Root", result=None)
        node2 = PathNode(type="test", name="Child1", result=None)
        node3 = PathNode(type="test", name="Child2", result=None)

        # Build path
        context.add_to_path(node1)
        assert len(context.path) == 1

        context.add_to_path(node2)
        assert len(context.path) == 2
        assert node2 in node1.children

        context.add_to_path(node3)
        assert len(context.path) == 3
        assert node3 in node2.children

        # Unwind path
        context.pop_path()
        assert len(context.path) == 2

        context.pop_path()
        assert len(context.path) == 1

        context.pop_path()
        assert len(context.path) == 0
