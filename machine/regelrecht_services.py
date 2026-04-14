"""Services using the regelrecht Rust engine (PyO3).

All law evaluation goes through the Rust engine. DataFrames are
registered as data sources. Pre-resolution handles field name mapping
and cross-law chains. Post-processing handles dot-notation projection.
"""

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from regelrecht_engine import RegelrechtEngine

from machine.service import RuleResult, Services

# Cache YAML law specs by path. Cross-law pre-resolution can re-enter the same
# laws dozens of times per evaluation; without the cache each re-entry re-parses
# a ~35ms YAML file and a single dashboard evaluation takes 500ms instead of the
# 40μs the Rust engine actually needs.
_LAW_YAML_CACHE: dict[str, dict] = {}


def _load_law_yaml(path: str) -> dict:
    """Load a law YAML file, cached by absolute path."""
    cached = _LAW_YAML_CACHE.get(path)
    if cached is not None:
        return cached
    data = yaml.safe_load(Path(path).read_text()) or {}
    _LAW_YAML_CACHE[path] = data
    return data


def _param_val_to_str(val: Any) -> str:
    """Convert a parameter value to string for DataFrame column comparison.

    When the value is a dict or list, serialize as JSON so it matches
    JSON strings stored in DataFrame columns. Uses default json.dumps
    format (no sorted keys) to match the storage format from feature files.
    For scalar values, use plain str() conversion.
    """
    if isinstance(val, (dict, list)):
        return json.dumps(val)
    return str(val)


def _df_col_matches(df: pd.DataFrame, col: str, target: str) -> pd.Series:
    """Compare a DataFrame column against a target string, handling dicts/lists.

    DataFrame columns may contain dict/list objects (from parse_value in test
    steps). Python's str() for dicts uses single quotes, but JSON uses double
    quotes. For object-valued columns we JSON-serialize each row so the
    comparison works. For scalar columns we compare the column as string,
    which is orders of magnitude faster than a per-row .apply().
    """
    series = df[col]
    if len(series) == 0:
        return series == target  # empty bool series
    # Sample the first non-null value: if it's dict/list, fall back to the
    # slow JSON-serialize path. Otherwise a vectorised astype(str) is enough.
    sample = None
    for v in series:
        if v is not None:
            sample = v
            break
    if isinstance(sample, (dict, list)):
        col_values = series.apply(lambda v: json.dumps(v) if isinstance(v, (dict, list)) else str(v))
        return col_values == target
    return series.astype(str) == target


def _resolve_param_ref(ref: str, params: dict[str, Any]) -> Any | None:
    """Resolve a $-prefixed parameter reference, supporting dot notation.

    - ``$bsn`` → ``params["bsn"]``
    - ``$adres.postcode`` → ``params["adres"]["postcode"]`` (when adres is a dict)
    """
    name = ref[1:] if ref.startswith("$") else ref
    if "." in name:
        var_name, _, field_name = name.partition(".")
        obj = params.get(var_name)
        if isinstance(obj, dict):
            return obj.get(field_name)
        return None
    return params.get(name)


from machine.logging_config import IndentLogger

logger = IndentLogger(logging.getLogger("rules_engine"))
LAWS_DIR = Path("laws")


