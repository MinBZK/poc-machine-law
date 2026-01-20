from enum import Enum
from typing import Any


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


def determine_item_type(item: dict[str, Any]) -> NrmlItemType:
    """
    Determine the NRML item type based on its structure and fields.

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

    # Check for presence of key fields
    has_target = "target" in version
    has_type = "type" in version
    has_condition = "condition" in version
    has_expression = "expression" in version
    has_value = "value" in version
    has_arguments = "arguments" in version

    # Apply schema-based detection rules

    # relationDefinition: has 'arguments' array
    if has_arguments:
        return NrmlItemType.RELATION_DEFINITION

    # typeDefinition: has 'type' but no 'target'
    if has_type and not has_target:
        return NrmlItemType.TYPE_DEFINITION

    # conditionalCalculatedValue: has 'target' + 'expression' + 'condition'
    if has_target and has_expression and has_condition:
        return NrmlItemType.CONDITIONAL_CALCULATED_VALUE

    # conditionalValue: has 'target' + 'value' + 'condition'
    if has_target and has_value and has_condition:
        return NrmlItemType.CONDITIONAL_VALUE

    # calculatedValue: has 'target' + 'expression' (no condition)
    if has_target and has_expression and not has_condition:
        return NrmlItemType.CALCULATED_VALUE

    # conditionalCharacteristic: has 'target' + 'condition' (no value, no expression)
    if has_target and has_condition and not has_value and not has_expression:
        return NrmlItemType.CONDITIONAL_CHARACTERISTIC

    # valueInitialization: has 'target' + 'value' (no condition, no expression)
    if has_target and has_value and not has_condition and not has_expression:
        return NrmlItemType.VALUE_INITIALIZATION

    # If none of the patterns match, return unknown
    return NrmlItemType.UNKNOWN
