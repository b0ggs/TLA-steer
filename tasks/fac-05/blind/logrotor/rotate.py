"""Log rotation for logrotor."""

import os
import time

from logrotor import scan


def timestamp(now=None):
    """Return a 14-digit UTC timestamp string (YYYYMMDDHHMMSS)."""
    if now is None:
        now = time.gmtime()
    return time.strftime("%Y%m%d%H%M%S", now)


def rotate_directory(directory):
    """Rotate every ``*.log`` file in *directory*.

    Each ``NAME.log`` is renamed to ``NAME.log.<TS>`` and an empty
    ``NAME.log`` is recreated in its place.  Returns a list of
    ``(log_name, archive_name)`` pairs in ascending log-name order.
    """
    rotated = []
    stamp = timestamp()
    for name in scan.find_logs(directory):
        source = os.path.join(directory, name)
        archive = name + "." + stamp
        os.rename(source, os.path.join(directory, archive))
        with open(source, "w"):
            pass
        rotated.append((name, archive))
    return rotated
