import copy
import unittest

from notifier import due_notification_ids, render


class NotifierRegressionTests(unittest.TestCase):
    def test_template_rendering(self):
        values = {"name": "Mira", "count": 3}
        self.assertEqual(render("Hi {name}: {count}", values), "Hi Mira: 3")

    def test_due_ids_keep_record_order(self):
        records = [
            {"id": "first", "scheduled_at": "2024-01-01T09:00:00Z"},
            {"id": "later", "scheduled_at": "2024-01-01T13:00:00Z"},
            {"id": "second", "scheduled_at": "2024-01-01T10:00:00Z"},
        ]
        before = copy.deepcopy(records)
        self.assertEqual(due_notification_ids(records, "2024-01-01T12:00:00Z"),
                         ["first", "second"])
        self.assertEqual(records, before)


if __name__ == "__main__":
    unittest.main()
