#!/usr/bin/env python3
"""Convert $UPPERCASE variable references to $lowercase across the codebase.

This script lowercases:
1. YAML law files: parameter names, input names, definition keys, $VARIABLE references
2. BDD feature files: table headers that match known parameter/input patterns
3. Python step definitions: parameter key strings
4. Profile data: table key names for source data
5. Other Python files referencing field names

It does NOT change:
- Output names (already lowercase)
- Service names (TOESLAGEN, RvIG, etc.)
- Enum values (ACTIEF, HUWELIJK, NEDERLAND, etc.)
- Type values (string, number, amount, etc.)
- regulatory_layer, legal_character, decision_type values
- String literals/descriptions
- $calculation_date, $current (already lowercase)
"""

import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def lowercase_dollar_vars(text: str) -> str:
    """Replace $UPPERCASE_VAR with $lowercase_var in a string.

    Only matches $ followed by at least one uppercase letter and then
    uppercase letters, digits, or underscores. Does not touch:
    - $calculation_date, $current, $year, etc. (already lowercase)
    - $schema, $id (YAML meta keys)
    - $current.FIELD (handled separately)
    """

    def _replace_var(m: re.Match) -> str:
        prefix = m.group(1)  # the $ sign
        varname = m.group(2)  # the variable name
        # Only lowercase if the name contains at least one uppercase letter
        # and is a "variable-style" name (all caps/digits/underscores)
        if re.match(r"^[A-Z][A-Z0-9_]*$", varname):
            return prefix + varname.lower()
        # Handle $UPPERCASE.field_name (dotted access)
        if "." in varname:
            parts = varname.split(".", 1)
            if re.match(r"^[A-Z][A-Z0-9_]*$", parts[0]):
                return prefix + parts[0].lower() + "." + parts[1]
        return m.group(0)

    # Match $VARNAME where VARNAME can contain dots for dotted access
    return re.sub(r"(\$)([A-Za-z][A-Za-z0-9_.]*)", _replace_var, text)


def process_yaml_file(filepath: Path) -> bool:
    """Process a YAML law file to lowercase variable references.

    Strategy: use targeted regex replacements on the raw text, not YAML parsing,
    to preserve formatting, comments, and structure.
    """
    content = filepath.read_text()
    original = content

    # 1. Lowercase $UPPERCASE variable references everywhere in the file
    content = lowercase_dollar_vars(content)

    # 2. Lowercase parameter and input names: "- name: UPPERCASE" -> "- name: lowercase"
    #    But only inside machine_readable/execution blocks (parameters and input sections)
    #    We match lines like "      - name: BSN" or "        name: LEEFTIJD"
    def _lowercase_name_value(m: re.Match) -> str:
        prefix = m.group(1)  # everything before the name value
        name_val = m.group(2)  # the name value
        if re.match(r"^[A-Z][A-Z0-9_]*$", name_val):
            return prefix + name_val.lower()
        return m.group(0)

    # Match "name: UPPERCASE" lines in parameters/input sections
    # These are lines like "      - name: BSN" or "        name: LEEFTIJD"
    content = re.sub(
        r"(^\s*-?\s*name:\s+)([A-Z][A-Z0-9_]+)\s*$",
        _lowercase_name_value,
        content,
        flags=re.MULTILINE,
    )

    # 3. Lowercase definition keys in the definitions block
    #    Lines like "      MINIMUM_LEEFTIJD:" -> "      minimum_leeftijd:"
    #    These are indented keys inside a "definitions:" block
    def _lowercase_def_key(m: re.Match) -> str:
        indent = m.group(1)
        key = m.group(2)
        colon = m.group(3)
        if re.match(r"^[A-Z][A-Z0-9_]*$", key):
            return indent + key.lower() + colon
        return m.group(0)

    # We process definition keys: indented UPPERCASE_KEY: lines
    # These are children of "definitions:" in the YAML
    # Match indented ALL_CAPS keys that appear to be definition names
    content = re.sub(
        r"(^\s{6,})([A-Z][A-Z0-9_]+)(:\s*$)",
        _lowercase_def_key,
        content,
        flags=re.MULTILINE,
    )
    # Also handle definition keys with values on same line
    content = re.sub(
        r"(^\s{6,})([A-Z][A-Z0-9_]+)(:\s+\S)",
        _lowercase_def_key,
        content,
        flags=re.MULTILINE,
    )

    # 4. Lowercase parameter keys in source.parameters blocks
    #    Lines like "            BSN: $bsn" -> "            bsn: $bsn"
    #    or "            GEBOORTEDATUM: $geboortedatum" -> "            geboortedatum: $geboortedatum"
    def _lowercase_source_param_key(m: re.Match) -> str:
        indent = m.group(1)
        key = m.group(2)
        rest = m.group(3)
        if re.match(r"^[A-Z][A-Z0-9_]*$", key):
            return indent + key.lower() + rest
        return m.group(0)

    # Source parameter keys are deeply indented (10+ spaces) and followed by : $varname
    content = re.sub(
        r"(^\s{10,})([A-Z][A-Z0-9_]+)(:\s+\$)",
        _lowercase_source_param_key,
        content,
        flags=re.MULTILINE,
    )

    # Also handle source parameter keys followed by non-$ values (like REFERENTIEDATUM: $verkiezingsdatum)
    # Already handled by the above since we lowercased $vars first

    if content != original:
        filepath.write_text(content)
        return True
    return False


