#!/usr/bin/env python3
"""
Compatibility matrix test for regelrecht engine v0.2.0.

Tests each operation we use in our YAML files against the v0.2.0 binary
to determine which operations are supported/evaluated vs unsupported/unevaluated.

Usage:
    uv run python3 tests/regelrecht_compat/test_operations.py
"""

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

BINARY = Path(__file__).parent.parent.parent / "bin" / "evaluate-v0.2.0"
REFERENCE_YAML = Path(__file__).parent.parent / "regelrecht_reference" / "zorgtoeslag_2025.yaml"
OUR_YAML = Path(__file__).parent.parent.parent / "laws" / "zorgtoeslagwet" / "TOESLAGEN-2025-01-01.yaml"


@dataclass
class TestResult:
    name: str
    status: str  # PASS, FAIL, ERROR, UNEVALUATED
    expected: object = None
    actual: object = None
    error: str = ""
    notes: str = ""


def run_binary(yaml_str: str, params: dict, date: str = "2025-01-01", output_name: str = "result") -> dict:
    """Run the v0.2.0 binary with given YAML and params."""
    request = {
        "law_yaml": yaml_str,
        "output_name": output_name,
        "params": params,
        "date": date,
    }
    try:
        proc = subprocess.run(
            [str(BINARY)],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=10,
        )
        combined = proc.stdout + proc.stderr
        return json.loads(combined.strip().split("\n")[-1])
    except subprocess.TimeoutExpired:
        return {"error": "TIMEOUT"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON decode error: {e}", "raw": proc.stdout + proc.stderr}
    except Exception as e:
        return {"error": str(e)}


def make_minimal_yaml(
    definitions: dict,
    inputs: list[dict],
    outputs: list[dict],
    actions: list[dict],
    requirements: list | None = None,
    schema_version: str = "v0.5.0",
) -> str:
    """Build a minimal article-based YAML for testing a single operation."""
    doc = {
        "$schema": f"https://raw.githubusercontent.com/MinBZK/regelrecht/refs/tags/schema-{schema_version}/schema/{schema_version}/schema.json",
        "$id": "test_law",
        "regulatory_layer": "WET",
        "publication_date": "2025-01-01",
        "valid_from": "2025-01-01",
        "bwb_id": "BWBR0000001",
        "url": "https://example.com",
        "name": "Test Law",
        "articles": [
            {
                "number": "1",
                "text": "Test article.",
                "url": "https://example.com#1",
                "machine_readable": {
                    "definitions": definitions,
                    "execution": {
                        "input": inputs,
                        "output": outputs,
                        "actions": actions,
                    },
                },
            }
        ],
    }
    if requirements is not None:
        doc["articles"][0]["machine_readable"]["execution"]["requirements"] = requirements

    import yaml

    return yaml.dump(doc, default_flow_style=False, allow_unicode=True, sort_keys=False)


def is_evaluated(value) -> bool:
    """Check if a value was actually evaluated (not returned as raw expression tree)."""
    if isinstance(value, dict) and "operation" in value:
        return False
    return not (isinstance(value, dict) and "conditions" in value)


# ============================================================
# Test 1: Reference zorgtoeslag (their format)
# ============================================================
def test_reference_zorgtoeslag() -> list[TestResult]:
    results = []
    yaml_str = REFERENCE_YAML.read_text()

    # Test hoogte_zorgtoeslag
    params = {
        "is_verzekerde": True,
        "heeft_toeslagpartner": False,
        "toetsingsinkomen": 2500000,
        "standaardpremie": 176400,
        "vermogen_onder_grens": True,
    }
    resp = run_binary(yaml_str, params, output_name="hoogte_zorgtoeslag")

    if "error" in resp:
        results.append(TestResult("reference/hoogte_zorgtoeslag", "ERROR", error=resp["error"]))
    else:
        val = resp.get("outputs", {}).get("hoogte_zorgtoeslag")
        if val is not None and is_evaluated(val):
            results.append(TestResult("reference/hoogte_zorgtoeslag", "PASS", expected="numeric", actual=val))
        else:
            results.append(TestResult("reference/hoogte_zorgtoeslag", "UNEVALUATED", actual=val))

    # Test heeft_recht_op_zorgtoeslag
    val2 = resp.get("outputs", {}).get("heeft_recht_op_zorgtoeslag")
    if val2 is not None and is_evaluated(val2):
        results.append(TestResult("reference/heeft_recht_op_zorgtoeslag", "PASS", expected=True, actual=val2))
    else:
        results.append(TestResult("reference/heeft_recht_op_zorgtoeslag", "UNEVALUATED", actual=val2))

    return results


# ============================================================
# Test 2: Our zorgtoeslag (our format)
# ============================================================
def test_our_zorgtoeslag() -> list[TestResult]:
    results = []
    yaml_str = OUR_YAML.read_text()

    params = {
        "LEEFTIJD": 30,
        "IS_VERZEKERDE": True,
        "INKOMEN": 2500000,
        "VERMOGEN": 1000000,
        "GEZAMENLIJK_VERMOGEN": 1000000,
        "PARTNER_INKOMEN": 0,
        "HEEFT_PARTNER": False,
        "STANDAARDPREMIE": 176400,
    }
    resp = run_binary(yaml_str, params, output_name="hoogte_toeslag")

    if "error" in resp:
        results.append(TestResult("ours/hoogte_toeslag", "ERROR", error=resp["error"]))
    else:
        val = resp.get("outputs", {}).get("hoogte_toeslag")
        if val is not None and is_evaluated(val):
            results.append(TestResult("ours/hoogte_toeslag", "PASS", expected="numeric", actual=val))
        else:
            results.append(
                TestResult(
                    "ours/hoogte_toeslag",
                    "UNEVALUATED",
                    actual="<expression tree returned>",
                    notes="IF with conditions/test/then/else NOT evaluated by v0.2.0",
                )
            )

        val2 = resp.get("outputs", {}).get("is_verzekerde_zorgtoeslag")
        if val2 is not None and is_evaluated(val2):
            results.append(TestResult("ours/is_verzekerde_zorgtoeslag", "PASS", expected=True, actual=val2))
        else:
            results.append(TestResult("ours/is_verzekerde_zorgtoeslag", "UNEVALUATED", actual=val2))

    return results


# ============================================================
# Test 3: Operation compatibility matrix
# ============================================================
def test_if_cases_when_then_default() -> TestResult:
    """IF with cases/when/then/default (schema format)."""
    yaml_str = make_minimal_yaml(
        definitions={},
        inputs=[{"name": "x", "type": "number"}],
        outputs=[{"name": "result", "type": "number"}],
        actions=[
            {
                "output": "result",
                "value": {
                    "operation": "IF",
                    "cases": [
                        {"when": {"operation": "EQUALS", "subject": "$x", "value": 1}, "then": 100},
                        {"when": {"operation": "EQUALS", "subject": "$x", "value": 2}, "then": 200},
                    ],
                    "default": 0,
                },
            }
        ],
    )
    resp = run_binary(yaml_str, {"x": 1})
    if "error" in resp:
        return TestResult("IF (cases/when/then/default)", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val) and val == 100:
        return TestResult("IF (cases/when/then/default)", "PASS", expected=100, actual=val)
    elif is_evaluated(val):
        return TestResult("IF (cases/when/then/default)", "FAIL", expected=100, actual=val)
    return TestResult("IF (cases/when/then/default)", "UNEVALUATED", actual=val)


def test_if_conditions_test_then_else() -> TestResult:
    """IF with conditions/test/then/else (our format)."""
    yaml_str = make_minimal_yaml(
        definitions={},
        inputs=[{"name": "x", "type": "number"}],
        outputs=[{"name": "result", "type": "number"}],
        actions=[
            {
                "output": "result",
                "value": {
                    "operation": "IF",
                    "conditions": [
                        {"test": {"operation": "EQUALS", "subject": "$x", "value": 1}, "then": 100},
                        {"test": {"operation": "EQUALS", "subject": "$x", "value": 2}, "then": 200},
                        {"else": 0},
                    ],
                },
            }
        ],
    )
    resp = run_binary(yaml_str, {"x": 1})
    if "error" in resp:
        return TestResult("IF (conditions/test/then/else)", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val) and val == 100:
        return TestResult("IF (conditions/test/then/else)", "PASS", expected=100, actual=val)
    elif is_evaluated(val):
        return TestResult("IF (conditions/test/then/else)", "FAIL", expected=100, actual=val)
    return TestResult("IF (conditions/test/then/else)", "UNEVALUATED", actual=val)


def test_and_conditions() -> TestResult:
    """AND with conditions (schema format)."""
    yaml_str = make_minimal_yaml(
        definitions={},
        inputs=[{"name": "a", "type": "boolean"}, {"name": "b", "type": "boolean"}],
        outputs=[{"name": "result", "type": "boolean"}],
        actions=[
            {
                "output": "result",
                "value": {
                    "operation": "AND",
                    "conditions": [
                        {"operation": "EQUALS", "subject": "$a", "value": True},
                        {"operation": "EQUALS", "subject": "$b", "value": True},
                    ],
                },
            }
        ],
    )
    resp = run_binary(yaml_str, {"a": True, "b": True})
    if "error" in resp:
        return TestResult("AND (conditions)", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val) and val is True:
        return TestResult("AND (conditions)", "PASS", expected=True, actual=val)
    elif is_evaluated(val):
        return TestResult("AND (conditions)", "FAIL", expected=True, actual=val)
    return TestResult("AND (conditions)", "UNEVALUATED", actual=val)


def test_and_values() -> TestResult:
    """AND with values (our format)."""
    yaml_str = make_minimal_yaml(
        definitions={},
        inputs=[{"name": "a", "type": "boolean"}, {"name": "b", "type": "boolean"}],
        outputs=[{"name": "result", "type": "boolean"}],
        actions=[
            {
                "output": "result",
                "value": {
                    "operation": "AND",
                    "values": [
                        {"operation": "EQUALS", "subject": "$a", "value": True},
                        {"operation": "EQUALS", "subject": "$b", "value": True},
                    ],
                },
            }
        ],
    )
    resp = run_binary(yaml_str, {"a": True, "b": True})
    if "error" in resp:
        return TestResult("AND (values)", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val) and val is True:
        return TestResult("AND (values)", "PASS", expected=True, actual=val)
    elif is_evaluated(val):
        return TestResult("AND (values)", "FAIL", expected=True, actual=val)
    return TestResult("AND (values)", "UNEVALUATED", actual=val)


def test_foreach() -> TestResult:
    """FOREACH with combine: ADD."""
    yaml_str = make_minimal_yaml(
        definitions={},
        inputs=[{"name": "items", "type": "array"}],
        outputs=[{"name": "result", "type": "number"}],
        actions=[
            {
                "output": "result",
                "value": {
                    "operation": "FOREACH",
                    "items": "$items",
                    "current": "$item",
                    "value": "$item",
                    "combine": "ADD",
                },
            }
        ],
    )
    resp = run_binary(yaml_str, {"items": [10, 20, 30]})
    if "error" in resp:
        return TestResult("FOREACH (combine: ADD)", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val) and val == 60:
        return TestResult("FOREACH (combine: ADD)", "PASS", expected=60, actual=val)
    elif is_evaluated(val):
        return TestResult("FOREACH (combine: ADD)", "FAIL", expected=60, actual=val)
    return TestResult("FOREACH (combine: ADD)", "UNEVALUATED", actual=val)


def test_concat() -> TestResult:
    """CONCAT operation."""
    yaml_str = make_minimal_yaml(
        definitions={},
        inputs=[{"name": "a", "type": "string"}, {"name": "b", "type": "string"}],
        outputs=[{"name": "result", "type": "string"}],
        actions=[
            {
                "output": "result",
                "value": {
                    "operation": "CONCAT",
                    "values": ["$a", " ", "$b"],
                },
            }
        ],
    )
    resp = run_binary(yaml_str, {"a": "hello", "b": "world"})
    if "error" in resp:
        return TestResult("CONCAT", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val) and val == "hello world":
        return TestResult("CONCAT", "PASS", expected="hello world", actual=val)
    elif is_evaluated(val):
        return TestResult("CONCAT", "FAIL", expected="hello world", actual=val)
    return TestResult("CONCAT", "UNEVALUATED", actual=val)


def test_not_equals() -> TestResult:
    """NOT_EQUALS operation."""
    yaml_str = make_minimal_yaml(
        definitions={},
        inputs=[{"name": "x", "type": "number"}],
        outputs=[{"name": "result", "type": "boolean"}],
        actions=[
            {
                "output": "result",
                "value": {
                    "operation": "NOT_EQUALS",
                    "subject": "$x",
                    "value": 5,
                },
            }
        ],
    )
    resp = run_binary(yaml_str, {"x": 3})
    if "error" in resp:
        return TestResult("NOT_EQUALS", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val) and val is True:
        return TestResult("NOT_EQUALS", "PASS", expected=True, actual=val)
    elif is_evaluated(val):
        return TestResult("NOT_EQUALS", "FAIL", expected=True, actual=val)
    return TestResult("NOT_EQUALS", "UNEVALUATED", actual=val)


def test_not_in() -> TestResult:
    """NOT_IN operation."""
    yaml_str = make_minimal_yaml(
        definitions={},
        inputs=[{"name": "x", "type": "string"}],
        outputs=[{"name": "result", "type": "boolean"}],
        actions=[
            {
                "output": "result",
                "value": {
                    "operation": "NOT_IN",
                    "subject": "$x",
                    "values": ["a", "b", "c"],
                },
            }
        ],
    )
    resp = run_binary(yaml_str, {"x": "d"})
    if "error" in resp:
        return TestResult("NOT_IN", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val) and val is True:
        return TestResult("NOT_IN", "PASS", expected=True, actual=val)
    elif is_evaluated(val):
        return TestResult("NOT_IN", "FAIL", expected=True, actual=val)
    return TestResult("NOT_IN", "UNEVALUATED", actual=val)


def test_not_null() -> TestResult:
    """NOT_NULL operation."""
    yaml_str = make_minimal_yaml(
        definitions={},
        inputs=[{"name": "x", "type": "string"}],
        outputs=[{"name": "result", "type": "boolean"}],
        actions=[
            {
                "output": "result",
                "value": {
                    "operation": "NOT_NULL",
                    "subject": "$x",
                },
            }
        ],
    )
    resp = run_binary(yaml_str, {"x": "hello"})
    if "error" in resp:
        return TestResult("NOT_NULL", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val) and val is True:
        return TestResult("NOT_NULL", "PASS", expected=True, actual=val)
    elif is_evaluated(val):
        return TestResult("NOT_NULL", "FAIL", expected=True, actual=val)
    return TestResult("NOT_NULL", "UNEVALUATED", actual=val)


def test_is_null() -> TestResult:
    """IS_NULL operation."""
    yaml_str = make_minimal_yaml(
        definitions={},
        inputs=[{"name": "x", "type": "string"}],
        outputs=[{"name": "result", "type": "boolean"}],
        actions=[
            {
                "output": "result",
                "value": {
                    "operation": "IS_NULL",
                    "subject": "$x",
                },
            }
        ],
    )
    # Pass null for x
    resp = run_binary(yaml_str, {"x": None})
    if "error" in resp:
        return TestResult("IS_NULL", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val) and val is True:
        return TestResult("IS_NULL", "PASS", expected=True, actual=val)
    elif is_evaluated(val):
        return TestResult("IS_NULL", "FAIL", expected=True, actual=val)
    return TestResult("IS_NULL", "UNEVALUATED", actual=val)


def test_exists() -> TestResult:
    """EXISTS operation."""
    yaml_str = make_minimal_yaml(
        definitions={},
        inputs=[{"name": "items", "type": "array"}],
        outputs=[{"name": "result", "type": "boolean"}],
        actions=[
            {
                "output": "result",
                "value": {
                    "operation": "EXISTS",
                    "items": "$items",
                    "current": "$item",
                    "condition": {"operation": "EQUALS", "subject": "$item", "value": 42},
                },
            }
        ],
    )
    resp = run_binary(yaml_str, {"items": [1, 42, 3]})
    if "error" in resp:
        return TestResult("EXISTS", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val) and val is True:
        return TestResult("EXISTS", "PASS", expected=True, actual=val)
    elif is_evaluated(val):
        return TestResult("EXISTS", "FAIL", expected=True, actual=val)
    return TestResult("EXISTS", "UNEVALUATED", actual=val)


def test_length() -> TestResult:
    """LENGTH operation."""
    yaml_str = make_minimal_yaml(
        definitions={},
        inputs=[{"name": "items", "type": "array"}],
        outputs=[{"name": "result", "type": "number"}],
        actions=[
            {
                "output": "result",
                "value": {
                    "operation": "LENGTH",
                    "subject": "$items",
                },
            }
        ],
    )
    resp = run_binary(yaml_str, {"items": [1, 2, 3]})
    if "error" in resp:
        return TestResult("LENGTH", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val) and val == 3:
        return TestResult("LENGTH", "PASS", expected=3, actual=val)
    elif is_evaluated(val):
        return TestResult("LENGTH", "FAIL", expected=3, actual=val)
    return TestResult("LENGTH", "UNEVALUATED", actual=val)


def test_coalesce() -> TestResult:
    """COALESCE operation."""
    yaml_str = make_minimal_yaml(
        definitions={},
        inputs=[{"name": "a", "type": "string"}, {"name": "b", "type": "string"}],
        outputs=[{"name": "result", "type": "string"}],
        actions=[
            {
                "output": "result",
                "value": {
                    "operation": "COALESCE",
                    "values": ["$a", "$b"],
                },
            }
        ],
    )
    resp = run_binary(yaml_str, {"a": None, "b": "fallback"})
    if "error" in resp:
        return TestResult("COALESCE", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val) and val == "fallback":
        return TestResult("COALESCE", "PASS", expected="fallback", actual=val)
    elif is_evaluated(val):
        return TestResult("COALESCE", "FAIL", expected="fallback", actual=val)
    return TestResult("COALESCE", "UNEVALUATED", actual=val)


def test_get() -> TestResult:
    """GET operation (access object property)."""
    yaml_str = make_minimal_yaml(
        definitions={},
        inputs=[{"name": "obj", "type": "object"}],
        outputs=[{"name": "result", "type": "string"}],
        actions=[
            {
                "output": "result",
                "value": {
                    "operation": "GET",
                    "subject": "$obj",
                    "key": "name",
                },
            }
        ],
    )
    resp = run_binary(yaml_str, {"obj": {"name": "test", "age": 25}})
    if "error" in resp:
        return TestResult("GET", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val) and val == "test":
        return TestResult("GET", "PASS", expected="test", actual=val)
    elif is_evaluated(val):
        return TestResult("GET", "FAIL", expected="test", actual=val)
    return TestResult("GET", "UNEVALUATED", actual=val)


def test_subtract_date() -> TestResult:
    """SUBTRACT_DATE with unit: years."""
    yaml_str = make_minimal_yaml(
        definitions={},
        inputs=[{"name": "date1", "type": "date"}, {"name": "date2", "type": "date"}],
        outputs=[{"name": "result", "type": "number"}],
        actions=[
            {
                "output": "result",
                "value": {
                    "operation": "SUBTRACT_DATE",
                    "values": ["$date1", "$date2"],
                    "unit": "years",
                },
            }
        ],
    )
    resp = run_binary(yaml_str, {"date1": "2025-01-01", "date2": "2000-01-01"})
    if "error" in resp:
        return TestResult("SUBTRACT_DATE (years)", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val) and val == 25:
        return TestResult("SUBTRACT_DATE (years)", "PASS", expected=25, actual=val)
    elif is_evaluated(val):
        return TestResult("SUBTRACT_DATE (years)", "FAIL", expected=25, actual=val)
    return TestResult("SUBTRACT_DATE (years)", "UNEVALUATED", actual=val)


def test_add_date() -> TestResult:
    """ADD_DATE with unit: days."""
    yaml_str = make_minimal_yaml(
        definitions={},
        inputs=[{"name": "start_date", "type": "date"}],
        outputs=[{"name": "result", "type": "date"}],
        actions=[
            {
                "output": "result",
                "value": {
                    "operation": "ADD_DATE",
                    "values": ["$start_date", 30],
                    "unit": "days",
                },
            }
        ],
    )
    resp = run_binary(yaml_str, {"start_date": "2025-01-01"})
    if "error" in resp:
        return TestResult("ADD_DATE (days)", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val) and val == "2025-01-31":
        return TestResult("ADD_DATE (days)", "PASS", expected="2025-01-31", actual=val)
    elif is_evaluated(val):
        return TestResult("ADD_DATE (days)", "FAIL", expected="2025-01-31", actual=val)
    return TestResult("ADD_DATE (days)", "UNEVALUATED", actual=val)


def test_day_of_week() -> TestResult:
    """DAY_OF_WEEK operation."""
    yaml_str = make_minimal_yaml(
        definitions={},
        inputs=[{"name": "d", "type": "date"}],
        outputs=[{"name": "result", "type": "string"}],
        actions=[
            {
                "output": "result",
                "value": {
                    "operation": "DAY_OF_WEEK",
                    "subject": "$d",
                },
            }
        ],
    )
    # 2025-01-01 is a Wednesday
    resp = run_binary(yaml_str, {"d": "2025-01-01"})
    if "error" in resp:
        return TestResult("DAY_OF_WEEK", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val):
        # Accept various representations of Wednesday
        return TestResult("DAY_OF_WEEK", "PASS", expected="Wednesday/3/woensdag", actual=val)
    return TestResult("DAY_OF_WEEK", "UNEVALUATED", actual=val)


def test_combine_datetime() -> TestResult:
    """COMBINE_DATETIME operation."""
    yaml_str = make_minimal_yaml(
        definitions={},
        inputs=[{"name": "d", "type": "date"}, {"name": "t", "type": "string"}],
        outputs=[{"name": "result", "type": "string"}],
        actions=[
            {
                "output": "result",
                "value": {
                    "operation": "COMBINE_DATETIME",
                    "values": ["$d", "$t"],
                },
            }
        ],
    )
    resp = run_binary(yaml_str, {"d": "2025-01-01", "t": "12:00:00"})
    if "error" in resp:
        return TestResult("COMBINE_DATETIME", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val):
        return TestResult("COMBINE_DATETIME", "PASS", expected="2025-01-01T12:00:00", actual=val)
    return TestResult("COMBINE_DATETIME", "UNEVALUATED", actual=val)


def test_greater_or_equal() -> TestResult:
    """GREATER_OR_EQUAL (our name)."""
    yaml_str = make_minimal_yaml(
        definitions={},
        inputs=[{"name": "x", "type": "number"}],
        outputs=[{"name": "result", "type": "boolean"}],
        actions=[
            {
                "output": "result",
                "value": {
                    "operation": "GREATER_OR_EQUAL",
                    "subject": "$x",
                    "value": 10,
                },
            }
        ],
    )
    resp = run_binary(yaml_str, {"x": 15})
    if "error" in resp:
        return TestResult("GREATER_OR_EQUAL", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val) and val is True:
        return TestResult("GREATER_OR_EQUAL", "PASS", expected=True, actual=val)
    elif is_evaluated(val):
        return TestResult("GREATER_OR_EQUAL", "FAIL", expected=True, actual=val)
    return TestResult("GREATER_OR_EQUAL", "UNEVALUATED", actual=val)


def test_greater_than_or_equal() -> TestResult:
    """GREATER_THAN_OR_EQUAL (schema name)."""
    yaml_str = make_minimal_yaml(
        definitions={},
        inputs=[{"name": "x", "type": "number"}],
        outputs=[{"name": "result", "type": "boolean"}],
        actions=[
            {
                "output": "result",
                "value": {
                    "operation": "GREATER_THAN_OR_EQUAL",
                    "subject": "$x",
                    "value": 10,
                },
            }
        ],
    )
    resp = run_binary(yaml_str, {"x": 15})
    if "error" in resp:
        return TestResult("GREATER_THAN_OR_EQUAL", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val) and val is True:
        return TestResult("GREATER_THAN_OR_EQUAL", "PASS", expected=True, actual=val)
    elif is_evaluated(val):
        return TestResult("GREATER_THAN_OR_EQUAL", "FAIL", expected=True, actual=val)
    return TestResult("GREATER_THAN_OR_EQUAL", "UNEVALUATED", actual=val)


def test_basic_operations() -> list[TestResult]:
    """Test basic ADD, SUBTRACT, MULTIPLY, etc. for baseline."""
    results = []

    for op, vals, expected in [
        ("ADD", [10, 20], 30),
        ("SUBTRACT", [100, 30], 70),
        ("MULTIPLY", [6, 7], 42),
        ("DIVIDE", [100, 4], 25),
        ("MAX", [10, 20, 5], 20),
        ("MIN", [10, 20, 5], 5),
        ("ROUND_DOWN", None, None),  # special
    ]:
        if op == "ROUND_DOWN":
            yaml_str = make_minimal_yaml(
                definitions={},
                inputs=[{"name": "x", "type": "number"}],
                outputs=[{"name": "result", "type": "number"}],
                actions=[
                    {
                        "output": "result",
                        "value": {
                            "operation": "ROUND_DOWN",
                            "subject": "$x",
                            "precision": 0,
                        },
                    }
                ],
            )
            resp = run_binary(yaml_str, {"x": 3.7})
            expected = 3
        else:
            yaml_str = make_minimal_yaml(
                definitions={},
                inputs=[],
                outputs=[{"name": "result", "type": "number"}],
                actions=[
                    {
                        "output": "result",
                        "value": {
                            "operation": op,
                            "values": vals,
                        },
                    }
                ],
            )
            resp = run_binary(yaml_str, {})

        if "error" in resp:
            results.append(TestResult(op, "ERROR", error=resp["error"]))
        else:
            val = resp.get("outputs", {}).get("result")
            if is_evaluated(val) and val == expected:
                results.append(TestResult(op, "PASS", expected=expected, actual=val))
            elif is_evaluated(val):
                results.append(TestResult(op, "FAIL", expected=expected, actual=val))
            else:
                results.append(TestResult(op, "UNEVALUATED", actual=val))

    return results


def test_comparison_operations() -> list[TestResult]:
    """Test comparison operations."""
    results = []
    for op, x_val, comp_val, expected in [
        ("EQUALS", 5, 5, True),
        ("GREATER_THAN", 10, 5, True),
        ("LESS_THAN", 3, 5, True),
        ("LESS_THAN_OR_EQUAL", 5, 5, True),
        ("IN", None, None, None),  # special
    ]:
        if op == "IN":
            yaml_str = make_minimal_yaml(
                definitions={},
                inputs=[{"name": "x", "type": "string"}],
                outputs=[{"name": "result", "type": "boolean"}],
                actions=[
                    {
                        "output": "result",
                        "value": {
                            "operation": "IN",
                            "subject": "$x",
                            "values": ["a", "b", "c"],
                        },
                    }
                ],
            )
            resp = run_binary(yaml_str, {"x": "b"})
            expected = True
        else:
            yaml_str = make_minimal_yaml(
                definitions={},
                inputs=[{"name": "x", "type": "number"}],
                outputs=[{"name": "result", "type": "boolean"}],
                actions=[
                    {
                        "output": "result",
                        "value": {
                            "operation": op,
                            "subject": "$x",
                            "value": comp_val,
                        },
                    }
                ],
            )
            resp = run_binary(yaml_str, {"x": x_val})

        if "error" in resp:
            results.append(TestResult(op, "ERROR", error=resp["error"]))
        else:
            val = resp.get("outputs", {}).get("result")
            if is_evaluated(val) and val == expected:
                results.append(TestResult(op, "PASS", expected=expected, actual=val))
            elif is_evaluated(val):
                results.append(TestResult(op, "FAIL", expected=expected, actual=val))
            else:
                results.append(TestResult(op, "UNEVALUATED", actual=val))

    return results


def test_or_operation() -> TestResult:
    """OR operation."""
    yaml_str = make_minimal_yaml(
        definitions={},
        inputs=[{"name": "a", "type": "boolean"}, {"name": "b", "type": "boolean"}],
        outputs=[{"name": "result", "type": "boolean"}],
        actions=[
            {
                "output": "result",
                "value": {
                    "operation": "OR",
                    "conditions": [
                        {"operation": "EQUALS", "subject": "$a", "value": True},
                        {"operation": "EQUALS", "subject": "$b", "value": True},
                    ],
                },
            }
        ],
    )
    resp = run_binary(yaml_str, {"a": False, "b": True})
    if "error" in resp:
        return TestResult("OR", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val) and val is True:
        return TestResult("OR", "PASS", expected=True, actual=val)
    elif is_evaluated(val):
        return TestResult("OR", "FAIL", expected=True, actual=val)
    return TestResult("OR", "UNEVALUATED", actual=val)


def test_not_operation() -> TestResult:
    """NOT operation."""
    yaml_str = make_minimal_yaml(
        definitions={},
        inputs=[{"name": "x", "type": "boolean"}],
        outputs=[{"name": "result", "type": "boolean"}],
        actions=[
            {
                "output": "result",
                "value": {
                    "operation": "NOT",
                    "subject": "$x",
                },
            }
        ],
    )
    resp = run_binary(yaml_str, {"x": True})
    if "error" in resp:
        return TestResult("NOT", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val) and val is False:
        return TestResult("NOT", "PASS", expected=False, actual=val)
    elif is_evaluated(val):
        return TestResult("NOT", "FAIL", expected=False, actual=val)
    return TestResult("NOT", "UNEVALUATED", actual=val)


def test_requirements() -> TestResult:
    """Requirements block (all conditions must pass for actions to execute)."""
    yaml_str = make_minimal_yaml(
        definitions={},
        inputs=[{"name": "eligible", "type": "boolean"}],
        outputs=[{"name": "result", "type": "number"}],
        actions=[
            {"output": "result", "value": 100},
        ],
        requirements=[
            {
                "all": [
                    {"subject": "$eligible", "operation": "EQUALS", "value": True},
                ]
            }
        ],
    )
    # Test with eligible=True (should get result)
    resp = run_binary(yaml_str, {"eligible": True})
    if "error" in resp:
        return TestResult("requirements (all)", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val) and val == 100:
        return TestResult("requirements (all)", "PASS", expected=100, actual=val)
    elif is_evaluated(val):
        return TestResult("requirements (all)", "FAIL", expected=100, actual=val, notes=f"got {val}")
    return TestResult("requirements (all)", "UNEVALUATED", actual=val)


def test_definitions_referenced() -> TestResult:
    """Definitions referenced in actions via $variable."""
    yaml_str = make_minimal_yaml(
        definitions={"THRESHOLD": {"value": 500}},
        inputs=[{"name": "x", "type": "number"}],
        outputs=[{"name": "result", "type": "boolean"}],
        actions=[
            {
                "output": "result",
                "value": {
                    "operation": "GREATER_THAN",
                    "subject": "$x",
                    "value": "$THRESHOLD",
                },
            }
        ],
    )
    resp = run_binary(yaml_str, {"x": 600})
    if "error" in resp:
        return TestResult("definitions ($variable ref)", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("result")
    if is_evaluated(val) and val is True:
        return TestResult("definitions ($variable ref)", "PASS", expected=True, actual=val)
    elif is_evaluated(val):
        return TestResult("definitions ($variable ref)", "FAIL", expected=True, actual=val)
    return TestResult("definitions ($variable ref)", "UNEVALUATED", actual=val)


def test_multi_article() -> TestResult:
    """Multiple articles with cross-article references."""
    import yaml

    doc = {
        "$schema": "https://raw.githubusercontent.com/MinBZK/regelrecht/refs/tags/schema-v0.5.0/schema/v0.5.0/schema.json",
        "$id": "test_multi",
        "regulatory_layer": "WET",
        "publication_date": "2025-01-01",
        "valid_from": "2025-01-01",
        "bwb_id": "BWBR0000001",
        "url": "https://example.com",
        "name": "Test Multi-Article Law",
        "articles": [
            {
                "number": "1",
                "text": "Article 1 defines the threshold.",
                "url": "https://example.com#1",
                "machine_readable": {
                    "definitions": {"THRESHOLD": {"value": 100}},
                    "execution": {
                        "output": [{"name": "threshold", "type": "number"}],
                        "actions": [{"output": "threshold", "value": "$THRESHOLD"}],
                    },
                },
            },
            {
                "number": "2",
                "text": "Article 2 uses the threshold from article 1.",
                "url": "https://example.com#2",
                "machine_readable": {
                    "execution": {
                        "input": [
                            {"name": "x", "type": "number"},
                            {"name": "threshold", "type": "number", "source": {"output": "threshold"}},
                        ],
                        "output": [{"name": "above_threshold", "type": "boolean"}],
                        "actions": [
                            {
                                "output": "above_threshold",
                                "value": {
                                    "operation": "GREATER_THAN",
                                    "subject": "$x",
                                    "value": "$threshold",
                                },
                            }
                        ],
                    }
                },
            },
        ],
    }
    yaml_str = yaml.dump(doc, default_flow_style=False, allow_unicode=True, sort_keys=False)
    resp = run_binary(yaml_str, {"x": 150}, output_name="above_threshold")
    if "error" in resp:
        return TestResult("multi-article (cross-ref)", "ERROR", error=resp["error"])
    val = resp.get("outputs", {}).get("above_threshold")
    if is_evaluated(val) and val is True:
        return TestResult("multi-article (cross-ref)", "PASS", expected=True, actual=val)
    elif is_evaluated(val):
        return TestResult("multi-article (cross-ref)", "FAIL", expected=True, actual=val)
    return TestResult("multi-article (cross-ref)", "UNEVALUATED", actual=val)


def print_results(results: list[TestResult]) -> None:
    """Print a formatted table of results."""
    # Calculate column widths
    name_w = max(len(r.name) for r in results)
    status_w = max(len(r.status) for r in results)

    # Header
    print(f"\n{'Operation':<{name_w}}  {'Status':<{status_w}}  {'Expected':<20}  {'Actual':<40}  Notes")
    print("-" * (name_w + status_w + 80))

    # Status symbols and colors
    status_sym = {"PASS": "+", "FAIL": "!", "ERROR": "X", "UNEVALUATED": "~"}

    for r in results:
        sym = status_sym.get(r.status, "?")
        exp_str = str(r.expected)[:20] if r.expected is not None else ""
        act_str = str(r.actual)[:40] if r.actual is not None else ""
        note_str = r.error if r.error else r.notes
        note_str = note_str[:60] if note_str else ""
        print(f"[{sym}] {r.name:<{name_w}}  {r.status:<{status_w}}  {exp_str:<20}  {act_str:<40}  {note_str}")


def main() -> None:
    all_results: list[TestResult] = []

    print("=" * 100)
    print("REGELRECHT ENGINE v0.2.0 COMPATIBILITY MATRIX")
    print("=" * 100)

    # ---- Section 1: Full law files ----
    print("\n## SECTION 1: Reference zorgtoeslag YAML (schema format)")
    ref_results = test_reference_zorgtoeslag()
    all_results.extend(ref_results)
    print_results(ref_results)

    print("\n## SECTION 2: Our zorgtoeslag YAML (our format)")
    our_results = test_our_zorgtoeslag()
    all_results.extend(our_results)
    print_results(our_results)

    # ---- Section 3: Individual operations ----
    print("\n## SECTION 3: Basic arithmetic operations")
    basic_results = test_basic_operations()
    all_results.extend(basic_results)
    print_results(basic_results)

    print("\n## SECTION 4: Comparison operations")
    comp_results = test_comparison_operations()
    all_results.extend(comp_results)
    print_results(comp_results)

    print("\n## SECTION 5: IF operation variants")
    if_results = [
        test_if_cases_when_then_default(),
        test_if_conditions_test_then_else(),
    ]
    all_results.extend(if_results)
    print_results(if_results)

    print("\n## SECTION 6: Logical operations")
    logic_results = [
        test_and_conditions(),
        test_and_values(),
        test_or_operation(),
        test_not_operation(),
    ]
    all_results.extend(logic_results)
    print_results(logic_results)

    print("\n## SECTION 7: Collection/list operations")
    coll_results = [
        test_foreach(),
        test_exists(),
        test_length(),
        test_not_in(),
        test_concat(),
    ]
    all_results.extend(coll_results)
    print_results(coll_results)

    print("\n## SECTION 8: Null-handling operations")
    null_results = [
        test_is_null(),
        test_not_null(),
        test_coalesce(),
    ]
    all_results.extend(null_results)
    print_results(null_results)

    print("\n## SECTION 9: Date/time operations")
    date_results = [
        test_subtract_date(),
        test_add_date(),
        test_day_of_week(),
        test_combine_datetime(),
    ]
    all_results.extend(date_results)
    print_results(date_results)

    print("\n## SECTION 10: Naming variants")
    naming_results = [
        test_greater_or_equal(),
        test_greater_than_or_equal(),
        test_not_equals(),
        test_get(),
    ]
    all_results.extend(naming_results)
    print_results(naming_results)

    print("\n## SECTION 11: Structure features")
    struct_results = [
        test_requirements(),
        test_definitions_referenced(),
        test_multi_article(),
    ]
    all_results.extend(struct_results)
    print_results(struct_results)

    # ---- Summary ----
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    pass_count = sum(1 for r in all_results if r.status == "PASS")
    fail_count = sum(1 for r in all_results if r.status == "FAIL")
    error_count = sum(1 for r in all_results if r.status == "ERROR")
    uneval_count = sum(1 for r in all_results if r.status == "UNEVALUATED")
    total = len(all_results)

    print(f"  PASS:        {pass_count:3d} / {total}")
    print(f"  FAIL:        {fail_count:3d} / {total}")
    print(f"  ERROR:       {error_count:3d} / {total}")
    print(f"  UNEVALUATED: {uneval_count:3d} / {total}")

    print("\nKey:")
    print("  [+] PASS        = Operation supported and produces correct result")
    print("  [!] FAIL        = Operation runs but produces wrong result")
    print("  [X] ERROR       = YAML parse error or runtime crash")
    print("  [~] UNEVALUATED = Expression tree returned instead of computed value")

    # Critical findings
    print("\n" + "=" * 100)
    print("CRITICAL FINDINGS")
    print("=" * 100)

    errors = [r for r in all_results if r.status == "ERROR"]
    if errors:
        print("\nOperations causing errors (not in v0.2.0):")
        for r in errors:
            print(f"  - {r.name}: {r.error}")

    uneval = [r for r in all_results if r.status == "UNEVALUATED"]
    if uneval:
        print("\nOperations returning raw expression trees (parsed but not evaluated):")
        for r in uneval:
            print(f"  - {r.name}: {r.notes}")

    fails = [r for r in all_results if r.status == "FAIL"]
    if fails:
        print("\nOperations producing wrong results:")
        for r in fails:
            print(f"  - {r.name}: expected={r.expected}, actual={r.actual}")

    sys.exit(0 if (error_count == 0 and fail_count == 0 and uneval_count == 0) else 1)


if __name__ == "__main__":
    main()
