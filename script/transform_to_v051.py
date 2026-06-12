#!/usr/bin/env python3
"""Transform law YAML files from custom dialect to regelrecht v0.5.1 / v0.2.0 engine dialect.

Applies the following transformations recursively:
1.  IF: conditions/test/else -> cases/when/default
2.  AND/OR: values -> conditions
3.  GREATER_OR_EQUAL -> GREATER_THAN_OR_EQUAL
4.  LESS_OR_EQUAL -> LESS_THAN_OR_EQUAL
5.  NOT_NULL -> NOT + IS_NULL
6.  NOT_EQUALS -> NOT + EQUALS
7.  EXISTS -> NOT + IS_NULL
8.  SUBTRACT_DATE (unit: years) -> AGE
9.  ADD_DATE -> DATE_ADD
10. DAY_OF_WEEK: subject -> date
11. COALESCE -> IF + IS_NULL chain
12. FOREACH/CONCAT/LENGTH/GET/COMBINE_DATETIME: kept as-is (custom extensions)

Usage:
    uv run python script/transform_to_v051.py
"""

import copy
import sys
from collections import Counter
from pathlib import Path

import yaml


class TransformStats:
    """Track transformation counts per file and globally."""

    def __init__(self) -> None:
        self.per_file: dict[str, Counter] = {}
        self.global_counts: Counter = Counter()
        self.current_file: str = ""
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def set_file(self, path: str) -> None:
        self.current_file = path
        if path not in self.per_file:
            self.per_file[path] = Counter()

    def record(self, transform_name: str) -> None:
        self.per_file[self.current_file][transform_name] += 1
        self.global_counts[transform_name] += 1

    def warn(self, msg: str) -> None:
        self.warnings.append(f"  {self.current_file}: {msg}")

    def error(self, msg: str) -> None:
        self.errors.append(f"  {self.current_file}: {msg}")


stats = TransformStats()


def transform_if(node: dict) -> dict:
    """Transform IF operation from conditions/test/else to cases/when/default."""
    if node.get("operation") != "IF":
        return node
    if "conditions" not in node:
        return node
    # Already transformed (has 'cases')
    if "cases" in node:
        return node

    conditions = node["conditions"]
    cases = []
    default = None

    for cond in conditions:
        if isinstance(cond, dict):
            if "test" in cond and "then" in cond:
                test_val = cond["test"]
                then_val = cond["then"]
                # If 'test' is a dict with operation, it's the when clause
                # If 'test' is a scalar, wrap it... but in practice test is always an operation dict
                case = {"when": test_val, "then": then_val}
                cases.append(case)
                stats.record("IF: test->when")
            elif "else" in cond:
                default = cond["else"]
                stats.record("IF: else->default")

    new_node = {}
    # Preserve all keys except conditions
    for k, v in node.items():
        if k == "conditions":
            continue
        new_node[k] = v

    new_node["cases"] = cases
    if default is not None:
        new_node["default"] = default

    return new_node


def transform_and_or(node: dict) -> dict:
    """Transform AND/OR: rename 'values' to 'conditions'."""
    op = node.get("operation")
    if op not in ("AND", "OR"):
        return node
    if "values" not in node:
        return node
    # Already has conditions
    if "conditions" in node:
        return node

    new_node = {}
    for k, v in node.items():
        if k == "values":
            new_node["conditions"] = v
            stats.record(f"{op}: values->conditions")
        else:
            new_node[k] = v
    return new_node


def transform_operation_rename(node: dict) -> dict:
    """Rename operations: GREATER_OR_EQUAL, LESS_OR_EQUAL."""
    op = node.get("operation")
    renames = {
        "GREATER_OR_EQUAL": "GREATER_THAN_OR_EQUAL",
        "LESS_OR_EQUAL": "LESS_THAN_OR_EQUAL",
    }
    if op in renames:
        new_node = dict(node)
        new_node["operation"] = renames[op]
        stats.record(f"rename: {op}->{renames[op]}")
        return new_node
    return node


def transform_not_null(node: dict) -> dict:
    """Transform NOT_NULL -> NOT + IS_NULL."""
    if node.get("operation") != "NOT_NULL":
        return node

    subject = node.get("subject")
    new_node = {"operation": "NOT", "value": {"operation": "IS_NULL", "subject": subject}}
    # Preserve legal_basis if present
    if "legal_basis" in node:
        new_node["legal_basis"] = node["legal_basis"]
    stats.record("NOT_NULL->NOT+IS_NULL")
    return new_node


