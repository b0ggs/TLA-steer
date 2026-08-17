#!/usr/bin/env python3
"""Regeneration after a prospective plan decision; not independent validation."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from fractions import Fraction
from pathlib import Path
from typing import Any


SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-development-simulation-v2"
AUTH_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-development-a-authorization-v2"
PROVENANCE_LABEL = "regeneration after a prospective plan decision"
INDEPENDENT_VALIDATION = False
ACTIVATION_CRITERION_IDS = ("AC-02", "AC-03", "AC-04", "AC-05", "AC-06", "AC-07", "AC-08")
REQUIRED_REPORTED_DIAGNOSTIC_IDS = ("AC-01",)
SEED = 2026081401
TRIALS = 20_000
REQUIREMENT_COUNTS = (8, 9, 10, 11, 12)
PLAN_BINDING = {
    "commit": "996614be4e0e783377155207fe91defb8065f4b0",
    "path": "CODER_BENEFICIAL_SENSITIVITY_M2_IMPLEMENTATION_PLAN.md",
    "sha256": "7211cf9ebbcc96df781cb0c89e1decccbe276ca123d0aa12a8f5af427a277357",
}
REGRESSION_BINDING = {
    "path": "experiments/coder-beneficial-sensitivity-m2-development-regression.json",
    "sha256": "143e0bf44270efadf744b02b2b8c646adc752766c258fc8a0ed6ee936ddc87da",
}
GATES = {
    "attempts_per_task": 3,
    "prototype_coverage_min": "11/20",
    "prototype_coverage_max": "9/10",
    "prototype_resolved_attempts": [1, 2],
    "four_task_coverage_min": "11/20",
    "four_task_coverage_max": "9/10",
    "four_task_minimum_mixed": 2,
    "eight_task_coverage_min": "11/20",
    "eight_task_coverage_max": "9/10",
    "eight_task_minimum_mixed": 4,
    "all_nonresolution_must_be_omission_only": True,
    "fidelity_required_for_every_task": True,
}
SCENARIOS = (
    {
        "id": "homogeneous-floor-hurdle",
        "group": "extreme",
        "kind": "hurdle",
        "resolved_rate": "1/50",
        "partial_requirement_pass_rate": "3/20",
    },
    {
        "id": "homogeneous-ceiling-hurdle",
        "group": "extreme",
        "kind": "hurdle",
        "resolved_rate": "49/50",
        "partial_requirement_pass_rate": "19/20",
    },
    {
        "id": "homogeneous-floor-independent",
        "group": "extreme",
        "kind": "independent",
        "requirement_pass_rate": "1/5",
    },
    {
        "id": "homogeneous-ceiling-independent",
        "group": "extreme",
        "kind": "independent",
        "requirement_pass_rate": "49/50",
    },
    {
        "id": "correlated-beta-floor",
        "group": "extreme",
        "kind": "beta_binomial",
        "alpha": "9/100",
        "beta": "51/100",
    },
    {
        "id": "correlated-beta-ceiling",
        "group": "extreme",
        "kind": "beta_binomial",
        "alpha": "57/100",
        "beta": "3/100",
    },
    {
        "id": "homogeneous-intermediate-balanced",
        "group": "primary_intermediate",
        "kind": "hurdle",
        "resolved_rate": "1/2",
        "partial_requirement_pass_rate": "1/2",
    },
    {
        "id": "heterogeneous-intermediate",
        "group": "primary_intermediate",
        "kind": "heterogeneous_hurdle",
        "resolved_rates": ["2/5", "3/5", "1/4", "3/4", "7/20", "13/20", "9/20", "11/20"],
        "partial_requirement_pass_rates": ["11/20", "2/5", "13/20", "1/4", "3/5", "7/20", "1/2", "9/20"],
    },
    {
        "id": "correlated-beta-intermediate",
        "group": "primary_intermediate",
        "kind": "beta_binomial",
        "alpha": "9/20",
        "beta": "3/20",
    },
    {
        "id": "homogeneous-intermediate-low-resolution",
        "group": "diagnostic_intermediate",
        "kind": "hurdle",
        "resolved_rate": "7/20",
        "partial_requirement_pass_rate": "11/20",
    },
    {
        "id": "homogeneous-intermediate-high-resolution",
        "group": "diagnostic_intermediate",
        "kind": "hurdle",
        "resolved_rate": "13/20",
        "partial_requirement_pass_rate": "7/20",
    },
    {
        "id": "homogeneous-intermediate-independent",
        "group": "diagnostic_intermediate",
        "kind": "independent",
        "requirement_pass_rate": "3/4",
    },
)
REPORTED_CRITERIA = (
    {
        "id": "AC-01",
        "metric": "maximum extreme Task-A pass probability",
        "operator": "<=",
        "threshold": "4/25",
    },
    {
        "id": "AC-02",
        "metric": "maximum extreme Development-PASS probability",
        "operator": "<=",
        "threshold": "1/50",
    },
    {
        "id": "AC-03",
        "metric": "minimum primary-intermediate Task-A pass probability",
        "operator": ">=",
        "threshold": "3/10",
    },
    {
        "id": "AC-04",
        "metric": "primary-intermediate mean Task-A probability minus maximum extreme Task-A probability",
        "operator": ">=",
        "threshold": "1/4",
    },
    {
        "id": "AC-05",
        "metric": "primary-intermediate mean Development-PASS probability",
        "operator": ">=",
        "threshold": "2/25",
    },
    {
        "id": "AC-06",
        "metric": "primary-intermediate mean Development-PASS probability minus maximum extreme Development-PASS probability",
        "operator": ">=",
        "threshold": "3/50",
    },
    {
        "id": "AC-07",
        "metric": "requirement-count support in every scenario",
        "operator": "==",
        "threshold": [8, 9, 10, 11, 12],
    },
    {
        "id": "AC-08",
        "metric": "scenario result completeness",
        "operator": "==",
        "threshold": len(SCENARIOS),
    },
)


def canonical(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_fraction(value: str) -> Fraction:
    numerator, denominator = value.split("/", 1)
    return Fraction(int(numerator), int(denominator))


def fraction_record(value: Fraction) -> dict[str, object]:
    return {
        "denominator": value.denominator,
        "numerator": value.numerator,
        "value": round(float(value), 8),
    }


def probability_record(count: int) -> dict[str, object]:
    return {"count": count, "trials": TRIALS, **fraction_record(Fraction(count, TRIALS))}


def scenario_seed(identifier: str) -> int:
    material = f"{SEED}:{identifier}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(material).digest(), "big")


def task_parameters(scenario: dict[str, Any], task_index: int) -> dict[str, Any]:
    if scenario["kind"] == "heterogeneous_hurdle":
        return {
            "kind": "hurdle",
            "resolved_rate": scenario["resolved_rates"][task_index],
            "partial_requirement_pass_rate": scenario[
                "partial_requirement_pass_rates"
            ][task_index],
        }
    return scenario


def attempt_passes(
    rng: random.Random, scenario: dict[str, Any], requirement_count: int
) -> list[bool]:
    kind = scenario["kind"]
    if kind == "hurdle":
        resolved_rate = float(parse_fraction(scenario["resolved_rate"]))
        if rng.random() < resolved_rate:
            return [True] * requirement_count
        partial_rate = float(
            parse_fraction(scenario["partial_requirement_pass_rate"])
        )
        result = [rng.random() < partial_rate for _ in range(requirement_count)]
        if all(result):
            result[rng.randrange(requirement_count)] = False
        return result
    if kind == "independent":
        rate = float(parse_fraction(scenario["requirement_pass_rate"]))
        return [rng.random() < rate for _ in range(requirement_count)]
    if kind == "beta_binomial":
        alpha = float(parse_fraction(scenario["alpha"]))
        beta = float(parse_fraction(scenario["beta"]))
        rate = rng.betavariate(alpha, beta)
        return [rng.random() < rate for _ in range(requirement_count)]
    raise ValueError(f"unknown scenario kind: {kind}")


def task_stats(
    rng: random.Random, scenario: dict[str, Any], task_index: int, requirements: int
) -> dict[str, Any]:
    parameters = task_parameters(scenario, task_index)
    attempts = [attempt_passes(rng, parameters, requirements) for _ in range(3)]
    resolved = sum(all(attempt) for attempt in attempts)
    passed = sum(sum(attempt) for attempt in attempts)
    return {
        "requirements": requirements,
        "resolved": resolved,
        "coverage": Fraction(passed, 3 * requirements),
        "omission_only": all(all(attempt) or not all(attempt) for attempt in attempts),
    }


def in_band(value: Fraction) -> bool:
    return Fraction(11, 20) <= value <= Fraction(9, 10)


def prototype_pass(task: dict[str, Any]) -> bool:
    return (
        in_band(task["coverage"])
        and task["resolved"] in {1, 2}
        and task["omission_only"]
    )


def aggregate_pass(tasks: list[dict[str, Any]], minimum_mixed: int) -> bool:
    macro_coverage = sum((task["coverage"] for task in tasks), Fraction()) / len(
        tasks
    )
    mixed = sum(task["resolved"] in {1, 2} for task in tasks)
    return (
        in_band(macro_coverage)
        and mixed >= minimum_mixed
        and all(task["omission_only"] for task in tasks)
    )


def simulate_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(scenario_seed(scenario["id"]))
    counts = {
        "task_a_pass": 0,
        "task_b_checkpoint_pass": 0,
        "four_task_checkpoint_pass": 0,
        "development_pass": 0,
    }
    requirement_histogram = {str(value): 0 for value in REQUIREMENT_COUNTS}
    for _ in range(TRIALS):
        requirement_counts = [rng.choice(REQUIREMENT_COUNTS) for _ in range(8)]
        for value in requirement_counts:
            requirement_histogram[str(value)] += 1
        tasks = [
            task_stats(rng, scenario, index, requirement_counts[index])
            for index in range(8)
        ]
        passed_a = prototype_pass(tasks[0])
        passed_b = passed_a and prototype_pass(tasks[1])
        passed_four = passed_b and aggregate_pass(tasks[:4], 2)
        passed_eight = passed_four and aggregate_pass(tasks, 4)
        counts["task_a_pass"] += passed_a
        counts["task_b_checkpoint_pass"] += passed_b
        counts["four_task_checkpoint_pass"] += passed_four
        counts["development_pass"] += passed_eight
    return {
        "id": scenario["id"],
        "group": scenario["group"],
        "kind": scenario["kind"],
        "checkpoint_probabilities": {
            key: probability_record(value) for key, value in counts.items()
        },
        "requirement_count_observations": requirement_histogram,
    }


def metric_fraction(result: dict[str, Any], key: str) -> Fraction:
    record = result["checkpoint_probabilities"][key]
    return Fraction(record["count"], record["trials"])


def evaluate_criteria(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    extremes = [result for result in results if result["group"] == "extreme"]
    primary = [
        result for result in results if result["group"] == "primary_intermediate"
    ]
    extreme_a = max(metric_fraction(result, "task_a_pass") for result in extremes)
    extreme_dev = max(
        metric_fraction(result, "development_pass") for result in extremes
    )
    primary_a_values = [metric_fraction(result, "task_a_pass") for result in primary]
    primary_dev_values = [
        metric_fraction(result, "development_pass") for result in primary
    ]
    primary_a_mean = sum(primary_a_values, Fraction()) / len(primary_a_values)
    primary_dev_mean = sum(primary_dev_values, Fraction()) / len(primary_dev_values)
    support_ok = all(
        sorted(
            int(key)
            for key, count in result["requirement_count_observations"].items()
            if count > 0
        )
        == list(REQUIREMENT_COUNTS)
        for result in results
    )
    observations: dict[str, tuple[object, bool]] = {
        "AC-01": (extreme_a, extreme_a <= Fraction(4, 25)),
        "AC-02": (extreme_dev, extreme_dev <= Fraction(1, 50)),
        "AC-03": (min(primary_a_values), min(primary_a_values) >= Fraction(3, 10)),
        "AC-04": (
            primary_a_mean - extreme_a,
            primary_a_mean - extreme_a >= Fraction(1, 4),
        ),
        "AC-05": (primary_dev_mean, primary_dev_mean >= Fraction(2, 25)),
        "AC-06": (
            primary_dev_mean - extreme_dev,
            primary_dev_mean - extreme_dev >= Fraction(3, 50),
        ),
        "AC-07": (list(REQUIREMENT_COUNTS) if support_ok else [], support_ok),
        "AC-08": (len(results), len(results) == len(SCENARIOS)),
    }
    evaluated = []
    for criterion in REPORTED_CRITERIA:
        observed, passed = observations[criterion["id"]]
        evaluated.append(
            {
                **criterion,
                "observed": (
                    fraction_record(observed)
                    if isinstance(observed, Fraction)
                    else observed
                ),
                "passed": passed,
                "role": (
                    "activation"
                    if criterion["id"] in ACTIVATION_CRITERION_IDS
                    else "required_reported_diagnostic"
                ),
            }
        )
    return evaluated


def load_authorization(path: Path, script_sha256: str) -> dict[str, Any]:
    authorization = json.loads(path.read_text(encoding="utf-8"))
    if authorization.get("schema") != AUTH_SCHEMA:
        raise ValueError("wrong authorization schema")
    if authorization.get("status") != "CONDITIONAL" or authorization.get(
        "initial_execution_state"
    ) != "DISABLED":
        raise ValueError("authorization is not prospectively disabled")
    if authorization.get("source_bindings") != {
        "active_plan": PLAN_BINDING,
        "historical_regression": REGRESSION_BINDING,
    }:
        raise ValueError("source binding mismatch")
    simulation = authorization.get("simulation")
    expected = {
        "activation_criterion_ids": list(ACTIVATION_CRITERION_IDS),
        "classification": "engineering_screen_not_power_calculation_or_scientific_threshold",
        "deliverable_output": "experiments/coder-beneficial-sensitivity-m2-development-simulation-v2.json",
        "gates": GATES,
        "independent_validation": INDEPENDENT_VALIDATION,
        "no_post_output_tuning": True,
        "provenance_label": PROVENANCE_LABEL,
        "reported_criteria": list(REPORTED_CRITERIA),
        "required_reported_diagnostic_ids": list(REQUIRED_REPORTED_DIAGNOSTIC_IDS),
        "requirement_counts": list(REQUIREMENT_COUNTS),
        "scenarios": list(SCENARIOS),
        "seed": SEED,
        "single_deliverable_run": True,
        "trials_per_scenario": TRIALS,
    }
    if not isinstance(simulation, dict):
        raise ValueError("missing simulation authorization")
    script = simulation.get("script")
    if script != {
        "path": "scripts/coder_beneficial_sensitivity_m2_development_simulation_v2.py",
        "sha256": script_sha256,
    }:
        raise ValueError("script binding mismatch")
    if {key: value for key, value in simulation.items() if key != "script"} != expected:
        raise ValueError("simulation specification mismatch")
    root = path.resolve().parent.parent
    for binding in (PLAN_BINDING, REGRESSION_BINDING):
        bound_path = root / binding["path"]
        if sha256_file(bound_path) != binding["sha256"]:
            raise ValueError(f"source drift: {binding['path']}")
    return authorization


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorization", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    script_path = Path(__file__).resolve()
    script_sha256 = sha256_file(script_path)
    authorization = load_authorization(arguments.authorization, script_sha256)
    authorization_sha256 = sha256_file(arguments.authorization)
    results = [simulate_scenario(scenario) for scenario in SCENARIOS]
    criteria = evaluate_criteria(results)
    status = (
        "PASS"
        if all(
            item["passed"]
            for item in criteria
            if item["id"] in ACTIVATION_CRITERION_IDS
        )
        else "STOP"
    )
    output = {
        "activation_criterion_ids": list(ACTIVATION_CRITERION_IDS),
        "authorization": {
            "path": "experiments/coder-beneficial-sensitivity-m2-development-a-authorization-v2.json",
            "sha256": authorization_sha256,
        },
        "classification": authorization["simulation"]["classification"],
        "gates": GATES,
        "independent_validation": INDEPENDENT_VALIDATION,
        "provenance_label": PROVENANCE_LABEL,
        "reported_criteria": criteria,
        "required_reported_diagnostic_ids": list(REQUIRED_REPORTED_DIAGNOSTIC_IDS),
        "requirement_counts": list(REQUIREMENT_COUNTS),
        "scenario_results": results,
        "schema": SCHEMA,
        "script": {
            "path": "scripts/coder_beneficial_sensitivity_m2_development_simulation_v2.py",
            "sha256": script_sha256,
        },
        "seed": SEED,
        "status": status,
        "trials_per_scenario": TRIALS,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    with arguments.output.open("xb") as stream:
        stream.write(canonical(output))
    print(status)
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