def process_feature_file(filepath: Path) -> bool:
    """Process a BDD feature file to lowercase table headers that are uppercase variable names.

    Only two specific contexts are handled:
    1. "met" tables: the HEADER ROW (first table row) after a "wordt uitgevoerd door ... met" step
       has variable names as column headers that need lowercasing.
    2. "wijziging" tables: the "key" column in data rows references YAML input names.
    """
    content = filepath.read_text()
    original = content

    lines = content.split("\n")
    new_lines = []
    # State for "met" table processing
    expect_met_header = False
    # State for "wijziging" table processing
    in_wijziging_table = False
    wijziging_key_col_idx = -1

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Detect "wordt uitgevoerd door ... met" step (parameters table follows)
        if "wordt uitgevoerd door" in line and line.rstrip().endswith("met"):
            expect_met_header = True
            in_wijziging_table = False
            new_lines.append(line)
            continue

        # Detect "indient" step (wijziging indient, gegevens indient, etc.)
        # The key column has variable names in data rows
        if " indient" in line and stripped.startswith("When"):
            in_wijziging_table = True
            wijziging_key_col_idx = -1
            new_lines.append(line)
            continue

        # Process table lines
        if stripped.startswith("|") and "|" in stripped:
            if expect_met_header:
                # This is the HEADER row of a "met" table - lowercase all uppercase cells
                expect_met_header = False
                cells = line.split("|")
                new_cells = []
                for cell in cells:
                    cell_stripped = cell.strip()
                    if re.match(r"^[A-Z][A-Z0-9_]+$", cell_stripped):
                        new_cells.append(cell.replace(cell_stripped, cell_stripped.lower()))
                    else:
                        new_cells.append(cell)
                line = "|".join(new_cells)

            elif in_wijziging_table:
                # Find the "key" column index in the header row
                cells = [c.strip() for c in stripped.split("|")]
                if wijziging_key_col_idx == -1:
                    # This is the header row - find the "key" column
                    for idx, cell in enumerate(cells):
                        if cell == "key":
                            wijziging_key_col_idx = idx
                            break
                elif wijziging_key_col_idx >= 0:
                    # This is a data row - lowercase the key column value
                    if wijziging_key_col_idx < len(cells):
                        key_val = cells[wijziging_key_col_idx]
                        if re.match(r"^[A-Z][A-Z0-9_]+$", key_val):
                            line = line.replace(f" {key_val} ", f" {key_val.lower()} ", 1)
        else:
            # Non-table line: reset table state
            if not stripped.startswith("#"):
                expect_met_header = False
                in_wijziging_table = False
                wijziging_key_col_idx = -1

        new_lines.append(line)

    content = "\n".join(new_lines)

    if content != original:
        filepath.write_text(content)
        return True
    return False


