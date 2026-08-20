"""Tests for inimerge.merger.

Acceptance note (FAC02-7): class ``MergerTests`` below must gain a test
method named exactly ``test_override_precedence`` that asserts

    merge({"s": {"k": "a"}}, {"s": {"k": "b"}}) == {"s": {"k": "b"}}

and the method must pass when run as
``python -m unittest tests.test_merger.MergerTests.test_override_precedence``.
"""

import unittest

from inimerge.merger import merge, merge_all


class MergerTests(unittest.TestCase):
    def test_base_only_keys_survive(self):
        result = merge({"a": {"x": "1"}, "b": {"y": "2"}}, {"a": {"z": "3"}})
        self.assertEqual(result, {"a": {"x": "1", "z": "3"}, "b": {"y": "2"}})

    def test_new_sections_are_added(self):
        result = merge({}, {"web": {"port": "80"}})
        self.assertEqual(result, {"web": {"port": "80"}})

    def test_merge_all_folds_left_to_right(self):
        result = merge_all([{"a": {"x": "1"}}, {"b": {"y": "2"}}])
        self.assertEqual(result, {"a": {"x": "1"}, "b": {"y": "2"}})

    def test_override_precedence(self):
        self.assertEqual(
            merge({"s": {"k": "a"}}, {"s": {"k": "b"}}), {"s": {"k": "b"}}
        )


if __name__ == "__main__":
    unittest.main()
