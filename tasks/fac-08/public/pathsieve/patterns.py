"""Pattern compilation for pathsieve.

Each pattern line becomes a :class:`Rule`. See docs/patterns.md for the
full syntax reference.
"""

import re

from .errors import PatternError


def _translate(body):
    """Translate a pattern body into an anchored regular expression source."""
    out = []
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == "*":
            if body.startswith("**", i):
                out.append(".*")
                i += 2
            else:
                out.append("[^/]*")
                i += 1
        elif ch == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(ch))
            i += 1
    return "".join(out)


class Rule:
    """A single compiled filter rule."""

    def __init__(self, pattern, body, negated):
        self.pattern = pattern
        self.body = body
        self.negated = negated
        self._source = _translate(body)

    def matches(self, path, ignore_case=False):
        """Return True when *path* matches this rule's pattern body.

        A body containing ``/`` is matched against the whole relative
        path; a body without ``/`` is matched against each path segment.
        """
        flags = re.IGNORECASE if ignore_case else 0
        rx = re.compile(self._source, flags)
        if path.startswith("./"):
            path = path[2:]
        path = path.strip("/")
        if "/" in self.body:
            return rx.fullmatch(path) is not None
        return any(rx.fullmatch(seg) is not None for seg in path.split("/"))

    def __repr__(self):
        return "Rule(%r)" % (self.pattern,)


def compile_pattern(text):
    """Compile one pattern line into a :class:`Rule`."""
    raw = text.strip()
    if not raw:
        raise PatternError("empty pattern")
    negated = raw.startswith("!")
    body = raw[1:].strip() if negated else raw
    body = body.rstrip("/")
    return Rule(raw, body, negated)
