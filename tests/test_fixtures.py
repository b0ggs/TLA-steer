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
        cache = next(case.fixture_dir.rglob("*.pyc"))
        cache_bytes = cache.read_bytes()
        prepared = prepare_fixture(case, variant, sha256_file(variant))
        try:
            _verify_prepared_inputs(case, variant, prepared.repo)
            self.assertTrue((prepared.repo / "CODER.md").is_file())
            self.assertTrue((prepared.repo / ".issue-contract.md").is_file())
            self.assertTrue((prepared.repo / "src/duration.py").is_file())
            self.assertFalse(any(prepared.repo.rglob("*.pyc")))
            self.assertFalse(any(path.name == "__pycache__" for path in prepared.repo.rglob("*")))
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
