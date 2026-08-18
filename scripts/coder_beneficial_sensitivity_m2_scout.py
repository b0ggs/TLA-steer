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
    load_config,
    preflight_live_scout,
    qualify_cohort,
    run_live_scout,
    run_smoke,
    verify_qualification,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=("smoke", "qualify", "verify-qualification", "preflight", "run"),
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
        else:
            if arguments.output is None:
                raise ScoutError("run requires an explicit create-once --output")
            result = run_live_scout(arguments.cohort, arguments.qualification, arguments.output)
    except ScoutError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
