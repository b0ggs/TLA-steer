"""Archive pruning for logrotor."""

import os

from logrotor import scan


def select_prunable(directory, keep):
    """Return archive filenames to delete, in ascending filename order.

    For each log base name the *keep* newest archives (largest
    timestamps) are retained; every older archive of that base name is
    selected for deletion.
    """
    groups = {}
    for name in scan.find_archives(directory):
        base, _, _ = name.rpartition(".")
        groups.setdefault(base, []).append(name)
    doomed = []
    for base in groups:
        archives = sorted(groups[base])
        if keep > 0:
            doomed.extend(archives[:-keep])
        else:
            doomed.extend(archives)
    return sorted(doomed)


def prune_directory(directory, keep=5, dry_run=False):
    """Delete prunable archives (unless *dry_run*) and return their names."""
    doomed = select_prunable(directory, keep)
    if not dry_run:
        for name in doomed:
            os.remove(os.path.join(directory, name))
    return doomed
