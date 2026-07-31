from __future__ import annotations

import json
import unittest

from tests.helpers import ROOT, no_ignore_inventory


class HistoricalEvidenceInventoryTests(unittest.TestCase):
    def test_historical_v1_evidence_matches_canonical_inventory(self) -> None:
        inventory = json.loads(
            (ROOT / "docs/historical-evidence-v1-inventory.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(inventory["schema_version"], 1)
        self.assertEqual(
            inventory["algorithm"], "os.scandir-lstat-full-sha256-v1"
        )
        actual = no_ignore_inventory(ROOT, inventory["roots"])
        self.assertEqual(actual, inventory["entries"])
        self.assertEqual(len(actual), inventory["entry_count"])


if __name__ == "__main__":
    unittest.main()