class RegelrechtServices:
    """Drop-in replacement for Services using the regelrecht Rust engine."""

    def __init__(self, reference_date: str) -> None:
        self._services = Services(reference_date, rules_engine=self)
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
        # Schema v0.5.1 uses hooks/overrides (RFC-007) instead of the legacy
        # `applies` mechanism. The case processor still calls this on Decided
        # events, but there is nothing to do here for v0.5.1 laws.
        return None

    def _sync_engine_data_sources(self) -> None:
        """Clear and re-register all data sources in the Rust engine.

        Rebuilds engine data sources from the Python-side DataFrames before
        each evaluation. The engine reads inline source metadata
        (table/field/select_on/fields) from YAML to resolve inputs natively.
        """
        self._engine.clear_data_sources()
        all_sources: dict[str, pd.DataFrame] = {}
        for svc in self._services.services.values():
            all_sources.update(svc.source_dataframes)

        for table, df in all_sources.items():
            self._register_dataframe(table, df)

    def _register_dataframe(self, table: str, df: pd.DataFrame) -> None:
        """Register a DataFrame as a record-set data source on the engine.

        The engine reads the law's YAML ``source.select_on`` to determine
        which columns to filter on per query — we don't need to constrain
        that at registration time. We only pass the raw records and let
        the engine pick the right criteria from the YAML spec.
        """
        if df.empty:
            return
        records = [_to_native({col: row[col] for col in df.columns}) for _, row in df.iterrows()]
        try:
            self._engine.register_record_set_source(name=table, records=records)
        except Exception as e:
            logger.debug("Could not register data source %s: %s", table, e)

    # -- Data sources ----------------------------------------------------------

    def set_source_dataframe(self, service: str, table: str, df: pd.DataFrame) -> None:
        """Register DataFrame in both Services and the Rust engine."""
        self._services.set_source_dataframe(service, table, df)
        self._register_dataframe(table, df)

    # -- Data source pre-resolution ---------------------------------------------

    def _pre_resolve_data_sources(self, law_id: str, params: dict[str, Any], data: dict) -> None:
        """Resolve ``source: {}`` inputs from DataFrames and inject into params.

        The Rust engine resolves data source inputs by looking up the input
        name in the DataSourceRegistry. When the DataFrame column name differs
        from the law input name (e.g. input ``advies_mate_van_gevaar`` vs column
        ``mate_van_gevaar``), the engine cannot find it. This method reads the
        inline ``source: {table, field, select_on, fields}`` metadata from the
        YAML and uses it to query the Python-side DataFrames, injecting the
        resolved values as parameters so the engine finds them directly.

        Additionally, for ``source: {}`` inputs with no inline metadata, it
        scans all DataFrames for a matching column name (fallback resolution).
        """
        # Gather all service DataFrames
        all_sources: dict[str, pd.DataFrame] = {}
        for svc in self._services.services.values():
            all_sources.update(svc.source_dataframes)

        # Build input type lookup from YAML for array detection
        input_types: dict[str, str] = {}
        for art in data.get("articles", []):
            for inp in art.get("machine_readable", {}).get("execution", {}).get("input", []):
                iname = inp.get("name", "")
                itype = inp.get("type", "")
                if iname:
                    input_types[iname] = itype

        # Phase 1: resolve inputs via inline YAML source metadata
        input_mapping = _build_input_mapping_from_yaml(data)
        for input_name, entry in input_mapping.items():
            if input_name in params:
                continue

            table = entry.get("table", "")
            if not table or table not in all_sources:
                continue

            df = all_sources[table]
            if df.empty:
                continue

            field = entry.get("field", input_name)
            select_on = entry.get("select_on", [])
            fields = entry.get("fields")

            # Build selection mask from select_on criteria
            mask = pd.Series(True, index=df.index)
            for criterion in select_on:
                col = criterion.get("name", "")
                ref = criterion.get("value", "")
                if not col or col not in df.columns:
                    mask = pd.Series(False, index=df.index)
                    break
                if isinstance(ref, str) and ref.startswith("$"):
                    param_val = _resolve_param_ref(ref, params)
                    if param_val is None:
                        mask = pd.Series(False, index=df.index)
                        break
                    mask = mask & _df_col_matches(df, col, _param_val_to_str(param_val))
                elif isinstance(ref, dict):
                    # Complex operations (e.g., {operation: IN, values: ...})
                    # Skip this criterion; match all rows for this column.
                    pass
                else:
                    mask = mask & (df[col] == ref)

            matched = df[mask]
            if matched.empty:
                continue

            # Array-type inputs: collect ALL matching rows as a list of objects
            # so the engine can iterate with FOREACH.
            is_array_input = input_types.get(input_name) == "array"
            if fields and is_array_input:
                rows = []
                for _, row in matched.iterrows():
                    obj = {f: _to_native(row[f]) for f in fields if f in row.index}
                    if obj:
                        rows.append(obj)
                if rows:
                    params[input_name] = rows
                continue

            if fields:
                row = matched.iloc[0]
                obj = {f: _to_native(row[f]) for f in fields if f in row.index}
                if obj:
                    params[input_name] = obj
            elif field in matched.columns:
                val = _to_native(matched.iloc[0][field])
                # Parse JSON strings for array/object inputs stored as JSON in DataFrames
                val = _maybe_parse_json(val)
                params[input_name] = val
            elif field == input_name and field not in matched.columns:
                # Object input without explicit fields list in mapping:
                # compose an object from the entire matched row.
                row = matched.iloc[0]
                obj = _to_native({col: row[col] for col in matched.columns})
                params[input_name] = obj

        # Phase 2: fallback for source: {} inputs not in the mapping.
        # For scalar inputs, scan all DataFrames for a matching column.
        # For object inputs, compose an object from the matched row.
        for art in data.get("articles", []):
            for inp in art.get("machine_readable", {}).get("execution", {}).get("input", []):
                input_name = inp.get("name", "")
                source = inp.get("source")
                input_type = inp.get("type", "")
                if input_name in params:
                    continue
                if source is None or source != {}:
                    continue  # Only handle empty source: {}
                # Skip inputs that Phase 1 already handled via the mapping.
                # If the mapping had select_on criteria that didn't match,
                # we should NOT fall back to unfiltered data.
                if input_name in input_mapping:
                    continue

                # Sort tables: prefer name matching input_name first
                sorted_tables = sorted(
                    all_sources.items(),
                    key=lambda item: (0 if input_name in item[0] or item[0] in input_name else 1, item[0]),
                )
                for tbl_name, df in sorted_tables:
                    if df.empty:
                        continue
                    # Use params to filter rows
                    mask = pd.Series(True, index=df.index)
                    for pkey, pval in params.items():
                        if pkey in df.columns:
                            mask = mask & (df[pkey].astype(str) == str(pval))
                    matched = df[mask]
                    if matched.empty:
                        matched = df  # Try without filtering

                    if input_type == "array":
                        # Collect all matching rows as a list of dicts
                        if not matched.empty and tbl_name == input_name:
                            rows = []
                            for _, row in matched.iterrows():
                                rows.append(_to_native({col: row[col] for col in df.columns}))
                            params[input_name] = rows
                            break
                    elif input_type == "object":
                        if not matched.empty:
                            row = matched.iloc[0]
                            obj = _to_native({col: row[col] for col in df.columns})
                            params[input_name] = obj
                            break
                    elif input_name in df.columns and not matched.empty:
                        params[input_name] = _to_native(matched.iloc[0][input_name])
                        break

    def _pre_resolve_data_sources_phase1_only(self, law_id: str, params: dict[str, Any], data: dict) -> None:
        """Phase 1 only: resolve inputs via source_ref_mapping (precise matching).

        Unlike ``_pre_resolve_data_sources``, this skips the Phase 2 fallback
        that scans all DataFrames for matching columns. This avoids contaminating
        inputs by matching the wrong table when used in cross-law pre-resolution.
        """
        all_sources: dict[str, pd.DataFrame] = {}
        for svc in self._services.services.values():
            all_sources.update(svc.source_dataframes)

        # Build input type lookup from YAML for array detection
        input_types: dict[str, str] = {}
        for art in data.get("articles", []):
            for inp in art.get("machine_readable", {}).get("execution", {}).get("input", []):
                iname = inp.get("name", "")
                itype = inp.get("type", "")
                if iname:
                    input_types[iname] = itype

        input_mapping = _build_input_mapping_from_yaml(data)
        # Multi-pass: some inputs depend on others (e.g., partner_geboortedatum
        # needs partner_bsn). Two passes handles one level of dependency.
        for _pass in range(2):
            resolved_any = False
            for input_name, entry in input_mapping.items():
                if input_name in params:
                    continue

                table = entry.get("table", "")
                if not table or table not in all_sources:
                    continue

                df = all_sources[table]
                if df.empty:
                    continue

                field = entry.get("field", input_name)
                select_on = entry.get("select_on", [])
                fields = entry.get("fields")

                mask = pd.Series(True, index=df.index)
                for criterion in select_on:
                    col = criterion.get("name", "")
                    ref = criterion.get("value", "")
                    if not col or col not in df.columns:
                        mask = pd.Series(False, index=df.index)
                        break
                    if isinstance(ref, str) and ref.startswith("$"):
                        param_val = _resolve_param_ref(ref, params)
                        if param_val is None:
                            mask = pd.Series(False, index=df.index)
                            break
                        mask = mask & _df_col_matches(df, col, _param_val_to_str(param_val))
                    elif isinstance(ref, dict):
                        # Complex operations (e.g., {operation: IN, values: ...})
                        # Skip this criterion; match all rows for this column.
                        pass
                    else:
                        mask = mask & (df[col] == ref)

                matched = df[mask]
                if matched.empty:
                    continue

                is_array_input = input_types.get(input_name) == "array"
                if fields and is_array_input:
                    rows = []
                    for _, row in matched.iterrows():
                        obj = {f: _to_native(row[f]) for f in fields if f in row.index}
                        if obj:
                            rows.append(obj)
                    if rows:
                        params[input_name] = rows
                        resolved_any = True
                    continue

                if fields:
                    row = matched.iloc[0]
                    obj = {f: _to_native(row[f]) for f in fields if f in row.index}
                    if obj:
                        params[input_name] = obj
                        resolved_any = True
                elif field in matched.columns:
                    val = _to_native(matched.iloc[0][field])
                    # Parse JSON strings for array/object inputs stored as JSON in DataFrames
                    val = _maybe_parse_json(val)
                    params[input_name] = val
                    resolved_any = True
                elif input_types.get(input_name) == "object":
                    # Object input without fields list and no matching column:
                    # compose object from the entire matched row.
                    row = matched.iloc[0]
                    obj = _to_native({col: row[col] for col in matched.columns})
                    params[input_name] = obj
                    resolved_any = True
            if not resolved_any:
                break

    # -- Cross-law pre-resolution -----------------------------------------------

    def _pre_resolve_cross_law_inputs(
        self, data: dict, params: dict[str, Any], reference_date: str, _depth: int = 0
    ) -> None:
        """Pre-resolve cross-law inputs (source.regulation) via recursive evaluation.

        The Rust engine resolves cross-law references internally but can fail
        when chains are deep or data sources are needed at intermediate steps.
        This method resolves them in Python first and injects the results as
        parameters so the engine finds them directly.
        """
        if _depth > 5:
            return  # Guard against infinite recursion

        for art in data.get("articles", []):
            for inp in art.get("machine_readable", {}).get("execution", {}).get("input", []):
                input_name = inp.get("name", "")
                if input_name in params:
                    continue
                source = inp.get("source")
                if not isinstance(source, dict) or not source.get("regulation"):
                    continue

                regulation = source["regulation"]
                output_name = source.get("output", input_name)
                source_params = source.get("parameters", {})

                # Build parameters for the target law.
                # Parameter refs like $bsn must match case-insensitively
                # because the web UI passes BSN (upper) while YAML uses $bsn.
                params_lower = {k.lower(): v for k, v in params.items()}
                target_params: dict[str, Any] = {}
                for target_key, source_ref in source_params.items():
                    if isinstance(source_ref, str) and source_ref.startswith("$"):
                        var_name = source_ref[1:]
                        if var_name in params:
                            target_params[target_key] = params[var_name]
                        elif var_name.lower() in params_lower:
                            target_params[target_key] = params_lower[var_name.lower()]
                    else:
                        target_params[target_key] = source_ref

                # Find the service for the target regulation
                target_service = source.get("service", "")

                # Handle temporal references that adjust the reference date
                # e.g. temporal.reference: $prev_january_first changes the date
                # used for cross-law evaluation. The Rust engine has the same
                # logic for its native cross-law path; this handles our Python
                # pre-resolution path which still exists.
                effective_date = reference_date
                temporal = inp.get("temporal")
                if isinstance(temporal, dict) and "reference" in temporal:
                    effective_date = _resolve_temporal_reference(temporal["reference"], reference_date)

                try:
                    sub_result = self._evaluate_for_preresolution(
                        target_service,
                        regulation,
                        target_params,
                        effective_date,
                        output_name,
                        _depth + 1,
                    )
                    if sub_result is not None:
                        params[input_name] = sub_result
                    else:
                        logger.debug("Cross-law %s returned None for %s", regulation, output_name)
                except Exception as exc:
                    logger.debug("Cross-law %s failed for %s: %s", regulation, input_name, exc)

    def _evaluate_for_preresolution(
        self,
        service: str,
        law: str,
        parameters: dict[str, Any],
        reference_date: str,
        requested_output: str,
        depth: int,
    ) -> Any | None:
        """Evaluate a cross-law reference for pre-resolution.

        Pre-resolves data source inputs (source: {}) for the target law
        using source_ref_mapping.json, then delegates to the engine.
        Cross-law inputs of the target law are recursively pre-resolved.
        """
        try:
            rule = self.resolver.find_rule(law, reference_date, service or None)
        except ValueError:
            try:
                rule = self.resolver.find_rule(law, reference_date, None)
            except ValueError:
                return None
        if not rule:
            return None

        data = _load_law_yaml(rule.path)
        law_id = data.get("$id", law)
        params = _to_native(dict(parameters))

        with logger.indent_block(f"{service or '?'}: {law} ({reference_date}) → {requested_output}"):
            self._pre_resolve_data_sources_phase1_only(law_id, params, data)

            # Log resolved data sources
            for art in data.get("articles", []):
                for inp in art.get("machine_readable", {}).get("execution", {}).get("input", []):
                    inp_name = inp.get("name", "")
                    src = inp.get("source")
                    if isinstance(src, dict) and not src.get("regulation") and inp_name in params:
                        logger.debug("Source: %s = %s", inp_name, params[inp_name])

            self._pre_resolve_cross_law_inputs(data, params, reference_date, depth)

            bsn = params.get("bsn")
            if bsn:
                claims = self.claim_manager.get_claim_by_bsn_service_law(bsn, service or "", law, approved=False)
                if claims:
                    for key, claim in claims.items():
                        params[key] = _to_native(claim.new_value)
                        logger.debug("Claim: %s = %s", key, params[key])

            _fill_input_defaults(data, params)

            try:
                result = self._engine.evaluate_with_trace(law_id, [requested_output], params, reference_date)
                outputs = result.get("outputs", {})
                val = outputs.get(requested_output)
                # Log the sub-evaluation trace
                trace_json = result.get("trace")
                if trace_json:
                    _log_trace(json.loads(trace_json))
                if val is not None:
                    logger.debug("Result: %s = %s", requested_output, val)
                    return val
            except Exception as exc:
                logger.debug("Engine error: %s", exc)

        return None

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
        """Evaluate a law using the Rust engine."""
        reference_date = reference_date or self.root_reference_date
        rule = self.resolver.find_rule(law, reference_date, service)
        if not rule:
            raise ValueError(f"No rule found for {law}")

        with logger.indent_block(f"{service}: {law} ({reference_date})", double_line=True):
            # Sync engine data sources
            self._sync_engine_data_sources()

            params = _to_native(dict(parameters))
            # Normalise BSN → bsn so YAML select_on ($bsn) can resolve
            # whether the caller passed BSN (web UI convention) or bsn.
            if "BSN" in params and "bsn" not in params:
                params["bsn"] = params.pop("BSN")
            if overwrite_input:
                for sv in overwrite_input.values():
                    if isinstance(sv, dict):
                        params.update(_to_native(sv))

            # Resolve claims (citizen-submitted data) and merge into params.
            bsn = params.get("bsn")
            if bsn:
                claims = self.claim_manager.get_claim_by_bsn_service_law(bsn, service, law, approved=approved)
                if claims:
                    for key, claim in claims.items():
                        if key not in params:
                            params[key] = _to_native(claim.new_value)
                            logger.debug("Claim: %s = %s", key, params[key])

            data = _load_law_yaml(rule.path)
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
                logger.debug("No output fields found")
                return RuleResult(
                    output={},
                    requirements_met=False,
                    input=params,
                    rulespec_uuid=rule.uuid,
                    path=None,
                    missing_required=True,
                )

            # Cross-law and data source resolution run natively in the
            # Rust engine (RecordSetDataSource + resolve_external_input
            # _internal). The engine's trace contains nested cross-law
            # evaluations which feed the dashboard's "Gebruikte gegevens"
            # hierarchical view.

            # Check for missing required source: {} inputs.
            missing = _find_missing_required_inputs(data, params)
            if missing:
                logger.debug("Missing required inputs: %s", missing)
                return RuleResult(
                    output={},
                    requirements_met=False,
                    input=params,
                    rulespec_uuid=rule.uuid,
                    path=None,
                    missing_required=True,
                )

            # Type defaults for unresolved inputs are handled natively by
            # the Rust engine (regelrecht 39998b6). Pre-filling them
            # Python-side would short-circuit the engine's native
            # cross-law resolution.

            # Evaluate with trace — the Rust engine records every step
            trace_json = None
            try:
                result = self._engine.evaluate_with_trace(law_id, output_names, params, reference_date)
                trace_json = result.get("trace")
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

            # Resolve any remaining $var strings in list-shaped outputs. The
            # Rust engine resolves scalars and FOREACH bodies, but some
            # LIST-constructed outputs (e.g. delegatie subject_ids) can still
            # carry unresolved $variable references.
            _postprocess_outputs(outputs, params)

            # Determine requirements_met from voldoet_aan_voorwaarden.
            _MISSING = object()
            voldoet = outputs.pop("voldoet_aan_voorwaarden", _MISSING)
            req_met = bool(outputs) if voldoet is _MISSING else voldoet is True

            if not req_met and voldoet is not _MISSING:
                outputs = {}

            # Log the Rust engine trace tree as DEBUG output
            if trace_json:
                _log_trace(json.loads(trace_json))

            for name, val in outputs.items():
                logger.debug("Output: %s = %s", name, val)
            logger.debug("Requirements met: %s", req_met)

            return RuleResult(
                output=outputs,
                requirements_met=req_met,
                input=params,
                rulespec_uuid=rule.uuid,
                path=json.loads(trace_json) if trace_json else None,
                missing_required=False,
            )


