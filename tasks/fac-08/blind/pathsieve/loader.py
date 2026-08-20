"""Parsing of pattern lists from text and files."""

from .patterns import compile_pattern


def load_text(text):
    """Compile the pattern lines in *text* and return a list of rules.

    Blank lines and comment lines produce no rule.
    """
    rules = []
    for line in text.splitlines():
        if not line.strip():
            continue
        if line.lstrip().startswith("#"):
            continue
        rules.append(compile_pattern(line))
    return rules


def load_file(path, encoding="utf-8"):
    """Read the file at *path* and compile its pattern lines."""
    with open(path, "r", encoding=encoding) as handle:
        return load_text(handle.read())
