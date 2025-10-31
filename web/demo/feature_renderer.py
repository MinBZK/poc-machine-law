"""Gherkin feature renderer for demo mode."""

import html
from typing import Any

# Dutch translations for Gherkin keywords
KEYWORD_TRANSLATIONS = {
    "Feature:": "Functionaliteit:",
    "Background:": "Achtergrond:",
    "Scenario:": "Scenario:",
    "Scenario Outline:": "Abstract Scenario:",
    "Examples:": "Voorbeelden:",
    "Given ": "Gegeven ",
    "When ": "Als ",
    "Then ": "Dan ",
    "And ": "En ",
    "But ": "Maar ",
    # Also handle without trailing space for keyword-only cases
    "Given": "Gegeven",
    "When": "Als",
    "Then": "Dan",
    "And": "En",
    "But": "Maar",
}


def translate_keyword(keyword: str) -> str:
    """Translate Gherkin keyword from English to Dutch."""
    return KEYWORD_TRANSLATIONS.get(keyword, keyword)


def render_feature_to_html(parsed_feature: dict[str, Any]) -> str:
    """
    Render parsed Gherkin feature to HTML with syntax highlighting.
    Filters out scenarios tagged with @ui or @browser.

    Args:
        parsed_feature: Parsed feature dict from feature_parser

    Returns:
        HTML string with collapsible scenarios and syntax highlighting
    """
    html_parts = []
    html_parts.append('<div class="gherkin-content">')
    excluded_tags = {"ui", "browser"}

    # Feature header
    if parsed_feature.get("feature"):
        feature = parsed_feature["feature"]
        html_parts.append(f'<div class="gherkin-feature">')
        html_parts.append(f'  <span class="gherkin-keyword">{translate_keyword("Feature:")}</span>')
        html_parts.append(f'  <span class="gherkin-name">{html.escape(feature["name"])}</span>')

        # Feature description
        if feature.get("description"):
            html_parts.append('  <div class="gherkin-description">')
            for line in feature["description"]:
                html_parts.append(f"    <div>{html.escape(line)}</div>")
            html_parts.append("  </div>")

        html_parts.append("</div>")

    # Background
    if parsed_feature.get("background"):
        background = parsed_feature["background"]
        html_parts.append('<div class="gherkin-background">')
        html_parts.append(f'  <span class="gherkin-keyword">{translate_keyword("Background:")}</span>')
        html_parts.append('  <div class="gherkin-steps">')

        for step in background["steps"]:
            html_parts.append(render_step(step))

        html_parts.append("  </div>")
        html_parts.append("</div>")

    # Filter and render scenarios
    scenarios = parsed_feature.get("scenarios", [])
    runnable_scenarios = [
        (idx, scenario)
        for idx, scenario in enumerate(scenarios)
        if not any(tag in excluded_tags for tag in scenario.get("tags", []))
    ]

    for idx, scenario in runnable_scenarios:
        html_parts.append(render_scenario(scenario, idx))

    # Show message if scenarios were filtered
    filtered_count = len(scenarios) - len(runnable_scenarios)
    if filtered_count > 0:
        html_parts.append('<div class="gherkin-filtered-notice">')
        html_parts.append(f"  <em>Let op: {filtered_count} scenario(s) verborgen (vereisen browser/UI setup)</em>")
        html_parts.append("</div>")

    html_parts.append("</div>")
    return "\n".join(html_parts)


def render_scenario(scenario: dict[str, Any], index: int) -> str:
    """Render a single scenario with collapse functionality."""
    html_parts = []

    scenario_type = "Scenario Outline:" if scenario.get("type") == "outline" else "Scenario:"
    translated_type = translate_keyword(scenario_type)

    html_parts.append(f'<div class="gherkin-scenario collapsed" data-scenario-index="{index}">')

    # Scenario header (always visible)
    html_parts.append('  <div class="gherkin-scenario-header" onclick="toggleScenario(this)">')
    html_parts.append('    <span class="collapse-icon">▶</span>')
    html_parts.append(f'    <span class="gherkin-keyword">{translated_type}</span>')
    html_parts.append(f'    <span class="gherkin-name">{html.escape(scenario["name"])}</span>')
    html_parts.append(
        f'    <button class="btn-run" onclick="event.stopPropagation(); runScenario(\'{index}\')">Uitvoeren ▶</button>'
    )
    html_parts.append("  </div>")

    # Scenario content (collapsible)
    html_parts.append('  <div class="gherkin-scenario-content">')
    html_parts.append('    <div class="gherkin-steps">')

    for step in scenario.get("steps", []):
        html_parts.append("      " + render_step(step))

    html_parts.append("    </div>")

    # Examples for Scenario Outline
    if scenario.get("examples"):
        examples = scenario["examples"]
        html_parts.append('    <div class="gherkin-examples">')
        html_parts.append(f'      <span class="gherkin-keyword">{translate_keyword("Examples:")}</span>')

        if examples.get("table"):
            html_parts.append("      " + render_table(examples["table"]))

        html_parts.append("    </div>")

    html_parts.append("  </div>")
    html_parts.append("</div>")

    return "\n".join(html_parts)


def render_step(step: dict[str, Any]) -> str:
    """Render a single Gherkin step."""
    html_parts = []

    translated_keyword = translate_keyword(step["keyword"])
    html_parts.append('<div class="gherkin-step">')
    html_parts.append(f'  <span class="gherkin-step-keyword">{html.escape(translated_keyword)}</span>')
    html_parts.append(f'  <span class="gherkin-step-text">{html.escape(step["text"])}</span>')

    # Table (for data tables in steps)
    if step.get("table"):
        html_parts.append("  " + render_table(step["table"]))

    html_parts.append("</div>")

    return "\n".join(html_parts)


def render_table(table_data: list[list[str]]) -> str:
    """Render a Gherkin table."""
    html_parts = []

    html_parts.append('<table class="gherkin-table">')

    # First row is header
    if table_data:
        html_parts.append("  <thead>")
        html_parts.append("    <tr>")
        for cell in table_data[0]:
            html_parts.append(f"      <th>{html.escape(cell)}</th>")
        html_parts.append("    </tr>")
        html_parts.append("  </thead>")

    # Remaining rows are data
    if len(table_data) > 1:
        html_parts.append("  <tbody>")
        for row in table_data[1:]:
            html_parts.append("    <tr>")
            for cell in row:
                html_parts.append(f"      <td>{html.escape(cell)}</td>")
            html_parts.append("    </tr>")
        html_parts.append("  </tbody>")

    html_parts.append("</table>")

    return "\n".join(html_parts)
