"""Merge parsed configuration layers."""


def merge(base, override):
    """Merge two parsed configuration mappings into a new mapping.

    Later layers take precedence over earlier layers.

    Sections present in either input appear in the result.  Sections are
    combined key by key; neither input mapping is modified.
    """
    result = {name: dict(section) for name, section in base.items()}
    for name, section in override.items():
        if name not in result:
            result[name] = dict(section)
            continue
        target = result[name]
        for key, value in section.items():
            target[key] = value
    return result


def merge_all(layers):
    """Fold an iterable of parsed layers into one mapping, left to right."""
    result = {}
    for layer in layers:
        result = merge(result, layer)
    return result
