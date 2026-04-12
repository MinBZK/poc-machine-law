"""Web adapter that delegates rule evaluation to RegelrechtServices.

RegelrechtServices wraps the regelrecht Rust engine via PyO3 and handles all
cross-law resolution, data source pre-resolution, and post-processing. This
adapter is a thin shim that bridges the web EngineInterface contract.
"""

import logging
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from fastapi import HTTPException

from machine.profile_loader import get_project_root, load_profiles_from_yaml
from machine.regelrecht_services import RegelrechtServices
from machine.utils import RuleResolver

from ..engine_interface import EngineInterface, PathNode, RuleResult

logger = logging.getLogger(__name__)


class RegelrechtMachineService(EngineInterface):
    """EngineInterface implementation backed by RegelrechtServices (PyO3)."""

    def __init__(self, services: RegelrechtServices):
        self.services = services
        self.resolver: RuleResolver = services.resolver

    def get_services(self) -> RegelrechtServices | None:
        return self.services

    def get_profile_data(self, bsn: str, effective_date: date | None = None) -> dict[str, Any]:
        return self.get_all_profiles().get(bsn)

    def get_all_profiles(self, effective_date: date | None = None) -> dict[str, dict[str, Any]]:
        profiles_path = get_project_root() / "data" / "profiles.yaml"
        return load_profiles_from_yaml(profiles_path)

    def get_business_profile(self, kvk_nummer: str) -> dict[str, Any] | None:
        kvk_service = self.services.services.get("KVK")
        if not kvk_service or "inschrijvingen" not in kvk_service.source_dataframes:
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
        rule = self.resolver.find_rule(law, reference_date or "", service)
        if not rule:
            raise HTTPException(status_code=400, detail=f"No rule found for {law} at {reference_date}")

        result = self.services.evaluate(
            service=service,
            law=law,
            parameters=parameters,
            reference_date=reference_date,
            overwrite_input=overwrite_input,
            requested_output=requested_output,
            approved=approved,
        )

        # Convert the Rust engine trace tree to a web PathNode tree. Pass
        # the YAML input specs so the converter can label each resolve with
        # its semantic source (SERVICE for cross-law, SOURCE for data source,
        # CLAIM for claim-store).
        input_specs = _collect_input_specs(rule.path)
        root = (
            _rust_trace_to_pathnode(result.path, input_specs)
            if result.path
            else PathNode(type="root", name="evaluation", result=None)
        )

        return RuleResult(
            output=dict(result.output),
            requirements_met=result.requirements_met,
            input=dict(result.input),
            rulespec_uuid=result.rulespec_uuid,
            path=root,
            missing_required=result.missing_required,
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

        return {svc: [law for law in laws if FeatureFlags.is_law_enabled(svc, law)] for svc, laws in all_laws.items()}

    def set_source_dataframe(self, service: str, table: str, df: pd.DataFrame) -> None:
        self.services.set_source_dataframe(service, table, df)

    def reset(self) -> None:
        import os
        import sys

        os.execl(sys.executable, sys.executable, *sys.argv)


def _collect_input_specs(yaml_path: str) -> dict[str, dict[str, Any]]:
    """Return ``{input_name: spec}`` for every input declared by the law."""
    try:
        data = yaml.safe_load(Path(yaml_path).read_text())
    except Exception as exc:
        logger.warning("Could not read YAML for input specs %s: %s", yaml_path, exc)
        return {}
    if not isinstance(data, dict):
        return {}
    specs: dict[str, dict[str, Any]] = {}
    for article in data.get("articles", []):
        execution = article.get("machine_readable", {}).get("execution", {})
        for inp in execution.get("input", []):
            name = inp.get("name")
            if name:
                specs[name] = inp
    return specs


def _classify_input(spec: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Classify a YAML input spec into ``(resolve_type, details)``.

    ``resolve_type`` is one of ``SERVICE`` (cross-law reference), ``SOURCE``
    (data source lookup), ``CLAIM`` (citizen-supplied), or ``NONE`` (direct
    parameter). The ``details`` dict carries the metadata the render_path
    template needs (type, type_spec, and for cross-law refs the source law).
    """
    details: dict[str, Any] = {
        "type": spec.get("type"),
        "type_spec": spec.get("type_spec"),
    }
    source = spec.get("source")
    if not isinstance(source, dict):
        return "NONE", details
    if source.get("regulation"):
        details["service"] = source.get("service")
        details["law"] = source.get("regulation")
        return "SERVICE", details
    if source.get("source_type") == "claim":
        return "CLAIM", details
    if any(k in source for k in ("table", "field", "fields", "select_on")):
        details["table"] = source.get("table")
        return "SOURCE", details
    return "NONE", details


def _rust_trace_to_pathnode(trace: dict, input_specs: dict[str, dict[str, Any]]) -> PathNode:
    """Convert a Rust engine trace tree into a web PathNode tree.

    The Rust trace contains every operation (AND, IF, SUBTRACT, ...) as
    nested nodes. The dashboard template ``render_path`` only wants the
    law's *resolved inputs* — the values that flowed in from cross-law
    references, data sources, and claims. We walk the trace to collect
    each declared input's resolved value, then classify it by its YAML
    source block so the UI can label the origin.
    """
    root = PathNode(type="root", name="evaluation", result=None)
    resolved_values: dict[str, Any] = {}

    def _walk(node: dict) -> None:
        if not isinstance(node, dict):
            return
        if node.get("node_type") == "resolve":
            name = node.get("name", "")
            if name in input_specs and name not in resolved_values:
                resolved_values[name] = node.get("result")
        for child in node.get("children", []):
            _walk(child)

    _walk(trace)

    for name, spec in input_specs.items():
        if name not in resolved_values:
            continue
        resolve_type, details = _classify_input(spec)
        details["path"] = f"${name}"
        root.children.append(
            PathNode(
                type="resolve",
                name=name,
                result=resolved_values[name],
                resolve_type=resolve_type,
                required=bool(spec.get("required", False)),
                details=details,
            )
        )
    return root
