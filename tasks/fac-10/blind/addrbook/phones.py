"""Phone-number normalization helpers."""


def normalize_phone(raw):
    """Normalize a phone number.

    Returns NANP numbers in +1-XXX-XXX-XXXX form.

    Non-NANP inputs are reduced to their digits only.
    """
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return "+1-{}-{}-{}".format(digits[:3], digits[3:6], digits[6:])
    return digits
