"""Serialise parsed configuration mappings back to INI text."""

DEFAULT_DELIMITER = "="


def dumps(config, delimiter=DEFAULT_DELIMITER):
    """Render a parsed mapping as INI text.

    See docs/merging.md, section "Output format", for the exact layout.
    """
    lines = []
    for name, section in config.items():
        lines.append("[%s]" % name)
        for key in section:
            lines.append(key + delimiter + section[key])
        lines.append("")
    return "\n".join(lines)
