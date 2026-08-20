"""durafmt: parse and format compact duration strings."""

from durafmt.parser import parse
from durafmt.formatter import format_duration, format_hours

__version__ = "1.2.0"

__all__ = ["parse", "format_duration", "format_hours", "__version__"]
