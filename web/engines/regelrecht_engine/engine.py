"""Web adapter that delegates rule evaluation to RegelrechtServices.

RegelrechtServices wraps the regelrecht Rust engine via PyO3 and handles all
cross-law resolution, data source pre-resolution, and post-processing. This
adapter is a thin shim that bridges the web EngineInterface contract.
"""

import logging
from datetime import date
from typing import Any

import pandas as pd
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

        # Convert the Rust engine trace tree to a web PathNode tree.
        # The trace is a nested dict with node_type/name/result/resolve_type/children.
        root = (
            _rust_trace_to_pathnode(result.path)
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


def _rust_trace_to_pathnode(trace: dict) -> PathNode:
    """Convert a Rust engine trace tree into a web PathNode tree.

    The Rust trace contains every operation (AND, IF, SUBTRACT, ...) as
    nested nodes, but the dashboard template ``render_path`` is meant to
    show only the law's *resolved inputs* — the data that flowed IN from
    cross-law references, data sources, parameters, and claims. We walk
    the tree, collect unique top-level input resolves, and discard the
    operation internals.
    """
    root = PathNode(type="root", name="evaluation", result=None)
    seen: set[str] = set()

    def _walk(node: dict) -> None:
        if not isinstance(node, dict):
            return
        node_type = node.get("node_type")
        if node_type == "resolve":
            name = node.get("name", "")
            resolve_type = node.get("resolve_type")
            # Only surface top-level variable resolves that represent real
            # citizen data (PARAMETER = input value, SERVICE = cross-law
            # result, DATASOURCE = record lookup, CLAIM = submitted by
            # citizen). DEFINITION nodes are internal law constants and
            # operation-internal resolves have no resolve_type — hide both.
            if resolve_type and resolve_type != "DEFINITION" and name and name not in seen and not name.startswith("$"):
                seen.add(name)
                root.children.append(
                    PathNode(
                        type="resolve",
                        name=name,
                        result=node.get("result"),
                        resolve_type=resolve_type,
                        details={"path": f"${name}", "message": node.get("message") or ""},
                    )
                )
        for child in node.get("children", []):
            _walk(child)

    _walk(trace)
    return root
