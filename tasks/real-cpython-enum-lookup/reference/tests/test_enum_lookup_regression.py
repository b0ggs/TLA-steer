import unittest

from enum import Enum


class EnumLookupRegressionTests(unittest.TestCase):
    def test_nonhashable_matches_hashable(self):
        class Directions(Enum):
            DOWN_ONLY = frozenset({"sc"})
            UP_ONLY = frozenset({"cs"})
            UNRESTRICTED = frozenset({"sc", "cs"})

        self.assertIs(Directions({"sc"}), Directions.DOWN_ONLY)

    def test_hashable_lookup_and_alias_still_work(self):
        class Directions(Enum):
            DOWN_ONLY = frozenset({"sc"})
            DOWN_ALIAS = frozenset({"sc"})

        self.assertIs(Directions(frozenset({"sc"})), Directions.DOWN_ONLY)
        self.assertIs(Directions.DOWN_ALIAS, Directions.DOWN_ONLY)

    def test_unhashable_member_lookup_still_works(self):
        class Payload(Enum):
            ITEM = {"key": "value"}

        self.assertIs(Payload({"key": "value"}), Payload.ITEM)


if __name__ == "__main__":
    unittest.main()
