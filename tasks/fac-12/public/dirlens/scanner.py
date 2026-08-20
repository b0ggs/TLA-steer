"""Filesystem walking helpers shared by every dirlens report."""

import os
from pathlib import Path


def iter_files(root):
    """Yield a Path for every regular file under *root*, recursively."""
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(str(root)):
        dirnames.sort()
        for name in sorted(filenames):
            path = Path(dirpath) / name
            if path.is_file():
                yield path


def rel_posix(path, root):
    """Return *path* relative to *root*, using forward slashes."""
    return Path(path).relative_to(Path(root)).as_posix()
