"""Render TOC entries as a Markdown list."""


def render_markdown(entries):
    """Render entries as `- [Title](#anchor)` lines, 2 spaces per level."""
    lines = []
    for entry in entries:
        indent = "  " * (entry["level"] - 1)
        lines.append("{}- [{}](#{})".format(indent, entry["title"], entry["anchor"]))
    if not lines:
        return ""
    return "\n".join(lines) + "\n"
