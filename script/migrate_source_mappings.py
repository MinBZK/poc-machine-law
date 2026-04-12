#!/usr/bin/env python3
"""Migrate machine/source_ref_mapping.json into the YAML law files themselves.

For each entry "law_id:input_name" in source_ref_mapping.json, finds the
matching YAML file in laws/, locates the input by name in the YAML article's
machine_readable.execution.input list, and merges the table/field/select_on/
fields/source_type data into the input's source: {} block.

Strategy: surgical text-based edit. We use ruamel.yaml only to LOCATE inputs
(via line-mark info) and to RENDER the new source: {} block; we then splice
the rendered block into the original file text. This preserves all surrounding
formatting (long string folding, URL line breaks, comments, blank lines) byte
for byte except for the spliced region.

Usage:
    uv run python script/migrate_source_mappings.py            # apply to all
    uv run python script/migrate_source_mappings.py --dry-run  # preview only
    uv run python script/migrate_source_mappings.py --law alcoholwet/register_sociale_hygiene
"""

import argparse
import io
import json
import sys
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

REPO_ROOT = Path(__file__).parent.parent
MAPPING_PATH = REPO_ROOT / "machine" / "source_ref_mapping.json"
LAWS_DIR = REPO_ROOT / "laws"

# Fields we copy from the JSON entry into source: {}
MIGRATION_FIELDS = ("table", "field", "select_on", "fields", "source_type")


def make_yaml() -> YAML:
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=2, offset=0)
    return yaml


def build_law_index() -> dict[str, list[Path]]:
    """Map $id → list of file paths. Multiple files share an $id when there
    are dated versions of the same law (e.g. TOESLAGEN-2024-01-01 and 2025-01-01).
    """
    yaml = make_yaml()
    index: dict[str, list[Path]] = {}
    for f in sorted(LAWS_DIR.rglob("*.yaml")):
        try:
            with open(f) as fh:
                doc = yaml.load(fh)
        except Exception as e:
            print(f"WARN: failed to parse {f}: {e}", file=sys.stderr)
            continue
        if not doc or "$id" not in doc:
            continue
        index.setdefault(doc["$id"], []).append(f)
    return index


def to_ruamel(value):
    """Convert plain Python list/dict from JSON to ruamel CommentedMap/Seq."""
    if isinstance(value, dict):
        m = CommentedMap()
        for k, v in value.items():
            m[k] = to_ruamel(v)
        return m
    if isinstance(value, list):
        s = CommentedSeq()
        for v in value:
            s.append(to_ruamel(v))
        return s
    return value


def render_source_block(entry: dict, yaml: YAML, base_indent: int) -> str:
    """Render the source: {} mapping body for splicing into the file.

    Returns text starting with "source:\n" and ending with a newline. The
    rendered lines are indented to base_indent (the column of the leading "-"
    of the input list item parent +2 for the field key, e.g. 8 spaces for
    an input nested under articles[0].machine_readable.execution.input).
    """
    source_map = CommentedMap()
    for key in MIGRATION_FIELDS:
        if key in entry:
            source_map[key] = to_ruamel(entry[key])

    wrapper = CommentedMap()
    wrapper["source"] = source_map

    buf = io.StringIO()
    yaml.dump(wrapper, buf)
    text = buf.getvalue()

    # Re-indent every non-empty line by base_indent spaces.
    indent = " " * base_indent
    lines = text.splitlines()
    indented = [indent + line if line else line for line in lines]
    return "\n".join(indented) + "\n"


def find_inputs_with_lines(doc: CommentedMap) -> dict[str, tuple[int, int, bool]]:
    """Walk articles → execution.input.

    Returns {input_name: (source_key_line, source_key_col, has_source_key)}.
    If the input has no `source` key at all, has_source_key is False and
    source_key_line/col point to the input's `- name:` list-item line.
    """
    results: dict[str, tuple[int, int, bool]] = {}
    articles = doc.get("articles") or []
    for article in articles:
        mr = (article or {}).get("machine_readable")
        if not mr:
            continue
        execution = mr.get("execution")
        if not execution:
            continue
        inputs = execution.get("input")
        if not inputs:
            continue
        for i, inp in enumerate(inputs):
            if not isinstance(inp, CommentedMap):
                continue
            name = inp.get("name")
            if not name:
                continue
            if "source" in inp:
                line, col = inp.lc.key("source")
                results[name] = (line, col, True)
            else:
                line, col = inputs.lc.item(i)
                results[name] = (line, col, False)
    return results


def splice_existing_source(
    text: str,
    source_line: int,
    source_col: int,
    rendered_source: str,
) -> str:
    """Replace the source: {...} block at (source_line, source_col) with rendered_source.

    rendered_source is a string starting with `<indent>source:\\n` where indent
    matches source_col. Determines the existing block's extent by finding lines
    that are indented strictly deeper than source_col, plus the source: line
    itself (whether inline like `source: {}` or multi-line).
    """
    lines = text.splitlines(keepends=True)
    n = len(lines)

    block_start = source_line
    src_line_text = lines[source_line].rstrip("\n")
    src_value = src_line_text[source_col + len("source:") :].strip()

    if src_value:
        # Inline form like "source: {}" — only that one line is the block
        block_end = source_line + 1
    else:
        # Multi-line form: include all subsequent lines indented > source_col
        j = source_line + 1
        deeper_prefix = " " * (source_col + 1)
        while j < n:
            line = lines[j]
            if not line.strip():
                # Blank line: peek ahead
                k = j + 1
                while k < n and not lines[k].strip():
                    k += 1
                if k < n and lines[k].startswith(deeper_prefix):
                    j = k + 1
                    continue
                break
            if line.startswith(deeper_prefix):
                j += 1
            else:
                break
        block_end = j

    new_lines = lines[:block_start] + [rendered_source] + lines[block_end:]
    return "".join(new_lines)


