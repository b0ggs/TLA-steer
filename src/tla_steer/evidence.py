"""Durable evidence aggregation and offline reporting for one prototype run.

The trusted coordinator owns aggregate files.  Workers write isolated call
spools; this module reads those spools only after the calls have completed.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Iterable, Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any


USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)
SUCCESS_STATUSES = frozenset({"completed", "exact", "ok", "success"})


class EvidenceError(ValueError):
    """Raised when durable run evidence cannot be interpreted safely."""


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"invalid JSON object at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvidenceError(f"expected JSON object at {path}")
    return value


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def write_json(path: Path, value: Any) -> None:
    """Write deterministic, UTF-8 JSON without leaving a partial aggregate."""

    _atomic_write(
        path,
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_usage(source: Mapping[str, Any] | None) -> dict[str, int | bool]:
    """Retain every exposed token counter with a stable zero-filled shape."""

    source = source or {}
    usage: dict[str, int | bool] = {}
    for field in USAGE_FIELDS:
        amount = source.get(field, 0)
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
            amount = 0
        usage[field] = amount
    usage["usage_reported"] = bool(source.get("usage_reported", False))
    usage["total_tokens"] = int(usage["input_tokens"]) + int(
        usage["output_tokens"]
    )
    return usage


def add_usage(values: Iterable[Mapping[str, Any]]) -> dict[str, int | bool]:
    totals: dict[str, int | bool] = {field: 0 for field in USAGE_FIELDS}
    reported = True
    count = 0
    for value in values:
        normalized = normalize_usage(value)
        count += 1
        for field in USAGE_FIELDS:
            totals[field] = int(totals[field]) + int(normalized[field])
        reported = reported and bool(normalized["usage_reported"])
    totals["usage_reported"] = bool(count and reported)
    totals["total_tokens"] = int(totals["input_tokens"]) + int(
        totals["output_tokens"]
    )
    return totals


def load_rate_card(path: Path) -> dict[str, Any]:
    card = _read_object(path)
    if card.get("schema_version") != "tla-steer-rate-card/0.1":
        raise EvidenceError(f"unsupported rate-card schema at {path}")
    if card.get("currency") != "USD" or card.get("unit") != "per_1m_tokens":
        raise EvidenceError(f"unsupported rate-card units at {path}")
    if not isinstance(card.get("observed_date"), str) or not isinstance(
        card.get("models"), dict
    ):
        raise EvidenceError(f"incomplete rate card at {path}")
    return card


def _money(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.000000000001")))


def price_equivalent(
    usage: Mapping[str, Any], model: str | None, rate_card: Mapping[str, Any]
) -> dict[str, Any]:
    """Apply the dated static API rates to one call's reported usage.

    The Codex usage surface reports cached reads and cache writes as subcounts
    of total input.  They are removed from ordinary input before their own
    rates are applied.  Reasoning output is a diagnostic subcount of output.
    """

    normalized = normalize_usage(usage)
    models = rate_card.get("models", {})
    rates = models.get(model) if isinstance(models, dict) and model else None
    base = {
        "currency": rate_card.get("currency", "USD"),
        "rate_card_date": rate_card.get("observed_date"),
        "model": model,
        "usage_reported": normalized["usage_reported"],
    }
    if not isinstance(rates, dict):
        return {**base, "priced": False, "reason": "model_not_in_rate_card"}

    try:
        input_rate = Decimal(str(rates["input"]))
        cached_rate = Decimal(str(rates["cached_input"]))
        output_rate = Decimal(str(rates["output"]))
        cache_write_rate = Decimal(
            str(rates.get("cache_write_input", rates["input"]))
        )
    except (KeyError, ArithmeticError, ValueError) as exc:
        raise EvidenceError(f"invalid rates for {model}") from exc

    input_tokens = int(normalized["input_tokens"])
    cached_tokens = int(normalized["cached_input_tokens"])
    cache_write_tokens = int(normalized["cache_write_input_tokens"])
    output_tokens = int(normalized["output_tokens"])
    overlap_exceeds_input = cached_tokens + cache_write_tokens > input_tokens
    ordinary_tokens = max(input_tokens - cached_tokens - cache_write_tokens, 0)

    threshold = rates.get("long_context_threshold_input_tokens")
    long_context = isinstance(threshold, int) and input_tokens > threshold
    input_multiplier = Decimal(
        str(rates.get("long_context_input_multiplier", 1) if long_context else 1)
    )
    output_multiplier = Decimal(
        str(rates.get("long_context_output_multiplier", 1) if long_context else 1)
    )
    million = Decimal(1_000_000)
    input_cost = Decimal(ordinary_tokens) * input_rate * input_multiplier / million
    cached_cost = Decimal(cached_tokens) * cached_rate * input_multiplier / million
    cache_write_cost = (
        Decimal(cache_write_tokens)
        * cache_write_rate
        * input_multiplier
        / million
    )
    output_cost = Decimal(output_tokens) * output_rate * output_multiplier / million
    total = input_cost + cached_cost + cache_write_cost + output_cost
    return {
        **base,
        "priced": True,
        "ordinary_input_tokens": ordinary_tokens,
        "cached_input_tokens": cached_tokens,
        "cache_write_input_tokens": cache_write_tokens,
        "output_tokens": output_tokens,
        "reasoning_output_tokens": normalized["reasoning_output_tokens"],
        "long_context_rates_applied": long_context,
        "usage_overlap_anomaly": overlap_exceeds_input,
        "input_usd": _money(input_cost),
        "cached_input_usd": _money(cached_cost),
        "cache_write_input_usd": _money(cache_write_cost),
        "output_usd": _money(output_cost),
        "total_usd": _money(total),
    }


def _role_and_arm(path: Path, run_dir: Path) -> tuple[str, str]:
    relative = path.relative_to(run_dir).parts
    if relative and relative[0] == "direct":
        return "direct", "direct"
    if len(relative) > 1 and relative[:2] == ("discipl", "planner"):
        return "planner", "discipl"
    if relative and relative[0] == "discipl":
        return "follower", "discipl"
    return "unknown", "unknown"


def _discover_result_paths(run_dir: Path) -> list[Path]:
    expected = [
        *run_dir.glob("direct/calls/*/result.json"),
        *run_dir.glob("discipl/planner/result.json"),
        *run_dir.glob("discipl/calls/*/result.json"),
    ]
    seen = {path.resolve() for path in expected if path.is_file()}
    for path in run_dir.glob("**/result.json"):
        if path.is_file():
            seen.add(path.resolve())
    return sorted(seen, key=lambda item: item.relative_to(run_dir.resolve()).as_posix())


def _call_record(path: Path, run_dir: Path) -> dict[str, Any]:
    result = _read_object(path)
    intent_path = path.parent / "intent.json"
    intent = _read_object(intent_path) if intent_path.is_file() else {}
    context_path = path.parent / "context.json"
    context = _read_object(context_path) if context_path.is_file() else {}
    default_role, default_arm = _role_and_arm(path, run_dir)
    usage_source = result.get("usage")
    if not isinstance(usage_source, dict):
        usage_source = result
    requested_model = (
        result.get("requested_model")
        or intent.get("requested_model")
        or intent.get("model")
    )
    returned_model = result.get("returned_model")
    status = str(result.get("status", "unknown"))
    exit_code = result.get("exit_code")
    retry_count = result.get("retry_count", intent.get("retry_count"))
    if isinstance(retry_count, bool) or not isinstance(retry_count, int):
        attempt = context.get("attempt")
        retry_count = (
            max(attempt - 1, 0)
            if isinstance(attempt, int) and not isinstance(attempt, bool)
            else 0
        )
    return {
        "call_id": str(result.get("call_id") or intent.get("call_id") or path.parent.name),
        "role": str(
            result.get("role") or intent.get("role") or context.get("role") or default_role
        ),
        "arm": str(
            result.get("arm") or intent.get("arm") or context.get("arm") or default_arm
        ),
        "particle_id": result.get("particle_id")
        or intent.get("particle_id")
        or context.get("particle_id"),
        "parent_id": result.get("parent_id")
        or intent.get("parent_id")
        or context.get("parent_id"),
        "step_id": result.get("step_id")
        or intent.get("step_id")
        or context.get("step_id"),
        "requested_model": requested_model,
        "returned_model": returned_model,
        "reasoning_effort": result.get("reasoning_effort")
        or intent.get("reasoning_effort"),
        "status": status,
        "exit_code": exit_code,
        "duration_seconds": float(result.get("duration_seconds") or 0.0),
        "queue_duration_seconds": float(result.get("queue_duration_seconds") or 0.0),
        "retry_count": retry_count,
        "timed_out": bool(result.get("timed_out")) or "timeout" in status.lower(),
        "error": result.get("error"),
        "usage": normalize_usage(usage_source),
        "evidence_path": path.relative_to(run_dir).as_posix(),
    }


def load_call_records(run_dir: Path) -> list[dict[str, Any]]:
    """Load completed worker result records in deterministic path order."""

    run_dir = run_dir.resolve()
    return [_call_record(path, run_dir) for path in _discover_result_paths(run_dir)]


def _load_optional_object(path: Path) -> dict[str, Any] | None:
    return _read_object(path) if path.is_file() else None


def _verification_summary(run_dir: Path, arm: str) -> dict[str, Any] | None:
    path = run_dir / arm / "verification.json"
    value = _load_optional_object(path)
    if value is None:
        return None
    return {
        "outcome": value.get("outcome") or value.get("status") or "UNKNOWN",
        "duration_seconds": value.get("duration_seconds")
        or value.get("verifier_duration_seconds"),
        "exact": value.get("exact"),
        "initial_exact": value.get("initial_exact"),
        "transition_sound": value.get("transition_sound"),
        "transition_complete": value.get("transition_complete"),
        "rooted_state_exact": value.get("rooted_state_exact"),
        "evidence_path": path.relative_to(run_dir).as_posix(),
        "details": value,
    }


def _trace_summary(run_dir: Path) -> dict[str, Any] | None:
    path = run_dir / "discipl" / "trace.jsonl"
    if not path.is_file():
        return None
    records: list[dict[str, Any]] = []
    malformed = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        if isinstance(value, dict):
            records.append(value)
        else:
            malformed += 1
    ess_values = [
        float(item["ess"])
        for item in records
        if isinstance(item.get("ess"), (int, float))
        and not isinstance(item.get("ess"), bool)
    ]
    step_ids = {
        str(item.get("step_id", item.get("step_index")))
        for item in records
        if item.get("step_id", item.get("step_index")) is not None
    }
    return {
        "record_count": len(records),
        "malformed_line_count": malformed,
        "completed_steps": len(step_ids),
        "resampling_events": sum(bool(item.get("resampled")) for item in records),
        "minimum_ess": min(ess_values) if ess_values else None,
        "final_ess": ess_values[-1] if ess_values else None,
        "particle_collapse": any(
            item.get("stopping_reason") == "particle_collapse" for item in records
        ),
        "evidence_path": path.relative_to(run_dir).as_posix(),
    }


def _arm_summary(
    arm: str,
    calls: list[dict[str, Any]],
    rate_card: Mapping[str, Any] | None,
    verification: dict[str, Any] | None,
) -> dict[str, Any]:
    arm_calls = [call for call in calls if call["arm"] == arm]
    priced_calls: list[dict[str, Any]] = []
    for call in arm_calls:
        model = call.get("returned_model") or call.get("requested_model")
        if rate_card is not None:
            priced_calls.append(price_equivalent(call["usage"], model, rate_card))
    successful = sum(
        call["status"].lower() in SUCCESS_STATUSES
        and (call["exit_code"] in (None, 0))
        for call in arm_calls
    )
    return {
        "call_count": len(arm_calls),
        "successful_calls": successful,
        "failed_calls": len(arm_calls) - successful,
        "timeouts": sum(call["timed_out"] for call in arm_calls),
        "retries": sum(call["retry_count"] for call in arm_calls),
        "call_duration_seconds": sum(call["duration_seconds"] for call in arm_calls),
        "queue_duration_seconds": sum(
            call["queue_duration_seconds"] for call in arm_calls
        ),
        "usage": add_usage(call["usage"] for call in arm_calls),
        "api_price_equivalent": {
            "currency": (rate_card or {}).get("currency", "USD"),
            "rate_card_date": (rate_card or {}).get("observed_date"),
            "fully_priced": bool(rate_card is not None)
            and all(item.get("priced") for item in priced_calls),
            "total_usd": _money(
                sum(
                    (Decimal(str(item.get("total_usd", 0))) for item in priced_calls),
                    Decimal(0),
                )
            ),
        },
        "verification": verification,
    }


def aggregate_run(
    run_dir: Path, *, rate_card_path: Path | None = None
) -> dict[str, Any]:
    """Build a comparison summary solely from durable files in ``run_dir``."""

    run_dir = run_dir.resolve()
    if not run_dir.is_dir():
        raise EvidenceError(f"run directory does not exist: {run_dir}")
    manifest = _load_optional_object(run_dir / "manifest.json") or {}
    card_path = rate_card_path or (run_dir / "rate-card.json")
    rate_card = load_rate_card(card_path) if card_path.is_file() else None
    calls = load_call_records(run_dir)
    direct_verification = _verification_summary(run_dir, "direct")
    discipl_verification = _verification_summary(run_dir, "discipl")
    arms = {
        "direct": _arm_summary("direct", calls, rate_card, direct_verification),
        "discipl": _arm_summary(
            "discipl", calls, rate_card, discipl_verification
        ),
    }
    errors = [
        {
            "call_id": call["call_id"],
            "arm": call["arm"],
            "role": call["role"],
            "status": call["status"],
            "error": call["error"],
        }
        for call in calls
        if call["status"].lower() not in SUCCESS_STATUSES
        or call["exit_code"] not in (None, 0)
    ]
    if rate_card is None:
        errors.append(
            {
                "kind": "missing_rate_card",
                "path": "rate-card.json",
                "message": "API-price-equivalent totals are unavailable",
            }
        )
    totals_usage = add_usage(call["usage"] for call in calls)
    return {
        "schema_version": "tla-steer-summary/0.1",
        "run_id": manifest.get("run_id", run_dir.name),
        "experiment_id": manifest.get("experiment_id", "twolights-prototype"),
        "containment_mode": manifest.get("containment_mode", "unknown"),
        "configuration": manifest.get("configuration", manifest.get("config")),
        "run_wall_time_seconds": manifest.get(
            "run_wall_time_seconds", manifest.get("duration_seconds")
        ),
        "run_status": manifest.get("status"),
        "arm_makespan_seconds": manifest.get("arm_makespan_seconds"),
        "maximum_observed_concurrency": manifest.get(
            "maximum_observed_concurrency"
        ),
        "planner_schema_repair_count": manifest.get("planner_schema_repair_count"),
        "follower_call_count": manifest.get("follower_call_count"),
        "rate_card": (
            {
                "observed_date": rate_card["observed_date"],
                "currency": rate_card["currency"],
                "source": rate_card.get("source"),
                "sha256": sha256_file(card_path),
            }
            if rate_card is not None
            else None
        ),
        "arms": arms,
        "totals": {
            "calls": len(calls),
            "usage": totals_usage,
            "api_price_equivalent_usd": _money(
                Decimal(str(arms["direct"]["api_price_equivalent"]["total_usd"]))
                + Decimal(
                    str(arms["discipl"]["api_price_equivalent"]["total_usd"])
                )
            ),
        },
        "smc": _trace_summary(run_dir),
        "calls": calls,
        "errors": errors,
    }


def _display(value: Any, default: str = "—") -> str:
    return default if value is None else str(value)


def render_markdown(summary: Mapping[str, Any]) -> str:
    """Render a compact, presentation-oriented report from a summary object."""

    lines = [
        f"# TLA-Steer comparison: {summary.get('run_id', 'unknown')}",
        "",
        "This is an exploratory comparison; no metric is designated primary and no statistical claim is made.",
        "",
        f"- Containment mode: `{summary.get('containment_mode', 'unknown')}`",
        f"- Run wall time (seconds): {_display(summary.get('run_wall_time_seconds'))}",
        f"- Arm makespans (seconds): {_display(summary.get('arm_makespan_seconds'))}",
        f"- Maximum observed concurrency: {_display(summary.get('maximum_observed_concurrency'))}",
        f"- Planner schema repairs: {_display(summary.get('planner_schema_repair_count'))}",
        f"- Follower calls: {_display(summary.get('follower_call_count'))}",
        f"- Total calls: {summary.get('totals', {}).get('calls', 0)}",
        f"- Total API-price-equivalent (USD): {summary.get('totals', {}).get('api_price_equivalent_usd', 0)}",
        "",
        "| Arm | Verifier outcome | Calls | Input tokens | Cached input | Cache writes | Output tokens | Reasoning output | Call seconds | API-price-equivalent USD |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    arms = summary.get("arms", {})
    if not isinstance(arms, Mapping):
        arms = {}
    for arm in ("direct", "discipl"):
        item = arms.get(arm, {})
        if not isinstance(item, Mapping):
            item = {}
        usage = item.get("usage", {})
        if not isinstance(usage, Mapping):
            usage = {}
        verification = item.get("verification")
        outcome = verification.get("outcome") if isinstance(verification, Mapping) else "NOT_RUN"
        price = item.get("api_price_equivalent", {})
        if not isinstance(price, Mapping):
            price = {}
        lines.append(
            f"| {arm} | {outcome} | {item.get('call_count', 0)} | "
            f"{usage.get('input_tokens', 0)} | {usage.get('cached_input_tokens', 0)} | "
            f"{usage.get('cache_write_input_tokens', 0)} | {usage.get('output_tokens', 0)} | "
            f"{usage.get('reasoning_output_tokens', 0)} | {item.get('call_duration_seconds', 0):.3f} | "
            f"{price.get('total_usd', 0)} |"
        )
    smc = summary.get("smc")
    if isinstance(smc, Mapping):
        lines.extend(
            [
                "",
                "## DisCIPL-style SMC trace",
                "",
                f"- Completed semantic steps: {smc.get('completed_steps', 0)}",
                f"- Trace records: {smc.get('record_count', 0)}",
                f"- Resampling events: {smc.get('resampling_events', 0)}",
                f"- Minimum / final ESS: {_display(smc.get('minimum_ess'))} / {_display(smc.get('final_ess'))}",
                f"- Particle collapse: {smc.get('particle_collapse', False)}",
            ]
        )
    errors = summary.get("errors", [])
    if isinstance(errors, list) and errors:
        lines.extend(["", "## Recorded errors and missing evidence", ""])
        for error in errors:
            lines.append(f"- `{json.dumps(error, sort_keys=True, ensure_ascii=False)}`")
    rate = summary.get("rate_card")
    if isinstance(rate, Mapping):
        lines.extend(
            [
                "",
                (
                    "API-price-equivalent values use the static rate card observed "
                    f"{rate.get('observed_date')}; they are not actual marginal Codex OAuth charges."
                ),
            ]
        )
    return "\n".join(lines) + "\n"


def write_run_report(
    run_dir: Path, *, rate_card_path: Path | None = None
) -> dict[str, Any]:
    """Rebuild and persist ``summary.json`` and ``summary.md`` offline."""

    summary = aggregate_run(run_dir, rate_card_path=rate_card_path)
    write_json(run_dir / "summary.json", summary)
    _atomic_write(run_dir / "summary.md", render_markdown(summary))
    return summary
