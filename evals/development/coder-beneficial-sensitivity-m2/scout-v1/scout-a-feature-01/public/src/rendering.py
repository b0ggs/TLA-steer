"""Text rendering for summaries."""


def render_summary(counts):
    """Render counts in insertion order."""
    return ", ".join(f"{level}:{count}" for level, count in counts.items())
