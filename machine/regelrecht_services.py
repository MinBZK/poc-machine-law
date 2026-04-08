"""Services wrapping the regelrecht Rust engine (PyO3) and the Python engine.

Law evaluation delegates to the Python engine which handles all law
features correctly (FOREACH, cross-law references, source_ref_mapping
field resolution, dot-notation projection on arrays).

DataFrames are registered in both engines so the Rust engine stays
primed for future use as its feature set catches up.
"""

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from regelrecht_engine import RegelrechtEngine

from machine.service import RuleResult, Services

logger = logging.getLogger(__name__)
LAWS_DIR = Path("laws")
_SOURCE_REF_MAPPING_PATH = Path(__file__).parent / "source_ref_mapping.json"


def _build_object_field_mapping() -> dict[str, dict[str, list[str]]]:
    """Build mapping: {table_name: {input_name: [field1, field2, ...]}} for multi-field inputs.

    Reads source_ref_mapping.json and identifies entries with a ``fields`` list
    (i.e. object-typed inputs that combine several DataFrame columns into a single dict).
    """
    if not _SOURCE_REF_MAPPING_PATH.exists():
        return {}
    with open(_SOURCE_REF_MAPPING_PATH) as f:
        mapping = json.load(f)
    result: dict[str, dict[str, list[str]]] = {}
    for key, entry in mapping.items():
        if "fields" not in entry:
            continue
        # key format: "law_path:input_name"
        input_name = key.rsplit(":", 1)[-1]
        table = entry["table"]
        fields = entry["fields"]
        if table not in result:
            result[table] = {}
        # Multiple laws may map the same table+input with different field lists;
        # merge them to keep the superset of columns.
        existing = result[table].get(input_name, [])
        merged = list(dict.fromkeys(existing + fields))  # preserves order, deduplicates
        result[table][input_name] = merged
    return result


# Module-level cache so we parse the JSON once.
_OBJECT_FIELD_MAPPING: dict[str, dict[str, list[str]]] = _build_object_field_mapping()


