"""Small decimal ledger used by the evaluation fixture."""
from decimal import Decimal

CENT = Decimal("0.01")


def _money(value):
    value = Decimal(str(value))
    if not value.is_finite():
        raise ValueError("amount must be finite")
    return value.quantize(CENT)


def running_balances(opening, entries):
    balance = _money(opening)
    result = []
    for entry in entries:
        amount = _money(entry["amount"])
        if entry["kind"] == "credit":
            balance += amount
        elif entry["kind"] == "debit":
            balance -= amount
        else:
            raise ValueError("unsupported entry kind")
        result.append(format(balance, ".2f"))
    return result


def period_summary(opening, entries, start, end):
    raise NotImplementedError("period summaries are not available")
