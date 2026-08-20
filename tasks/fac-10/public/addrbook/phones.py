"""Phone-number normalization helpers."""


def normalize_phone(raw):
    """Normalize a phone number.

    Strips punctuation and whitespace, returning the digits only.
    """
    return "".join(ch for ch in raw if ch.isdigit())
