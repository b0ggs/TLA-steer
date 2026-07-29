from __future__ import annotations

import errno
import os
import signal
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from mdseval.processutils import run_process_group


class ProcessUtilsTests(unittest.TestCase):
    def test_timeout_kills_background_descendant(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            marker = root / "marker"
            script = (
                "import subprocess,sys,time;"
                "subprocess.Popen([sys.executable,'-c',"
                f"\"import time,pathlib;time.sleep(2);pathlib.Path({str(marker)!r}).write_text('bad')\"]);"
                "time.sleep(10)"
            )
            result = run_process_group(
                [sys.executable, "-c", script],
                cwd=root,
                input_text=None,
                timeout=1,
                environment=dict(os.environ),
            )
            self.assertTrue(result.timed_out)
            time.sleep(1.5)
            self.assertFalse(marker.exists())

    def test_keyboard_interrupt_and_eperm_cleanup_are_evidence_safe(self) -> None:
        class InterruptingProcess:
            pid = 12345
            returncode = None
            calls = 0

            def communicate(self, *_args, **_kwargs):
                self.calls += 1
                if self.calls == 1:
                    raise KeyboardInterrupt
                return ("partial", "interrupted")

        process = InterruptingProcess()
        permission = PermissionError(errno.EPERM, "not permitted")
        with mock.patch(
            "mdseval.processutils.subprocess.Popen", return_value=process
        ), mock.patch("mdseval.processutils.os.killpg", side_effect=permission), mock.patch(
            "mdseval.processutils.time.sleep"
        ):
            result = run_process_group(
                ["ignored"],
                cwd=Path("."),
                input_text=None,
                timeout=1,
                environment={},
            )
        self.assertTrue(result.interrupted)
        self.assertEqual(result.stderr, "interrupted")

