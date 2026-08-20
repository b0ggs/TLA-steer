"""Record-level normalization for address-book entries."""

from . import phones


def clean_name(raw):
    """Collapse runs of any whitespace inside a name and strip the ends."""
    return " ".join(raw.split())


def normalize_email(raw):
    """Lowercase an e-mail address and strip surrounding whitespace."""
    return raw.strip().lower()


def normalize_record(record):
    """Normalize one contact record.

    Returns a new dict; the input record (including its "phones" list)
    is left unchanged.
    """
    out = dict(record)
    out["name"] = clean_name(record.get("name", ""))
    out["email"] = normalize_email(record.get("email", ""))
    out["phones"] = [phones.normalize_phone(value) for value in record.get("phones", [])]
    return out
