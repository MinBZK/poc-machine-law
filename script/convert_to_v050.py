#!/usr/bin/env python3
"""Convert law YAML files from v0.1.x format to v0.5.0 article-based format.

Usage:
    uv run python script/convert_to_v050.py laws/                     # convert all
    uv run python script/convert_to_v050.py laws/zorgtoeslagwet/      # convert directory
    uv run python script/convert_to_v050.py laws/zorgtoeslagwet/TOESLAGEN-2025-01-01.yaml  # single file
    uv run python script/convert_to_v050.py laws/ --dry-run           # preview only
    uv run python script/convert_to_v050.py laws/ --output-dir out/   # write to separate dir
    uv run python script/convert_to_v050.py laws/ --validate          # validate against schema
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

V050_SCHEMA_URL = "https://raw.githubusercontent.com/MinBZK/regelrecht/refs/heads/main/schema/v0.5.0/schema.json"

LAW_TYPE_TO_REGULATORY_LAYER = {
    "FORMELE_WET": "WET",
    "GEMEENTELIJKE_VERORDENING": "GEMEENTELIJKE_VERORDENING",
    "PROVINCIALE_VERORDENING": "PROVINCIALE_VERORDENING",
    "AMVB": "AMVB",
    "MINISTERIELE_REGELING": "MINISTERIELE_REGELING",
    "BELEIDSREGEL": "BELEIDSREGEL",
}

# Don't decompose NOT_EQUALS etc. - our engines understand them natively
NEGATED_OPS = {}

# Old comparison aliases that need renaming
# Don't rename operations - keep originals that our engines understand
OP_RENAMES = {}


def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def dump_yaml(data: dict) -> str:
    return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)


def is_old_format(data: dict) -> bool:
    """Check if a YAML file is in the old v0.1.x format."""
    if not isinstance(data, dict):
        return False
    # Already v0.5.0 - has articles
    if "articles" in data:
        return False
    # Already v0.5.0 - $schema points to v0.5.0
    schema = data.get("$schema", "")
    if isinstance(schema, str) and "v0.5.0" in schema:
        return False
    # Old format has $id pointing to schema URL and a `law` field,
    # or uses schema_version with a `law` field
    if "law" not in data:
        return False
    id_val = data.get("$id", "")
    if isinstance(id_val, str) and "schema" in id_val.lower():
        return True
    if "schema_version" in data:
        return True
    # Also detect files with law + properties (the classic v0.1.x structure)
    if "properties" in data:
        return True
    return False


def convert_service_reference(input_field: dict) -> dict:
    """Convert old service_reference to new source format.

    Preserves 'service' field so the engine can resolve cross-law references
    without needing to look up the service from the law name.
    """
    sref = input_field.get("service_reference", {})
    if not sref:
        return {}

    source: dict = {}
    law = sref.get("law")
    if law:
        source["regulation"] = law
    field = sref.get("field")
    if field:
        source["output"] = field
    # Preserve service for engine resolution
    service = sref.get("service")
    if service:
        source["service"] = service

    # Convert parameters
    params = sref.get("parameters")
    if params and isinstance(params, list):
        source["parameters"] = {}
        for p in params:
            name = p.get("name", "")
            ref = p.get("reference", p.get("value", ""))
            source["parameters"][name] = ref
    elif not params:
        # Infer BSN parameter from the parent if the law uses BSN
        pass

    return source


def convert_source_reference(source_field: dict) -> dict:
    """Convert old source_reference to new source format for source-type fields.

    Preserves table lookup markers (table, select_on, fields, source_type) so the
    engine can distinguish table lookups from cross-law references.
    """
    sref = source_field.get("source_reference", {})
    if not sref:
        return {}

    # Preserve the original source_reference structure as-is in the source block
    # This allows the engine to detect it's a table lookup (not a cross-law ref)
    source: dict = {}
    for key in ("table", "field", "fields", "select_on", "source_type"):
        if key in sref:
            source[key] = sref[key]

    return source


def transform_operation(node: dict | list | str | int | float | bool | None) -> dict | list | str | int | float | bool | None:
    """Recursively transform operations from old format to new format.

    Handles:
    - IF conditions → cases/default
    - NOT_EQUALS → NOT + EQUALS
    - NOT_NULL → NOT + IS_NULL
    - NOT_IN → NOT + IN
    - GREATER_OR_EQUAL → GREATER_THAN_OR_EQUAL
    - LESS_OR_EQUAL → LESS_THAN_OR_EQUAL
    - Strip legal_basis from within operations (keep at action level only)
    """
    if node is None or isinstance(node, (str, int, float, bool)):
        return node

    if isinstance(node, list):
        return [transform_operation(item) for item in node]

    if not isinstance(node, dict):
        return node

    op = node.get("operation")

    if op is None:
        # Not an operation node, just recurse into known keys
        result = {}
        for k, v in node.items():
            if k == "legal_basis":
                continue  # Strip legal_basis from nested operations
            result[k] = transform_operation(v)
        return result

    # Rename operations
    if op in OP_RENAMES:
        op = OP_RENAMES[op]

    # Handle negated operations
    if op in NEGATED_OPS:
        inner_op = NEGATED_OPS[op]
        inner = {"operation": inner_op}
        if "subject" in node:
            inner["subject"] = transform_operation(node["subject"])
        if "value" in node:
            inner["value"] = transform_operation(node["value"])
        if "values" in node:
            inner["values"] = transform_operation(node["values"])
        return {"operation": "NOT", "value": inner}

    # Handle IS_NULL (keep as-is but might need wrapping)
    if op == "IS_NULL":
        result = {"operation": "IS_NULL"}
        if "subject" in node:
            result["subject"] = transform_operation(node["subject"])
        if "value" in node:
            result["value"] = transform_operation(node["value"])
        return result

    # Keep IF conditions in original format (our engines understand test/then/else)
    # The v0.5.0 cases/when/then/default transformation will happen when engines are updated

    # Handle new-style IF (already has cases) - just recurse
    if op == "IF" and "cases" in node:
        result = {"operation": "IF"}
        result["cases"] = []
        for case in node["cases"]:
            new_case = {}
            if "when" in case:
                new_case["when"] = transform_operation(case["when"])
            if "then" in case:
                new_case["then"] = transform_operation(case["then"])
            result["cases"].append(new_case)
        if "default" in node:
            result["default"] = transform_operation(node["default"])
        return result

    # Handle FOREACH (pass through, transform children)
    if op == "FOREACH":
        result = {"operation": "FOREACH"}
        if "subject" in node:
            result["subject"] = transform_operation(node["subject"])
        if "where" in node:
            result["where"] = transform_operation(node["where"])
        if "value" in node:
            result["value"] = transform_operation(node["value"])
        if "select" in node:
            result["select"] = transform_operation(node["select"])
        if "combine" in node:
            result["combine"] = node["combine"]
        if "as" in node:
            result["as"] = node["as"]
        return result

    # Comparison operations that use `values: [a, b]` instead of subject/value
    COMPARISON_OPS = {
        "EQUALS", "GREATER_THAN", "LESS_THAN", "GREATER_OR_EQUAL",
        "LESS_OR_EQUAL",
    }
    if op in COMPARISON_OPS and "values" in node and "subject" not in node:
        vals = node["values"]
        if isinstance(vals, list) and len(vals) == 2:
            result = {"operation": op}
            result["subject"] = transform_operation(vals[0])
            result["value"] = transform_operation(vals[1])
            return result

    # AND/OR: keep using `values` key (our engines expect it)
    if op in ("AND", "OR"):
        result = {"operation": op}
        items = node.get("values") or node.get("conditions", [])
        result["values"] = [transform_operation(item) for item in items]
        return result

    # General operation: recurse into ALL fields (except operation and legal_basis)
    result = {"operation": op}
    skip_keys = {"operation", "legal_basis"}
    for key, val in node.items():
        if key in skip_keys:
            continue
        result[key] = transform_operation(val)

    return result


def transform_if_conditions(node: dict) -> dict:
    """Transform old IF conditions format to new cases/default format.

    Old:
      conditions:
        - test: {subject: $X, operation: EQUALS, value: true}
          then: 100
        - test: {subject: $Y, operation: EQUALS, value: false}
          then: 200
        - else: 0

    New:
      cases:
        - when: {operation: EQUALS, subject: $X, value: true}
          then: 100
        - when: {operation: EQUALS, subject: $Y, value: false}
          then: 200
      default: 0
    """
    conditions = node.get("conditions", [])
    cases = []
    default = None

    for cond in conditions:
        if "test" in cond:
            test = cond["test"]
            when = transform_operation(test)
            then = transform_operation(cond.get("then"))
            cases.append({"when": when, "then": then})
        elif "else" in cond:
            default = transform_operation(cond["else"])

    result: dict = {"operation": "IF", "cases": cases}
    if default is not None:
        result["default"] = default
    return result


def transform_action(action: dict) -> dict:
    """Transform a single action from old to new format.

    In old format, actions have operation/values/subject/value at the action root.
    In v0.5.0, actions have output + value (which wraps the operation).
    """
    result: dict = {"output": action["output"]}

    if "value" in action and "operation" not in action:
        # Direct value assignment
        val = action["value"]
        if isinstance(val, list):
            # Keep list values as-is (our engines handle raw lists)
            result["value"] = [transform_operation(v) for v in val]
        else:
            result["value"] = transform_operation(val)
    elif "operation" in action:
        # Build a synthetic operation node from ALL action fields except output/legal_basis
        op_node: dict = {}
        skip_keys = {"output", "legal_basis"}
        for key, val in action.items():
            if key not in skip_keys:
                op_node[key] = val
        result["value"] = transform_operation(op_node)
    elif "subject" in action:
        # Actions with only output + subject (e.g., subject: "$actieve_curatele.bsn_curandus")
        # are direct field extractions. Preserve the subject as the value.
        result["value"] = transform_operation(action["subject"])

    # Keep legal_basis at action level if present
    if "legal_basis" in action:
        result["legal_basis"] = action["legal_basis"]

    return result


def transform_requirements_to_actions(requirements: list) -> list[dict]:
    """Convert old requirements block into an action that computes a boolean guard.

    Requirements in old format can be:
    1. Wrapped in all/any blocks: [{all: [...conditions...]}, ...]
    2. Bare operation list: [{operation: EXISTS, ...}, {operation: EQUALS, ...}]
    We convert these to AND/OR operations that produce a _voldoet_aan_voorwaarden output.
    """
    actions = []
    bare_ops = []
    for req in requirements:
        if "all" in req:
            action_value = transform_requirement_list(req["all"], "AND")
            actions.append({"output": "_voldoet_aan_voorwaarden", "value": action_value})
        elif "any" in req:
            action_value = transform_requirement_list(req["any"], "OR")
            actions.append({"output": "_voldoet_aan_voorwaarden", "value": action_value})
        elif "operation" in req:
            # Bare operation (not wrapped in all/any)
            bare_ops.append(req)
    # If there were bare operations, wrap them in an AND
    if bare_ops:
        if len(bare_ops) == 1:
            action_value = transform_operation(bare_ops[0])
        else:
            action_value = transform_requirement_list(bare_ops, "AND")
        actions.append({"output": "_voldoet_aan_voorwaarden", "value": action_value})
    return actions


def transform_requirement_list(items: list, logical_op: str) -> dict:
    """Convert a list of requirement conditions into a logical operation."""
    conditions = []
    for item in items:
        if "all" in item:
            conditions.append(transform_requirement_list(item["all"], "AND"))
        elif "any" in item:
            conditions.append(transform_requirement_list(item["any"], "OR"))
        elif "or" in item:
            conditions.append(transform_requirement_list(item["or"], "OR"))
        elif "operation" in item:
            conditions.append(transform_operation(item))
        elif "subject" in item:
            # Simple comparison - delegate to transform_operation
            conditions.append(transform_operation(item))

    return {"operation": logical_op, "conditions": conditions}


def transform_input_field(field: dict) -> dict:
    """Transform an input field from old to new format."""
    result: dict = {"name": field["name"], "type": field["type"]}

    if "type_spec" in field:
        result["type_spec"] = field["type_spec"]

    if field.get("required"):
        result["required"] = True

    # Convert service_reference to source
    if "service_reference" in field:
        source = convert_service_reference(field)
        if source:
            result["source"] = source
    elif "source_reference" in field:
        # Preserve source_reference as-is (table lookups, not cross-law calls)
        sref = field["source_reference"]
        new_sref = dict(sref)
        if "select_on" in new_sref:
            new_select_on = []
            for sel in new_sref["select_on"]:
                new_sel = dict(sel)
                pass  # Keep original casing
                new_select_on.append(new_sel)
            new_sref["select_on"] = new_select_on
        result["source_reference"] = new_sref
    elif "source" in field:
        result["source"] = field["source"]

    if "temporal" in field:
        result["temporal"] = field["temporal"]

    return result


def transform_parameter_field(field: dict) -> dict:
    """Transform a parameter field from old to new format."""
    result: dict = {"name": field["name"], "type": field["type"]}
    if field.get("required"):
        result["required"] = True
    if "type_spec" in field:
        result["type_spec"] = field["type_spec"]
    return result


def transform_output_field(field: dict) -> dict:
    """Transform an output field from old to new format."""
    result: dict = {"name": field["name"], "type": field["type"]}
    if "type_spec" in field:
        result["type_spec"] = field["type_spec"]
    return result


def transform_source_to_input(source_field: dict) -> dict:
    """Convert old source fields to input fields with source reference.

    Source fields (from properties.sources) are table lookups, NOT cross-law references.
    We preserve them as source_reference to avoid confusion with service_references
    which are actual cross-law calls.
    """
    result: dict = {
        "name": source_field["name"],
        "type": source_field.get("type", "object"),
    }
    if source_field.get("required"):
        result["required"] = True
    if "type_spec" in source_field:
        result["type_spec"] = source_field["type_spec"]
    # Preserve source_reference as-is (table lookups should NOT be converted to source.regulation
    # because table names can collide with law names, causing circular references)
    if "source_reference" in source_field:
        sref = source_field["source_reference"]
        # Lowercase variable references in select_on values
        new_sref = dict(sref)
        if "select_on" in new_sref:
            new_select_on = []
            for sel in new_sref["select_on"]:
                new_sel = dict(sel)
                pass  # Keep original casing
                new_select_on.append(new_sel)
            new_sref["select_on"] = new_select_on
        result["source_reference"] = new_sref
    return result


def transform_definitions(definitions: dict) -> dict:
    """Transform old flat definitions to new format with value wrapper."""
    result = {}
    for key, value in definitions.items():
        if isinstance(value, dict) and "value" in value:
            # Already has a value wrapper (e.g., {value: 1.8, legal_basis: {...}})
            result[key] = value
        else:
            result[key] = {"value": value}
    return result


def lowercase_var_refs(node):
    """Recursively lowercase variable references ($VAR → $var) in operation trees."""
    if node is None:
        return None
    if isinstance(node, bool):
        return node
    if isinstance(node, (int, float)):
        return node
    if isinstance(node, str):
        if node.startswith("$"):
            return node.lower()
        return node
    if isinstance(node, list):
        return [lowercase_var_refs(item) for item in node]
    if isinstance(node, dict):
        result = {}
        for k, v in node.items():
            if k == "output" and isinstance(v, str):
                result[k] = v  # Keep output names as-is
            elif k in ("name",) and isinstance(v, str):
                result[k] = v  # Keep field names as-is
            else:
                result[k] = lowercase_var_refs(v)
        return result
    return node


def convert_file(data: dict) -> dict:
    """Convert a single law YAML from v0.1.x to v0.5.0 format."""
    props = data.get("properties", {})

    # --- Root-level metadata ---
    result: dict = {}

    # $schema
    result["$schema"] = V050_SCHEMA_URL

    # $id (from old `law` field)
    law_id = data.get("law", "")
    result["$id"] = law_id

    # regulatory_layer
    law_type = data.get("law_type", "FORMELE_WET")
    result["regulatory_layer"] = LAW_TYPE_TO_REGULATORY_LAYER.get(law_type, "WET")

    # publication_date (use valid_from as fallback)
    valid_from = str(data.get("valid_from", ""))
    result["publication_date"] = valid_from
    result["valid_from"] = valid_from

    # name
    if "name" in data:
        result["name"] = data["name"]

    # bwb_id
    legal_basis = data.get("legal_basis", {})
    bwb_id = legal_basis.get("bwb_id", "")
    if bwb_id:
        result["bwb_id"] = bwb_id

    # url
    if bwb_id and valid_from:
        result["url"] = f"https://wetten.overheid.nl/{bwb_id}/{valid_from}"
    elif legal_basis.get("url"):
        result["url"] = legal_basis["url"]
    else:
        result["url"] = f"https://wetten.overheid.nl/{valid_from}"

    # Keep service as custom extension field
    if "service" in data:
        result["service"] = data["service"]

    # Preserve uuid and discoverable (custom extension fields used by the engine)
    if "uuid" in data:
        result["uuid"] = data["uuid"]
    if "discoverable" in data:
        result["discoverable"] = data["discoverable"]

    # --- Build articles ---
    # Gather all components
    parameters = props.get("parameters", [])
    inputs = props.get("input", [])
    outputs = props.get("output", [])
    sources = props.get("sources", [])
    definitions = props.get("definitions", {})
    requirements = data.get("requirements", [])
    actions = data.get("actions", [])
    legal_character = data.get("legal_character", "")
    decision_type = data.get("decision_type", "")

    # Determine article number from legal_basis
    article_number = legal_basis.get("article", "1")

    # Build single article (most files map to one article)
    article = build_article(
        number=article_number,
        bwb_id=bwb_id,
        valid_from=valid_from,
        legal_character=legal_character,
        decision_type=decision_type,
        parameters=parameters,
        inputs=inputs,
        outputs=outputs,
        sources=sources,
        definitions=definitions,
        requirements=requirements,
        actions=actions,
    )

    result["articles"] = [article]

    return result


def build_article(
    number: str,
    bwb_id: str,
    valid_from: str,
    legal_character: str,
    decision_type: str,
    parameters: list,
    inputs: list,
    outputs: list,
    sources: list,
    definitions: dict,
    requirements: list,
    actions: list,
) -> dict:
    """Build a single article in v0.5.0 format."""
    # Article URL
    if bwb_id and valid_from:
        url = f"https://wetten.overheid.nl/{bwb_id}/{valid_from}#Artikel{number}"
    else:
        url = f"https://wetten.overheid.nl/{valid_from}#Artikel{number}"

    article: dict = {
        "number": str(number),
        "text": "",
        "url": url,
    }

    machine_readable: dict = {}

    # Definitions
    if definitions:
        machine_readable["definitions"] = transform_definitions(definitions)

    # Execution block
    execution: dict = {}

    # produces
    if legal_character or decision_type:
        produces: dict = {}
        if legal_character:
            produces["legal_character"] = legal_character
        if decision_type:
            produces["decision_type"] = decision_type
        execution["produces"] = produces

    # parameters
    if parameters:
        execution["parameters"] = [transform_parameter_field(p) for p in parameters]

    # input (merge sources into inputs)
    new_inputs = []
    for inp in inputs:
        new_inputs.append(transform_input_field(inp))
    for src in sources:
        new_inputs.append(transform_source_to_input(src))
    if new_inputs:
        execution["input"] = new_inputs

    # output
    if outputs:
        execution["output"] = [transform_output_field(o) for o in outputs]

    # requirements - keep in original format
    if requirements:
        execution["requirements"] = requirements

    # actions
    new_actions = []

    # Convert regular actions
    for action in actions:
        new_actions.append(transform_action(action))

    if new_actions:
        execution["actions"] = new_actions

    if execution:
        machine_readable["execution"] = execution

    if machine_readable:
        article["machine_readable"] = machine_readable

    return article


def validate_against_schema(data: dict, schema_path: Path) -> list[str]:
    """Validate converted data against v0.5.0 JSON schema."""
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema package not installed. Run: uv add jsonschema"]

    schema = json.loads(schema_path.read_text())
    validator = jsonschema.Draft7Validator(schema)
    errors = []
    for error in validator.iter_errors(data):
        # Skip "valid under each of" errors - these are oneOf ambiguities in the schema
        # (e.g. $prev_january_first matches both variableReference and enum)
        if "is valid under each of" in error.message:
            continue
        path = ".".join(str(p) for p in error.absolute_path)
        errors.append(f"  {path}: {error.message}")
    return errors


def process_file(
    input_path: Path,
    output_dir: Path | None,
    dry_run: bool,
    validate: bool,
    schema_path: Path | None,
) -> tuple[bool, list[str]]:
    """Process a single YAML file. Returns (success, messages)."""
    messages = []

    try:
        data = load_yaml(input_path)
    except Exception as e:
        return False, [f"Failed to parse {input_path}: {e}"]

    if not is_old_format(data):
        messages.append(f"Skipping {input_path} (not old format or already converted)")
        return True, messages

    try:
        converted = convert_file(data)
    except Exception as e:
        return False, [f"Failed to convert {input_path}: {e}"]

    yaml_output = dump_yaml(converted)

    if dry_run:
        messages.append(f"Would convert: {input_path}")
        messages.append(f"  $id: {converted.get('$id', '?')}")
        messages.append(f"  regulatory_layer: {converted.get('regulatory_layer', '?')}")
        articles = converted.get("articles", [])
        messages.append(f"  articles: {len(articles)}")
        for art in articles:
            mr = art.get("machine_readable", {})
            exe = mr.get("execution", {})
            n_actions = len(exe.get("actions", []))
            n_inputs = len(exe.get("input", []))
            n_outputs = len(exe.get("output", []))
            messages.append(f"    article {art['number']}: {n_inputs} inputs, {n_outputs} outputs, {n_actions} actions")
    else:
        if output_dir:
            out_path = output_dir / input_path.relative_to(input_path.parents[len(input_path.parts) - 2])
            out_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            out_path = input_path

        with open(out_path, "w") as f:
            f.write(yaml_output)
        messages.append(f"Converted: {input_path} -> {out_path}")

    if validate and schema_path:
        errors = validate_against_schema(converted, schema_path)
        if errors:
            messages.append(f"  Validation errors in {input_path}:")
            messages.extend(errors)
            return False, messages
        else:
            messages.append(f"  Validation passed: {input_path}")

    return True, messages


def main():
    parser = argparse.ArgumentParser(description="Convert law YAML files from v0.1.x to v0.5.0 format")
    parser.add_argument("path", type=Path, help="File or directory to convert")
    parser.add_argument("--output-dir", type=Path, default=None, help="Output directory (default: overwrite in place)")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument("--validate", action="store_true", help="Validate output against v0.5.0 schema")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")

    schema_path = Path(__file__).parent.parent / "schema" / "v0.5.0" / "schema.json"
    if args.validate and not schema_path.exists():
        logger.error(f"Schema not found at {schema_path}")
        sys.exit(1)

    # Collect YAML files
    target = args.path
    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = sorted(target.rglob("*.yaml"))
    else:
        logger.error(f"Path not found: {target}")
        sys.exit(1)

    if not files:
        logger.error(f"No YAML files found in {target}")
        sys.exit(1)

    success_count = 0
    fail_count = 0
    skip_count = 0

    for f in files:
        ok, messages = process_file(
            f,
            output_dir=args.output_dir,
            dry_run=args.dry_run,
            validate=args.validate,
            schema_path=schema_path if args.validate else None,
        )
        for msg in messages:
            if "Skipping" in msg:
                skip_count += 1
                if args.verbose:
                    logger.info(msg)
            else:
                logger.info(msg)

        if ok:
            if not any("Skipping" in m for m in messages):
                success_count += 1
        else:
            fail_count += 1

    logger.info(f"\nDone: {success_count} converted, {skip_count} skipped, {fail_count} failed")
    sys.exit(1 if fail_count > 0 else 0)


if __name__ == "__main__":
    main()