def transform_not_equals(node: dict) -> dict:
    """Transform NOT_EQUALS -> NOT + EQUALS."""
    if node.get("operation") != "NOT_EQUALS":
        return node

    # Handle both subject/value form and values form
    if "subject" in node and "value" in node:
        inner = {"operation": "EQUALS", "subject": node["subject"], "value": node["value"]}
    elif "values" in node:
        inner = {"operation": "EQUALS", "values": node["values"]}
    else:
        stats.warn(f"NOT_EQUALS with unexpected structure: {list(node.keys())}")
        return node

    new_node = {"operation": "NOT", "value": inner}
    if "legal_basis" in node:
        new_node["legal_basis"] = node["legal_basis"]
    stats.record("NOT_EQUALS->NOT+EQUALS")
    return new_node


def transform_exists(node: dict) -> dict:
    """Transform EXISTS -> NOT + IS_NULL."""
    if node.get("operation") != "EXISTS":
        return node

    subject = node.get("subject")
    new_node = {"operation": "NOT", "value": {"operation": "IS_NULL", "subject": subject}}
    if "legal_basis" in node:
        new_node["legal_basis"] = node["legal_basis"]
    stats.record("EXISTS->NOT+IS_NULL")
    return new_node


def transform_subtract_date(node: dict) -> dict:
    """Transform SUBTRACT_DATE (unit: years) -> AGE."""
    if node.get("operation") != "SUBTRACT_DATE":
        return node

    unit = node.get("unit")
    values = node.get("values", [])

    if unit == "years" and len(values) == 2:
        new_node = {
            "operation": "AGE",
            "reference_date": values[0],
            "date_of_birth": values[1],
        }
        if "legal_basis" in node:
            new_node["legal_basis"] = node["legal_basis"]
        stats.record("SUBTRACT_DATE(years)->AGE")
        return new_node
    else:
        # Keep as-is for non-years units, record a warning
        stats.warn(f"SUBTRACT_DATE with unit={unit} kept as-is (not years)")
        stats.record("SUBTRACT_DATE(other): kept as-is")
        return node


def transform_add_date(node: dict) -> dict:
    """Transform ADD_DATE -> DATE_ADD."""
    if node.get("operation") != "ADD_DATE":
        return node

    unit = node.get("unit", "years")
    values = node.get("values", [])

    if len(values) != 2:
        stats.warn(f"ADD_DATE with {len(values)} values (expected 2), kept as-is")
        return node

    new_node = {
        "operation": "DATE_ADD",
        "date": values[0],
        unit: values[1],  # years, months, weeks, or days
    }
    if "legal_basis" in node:
        new_node["legal_basis"] = node["legal_basis"]
    stats.record(f"ADD_DATE->DATE_ADD(unit={unit})")
    return new_node


def transform_day_of_week(node: dict) -> dict:
    """Transform DAY_OF_WEEK: subject -> date."""
    if node.get("operation") != "DAY_OF_WEEK":
        return node
    if "subject" not in node:
        return node
    # Already has 'date'
    if "date" in node:
        return node

    new_node = {}
    for k, v in node.items():
        if k == "subject":
            new_node["date"] = v
            stats.record("DAY_OF_WEEK: subject->date")
        else:
            new_node[k] = v
    return new_node


def transform_coalesce(node: dict) -> dict:
    """Transform COALESCE -> IF + IS_NULL chain."""
    if node.get("operation") != "COALESCE":
        return node

    values = node.get("values", [])
    if len(values) < 2:
        stats.warn(f"COALESCE with {len(values)} values, kept as-is")
        return node

    legal_basis = node.get("legal_basis")

    def build_coalesce_if(vals: list) -> dict:
        if len(vals) == 2:
            result: dict = {
                "operation": "IF",
                "cases": [
                    {
                        "when": {"operation": "NOT", "value": {"operation": "IS_NULL", "subject": vals[0]}},
                        "then": vals[0],
                    }
                ],
                "default": vals[1],
            }
            return result
        else:
            # Nested: IF first is not null, use it, else recurse
            result = {
                "operation": "IF",
                "cases": [
                    {
                        "when": {"operation": "NOT", "value": {"operation": "IS_NULL", "subject": vals[0]}},
                        "then": vals[0],
                    }
                ],
                "default": build_coalesce_if(vals[1:]),
            }
            return result

    new_node = build_coalesce_if(values)
    if legal_basis:
        new_node["legal_basis"] = legal_basis
    stats.record("COALESCE->IF+IS_NULL")
    return new_node


