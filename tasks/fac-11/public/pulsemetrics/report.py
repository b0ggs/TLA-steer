"""Plain-text rendering of rollup summaries."""

DEFAULT_PRECISION = 2


def render_report(summary, precision=None):
    """Render one text line per metric from a rollup summary mapping."""
    if precision is None:
        precision = DEFAULT_PRECISION
    lines = []
    for metric, row in summary.items():
        lines.append(
            "%s: mean=%.*f min=%.*f max=%.*f (n=%d)"
            % (
                metric,
                precision,
                row["mean"],
                precision,
                row["min"],
                precision,
                row["max"],
                row["count"],
            )
        )
    return lines
