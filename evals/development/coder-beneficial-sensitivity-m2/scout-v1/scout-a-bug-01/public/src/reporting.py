"""Human-readable header reports."""


def render_header(headers, name, missing="<missing>"):
    """Render one present header."""
    return f"{name}={headers.get(name, missing)}"
