"""Durable evidence aggregation and offline reporting for one prototype run.

The trusted coordinator owns aggregate files.  Workers write isolated call
spools; this module reads those spools only after the calls have completed.
"""

from __future__ import annotations

import hashlib
import json
import math
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


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON value: {value}")


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_pairs, parse_constant=_reject_constant)
    except (OSError, ValueError, UnicodeError) as exc:
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


def normalize_usage(source: Mapping[str, Any] | None) -> dict[str, Any]:
    """Unknown or invalid usage is null, never a zero-cost observation."""

    source = source or {}
    valid = source.get("usage_reported") is True and all(
        isinstance(source.get(field), int) and not isinstance(source.get(field), bool)
        and source[field] >= 0 for field in USAGE_FIELDS
    )
    if valid:
        valid = (source["cached_input_tokens"] + source["cache_write_input_tokens"]
                 <= source["input_tokens"] and source["reasoning_output_tokens"] <= source["output_tokens"])
    usage = {field: source[field] if valid else None for field in USAGE_FIELDS}
    usage["usage_reported"] = valid
    usage["total_tokens"] = source["input_tokens"] + source["output_tokens"] if valid else None
    return usage


def add_usage(values: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    normalized = [normalize_usage(value) for value in values]
    if not all(value["usage_reported"] for value in normalized):
        return normalize_usage(None)
    totals = {field: sum(value[field] for value in normalized) for field in USAGE_FIELDS}
    return normalize_usage({**totals, "usage_reported": True})


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
    rates = models.get(model) if isinstance(models, dict) and isinstance(model, str) else None
    base = {
        "currency": rate_card.get("currency", "USD"),
        "rate_card_date": rate_card.get("observed_date"),
        "model": model,
        "usage_reported": normalized["usage_reported"],
    }
    if not normalized["usage_reported"]:
        return {**base, "priced": False, "total_usd": None, "reason": "usage_unknown_or_invalid"}
    if not isinstance(rates, dict):
        return {**base, "priced": False, "reason": "model_not_in_rate_card", "total_usd": None}

    try:
        input_rate = Decimal(str(rates["input"]))
        cached_rate = Decimal(str(rates["cached_input"]))
        output_rate = Decimal(str(rates["output"]))
        cache_write_rate = Decimal(
            str(rates.get("cache_write_input", rates["input"]))
        )
    except (KeyError, ArithmeticError, ValueError) as exc:
        raise EvidenceError(f"invalid rates for {model}") from exc

    if not all(rate.is_finite() and rate >= 0 for rate in (input_rate, cached_rate, output_rate, cache_write_rate)):
        raise EvidenceError(f"invalid rates for {model}")
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
    if not all(rate.is_finite() and rate >= 0 for rate in (input_multiplier, output_multiplier)):
        raise EvidenceError(f"invalid rate multipliers for {model}")
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
    if relative and relative[0] in {"direct", "cheap_alone"}:
        return relative[0], relative[0]
    if len(relative) > 1 and relative[:2] == ("discipl", "planner"):
        return "planner", "discipl"
    if relative and relative[0] == "discipl":
        return "follower", "discipl"
    return "unknown", "unknown"


def _discover_result_paths(run_dir: Path) -> list[Path]:
    # Include intent-only attempts; missing terminal evidence must not disappear.
    spools = {path.parent for pattern in ("**/result.json", "**/intent.json")
              for path in run_dir.glob(pattern) if path.is_file()}
    return [directory / "result.json" for directory in sorted(spools)]


def _call_record(path: Path, run_dir: Path) -> dict[str, Any]:
    issues: list[str] = []

    def read(name: str, *, required: bool = True) -> dict[str, Any]:
        target = path.parent / name
        if not required and not target.is_file():
            return {}
        try:
            return _read_object(target)
        except EvidenceError as exc:
            issues.append(str(exc))
            return {}

    result = read("result.json")
    intent = read("intent.json")
    context = read("context.json", required=False)
    role, arm = _role_and_arm(path, run_dir)
    for name, document in (("intent", intent), ("result", result)):
        if document.get("call_id") != path.parent.name:
            issues.append(f"{name} call_id differs from spool")
        if document.get("role") != role or role == "unknown":
            issues.append(f"{name} role differs from spool")
    for field in ("requested_model", "reasoning_effort"):
        if (not isinstance(intent.get(field), str) or not intent[field]
                or result.get(field) != intent[field]):
            issues.append(f"intent/result {field} missing or inconsistent")
    returned_model = result.get("returned_model")
    if returned_model is not None and (not isinstance(returned_model, str) or not returned_model):
        issues.append("invalid returned_model")
        returned_model = None
    status = result.get("status")
    if not isinstance(status, str) or not status:
        issues.append("missing or invalid result status")
        status = "INVALID_EVIDENCE"
    exit_code = result.get("exit_code")
    if exit_code is not None and (isinstance(exit_code, bool) or not isinstance(exit_code, int)):
        issues.append("invalid exit code")
        exit_code = None
    usage = normalize_usage(result.get("usage") if isinstance(result.get("usage"), dict) else None)
    if not usage["usage_reported"]:
        issues.append("usage missing, incomplete or invalid")
    if result.get("event_fatal_defects"):
        issues.append("worker recorded invalid event evidence")
    durations = {}
    for field in ("duration_seconds", "queue_duration_seconds"):
        value = result.get(field)
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value < 0:
            issues.append(f"missing or invalid {field}")
            value = 0.0
        durations[field] = float(value)
    attempt = context.get("attempt", 1)
    retry_count = max(attempt - 1, 0) if isinstance(attempt, int) and not isinstance(attempt, bool) else 0
    if issues:
        usage = normalize_usage(None)
    return {
        "call_id": str(result.get("call_id") or intent.get("call_id") or path.parent.name),
        "role": role, "arm": arm,
        "particle_id": context.get("particle_id"), "parent_id": context.get("parent_id"),
        "step_id": context.get("step_id"),
        "requested_model": result.get("requested_model") or intent.get("requested_model"),
        "returned_model": returned_model,
        "reasoning_effort": result.get("reasoning_effort") or intent.get("reasoning_effort"),
        "status": status, "exit_code": exit_code, **durations,
        "retry_count": retry_count,
        "timed_out": result.get("timed_out") is True or "timeout" in status.lower(),
        "error": result.get("error"), "usage": usage,
        "evidence_path": path.relative_to(run_dir).as_posix(), "evidence_errors": issues,
    }


def load_call_records(run_dir: Path) -> list[dict[str, Any]]:
    """Reconcile both sides of every observed intent/result spool."""

    run_dir = run_dir.resolve()
    calls = [_call_record(path, run_dir) for path in _discover_result_paths(run_dir)]
    ids: dict[str, list[dict[str, Any]]] = {}
    for call in calls:
        ids.setdefault(call["call_id"], []).append(call)
    for call_id, duplicates in ids.items():
        if len(duplicates) > 1:
            for call in duplicates:
                call["evidence_errors"].append(f"duplicate call_id: {call_id}")
                call["usage"] = normalize_usage(None)
    return calls


def _accounting(manifest: Mapping[str, Any], calls: list[dict[str, Any]]) -> dict[str, Any]:
    expected = manifest.get("attempted_calls_by_role")
    observed = {role: sum(call["role"] == role for call in calls)
                for role in ("direct", "cheap_alone", "planner", "follower")}
    issues = []
    bad_arms = set()
    if (not isinstance(expected, dict) or not expected or any(
        role not in observed or isinstance(count, bool) or not isinstance(count, int) or count < 0
        for role, count in expected.items()
    )):
        issues.append("missing or invalid coordinator attempted-call counts")
        expected = None
        bad_arms.update(("direct", "cheap_alone", "discipl"))
    else:
        for role in observed:
            if observed[role] != expected.get(role, 0):
                issues.append(f"{role}: coordinator attempted {expected.get(role, 0)}, observed {observed[role]}")
                bad_arms.add(role if role in {"direct", "cheap_alone"} else "discipl")
    for call in calls:
        if call["evidence_errors"]:
            bad_arms.add(call["arm"])
            issues.extend(f"{call['evidence_path']}: {error}" for error in call["evidence_errors"])
        if call["arm"] == "unknown":
            bad_arms.update(("direct", "cheap_alone", "discipl"))
    return {"complete": not issues, "attempted_by_role": expected,
            "observed_by_role": observed, "observed_records": len(calls),
            "incomplete_arms": sorted(bad_arms), "issues": issues}


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
    *, complete: bool,
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
    fully_priced = complete and rate_card is not None and all(item.get("priced") for item in priced_calls)
    return {
        "accounting_complete": complete,
        "call_count": len(arm_calls),
        "successful_calls": successful,
        "failed_calls": len(arm_calls) - successful,
        "timeouts": sum(call["timed_out"] for call in arm_calls),
        "retries": sum(call["retry_count"] for call in arm_calls),
        "call_duration_seconds": sum(call["duration_seconds"] for call in arm_calls),
        "queue_duration_seconds": sum(
            call["queue_duration_seconds"] for call in arm_calls
        ),
        "usage": add_usage(call["usage"] for call in arm_calls) if complete else normalize_usage(None),
        "api_price_equivalent": {
            "currency": (rate_card or {}).get("currency", "USD"),
            "rate_card_date": (rate_card or {}).get("observed_date"),
            "fully_priced": fully_priced,
            "total_usd": _money(sum((Decimal(str(item["total_usd"])) for item in priced_calls), Decimal(0))) if fully_priced else None,
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
    expected_card_hash = manifest.get("inputs", {}).get("rate_card_sha256")
    if card_path.is_file() and expected_card_hash and sha256_file(card_path) != expected_card_hash:
        raise EvidenceError("rate card differs from the frozen run snapshot")
    rate_card = load_rate_card(card_path) if card_path.is_file() else None
    calls = load_call_records(run_dir)
    accounting = _accounting(manifest, calls)
    arm_names = ["direct", "cheap_alone", "discipl"] if (
        "cheap_alone" in manifest.get("arms", []) or any(call["arm"] == "cheap_alone" for call in calls)
    ) else ["direct", "discipl"]
    arms = {arm: _arm_summary(arm, calls, rate_card, _verification_summary(run_dir, arm),
                              complete=arm not in accounting["incomplete_arms"])
            for arm in arm_names}
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
    errors.extend({"kind": "incomplete_accounting", "message": issue} for issue in accounting["issues"])
    if manifest.get("pipeline_error"):
        errors.append({"kind": "pipeline_error", "message": manifest["pipeline_error"]})
    nonconformities = manifest.get("nonconformities", [])
    if isinstance(nonconformities, list):
        errors.extend(
            {"kind": "nonconformity", "message": message}
            for message in nonconformities
        )
    if rate_card is None:
        errors.append(
            {
                "kind": "missing_rate_card",
                "path": "rate-card.json",
                "message": "API-price-equivalent totals are unavailable",
            }
        )
    totals_usage = add_usage(call["usage"] for call in calls) if accounting["complete"] else normalize_usage(None)
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
        "offline_fixture": manifest.get("offline_fixture", False),
        "measurement_note": manifest.get("measurement_note"),
        "accounting": accounting,
        "arm_makespan_seconds": manifest.get("arm_makespan_seconds"),
        "arm_timing_note": manifest.get("arm_timing_note"),
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
            "attempted_calls": sum(accounting["attempted_by_role"].values()) if accounting["attempted_by_role"] is not None else None,
            "api_price_equivalent_usd": _money(sum(
                (Decimal(str(arm["api_price_equivalent"]["total_usd"])) for arm in arms.values()), Decimal(0)
            )) if accounting["complete"] and all(arm["api_price_equivalent"]["fully_priced"] for arm in arms.values()) else None,
        },
        "smc": _trace_summary(run_dir),
        "calls": calls,
        "errors": errors,
    }


def _display(value: Any, default: str = "—") -> str:
    return default if value is None else str(value)


def render_markdown(summary: Mapping[str, Any]) -> str:
    """Render a compact, presentation-oriented report from a summary object."""

    arm_time_label = "Arm active times" if summary.get("arm_timing_note") else "Arm makespans"
    lines = [
        f"# TLA-Steer comparison: {summary.get('run_id', 'unknown')}",
        "",
        summary.get("measurement_note") or "This is an exploratory comparison; no metric is designated primary and no statistical claim is made.",
        "",
        f"- Containment mode: `{summary.get('containment_mode', 'unknown')}`",
        f"- Run status: `{summary.get('run_status', 'unknown')}`",
        f"- Run wall time (seconds): {_display(summary.get('run_wall_time_seconds'))}",
        f"- {arm_time_label} (seconds): {_display(summary.get('arm_makespan_seconds'))}",
        *([f"- Timing: {summary['arm_timing_note']}"] if summary.get("arm_timing_note") else []),
        f"- Maximum observed concurrency: {_display(summary.get('maximum_observed_concurrency'))}",
        f"- Planner schema repairs: {_display(summary.get('planner_schema_repair_count'))}",
        f"- Follower calls: {_display(summary.get('follower_call_count'))}",
        f"- Observed call records: {summary.get('totals', {}).get('calls', 0)}",
        f"- Coordinator attempted calls: {_display(summary.get('totals', {}).get('attempted_calls'), 'UNKNOWN')}",
        f"- Accounting complete: {summary.get('accounting', {}).get('complete', False)}",
        f"- Total API-price-equivalent (USD): {_display(summary.get('totals', {}).get('api_price_equivalent_usd'), 'UNKNOWN')}",
        "",
        "| Arm | Verifier outcome | Calls | Input tokens | Cached input | Cache writes | Output tokens | Reasoning output | Call seconds | API-price-equivalent USD |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    arms = summary.get("arms", {})
    if not isinstance(arms, Mapping):
        arms = {}
    for arm in arms:
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
            f"{_display(usage.get('input_tokens'), 'UNKNOWN')} | {_display(usage.get('cached_input_tokens'), 'UNKNOWN')} | "
            f"{_display(usage.get('cache_write_input_tokens'), 'UNKNOWN')} | {_display(usage.get('output_tokens'), 'UNKNOWN')} | "
            f"{_display(usage.get('reasoning_output_tokens'), 'UNKNOWN')} | {item.get('call_duration_seconds', 0):.3f} | "
            f"{_display(price.get('total_usd'), 'UNKNOWN')} |"
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
