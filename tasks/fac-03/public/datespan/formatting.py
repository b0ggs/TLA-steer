"""Human-readable rendering of date spans."""


def format_span(start, end):
    """Render a span as 'START → END (N days)'."""
    days = (end - start).days
    return "{} → {} ({} days)".format(start.isoformat(), end.isoformat(), days)
