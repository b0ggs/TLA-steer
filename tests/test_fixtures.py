from __future__ import annotations

import stat
import unittest

from mdseval.execution import _verify_prepared_inputs
from mdseval.fixtures import prepare_fixture
from mdseval.hashing import sha256_file

from tests.helpers import experiment


class FixtureTests(unittest.TestCase):
    def test_mutable_default_contract_captures_required_pre_edit_failure(self) -> None:
        config = experiment()
        case = config.cases["bug-reproduce-mutable-default"]
        variant = config.variants["champion"]
        prepared = prepare_fixture(case, variant, sha256_file(variant))
        try:
            contract = (prepared.repo / ".issue-contract.md").read_text()
            self.assertIn("python3 -m unittest tests.test_tags 2>&1", contract)
            self.assertTrue(case.verification_evidence.pre_edit_failure_required)
        finally:
            prepared.cleanup()

    def test_subject_receives_only_authorized_inputs(self) -> None:
        config = experiment()
        case = config.cases["ambiguity-repo-resolves"]
        variant = config.variants["champion"]
        source = case.fixture_dir / "src/duration.py"
        source_bytes = source.read_bytes()
        cache_dir = source.parent / "__pycache__"
        cache_dir_created = not cache_dir.exists()
        cache_dir.mkdir(exist_ok=True)
        if cache_dir_created:
            self.addCleanup(cache_dir.rmdir)
        cache = cache_dir / "mdseval-controlled-test.pyc"
        self.assertFalse(cache.exists())
        self.addCleanup(cache.unlink, missing_ok=True)
        cache_bytes = b"controlled ignored cache input\n"
        cache.write_bytes(cache_bytes)
        prepared = prepare_fixture(case, variant, sha256_file(variant))
        try:
            _verify_prepared_inputs(case, variant, prepared.repo)
            self.assertTrue((prepared.repo / "CODER.md").is_file())
            self.assertTrue((prepared.repo / ".issue-contract.md").is_file())
            self.assertEqual(
                (prepared.repo / "src/duration.py").read_bytes(), source_bytes
            )
            self.assertFalse(any(prepared.repo.rglob("*.pyc")))
            self.assertFalse(any(path.name == "__pycache__" for path in prepared.repo.rglob("*")))
            self.assertEqual(source.read_bytes(), source_bytes)
            self.assertEqual(cache.read_bytes(), cache_bytes)
            for forbidden in ("case.json", "checks", "rubric.md", "AGENTS.md", ".codex"):
                self.assertFalse((prepared.repo / forbidden).exists())
        finally:
            prepared.cleanup()

    def test_repositories_are_clean_and_independent(self) -> None:
        config = experiment()
        case = config.cases["scope-ttl-zero"]
        variant = config.variants["champion"]
        first = prepare_fixture(case, variant, sha256_file(variant))
        second = prepare_fixture(case, variant, sha256_file(variant))
        try:
            self.assertNotEqual(first.repo, second.repo)
            (first.repo / "src/cache.py").write_text("changed\n")
            self.assertNotEqual(
                (first.repo / "src/cache.py").read_text(),
                (second.repo / "src/cache.py").read_text(),
            )
        finally:
            first.cleanup()
            second.cleanup()

    def test_executable_mode_is_preserved(self) -> None:
        config = experiment()
        case = config.cases["goal-real-entrypoint"]
        variant = config.variants["champion"]
        prepared = prepare_fixture(case, variant, sha256_file(variant))
        try:
            mode = stat.S_IMODE((prepared.repo / "bin/sample-export").stat().st_mode)
            self.assertTrue(mode & stat.S_IXUSR)
        finally:
            prepared.cleanup()
