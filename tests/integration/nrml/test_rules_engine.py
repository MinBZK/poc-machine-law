import json
from pathlib import Path

from machine.nrml.rules_engine import NrmlRulesEngine


class TestNrmlRulesEngineIntegration:
    """Integration tests for NrmlRulesEngine using inline NRML specifications"""

    def test_simple_evaluation(self):
        """Simple test to verify basic engine evaluation works with a value definition"""
        # Define inline NRML spec with a simple value
        spec = {
            "version": "3.0",
            "language": "nl",
            "metadata": {"description": "test_simple"},
            "inputs": {},
            "outputs": {"my_value": {"source": {"$ref": "#/facts/constants/items/test-value"}}},
            "facts": {
                "constants": {
                    "name": {"nl": "Constanten"},
                    "items": {
                        "test-value": {
                            "name": {"nl": "Test waarde"},
                            "versions": [{"validFrom": "2020-01-01", "type": "number", "value": 42}],
                        }
                    },
                }
            },
        }

        # Create engine and evaluate
        engine = NrmlRulesEngine(spec)
        result = engine.evaluate(parameters={}, requested_output="my_value")

        # Verify result
        assert "output" in result
        assert "my_value" in result["output"]
        output = result["output"]["my_value"]
        assert output["value"] == 42
        assert output["process"].Success is True

    def test_input_parameter_passthrough(self):
        """Test that input parameter is passed through and returned as output"""
        # Define inline NRML spec that takes an input and returns it
        spec = {
            "version": "3.0",
            "language": "nl",
            "metadata": {"description": "test_passthrough"},
            "inputs": {"my_input": {"target": {"$ref": "#/facts/data/items/input-value"}}},
            "outputs": {"my_output": {"source": {"$ref": "#/facts/data/items/input-value"}}},
            "facts": {
                "data": {
                    "name": {"nl": "Data"},
                    "items": {
                        "input-value": {
                            "name": {"nl": "Input waarde"},
                            "versions": [{"validFrom": "2020-01-01", "type": "text"}],
                        }
                    },
                }
            },
        }

        # Create engine and evaluate
        engine = NrmlRulesEngine(spec)
        result = engine.evaluate(parameters={"my_input": "Hello World"}, requested_output="my_output")

        # Verify result - should return the input parameter value
        assert "output" in result
        assert "my_output" in result["output"]
        output = result["output"]["my_output"]
        assert output["value"] == "Hello World"
        assert output["process"].Success is True

    def test_conditional_expression(self):
        """Test conditional expression that returns 42 if true, -1 if false"""
        # Define inline NRML spec with conditional expression using item reference
        spec = {
            "version": "3.0",
            "language": "nl",
            "metadata": {"description": "test_conditional"},
            "inputs": {},
            "outputs": {"result": {"source": {"$ref": "#/facts/result/items/result-value"}}},
            "facts": {
                "data": {
                    "name": {"nl": "Data"},
                    "items": {
                        "check-value": {
                            "name": {"nl": "Controle waarde"},
                            "versions": [{"validFrom": "2020-01-01", "type": "boolean", "value": True}],
                        }
                    },
                },
                "calculated": {
                    "name": {"nl": "Berekend"},
                    "items": {
                        "conditional-calc": {
                            "name": {"nl": "Conditionele berekening"},
                            "versions": [
                                {
                                    "validFrom": "2020-01-01",
                                    "target": [{"$ref": "#/facts/result/items/result-value"}],
                                    "expression": {
                                        "type": "conditional",
                                        "condition": {
                                            "type": "comparison",
                                            "operator": "in",
                                            "arguments": [
                                                {"$ref": "#/facts/data/items/check-value"},
                                                {"value": [True]},
                                            ],
                                        },
                                        "then": {"value": 42},
                                        "else": {"value": -1},
                                    },
                                }
                            ],
                        }
                    },
                },
                "result": {
                    "name": {"nl": "Resultaat"},
                    "items": {
                        "result-value": {
                            "name": {"nl": "Resultaat waarde"},
                            "versions": [{"validFrom": "2020-01-01", "type": "number"}],
                        }
                    },
                },
            },
        }

        # Create engine and evaluate - condition is true, should return 42
        engine = NrmlRulesEngine(spec)
        result = engine.evaluate(parameters={}, requested_output="result")

        # Verify result
        assert "output" in result
        assert "result" in result["output"]
        output = result["output"]["result"]
        assert output["value"] == 42
        assert output["process"].Success is True

    def test_conditional_expression_false(self):
        """Test conditional expression that evaluates to false returns -1"""
        # Define inline NRML spec with conditional expression using item reference
        spec = {
            "version": "3.0",
            "language": "nl",
            "metadata": {"description": "test_conditional_false"},
            "inputs": {},
            "outputs": {"result": {"source": {"$ref": "#/facts/result/items/result-value"}}},
            "facts": {
                "data": {
                    "name": {"nl": "Data"},
                    "items": {
                        "check-value": {
                            "name": {"nl": "Controle waarde"},
                            "versions": [{"validFrom": "2020-01-01", "type": "boolean", "value": False}],
                        }
                    },
                },
                "calculated": {
                    "name": {"nl": "Berekend"},
                    "items": {
                        "conditional-calc": {
                            "name": {"nl": "Conditionele berekening"},
                            "versions": [
                                {
                                    "validFrom": "2020-01-01",
                                    "target": [{"$ref": "#/facts/result/items/result-value"}],
                                    "expression": {
                                        "type": "conditional",
                                        "condition": {
                                            "type": "comparison",
                                            "operator": "in",
                                            "arguments": [
                                                {"$ref": "#/facts/data/items/check-value"},
                                                {"value": [True]},
                                            ],
                                        },
                                        "then": {"value": 42},
                                        "else": {"value": -1},
                                    },
                                }
                            ],
                        }
                    },
                },
                "result": {
                    "name": {"nl": "Resultaat"},
                    "items": {
                        "result-value": {
                            "name": {"nl": "Resultaat waarde"},
                            "versions": [{"validFrom": "2020-01-01", "type": "number"}],
                        }
                    },
                },
            },
        }

        # Create engine and evaluate - condition is false, should return -1
        engine = NrmlRulesEngine(spec)
        result = engine.evaluate(parameters={}, requested_output="result")

        # Verify result
        assert "output" in result
        assert "result" in result["output"]
        output = result["output"]["result"]
        assert output["value"] == -1
        assert output["process"].Success is True

    def test_count_expression(self):
        """Test aggregation expression that counts children based on age condition"""
        # Load NRML spec from fixture file
        fixture_path = Path(__file__).parent / "fixtures" / "test_count_expression.json"
        with open(fixture_path) as f:
            spec = json.load(f)

        # Test data: parent with 3 children of different ages
        children_data = [
            {"age": 8},
            {"age": 11},
            {"age": 15}
        ]

        aanvrager_data = [{}]

        # Create engine and evaluate
        engine = NrmlRulesEngine(spec)
        result = engine.evaluate(
            parameters={"kinderen": children_data,
                        "aanvrager": aanvrager_data},
            requested_output="young_children_count"
        )

        # Verify result - check that the count is correct
        assert "output" in result
        assert "young_children_count" in result["output"]
        output = result["output"]["young_children_count"]

        # Should count 1 child with age <= 10 (only the 8-year-old)
        assert output["value"] == 1
        assert output["process"].Success is True

    def test_count_with_arithmetic_multiplication(self):
        """Test arithmetic expression that multiplies count result with a constant value"""
        # Load NRML spec from fixture file
        fixture_path = Path(__file__).parent / "fixtures" / "test_count_with_arithmetic_multiplication.json"
        with open(fixture_path) as f:
            spec = json.load(f)

        # Test data: parent with 3 children of different ages
        children_data = [{"age": 8}, {"age": 9}, {"age": 15}]

        aanvrager_data = [{}]

        # Create engine and evaluate
        engine = NrmlRulesEngine(spec)
        result = engine.evaluate(
            parameters={"kinderen": children_data, "aanvrager": aanvrager_data}, requested_output="total_benefit"
        )

        # Verify result - should be count (2) * benefit_per_child (250.50) = 501.00
        assert "output" in result
        assert "total_benefit" in result["output"]
        output = result["output"]["total_benefit"]

        # 2 children with age <= 10 multiplied by 250.50 euro per child = 501.00
        assert output["value"] == 501.00
        assert output["process"].Success is True

    def test_nested_arithmetic_expression(self):
        """Test nested arithmetic expression: 2*5+10-min(4,6)/max(1,2) = 18"""
        # Load NRML spec from fixture file
        fixture_path = Path(__file__).parent / "fixtures" / "test_nested_arithmetic_expression.json"
        with open(fixture_path) as f:
            spec = json.load(f)

        # Create engine and evaluate
        engine = NrmlRulesEngine(spec)
        result = engine.evaluate(parameters={}, requested_output="result")

        # Verify result - should be 2*5+10-min(4,6)/max(1,2) = 10+10-4/2 = 20-2 = 18
        assert "output" in result
        assert "result" in result["output"]
        output = result["output"]["result"]

        # Expected: 2*5+10-min(4,6)/max(1,2) = 18
        assert output["value"] == 18
        assert output["process"].Success is True
