from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

BASE_DIR = "law"


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
        with open(path) as f:
            data = yaml.safe_load(f)

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


class RuleResolver:
    def __init__(self) -> None:
        self.rules_dir = Path(BASE_DIR)
        self.rules: list[RuleSpec] = []
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
        return max(valid_rules, key=lambda r: r.valid_from)

    def get_rule_spec(self, law: str, reference_date: str, service: str | None = None) -> dict:
        """Get the rule specification as a dictionary"""
        rule = self.find_rule(law, reference_date, service)
        if not rule:
            raise ValueError(f"No rule found for {law} at {reference_date}")

        with open(rule.path) as f:
            return yaml.safe_load(f)

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
