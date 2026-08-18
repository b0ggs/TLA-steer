#!/usr/bin/env python3
"""Run offline qualification, preflight, or the frozen null-only M2 scout."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mdseval.scout import (  # noqa: E402
    ScoutError,
    finalize_rolling_candidate,
    load_config,
    preflight_live_scout,
    qualify_cohort,
    run_live_scout,
    run_live_rolling_candidate,
    run_smoke,
    verify_live_rolling,
    verify_qualification,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=("smoke", "qualify", "verify-qualification", "preflight", "run", "rolling-run", "rolling-finalize", "rolling-verify"),
        nargs="?",
        default="smoke",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "experiments/coder-beneficial-sensitivity-m2-scout-v1.json",
    )
    parser.add_argument(
        "--cohort",
        type=Path,
        default=ROOT / "evals/development/coder-beneficial-sensitivity-m2/scout-v1/cohort-v1.json",
    )
    parser.add_argument(
        "--qualification",
        type=Path,
        default=ROOT / "runs/development/coder-beneficial-sensitivity-m2/scout-v1/qualification",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--freeze-commit")
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--semantic-clearance", type=Path)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--disposition", type=Path)
    arguments = parser.parse_args()
    try:
        if arguments.action == "smoke":
            config = load_config(arguments.config)
            output = arguments.output or ROOT / config["evidence_root"]
            result = run_smoke(arguments.config, output)
        elif arguments.action == "qualify":
            result = qualify_cohort(arguments.cohort, arguments.output or arguments.qualification)
        elif arguments.action == "verify-qualification":
            result = verify_qualification(arguments.cohort, arguments.output or arguments.qualification)
        elif arguments.action == "preflight":
            result = preflight_live_scout(arguments.cohort)
        elif arguments.action == "run":
            if arguments.output is None or arguments.freeze_commit is None:
                raise ScoutError("run requires explicit --output and --freeze-commit")
            result = run_live_scout(
                arguments.cohort, arguments.qualification, arguments.output,
                freeze_commit=arguments.freeze_commit,
            )
        elif arguments.action == "rolling-run":
            if any(value is None for value in (
                arguments.candidate, arguments.semantic_clearance,
                arguments.authorization, arguments.output, arguments.freeze_commit,
            )):
                raise ScoutError(
                    "rolling-run requires explicit --candidate, --semantic-clearance, "
                    "--authorization, --output, and --freeze-commit"
                )
            result = run_live_rolling_candidate(
                arguments.candidate, arguments.semantic_clearance,
                arguments.authorization, arguments.output,
                freeze_commit=arguments.freeze_commit,
            )
        elif arguments.action == "rolling-finalize":
            if None in (arguments.authorization, arguments.output, arguments.disposition):
                raise ScoutError("rolling-finalize requires --authorization, --output, and --disposition")
            result = finalize_rolling_candidate(arguments.authorization, arguments.output, arguments.disposition)
        else:
            if None in (arguments.authorization, arguments.output):
                raise ScoutError("rolling-verify requires --authorization and --output")
            result = verify_live_rolling(arguments.authorization, arguments.output)
    except ScoutError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
