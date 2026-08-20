"""Extract ATX headings from Markdown text."""

import re
from collections import namedtuple

Heading = namedtuple("Heading", ["level", "title", "line"])

_ATX = re.compile(r"^(#{1,6}) (.+?)\s*$")
_FENCE = re.compile(r"^\s{0,3}(```|~~~)")


def scan_text(text):
    """Return a list of Heading(level, title, line) for ATX headings.

    Headings inside fenced code blocks are ignored.  A leading YAML
    front-matter block delimited by `---` lines is skipped.
    Line numbers are 1-based.
    """
    lines = text.splitlines()
    start = 0
    if lines and lines[0] == "---":
        for i in range(1, len(lines)):
            if lines[i] == "---":
                start = i + 1
                break
    headings = []
    in_fence = False
    for offset, line in enumerate(lines[start:], start=start):
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = _ATX.match(line)
        if match:
            headings.append(Heading(len(match.group(1)), match.group(2), offset + 1))
    return headings
