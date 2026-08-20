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


def _mtime_iso(timestamp):
    """Format *timestamp* in UTC, whole seconds, as YYYY-MM-DDTHH:MM:SSZ."""
    moment = datetime.fromtimestamp(int(timestamp), timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def newest_entries(root, limit):
    """Return dicts for the *limit* most recently modified files under *root*.

    Each dict has exactly two keys, ``path`` and ``mtime``. Entries are ordered
    newest first; equal modification times fall back to relative path order.
    An empty tree yields an empty list.
    """
    rows = []
    for path in iter_files(root):
        stat = path.stat()
        rows.append((stat.st_mtime, rel_posix(path, root)))
    rows.sort(key=lambda row: (-row[0], row[1]))
    return [
        {"path": rel, "mtime": _mtime_iso(mtime)} for mtime, rel in rows[:limit]
    ]


def newest_lines(root, limit):
    """Return ``<mtime>\\t<relative-path>`` lines, newest first."""
    return [
        "%s\t%s" % (entry["mtime"], entry["path"])
        for entry in newest_entries(root, limit)
    ]
