"""Phone-number normalization helpers."""


def normalize_phone(raw):
    """Normalize a phone number.

    Returns NANP numbers in +1-XXX-XXX-XXXX form. Inputs whose digits do
    not form a 10-digit number (or an 11-digit number starting with 1)
    are returned as digits only.
    """
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return "+1-{}-{}-{}".format(digits[:3], digits[3:6], digits[6:])
    return digits
