"""Rendering helpers for frequency reports."""


def sorted_items(counts):
    """Return (word, count) pairs sorted by descending count, ties alphabetical."""
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def render_table(counts):
    """Render a full frequency table: one 'word count' line per distinct word."""
    return ["%s %d" % (word, count) for word, count in sorted_items(counts)]
