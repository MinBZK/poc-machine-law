import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

BASE_DIR = "laws"

# Mapping from v0.5.0 regulatory_layer to v0.1.x law_type
REGULATORY_LAYER_TO_LAW_TYPE = {
    "GRONDWET": "GRONDWET",
    "WET": "FORMELE_WET",
    "AMVB": "AMVB",
    "KONINKLIJK_BESLUIT": "KONINKLIJK_BESLUIT",
    "MINISTERIELE_REGELING": "MINISTERIELE_REGELING",
    "BELEIDSREGEL": "BELEIDSREGEL",
    "EU_VERORDENING": "EU_VERORDENING",
    "EU_RICHTLIJN": "EU_RICHTLIJN",
    "VERDRAG": "VERDRAG",
    "UITVOERINGSBELEID": "UITVOERINGSBELEID",
    "GEMEENTELIJKE_VERORDENING": "GEMEENTELIJKE_VERORDENING",
    "PROVINCIALE_VERORDENING": "PROVINCIALE_VERORDENING",
}


# Cache for parsed YAML files
_yaml_cache = {}


def _is_v050_format(data) -> bool:
    """Detect if a YAML law file uses the v0.5.x article-based schema."""
    if not isinstance(data, dict):
        return False
    schema = data.get("$schema", "")
    return "articles" in data or (isinstance(schema, str) and bool(re.search(r"v0\.5\.\d+", schema)))


def _convert_source_to_reference(source: dict) -> tuple[str, dict]:
    """Convert v0.5.0 'source' format to the appropriate v0.1.x reference format.

    Returns (ref_key, ref_dict) where ref_key is 'service_reference' or 'source_reference'.

    The converter may have mapped original source_reference (table lookups) into
    v0.5.0 source format. We detect table names by checking if the regulation
    lacks underscores or slashes (law names always contain them).
    """
    if not source:
        return "service_reference", {}

    regulation = source.get("regulation", "")
    output_field = source.get("output", "")
    params = source.get("parameters", {})

    # Detect source_reference (table lookup) vs service_reference (cross-law)
    # Table lookups have table/select_on/fields/source_type markers from the converter
    has_table_markers = any(k in source for k in ("select_on", "fields", "source_type", "table"))

    if has_table_markers:
        # It's a table lookup - preserve as source_reference
        source_ref = {}
        for key in ("table", "field", "fields", "select_on", "source_type"):
            if key in source:
                source_ref[key] = source[key]
        return "source_reference", source_ref
    else:
        # Cross-law service reference
        param_list = [{"name": k, "reference": v} for k, v in params.items()]
        service = source.get("service", "")  # Preserved by converter
        service_ref = {
            "field": output_field,
            "law": regulation,
            "service": service,
        }
        if param_list:
            service_ref["parameters"] = param_list
        return "service_reference", service_ref


def _unwrap_definitions(definitions: dict) -> dict:
    """Unwrap v0.5.0 definitions that are wrapped in {value: ...}."""
    if not definitions:
        return {}
    unwrapped = {}
    for key, val in definitions.items():
        if isinstance(val, dict) and "value" in val and len(val) == 1:
            unwrapped[key] = val["value"]
        else:
            unwrapped[key] = val
    return unwrapped


