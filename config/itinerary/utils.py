from __future__ import annotations

from django.utils.html import escape
from django.utils.safestring import mark_safe


def _basic_markdown_to_html(text: str) -> str:
    """Fallback converter when python-markdown is unavailable."""
    lines = text.splitlines()
    html_parts: list[str] = []
    paragraph: list[str] = []
    in_ul = False
    in_ol = False
    in_code = False

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            html_parts.append("</ul>")
            in_ul = False
        if in_ol:
            html_parts.append("</ol>")
            in_ol = False

    def flush_paragraph():
        nonlocal paragraph
        if paragraph:
            html_parts.append(f"<p>{' '.join(paragraph)}</p>")
            paragraph = []

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            if in_code:
                html_parts.append("</code></pre>")
                in_code = False
            else:
                close_lists()
                html_parts.append("<pre><code>")
                in_code = True
            continue

        if in_code:
            html_parts.append(escape(line) + "\n")
            continue

        if not stripped:
            flush_paragraph()
            close_lists()
            continue

        if stripped.startswith("#"):
            flush_paragraph()
            close_lists()
            level = len(stripped) - len(stripped.lstrip("#"))
            level = max(1, min(level, 6))
            content = stripped[level:].strip()
            html_parts.append(f"<h{level}>{escape(content)}</h{level}>")
            continue

        if stripped.startswith(("- ", "* ")):
            flush_paragraph()
            if in_ol:
                html_parts.append("</ol>")
                in_ol = False
            if not in_ul:
                html_parts.append("<ul>")
                in_ul = True
            html_parts.append(f"<li>{escape(stripped[2:].strip())}</li>")
            continue

        if stripped[0].isdigit():
            number_parts = stripped.split(". ", 1)
            if len(number_parts) == 2 and number_parts[0].isdigit():
                flush_paragraph()
                if in_ul:
                    html_parts.append("</ul>")
                    in_ul = False
                if not in_ol:
                    html_parts.append("<ol>")
                    in_ol = True
                html_parts.append(f"<li>{escape(number_parts[1].strip())}</li>")
                continue

        paragraph.append(escape(stripped))

    flush_paragraph()
    if in_ul:
        html_parts.append("</ul>")
    if in_ol:
        html_parts.append("</ol>")
    if in_code:
        html_parts.append("</code></pre>")

    if not html_parts:
        return f"<p>{escape(text)}</p>"
    return "".join(html_parts)


def render_markdown(text: str) -> str:
    """Convert markdown text to safe HTML for template rendering."""
    if not text:
        return ""

    try:
        import markdown
    except ImportError:
        html = _basic_markdown_to_html(text)
    else:
        html = markdown.markdown(text, extensions=["extra", "sane_lists"])

    return mark_safe(html)
