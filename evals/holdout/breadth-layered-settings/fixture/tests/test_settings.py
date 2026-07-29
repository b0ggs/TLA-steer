import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from src.settings import load_settings


class SettingsTests(unittest.TestCase):
    def test_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                {"timeout_seconds": 30, "debug": False},
                load_settings(),
            )

    def test_json_file_overrides_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text(
                json.dumps({"timeout_seconds": 45, "debug": True}),
                encoding="utf-8",
            )
            with mock.patch.dict(os.environ, {}, clear=True):
                self.assertEqual(
                    {"timeout_seconds": 45, "debug": True},
                    load_settings(path),
                )


if __name__ == "__main__":
    unittest.main()