class RegelrechtServices:
    """Drop-in replacement for Services using the regelrecht Rust engine."""

    def __init__(self, reference_date: str) -> None:
        self._services = Services(reference_date)
        self.resolver = self._services.resolver
        self.root_reference_date = reference_date
        self._engine = RegelrechtEngine()
        self._load_all_laws()

    def _load_all_laws(self) -> None:
        """Load all laws into the engine as-is. Cross-law sources (source.regulation)
        are resolved by the engine. Data source inputs (source: {}) are resolved
        from registered DataFrames."""
        for path in sorted(LAWS_DIR.rglob("*.yaml")):
            try:
                self._engine.load_law(path.read_text())
            except Exception as e:
                logger.debug("Could not load %s: %s", path, e)
        logger.info("Loaded %d laws into engine", self._engine.law_count())

    # -- Orchestration delegates -----------------------------------------------

    @property
    def services(self):
        return self._services.services

    @property
    def case_manager(self):
        return self._services.case_manager

    @property
    def claim_manager(self):
        return self._services.claim_manager

    @property
    def runner(self):
        return self._services.runner

    def get_discoverable_service_laws(self, discoverable_by="CITIZEN"):
        return self._services.get_discoverable_service_laws(discoverable_by)

    def get_service_laws(self):
        return self._services.resolver.get_service_laws()

    def get_law(self, service, law, reference_date=None):
        return self._services.get_law(service, law, reference_date)

    def apply_rules(self, event):
        return self._services.apply_rules(event)

    # -- Data sources ----------------------------------------------------------

    def set_source_dataframe(self, service: str, table: str, df: pd.DataFrame) -> None:
        """Register DataFrame in both Services and the Rust engine.

        Uses source_ref_mapping.json to determine the correct key field per table
        and to create synthetic object/array fields for multi-field inputs.
        """
        self._services.set_source_dataframe(service, table, df)
        if df.empty:
            return

        key_field = _pick_key_field_for_table(table, df)
        param_key = _get_param_key_for_table(table, key_field)
        object_inputs = _OBJECT_FIELD_MAPPING.get(table, {})

        records = []
        for _, row in df.iterrows():
            record = _to_native({col: row[col] for col in df.columns})
            # If the DataFrame key differs from the parameter key, add an alias
            # so the engine can look up by parameter name (e.g., bsn → bsn_curator)
            if param_key != key_field and param_key not in record and key_field in record:
                record[param_key] = record[key_field]
            # Inject synthetic object fields for multi-field inputs.
            # DON'T inject if the input name matches the table name - that means
            # it's an array-type input that should come from _register_array_data_source.
            for input_name, field_list in object_inputs.items():
                if input_name == table:
                    continue
                obj = {f: record[f] for f in field_list if f in record}
                if obj:
                    record[input_name] = obj
            records.append(record)

        try:
            # Register with the parameter-side key so engine criteria match
            self._engine.register_data_source(table, param_key, records)
        except Exception as e:
            logger.debug("Could not register data source %s: %s", table, e)

        # For tables that have array-type inputs (e.g., curatele_registraties),
        # also register a grouped version where all rows for the same key are
        # collected into an array under the table name as field.
        if table in _ARRAY_INPUT_TABLES:
            self._register_array_data_source(table, key_field, records)

    def _register_array_data_source(self, table: str, key_field: str, records: list) -> None:
        """Group records by key and register as array-valued data source.

        The key_field in the data source must match the parameter name that the
        law uses (e.g., 'bsn'), not the DataFrame column name (e.g., 'bsn_curator').
        We use source_ref_mapping.json to find the parameter name from the select_on
        value reference (e.g., '$bsn' → 'bsn').
        """
        # Determine the parameter-side key name from the mapping
        param_key = _get_param_key_for_table(table, key_field)

        grouped: dict[str, list] = {}
        for record in records:
            key = str(record.get(key_field, ""))
            grouped.setdefault(key, []).append(record)

        array_records = []
        for key, rows in grouped.items():
            array_records.append({param_key: key, table: rows})

        try:
            self._engine.register_data_source(f"{table}_array", param_key, array_records)
        except Exception as e:
            logger.debug("Could not register array data source %s: %s", table, e)

    # -- Evaluation ------------------------------------------------------------

    def evaluate(
        self,
        service: str,
        law: str,
        parameters: dict[str, Any],
        reference_date: str | None = None,
        overwrite_input: dict[str, Any] | None = None,
        overwrite_definitions: dict[str, Any] | None = None,
        requested_output: str | None = None,
        approved: bool = False,
        **kwargs,
    ) -> RuleResult:
        """Evaluate a law using the Rust engine.

        After evaluation, applies dot-notation projection for any outputs
        the engine returned as None (e.g. ``$actieve_curatele.bsn_curandus``).
        The engine computes FOREACH correctly but cannot yet project fields
        from arrays, so we do that in Python as a post-processing step.
        """
        reference_date = reference_date or self.root_reference_date
        rule = self.resolver.find_rule(law, reference_date, service)
        if not rule:
            raise ValueError(f"No rule found for {law}")

        params = _to_native(dict(parameters))
        if overwrite_input:
            for sv in overwrite_input.values():
                if isinstance(sv, dict):
                    params.update(_to_native(sv))

        import yaml as yaml_mod

        data = yaml_mod.safe_load(Path(rule.path).read_text())
        law_id = data.get("$id", law)
        output_names = []
        for art in data.get("articles", []):
            for o in art.get("machine_readable", {}).get("execution", {}).get("output", []):
                name = o.get("name")
                if name and name not in output_names:
                    output_names.append(name)
        if requested_output:
            output_names = [requested_output]
        if not output_names:
            return RuleResult(
                output={},
                requirements_met=False,
                input=params,
                rulespec_uuid=rule.uuid,
                path=None,
                missing_required=True,
            )

        try:
            result = self._engine.evaluate(law_id, output_names, params, reference_date)
        except Exception as e:
            logger.warning("Engine error for %s: %s", law, e)
            return RuleResult(
                output={},
                requirements_met=False,
                input=params,
                rulespec_uuid=rule.uuid,
                path=None,
                missing_required=True,
            )

        outputs = dict(result.get("outputs", {}))
        resolved = dict(result.get("resolved_inputs", {}))

        # Post-process: the engine handles FOREACH correctly but cannot yet
        # perform dot-notation projection on arrays, evaluate CONCAT inside
        # FOREACH bodies, or resolve $variable references in FOREACH bodies.
        # We fix these in Python as post-processing.
        _postprocess_outputs(outputs, params, data)

        voldoet = outputs.pop("voldoet_aan_voorwaarden", None)
        req_met = bool(voldoet) if voldoet is not None else bool(outputs)

        return RuleResult(
            output=outputs,
            requirements_met=req_met,
            input=resolved,
            rulespec_uuid=rule.uuid,
            path=None,
            missing_required=not req_met and not outputs,
        )


