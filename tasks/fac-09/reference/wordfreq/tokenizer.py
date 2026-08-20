"""Turn raw text into a list of lowercase words."""

import re

_WORD_RE = re.compile(r"[a-z0-9']+")


def tokenize(text):
    """Return the words in *text* as a list of lowercase strings.

    Words are maximal runs of ASCII letters, digits, and apostrophes;
    leading and trailing apostrophes are stripped.  Everything else is
    treated as a separator.
    """
    words = []
    for raw in _WORD_RE.findall(text.lower()):
        word = raw.strip("'")
        if word:
            words.append(word)
    return words
