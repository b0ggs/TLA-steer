"""Record-level normalization for address-book entries."""

from . import phones


def clean_name(raw):
    """Collapse every run of whitespace inside a name."""
    return " ".join(raw.split())


def normalize_email(raw):
    """Lowercase an e-mail address and strip surrounding whitespace."""
    return raw.strip().lower()


def normalize_record(record):
    """Return a normalized copy of one contact record."""
    normalized = dict(record)
    normalized["name"] = clean_name(record.get("name", ""))
    normalized["email"] = normalize_email(record.get("email", ""))
    normalized["phones"] = [
        phones.normalize_phone(value) for value in record.get("phones", [])
    ]
    return normalized
