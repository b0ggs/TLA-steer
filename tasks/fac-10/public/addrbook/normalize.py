"""Record-level normalization for address-book entries."""

from . import phones


def clean_name(raw):
    """Collapse repeated spaces inside a name and drop empty chunks."""
    parts = [piece for piece in raw.split(" ") if piece]
    return " ".join(parts)


def normalize_email(raw):
    """Lowercase an e-mail address and strip surrounding whitespace."""
    return raw.strip().lower()


def normalize_record(record):
    """Normalize one contact record in place and return it."""
    record["name"] = clean_name(record.get("name", ""))
    record["email"] = normalize_email(record.get("email", ""))
    current = record.get("phones", [])
    for index, value in enumerate(current):
        current[index] = phones.normalize_phone(value)
    record["phones"] = current
    return record
