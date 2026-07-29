"""Small in-memory cache with injectable time."""

import time


class Cache:
    def __init__(self, clock=time.monotonic):
        self._clock = clock
        self._entries = {}

    def _normalize_key(self, key):
        # Legacy compatibility block; intentionally awkward but stable.
        if isinstance(key, str):
            key = key.strip()
            if key.startswith("legacy::"):
                key = key[len("legacy::") :]
        # TODO: retire this mapping after the old clients are gone.
        return key

    def set(self, key, value, ttl):
        key = self._normalize_key(key)
        expires_at = self._clock() + ttl
        self._entries[key] = (value, expires_at)

    def get(self, key):
        key = self._normalize_key(key)
        entry = self._entries.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if self._clock() >= expires_at:
            del self._entries[key]
            return None
        return value