def _log_trace(node: dict, depth: int = 0) -> None:
    """Recursively log a Rust engine trace tree via the IndentLogger.

    Early-exits when the underlying logger is not at DEBUG level — walking
    a multi-thousand-node trace and formatting strings we'll throw away is
    one of the biggest time sinks in the Python wrapper (300ms+ per eval).
    """
    if not logger._logger.isEnabledFor(logging.DEBUG):
        return

    name = node.get("name", "?")
    ntype = node.get("node_type", "?")
    result = node.get("result")
    rtype = node.get("resolve_type")
    msg = node.get("message")

    label = f"{ntype}: {name}"
    if rtype:
        label += f" [{rtype}]"
    if result is not None:
        label += f" = {result}"
    if msg and msg != name:
        label += f" ({msg})"

    logger.debug(label)

    for child in node.get("children", []):
        with logger.indent_block(None):
            _log_trace(child, depth + 1)


def _resolve_temporal_reference(ref: str, reference_date: str) -> str:
    """Resolve a ``$prev_january_first``-style temporal reference to a date.

    Used by the Python pre-resolution path for cross-law inputs whose
    ``temporal.reference`` demands a shifted evaluation date. The Rust
    engine has its own equivalent for its native cross-law path.
    """
    from datetime import datetime as _dt

    if not isinstance(ref, str) or not ref.startswith("$"):
        return reference_date
    name = ref[1:]
    try:
        dt = _dt.strptime(reference_date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return reference_date
    if name == "prev_january_first":
        return dt.replace(month=1, day=1, year=dt.year - 1).isoformat()
    if name == "january_first":
        return dt.replace(month=1, day=1).isoformat()
    return reference_date


def _postprocess_outputs(outputs: dict, params: dict) -> None:
    """Resolve remaining ``$variable`` strings in engine outputs.

    The Rust engine resolves most scalars and FOREACH bodies natively, but
    some LIST-constructed outputs still carry unresolved ``$var`` entries
    that reference either a parameter or a sibling output (e.g. delegatie
    ``permissions: ['$base_permissions']`` referencing the ``base_permissions``
    output). This walks the output dict and substitutes from both scopes,
    iterating until no more substitutions happen (for chains of references).
    """

    def _ns() -> dict:
        return {**params, **outputs}

    def _resolve(v: Any, ns: dict) -> Any:
        if isinstance(v, list):
            return [_resolve(item, ns) for item in v]
        if isinstance(v, dict):
            return {k: _resolve(val, ns) for k, val in v.items()}
        if isinstance(v, str) and v.startswith("$"):
            name = v[1:]
            if "." in name:
                var, _, field = name.partition(".")
                obj = ns.get(var)
                if isinstance(obj, dict):
                    return obj.get(field, v)
            return ns.get(name, v)
        return v

    # Iterate because a resolved value may itself reference another output.
    for _ in range(5):
        changed = False
        ns = _ns()
        for key in list(outputs.keys()):
            new = _resolve(outputs[key], ns)
            if new != outputs[key]:
                outputs[key] = new
                changed = True
        if not changed:
            break


def _fill_input_defaults(data: dict, params: dict) -> None:
    """Type-default optional inputs that remained unresolved.

    The Rust engine does most of this natively (regelrecht commit 39998b6),
    but a few corner cases (cross-law nulls, data source non-matches
    involving object/array types) still need a Python pre-fill to avoid
    TypeMismatch on downstream arithmetic. Required inputs are left alone
    so the engine can still report ``missing_required``.
    """
    _TYPE_DEFAULTS: dict[str, Any] = {
        "number": 0,
        "amount": 0,
        "boolean": False,
        "string": "",
        "date": "2000-01-01",
        "array": [],
        "object": {},
    }
    for art in data.get("articles", []):
        for inp in art.get("machine_readable", {}).get("execution", {}).get("input", []):
            name = inp.get("name", "")
            if not name or name in params or inp.get("required"):
                continue
            source = inp.get("source")
            if not isinstance(source, dict):
                continue
            is_cross_law = bool(source.get("regulation"))
            is_data_source = source == {} or any(k in source for k in ("table", "field", "fields", "select_on"))
            if not (is_cross_law or is_data_source):
                continue
            input_type = inp.get("type", "string")
            # Leave string/date cross-law nulls intact so IS_NULL checks work.
            if is_cross_law and input_type in ("string", "date"):
                continue
            params[name] = _TYPE_DEFAULTS.get(input_type, "")


def _find_missing_required_inputs(data: dict, params: dict) -> list[str]:
    """Find required source: {} or source: {source_type: claim} inputs that are unresolved.

    Returns the list of missing input names. These are typically claim-based
    inputs that must be supplied by the citizen before evaluation can proceed.
    """
    missing = []
    for art in data.get("articles", []):
        for inp in art.get("machine_readable", {}).get("execution", {}).get("input", []):
            name = inp.get("name", "")
            source = inp.get("source")
            if not (name and inp.get("required") and name not in params):
                continue
            # Original v0.5.1 form: empty source: {}
            if source == {}:
                missing.append(name)
                continue
            # Migrated form: source: {source_type: claim}
            if isinstance(source, dict) and source.get("source_type") == "claim":
                missing.append(name)
    return missing


def _build_input_mapping_from_yaml(data: dict) -> dict[str, dict]:
    """Build per-law input→{table, field, select_on, fields} mapping from YAML.

    Reads the inline source metadata on each input in the law's articles.
    Only inputs with ``source.table`` (or an empty ``source: {}``) are included.
    Cross-law (``source.regulation``) and claim (``source.source_type``) inputs
    are skipped.
    """
    result: dict[str, dict] = {}
    for art in data.get("articles", []):
        for inp in art.get("machine_readable", {}).get("execution", {}).get("input", []):
            name = inp.get("name", "")
            source = inp.get("source")
            if not name or not isinstance(source, dict):
                continue
            if source.get("regulation") or source.get("source_type") == "claim":
                continue
            if not source.get("table"):
                continue
            entry: dict = {"table": source["table"]}
            if "field" in source:
                entry["field"] = source["field"]
            if "fields" in source:
                entry["fields"] = source["fields"]
            if "select_on" in source:
                entry["select_on"] = source["select_on"]
            result[name] = entry
    return result


def _maybe_parse_json(val: Any) -> Any:
    """Parse a string as JSON if it looks like a JSON array or object.

    DataFrame columns sometimes store complex values as JSON strings
    (e.g. kinderen: '[{"bsn": "111111111"}]'). When these are used as
    array or object inputs, they need to be parsed into native Python types.
    """
    if isinstance(val, str) and val and val[0] in ("[", "{"):
        try:
            return json.loads(val)
        except (json.JSONDecodeError, ValueError):
            pass
    return val


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
