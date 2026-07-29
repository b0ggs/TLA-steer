from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mdseval.report import build_report, render_markdown, write_report


def response(hard: bool, score: int, tokens: int, duration: float) -> dict:
    return {
        "mechanical": {"hard_pass": hard, "mechanical_score": score},
        "usage": {"total_tokens": tokens},
        "duration_seconds": duration,
    }


class ReportTests(unittest.TestCase):
    def test_report_leads_with_required_summary_and_case_rows(self) -> None:
        comparisons = [
            {
                "case_id": "breadth-layered-settings",
                "suite": "holdout",
                "replicate": replicate,
                "champion": response(True, 90, 100, 1.0),
                "candidate": response(True, 95, 110, 1.2),
                "qualitative_winner": "TIE",
                "evidence_path": f"comparisons/case-{replicate}.json",
            }
            for replicate in (1, 2)
        ]
        report = build_report(
            mode="candidate-comparison",
            experiment_id="test",
            verdict="INCONCLUSIVE",
            champion_hash="a",
            candidate_hash="b",
            comparisons=comparisons,
            live_runner_status="LIVE_RUNNER_AVAILABLE",
            live_evidence_complete=True,
        )
        markdown = render_markdown(report)
        self.assertIn("Holdout outcome: NO_HARD_REGRESSION", markdown)
        self.assertIn("Total tokens", markdown)
        self.assertEqual(markdown.count("| breadth-layered-settings"), 1)
        self.assertTrue(report["baseline_metadata"]["mismatch_preserved"])
        self.assertIn("GPT-5.5 @ xhigh", markdown)
        self.assertIn("gpt-5.6-sol @ high", markdown)

    def test_demo_report_never_claims_quality_and_links_resolve(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            (run_dir / "comparisons").mkdir()
            (run_dir / "comparisons/case-1.json").write_text("{}")
            comparison = {
                "case_id": "case",
                "suite": "dev",
                "replicate": 1,
                "champion": response(True, 100, 10, 0.1),
                "candidate": response(True, 100, 10, 0.1),
                "qualitative_winner": "NOT_RUN",
                "evidence_path": "comparisons/case-1.json",
            }
            report = build_report(
                mode="demo",
                experiment_id="test",
                verdict="NOT_RUN",
                champion_hash="a",
                candidate_hash="b",
                comparisons=[comparison],
                live_runner_status="LIVE_RUNNER_UNAVAILABLE",
            )
            write_report(run_dir, report)
            self.assertFalse(report["quality_claim_established"])
            self.assertIn(
                "No claim about CODER.md quality has been established.",
                (run_dir / "report.md").read_text(),
            )
            self.assertTrue((run_dir / comparison["evidence_path"]).resolve().is_file())
