"""What can go wrong reaching stored files."""
from __future__ import annotations


class StorageUnavailable(RuntimeError):
    """The store isn't configured or can't be reached."""


class StoredFileMissing(LookupError):
    """No object is stored under the key."""