def _postprocess_outputs(outputs: dict, params: dict, data: dict) -> None:
    """Fix engine outputs that require Python-side post-processing.

    Handles three cases the Rust engine doesn't support yet:
    1. Dot-notation projection: ``$actieve_curatele.bsn_curandus``
    2. Unevaluated CONCAT operations in FOREACH body results
    3. Unresolved ``$variable`` references in FOREACH body results
    """
    namespace = {**params, **outputs}

    # Collect all actions for FOREACH-aware resolution
    actions: list[dict] = []
    for art in data.get("articles", []):
        actions.extend(art.get("machine_readable", {}).get("execution", {}).get("actions", []))

    for action in actions:
        value = action.get("value")
        output_name = action.get("output")
        if not output_name:
            continue

        # 1. Dot-notation projection on arrays/objects
        if isinstance(value, str) and value.startswith("$") and "." in value:
            if outputs.get(output_name) is not None:
                continue
            ref = value[1:]
            var_name, _, field_name = ref.partition(".")
            source = outputs.get(var_name)
            if source is None:
                continue
            if isinstance(source, list):
                outputs[output_name] = [item.get(field_name) if isinstance(item, dict) else None for item in source]
            elif isinstance(source, dict):
                outputs[output_name] = source.get(field_name)
            continue

        # 2. FOREACH with unevaluated body (CONCAT, $current refs, $variable refs)
        if isinstance(value, dict) and value.get("operation") == "FOREACH":
            current_value = outputs.get(output_name)
            if current_value is None or not isinstance(current_value, list):
                continue
            if not _needs_resolution(current_value):
                continue
            # Get the FOREACH collection to use as element context
            collection_ref = value.get("collection", "")
            as_name = value.get("as", "current")
            collection = []
            if isinstance(collection_ref, str) and collection_ref.startswith("$"):
                collection = outputs.get(collection_ref[1:], []) or []
            # Resolve each element against its corresponding collection item
            resolved = []
            for i, item in enumerate(current_value):
                element = collection[i] if i < len(collection) and isinstance(collection, list) else {}
                item_ns = {**namespace, as_name: element}
                if isinstance(element, dict):
                    # Also make $current.field accessible as top-level in namespace
                    item_ns.update({f"{as_name}.{k}": v for k, v in element.items()})
                resolved.append(_resolve_value(item, item_ns))
            outputs[output_name] = resolved

    # 3. Final pass: resolve any remaining $variable strings
    namespace = {**params, **outputs}
    for key, value in list(outputs.items()):
        outputs[key] = _resolve_value(value, namespace)


def _needs_resolution(value: Any) -> bool:
    """Check if a value contains unevaluated operations or $references."""
    if isinstance(value, dict) and "operation" in value:
        return True
    if isinstance(value, str) and value.startswith("$"):
        return True
    if isinstance(value, list):
        return any(_needs_resolution(item) for item in value)
    return False


