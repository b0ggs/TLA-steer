"""Load schema-lite rules files (required keys, types, ranges)."""
import json

TYPE_NAMES = {
    "int": int,
    "float": (int, float),
    "str": str,
    "bool": bool,
    "list": list,
    "dict": dict,
}


class RulesError(ValueError):
    """Raised when a rules file is malformed."""


def load_rules(path):
    """Return a rules dict with `required`, `types`, and `ranges` keys."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise RulesError("rules file must contain a JSON object")
    rules = {
        "required": data.get("required", []),
        "types": data.get("types", {}),
        "ranges": data.get("ranges", {}),
    }
    for name in rules["types"].values():
        if name not in TYPE_NAMES:
            raise RulesError("unknown type name: %s" % name)
    return rules
