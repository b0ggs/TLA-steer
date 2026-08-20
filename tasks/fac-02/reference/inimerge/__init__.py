"""inimerge: merge layered INI-style configuration files."""

from inimerge.merger import merge, merge_all
from inimerge.parser import parse
from inimerge.writer import dumps

__version__ = "1.2.1"

__all__ = ["parse", "merge", "merge_all", "dumps", "__version__"]
