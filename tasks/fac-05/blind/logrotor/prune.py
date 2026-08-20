"""Retention pruning for rotated log archives."""

import os

from logrotor import scan


def prune_directory(directory, keep=5, dry_run=False):
    """Remove old archives, keeping *keep* newest files for each log.

    Return the archive filenames selected for pruning in ascending order.
    When *dry_run* is true, report the same selection without deleting files.
    """
    if keep < 0:
        raise ValueError("keep must be non-negative")

    archives_by_log = {}
    for name in scan.find_archives(directory):
        log_name = name.rsplit(".", 1)[0]
        archives_by_log.setdefault(log_name, []).append(name)

    selected = []
    for archives in archives_by_log.values():
        selected.extend(archives if keep == 0 else archives[:-keep])
    selected.sort()

    if not dry_run:
        for name in selected:
            os.remove(os.path.join(directory, name))
    return selected