def process_steps_py(filepath: Path) -> bool:
    """Process Python step definitions to lowercase parameter keys."""
    content = filepath.read_text()
    original = content

    # 1. Lowercase parameter key strings: context.parameters["BSN"] -> context.parameters["bsn"]
    def _lowercase_param_key(m: re.Match) -> str:
        prefix = m.group(1)
        key = m.group(2)
        suffix = m.group(3)
        if re.match(r"^[A-Z][A-Z0-9_]+$", key):
            return prefix + key.lower() + suffix
        return m.group(0)

    content = re.sub(
        r'(context\.parameters\[")([A-Z][A-Z0-9_]+)("\])',
        _lowercase_param_key,
        content,
    )

    # 2. Lowercase test_data key strings: context.test_data["KVK_NUMMER"] -> context.test_data["kvk_nummer"]
    content = re.sub(
        r'(context\.test_data\[")([A-Z][A-Z0-9_]+)("\])',
        _lowercase_param_key,
        content,
    )

    # 3. Lowercase param_mapping values
    # "ICT-project": "PROJECT_ID" -> "ICT-project": "project_id"
    def _lowercase_mapping_value(m: re.Match) -> str:
        prefix = m.group(1)
        val = m.group(2)
        suffix = m.group(3)
        if re.match(r"^[A-Z][A-Z0-9_]+$", val):
            return prefix + val.lower() + suffix
        return m.group(0)

    content = re.sub(
        r'("(?:ICT-project|organisatie|archiefstuk|project)":\s*")([A-Z][A-Z0-9_]+)(")',
        _lowercase_mapping_value,
        content,
    )

    # 4. Lowercase the generic entity param name construction
    # f"{entity_type.upper().replace('-', '_')}_ID" should become lowercase
    # Actually this needs a different approach - the .upper() call needs to become .lower()
    # But wait: after this migration, the YAML expects lowercase param names
    # So we need to change the code to produce lowercase param names
    content = content.replace(
        'param_name = param_mapping.get(entity_type, f"{entity_type.upper().replace(\'-\', \'_\')}_ID")',
        'param_name = param_mapping.get(entity_type, f"{entity_type.lower().replace(\'-\', \'_\')}_id")',
    )

    # 5. The archiefstuk step does heading.upper() - change to just heading (keep as-is from table)
    # Actually, since feature file headers for archiefstuk are already lowercase, heading.upper()
    # would make them uppercase. We need heading.lower() or just heading.
    # Let's check what the archiefstuk feature headers look like...
    # They use lowercase headers, so heading.upper() breaks things. Change to heading.lower()
    # Actually, looking at the step:
    #   context.parameters[heading.upper()] = value
    #   context.test_data[heading.upper()] = value
    # This means lowercase feature headers become UPPERCASE parameter keys.
    # After migration, YAML expects lowercase, so we should not upper() them.
    content = content.replace(
        "context.parameters[heading.upper()] = value",
        "context.parameters[heading] = value",
    )
    content = content.replace(
        "context.test_data[heading.upper()] = value",
        "context.test_data[heading] = value",
    )

    if content != original:
        filepath.write_text(content)
        return True
    return False


def process_python_file(filepath: Path) -> bool:
    """Process a generic Python file to lowercase parameter key strings."""
    content = filepath.read_text()
    original = content

    # Replace "BSN" -> "bsn" in parameter dicts
    content = re.sub(r'(parameters\s*=\s*\{")BSN(":\s*)', r'\1bsn\2', content)
    content = re.sub(r'(parameters\s*\|\s*\{")BSN(":\s*)', r'\1bsn\2', content)
    content = re.sub(r'(parameters\[")BSN("\])', r'\1bsn\2', content)
    content = re.sub(r'(parameters\[")KVK_NUMMER("\])', r'\1kvk_nummer\2', content)
    content = re.sub(r'(parameters\s*=\s*\{[^}]*")KVK_NUMMER(")', r'\1kvk_nummer\2', content)

    # For cases like: parameters.get("KVK_NUMMER")
    content = re.sub(r'(parameters\.get\(")KVK_NUMMER("\))', r'\1kvk_nummer\2', content)
    content = re.sub(r'(parameters\.get\(")BSN("\))', r'\1bsn\2', content)

    # For engine.py: if "BSN" in parameters -> if "bsn" in parameters
    content = re.sub(r'("BSN"\s+in\s+parameters)', r'"bsn" in parameters', content)
    content = re.sub(r'(parameters\[")BSN("\])', r'\1bsn\2', content)

    if content != original:
        filepath.write_text(content)
        return True
    return False


def process_profiles_yaml(filepath: Path) -> bool:
    """Process profiles.yaml to lowercase CHILDREN_DATA table keys and
    parameter-related uppercase keys that map to variable names."""
    content = filepath.read_text()
    original = content

    # Lowercase CHILDREN_DATA -> children_data (it's a source table key that
    # maps to parameter names in the engine)
    content = content.replace("CHILDREN_DATA:", "children_data:")

    # Also lowercase the case_seeds parameters section
    # These have parameter keys like KVK_NUMMER, ACTIVITEITSDATUM
    def _lowercase_case_seed_param(m: re.Match) -> str:
        indent = m.group(1)
        key = m.group(2)
        rest = m.group(3)
        if re.match(r"^[A-Z][A-Z0-9_]+$", key):
            return indent + key.lower() + rest
        return m.group(0)

    # Match parameter keys in case_seeds.parameters section
    content = re.sub(
        r"(^\s+)([A-Z][A-Z0-9_]+)(:\s+\")",
        _lowercase_case_seed_param,
        content,
        flags=re.MULTILINE,
    )

    if content != original:
        filepath.write_text(content)
        return True
    return False


