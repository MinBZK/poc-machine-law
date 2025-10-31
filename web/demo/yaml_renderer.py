"""YAML rendering and parsing utilities for demo mode."""

import html
import re
from pathlib import Path
from typing import Any

import yaml

from web.demo.demo_collapse_config import should_expand_in_demo_mode

# Global context for current law path (used during rendering)
_current_law_path: str | None = None


def discover_laws(law_dir: Path, grouped: bool = False) -> list[dict[str, Any]] | dict[str, list[dict[str, Any]]]:
    """
    Discover all law YAML files in the law directory.

    Args:
        law_dir: Base directory containing law files
        grouped: If True, return laws grouped by directory

    Returns:
        List of law dicts, or dict of {directory: [laws]} if grouped=True
    """
    laws = []

    for yaml_file in sorted(law_dir.rglob("*.yaml")):
        # Skip files in subdirectories like regelingen
        relative_path = yaml_file.relative_to(law_dir)

        try:
            with open(yaml_file) as f:
                data = yaml.safe_load(f)

            # Extract metadata
            law_info = {
                "path": str(relative_path.with_suffix("")),  # Remove .yaml extension
                "file_path": str(relative_path),
                "name": data.get("name", yaml_file.stem),
                "law": data.get("law", ""),
                "service": data.get("service", ""),
                "description": data.get("description", ""),
                "valid_from": str(data.get("valid_from", "")),
                "directory": str(relative_path.parent),  # Parent directory
            }
            laws.append(law_info)
        except Exception:
            # Skip files that can't be parsed
            continue

    if not grouped:
        return laws

    # Group by directory
    from collections import defaultdict

    grouped_laws = defaultdict(list)
    for law in laws:
        directory = law["directory"]
        grouped_laws[directory].append(law)

    # Convert to regular dict and sort directories
    return dict(sorted(grouped_laws.items()))


def parse_law_yaml(yaml_file: Path, law_dir: Path = None, law_path: str = None) -> dict[str, Any]:
    """
    Parse a law YAML file and prepare it for rendering.

    Detects service references for cross-law linking.

    Args:
        yaml_file: Path to the YAML file
        law_dir: Base directory for laws (default: Path("law"))
        law_path: Relative path used for demo config (e.g., "zorgtoeslagwet/TOESLAGEN-2025-01-01")
    """
    with open(yaml_file) as f:
        data = yaml.safe_load(f)

    # Discover all laws for cross-reference resolution
    if law_dir is None:
        law_dir = Path("law")

    all_laws = discover_laws(law_dir)

    # Store law_path in data for demo mode configuration
    if law_path:
        data["_law_path"] = law_path

    # Process the data to detect cross-references
    data = _detect_cross_references(data, all_laws=all_laws)

    return data


def _detect_cross_references(data: Any, path: str = "", all_laws: list[dict[str, Any]] = None) -> Any:
    """
    Recursively detect service_reference fields and mark them for linking.

    Adds a _link metadata field to enable automatic cross-law navigation.
    """
    if all_laws is None:
        all_laws = []

    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            if key == "service_reference" and isinstance(value, dict):
                # This is a cross-reference - add link metadata
                service = value.get("service")
                law = value.get("law")
                if service and law:
                    # Find matching law file
                    target_path = _find_law_path(law, service, all_laws)
                    if target_path:
                        value["_link"] = {
                            "target": target_path,
                            "display": f"{service}/{law}",
                        }
                new_data[key] = _detect_cross_references(value, f"{path}.{key}", all_laws)
            else:
                new_data[key] = _detect_cross_references(value, f"{path}.{key}", all_laws)
        return new_data
    elif isinstance(data, list):
        return [_detect_cross_references(item, f"{path}[]", all_laws) for item in data]
    else:
        return data


def _find_law_path(law: str, service: str, all_laws: list[dict[str, Any]]) -> str | None:
    """
    Find the full path to a law file based on law name and service.

    Args:
        law: The law identifier (e.g., "zvw", "wet_brp")
        service: The service identifier (e.g., "RVZ", "RvIG")
        all_laws: List of all discovered laws

    Returns:
        Full path like "zvw/RVZ-2024-01-01" or None if not found
    """
    # Try to find exact match on law and service
    for law_info in all_laws:
        if law_info["law"] == law and law_info["service"] == service:
            return law_info["path"]

    # Fallback: try to match just on law (take first match)
    for law_info in all_laws:
        if law_info["law"] == law:
            return law_info["path"]

    return None


