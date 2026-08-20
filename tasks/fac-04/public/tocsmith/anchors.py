"""GitHub-style anchor slugs for Markdown headings."""

import re

_DISALLOWED = re.compile(r"[^0-9a-z _-]")


def slugify(title):
    """Lowercase, drop punctuation, and turn spaces into hyphens."""
    slug = title.strip().lower()
    slug = _DISALLOWED.sub("", slug)
    slug = slug.replace(" ", "-")
    return slug


class AnchorRegistry:
    """Deduplicates anchors the way GitHub does: install, install-1, ..."""

    def __init__(self):
        self._seen = {}

    def anchor_for(self, title):
        base = slugify(title)
        count = self._seen.get(base)
        if count is None:
            self._seen[base] = 0
            return base
        self._seen[base] = count + 1
        return "{}-{}".format(base, count + 1)
