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
        candidate_text = config.variants["karpathy-v1"].read_text()
        unique = "smallest implementation that fully satisfies the issue contract"
        left = {
            "final_text": f"IMPLEMENTED\n{unique}\nkarpathy-v1",
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
            variant_ids=("champion", "karpathy-v1"),
            variant_paths=tuple(str(config.variants[name]) for name in ("champion", "karpathy-v1")),
            instruction_texts=(
                config.variants["champion"].read_text(),
                candidate_text,
            ),
        )
        serialized = json.dumps(packet)
        self.assertNotIn("karpathy-v1", serialized)
        self.assertNotIn(unique, serialized)
        self.assertNotIn("CODER.md", serialized)

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
