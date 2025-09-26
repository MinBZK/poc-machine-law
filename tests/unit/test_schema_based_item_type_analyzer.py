import pytest
import json
from pathlib import Path
from machine.nrml.schema_based_item_type_analyzer import NrmlSchemaBasedItemTypeAnalyzer, determine_item_type
from machine.nrml.schema_based_item_type_analyzer import NrmlItemType as SchemaNrmlItemType
from machine.nrml.item_type_analyzer import determine_item_type as basic_determine_item_type, NrmlItemType as BasicNrmlItemType


class TestSchemaBasedItemTypeAnalyzer:
    """Test the schema-based item type analyzer"""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return NrmlSchemaBasedItemTypeAnalyzer()

    @pytest.fixture
    def brp_data(self):
        """Load BRP NRML test data"""
        project_root = Path(__file__).parent.parent.parent
        brp_path = project_root / "law" / "nrml" / "brp_nationaliteit.nrml.json"
        with open(brp_path, 'r') as f:
            return json.load(f)

    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initializes correctly"""
        assert analyzer.schema is not None
        assert len(analyzer.item_type_schemas) == 7
        assert SchemaNrmlItemType.TYPE_DEFINITION in analyzer.item_type_schemas
        assert SchemaNrmlItemType.CALCULATED_VALUE in analyzer.item_type_schemas

    def test_schema_validation_vs_rule_based(self, analyzer, brp_data):
        """Compare schema validation results with rule-based detection"""
        for fact_id, fact in brp_data['facts'].items():
            for item_id, item in fact['items'].items():
                schema_result = analyzer.determine_item_type(item)
                rule_result = basic_determine_item_type(item)

                # Both methods should give the same result for valid items (compare values)
                assert schema_result.value == rule_result.value, f"Mismatch for item {item_id}: schema={schema_result.value}, rule={rule_result.value}"

    def test_type_definition_validation(self, analyzer):
        """Test schema validation for type definitions"""
        # Text type
        text_item = {
            "name": {"nl": "test", "en": "test"},
            "versions": [{"validFrom": "2020-01-01", "type": "text"}]
        }
        assert analyzer.determine_item_type(text_item) == SchemaNrmlItemType.TYPE_DEFINITION

        # Enumeration type
        enum_item = {
            "name": {"nl": "test", "en": "test"},
            "versions": [{"validFrom": "2020-01-01", "type": "enumeration", "values": ["A", "B"]}]
        }
        assert analyzer.determine_item_type(enum_item) == SchemaNrmlItemType.TYPE_DEFINITION

    def test_calculated_value_validation(self, analyzer):
        """Test schema validation for calculated values"""
        calc_item = {
            "name": {"nl": "test", "en": "test"},
            "versions": [{
                "validFrom": "2020-01-01",
                "target": [{"$ref": "#/facts/test/items/test"}],
                "expression": {"type": "conditional", "condition": {}, "then": {"value": True}, "else": {"value": False}}
            }]
        }
        assert analyzer.determine_item_type(calc_item) == SchemaNrmlItemType.CALCULATED_VALUE

    def test_get_schema_info(self, analyzer):
        """Test getting schema information"""
        type_def_schema = analyzer.get_schema_info(SchemaNrmlItemType.TYPE_DEFINITION)
        assert "required" in type_def_schema
        assert "validFrom" in type_def_schema["required"]
        assert "type" in type_def_schema["required"]

    def test_get_required_fields(self, analyzer):
        """Test getting required fields"""
        required = analyzer.get_required_fields(SchemaNrmlItemType.TYPE_DEFINITION)
        assert "validFrom" in required
        assert "type" in required

    def test_get_allowed_fields(self, analyzer):
        """Test getting allowed fields"""
        allowed = analyzer.get_allowed_fields(SchemaNrmlItemType.CALCULATED_VALUE)
        assert "validFrom" in allowed
        assert "target" in allowed
        assert "expression" in allowed

    def test_fallback_detection(self, analyzer):
        """Test fallback to rule-based detection"""
        # Create an item that might not validate perfectly but has clear structure
        fallback_item = {
            "name": {"nl": "test", "en": "test"},
            "versions": [{
                "validFrom": "2020-01-01",
                "type": "text",
                "extra_field": "should_not_break_detection"
            }]
        }
        # Should still detect as type definition
        result = analyzer.determine_item_type(fallback_item)
        assert result in [SchemaNrmlItemType.TYPE_DEFINITION, SchemaNrmlItemType.UNKNOWN]

    def test_convenience_function(self, brp_data):
        """Test the convenience determine_item_type function"""
        first_item = next(iter(next(iter(brp_data['facts'].values()))['items'].values()))
        result = determine_item_type(first_item)
        assert isinstance(result, SchemaNrmlItemType)
        assert result != SchemaNrmlItemType.UNKNOWN

    def test_invalid_items(self, analyzer):
        """Test handling of invalid items"""
        assert analyzer.determine_item_type({}) == SchemaNrmlItemType.UNKNOWN
        assert analyzer.determine_item_type({"versions": []}) == SchemaNrmlItemType.UNKNOWN
        assert analyzer.determine_item_type({"versions": ["invalid"]}) == SchemaNrmlItemType.UNKNOWN