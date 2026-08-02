import copy
import unittest

from workflow import merge_context


class WorkflowRegressionTests(unittest.TestCase):
    def test_overlay_replaces_top_level_values(self):
        base = {"mode": "safe", "limit": 2}
        overlay = {"limit": 3, "owner": "Ada"}
        before = copy.deepcopy((base, overlay))
        self.assertEqual(merge_context(base, overlay),
                         {"mode": "safe", "limit": 3, "owner": "Ada"})
        self.assertEqual((base, overlay), before)

    def test_empty_inputs(self):
        self.assertEqual(merge_context({}, {}), {})
        self.assertEqual(merge_context({"a": 1}, {}), {"a": 1})
        self.assertEqual(merge_context({}, {"b": 2}), {"b": 2})


if __name__ == "__main__":
    unittest.main()
