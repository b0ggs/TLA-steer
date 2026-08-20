"""Parser for the inimerge INI dialect.

See docs/merging.md for the grammar accepted by :func:`parse`.
"""

from inimerge.errors import ParseError

COMMENT_CHARS = ("#", ";")


def parse(text):
    """Parse INI text into a dict mapping section names to key/value dicts.

    Sections and keys keep their input order.  Values are always strings.
    A line of the form ``key =`` with no value assigns the empty string.
    Keys that appear before any section header are stored under the empty
    section name "".
    """
    config = {}
    current = None
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith(COMMENT_CHARS):
            continue
        if line.startswith("[") and line.endswith("]"):
            name = line[1:-1].strip()
            current = config.setdefault(name, {})
            continue
        if "=" not in line:
            raise ParseError(
                "line %d: expected 'key = value' or '[section]'" % lineno
            )
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if current is None:
            current = config.setdefault("", {})
        current[key] = value
    return config
