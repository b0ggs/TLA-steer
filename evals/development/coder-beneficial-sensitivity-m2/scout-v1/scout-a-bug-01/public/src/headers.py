"""Header lookup helpers."""


def get_header(headers, name, default=None):
    """Return a header value when its key matches exactly."""
    return headers.get(name, default)
