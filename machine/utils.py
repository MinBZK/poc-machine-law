import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import jsonpatch
import pandas as pd
import yaml

from .context import logger

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

        # Filter out jurisprudence patch files that follow the naming convention
        rule_files = []
        for path in yaml_files:
            # Check if file is a patch file
            if path.name.startswith("JURISPRUDENTIE-"):
                logger.debug(f"Skipping jurisprudence file {path} during rule loading - will be applied as patch")
                continue
            rule_files.append(path)

        for path in rule_files:
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

    def _find_patches_for_rule(self, rule: RuleSpec) -> list[Path]:
        """Find all patch files for a rule based on naming convention"""
        patches = []

        # Find the base directory of the rule
        rule_path = Path(rule.path)
        base_dir = rule_path.parent

        # If the rule is in a service-specific subdirectory, go up one level
        law_parts = rule.law.split("/")
        if len(law_parts) > 1 and law_parts[-1] in rule_path.parent.name:
            base_dir = rule_path.parent
        elif len(law_parts) > 1 and law_parts[-1] in rule_path.parent.parent.name:
            base_dir = rule_path.parent.parent

        logger.info(f"Looking for patches in {base_dir} for {rule.law} (service: {rule.service})")

        # First try to find jurisprudence patches with the prefix format
        prefix_patches = list(base_dir.glob("JURISPRUDENTIE-*.yaml"))
        if prefix_patches:
            patches.extend(prefix_patches)
            logger.debug(f"Found {len(prefix_patches)} patches with JURISPRUDENTIE prefix")

        # Sort patches by date in filename to ensure consistent application order
        patches.sort(key=lambda p: p.name)

        logger.info(f"Found {len(patches)} patch files for {rule.law} ({rule.service}): {[p.name for p in patches]}")
        return patches

    def _apply_patches_to_rule_spec(self, rule_spec: dict[str, Any], patch_files: list[Path]) -> dict[str, Any]:
        """Apply a list of patches to a rule specification, using the patches exactly as they are"""
        result = rule_spec.copy()
        # return result

        for patch_file in patch_files:
            try:
                logger.info(f"Applying patch from {patch_file}")
                with open(patch_file) as f:
                    patch_data = yaml.safe_load(f)

                # Log patch operations before applying
                for i, patch_op in enumerate(patch_data):
                    op = patch_op.get("op")
                    path = patch_op.get("path")
                    logger.debug(f"Patch operation {i + 1}: {op} at {path}")

                # Make a copy to check for changes
                before_patch = result.copy()

                # Apply the patch to the rule spec
                try:
                    result = jsonpatch.apply_patch(result, patch_data)
                    logger.info(f"Successfully applied patch from {patch_file}")
                except jsonpatch.JsonPatchException as e:
                    logger.error(f"Error applying patch {patch_file}: {e}")
                    logger.info("Patches must match the exact structure of the target rule file.")
                    logger.info("Skipping this patch - needs to be updated to match the rule file structure.")
                    continue

                # Check for changes
                if result == before_patch:
                    logger.warning(f"No changes detected after applying patch {patch_file.name}")

            except Exception as e:
                logger.error(f"Error applying patch {patch_file}: {e}")

        return result

    def get_rule_spec(self, law: str, reference_date: str, service: str | None = None) -> dict:
        """Get the rule specification as a dictionary, with applicable patches applied"""
        rule = self.find_rule(law, reference_date, service)
        if not rule:
            raise ValueError(f"No rule found for {law} at {reference_date}")

        # Load the base rule specification
        with open(rule.path) as f:
            rule_spec = yaml.safe_load(f)
            logger.debug(f"Loaded base rule from {rule.path}")

        # Find and apply patches for this rule
        patch_files = self._find_patches_for_rule(rule)
        if patch_files:
            logger.info(f"Found {len(patch_files)} jurisprudence patches for {rule.law}")
            original_rule_spec = rule_spec.copy()
            rule_spec = self._apply_patches_to_rule_spec(rule_spec, patch_files)

            # Log a summary of patches applied
            if rule_spec != original_rule_spec:
                logger.info(f"Successfully patched {rule.law} with {len(patch_files)} jurisprudence files")
            else:
                logger.warning("Patches were processed but no changes detected in the rule spec")

        return rule_spec

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
    # Setup basic logging
    import logging

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Create resolver
    resolver = RuleResolver()

    # Get available rule specifications and their valid_from dates
    print("\nRule specifications with valid_from dates:")
    for rule in resolver.rules:
        if rule.law == "participatiewet/bijstand":
            print(f"- {rule.path}: valid_from={rule.valid_from}, service={rule.service}")

    # Print available laws by service
    print("\nAvailable laws and services:")
    service_laws = resolver.get_service_laws()
    for service, laws in service_laws.items():
        if "participatiewet" in str(laws):
            print(f"{service}: {laws}")

    # Test participatiewet bijstand patching
    print("\n\nTesting jurisprudence patches for participatiewet/bijstand GEMEENTE_AMSTERDAM:")
    try:
        # Load the base rule first to analyze structure
        amsterdam_rule = resolver.find_rule("participatiewet/bijstand", "2024-01-01", "GEMEENTE_AMSTERDAM")
        with open(amsterdam_rule.path) as f:
            base_spec = yaml.safe_load(f)

        # Print rule structure to help diagnose patch issues
        print(f"\nStructure of {amsterdam_rule.path}:")
        print(f"Top-level keys: {list(base_spec.keys())}")
        if "properties" in base_spec and "definitions" in base_spec["properties"]:
            print(f"Properties -> definitions keys: {list(base_spec['properties']['definitions'].keys())}")

        # Load the patches and analyze
        patch_files = resolver._find_patches_for_rule(amsterdam_rule)
        print("\nFound patches:")
        for patch_file in patch_files:
            print(f"\nAnalyzing patch: {patch_file}")
            with open(patch_file) as f:
                patch_data = yaml.safe_load(f)

            # Print patch operations to help diagnose issues
            print("Patch operations:")
            for i, op in enumerate(patch_data):
                print(f"  {i + 1}. {op.get('op')} {op.get('path')}")

                # Check if path exists in target structure
                path = op.get("path", "")
                if path.startswith("/definitions") and "definitions" not in base_spec:
                    print("    WARNING: Target has no top-level 'definitions' key")
                    print(f"    SUGGESTION: Change to /properties/definitions{path[11:]}")

        # Now try to apply the patches
        bijstand_spec = resolver.get_rule_spec("participatiewet/bijstand", "2024-01-01", "GEMEENTE_AMSTERDAM")
        print("\nSuccessfully loaded participatiewet/bijstand")

        # Check references
        references = bijstand_spec.get("references", [])
        jurisprudence_refs = [ref for ref in references if ref.get("law") == "Jurisprudentie"]

        print(f"Found {len(jurisprudence_refs)} jurisprudence references in the patched law:")
        for ref in jurisprudence_refs:
            print(f" - {ref.get('article')}: {ref.get('description')}")

    except Exception as e:
        print(f"Error testing jurisprudence patches: {e}")

    # Test SZW version
    print("\n\nTesting jurisprudence patches for participatiewet/bijstand SZW:")
    try:
        # Load the base rule to analyze structure
        szw_rule = resolver.find_rule("participatiewet/bijstand", "2025-01-01", "SZW")
        with open(szw_rule.path) as f:
            szw_base_spec = yaml.safe_load(f)

        # Print rule structure
        print(f"\nStructure of {szw_rule.path}:")
        print(f"Top-level keys: {list(szw_base_spec.keys())}")
        if "properties" in szw_base_spec and "definitions" in szw_base_spec["properties"]:
            print(f"Properties -> definitions keys: {list(szw_base_spec['properties']['definitions'].keys())}")

        # Now try to apply the patches
        bijstand_spec_szw = resolver.get_rule_spec("participatiewet/bijstand", "2025-01-01", "SZW")
        print("Successfully loaded participatiewet/bijstand for SZW")

        # Check references
        references = bijstand_spec_szw.get("references", [])
        jurisprudence_refs = [ref for ref in references if ref.get("law") == "Jurisprudentie"]
        print(f"Found {len(jurisprudence_refs)} jurisprudence references in the patched SZW law")
    except Exception as e:
        print(f"Error testing SZW jurisprudence patches: {e}")

    print("\nImportant notes for fixing patches:")
    print("1. Each patch must match the exact structure of the target law file")
    print("2. If the target has definitions under properties, use /properties/definitions/...")
    print("3. If the target has no 'sources' key, add operations need to create parent paths first")
    print("4. Check all patch operations against the actual structure of the target file")

    print("\nExample of a fixed patch (for Amsterdam structure):")
    print("""# Jurisprudentie: ECLI:NL:CRVB:2001:AD7128
# Original patch operations with correct paths for the Amsterdam rule

- op: add
  path: /references/-
  value:
    law: "Jurisprudentie"
    article: "ECLI:NL:CRVB:2001:AD7128"
    url: "https://uitspraken.rechtspraak.nl/inziendocument?id=ECLI:NL:CRVB:2001:AD7128"
    description: "Definitie van een woning in relatie tot de kostendelersnorm"

# Path updated to match target structure
- op: add
  path: /properties/definitions/WONINGTYPEN
  value:
    - "REGULIERE_WONING"
    - "WOONWAGEN"
    - "WOONSCHIP"
    - "CARAVAN"
    - "STACARAVAN"

# First create the array if it doesn't exist
- op: add
  path: /properties/definitions/KOSTENDELERSNORM_UITZONDERINGEN
  value: []
  # Only add if doesn't exist already

# Then add to the array
- op: add
  path: /properties/definitions/KOSTENDELERSNORM_UITZONDERINGEN/-
  value: "ERKEND_WONINGTYPE"

# The rest of the operations remain unchanged
- op: add
  path: /actions/-
  value:
    description: "Bepaalt of secundaire woonruimte als woning wordt aangemerkt volgens definitie"
    operation: "IF"
    # ...rest of action definition...
""")
