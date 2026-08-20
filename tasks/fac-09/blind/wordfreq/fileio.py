"""Reading input files for the CLI."""


def read_texts(paths):
    """Read every path as UTF-8 text and return the contents as a list."""
    texts = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as handle:
            texts.append(handle.read())
    return texts
