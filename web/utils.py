"""
Utilities for the web application.
"""

import re

import markdown
from markupsafe import Markup

# Mapping from law names (as used in YAML) to BWB IDs
LAW_NAME_TO_BWB = {
    # Toeslagen
    "wet_op_de_zorgtoeslag": "BWBR0018451",
    "zorgtoeslagwet": "BWBR0018451",
    "wet_op_de_huurtoeslag": "BWBR0008659",
    "wet_kinderopvang": "BWBR0017017",
    # Sociale zekerheid
    "algemene_ouderdomswet": "BWBR0002221",
    "participatiewet": "BWBR0015703",
    "participatiewet/bijstand": "BWBR0015703",
    # Belastingen
    "wet_inkomstenbelasting": "BWBR0011353",
    # Kieswet
    "kieswet": "BWBR0004627",
    # Algemeen bestuursrecht
    "awb": "BWBR0005537",
    "awb/bezwaar": "BWBR0005537",
    "awb/beroep": "BWBR0005537",
}


def get_bwb_id(law_name: str) -> str | None:
    """Get BWB ID for a law name."""
    # Direct lookup
    if law_name in LAW_NAME_TO_BWB:
        return LAW_NAME_TO_BWB[law_name]

    # Try without service prefix (e.g., "participatiewet/bijstand" -> "participatiewet")
    base_law = law_name.split("/")[0]
    if base_law in LAW_NAME_TO_BWB:
        return LAW_NAME_TO_BWB[base_law]

    return None


def get_law_url(law_name: str, service: str = None) -> str | None:
    """Get the /wetten URL for a law."""
    bwb_id = get_bwb_id(law_name)
    if bwb_id:
        return f"/wetten/{bwb_id}"

    return None


def format_message(text: str, is_user_message: bool = False) -> Markup:
    """
    Format a message with markdown for server-side rendering.

    Args:
        text: The text to format
        is_user_message: Whether this is a user message (only convert URLs)

    Returns:
        HTML-rendered version of the text
    """
    if not text:
        return Markup("")

    # URL regex pattern
    url_regex = r"(https?://[^\s]+)"

    # For user messages, only convert URLs (no markdown)
    if is_user_message:
        # Convert URLs to actual links
        formatted_text = re.sub(url_regex, r'<a href="\1" target="_blank" class="underline">\1</a>', text)
        return Markup(formatted_text)

    # For bot messages, apply markdown rendering
    try:
        # First convert URLs to markdown links if they're not already in a link format
        text_with_links = re.sub(
            url_regex,
            lambda m: m.group(0)
            if "[" in text[: m.start()] and "](" in text[m.start() :]
            else f"[{m.group(0)}]({m.group(0)})",
            text,
        )

        # Configure markdown extensions
        md = markdown.Markdown(extensions=["extra", "nl2br", "sane_lists"], output_format="html5")

        # Convert markdown to HTML
        html = md.convert(text_with_links)
        return Markup(html)
    except Exception as e:
        print(f"Error parsing markdown: {e}")
        return Markup(text)  # Fallback to plain text
