import json
import logging
import os
import subprocess
from datetime import date, datetime
from typing import Any

import pandas as pd
import yaml
from fastapi import HTTPException

from machine.profile_loader import get_project_root, load_profiles_from_yaml
from machine.service import Services
from machine.utils import RuleResolver

from ..engine_interface import EngineInterface, PathNode, RuleResult

logger = logging.getLogger(__name__)

DEFAULT_BINARY_PATH = "bin/evaluate-v0.2.0"


class RegelrechtMachineService(EngineInterface):
    """
    Implementation of EngineInterface that calls the regelrecht Rust engine CLI binary.

    The binary reads JSON from stdin and returns JSON on stdout. This adapter
    translates between the web engine interface and the CLI protocol.
    """

    def __init__(self, binary_path: str | None = None, services: Services | None = None):
        self.binary_path = binary_path or os.environ.get("REGELRECHT_BINARY", DEFAULT_BINARY_PATH)
        self.services = services
        self.resolver = services.resolver if services else RuleResolver()

    def get_services(self) -> Services | None:
        return self.services

    def get_profile_data(self, bsn: str, effective_date: date | None = None) -> dict[str, Any]:
        profiles = self.get_all_profiles()
        return profiles.get(bsn)

    def get_all_profiles(self, effective_date: date | None = None) -> dict[str, dict[str, Any]]:
        project_root = get_project_root()
        profiles_path = project_root / "data" / "profiles.yaml"
        return load_profiles_from_yaml(profiles_path)

    def get_business_profile(self, kvk_nummer: str) -> dict[str, Any] | None:
        if not self.services or "KVK" not in self.services.services:
            return None

        kvk_service = self.services.services["KVK"]
        if "inschrijvingen" not in kvk_service.source_dataframes:
            return None

        df = kvk_service.source_dataframes["inschrijvingen"]
        matches = df[df["kvk_nummer"] == kvk_nummer]

        if matches.empty:
            return None

        row = matches.iloc[0]
        return {
            "kvk_nummer": row.get("kvk_nummer"),
            "handelsnaam": row.get("handelsnaam"),
            "rechtsvorm": row.get("rechtsvorm"),
            "activiteit": row.get("activiteit"),
            "status": row.get("status"),
        }

    def evaluate(
        self,
        service: str,
        law: str,
        parameters: dict[str, Any],
        reference_date: str | None = None,
        effective_date: str | None = None,
        overwrite_input: dict[str, Any] | None = None,
        requested_output: str | None = None,
        approved: bool = False,
    ) -> RuleResult:
        reference_date = reference_date or datetime.today().strftime("%Y-%m-%d")

        # Find the rule spec to get the YAML file path
        rule = self.resolver.find_rule(law, reference_date, service)
        if not rule:
            raise HTTPException(status_code=400, detail=f"No rule found for {law} at {reference_date}")

        # Read raw YAML content
        with open(rule.path) as f:
            yaml_content = f.read()

        # Collect cross-law dependencies
        extra_laws = self._collect_extra_laws(yaml_content, reference_date)

        # Build params dict from parameters
        params = dict(parameters)

        # Inject overwrite_input values as params
        if overwrite_input:
            for section_values in overwrite_input.values():
                if isinstance(section_values, dict):
                    params.update(section_values)

        # Pre-resolve source_reference fields from services' DataFrames
        source_params = self._pre_resolve_sources(yaml_content, params)
        params.update(source_params)

        # Get output field names from the YAML spec
        parsed_yaml = yaml.safe_load(yaml_content)
        output_names = self._get_output_names(parsed_yaml)

        if requested_output:
            output_names = [requested_output]

        # Call CLI for each output field and merge results
        merged_outputs = {}
        merged_resolved_inputs = {}
        last_uuid = rule.uuid
        had_error = False
        missing_required = False

        for output_name in output_names:
            cli_result = self._call_cli(
                yaml_content=yaml_content,
                output_name=output_name,
                params=params,
                reference_date=reference_date,
                extra_laws=extra_laws,
            )

            if "error" in cli_result:
                error_msg = cli_result["error"]
                logger.warning(f"Regelrecht CLI error for {law}/{output_name}: {error_msg}")
                if "missing" in error_msg.lower() or "variable" in error_msg.lower():
                    missing_required = True
                had_error = True
                continue

            # Merge outputs
            outputs = cli_result.get("outputs", {})
            merged_outputs.update(outputs)

            # Merge resolved inputs
            resolved = cli_result.get("resolved_inputs", {})
            merged_resolved_inputs.update(resolved)

            # Capture UUID from response
            if "law_uuid" in cli_result:
                last_uuid = cli_result["law_uuid"]

        # Build enriched output: match what PythonMachineService produces
        # The Python engine returns {name: raw_value} in RuleResult.output
        enriched_output = {}
        for name, value in merged_outputs.items():
            enriched_output[name] = value

        requirements_met = bool(merged_outputs) and not had_error

        return RuleResult(
            output=enriched_output,
            requirements_met=requirements_met,
            input=merged_resolved_inputs,
            rulespec_uuid=last_uuid,
            path=PathNode(type="root", name="evaluation", result=None),
            missing_required=missing_required,
        )

    def get_rule_spec(self, law: str, reference_date: str, service: str) -> dict[str, Any]:
        return self.resolver.get_rule_spec(law, reference_date, service)

    def get_discoverable_service_laws(
        self, discoverable_by="CITIZEN", filter_disabled: bool = True
    ) -> dict[str, list[str]]:
        all_laws = self.resolver.get_discoverable_service_laws(discoverable_by)

        if not filter_disabled:
            return all_laws

        from web.feature_flags import FeatureFlags

        result = {}
        for svc, laws in all_laws.items():
            result[svc] = []
            for law in laws:
                if FeatureFlags.is_law_enabled(svc, law):
                    result[svc].append(law)

        return result

    def set_source_dataframe(self, service: str, table: str, df: pd.DataFrame) -> None:
        if self.services:
            self.services.set_source_dataframe(service, table, df)

    def reset(self) -> None:
        import os
        import sys

        os.execl(sys.executable, sys.executable, *sys.argv)

    # ---- CLI interaction ----

    def _call_cli(
        self,
        yaml_content: str,
        output_name: str,
        params: dict[str, Any],
        reference_date: str,
        extra_laws: list[str],
    ) -> dict[str, Any]:
        """Call the regelrecht CLI binary and return parsed JSON response."""
        cli_input = {
            "law_yaml": yaml_content,
            "output_name": output_name,
            "params": params,
            "date": reference_date,
            "extra_laws": extra_laws,
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
            logger.error(f"Regelrecht binary not found at {self.binary_path}")
            return {"error": f"Binary not found: {self.binary_path}"}
        except subprocess.TimeoutExpired:
            logger.error("Regelrecht CLI timed out after 30s")
            return {"error": "CLI timeout"}

        if proc.returncode != 0:
            stderr = proc.stderr.strip() if proc.stderr else "unknown error"
            logger.error(f"Regelrecht CLI exited with code {proc.returncode}: {stderr}")
            # Try to parse stdout anyway; some errors come as JSON on stdout
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
            logger.error(f"Failed to parse CLI output as JSON: {e}")
            return {"error": f"Invalid JSON from CLI: {e}"}

    # ---- Cross-law dependency collection ----

    def _collect_extra_laws(self, yaml_content: str, reference_date: str) -> list[str]:
        """Scan YAML for source.regulation references and collect those law YAML files.

        Recursively resolves dependencies so that transitive references are also included.
        """
        data = yaml.safe_load(yaml_content)
        regulations: set[str] = set()
        _find_regulations(data, regulations)

        extra_yamls: list[str] = []
        visited: set[str] = set()

        # Use a work queue for recursive resolution
        queue = list(regulations)
        while queue:
            reg = queue.pop()
            if reg in visited:
                continue
            visited.add(reg)

            try:
                rule = self.resolver.find_rule(reg, reference_date)
            except ValueError:
                logger.debug(f"Referenced law not found: {reg}")
                continue

            if not rule:
                continue

            with open(rule.path) as f:
                extra_yaml = f.read()

            extra_yamls.append(extra_yaml)

            # Scan this dependency for further references
            dep_data = yaml.safe_load(extra_yaml)
            dep_regulations: set[str] = set()
            _find_regulations(dep_data, dep_regulations)
            for dep_reg in dep_regulations:
                if dep_reg not in visited:
                    queue.append(dep_reg)

        return extra_yamls

    # ---- Source reference pre-resolution ----

    def _pre_resolve_sources(self, yaml_content: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """Pre-resolve source_reference fields from services' DataFrames.

        The regelrecht CLI does not support data source lookups, so we resolve
        table-based input fields here and inject the results as params.
        """
        if not self.services:
            return {}

        data = yaml.safe_load(yaml_content)
        resolved: dict[str, Any] = {}

        # Walk through all articles' input fields looking for source_reference patterns
        articles = data.get("articles", [])
        for article in articles:
            mr = article.get("machine_readable", {})
            execution = mr.get("execution", {})
            for inp in execution.get("input", []):
                name = inp.get("name")
                source = inp.get("source", {})
                if not name or not source:
                    continue

                # Detect table-lookup sources (they have table/select_on/fields/source_type markers)
                has_table_markers = any(k in source for k in ("select_on", "fields", "source_type", "table"))
                if not has_table_markers:
                    continue

                # Skip if we already have this value in params
                if name in parameters:
                    continue

                source_type = source.get("source_type", "")
                table_name = source.get("table", "")
                field = source.get("field", name)
                select_on = source.get("select_on", {})

                df = self._get_source_dataframe(source_type, table_name)
                if df is None:
                    continue

                value = self._lookup_in_dataframe(df, field, select_on, parameters)
                if value is not None:
                    resolved[name] = value

        return resolved

    def _get_source_dataframe(self, source_type: str, table_name: str) -> pd.DataFrame | None:
        """Get a DataFrame from the services' source data."""
        if not self.services:
            return None

        # Check if source_type is a service name
        if source_type in self.services.services:
            svc = self.services.services[source_type]
            if table_name in svc.source_dataframes:
                return svc.source_dataframes[table_name]

        # Check special source types
        if source_type == "laws":
            return self.resolver.rules_dataframe()
        elif source_type == "cases" and hasattr(self.services, "case_manager"):
            cases = self.services.case_manager.get_all_cases()
            if cases:
                return pd.DataFrame(
                    [
                        {
                            "case_id": str(case.id),
                            "bsn": case.bsn,
                            "service": case.service,
                            "law": case.law,
                            "status": case.status.value if hasattr(case.status, "value") else str(case.status),
                            "approved": case.approved,
                            "created_at": case.created_at,
                            "year": case.created_at.year if case.created_at else None,
                            **(case.parameters or {}),
                        }
                        for case in cases
                        if case is not None
                    ]
                )
        return None

    @staticmethod
    def _lookup_in_dataframe(
        df: pd.DataFrame,
        field: str,
        select_on: dict[str, Any],
        parameters: dict[str, Any],
    ) -> Any:
        """Look up a value in a DataFrame using select_on criteria."""
        if df.empty:
            return None

        filtered = df
        for col, ref in select_on.items():
            if col not in filtered.columns:
                return None
            # Resolve parameter references
            if isinstance(ref, str) and ref.startswith("$"):
                param_name = ref[1:]
                ref_value = parameters.get(param_name)
                if ref_value is None:
                    return None
            else:
                ref_value = ref
            filtered = filtered[filtered[col] == ref_value]

        if filtered.empty:
            return None

        if field in filtered.columns:
            return filtered.iloc[0][field]

        return None

    # ---- Output spec helpers ----

    @staticmethod
    def _get_output_names(data: dict) -> list[str]:
        """Extract output field names from the parsed YAML data."""
        names = []
        for article in data.get("articles", []):
            mr = article.get("machine_readable", {})
            execution = mr.get("execution", {})
            for out in execution.get("output", []):
                name = out.get("name")
                if name and name not in names:
                    names.append(name)
        return names

    @staticmethod
    def _get_output_specs(data: dict) -> dict[str, dict[str, Any]]:
        """Extract output specifications (type, description, type_spec) from the parsed YAML."""
        specs: dict[str, dict[str, Any]] = {}
        for article in data.get("articles", []):
            mr = article.get("machine_readable", {})
            execution = mr.get("execution", {})
            for out in execution.get("output", []):
                name = out.get("name")
                if name:
                    specs[name] = {
                        "type": out.get("type", "unknown"),
                        "description": out.get("description", ""),
                    }
                    if "type_spec" in out:
                        specs[name]["type_spec"] = out["type_spec"]
                    if "temporal" in out:
                        specs[name]["temporal"] = out["temporal"]
        return specs


def _find_regulations(data: Any, regulations: set[str]) -> None:
    """Recursively find all source.regulation references in a YAML structure."""
    if isinstance(data, dict):
        if "regulation" in data and isinstance(data["regulation"], str):
            regulations.add(data["regulation"])
        for value in data.values():
            _find_regulations(value, regulations)
    elif isinstance(data, list):
        for item in data:
            _find_regulations(item, regulations)
