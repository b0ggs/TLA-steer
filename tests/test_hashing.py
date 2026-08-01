from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from mdseval.hashing import sha256_file, tree_sha256
from mdseval.variants import (
    BAD_CONTROL_BLOCK,
    CANDIDATE_BLOCK,
    CHAMPION_SHA256,
    expected_variant,
    validate_locked_variants,
)

from tests.helpers import ROOT


class HashingTests(unittest.TestCase):
    def test_champion_hash_is_locked(self) -> None:
        self.assertEqual(
            sha256_file(ROOT / "targets/coder/champion.md"), CHAMPION_SHA256
        )

    def test_candidate_is_only_authorized_block(self) -> None:
        champion = (ROOT / "targets/coder/champion.md").read_text()
        candidate = (ROOT / "candidates/coder/karpathy-v1.md").read_text()
        self.assertEqual(candidate, expected_variant(champion, CANDIDATE_BLOCK))

    def test_bad_control_is_only_authorized_block(self) -> None:
        champion = (ROOT / "targets/coder/champion.md").read_text()
        bad = (ROOT / "controls/coder/deliberately-bad.md").read_text()
        self.assertEqual(bad, expected_variant(champion, BAD_CONTROL_BLOCK))

    def test_locked_validation_ignores_internal_aliases_and_candidates(self) -> None:
        validate_locked_variants({
            "champion": ROOT / "targets/coder/champion.md",
            "deliberately-bad": ROOT / "controls/coder/deliberately-bad.md",
            "champion-aa-a": ROOT / "missing-aa-a",
            "champion-aa-b": ROOT / "missing-aa-b",
            "unchecked-v1": ROOT / "missing-candidate",
        })

    def test_tree_hash_excludes_only_narrow_caches(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "a.py").write_text("x = 1\n")
            before = tree_sha256(root)
            (root / "__pycache__").mkdir()
            (root / "__pycache__/a.pyc").write_bytes(b"cache")
            self.assertEqual(before, tree_sha256(root))
            (root / "note.md").write_text("material\n")
            self.assertNotEqual(before, tree_sha256(root))

    def test_tree_hash_includes_executable_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "tool"
            path.write_text("#!/bin/sh\n")
            path.chmod(0o644)
            first = tree_sha256(Path(temporary))
            path.chmod(0o755)
            self.assertNotEqual(first, tree_sha256(Path(temporary)))

    def test_tree_hash_includes_empty_directories_and_full_modes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "file"
            path.write_text("x")
            path.chmod(0o644)
            before = tree_sha256(root)
            (root / "empty").mkdir()
            with_directory = tree_sha256(root)
            self.assertNotEqual(before, with_directory)
            (root / "empty").rmdir()
            path.chmod(0o444)
            self.assertNotEqual(before, tree_sha256(root))

    def test_tree_hash_rejects_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "real").write_text("x")
            (root / "link").symlink_to(root / "real")
            with self.assertRaises(ValueError):
                tree_sha256(root)