def format_yaml_value(value: Any) -> str:
    """
    Format a YAML value for display.

    Handles special formatting for different types.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        # Handle multi-line strings
        if "\n" in value:
            return value.strip()
        return value
    elif value is None:
        return "null"
    else:
        return str(value)


def should_collapse_by_default(key: str) -> bool:
    """
    Determine if a section should be collapsed by default.

    legal_basis and long text sections are collapsed by default.
    """
    collapse_keys = {
        "legal_basis",
        "references",
        "explanation",
        "requirements",
        "actions",
    }
    return key in collapse_keys


def get_yaml_section_priority(key: str) -> int:
    """
    Get display priority for YAML sections.

    Lower numbers are more important and shown first.
    """
    priority_map = {
        "name": 0,
        "law": 1,
        "service": 2,
        "valid_from": 3,
        "description": 4,
        "properties": 10,
        "input": 11,
        "output": 12,
        "parameters": 13,
        "requirements": 20,
        "actions": 21,
        "legal_basis": 30,
        "references": 31,
    }
    return priority_map.get(key, 100)


def render_yaml_to_html(data: Any, level: int = 0, key: str = None, parent_path: str = "") -> str:
    """
    Render YAML data structure to HTML with collapsible sections.

    Args:
        data: The YAML data to render
        level: Current nesting level
        key: The key for this data element
        parent_path: Dot-separated path to parent (for demo collapse config)

    Returns:
        HTML string representing the YAML structure
    """
    global _current_law_path

    # Extract and set law_path from root data if available
    if isinstance(data, dict) and level == 0:
        _current_law_path = data.get("_law_path")

    if isinstance(data, dict):
        html_parts = []
        html_parts.append(f'<div class="yaml-object level-{level}">')

        for k, v in data.items():
            # Skip metadata fields
            if k in ("_link", "_law_path"):
                continue

            is_collapsible = isinstance(v, (dict, list))

            # Build current path for demo mode
            current_path = f"{parent_path}.{k}" if parent_path else k

            # Determine collapsed state (demo mode or default)
            demo_expand = should_expand_in_demo_mode(_current_law_path, current_path) if _current_law_path else None
            if demo_expand is not None:
                # Use demo mode configuration
                default_collapsed = not demo_expand
            else:
                # Use default collapse logic
                default_collapsed = should_collapse_by_default(k)

            collapsed_class = "collapsed" if default_collapsed else ""

            html_parts.append(f'<div class="yaml-section {collapsed_class}" data-key="{html.escape(k)}">')
            html_parts.append('  <div class="yaml-key-line" onclick="toggleSection(this)">')

            if is_collapsible:
                html_parts.append('    <span class="collapse-icon">▶</span>')
            else:
                html_parts.append('    <span class="collapse-icon-placeholder"></span>')

            html_parts.append(f'    <span class="yaml-key">{html.escape(k)}:</span>')

            # Add cross-law link if this is a service_reference
            if k == "service_reference" and isinstance(v, dict) and "_link" in v:
                link_info = v["_link"]
                html_parts.append(
                    f'    <a href="/demo/law/{html.escape(link_info["target"])}" class="cross-law-link">'
                    f"→ Go to {html.escape(link_info['display'])}</a>"
                )

            if not is_collapsible:
                html_parts.append(f'    <span class="yaml-value">{html.escape(format_yaml_value(v))}</span>')

            html_parts.append("  </div>")  # Close yaml-key-line

            if is_collapsible:
                html_parts.append('  <div class="yaml-value-content">')
                html_parts.append(render_yaml_to_html(v, level + 1, k, current_path))
                html_parts.append("  </div>")

            html_parts.append("</div>")  # Close yaml-section

        html_parts.append("</div>")  # Close yaml-object
        return "\n".join(html_parts)

    elif isinstance(data, list):
        html_parts = []
        html_parts.append(f'<div class="yaml-array level-{level}">')

        for idx, item in enumerate(data):
            # Check if item is a dict - if so, make it collapsible
            if isinstance(item, dict):
                # Try to get a label from the item
                # Prefer: name > output > field > subject > test.subject+value > test.operation > operation > "else" > index
                # Check for nested test fields (common in conditions)
                test_label = None
                if "test" in item and isinstance(item["test"], dict):
                    test_subject = item["test"].get("subject")
                    test_value = item["test"].get("value")
                    test_operation = item["test"].get("operation")

                    # Create a more specific label for test conditions
                    if test_subject and test_value is not None:
                        # Include the value to distinguish between different tests on same subject
                        # Convert boolean to lowercase string for consistency
                        if isinstance(test_value, bool):
                            value_str = str(test_value).lower()
                        else:
                            value_str = str(test_value)
                        test_label = f"{test_subject}={value_str}"
                    elif test_subject:
                        test_label = test_subject
                    elif test_operation:
                        test_label = test_operation

                # Check if this is an else block
                has_else = "else" in item

                # Try to get a meaningful label, including law field for references
                label = item.get(
                    "name",
                    item.get(
                        "output",
                        item.get(
                            "field",
                            item.get(
                                "subject",
                                item.get(
                                    "law",
                                    test_label or item.get("operation", "else" if has_else else f"Item {idx + 1}"),
                                ),
                            ),
                        ),
                    ),
                )

                # Build path for this array item
                item_path = f"{parent_path}.{label}" if parent_path else str(label)

                # Determine collapsed state (demo mode or default)
                demo_expand = should_expand_in_demo_mode(_current_law_path, item_path) if _current_law_path else None
                if demo_expand is not None:
                    default_collapsed = not demo_expand
                else:
                    default_collapsed = should_collapse_by_default(str(label))

                collapsed_class = "collapsed" if default_collapsed else ""

                html_parts.append(
                    f'  <div class="yaml-array-item yaml-section {collapsed_class}" data-key="{html.escape(str(label))}">'
                )
                html_parts.append('    <div class="yaml-key-line" onclick="toggleSection(this)">')
                html_parts.append('      <span class="collapse-icon">▶</span>')
                html_parts.append('      <span class="array-bullet">-</span>')
                html_parts.append(f'      <span class="yaml-key">{html.escape(str(label))}</span>')
                html_parts.append("    </div>")
                html_parts.append('    <div class="yaml-value-content">')
                html_parts.append(f"      {render_yaml_to_html(item, level + 1, key=None, parent_path=item_path)}")
                html_parts.append("    </div>")
                html_parts.append("  </div>")
            else:
                # Non-dict items: render as before (not collapsible)
                html_parts.append('  <div class="yaml-array-item">')
                html_parts.append('    <span class="array-bullet">-</span>')
                html_parts.append(f"    {render_yaml_to_html(item, level + 1, parent_path=parent_path)}")
                html_parts.append("  </div>")

        html_parts.append("</div>")
        return "\n".join(html_parts)

    else:
        # Primitive value
        return f'<span class="yaml-primitive">{html.escape(format_yaml_value(data))}</span>'
