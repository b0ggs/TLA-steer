"""Report builders that turn a directory tree into output lines."""

from .scanner import iter_files, rel_posix


def scan_lines(root):
    """Return ``<relative-path>\\t<size>`` lines sorted by path ascending."""
    rows = []
    for path in iter_files(root):
        rows.append((rel_posix(path, root), path.stat().st_size))
    rows.sort(key=lambda row: row[0])
    return ["%s\t%d" % row for row in rows]


def ext_lines(root):
    """Return ``<extension>\\t<count>`` lines sorted by extension ascending."""
    counts = {}
    for path in iter_files(root):
        label = path.suffix[1:] if path.suffix else "(none)"
        counts[label] = counts.get(label, 0) + 1
    return ["%s\t%d" % (label, counts[label]) for label in sorted(counts)]