def apply_transforms(node: dict) -> dict:
    """Apply all operation-level transforms to a single dict node."""
    if "operation" not in node:
        return node

    # Apply transforms in order
    node = transform_if(node)
    node = transform_and_or(node)
    node = transform_operation_rename(node)
    node = transform_not_null(node)
    node = transform_not_equals(node)
    node = transform_exists(node)
    node = transform_subtract_date(node)
    node = transform_add_date(node)
    node = transform_day_of_week(node)
    node = transform_coalesce(node)

    return node


def transform_recursive(obj):
    """Recursively walk the YAML structure and apply transforms."""
    if isinstance(obj, dict):
        # First, recursively transform all children
        transformed = {}
        for k, v in obj.items():
            transformed[k] = transform_recursive(v)
        # Then apply operation-level transforms to this dict
        if "operation" in transformed:
            transformed = apply_transforms(transformed)
        return transformed
    elif isinstance(obj, list):
        return [transform_recursive(item) for item in obj]
    else:
        return obj


def transform_requirements(requirements: list) -> list:
    """Transform requirement blocks (which may have inline operations)."""
    # Requirements are a list of dicts. Each may be:
    # - An operation dict (has 'operation' key)
    # - An 'all' block: {'all': [...list of requirements...]}
    # - An 'or' block: {'or': [...list of requirements...]}
    # - A bare comparison: {'subject': ..., 'operation': ..., 'value': ...}
    # All of these get recursively transformed.
    return [transform_recursive(req) for req in requirements]


def transform_file(file_path: Path) -> bool:
    """Transform a single YAML file. Returns True if changes were made."""
    stats.set_file(str(file_path))

    with open(file_path) as f:
        original_content = f.read()

    try:
        data = yaml.safe_load(original_content)
    except yaml.YAMLError as e:
        stats.error(f"YAML parse error: {e}")
        return False

    if not isinstance(data, dict):
        stats.warn("Not a dict, skipping")
        return False

    # Deep copy to compare later
    original_data = copy.deepcopy(data)

    # Transform the entire document recursively
    data = transform_recursive(data)

    # Check if anything changed
    if data == original_data:
        return False

    # Write back with clean formatting
    with open(file_path, "w") as f:
        yaml.dump(
            data,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=120,
        )

    return True


def setup_yaml_representer() -> None:
    """Configure YAML dumper for clean output."""

    # Represent None as 'null' (not '')
    def represent_none(dumper, _):
        return dumper.represent_scalar("tag:yaml.org,2002:null", "null")

    yaml.add_representer(type(None), represent_none)

    # Use literal block style for long strings (article text)
    def represent_str(dumper, data):
        if "\n" in data:
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        if len(data) > 120:
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)

    yaml.add_representer(str, represent_str)


def main() -> None:
    base_dir = Path("laws")
    if not base_dir.exists():
        print("Error: 'laws' directory not found. Run from the project root.")
        sys.exit(1)

    setup_yaml_representer()

    yaml_files = sorted(list(base_dir.rglob("*.yaml")) + list(base_dir.rglob("*.yml")))
    print(f"Found {len(yaml_files)} YAML files in laws/\n")

    changed_files = 0
    unchanged_files = 0

    for file_path in yaml_files:
        was_changed = transform_file(file_path)
        if was_changed:
            changed_files += 1
            file_stats = stats.per_file[str(file_path)]
            changes_summary = ", ".join(f"{k}={v}" for k, v in sorted(file_stats.items()))
            print(f"  CHANGED: {file_path} ({changes_summary})")
        else:
            unchanged_files += 1

    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY: {changed_files} files changed, {unchanged_files} files unchanged")
    print(f"Total YAML files: {len(yaml_files)}")

    if stats.global_counts:
        print(f"\nTransformation counts:")
        for name, count in sorted(stats.global_counts.items(), key=lambda x: -x[1]):
            print(f"  {name}: {count}")

    if stats.warnings:
        print(f"\nWarnings ({len(stats.warnings)}):")
        for w in stats.warnings:
            print(w)

    if stats.errors:
        print(f"\nErrors ({len(stats.errors)}):")
        for e in stats.errors:
            print(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
