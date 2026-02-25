"""
Shared constants and utilities for the synthesize package.

Contains common data structures and helper functions used across
multiple modules to avoid code duplication.
"""

from typing import Any

import numpy as np

# Dutch translations for feature names used in explanations
FEATURE_LABELS_NL: dict[str, str] = {
    "age": "uw leeftijd",
    "income": "uw toetsingsinkomen",
    "net_worth": "uw vermogen",
    "rent_amount": "uw maandelijkse huur",
    "has_partner": "u een toeslagpartner heeft",
    "has_children": "u kinderen heeft",
    "children_count": "het aantal kinderen",
    "youngest_child_age": "de leeftijd van uw jongste kind",
    "housing_type_rent": "u een huurwoning heeft",
    "is_student": "u student bent",
}


def to_native(obj: Any) -> Any:
    """Recursively convert numpy types to native Python types for YAML serialization."""
    if isinstance(obj, dict):
        return {k: to_native(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_native(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj
