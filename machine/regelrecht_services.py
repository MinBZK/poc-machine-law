"""Wrapper around Services that delegates evaluation to the regelrecht CLI engine.

This module provides a drop-in replacement for Services that can be used in BDD tests
to run evaluations through the regelrecht Rust binary instead of the Python engine.
Case management, claim management, and source data operations are still handled by
the underlying Python Services instance.

The CLI binary cannot do DataFrame-based source lookups or resolve cross-law
dependencies that require table access. To work around this, we pre-evaluate all
dependency laws using the Python engine and strip source references from the YAML
before sending it to the CLI, passing all resolved values as params.

The CLI does not enforce requirements blocks. The YAML files now contain a
`voldoet_aan_voorwaarden` boolean output action that models requirements as
explicit computed output, but the Python engine is still used for requirements_met
evaluation in the adapter to ensure correctness.
"""

import json
import logging
import os
import subprocess
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
import yaml

from machine.context import PathNode, TypeSpec
from machine.service import RuleResult, Services
from machine.utils import RuleResolver

logger = logging.getLogger(__name__)

DEFAULT_BINARY_PATH = "bin/evaluate-v0.2.0"


class RegelrechtServices:
    """Wrapper around Services that delegates evaluate() to the regelrecht CLI."""

    def __init__(self, reference_date: str, binary_path: str | None = None) -> None:
        self._services = Services(reference_date)
        self.binary_path = binary_path or os.environ.get("REGELRECHT_BINARY", DEFAULT_BINARY_PATH)
        self.resolver: RuleResolver = self._services.resolver
        self.root_reference_date = reference_date

    @property
    def services(self) -> dict:
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

    def set_source_dataframe(self, service: str, table: str, df: pd.DataFrame) -> None:
        self._services.set_source_dataframe(service, table, df)

    def get_discoverable_service_laws(self, discoverable_by: str = "CITIZEN") -> dict[str, list[str]]:
        return self._services.get_discoverable_service_laws(discoverable_by)

    def get_service_laws(self):
        return self._services.resolver.get_service_laws()

    def get_law(self, service: str, law: str, reference_date: str | None = None) -> dict[str, Any] | None:
        return self._services.get_law(service, law, reference_date)

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
        """Evaluate using the regelrecht CLI instead of the Python engine.

        Strategy:
        1. Pre-evaluate all dependency laws (source.regulation references)
           using the Python engine to get their output values, respecting
           temporal references on input specs.
        2. Pre-resolve source_reference fields from DataFrames.
        3. Strip all source/source_reference from the main YAML so the CLI
           doesn't try to resolve cross-law references.
        4. Pass the stripped YAML and all pre-resolved values as params to the CLI.
        5. Use the Python engine to evaluate requirements (the CLI ignores them).
        """
        reference_date = reference_date or self.root_reference_date

        rule = self.resolver.find_rule(law, reference_date, service)
        if not rule:
            raise ValueError(f"No rule found for {law} at {reference_date}")

        with open(rule.path) as f:
            yaml_content = f.read()

        parsed_yaml = yaml.safe_load(yaml_content)

        # Build params from parameters
        params = dict(parameters)

        # Inject overwrite_input values as params
        if overwrite_input:
            for section_values in overwrite_input.values():
                if isinstance(section_values, dict):
                    params.update(section_values)

        # Pre-evaluate ALL dependency laws using the Python engine
        dep_outputs = self._pre_evaluate_dependencies(
            parsed_yaml, reference_date, parameters, overwrite_input, approved
        )
        params.update(dep_outputs)

        # Pre-resolve source_reference fields from DataFrames
        source_ref_outputs = self._pre_resolve_source_references(parsed_yaml, params)
        params.update(source_ref_outputs)

        # Strip source references so the CLI uses params for all input values
        stripped_yaml = _strip_all_sources(yaml_content)

        # Get output field names from the original YAML spec
        output_names = _get_output_names(parsed_yaml)

        if requested_output:
            output_names = [requested_output]

        # Call CLI for each output field and merge results
        merged_outputs: dict[str, Any] = {}
        merged_resolved_inputs: dict[str, Any] = {}
        last_uuid = rule.uuid

        for output_name in output_names:
            cli_result = self._call_cli(
                yaml_content=stripped_yaml,
                output_name=output_name,
                params=params,
                reference_date=reference_date,
            )

            if "error" in cli_result:
                error_msg = cli_result["error"]
                logger.warning("Regelrecht CLI error for %s/%s: %s", law, output_name, error_msg)
                continue

            merged_outputs.update(cli_result.get("outputs", {}))
            merged_resolved_inputs.update(cli_result.get("resolved_inputs", {}))

            if "law_uuid" in cli_result:
                last_uuid = cli_result["law_uuid"]

        # Detect unevaluated CLI outputs (e.g. FOREACH operations returned as dicts).
        # Remove them so the Python fallback can fill them in.
        unevaluated_keys = [k for k, v in merged_outputs.items() if isinstance(v, dict) and "operation" in v]
        for k in unevaluated_keys:
            logger.debug("CLI returned unevaluated operation for %s/%s, will use Python fallback", law, k)
            del merged_outputs[k]

        # Strip voldoet_aan_voorwaarden from CLI outputs — the Python engine
        # handles requirements evaluation via the reconstructed requirements list.
        merged_outputs.pop("voldoet_aan_voorwaarden", None)

        # The CLI does not enforce requirements blocks, so we evaluate them
        # using the Python engine to get the correct requirements_met flag.
        py_result = self._evaluate_requirements_via_python(
            service=service,
            law=law,
            parameters=parameters,
            reference_date=reference_date,
            overwrite_input=overwrite_input,
            overwrite_definitions=overwrite_definitions,
            requested_output=requested_output,
            approved=approved,
        )

        requirements_met = py_result.requirements_met
        missing_required = py_result.missing_required

        # When requirements are not met, clear outputs (Python engine would not produce them)
        if not requirements_met:
            merged_outputs = {}
        elif py_result.output:
            if not merged_outputs:
                # CLI produced no outputs at all. Fall back to Python engine outputs.
                merged_outputs = py_result.output
                merged_resolved_inputs = py_result.input
            else:
                # Fill in any outputs that the CLI couldn't evaluate (e.g. FOREACH)
                # with values from the Python engine.
                for key, value in py_result.output.items():
                    if key not in merged_outputs:
                        logger.debug("Using Python fallback for output %s/%s", law, key)
                        merged_outputs[key] = value

        # Enforce output type specs (precision, min/max, eurocent conversion)
        # to match the Python engine behaviour.
        output_specs = _build_output_specs(parsed_yaml)
        for key in list(merged_outputs.keys()):
            if key in output_specs:
                merged_outputs[key] = output_specs[key].enforce(merged_outputs[key])

        return RuleResult(
            output=merged_outputs,
            requirements_met=requirements_met,
            input=merged_resolved_inputs,
            rulespec_uuid=last_uuid,
            path=PathNode(type="root", name="regelrecht", result=None),
            missing_required=missing_required,
        )

    def apply_rules(self, event) -> None:
        return self._services.apply_rules(event)

    # ---- Dependency pre-evaluation via Python engine ----

    def _pre_evaluate_dependencies(
        self,
        parsed_yaml: dict,
        reference_date: str,
        parameters: dict[str, Any],
        overwrite_input: dict[str, Any] | None,
        approved: bool,
    ) -> dict[str, Any]:
        """Pre-evaluate dependency laws using the Python engine.

        Walks the main law's input fields looking for source.regulation references,
        evaluates each referenced law, and maps the output to the input name
        expected by the main law. Respects temporal references on input specs
        to adjust the reference_date for dependency evaluations.
        """
        resolved: dict[str, Any] = {}

        for article in parsed_yaml.get("articles", []):
            mr = article.get("machine_readable", {})
            execution = mr.get("execution", {})
            for inp in execution.get("input", []):
                input_name = inp.get("name")
                source = inp.get("source", {})
                if not source or not input_name:
                    continue

                regulation = source.get("regulation")
                output_name = source.get("output")
                dep_service = source.get("service")
                if not regulation or not output_name:
                    continue

                if input_name in resolved:
                    continue

                # Resolve temporal reference to adjust the reference_date
                dep_reference_date = _resolve_temporal_reference(inp, reference_date)

                try:
                    dep_result = self._services.evaluate(
                        service=dep_service or "UNKNOWN",
                        law=regulation,
                        parameters=parameters,
                        reference_date=dep_reference_date,
                        overwrite_input=overwrite_input,
                        requested_output=output_name,
                        approved=approved,
                    )
                    if dep_result and dep_result.output:
                        value = dep_result.output.get(output_name)
                        if value is not None:
                            resolved[input_name] = value
                except Exception as e:
                    logger.debug(
                        "Failed to pre-evaluate dependency %s/%s: %s",
                        regulation,
                        output_name,
                        e,
                    )

        return resolved

    # ---- Source reference pre-resolution from DataFrames ----

    def _pre_resolve_source_references(
        self,
        parsed_yaml: dict,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Pre-resolve source_reference fields from services' DataFrames.

        The CLI cannot do DataFrame-based lookups, so we resolve table-based
        input fields here and inject the results as params.
        """
        resolved: dict[str, Any] = {}

        for article in parsed_yaml.get("articles", []):
            mr = article.get("machine_readable", {})
            execution = mr.get("execution", {})
            for inp in execution.get("input", []):
                name = inp.get("name")
                source_ref = inp.get("source_reference")
                if not name or not source_ref:
                    continue

                # Skip if we already have this value in params
                if name in params:
                    continue

                table_name = source_ref.get("table", "")
                field = source_ref.get("field", name)
                fields = source_ref.get("fields")
                select_on = source_ref.get("select_on", [])
                input_type = inp.get("type", "")

                df = self._find_dataframe(table_name)
                if df is None:
                    continue

                # Array types: return all matching rows as list of dicts
                if input_type == "array":
                    value = _lookup_in_dataframe_array(df, fields or ([field] if field else []), select_on, params)
                else:
                    value = _lookup_in_dataframe(df, field, fields, select_on, params)

                if value is not None:
                    resolved[name] = value

        return resolved

    def _find_dataframe(self, table_name: str) -> pd.DataFrame | None:
        """Find a DataFrame by table name across all services."""
        for service in self._services.services.values():
            if table_name in service.source_dataframes:
                return service.source_dataframes[table_name]
        return None

    # ---- Requirements evaluation via Python engine ----

    def _evaluate_requirements_via_python(
        self,
        service: str,
        law: str,
        parameters: dict[str, Any],
        reference_date: str,
        overwrite_input: dict[str, Any] | None,
        overwrite_definitions: dict[str, Any] | None,
        requested_output: str | None,
        approved: bool,
    ) -> RuleResult:
        """Use the Python engine to evaluate requirements_met and missing_required.

        The CLI does not enforce requirement blocks, so we run the Python engine
        for the same inputs and use its requirements_met / missing_required flags.
        """
        try:
            return self._services.evaluate(
                service=service,
                law=law,
                parameters=parameters,
                reference_date=reference_date,
                overwrite_input=overwrite_input,
                overwrite_definitions=overwrite_definitions,
                requested_output=requested_output,
                approved=approved,
            )
        except Exception as e:
            logger.debug("Failed to evaluate requirements via Python engine: %s", e)
            return RuleResult(
                output={},
                requirements_met=False,
                input={},
                rulespec_uuid="",
                path=None,
                missing_required=True,
            )

    # ---- CLI interaction ----

    def _call_cli(
        self,
        yaml_content: str,
        output_name: str,
        params: dict[str, Any],
        reference_date: str,
    ) -> dict[str, Any]:
        """Call the regelrecht CLI binary and return parsed JSON response."""
        cli_input = {
            "law_yaml": yaml_content,
            "output_name": output_name,
            "params": _convert_to_native(params),
            "date": reference_date,
            "extra_laws": [],
        }

        try:
            proc = subprocess.run(
                [self.binary_path],
                input=json.dumps(cli_input),
                capture_output=True,
                text=True,
                timeout=30,
            )
        except FileNotFoundError:
            logger.error("Regelrecht binary not found at %s", self.binary_path)
            return {"error": f"Binary not found: {self.binary_path}"}
        except subprocess.TimeoutExpired:
            logger.error("Regelrecht CLI timed out after 30s")
            return {"error": "CLI timeout"}

        if proc.returncode != 0:
            stderr = proc.stderr.strip() if proc.stderr else "unknown error"
            logger.error("Regelrecht CLI exited with code %d: %s", proc.returncode, stderr)
            if proc.stdout and proc.stdout.strip():
                try:
                    return json.loads(proc.stdout)
                except json.JSONDecodeError:
                    pass
            return {"error": f"CLI error (exit {proc.returncode}): {stderr}"}

        if not proc.stdout or not proc.stdout.strip():
            return {"error": "Empty response from CLI"}

        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse CLI output as JSON: %s", e)
            return {"error": f"Invalid JSON from CLI: {e}"}


# ---- Module-level helpers ----


def _resolve_temporal_reference(input_spec: dict, reference_date: str) -> str:
    """Resolve temporal reference on an input spec to get the adjusted reference_date.

    For example, if the input has temporal.reference = $prev_january_first and the
    reference_date is 2025-02-01, the resolved date is 2024-01-01.
    """
    temporal = input_spec.get("temporal", {})
    ref = temporal.get("reference")
    if not ref or not isinstance(ref, str) or not ref.startswith("$"):
        return reference_date

    ref_name = ref[1:]
    calc_date = datetime.strptime(reference_date, "%Y-%m-%d").date()

    if ref_name == "prev_january_first":
        return calc_date.replace(month=1, day=1, year=calc_date.year - 1).isoformat()
    elif ref_name == "january_first":
        return calc_date.replace(month=1, day=1).isoformat()
    elif ref_name in ("calculation_date", "year"):
        return reference_date

    return reference_date


def _lookup_in_dataframe(
    df: pd.DataFrame,
    field: str | None,
    fields: list[str] | None,
    select_on: list[dict] | dict,
    params: dict[str, Any],
) -> Any:
    """Look up a value in a DataFrame using select_on criteria.

    Handles both list-of-dicts (v0.5.0 source_reference) and dict (legacy) select_on formats.
    """
    if df.empty:
        return None

    filtered = df

    # Normalize select_on to list-of-dicts format
    if isinstance(select_on, dict):
        select_on_items = [{"name": k, "value": v} for k, v in select_on.items()]
    else:
        select_on_items = select_on

    for criterion in select_on_items:
        col = criterion.get("name")
        ref = criterion.get("value")
        if not col or col not in filtered.columns:
            return None

        # Resolve parameter references like $BSN
        if isinstance(ref, str) and ref.startswith("$"):
            param_name = ref[1:]
            # Handle dotted paths like $ADRES.postcode
            if "." in param_name:
                parts = param_name.split(".", 1)
                parent = params.get(parts[0])
                ref_value = parent.get(parts[1]) if isinstance(parent, dict) else None
            else:
                ref_value = params.get(param_name)
            if ref_value is None:
                return None
        else:
            ref_value = ref

        filtered = filtered[filtered[col] == ref_value]

    if filtered.empty:
        return None

    # Multi-field lookup: return a dict of field values
    if fields:
        row = filtered.iloc[0]
        result = {}
        for f in fields:
            if f in filtered.columns:
                result[f] = row[f]
        return result if result else None

    # Single field lookup
    if field and field in filtered.columns:
        return filtered.iloc[0][field]

    return None


def _convert_to_native(obj: Any) -> Any:
    """Recursively convert numpy/pandas types to native Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _convert_to_native(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_to_native(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if pd.isna(obj) if isinstance(obj, float) else False:
        return None
    return obj


def _lookup_in_dataframe_array(
    df: pd.DataFrame,
    fields: list[str],
    select_on: list[dict] | dict,
    params: dict[str, Any],
) -> list[dict[str, Any]] | None:
    """Look up all matching rows in a DataFrame, returning a list of dicts.

    Used for array-type inputs where multiple rows may match the select criteria.
    """
    if df.empty:
        return None

    filtered = df

    # Normalize select_on to list-of-dicts format
    if isinstance(select_on, dict):
        select_on_items = [{"name": k, "value": v} for k, v in select_on.items()]
    else:
        select_on_items = select_on

    for criterion in select_on_items:
        col = criterion.get("name")
        ref = criterion.get("value")
        if not col or col not in filtered.columns:
            return None

        if isinstance(ref, str) and ref.startswith("$"):
            param_name = ref[1:]
            if "." in param_name:
                parts = param_name.split(".", 1)
                parent = params.get(parts[0])
                ref_value = parent.get(parts[1]) if isinstance(parent, dict) else None
            else:
                ref_value = params.get(param_name)
            if ref_value is None:
                return None
        else:
            ref_value = ref

        filtered = filtered[filtered[col] == ref_value]

    if filtered.empty:
        return None

    # Determine which columns to include
    available_fields = [f for f in fields if f in filtered.columns]
    if not available_fields:
        # If none of the requested fields exist, use all columns
        available_fields = list(filtered.columns)

    rows = []
    for _, row in filtered.iterrows():
        row_dict = {}
        for f in available_fields:
            val = row[f]
            # Convert numpy types to native Python types
            if isinstance(val, (np.integer,)):
                val = int(val)
            elif isinstance(val, (np.floating,)):
                val = float(val)
            elif isinstance(val, (np.bool_,)):
                val = bool(val)
            elif pd.isna(val) if isinstance(val, float) else False:
                val = None
            row_dict[f] = val
        rows.append(row_dict)

    return rows if rows else None


def _strip_all_sources(yaml_content: str) -> str:
    """Remove source and source_reference entries from all input fields.

    The CLI gets all resolved values via params, so it doesn't need to resolve
    cross-law references or DataFrame lookups.
    """
    data = yaml.safe_load(yaml_content)
    changed = False
    for article in data.get("articles", []):
        mr = article.get("machine_readable", {})
        execution = mr.get("execution", {})
        for inp in execution.get("input", []):
            if "source" in inp:
                del inp["source"]
                changed = True
            if "source_reference" in inp:
                del inp["source_reference"]
                changed = True
    if changed:
        return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return yaml_content


def _get_output_names(data: dict) -> list[str]:
    """Extract output field names from the parsed YAML data."""
    names: list[str] = []
    for article in data.get("articles", []):
        mr = article.get("machine_readable", {})
        execution = mr.get("execution", {})
        for out in execution.get("output", []):
            name = out.get("name")
            if name and name not in names:
                names.append(name)
    return names


def _build_output_specs(data: dict) -> dict[str, TypeSpec]:
    """Build mapping of output names to their TypeSpec from parsed YAML.

    This mirrors RuleEngine._build_output_specs so the regelrecht wrapper
    can enforce the same precision/min/max/eurocent constraints.
    """
    specs: dict[str, TypeSpec] = {}
    for article in data.get("articles", []):
        mr = article.get("machine_readable", {})
        execution = mr.get("execution", {})
        for out in execution.get("output", []):
            name = out.get("name")
            if name:
                ts = out.get("type_spec", {})
                specs[name] = TypeSpec(
                    type=out.get("type"),
                    unit=ts.get("unit"),
                    precision=ts.get("precision"),
                    min=ts.get("min"),
                    max=ts.get("max"),
                )
    return specs
