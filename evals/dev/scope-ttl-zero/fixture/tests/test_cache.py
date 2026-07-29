import unittest

from src.cache import Cache


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


class CacheTests(unittest.TestCase):
    def test_positive_ttl_is_available_before_deadline(self):
        clock = Clock()
        cache = Cache(clock)
        cache.set("item", "value", 5)
        clock.now += 4
        self.assertEqual("value", cache.get("item"))

    def test_positive_ttl_expires_at_deadline(self):
        clock = Clock()
        cache = Cache(clock)
        cache.set("item", "value", 5)
        clock.now += 5
        self.assertIsNone(cache.get("item"))


if __name__ == "__main__":
    unittest.main()
