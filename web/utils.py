"""
Utilities for the web application.
"""

import re

import markdown
from markupsafe import Markup


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
