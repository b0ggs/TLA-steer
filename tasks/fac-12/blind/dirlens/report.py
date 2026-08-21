"""Report builders that turn a directory tree into output lines."""

from datetime import datetime, timezone

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


def newest_entries(root, limit=5):
    """Return the newest files as ``path``/``mtime`` dictionaries."""
    rows = []
    for path in iter_files(root):
        mtime_ns = path.stat().st_mtime_ns
        rows.append((mtime_ns, rel_posix(path, root)))

    rows.sort(key=lambda row: (-row[0], row[1]))
    entries = []
    for mtime_ns, relative_path in rows[:limit]:
        timestamp = datetime.fromtimestamp(
            mtime_ns // 1_000_000_000, timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        entries.append({"path": relative_path, "mtime": timestamp})
    return entries
