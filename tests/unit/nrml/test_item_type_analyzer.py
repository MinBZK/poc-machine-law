from machine.nrml.item_type_analyzer import NrmlItemType, determine_item_type


class TestItemTypeAnalyzer:
    """Unit tests for NRML item type analyzer using real examples from brp_nationaliteit.nrml.json"""

    def test_type_definition_text(self):
        """Test TYPE_DEFINITION with text type"""
        item = {
            "name": {"nl": "Nationaliteit definitie", "en": "Nationality definition"},
            "versions": [{"validFrom": "2020-01-01", "type": "text"}],
        }

        result = determine_item_type(item)
        assert result == NrmlItemType.TYPE_DEFINITION

    def test_type_definition_enumeration(self):
        """Test TYPE_DEFINITION with enumeration type"""
        item = {
            "name": {"nl": "Nederlandse nationaliteiten definitie", "en": "Dutch nationalities definition"},
            "versions": [{"validFrom": "2020-01-01", "type": "enumeration", "values": ["NEDERLANDS"]}],
        }

        result = determine_item_type(item)
        assert result == NrmlItemType.TYPE_DEFINITION

    def test_type_definition_boolean(self):
        """Test TYPE_DEFINITION with boolean type"""
        item = {
            "name": {"nl": "Nederlandse nationaliteit resultaat", "en": "Dutch nationality result"},
            "versions": [{"validFrom": "2020-01-01", "type": "boolean"}],
        }

        result = determine_item_type(item)
        assert result == NrmlItemType.TYPE_DEFINITION

    def test_calculated_value_with_expression(self):
        """Test CALCULATED_VALUE with target and expression (no condition)"""
        item = {
            "name": {"nl": "heeft Nederlandse nationaliteit definitie", "en": "has Dutch nationality definition"},
            "versions": [
                {
                    "validFrom": "2020-01-01",
                    "target": [
                        {
                            "$ref": "#/facts/f1e2d3c4-5b6a-7c8d-9e0f-1a2b3c4d5e6f/items/a2f3e4d5-6c7b-8d9e-0f1a-2b3c4d5e6f78"
                        }
                    ],
                    "expression": {
                        "type": "conditional",
                        "condition": {
                            "type": "comparison",
                            "operator": "in",
                            "arguments": [
                                [
                                    {
                                        "$ref": "#/facts/3c8e2a5f-1b6d-4e9c-7f2d-a5c3b6e1d9f4/items/9d2c5b1e-7f3a-4d6c-b2e8-f5a1c9d3b7e6"
                                    }
                                ],
                                {
                                    "parameter": {
                                        "$ref": "#/facts/8c3f1d6a-5b9e-4f2c-d7b1-e3a6f4c8d5b2/items/2d9f5c1b-7e3a-4b6d-c8f2-1a5e9d3b7f4c"
                                    }
                                },
                            ],
                        },
                        "then": {"value": True},
                        "else": {"value": False},
                    },
                }
            ],
        }

        result = determine_item_type(item)
        assert result == NrmlItemType.CALCULATED_VALUE

    def test_conditional_calculated_value(self):
        """Test CONDITIONAL_CALCULATED_VALUE with target, expression, and condition"""
        item = {
            "name": {"nl": "test conditional calculated value", "en": "test conditional calculated value"},
            "versions": [
                {
                    "validFrom": "2020-01-01",
                    "target": [{"$ref": "#/facts/test-fact/items/test-item"}],
                    "expression": {"type": "arithmetic", "operator": "add", "operands": [10, 20]},
                    "condition": {"type": "comparison", "operator": "equals", "left": "value1", "right": "value2"},
                }
            ],
        }

        result = determine_item_type(item)
        assert result == NrmlItemType.CONDITIONAL_CALCULATED_VALUE

    def test_value_initialization(self):
        """Test VALUE_INITIALIZATION with target and value (no condition, no expression)"""
        item = {
            "name": {"nl": "test value initialization", "en": "test value initialization"},
            "versions": [
                {
                    "validFrom": "2020-01-01",
                    "target": [{"$ref": "#/facts/test-fact/items/test-item"}],
                    "value": {"type": "boolean", "value": True},
                }
            ],
        }

        result = determine_item_type(item)
        assert result == NrmlItemType.VALUE_INITIALIZATION

    def test_conditional_value(self):
        """Test CONDITIONAL_VALUE with target, value, and condition"""
        item = {
            "name": {"nl": "test conditional value", "en": "test conditional value"},
            "versions": [
                {
                    "validFrom": "2020-01-01",
                    "target": [{"$ref": "#/facts/test-fact/items/test-item"}],
                    "value": {"type": "numeric", "value": 100},
                    "condition": {"type": "comparison", "operator": "greater_than", "left": "age", "right": 18},
                }
            ],
        }

        result = determine_item_type(item)
        assert result == NrmlItemType.CONDITIONAL_VALUE

    def test_conditional_characteristic(self):
        """Test CONDITIONAL_CHARACTERISTIC with target and condition (no value, no expression)"""
        item = {
            "name": {"nl": "test conditional characteristic", "en": "test conditional characteristic"},
            "versions": [
                {
                    "validFrom": "2020-01-01",
                    "target": [{"$ref": "#/facts/test-fact/items/test-item"}],
                    "condition": {"type": "comparison", "operator": "equals", "left": "status", "right": "active"},
                }
            ],
        }

        result = determine_item_type(item)
        assert result == NrmlItemType.CONDITIONAL_CHARACTERISTIC

    def test_relation_definition(self):
        """Test RELATION_DEFINITION with arguments array"""
        item = {
            "name": {"nl": "test relation", "en": "test relation"},
            "versions": [
                {
                    "validFrom": "2020-01-01",
                    "arguments": [
                        {
                            "name": {"nl": "persoon", "en": "person"},
                            "cardinality": "one",
                            "objectType": {"$ref": "#/facts/person-fact/items/person-item"},
                        },
                        {
                            "name": {"nl": "adres", "en": "address"},
                            "cardinality": "many",
                            "objectType": {"$ref": "#/facts/address-fact/items/address-item"},
                        },
                    ],
                }
            ],
        }

        result = determine_item_type(item)
        assert result == NrmlItemType.RELATION_DEFINITION

    def test_unknown_type_empty_item(self):
        """Test UNKNOWN type for empty item"""
        item = {}

        result = determine_item_type(item)
        assert result == NrmlItemType.UNKNOWN

    def test_unknown_type_no_versions(self):
        """Test UNKNOWN type for item without versions"""
        item = {"name": {"nl": "test item", "en": "test item"}}

        result = determine_item_type(item)
        assert result == NrmlItemType.UNKNOWN

    def test_unknown_type_empty_versions(self):
        """Test UNKNOWN type for item with empty versions array"""
        item = {"name": {"nl": "test item", "en": "test item"}, "versions": []}

        result = determine_item_type(item)
        assert result == NrmlItemType.UNKNOWN

    def test_unknown_type_invalid_version(self):
        """Test UNKNOWN type for item with non-dict version"""
        item = {"name": {"nl": "test item", "en": "test item"}, "versions": ["invalid"]}

        result = determine_item_type(item)
        assert result == NrmlItemType.UNKNOWN

    def test_unknown_type_unrecognized_pattern(self):
        """Test UNKNOWN type for unrecognized field pattern"""
        item = {
            "name": {"nl": "test item", "en": "test item"},
            "versions": [{"validFrom": "2020-01-01", "unknown_field": "unknown_value"}],
        }

        result = determine_item_type(item)
        assert result == NrmlItemType.UNKNOWN
