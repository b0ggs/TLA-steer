"""Small command line for the one frozen TLA-Steer prototype."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .evidence import EvidenceError, render_markdown, write_json, write_run_report


DEFAULT_CONFIG = Path("configs/prototype.json")


class ConfigError(ValueError):
    """The prototype configuration does not match the frozen experiment."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tla-steer",
        description="Run or report the fixed TwoLights translation comparison.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    compare = commands.add_parser("compare", help="run the intended N=8, C=4 comparison")
    compare.add_argument("--config", type=Path, default=DEFAULT_CONFIG)

    smoke = commands.add_parser("smoke", help="run the permitted N=2, C=2 smoke path")
    smoke.add_argument("--config", type=Path, default=DEFAULT_CONFIG)

    verify = commands.add_parser("verify", help="exhaustively verify one candidate")
    verify.add_argument("candidate", type=Path)
    verify.add_argument("--output", type=Path)

    report = commands.add_parser("report", help="rebuild a run report without model calls")
    report.add_argument("run_dir", type=Path)
    report.add_argument(
        "--rate-card",
        type=Path,
        help="explicit static card; defaults to RUN_DIR/rate-card.json",
    )
    report.add_argument("--json", action="store_true", help="print JSON instead of Markdown")
    return parser


def load_config(path: Path) -> tuple[dict[str, Any], Path]:
    """Load and mechanically confirm the frozen prototype decisions."""

    path = path.resolve()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"invalid prototype config {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ConfigError("prototype config must be a JSON object")
    if value.get("schema_version") != "tla-steer-config/0.1":
        raise ConfigError("unsupported prototype config schema")

    models = value.get("models")
    smc = value.get("smc")
    paths = value.get("paths")
    if not isinstance(models, dict) or not isinstance(smc, dict) or not isinstance(paths, dict):
        raise ConfigError("prototype config is missing models, smc, or paths")
    expected_models = {
        "direct": ("gpt-5.6-sol", "xhigh", 1),
        "planner": ("gpt-5.6-sol", "xhigh", 2),
        "follower": ("gpt-5.6-luna", "low", 1),
    }
    for role, (model, effort, attempts) in expected_models.items():
        source = models.get(role)
        if not isinstance(source, dict):
            raise ConfigError(f"missing {role} model configuration")
        actual = (
            source.get("model"),
            source.get("reasoning_effort"),
            source.get("max_attempts"),
        )
        if actual != (model, effort, attempts) or source.get("internal_subagents") is not False:
            raise ConfigError(f"{role} model configuration is outside frozen scope")
    expected_smc = {
        "logical_particles": 8,
        "max_active_follower_calls": 4,
        "semantic_steps": 8,
        "ess_threshold": 4.0,
        "resampling": "multinomial",
        "seed": 20260830,
    }
    if any(smc.get(key) != expected for key, expected in expected_smc.items()):
        raise ConfigError("SMC configuration is outside frozen N=8, C=4 design")

    root = path.parent.parent
    required_paths = (
        "rate_card",
        "controller_schema",
        "proposal_schema",
        "direct_prompt",
        "planner_prompt",
        "follower_prompt",
    )
    for key in required_paths:
        relative = paths.get(key)
        if not isinstance(relative, str) or not (root / relative).is_file():
            raise ConfigError(f"configured {key} is missing: {relative!r}")
    input_config = value.get("input")
    if not isinstance(input_config, dict):
        raise ConfigError("prototype config is missing input")
    for key in ("tla_path", "cfg_path"):
        relative = input_config.get(key)
        if not isinstance(relative, str) or not (root / relative).is_file():
            raise ConfigError(f"configured {key} is missing: {relative!r}")
    return value, root


def _json_ready(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if hasattr(value, "as_dict"):
        return value.as_dict()
    if isinstance(value, Mapping):
        return dict(value)
    raise TypeError(f"result is not JSON serializable: {type(value).__name__}")


def _verification_adapter(candidate: Path) -> dict[str, Any]:
    """Late import keeps the offline report independent of candidate execution."""

    from . import verifier

    entrypoint = getattr(verifier, "verify_candidate", None)
    if entrypoint is None:
        raise RuntimeError("verifier.py does not expose verify_candidate(path)")
    return _json_ready(entrypoint(candidate.resolve()))


def _comparison_adapter(
    config_path: Path, config: dict[str, Any], root: Path, *, smoke: bool
) -> Path:
    """Call the deliberately thin live coordinator adapter when present.

    The algorithm, worker, and verifier stay separate.  A live coordinator may
    expose ``run_comparison`` from ``tla_steer.pipeline`` without changing the
    stable command surface or the offline report.
    """

    try:
        from .pipeline import run_comparison  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "live comparison adapter is not connected; offline report and verify are available"
        ) from exc
    result = run_comparison(
        config=config,
        config_path=config_path.resolve(),
        repository_root=root,
        particle_count=2 if smoke else 8,
        max_concurrency=2 if smoke else 4,
        smoke=smoke,
    )
    if isinstance(result, Path):
        return result
    if isinstance(result, str):
        return Path(result)
    if isinstance(result, Mapping) and isinstance(result.get("run_dir"), (str, Path)):
        return Path(result["run_dir"])
    raise RuntimeError("live comparison adapter did not return a run directory")


def _command_verify(candidate: Path, output: Path | None) -> int:
    result = _verification_adapter(candidate)
    if output is not None:
        write_json(output, result)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    outcome = str(result.get("outcome") or result.get("status") or "")
    if outcome == "EXACT":
        return 0
    if outcome == "EVALUATOR_ERROR":
        return 3
    return 2


def _command_report(run_dir: Path, rate_card: Path | None, as_json: bool) -> int:
    summary = write_run_report(run_dir.resolve(), rate_card_path=rate_card)
    if as_json:
        print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(render_markdown(summary), end="")
    return 0


def _command_live(config_path: Path, *, smoke: bool) -> int:
    config, root = load_config(config_path)
    run_dir = _comparison_adapter(config_path, config, root, smoke=smoke).resolve()
    card = root / str(config["paths"]["rate_card"])
    summary = write_run_report(run_dir, rate_card_path=card)
    print(render_markdown(summary), end="")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "verify":
            return _command_verify(args.candidate, args.output)
        if args.command == "report":
            return _command_report(args.run_dir, args.rate_card, args.json)
        if args.command == "smoke":
            return _command_live(args.config, smoke=True)
        if args.command == "compare":
            return _command_live(args.config, smoke=False)
        raise AssertionError(f"unhandled command: {args.command}")
    except (ConfigError, EvidenceError, OSError, RuntimeError, ValueError) as exc:
        print(f"tla-steer: {exc}", file=sys.stderr)
        return 3


__all__ = ["ConfigError", "load_config", "main"]