def _resolve_value(value: Any, namespace: dict) -> Any:
    """Recursively resolve unevaluated engine output values.

    Handles:
    - ``{'operation': 'CONCAT', 'values': [...]}`` dicts
    - ``$variable`` string references
    - Lists containing any of the above
    """
    if isinstance(value, list):
        return [_resolve_value(item, namespace) for item in value]
    if isinstance(value, dict) and value.get("operation") == "CONCAT":
        parts = []
        for v in value.get("values", []):
            resolved = _resolve_value(v, namespace)
            parts.append(str(resolved) if resolved is not None else "")
        return "".join(parts)
    if isinstance(value, str) and value.startswith("$"):
        ref = value[1:]
        if "." in ref:
            var_name, _, field_name = ref.partition(".")
            source = namespace.get(var_name)
            if isinstance(source, dict):
                return source.get(field_name, value)
            if isinstance(source, list):
                return [item.get(field_name) if isinstance(item, dict) else None for item in source]
        elif ref in namespace:
            return namespace[ref]
    return value


def _pick_key_field(df: pd.DataFrame) -> str:
    for c in ("bsn", "kvk_nummer", "uuid", "id"):
        if c in df.columns:
            return c
    return df.columns[0]


def _pick_key_field_for_table(table: str, df: pd.DataFrame) -> str:
    """Pick the best key field using source_ref_mapping.json knowledge."""
    # Check mapping for this table's select_on fields
    table_keys = _TABLE_KEY_FIELDS.get(table)
    if table_keys:
        for key in table_keys:
            if key in df.columns:
                return key
    return _pick_key_field(df)


def _build_table_key_fields() -> dict[str, list[str]]:
    """Build mapping of table → ALL possible key fields from source_ref_mapping.json."""
    result: dict[str, list[str]] = {}
    if not _SOURCE_REF_MAPPING_PATH.exists():
        return result
    with open(_SOURCE_REF_MAPPING_PATH) as f:
        mapping = json.load(f)
    for entry in mapping.values():
        table = entry.get("table", "")
        select_on = entry.get("select_on", [])
        if table and isinstance(select_on, list):
            existing = result.get(table, [])
            for s in select_on:
                name = s.get("name")
                if name and name not in existing:
                    existing.append(name)
            result[table] = existing
    return result


def _build_array_input_tables() -> set[str]:
    """Find tables that serve array-type inputs."""
    result = set()
    if not _SOURCE_REF_MAPPING_PATH.exists():
        return result
    with open(_SOURCE_REF_MAPPING_PATH) as f:
        mapping = json.load(f)
    for entry in mapping.values():
        table = entry.get("table", "")
        if table and "fields" in entry:
            result.add(table)
    return result


_TABLE_KEY_FIELDS: dict[str, list[str]] = _build_table_key_fields()
_ARRAY_INPUT_TABLES: set[str] = _build_array_input_tables()


def _get_param_key_for_table(table: str, df_key_field: str) -> str:
    """Get the parameter-side key name for a table's select_on.

    E.g., curatele_registraties has select_on: [{name: bsn_curator, value: $bsn}]
    The DataFrame key is 'bsn_curator' but the parameter key is 'bsn'.
    """
    if not _SOURCE_REF_MAPPING_PATH.exists():
        return df_key_field
    with open(_SOURCE_REF_MAPPING_PATH) as f:
        mapping = json.load(f)
    for entry in mapping.values():
        if entry.get("table") != table:
            continue
        select_on = entry.get("select_on", [])
        for criterion in select_on:
            col = criterion.get("name", "")
            ref = criterion.get("value", "")
            if col == df_key_field and isinstance(ref, str) and ref.startswith("$"):
                return ref[1:]  # Strip $ prefix → parameter name
    return df_key_field


def _to_native(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _to_native(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_native(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if isinstance(obj, float) and pd.isna(obj):
        return None
    return obj
