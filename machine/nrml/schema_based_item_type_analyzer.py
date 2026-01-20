import json
from enum import Enum
from pathlib import Path
from typing import Any

from jsonschema import ValidationError, validate


class NrmlItemType(Enum):
    """Enumeration of NRML item types based on schema definitions"""

    TYPE_DEFINITION = "typeDefinition"
    RELATION_DEFINITION = "relationDefinition"
    VALUE_INITIALIZATION = "valueInitialization"
    CONDITIONAL_CHARACTERISTIC = "conditionalCharacteristic"
    CALCULATED_VALUE = "calculatedValue"
    CONDITIONAL_VALUE = "conditionalValue"
    CONDITIONAL_CALCULATED_VALUE = "conditionalCalculatedValue"
    UNKNOWN = "unknown"


# alternative approach to analyzing the item types, but very slow
#   Speed Comparison:
#
#   - Rule-based analyzer: ~2.5 million calls/second
#   - Schema-based analyzer: ~4 calls/second
#   - Performance ratio: ~615,000x faster (rule-based)


class NrmlSchemaBasedItemTypeAnalyzer:
    """Schema-based NRML item type analyzer that uses schema.json for validation"""

    def __init__(self, schema_path: str = None):
        """Initialize with schema file path"""
        if schema_path is None:
            # Default to schema.json in law/nrml directory
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent
            schema_path = project_root / "law" / "nrml" / "schema.json"

        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()
        self.item_type_schemas = self._extract_item_type_schemas()

    def _load_schema(self) -> dict[str, Any]:
        """Load the JSON schema file"""
        try:
            with open(self.schema_path, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in schema file: {e}")

    def _extract_item_type_schemas(self) -> dict[str, dict[str, Any]]:
        """Extract individual item type schemas from the $defs section"""
        defs = self.schema.get("$defs", {})
        item_type_schemas = {}

        # Map each item type to its schema definition
        type_mappings = {
            NrmlItemType.TYPE_DEFINITION: "typeDefinition",
            NrmlItemType.RELATION_DEFINITION: "relationDefinition",
            NrmlItemType.VALUE_INITIALIZATION: "valueInitialization",
            NrmlItemType.CONDITIONAL_CHARACTERISTIC: "conditionalCharacteristic",
            NrmlItemType.CALCULATED_VALUE: "calculatedValue",
            NrmlItemType.CONDITIONAL_VALUE: "conditionalValue",
            NrmlItemType.CONDITIONAL_CALCULATED_VALUE: "conditionalCalculatedValue",
        }

        for item_type, schema_key in type_mappings.items():
            if schema_key in defs:
                item_type_schemas[item_type] = defs[schema_key]

        return item_type_schemas

    def _validate_against_schema(self, version: dict[str, Any], item_type: NrmlItemType) -> bool:
        """Validate a version object against a specific item type schema"""
        if item_type not in self.item_type_schemas:
            return False

        try:
            # Create a temporary schema that includes the $defs for reference resolution
            temp_schema = {**self.item_type_schemas[item_type], "$defs": self.schema.get("$defs", {})}

            validate(instance=version, schema=temp_schema)
            return True
        except ValidationError:
            return False
        except Exception:
            # Handle any other validation errors
            return False

    def determine_item_type(self, item: dict[str, Any]) -> NrmlItemType:
        """
        Determine the NRML item type using schema validation.

        Args:
            item: The item dictionary from NRML facts

        Returns:
            NrmlItemType: The determined item type
        """
        if not isinstance(item, dict) or "versions" not in item:
            return NrmlItemType.UNKNOWN

        # Analyze the first version (assuming all versions have the same type)
        versions = item.get("versions", [])
        if not versions:
            return NrmlItemType.UNKNOWN

        version = versions[0]
        if not isinstance(version, dict):
            return NrmlItemType.UNKNOWN

        # Try to validate against each item type schema
        # Order matters - more specific types should be checked first
        validation_order = [
            NrmlItemType.RELATION_DEFINITION,
            NrmlItemType.CONDITIONAL_CALCULATED_VALUE,
            NrmlItemType.CONDITIONAL_VALUE,
            NrmlItemType.CONDITIONAL_CHARACTERISTIC,
            NrmlItemType.CALCULATED_VALUE,
            NrmlItemType.VALUE_INITIALIZATION,
            NrmlItemType.TYPE_DEFINITION,
        ]

        for item_type in validation_order:
            if self._validate_against_schema(version, item_type):
                return item_type

        # Fallback to rule-based detection if schema validation fails
        return self._fallback_rule_based_detection(version)

    def _fallback_rule_based_detection(self, version: dict[str, Any]) -> NrmlItemType:
        """Fallback to rule-based detection if schema validation fails"""
        # Check for presence of key fields
        has_target = "target" in version
        has_type = "type" in version
        has_condition = "condition" in version
        has_expression = "expression" in version
        has_value = "value" in version
        has_a = "a" in version
        has_b = "b" in version

        # Apply schema-based detection rules (same as original)
        if has_a and has_b:
            return NrmlItemType.RELATION_DEFINITION
        if has_type and not has_target:
            return NrmlItemType.TYPE_DEFINITION
        if has_target and has_expression and has_condition:
            return NrmlItemType.CONDITIONAL_CALCULATED_VALUE
        if has_target and has_value and has_condition:
            return NrmlItemType.CONDITIONAL_VALUE
        if has_target and has_expression and not has_condition:
            return NrmlItemType.CALCULATED_VALUE
        if has_target and has_condition and not has_value and not has_expression:
            return NrmlItemType.CONDITIONAL_CHARACTERISTIC
        if has_target and has_value and not has_condition and not has_expression:
            return NrmlItemType.VALUE_INITIALIZATION

        return NrmlItemType.UNKNOWN

    def get_schema_info(self, item_type: NrmlItemType) -> dict[str, Any]:
        """Get schema information for a specific item type"""
        return self.item_type_schemas.get(item_type, {})

    def get_required_fields(self, item_type: NrmlItemType) -> list[str]:
        """Get required fields for a specific item type"""
        schema = self.item_type_schemas.get(item_type, {})
        return schema.get("required", [])

    def get_allowed_fields(self, item_type: NrmlItemType) -> set[str]:
        """Get all allowed fields for a specific item type"""
        schema = self.item_type_schemas.get(item_type, {})
        properties = schema.get("properties", {})
        return set(properties.keys())


# Convenience function that uses the default analyzer
_default_analyzer = None


def determine_item_type(item: dict[str, Any]) -> NrmlItemType:
    """
    Convenience function to determine item type using the default schema-based analyzer.

    Args:
        item: The item dictionary from NRML facts

    Returns:
        NrmlItemType: The determined item type
    """
    global _default_analyzer
    if _default_analyzer is None:
        _default_analyzer = NrmlSchemaBasedItemTypeAnalyzer()

    return _default_analyzer.determine_item_type(item)
