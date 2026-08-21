"""Rendering helpers for frequency reports."""


def sorted_items(counts):
    """Return (word, count) pairs sorted by descending count, ties alphabetical."""
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def render_table(counts):
    """Render a full frequency table: one 'word count' line per distinct word."""
    return ["%s %d" % (word, count) for word, count in sorted_items(counts)]


def summarize(counts):
    """Render summary lines for *counts*, or return None when it is empty."""
    if not counts:
        return None

    top_word, top_count = sorted_items(counts)[0]
    return [
        "total_words: %d" % sum(counts.values()),
        "unique_words: %d" % len(counts),
        "top_word: %s (%d)" % (top_word, top_count),
    ]