def _flatten_v050(data: dict) -> dict:
    """Flatten a v0.5.0 article-based YAML to the internal flat representation.

    Merges all articles' machine_readable sections into a single flat spec
    that the engine can process identically to v0.1.x files.
    """
    articles = data.get("articles") or []

    merged_parameters = []
    merged_input = []
    merged_output = []
    merged_actions = []
    merged_definitions = {}
    merged_requirements = []
    legal_character = ""
    decision_type = ""

    # Track names to avoid duplicates when merging across articles
    seen_param_names = set()
    seen_input_names = set()
    seen_output_names = set()

    for article in articles:
        mr = article.get("machine_readable", {})
        if not mr:
            continue

        # Definitions
        defs = mr.get("definitions", {})
        merged_definitions.update(_unwrap_definitions(defs))

        execution = mr.get("execution", {})
        if not execution:
            continue

        # Produces metadata (take from first article that has it)
        produces = execution.get("produces", {})
        if produces:
            if not legal_character and "legal_character" in produces:
                legal_character = produces["legal_character"]
            if not decision_type and "decision_type" in produces:
                decision_type = produces["decision_type"]

        # Parameters
        for param in execution.get("parameters", []):
            name = param.get("name")
            if name and name not in seen_param_names:
                seen_param_names.add(name)
                merged_parameters.append(param)

        # Input - convert source to appropriate reference type
        for inp in execution.get("input", []):
            name = inp.get("name")
            if name and name not in seen_input_names:
                seen_input_names.add(name)
                # Convert v0.5.0 source format to service_reference or source_reference
                if "source" in inp and "service_reference" not in inp and "source_reference" not in inp:
                    inp = dict(inp)  # Don't mutate the original
                    ref_key, ref_dict = _convert_source_to_reference(inp.pop("source"))
                    # For source_reference: default field to input name if not set
                    if ref_key == "source_reference" and "field" not in ref_dict:
                        ref_dict["field"] = name
                    inp[ref_key] = ref_dict
                merged_input.append(inp)

        # Output
        for out in execution.get("output", []):
            name = out.get("name")
            if name and name not in seen_output_names:
                seen_output_names.add(name)
                merged_output.append(out)

        # Actions
        merged_actions.extend(execution.get("actions", []))

        # Requirements
        merged_requirements.extend(execution.get("requirements", []))

    # Build the flat spec
    flat = {}

    # Copy over metadata
    if "$id" in data:
        flat["law"] = data["$id"]
    elif "law" in data:
        flat["law"] = data["law"]

    if "regulatory_layer" in data:
        flat["law_type"] = REGULATORY_LAYER_TO_LAW_TYPE.get(data["regulatory_layer"], data["regulatory_layer"])

    flat["legal_character"] = legal_character
    flat["decision_type"] = decision_type

    # Keep service if it's a custom extension in the file
    if "service" in data:
        flat["service"] = data["service"]

    # Copy other top-level fields that the engine/RuleSpec needs
    for key in ("uuid", "name", "valid_from", "description"):
        if key in data:
            flat[key] = data[key]

    # discoverable was removed in v0.5.0 - default to CITIZEN for backwards compatibility
    flat["discoverable"] = data.get("discoverable", "CITIZEN")

    # Properties block (same structure as v0.1.x)
    flat["properties"] = {
        "parameters": merged_parameters,
        "input": merged_input,
        "output": merged_output,
        "definitions": merged_definitions,
    }

    # Extract _voldoet_aan_voorwaarden action as requirements (converter moved them)
    final_actions = []
    for action in merged_actions:
        if action.get("output") == "_voldoet_aan_voorwaarden":
            # Convert the action's value/operation back to a requirements list
            val = action.get("value", action)
            if isinstance(val, dict) and val.get("operation") == "AND":
                # AND conditions become individual requirements in an all block
                conditions = val.get("conditions", val.get("values", []))
                merged_requirements.append({"all": conditions})
            elif isinstance(val, dict) and "operation" in val:
                merged_requirements.append(val)
        else:
            final_actions.append(action)

    flat["requirements"] = merged_requirements
    flat["actions"] = final_actions

    return flat


def load_yaml_cached(file_path: str) -> dict:
    """Load YAML file with caching for better performance.

    Automatically detects and flattens v0.5.0 article-based format.
    """
    if file_path in _yaml_cache:
        return _yaml_cache[file_path]

    with open(file_path) as f:
        data = yaml.load(f, Loader=Loader)

    if not isinstance(data, dict):
        _yaml_cache[file_path] = data or {}
        return _yaml_cache[file_path]

    # Flatten v0.5.0 format to internal representation
    if _is_v050_format(data):
        data = _flatten_v050(data)

    _yaml_cache[file_path] = data
    return data


@dataclass
class RuleSpec:
    path: str
    decision_type: str
    law_type: str
    legal_character: str
    uuid: str
    name: str
    law: str
    valid_from: datetime
    service: str
    discoverable: str
    properties: dict[str, Any]

    @classmethod
    def from_yaml(cls, path: str) -> "RuleSpec":
        """Create RuleSpec from a YAML file path"""
        data = load_yaml_cached(path)

        # Parse valid_from: handle datetime, date, and string formats
        valid_from_raw = data.get("valid_from")
        if valid_from_raw is None:
            raise ValueError(f"Missing valid_from in {path}")
        elif isinstance(valid_from_raw, datetime):
            valid_from = valid_from_raw
        elif isinstance(valid_from_raw, str):
            valid_from = datetime.strptime(valid_from_raw, "%Y-%m-%d")
        else:
            # datetime.date or other
            valid_from = datetime.combine(valid_from_raw, datetime.min.time())

        return cls(
            path=path,
            decision_type=data.get("decision_type", ""),
            law_type=data.get("law_type", ""),
            legal_character=data.get("legal_character", ""),
            uuid=data.get("uuid", ""),
            name=data.get("name", ""),
            law=data.get("law", ""),
            discoverable=data.get("discoverable", ""),
            valid_from=valid_from,
            service=data.get("service", ""),
            properties=data.get("properties", {}),
        )


