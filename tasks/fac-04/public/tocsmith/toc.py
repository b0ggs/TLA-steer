"""Build TOC entry dicts from scanned headings."""

from .anchors import AnchorRegistry


def build_entries(headings):
    """Turn Heading tuples into dicts with keys level, title, anchor, line."""
    registry = AnchorRegistry()
    entries = []
    for heading in headings:
        entries.append(
            {
                "level": heading.level,
                "title": heading.title,
                "anchor": registry.anchor_for(heading.title),
                "line": heading.line,
            }
        )
    return entries
