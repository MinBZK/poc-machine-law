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

        # Convert the Rust engine trace tree to a web PathNode tree. The
        # trace already contains nested cross-law evaluations with their
        # own resolve nodes, so we walk the tree and classify each resolve
        # by the YAML source of the law it belongs to.
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

    The Rust trace already contains every cross-law resolution as a
    nested ``cross_law_reference`` node whose children expose the inputs
    that the referenced law resolved. This mirrors the hierarchical
    "Gebruikte gegevens" layout the dashboard wants, so the mapping is
    one-to-one:

    - Each input declared on the current article becomes a ``resolve``
      or ``service_evaluation`` PathNode on the root.
    - If the input is a cross-law reference, we locate the matching
      ``cross_law_reference`` trace node by ``{regulation}#{output}``
      and recurse into it: its own resolved inputs become nested
      children on the parent node.
    - Data-source / direct inputs stay as single ``resolve`` leaves.
    """
    root = PathNode(type="root", name="evaluation", result=None)

    # Build a lookup of cross_law_reference nodes in the trace keyed by
    # "{regulation}#{output}" so we can attach nested traces to inputs.
    cross_law_nodes: dict[str, list[dict]] = {}
    resolve_nodes: dict[str, Any] = {}

    def _index(node: dict, in_crosslaw: str | None) -> None:
        if not isinstance(node, dict):
            return
        nt = node.get("node_type")
        name = node.get("name", "")
        if nt == "cross_law_reference":
            cross_law_nodes.setdefault(name, []).append(node)
            for child in node.get("children", []):
                _index(child, name)
            return
        if nt == "resolve" and in_crosslaw is None and name not in resolve_nodes:
            resolve_nodes[name] = node.get("result")
        for child in node.get("children", []):
            _index(child, in_crosslaw)

    _index(trace, None)

    for name, spec in input_specs.items():
        resolve_type, details = _classify_input(spec)
        details["path"] = f"${name}"
        required = bool(spec.get("required", False))

        if resolve_type == "SERVICE":
            source = spec.get("source") or {}
            regulation = source.get("regulation")
            output = source.get("output", name)
            key = f"{regulation}#{output}"
            cross_nodes = cross_law_nodes.get(key) or []
            cross_node = cross_nodes[0] if cross_nodes else None
            result = cross_node.get("result") if cross_node else resolve_nodes.get(name)
            node = PathNode(
                type="service_evaluation",
                name=name,
                result=result,
                resolve_type=resolve_type,
                required=required,
                details=details,
            )
            if cross_node:
                node.children = _crosslaw_children_as_pathnodes(cross_node, regulation, output)
            root.children.append(node)
        else:
            if name not in resolve_nodes:
                continue
            root.children.append(
                PathNode(
                    type="resolve",
                    name=name,
                    result=resolve_nodes[name],
                    resolve_type=resolve_type,
                    required=required,
                    details=details,
                )
            )
    return root


def _crosslaw_children_as_pathnodes(
    cross_node: dict,
    regulation: str,
    output: str,
    depth: int = 0,
    max_depth: int = 3,
) -> list[PathNode]:
    """Return the decomposition children for a cross-law service.

    Matches the production dashboard: under a cross-law expansion we
    show the ``$var`` references that appear as direct arguments to
    the action that produced the requested output. Those are the
    "components" the value breaks down into (e.g. ``inkomen = box1 +
    box2 + box3 + buitenlands``). When a component is itself an output
    of the same law, it becomes a nested ``service_evaluation`` so the
    user can drill in further (e.g. box1 → loon/winst/uitkeringen).
    Plain input components render as leaves.
    """
    if depth >= max_depth:
        return []

    nested_outputs = _output_specs_for_law(regulation)
    nested_inputs = _input_specs_for_law(regulation)

    # Find the action node for this output.
    action = _find_action_in_trace(cross_node, output)
    if not action:
        return []

    # Walk the action's operation tree and pick up the direct $var refs.
    refs: list[tuple[str, Any]] = _collect_direct_refs(action)
    if not refs:
        return []

    seen: set[str] = set()
    children: list[PathNode] = []

    for ref_name, ref_value in refs:
        if ref_name in seen:
            continue
        seen.add(ref_name)

        if ref_name in nested_outputs:
            # Same-law output: render as a nested service_evaluation so
            # the dashboard can recurse one level further down.
            out_spec = nested_outputs[ref_name]
            details = {
                "type": out_spec.get("type"),
                "type_spec": out_spec.get("type_spec"),
                "path": f"${ref_name}",
            }
            node = PathNode(
                type="service_evaluation",
                name=ref_name,
                result=ref_value,
                resolve_type="SERVICE",
                required=False,
                details=details,
            )
            node.children = _crosslaw_children_as_pathnodes(cross_node, regulation, ref_name, depth + 1, max_depth)
            children.append(node)
        else:
            # Treat as input / data-source leaf.
            spec = nested_inputs.get(ref_name, {})
            resolve_type, details = _classify_input(spec) if spec else ("NONE", {"type": None, "type_spec": None})
            details["path"] = f"${ref_name}"
            children.append(
                PathNode(
                    type="resolve",
                    name=ref_name,
                    result=ref_value,
                    resolve_type=resolve_type,
                    required=bool(spec.get("required", False)) if spec else False,
                    details=details,
                )
            )

    return children


def _find_action_in_trace(cross_node: dict, output: str) -> dict | None:
    """Locate the ``action`` trace node that computes ``output``."""
    for child in cross_node.get("children", []):
        if not isinstance(child, dict):
            continue
        if child.get("node_type") == "action" and child.get("name") == output:
            return child
    # Fall back to depth search in case the action is wrapped.
    for child in cross_node.get("children", []):
        if not isinstance(child, dict):
            continue
        if child.get("node_type") == "article":
            for grand in child.get("children", []):
                if isinstance(grand, dict) and grand.get("node_type") == "action" and grand.get("name") == output:
                    return grand
    return None


def _collect_direct_refs(action: dict) -> list[tuple[str, Any]]:
    """Collect ``(name, result)`` for $var refs inside an action value.

    Walks the action's operation subtree and returns the first
    ``resolve`` node encountered per name — these are the direct
    components of the action's computation.
    """
    out: list[tuple[str, Any]] = []
    seen: set[str] = set()

    def _walk(n: dict) -> None:
        if not isinstance(n, dict):
            return
        if n.get("node_type") == "resolve":
            name = n.get("name", "")
            if name and name not in seen:
                seen.add(name)
                out.append((name, n.get("result")))
            return
        for c in n.get("children", []):
            _walk(c)

    for child in action.get("children", []):
        _walk(child)
    return out


def _output_specs_for_law(law_id: str) -> dict[str, dict[str, Any]]:
    """Return ``{output_name: spec}`` for a law identified by ``$id``."""
    if law_id in _OUTPUT_SPEC_CACHE:
        return _OUTPUT_SPEC_CACHE[law_id]

    from machine.utils import RuleResolver

    specs: dict[str, dict[str, Any]] = {}
    try:
        resolver = RuleResolver()
        rules = [r for r in resolver.rules if r.law == law_id]
        if rules:
            latest = max(rules, key=lambda r: r.valid_from)
            data = yaml.safe_load(Path(latest.path).read_text())
            if isinstance(data, dict):
                for article in data.get("articles", []):
                    execution = article.get("machine_readable", {}).get("execution", {})
                    for out in execution.get("output", []):
                        name = out.get("name")
                        if name:
                            specs[name] = out
    except Exception as exc:
        logger.debug("Could not load output specs for %s: %s", law_id, exc)

    _OUTPUT_SPEC_CACHE[law_id] = specs
    return specs


_OUTPUT_SPEC_CACHE: dict[str, dict[str, dict[str, Any]]] = {}


_INPUT_SPEC_CACHE: dict[str, dict[str, dict[str, Any]]] = {}


def _input_specs_for_law(law_id: str) -> dict[str, dict[str, Any]]:
    """Return cached input specs for a law identified by its ``$id``."""
    if law_id in _INPUT_SPEC_CACHE:
        return _INPUT_SPEC_CACHE[law_id]

    from machine.utils import RuleResolver

    specs: dict[str, dict[str, Any]] = {}
    try:
        resolver = RuleResolver()
        rules = [r for r in resolver.rules if r.law == law_id]
        if rules:
            latest = max(rules, key=lambda r: r.valid_from)
            specs = _collect_input_specs(latest.path)
    except Exception as exc:
        logger.debug("Could not load input specs for %s: %s", law_id, exc)

    _INPUT_SPEC_CACHE[law_id] = specs
    return specs
