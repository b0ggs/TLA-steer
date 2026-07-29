"""Canonical and legacy identifier parsing."""

from urllib.parse import unquote


ALLOWED_KINDS = {"job", "user"}


def parse_canonical_id(value):
    kind, separator, raw_number = value.partition(":")
    if separator != ":" or kind not in ALLOWED_KINDS or not raw_number.isdigit():
        raise ValueError(f"invalid canonical id: {value!r}")
    return kind, int(raw_number)


def _strip_legacy_prefix(value):
    decoded = unquote(value)
    if decoded.startswith("legacy-"):
        return decoded[len("legacy-") :]
    return decoded


def parse_id(value):
    return parse_canonical_id(_strip_legacy_prefix(value))


def format_id(kind, number):
    """Format an already validated identifier pair."""
    return f"{kind}:{number}"
