"""Output rendering for colstat summaries."""

import json


def render_json(summary):
    """Render a summary mapping as pretty-printed JSON."""
    return json.dumps(summary, indent=2)


def render_table(summary):
    """Render a summary mapping as aligned key/value lines."""
    width = max(len(key) for key in summary)
    return "\n".join("%-*s %s" % (width, key, value) for key, value in summary.items())
