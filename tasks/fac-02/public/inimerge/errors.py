"""Exception types raised by inimerge."""


class IniMergeError(Exception):
    """Base class for all inimerge errors."""


class ParseError(IniMergeError):
    """Raised when INI text does not match the accepted grammar."""
