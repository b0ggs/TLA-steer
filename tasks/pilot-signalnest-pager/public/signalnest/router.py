"""Resolve user-facing aliases to canonical routes."""

from .generated_routes import ROUTES


class UnknownRoute(ValueError):
    """Raised when a route alias is not registered."""


def resolve_route(value: str) -> str:
    """Return the canonical route for *value*."""
    if not isinstance(value, str):
        raise TypeError("route alias must be a string")
    try:
        return ROUTES[value.lower()]
    except KeyError as exc:
        raise UnknownRoute(f"unknown route alias: {value}") from exc
