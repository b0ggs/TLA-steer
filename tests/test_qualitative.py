from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mdseval.capture import Redactor
from mdseval.scoring.qualitative import (
    build_blinded_packet,
    parse_judge_output,
    randomize_labels,
)

from tests.helpers import experiment


class QualitativeTests(unittest.TestCase):
    def test_randomization_is_deterministic(self) -> None:
        self.assertEqual(
            randomize_labels(7, "case", 1), randomize_labels(7, "case", 1)
        )

    def test_packet_blinds_variant_identity_and_unique_fragments(self) -> None:
        config = experiment()
        case = config.cases["scope-ttl-zero"]
        unique = "STAGE3-UNIQUE-INSTRUCTION-MARKER-7391"; mock = __import__("unittest.mock", fromlist=["patch"]); captured = {}; dimension = {"winner": "TIE", "reason": "offline stable judge"}
        champion_text = config.variants["champion"].read_text(); candidate_text = f"## Scope Guardian\n\n{unique}\nNever leak this complete instruction.\n"; judge_result = {"schema_version": 1, "winner": "TIE", "confidence": "medium", "dimensions": {name: dimension for name in ("assumption_handling", "simplicity", "scope_discipline", "verification_quality")}, "hard_concerns": []}
        left = {
            "final_text": f"IMPLEMENTED\n{unique}\nscope-guardian-v2",
            "diff": "diff --git a/CODER.md b/CODER.md\n" + unique,
            "commands": [],
            "mechanical": {"fields": {}},
            "usage": {},
            "duration_seconds": 1,
        }
        packet, _ = build_blinded_packet(
            case_id=case.id,
            replicate=1,
            seed=1,
            contract=case.contract_path.read_text(),
            fixture=case.fixture_dir,
            left=left,
            right={**left, "final_text": "IMPLEMENTED\n"},
            variant_ids=("champion", "scope-guardian-v2", "champion-slot-secret", "candidate-slot-secret"),
            variant_paths=("targets/coder/champion.md", "candidates/coder/scope-guardian-v2.md"),
            instruction_texts=(
                config.variants["champion"].read_text(),
                candidate_text,
            ),
        )
        serialized = json.dumps(packet)
        with mock.patch.dict("os.environ", {"MDSEVAL_CODEX_HOME": "offline"}), mock.patch("mdseval.execution.init_repository"), mock.patch("mdseval.execution.build_judge_command", return_value=["offline-judge"]), mock.patch("mdseval.execution.run_process_group", side_effect=lambda command, **kwargs: (captured.setdefault("payload", (kwargs["cwd"] / "packet.json").read_bytes()), (kwargs["cwd"] / "judge-output.json").write_text(json.dumps(judge_result)), mock.Mock(returncode=0, timed_out=False, interrupted=False, stderr=""))[-1]) as process:
            result = __import__("mdseval.execution", fromlist=["run_live_judge"]).run_live_judge(config, packet, Redactor())
        actual_payload = captured["payload"].decode("utf-8"); forbidden = ("champion", "scope-guardian-v2", "champion-slot-secret", "candidate-slot-secret", "targets/coder/champion.md", "candidates/coder/scope-guardian-v2.md", "champion.md", "scope-guardian-v2.md", champion_text, candidate_text, json.dumps(champion_text)[1:-1], json.dumps(candidate_text)[1:-1], unique, "CODER.md"); self.assertEqual((json.loads(actual_payload), result[0], result[1]["winner"], result[2], process.call_count), (packet, "COMPLETED", "TIE", None, 1)); self.assertTrue(json.dumps(champion_text)[1:-1] and json.dumps(candidate_text)[1:-1]); self.assertFalse([secret for secret in forbidden if secret in actual_payload])

    def test_packet_blinds_unique_three_and_four_token_instruction_phrases(self) -> None:
        config = experiment()
        case = config.cases["scope-ttl-zero"]
        candidate_text = config.variants["karpathy-v1"].read_text()
        phrases = (
            "ask one focused question",
            "unrelated cleanup alone",
            "consequential ambiguity",
            "speculative abstractions",
            "unrequested configurability",
        )
        left = {
            "final_text": "IMPLEMENTED\n" + "\n".join(phrases),
            "diff": "",
            "commands": [],
            "mechanical": {"fields": {}},
            "usage": {},
            "duration_seconds": 1,
        }
        packet, _ = build_blinded_packet(
            case_id=case.id,
            replicate=1,
            seed=1,
            contract=case.contract_path.read_text(),
            fixture=case.fixture_dir,
            left=left,
            right={**left, "final_text": "IMPLEMENTED\n"},
            variant_ids=("champion", "karpathy-v1"),
            variant_paths=tuple(
                str(config.variants[name]) for name in ("champion", "karpathy-v1")
            ),
            instruction_texts=(
                config.variants["champion"].read_text(),
                candidate_text,
            ),
        )
        serialized = json.dumps(packet).lower()
        for phrase in phrases:
            self.assertNotIn(phrase, serialized)
        # Authoritative context is not over-blinded by short-phrase matching.
        self.assertEqual(packet["contract"], case.contract_path.read_text())

    def test_fixture_filename_secret_is_redacted_from_serialized_packet(self) -> None:
        config = experiment()
        case = config.cases["scope-ttl-zero"]
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary)
            (fixture / "CANARY-SECRET.txt").write_text("safe")
            side = {
                "final_text": "IMPLEMENTED\n",
                "diff": "",
                "commands": [],
                "mechanical": {"fields": {}},
                "usage": {},
                "duration_seconds": 1,
            }
            packet, _ = build_blinded_packet(
                case_id=case.id,
                replicate=1,
                seed=1,
                contract=case.contract_path.read_text(),
                fixture=fixture,
                left=side,
                right=side,
                variant_ids=("champion", "karpathy-v1"),
                variant_paths=tuple(
                    str(config.variants[name])
                    for name in ("champion", "karpathy-v1")
                ),
                instruction_texts=tuple(
                    config.variants[name].read_text()
                    for name in ("champion", "karpathy-v1")
                ),
            )
            serialized = json.dumps(Redactor(["CANARY-SECRET"]).object(packet))
            self.assertNotIn("CANARY-SECRET", serialized)
            self.assertIn("[REDACTED].txt", serialized)

    def test_generated_files_are_absent_from_fixture_context_and_blinded_diffs(self) -> None:
        raw_diff = """diff --git a/material.py b/material.py
--- a/material.py
+++ b/material.py
@@ -1 +1 @@
-old
+material change
diff --git "a/pkg/__pycache__/cache file.pyc" "b/pkg/__pycache__/cache file.pyc"
new file mode 100644
+cache bytes
diff --git a/.pytest_cache/v/cache/nodeids b/.pytest_cache/v/cache/nodeids
new file mode 100644
+cache index
diff --git a/generated.pyo b/generated.pyo
new file mode 100644
+compiled bytes
"""
        side = {
            "final_text": "IMPLEMENTED",
            "diff": raw_diff,
            "commands": [],
            "mechanical": {"fields": {}},
        }
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary)
            (fixture / "material.py").write_text("print('ok')\n")
            (fixture / "pkg/__pycache__").mkdir(parents=True)
            (fixture / "pkg/__pycache__/cache file.pyc").write_bytes(b"secret cache")
            (fixture / ".pytest_cache/v/cache").mkdir(parents=True)
            (fixture / ".pytest_cache/v/cache/nodeids").write_text("secret index")
            (fixture / "generated.pyo").write_bytes(b"compiled")
            packet, _ = build_blinded_packet(
                case_id="cache-filter",
                replicate=1,
                seed=1,
                contract="material contract",
                fixture=fixture,
                left=side,
                right=side,
                variant_ids=("left-id", "right-id"),
                variant_paths=("left.md", "right.md"),
                instruction_texts=("left-guide", "right-guide"),
            )
        self.assertEqual(
            packet["original_fixture_files"], {"material.py": "print('ok')\n"}
        )
        for response in packet["responses"].values():
            self.assertIn("material change", response["diff"])
            for generated in ("__pycache__", ".pytest_cache", "generated.pyo"):
                self.assertNotIn(generated, response["diff"])
        self.assertEqual(side["diff"], raw_diff)

    def test_judge_parser_is_strict(self) -> None:
        dimension = {"winner": "TIE", "reason": "no meaningful difference"}
        valid = {
            "schema_version": 1,
            "winner": "TIE",
            "confidence": "medium",
            "dimensions": {
                "assumption_handling": dimension,
                "simplicity": dimension,
                "scope_discipline": dimension,
                "verification_quality": dimension,
            },
            "hard_concerns": [],
        }
        self.assertEqual(parse_judge_output(valid)["winner"], "TIE")
        valid["extra"] = True
        with self.assertRaises(ValueError):
            parse_judge_output(valid)
