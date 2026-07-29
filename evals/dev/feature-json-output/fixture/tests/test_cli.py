from pathlib import Path
import subprocess
import sys
import unittest


REPO = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def test_default_text_output(self):
        result = subprocess.run(
            [sys.executable, "sample_cli.py", "Ada"],
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode)
        self.assertEqual("Hello, Ada!\n", result.stdout)
        self.assertEqual("", result.stderr)


if __name__ == "__main__":
    unittest.main()
