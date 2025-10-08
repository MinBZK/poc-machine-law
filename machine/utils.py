import json
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

BASE_DIR = "law"
NRML_BASE_DIR = "nrml-law"


# Cache for parsed files
_file_cache = {}


def load_file_cached(file_path: str) -> dict:
    """Load YAML file with caching for better performance"""
    if file_path in _file_cache:
        return _file_cache[file_path]

    with open(file_path) as f:
        data = json.load(f) if file_path.endswith(".json") else yaml.load(f, Loader=Loader)
    _file_cache[file_path] = data
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
        data = load_file_cached(path)

        return cls(
            path=path,
            decision_type=data.get("decision_type", ""),
            law_type=data.get("law_type", ""),
            legal_character=data.get("legal_character", ""),
            uuid=data.get("uuid", ""),
            name=data.get("name", ""),
            law=data.get("law", ""),
            discoverable=data.get("discoverable", ""),
            valid_from=data.get("valid_from")
            if isinstance(data.get("valid_from"), datetime)
            else datetime.combine(data.get("valid_from"), datetime.min.time()),
            service=data.get("service", ""),
            properties=data.get("properties", {}),
        )

    @classmethod
    def from_json(cls, path: str) -> "RuleSpec":
        """Create RuleSpec from a JSON file path"""
        data = load_file_cached(path)

        # Extract metadata for rule properties
        metadata = data.get("metadata", {})

        # Use filename without extension as law name if not in metadata
        law_name = metadata.get("description", Path(path).stem.replace(".nrml", ""))

        # Extract validFrom from facts if available, otherwise use placeholder
        valid_from_str = None
        facts = data.get("facts", {})
        for fact_id, fact_data in facts.items():
            items = fact_data.get("items", {})
            for item_id, item_data in items.items():
                versions = item_data.get("versions", [])
                if versions and "validFrom" in versions[0]:
                    valid_from_str = versions[0]["validFrom"]
                    break
            if valid_from_str:
                break

        # Parse the date or use a default
        if valid_from_str:
            try:
                # Try parsing as full date first
                valid_from = datetime.strptime(valid_from_str, "%Y-%m-%d")
            except ValueError:
                # If that fails, try parsing as year only
                try:
                    valid_from = datetime.strptime(valid_from_str, "%Y")
                except ValueError:
                    # If both fail, use default
                    valid_from = datetime(2020, 1, 1)
        else:
            valid_from = datetime(2020, 1, 1)

        return cls(
            path=path,
            decision_type=metadata.get("decision_type", "TOEKENNING"),
            law_type=metadata.get("law_type", "FORMELE_WET"),
            legal_character=metadata.get("legal_character", "BESCHIKKING"),
            uuid=metadata.get("uuid", f"json-{Path(path).stem}"),
            name=metadata.get("name", law_name),
            law=metadata.get("description", law_name),
            discoverable=metadata.get("discoverable", ""),
            valid_from=valid_from,
            service=metadata.get("service", "NRML"),
            properties=metadata,
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
        # Use Path.rglob to find all .yaml, .yml files from law directory
        yaml_files = list(self.rules_dir.rglob("*.yaml")) + list(self.rules_dir.rglob("*.yml"))

        # Load JSON files from nrml-law directory
        nrml_dir = Path(NRML_BASE_DIR)
        json_files = list(nrml_dir.rglob("*.json")) if nrml_dir.exists() else []

        # Load YAML files
        for path in yaml_files:
            try:
                rule = RuleSpec.from_yaml(str(path))
                self.rules.append(rule)
            except Exception as e:
                print(f"Error loading YAML rule from {path}: {e}")

        # Load JSON files
        for path in json_files:
            try:
                rule = RuleSpec.from_json(str(path))
                self.rules.append(rule)
            except Exception as e:
                print(f"Error loading JSON rule from {path}: {e}")

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

        return load_file_cached(rule.path)

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
    assert spec["uuid"] == "4d8c7237-b930-4f0f-aaa3-624ba035e449"
