from typing import Any

import pytest


@pytest.fixture
def simple_text_fact() -> dict[str, Any]:
    """Simple text parameter fact like the Nationaliteit example"""
    return {
        "3c8e2a5f-1b6d-4e9c-7f2d-a5c3b6e1d9f4": {
            "name": {"nl": "Nationaliteit", "en": "Nationality"},
            "items": {
                "9d2c5b1e-7f3a-4d6c-b2e8-f5a1c9d3b7e6": {
                    "name": {"nl": "Nationaliteit definitie", "en": "Nationality definition"},
                    "versions": [{"validFrom": "2020-01-01", "type": "text"}],
                }
            },
        }
    }


@pytest.fixture
def enumeration_fact() -> dict[str, Any]:
    """Enumeration fact with predefined values (should not be parameter)"""
    return {
        "8c3f1d6a-5b9e-4f2c-d7b1-e3a6f4c8d5b2": {
            "name": {"nl": "Nederlandse nationaliteiten", "en": "Dutch nationalities"},
            "items": {
                "2d9f5c1b-7e3a-4b6d-c8f2-1a5e9d3b7f4c": {
                    "name": {"nl": "Nederlandse nationaliteiten definitie", "en": "Dutch nationalities definition"},
                    "versions": [{"validFrom": "2020-01-01", "type": "enumeration", "values": ["NEDERLANDS"]}],
                }
            },
        }
    }


@pytest.fixture
def expression_fact() -> dict[str, Any]:
    """Fact with expression (should not be parameter)"""
    return {
        "a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d": {
            "name": {"nl": "heeft Nederlandse nationaliteit", "en": "has Dutch nationality"},
            "items": {
                "b2c3d4e5-6f7a-8b9c-0d1e-2f3a4b5c6d7e": {
                    "name": {
                        "nl": "heeft Nederlandse nationaliteit definitie",
                        "en": "has Dutch nationality definition",
                    },
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
                                    "left": [
                                        {
                                            "$ref": "#/facts/3c8e2a5f-1b6d-4e9c-7f2d-a5c3b6e1d9f4/items/9d2c5b1e-7f3a-4d6c-b2e8-f5a1c9d3b7e6"
                                        }
                                    ],
                                    "right": [
                                        {
                                            "$ref": "#/facts/8c3f1d6a-5b9e-4f2c-d7b1-e3a6f4c8d5b2/items/2d9f5c1b-7e3a-4b6d-c8f2-1a5e9d3b7f4c"
                                        }
                                    ],
                                },
                                "then": {"value": True},
                                "else": {"value": False},
                            },
                        }
                    ],
                }
            },
        }
    }


@pytest.fixture
def target_fact() -> dict[str, Any]:
    """Fact that is used as target (should not be parameter)"""
    return {
        "f1e2d3c4-5b6a-7c8d-9e0f-1a2b3c4d5e6f": {
            "name": {"nl": "BRP resultaat", "en": "BRP result"},
            "items": {
                "a2f3e4d5-6c7b-8d9e-0f1a-2b3c4d5e6f78": {
                    "name": {"nl": "Nederlandse nationaliteit resultaat", "en": "Dutch nationality result"},
                    "versions": [{"validFrom": "2020-01-01", "type": "boolean"}],
                }
            },
        }
    }


@pytest.fixture
def brp_nationaliteit_facts(simple_text_fact, enumeration_fact, expression_fact, target_fact) -> dict[str, Any]:
    """Complete brp_nationaliteit facts structure"""
    facts = {}
    facts.update(simple_text_fact)
    facts.update(enumeration_fact)
    facts.update(expression_fact)
    facts.update(target_fact)
    return facts
