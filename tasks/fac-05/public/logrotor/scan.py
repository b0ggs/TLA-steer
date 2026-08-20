"""Filesystem scanning helpers for logrotor."""

import os
import re

# A live log file: NAME.log
LOG_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+\.log$")

# A rotated archive: NAME.log.<14-digit UTC timestamp>
ARCHIVE_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+\.log\.\d{14}$")


def find_logs(directory):
    """Return live ``*.log`` filenames in *directory*, in ascending order."""
    names = []
    for name in os.listdir(directory):
        if LOG_PATTERN.match(name) and os.path.isfile(os.path.join(directory, name)):
            names.append(name)
    return sorted(names)
