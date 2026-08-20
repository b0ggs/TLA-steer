"""pathsieve - a small gitignore-style include/exclude filter for paths."""

__version__ = "0.4.1"

from .engine import Sieve
from .errors import PatternError
from .loader import load_file, load_text

__all__ = [
    "PatternError",
    "Sieve",
    "load_file",
    "load_text",
    "filter_paths",
    "__version__",
]


def filter_paths(paths, patterns):
    """Return the paths from *paths* that survive filtering by *patterns*."""
    sieve = Sieve(patterns)
    return [p for p in paths if not sieve.excludes(p)]
