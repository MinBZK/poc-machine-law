#!/usr/bin/env python3
"""Reconcile stale source_ref_mapping.json keys against renamed YAML inputs.

For each JSON entry whose input name no longer exists in the matching law's
YAML, find the orphan YAML input that matches the JSON entry's `field` column
(taking the `partner_` prefix into account) and rewrite the JSON key.

After this script runs, every JSON entry refers to a real YAML input, and a
subsequent run of `migrate_source_mappings.py` will populate all 177 source: {}
blocks instead of just 114.

Usage:
    uv run python script/reconcile_source_mappings.py            # apply
    uv run python script/reconcile_source_mappings.py --dry-run  # preview
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
MAPPING_PATH = REPO_ROOT / "machine" / "source_ref_mapping.json"
LAWS_DIR = REPO_ROOT / "laws"


def load_yaml_inputs() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Returns (all_inputs_by_law, orphan_inputs_by_law).

    Orphan = input with empty `source: {}` block (no metadata yet).
    """
    all_inputs: dict[str, set[str]] = {}
    orphans: dict[str, set[str]] = {}
    for f in sorted(LAWS_DIR.rglob("*.yaml")):
        try:
            doc = yaml.safe_load(f.read_text())
        except Exception:
            continue
        if not doc or "$id" not in doc:
            continue
        lid = doc["$id"]
        for art in doc.get("articles") or []:
            for inp in art.get("machine_readable", {}).get("execution", {}).get("input") or []:
                if not isinstance(inp, dict):
                    continue
                name = inp.get("name")
                if not name:
                    continue
                all_inputs.setdefault(lid, set()).add(name)
                source = inp.get("source")
                if isinstance(source, dict) and not source:
                    orphans.setdefault(lid, set()).add(name)
    return all_inputs, orphans


def candidate_new_names(old_name: str, entry: dict) -> list[str]:
    """Return candidate new YAML input names for a stale JSON entry.

    Strategy: when an input was renamed, the new name is the column name
    (entry["field"]). When the old name carried a `partner_` prefix, the
    new name keeps it: `partner_<field>`. Try the prefixed form first so
    we don't accidentally collapse partner fields onto their non-partner
    counterparts.
    """
    field = entry.get("field")
    if not field:
        return []
    cands = []
    if old_name.startswith("partner_"):
        cands.append(f"partner_{field}")
    cands.append(field)
    return cands


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not MAPPING_PATH.exists():
        print(f"ERR: {MAPPING_PATH} not found", file=sys.stderr)
        sys.exit(1)

    src = json.loads(MAPPING_PATH.read_text())
    all_inputs, orphans_by_law = load_yaml_inputs()

    rename_map: dict[str, str] = {}
    unresolved: list[tuple[str, dict]] = []
    per_law_claimed: dict[str, set[str]] = {}

    for key, entry in src.items():
        law_id, old_name = key.rsplit(":", 1)
        if old_name in all_inputs.get(law_id, set()):
            continue  # not stale
        orphans = orphans_by_law.get(law_id, set())
        claimed = per_law_claimed.setdefault(law_id, set())
        for cand in candidate_new_names(old_name, entry):
            if cand in orphans and cand not in claimed:
                rename_map[key] = f"{law_id}:{cand}"
                claimed.add(cand)
                break
        else:
            unresolved.append((key, entry))

    print(f"Stale entries reconciled: {len(rename_map)}")
    print(f"Unresolved: {len(unresolved)}")
    if unresolved:
        print()
        print("Unresolved entries (no matching orphan with that field name):")
        for key, entry in unresolved:
            print(f"  {key}  field={entry.get('field')}  fields={entry.get('fields')}")
        print()
        print("ERROR: cannot proceed with unresolved entries.", file=sys.stderr)
        sys.exit(2)

    # Sample
    print()
    print("Sample renames:")
    for old_key, new_key in list(rename_map.items())[:5]:
        print(f"  {old_key}\n    -> {new_key}")
    if len(rename_map) > 5:
        print(f"  ... and {len(rename_map) - 5} more")

    if args.dry_run:
        print()
        print("(dry run — no file written)")
        return

    # Apply: build new dict preserving original ordering
    new_src = {}
    for key, entry in src.items():
        new_key = rename_map.get(key, key)
        new_src[new_key] = entry

    MAPPING_PATH.write_text(json.dumps(new_src, indent=2) + "\n")
    print()
    print(f"Wrote {MAPPING_PATH} ({len(new_src)} entries, {len(rename_map)} keys renamed)")


if __name__ == "__main__":
    main()
