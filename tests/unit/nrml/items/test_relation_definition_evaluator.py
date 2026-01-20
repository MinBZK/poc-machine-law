import pytest

from machine.nrml.context import NrmlRuleContext
from machine.nrml.items.relation_definition_evaluator import RelationDefinitionEvaluator


class TestRelationDefinitionEvaluator:
    """Test cases for RelationDefinitionEvaluator"""

    @pytest.fixture
    def evaluator(self):
        """Create a relation definition evaluator instance"""
        return RelationDefinitionEvaluator()

    @pytest.fixture
    def context_with_inputs(self):
        """Create context with sample inputs configuration"""
        spec = {
            "inputs": {
                "aanvrager": {
                    "type": {"$ref": "#/facts/applicant"},
                    "properties": {"bsn": "#/facts/applicant/items/bsn"},
                },
                "kinderen": {
                    "type": {"$ref": "#/facts/child"},
                    "properties": {"age": "#/facts/child/items/age", "name": "#/facts/child/items/name"},
                },
            }
        }

        parameters = {
            "aanvrager": [{"bsn": "123456789"}],
            "kinderen": [{"age": 8, "name": "Alice"}, {"age": 11, "name": "Bob"}],
        }

        return NrmlRuleContext(nrml_spec=spec, parameters=parameters)

    def test_find_input_for_fact_exists(self, evaluator, context_with_inputs):
        """Test finding input that matches fact reference"""
        result = evaluator._find_input_for_fact("#/facts/child", context_with_inputs)

        assert result is not None
        input_name, input_config = result
        assert input_name == "kinderen"
        assert input_config["type"]["$ref"] == "#/facts/child"

    def test_find_input_for_fact_not_exists(self, evaluator, context_with_inputs):
        """Test finding input that doesn't exist"""
        result = evaluator._find_input_for_fact("#/facts/nonexistent", context_with_inputs)

        assert result is None

    def test_find_input_for_fact_empty_inputs(self, evaluator):
        """Test finding input when inputs are empty"""
        context = NrmlRuleContext(nrml_spec={"inputs": {}})

        result = evaluator._find_input_for_fact("#/facts/child", context)

        assert result is None

    def test_get_property_mappings(self, evaluator):
        """Test extracting property mappings from input config"""
        input_config = {"properties": {"age": "#/facts/child/items/age", "name": "#/facts/child/items/name"}}

        mappings = evaluator._get_property_mappings(input_config)

        assert mappings == {"age": "#/facts/child/items/age", "name": "#/facts/child/items/name"}

    def test_get_property_mappings_empty(self, evaluator):
        """Test extracting property mappings when none exist"""
        input_config = {}

        mappings = evaluator._get_property_mappings(input_config)

        assert mappings == {}

    def test_resolve_argument_data_success(self, evaluator, context_with_inputs):
        """Test resolving argument data successfully"""
        result = evaluator._resolve_argument_data("#/facts/child", context_with_inputs)

        assert len(result) == 2
        assert result[0] == {
            "#/facts/child/items/age": 8,
            "#/facts/child/items/name": "Alice",
        }
        assert result[1] == {
            "#/facts/child/items/age": 11,
            "#/facts/child/items/name": "Bob",
        }

    def test_resolve_argument_data_no_matching_input(self, evaluator, context_with_inputs):
        """Test resolving argument data when no matching input exists"""
        result = evaluator._resolve_argument_data("#/facts/nonexistent", context_with_inputs)

        assert result == []

    def test_resolve_argument_data_no_parameter_value(self, evaluator):
        """Test resolving argument data when parameter value doesn't exist"""
        spec = {
            "inputs": {
                "kinderen": {"type": {"$ref": "#/facts/child"}, "properties": {"age": "#/facts/child/items/age"}}
            }
        }
        context = NrmlRuleContext(nrml_spec=spec, parameters={})  # Empty parameters

        result = evaluator._resolve_argument_data("#/facts/child", context)

        assert result == []

    def test_resolve_argument_data_empty_fact_ref(self, evaluator, context_with_inputs):
        """Test resolving with empty fact reference"""
        result = evaluator._resolve_argument_data("", context_with_inputs)

        assert result == []

    def test_resolve_argument_data_none_fact_ref(self, evaluator, context_with_inputs):
        """Test resolving with None fact reference"""
        result = evaluator._resolve_argument_data(None, context_with_inputs)

        assert result == []

    def test_evaluate_valid_relation(self, evaluator, context_with_inputs):
        """Test evaluating a valid relation with 2 arguments"""
        item = {
            "versions": [
                {
                    "validFrom": "2020-01-01",
                    "arguments": [
                        {"objectType": {"$ref": "#/facts/applicant"}},
                        {"objectType": {"$ref": "#/facts/child"}},
                    ],
                }
            ]
        }

        result = evaluator.evaluate("test_relation", item, context_with_inputs)

        assert result.Success is True
        # 1 applicant x 2 children = 2 combinations
        assert len(result.Value) == 2
        assert result.Value[0] == {
            "#/facts/applicant": {"#/facts/applicant/items/bsn": "123456789"},
            "#/facts/child": {"#/facts/child/items/age": 8, "#/facts/child/items/name": "Alice"},
        }
        assert result.Value[1] == {
            "#/facts/applicant": {"#/facts/applicant/items/bsn": "123456789"},
            "#/facts/child": {"#/facts/child/items/age": 11, "#/facts/child/items/name": "Bob"},
        }
        assert "Relation test_relation resolved with 2 arguments" in result.Action

    def test_evaluate_multiple_applicants(self, evaluator):
        """Test evaluating relation with multiple applicants and children"""
        spec = {
            "inputs": {
                "aanvrager": {
                    "type": {"$ref": "#/facts/applicant"},
                    "properties": {"id": "#/facts/applicant/items/id"},
                },
                "kinderen": {"type": {"$ref": "#/facts/child"}, "properties": {"id": "#/facts/child/items/id"}},
            }
        }

        parameters = {
            "aanvrager": [{"id": "A1"}, {"id": "A2"}],
            "kinderen": [{"id": "C1"}, {"id": "C2"}, {"id": "C3"}],
        }

        context = NrmlRuleContext(nrml_spec=spec, parameters=parameters, calculation_date="2024-01-01")

        item = {
            "versions": [
                {
                    "validFrom": "2020-01-01",
                    "arguments": [
                        {"objectType": {"$ref": "#/facts/applicant"}},
                        {"objectType": {"$ref": "#/facts/child"}},
                    ],
                }
            ]
        }

        result = evaluator.evaluate("test_relation", item, context)

        # 2 applicants x 3 children = 6 combinations
        assert result.Success is True
        assert len(result.Value) == 6

    def test_evaluate_invalid_argument_count_zero(self, evaluator, context_with_inputs):
        """Test evaluating relation with zero arguments raises error"""
        item = {"versions": [{"validFrom": "2020-01-01", "arguments": []}]}

        with pytest.raises(ValueError, match="must have exactly 2 arguments, found 0"):
            evaluator.evaluate("test_relation", item, context_with_inputs)

    def test_evaluate_invalid_argument_count_one(self, evaluator, context_with_inputs):
        """Test evaluating relation with one argument raises error"""
        item = {"versions": [{"validFrom": "2020-01-01", "arguments": [{"objectType": {"$ref": "#/facts/child"}}]}]}

        with pytest.raises(ValueError, match="must have exactly 2 arguments, found 1"):
            evaluator.evaluate("test_relation", item, context_with_inputs)

    def test_evaluate_invalid_argument_count_three(self, evaluator, context_with_inputs):
        """Test evaluating relation with three arguments raises error"""
        item = {
            "versions": [
                {
                    "validFrom": "2020-01-01",
                    "arguments": [
                        {"objectType": {"$ref": "#/facts/applicant"}},
                        {"objectType": {"$ref": "#/facts/child"}},
                        {"objectType": {"$ref": "#/facts/other"}},
                    ],
                }
            ]
        }

        with pytest.raises(ValueError, match="must have exactly 2 arguments, found 3"):
            evaluator.evaluate("test_relation", item, context_with_inputs)

    def test_evaluate_empty_arguments(self, evaluator):
        """Test evaluating when arguments resolve to empty data"""
        spec = {
            "inputs": {
                "aanvrager": {
                    "type": {"$ref": "#/facts/applicant"},
                    "properties": {"id": "#/facts/applicant/items/id"},
                }
            }
        }

        parameters = {"aanvrager": []}  # Empty list

        context = NrmlRuleContext(nrml_spec=spec, parameters=parameters, calculation_date="2024-01-01")

        item = {
            "versions": [
                {
                    "validFrom": "2020-01-01",
                    "arguments": [
                        {"objectType": {"$ref": "#/facts/applicant"}},
                        {"objectType": {"$ref": "#/facts/child"}},
                    ],
                }
            ]
        }

        result = evaluator.evaluate("test_relation", item, context)

        assert result.Success is True
        assert result.Value == []
        assert "resolved with 0 arguments" in result.Action

    def test_evaluate_uses_active_version(self, evaluator, context_with_inputs):
        """Test that evaluate uses the active version based on calculation date"""
        item = {
            "versions": [
                {
                    "validFrom": "2020-01-01",
                    "arguments": [
                        {"objectType": {"$ref": "#/facts/applicant"}},
                        {"objectType": {"$ref": "#/facts/child"}},
                    ],
                },
                {
                    "validFrom": "2025-01-01",
                    "arguments": [
                        {"objectType": {"$ref": "#/facts/other"}},
                        {"objectType": {"$ref": "#/facts/another"}},
                    ],
                },
            ]
        }

        # Context with date that should use first version
        context_with_inputs.calculation_date = "2024-01-01"

        result = evaluator.evaluate("test_relation", item, context_with_inputs)

        # Should resolve based on first version's arguments
        assert result.Success is True
        assert len(result.Value) == 2  # 1 applicant x 2 children

    def test_evaluator_is_stateless(self, evaluator, context_with_inputs):
        """Test that evaluator doesn't maintain state between calls"""
        item = {
            "versions": [
                {
                    "validFrom": "2020-01-01",
                    "arguments": [
                        {"objectType": {"$ref": "#/facts/applicant"}},
                        {"objectType": {"$ref": "#/facts/child"}},
                    ],
                }
            ]
        }

        # First evaluation
        result1 = evaluator.evaluate("relation1", item, context_with_inputs)
        # Second evaluation
        result2 = evaluator.evaluate("relation2", item, context_with_inputs)

        # Both should have same structure
        assert result1.Value == result2.Value
        # But different actions mentioning different item keys
        assert "relation1" in result1.Action
        assert "relation2" in result2.Action