class RuleResolver:
    def __init__(self) -> None:
        self.rules_dir = Path(BASE_DIR)
        self.rules: list[RuleSpec] = []
        # Rule cache indexed by (law, reference_date, service)
        self._rule_cache = {}
        # Rule spec cache indexed by rule path
        self._rule_spec_cache = {}
        self._load_rules()

    def _load_rules(self) -> None:
        """Load all rule specifications from the rules directory"""
        # Use Path.rglob to find all .yaml and .yml files recursively
        yaml_files = list(self.rules_dir.rglob("*.yaml")) + list(self.rules_dir.rglob("*.yml"))

        for path in yaml_files:
            try:
                rule = RuleSpec.from_yaml(str(path))
                self.rules.append(rule)
            except Exception as e:
                print(f"Error loading rule from {path}: {e}")

        self.laws_by_service = defaultdict(set)
        self.discoverable_laws_by_service = defaultdict(lambda: defaultdict(set))
        for rule in self.rules:
            self.laws_by_service[rule.service].add(rule.law)
            if rule.discoverable:
                self.discoverable_laws_by_service[rule.discoverable][rule.service].add(rule.law)

    def get_service_laws(self):
        return self.laws_by_service

    def get_discoverable_service_laws(self, discoverable_by="CITIZEN"):
        return self.discoverable_laws_by_service[discoverable_by]

    def find_rule(self, law: str, reference_date: str, service: str | None = None) -> RuleSpec | None:
        """Find the applicable rule for a given law and reference date"""
        # Check if we have a cached result
        cache_key = (law, reference_date, service)
        if cache_key in self._rule_cache:
            return self._rule_cache[cache_key]

        ref_date = datetime.strptime(reference_date, "%Y-%m-%d")

        # Filter rules for the given law
        law_rules = [r for r in self.rules if r.law == law]

        if service:
            # If a service is given, filter rules for the given service
            law_rules = [r for r in law_rules if r.service == service]

        if not law_rules:
            raise ValueError(f"No rules found for law: {law} (and service: {service})")

        # Find the most recent valid rule before the reference date
        valid_rules = [r for r in law_rules if r.valid_from <= ref_date]

        if not valid_rules:
            raise ValueError(f"No valid rules found for law {law} at date {reference_date}")

        # Return the most recently valid rule
        rule = max(valid_rules, key=lambda r: r.valid_from)

        # Cache the result
        self._rule_cache[cache_key] = rule

        return rule

    def get_rule_spec(self, law: str, reference_date: str, service: str | None = None) -> dict:
        """Get the rule specification as a dictionary"""
        rule = self.find_rule(law, reference_date, service)
        if not rule:
            raise ValueError(f"No rule found for {law} at {reference_date}")

        return load_yaml_cached(rule.path)

    def rules_dataframe(self) -> pd.DataFrame:
        """Convert the list of RuleSpec objects into a pandas DataFrame."""
        rules_data = [
            {
                "path": rule.path,
                "decision_type": rule.decision_type,
                "legal_character": rule.legal_character,
                "law_type": rule.law_type,
                "uuid": rule.uuid,
                "name": rule.name,
                "law": rule.law,
                "valid_from": rule.valid_from,
                "service": rule.service,
                "discoverable": rule.discoverable,
                **{f"prop_{k}": v for k, v in rule.properties.items()},
            }
            for rule in self.rules
        ]

        return pd.DataFrame(rules_data)


if __name__ == "__main__":
    reference_date = "2025-01-01"
    resolver = RuleResolver()
    spec = resolver.get_rule_spec("zorgtoeslagwet", reference_date)
    assert spec["law"] == "zorgtoeslagwet"
