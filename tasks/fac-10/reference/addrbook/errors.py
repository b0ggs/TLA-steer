"""Exception types used across addrbook."""


class AddressBookError(Exception):
    """Base class for all addrbook errors."""


class DuplicateKeyError(AddressBookError):
    """Raised when strict deduplication encounters a repeated key value."""
