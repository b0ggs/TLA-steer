import copy
import unittest

from ledger import running_balances


class RunningBalanceRegressionTests(unittest.TestCase):
    def test_mixed_entries_and_exact_decimal_output(self):
        entries = [
            {"kind": "credit", "amount": "0.10"},
            {"kind": "credit", "amount": "0.20"},
            {"kind": "debit", "amount": "1.05"},
        ]
        before = copy.deepcopy(entries)
        self.assertEqual(running_balances("2.00", entries),
                         ["2.10", "2.30", "1.25"])
        self.assertEqual(entries, before)

    def test_unsupported_kind_is_rejected(self):
        with self.assertRaises(ValueError):
            running_balances("0.00", [{"kind": "hold", "amount": "1.00"}])


if __name__ == "__main__":
    unittest.main()