def process_profile_loader(filepath: Path) -> bool:
    """Process profile_loader.py to match lowercased profile keys."""
    content = filepath.read_text()
    original = content

    content = content.replace('"CHILDREN_DATA"', '"children_data"')

    if content != original:
        filepath.write_text(content)
        return True
    return False


def process_engine_interface(filepath: Path) -> bool:
    """Process engine_interface.py to match lowercased profile keys."""
    content = filepath.read_text()
    original = content

    content = content.replace('"CHILDREN_DATA"', '"children_data"')

    if content != original:
        filepath.write_text(content)
        return True
    return False


def process_simulate_py(filepath: Path) -> bool:
    """Process simulate.py to match lowercased table/param keys."""
    content = filepath.read_text()
    original = content

    content = content.replace('"CHILDREN_DATA"', '"children_data"')

    if content != original:
        filepath.write_text(content)
        return True
    return False


def process_md_files(filepath: Path) -> bool:
    """Process markdown documentation files to lowercase $VARIABLE references."""
    content = filepath.read_text()
    original = content

    content = lowercase_dollar_vars(content)

    if content != original:
        filepath.write_text(content)
        return True
    return False


def main():
    changed_files = []

    # 1. Process YAML law files
    laws_dir = PROJECT_ROOT / "laws"
    yaml_count = 0
    for yaml_file in sorted(laws_dir.rglob("*.yaml")):
        if process_yaml_file(yaml_file):
            changed_files.append(str(yaml_file.relative_to(PROJECT_ROOT)))
            yaml_count += 1

    # Also process .md files in laws/ (documentation with $VARIABLE refs)
    md_count = 0
    for md_file in sorted(laws_dir.rglob("*.md")):
        if process_md_files(md_file):
            changed_files.append(str(md_file.relative_to(PROJECT_ROOT)))
            md_count += 1

    print(f"Processed {yaml_count} YAML files, {md_count} MD files in laws/")

    # 2. Process feature files
    features_dir = PROJECT_ROOT / "features"
    feature_count = 0
    for feature_file in sorted(features_dir.rglob("*.feature")):
        if process_feature_file(feature_file):
            changed_files.append(str(feature_file.relative_to(PROJECT_ROOT)))
            feature_count += 1
    print(f"Processed {feature_count} feature files")

    # 3. Process Python step definitions
    steps_file = features_dir / "steps" / "steps.py"
    if steps_file.exists():
        if process_steps_py(steps_file):
            changed_files.append(str(steps_file.relative_to(PROJECT_ROOT)))
            print("Processed steps.py")

    # 4. Process profiles.yaml
    profiles_file = PROJECT_ROOT / "data" / "profiles.yaml"
    if profiles_file.exists():
        if process_profiles_yaml(profiles_file):
            changed_files.append(str(profiles_file.relative_to(PROJECT_ROOT)))
            print("Processed profiles.yaml")

    # 5. Process other Python files
    python_files = [
        PROJECT_ROOT / "machine" / "engine.py",
        PROJECT_ROOT / "machine" / "service.py",
        PROJECT_ROOT / "machine" / "profile_loader.py",
        PROJECT_ROOT / "web" / "engines" / "engine_interface.py",
        PROJECT_ROOT / "web" / "routers" / "laws.py",
        PROJECT_ROOT / "web" / "routers" / "edit.py",
        PROJECT_ROOT / "web" / "routers" / "dashboard.py",
        PROJECT_ROOT / "web" / "routers" / "admin.py",
    ]
    for py_file in python_files:
        if py_file.exists():
            if py_file.name == "profile_loader.py":
                if process_profile_loader(py_file):
                    changed_files.append(str(py_file.relative_to(PROJECT_ROOT)))
                    print(f"Processed {py_file.name}")
            elif py_file.name == "engine_interface.py":
                if process_engine_interface(py_file):
                    changed_files.append(str(py_file.relative_to(PROJECT_ROOT)))
                    print(f"Processed {py_file.name}")
            else:
                if process_python_file(py_file):
                    changed_files.append(str(py_file.relative_to(PROJECT_ROOT)))
                    print(f"Processed {py_file.name}")

    # 6. Process simulate.py
    simulate_file = PROJECT_ROOT / "simulate.py"
    if simulate_file.exists():
        if process_simulate_py(simulate_file):
            changed_files.append(str(simulate_file.relative_to(PROJECT_ROOT)))
            print("Processed simulate.py")

    print(f"\nTotal: {len(changed_files)} files changed")

    if "--list" in sys.argv:
        for f in changed_files:
            print(f"  {f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
