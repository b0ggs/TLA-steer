"""Rendering helpers for frequency reports."""


def sorted_items(counts):
    """Return (word, count) pairs sorted by descending count, ties alphabetical."""
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def render_table(counts):
    """Render a full frequency table: one 'word count' line per distinct word."""
    return ["%s %d" % (word, count) for word, count in sorted_items(counts)]


def summarize(counts):
    """Summarize a word-count mapping for the stats subcommand.

    Returns None when given an empty mapping; otherwise returns a dict with
    the total number of words, the number of distinct words, and the top
    word (ties broken alphabetically) with its count.
    """
    if not counts:
        return None
    top_word = min(counts, key=lambda word: (-counts[word], word))
    return {
        "total": sum(counts.values()),
        "unique": len(counts),
        "top_word": top_word,
        "top_count": counts[top_word],
    }