def insert_source_after_input(
    text: str,
    input_line: int,
    input_col: int,
    rendered_source: str,
) -> str:
    """Insert a new source: block as a sibling key inside the input dict.

    The input list item starts at input_line (the `- name: foo` line). The
    sibling key indent is input_col + 2. We find the end of this input dict
    (next list item at input_col, or dedent) and insert just before that.
    rendered_source must already be indented to input_col + 2.
    """
    lines = text.splitlines(keepends=True)
    n = len(lines)

    sibling_prefix = " " * (input_col + 2)
    list_marker_prefix = " " * input_col + "-"

    j = input_line + 1
    while j < n:
        line = lines[j]
        stripped = line.rstrip("\n")
        if not stripped:
            j += 1
            continue
        if stripped.startswith(list_marker_prefix):
            break
        if not stripped.startswith(sibling_prefix):
            break
        j += 1

    # Insert before line j
    new_lines = lines[:j] + [rendered_source] + lines[j:]
    return "".join(new_lines)


def migrate_one_file(
    yaml: YAML,
    file_path: Path,
    entries: dict[str, dict],
    dry_run: bool,
) -> tuple[int, list[str]]:
    """Apply all entries to one YAML file. Returns (count_updated, missing_input_names)."""
    text = file_path.read_text()
    with open(file_path) as fh:
        doc = yaml.load(fh)

    inputs_by_name = find_inputs_with_lines(doc)

    # Process in reverse line order so earlier line indices remain valid
    work = []
    missing: list[str] = []
    for input_name, entry in entries.items():
        loc = inputs_by_name.get(input_name)
        if loc is None:
            missing.append(input_name)
            continue
        work.append((loc[0], loc[1], loc[2], input_name, entry))
    work.sort(key=lambda t: t[0], reverse=True)

    updated = 0
    for line, col, has_source, input_name, entry in work:
        if has_source:
            # `col` is the column of the existing `source:` key
            rendered = render_source_block(entry, yaml, base_indent=col)
            text = splice_existing_source(text, line, col, rendered)
        else:
            # `col` is the column of the `- name:` list-item dash
            sibling_col = col + 2
            rendered = render_source_block(entry, yaml, base_indent=sibling_col)
            text = insert_source_after_input(text, line, col, rendered)
        updated += 1

    if updated and not dry_run:
        file_path.write_text(text)

    return updated, missing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="don't write files, just report")
    parser.add_argument("--law", help="only migrate a single law_id (for testing)")
    parser.add_argument("--diff", action="store_true", help="print before/after diff for first migrated file")
    args = parser.parse_args()

    if not MAPPING_PATH.exists():
        print(f"ERR: {MAPPING_PATH} not found", file=sys.stderr)
        sys.exit(1)

    with open(MAPPING_PATH) as f:
        raw = json.load(f)

    by_law: dict[str, dict[str, dict]] = {}
    for key, value in raw.items():
        if ":" not in key:
            print(f"WARN: skipping malformed key {key!r}", file=sys.stderr)
            continue
        law_id, input_name = key.split(":", 1)
        if args.law and law_id != args.law:
            continue
        by_law.setdefault(law_id, {})[input_name] = value

    if not by_law:
        print("Nothing to migrate.")
        return

    print(f"Building law index from {LAWS_DIR}...")
    index = build_law_index()
    print(f"  found {len(index)} laws")

    yaml = make_yaml()

    total_files = 0
    total_inputs = 0
    total_missing: list[tuple[str, str]] = []
    not_found_laws: list[str] = []

    diff_done = False
    for law_id, entries in sorted(by_law.items()):
        file_paths = index.get(law_id)
        if not file_paths:
            not_found_laws.append(law_id)
            continue

        for file_path in file_paths:
            original_text = file_path.read_text() if args.diff and not diff_done else None

            updated, missing = migrate_one_file(yaml, file_path, entries, args.dry_run)

            if updated:
                total_files += 1
                total_inputs += updated
                rel = file_path.relative_to(REPO_ROOT)
                print(f"  {rel}: {updated} input(s) updated")

                if args.diff and not diff_done and not args.dry_run:
                    new_text = file_path.read_text()
                    _print_diff(original_text, new_text, str(file_path))
                    diff_done = True

            for m in missing:
                total_missing.append((law_id, m))

    print()
    print("=" * 60)
    print(f"Files updated: {total_files}")
    print(f"Inputs updated: {total_inputs}")
    if not_found_laws:
        print(f"Laws not found in YAMLs ({len(not_found_laws)}):")
        for lid in not_found_laws:
            print(f"  - {lid}")
    if total_missing:
        print(f"Inputs not found in YAMLs ({len(total_missing)}):")
        for lid, name in total_missing[:50]:
            print(f"  - {lid}:{name}")
        if len(total_missing) > 50:
            print(f"  ... and {len(total_missing) - 50} more")
    if args.dry_run:
        print("(dry run — no files written)")


def _print_diff(before: str, after: str, path: str) -> None:
    import difflib

    diff = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=f"{path} (before)",
        tofile=f"{path} (after)",
        n=3,
    )
    print()
    print("=" * 60)
    print("DIFF for first migrated file:")
    print("=" * 60)
    for line in diff:
        print(line, end="")
    print()


if __name__ == "__main__":
    main()
