"""Independent exhaustive verifier for fixed TwoLights Python candidates.

Candidate code is evaluated in a fresh ``python -I -S`` subprocess.  This is
useful process isolation for the prototype, but it is deliberately reported as
``prototype_local``: it is not a hostile-code security boundary and it does
not reproduce the sealed MDs_EVAL container.
"""

from __future__ import annotations

import ast
from collections import deque
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any

from .oracle import (
    ACTION_LABELS,
    ACTION_SYMBOLS,
    CONSTANTS,
    EXPECTED_STATE_COUNT,
    EXPECTED_TRANSITION_COUNT,
    INITIAL,
    OracleError,
    is_type_correct_state,
    iter_type_correct_states,
    oracle_successor,
    self_check,
    state_key,
)


EXACT = "EXACT"
SEMANTIC_MISMATCH = "SEMANTIC_MISMATCH"
INVALID_CANDIDATE = "INVALID_CANDIDATE"
EVALUATOR_ERROR = "EVALUATOR_ERROR"

SCHEMA_VERSION = "tla-steer-verification/0.1"
CONTAINMENT_MODE = "prototype_local"
CONTAINMENT_NOTE = (
    "Candidate code ran in a fresh python -I -S subprocess with restricted "
    "builtins. This prototype fallback is not a hostile-code security boundary "
    "and does not provide the sealed MDs_EVAL containment guarantee."
)
DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_COUNTEREXAMPLES = 20

PRESERVED_FIELDS = {
    "Tick": ("lightA", "lightB"),
    "AGreenToYellow": ("clock", "lightB", "timerB"),
    "AYellowToRed": ("clock", "lightB", "timerB"),
    "ARedToGreen": ("clock", "lightB", "timerB"),
    "BGreenToYellow": ("clock", "lightA", "timerA"),
    "BYellowToRed": ("clock", "lightA", "timerA"),
    "BRedToGreen": ("clock", "lightA", "timerA"),
}


# The child intentionally contains no oracle logic or expected successors.  It
# receives the finite input states, executes every action twice on fresh copies,
# and returns observations for comparison by this trusted host module.
_CANDIDATE_RUNNER = r'''
import json
import sys


STATE_KEYS = {"clock", "lightA", "timerA", "lightB", "timerB"}
COLORS = {"red", "green", "yellow"}


def valid_state(value):
    return (
        type(value) is dict
        and set(value) == STATE_KEYS
        and type(value["clock"]) is int
        and 0 <= value["clock"] < 8
        and type(value["lightA"]) is str
        and value["lightA"] in COLORS
        and type(value["timerA"]) is int
        and 0 <= value["timerA"] <= 6
        and type(value["lightB"]) is str
        and value["lightB"] in COLORS
        and type(value["timerB"]) is int
        and 0 <= value["timerB"] <= 6
    )


def emit(value):
    sys.stdout.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def invalid(kind, message, action=None, state_index=None):
    row = {
        "protocol": "tla-steer-candidate-observations/0.1",
        "status": "invalid_candidate",
        "failure": {
            "kind": kind,
            "message": str(message)[:500],
            "action": action,
            "state_index": state_index,
        },
    }
    emit(row)
    raise SystemExit(0)


request = json.loads(sys.stdin.read())
expected_constants = request["constants"]
action_symbols = request["action_symbols"]
states = request["states"]
candidate_path = sys.argv[1]

safe_builtins = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "float": float,
    "frozenset": frozenset,
    "int": int,
    "isinstance": isinstance,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "object": object,
    "range": range,
    "set": set,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "type": type,
    "zip": zip,
    "ArithmeticError": ArithmeticError,
    "AssertionError": AssertionError,
    "Exception": Exception,
    "RuntimeError": RuntimeError,
    "TypeError": TypeError,
    "ValueError": ValueError,
}
namespace = {"__builtins__": safe_builtins, "__name__": "candidate"}

try:
    with open(candidate_path, "r", encoding="utf-8") as handle:
        source = handle.read()
    exec(compile(source, candidate_path, "exec"), namespace, namespace)
except BaseException as exc:
    invalid("module_load", type(exc).__name__ + ": " + str(exc))

for name, expected in expected_constants.items():
    actual = namespace.get(name)
    if type(actual) is not int or actual != expected:
        invalid("constant_contract", name + " does not match the configured value")

initial = namespace.get("INITIAL")
if not valid_state(initial):
    invalid("initial_contract", "INITIAL is not an exact TwoLights state dictionary")

function_type = type(lambda value: value)
for label, symbol in action_symbols.items():
    function = namespace.get(symbol)
    if type(function) is not function_type:
        invalid("api_contract", symbol + " is not a Python function")
    code = function.__code__
    if (
        code.co_argcount != 1
        or code.co_posonlyargcount > 1
        or code.co_kwonlyargcount != 0
        or code.co_flags & 0x0C
    ):
        invalid("api_contract", symbol + " must accept exactly one argument")

actions = namespace.get("ACTIONS")
if type(actions) is not dict or set(actions) != set(action_symbols):
    invalid("api_contract", "ACTIONS must contain exactly the seven TLA+ labels")
for label, symbol in action_symbols.items():
    if actions[label] is not namespace[symbol]:
        invalid("api_contract", "ACTIONS[" + label + "] does not reference " + symbol)

results = {}
for label in action_symbols:
    function = actions[label]
    action_results = []
    for state_index, state in enumerate(states):
        if not valid_state(state):
            invalid("runner_protocol", "host supplied an invalid state", label, state_index)
        first_input = dict(state)
        second_input = dict(state)
        try:
            first = function(first_input)
            second = function(second_input)
        except BaseException as exc:
            invalid(
                "action_exception",
                type(exc).__name__ + ": " + str(exc),
                label,
                state_index,
            )
        if first_input != state or second_input != state:
            invalid("input_mutation", "action mutated its input state", label, state_index)
        if first is not None and not valid_state(first):
            invalid(
                "invalid_successor",
                "action returned a value outside the TwoLights state domain",
                label,
                state_index,
            )
        if second is not None and not valid_state(second):
            invalid(
                "invalid_successor",
                "repeated action returned a value outside the TwoLights state domain",
                label,
                state_index,
            )
        if first != second:
            invalid("nondeterminism", "repeated calls returned different results", label, state_index)
        action_results.append(first)
    results[label] = action_results

emit(
    {
        "protocol": "tla-steer-candidate-observations/0.1",
        "status": "ok",
        "initial": initial,
        "results": results,
    }
)
'''


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _base_result(
    candidate_path: Path,
    candidate_sha256: str | None,
    oracle: dict[str, object] | None,
    timeout_seconds: float,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "candidate_path": str(candidate_path),
        "candidate_sha256": candidate_sha256,
        "containment_mode": CONTAINMENT_MODE,
        "containment_note": CONTAINMENT_NOTE,
        "runner": {
            "python_executable": sys.executable,
            "python_flags": ["-I", "-S"],
            "timeout_seconds": timeout_seconds,
        },
        "oracle": oracle,
        "outcome": EVALUATOR_ERROR,
        "exact": False,
        "initial_exact": None,
        "constant_contract_valid": None,
        "api_contract_valid": None,
        "transition_sound": None,
        "transition_complete": None,
        "rooted_state_exact": None,
        "rooted_reachable_state_count": None,
        "expected_state_action_pairs": EXPECTED_STATE_COUNT * len(ACTION_LABELS),
        "observed_state_action_pairs": 0,
        "expected_transition_count": EXPECTED_TRANSITION_COUNT,
        "candidate_transition_count": None,
        "frame_violations": None,
        "frame_violation_fields": {},
        "runtime_failure": False,
        "contract_failures": [],
        "per_action": {},
        "counterexamples": [],
        "verifier_duration_seconds": None,
    }


def _finish(
    result: dict[str, Any], started: float, outcome: str, *, failure: str | None = None
) -> dict[str, Any]:
    result["outcome"] = outcome
    if failure is not None:
        result["contract_failures"].append(failure)
    result["verifier_duration_seconds"] = time.monotonic() - started
    return result


def _static_contract_failure(source: str) -> str | None:
    try:
        tree = ast.parse(source, filename="candidate.py")
    except SyntaxError as exc:
        return f"syntax_error: {exc.msg} at line {exc.lineno}"
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return f"imports_not_allowed: line {getattr(node, 'lineno', '?')}"
    return None


def _run_candidate(
    candidate_path: Path,
    states: list[dict[str, object]],
    timeout_seconds: float,
) -> tuple[dict[str, Any] | None, str | None, bool]:
    request = json.dumps(
        {
            "constants": CONSTANTS,
            "action_symbols": ACTION_SYMBOLS,
            "states": states,
        },
        separators=(",", ":"),
    )
    with tempfile.TemporaryDirectory(prefix="tla-steer-candidate-") as name:
        scratch = Path(name)
        isolated_candidate = scratch / "candidate.py"
        shutil.copyfile(candidate_path, isolated_candidate)
        try:
            process = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-S",
                    "-c",
                    _CANDIDATE_RUNNER,
                    str(isolated_candidate),
                ],
                cwd=scratch,
                input=request,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return None, f"candidate_timeout: exceeded {timeout_seconds} seconds", True
        except OSError as exc:
            return None, f"candidate_runner_error: {type(exc).__name__}: {exc}", False

    if process.returncode != 0:
        detail = process.stderr.strip()[:500]
        return (
            None,
            f"candidate_process_exit: return code {process.returncode}"
            + (f": {detail}" if detail else ""),
            True,
        )
    try:
        payload = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        return None, f"candidate_protocol_error: invalid JSON: {exc}", False
    if not isinstance(payload, dict):
        return None, "candidate_protocol_error: response is not an object", False
    return payload, None, False


def _counterexample(
    kind: str,
    state: dict[str, object] | None,
    action: str | None,
    expected: object,
    actual: object,
) -> dict[str, object]:
    return {
        "kind": kind,
        "state": state,
        "action": action,
        "expected": expected,
        "actual": actual,
    }


def verify_candidate(
    candidate_path: str | Path,
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Exhaustively grade one candidate against the fixed TwoLights oracle.

    The returned dictionary is directly JSON serializable.  Oracle failure is
    reported as ``EVALUATOR_ERROR``; candidate contract/runtime failures are
    reported as ``INVALID_CANDIDATE``; valid but unequal relations are
    ``SEMANTIC_MISMATCH``.
    """

    started = time.monotonic()
    path = Path(candidate_path).expanduser().absolute()
    oracle_summary: dict[str, object] | None = None
    try:
        oracle_summary = self_check().as_dict()
    except (OracleError, Exception) as exc:
        result = _base_result(path, None, None, timeout_seconds)
        return _finish(
            result,
            started,
            EVALUATOR_ERROR,
            failure=f"oracle_self_check: {type(exc).__name__}: {exc}",
        )

    candidate_digest: str | None = None
    result = _base_result(path, candidate_digest, oracle_summary, timeout_seconds)
    if timeout_seconds <= 0:
        return _finish(
            result,
            started,
            EVALUATOR_ERROR,
            failure="invalid verifier timeout",
        )
    if path.is_symlink() or not path.is_file():
        result["api_contract_valid"] = False
        return _finish(
            result,
            started,
            INVALID_CANDIDATE,
            failure="candidate_path must be a regular non-symlink file",
        )

    try:
        candidate_digest = _sha256(path)
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        result["api_contract_valid"] = False
        return _finish(
            result,
            started,
            INVALID_CANDIDATE,
            failure=f"candidate_read: {type(exc).__name__}: {exc}",
        )
    result["candidate_sha256"] = candidate_digest

    static_failure = _static_contract_failure(source)
    if static_failure is not None:
        result["api_contract_valid"] = False
        return _finish(
            result, started, INVALID_CANDIDATE, failure=static_failure
        )

    states = list(iter_type_correct_states())
    payload, runner_failure, candidate_runtime_failure = _run_candidate(
        path, states, timeout_seconds
    )
    if runner_failure is not None:
        result["runtime_failure"] = candidate_runtime_failure
        return _finish(
            result,
            started,
            INVALID_CANDIDATE if candidate_runtime_failure else EVALUATOR_ERROR,
            failure=runner_failure,
        )
    assert payload is not None
    if payload.get("protocol") != "tla-steer-candidate-observations/0.1":
        return _finish(
            result,
            started,
            EVALUATOR_ERROR,
            failure="candidate_protocol_error: unsupported or missing protocol",
        )
    if payload.get("status") == "invalid_candidate":
        failure = payload.get("failure")
        if not isinstance(failure, dict):
            return _finish(
                result,
                started,
                EVALUATOR_ERROR,
                failure="candidate_protocol_error: malformed failure record",
            )
        kind = str(failure.get("kind", "candidate_failure"))
        message = str(failure.get("message", ""))
        action = failure.get("action")
        state_index = failure.get("state_index")
        detail = f"{kind}: {message}"
        if action is not None:
            detail += f"; action={action}"
        if state_index is not None:
            detail += f"; state_index={state_index}"
        result["runtime_failure"] = kind in {
            "module_load",
            "action_exception",
            "input_mutation",
            "invalid_successor",
            "nondeterminism",
        }
        result["constant_contract_valid"] = kind != "constant_contract"
        result["api_contract_valid"] = kind not in {
            "constant_contract",
            "initial_contract",
            "api_contract",
        }
        if isinstance(state_index, int) and 0 <= state_index < len(states):
            result["counterexamples"].append(
                _counterexample(kind, states[state_index], str(action), None, message)
            )
        return _finish(
            result, started, INVALID_CANDIDATE, failure=detail
        )
    if payload.get("status") != "ok":
        return _finish(
            result,
            started,
            EVALUATOR_ERROR,
            failure="candidate_protocol_error: unrecognized status",
        )

    candidate_initial = payload.get("initial")
    observations = payload.get("results")
    if not is_type_correct_state(candidate_initial) or not isinstance(observations, dict):
        return _finish(
            result,
            started,
            EVALUATOR_ERROR,
            failure="candidate_protocol_error: malformed successful response",
        )
    if set(observations) != set(ACTION_LABELS) or any(
        not isinstance(observations[label], list)
        or len(observations[label]) != len(states)
        for label in ACTION_LABELS
    ):
        return _finish(
            result,
            started,
            EVALUATOR_ERROR,
            failure="candidate_protocol_error: incomplete observation matrix",
        )

    result["constant_contract_valid"] = True
    result["api_contract_valid"] = True
    result["initial_exact"] = candidate_initial == INITIAL
    result["observed_state_action_pairs"] = len(states) * len(ACTION_LABELS)
    if not result["initial_exact"]:
        result["counterexamples"].append(
            _counterexample("initial_mismatch", None, None, INITIAL, candidate_initial)
        )

    total_false_positive = 0
    total_false_negative = 0
    total_wrong_successor = 0
    total_candidate_transitions = 0
    total_frame_violations = 0
    frame_fields: dict[str, int] = {}

    for label in ACTION_LABELS:
        metrics = {
            "expected_enabled": 0,
            "candidate_enabled": 0,
            "exact_successors": 0,
            "false_positive": 0,
            "false_negative": 0,
            "wrong_successor": 0,
            "frame_violations": 0,
        }
        action_results = observations[label]
        for index, state in enumerate(states):
            expected = oracle_successor(label, state)
            actual = action_results[index]
            if actual is not None and not is_type_correct_state(actual):
                return _finish(
                    result,
                    started,
                    EVALUATOR_ERROR,
                    failure="candidate_protocol_error: invalid successor escaped child validation",
                )
            if expected is not None:
                metrics["expected_enabled"] += 1
            if actual is not None:
                metrics["candidate_enabled"] += 1
                total_candidate_transitions += 1

            mismatch_kind: str | None = None
            if expected is None and actual is not None:
                metrics["false_positive"] += 1
                total_false_positive += 1
                mismatch_kind = "false_positive"
            elif expected is not None and actual is None:
                metrics["false_negative"] += 1
                total_false_negative += 1
                mismatch_kind = "false_negative"
            elif expected is not None and actual != expected:
                metrics["wrong_successor"] += 1
                total_wrong_successor += 1
                mismatch_kind = "wrong_successor"
            elif expected is not None:
                metrics["exact_successors"] += 1

            if mismatch_kind and len(result["counterexamples"]) < MAX_COUNTEREXAMPLES:
                result["counterexamples"].append(
                    _counterexample(mismatch_kind, state, label, expected, actual)
                )

            if actual is not None:
                changed_preserved = [
                    field
                    for field in PRESERVED_FIELDS[label]
                    if actual[field] != state[field]
                ]
                if changed_preserved:
                    metrics["frame_violations"] += 1
                    total_frame_violations += 1
                    for field in changed_preserved:
                        frame_fields[field] = frame_fields.get(field, 0) + 1

        result["per_action"][label] = metrics

    all_state_keys = {state_key(state) for state in states}
    state_indexes = {state_key(state): index for index, state in enumerate(states)}
    start_key = state_key(candidate_initial)
    reachable = {start_key}
    pending = deque([start_key])
    while pending:
        current_key = pending.popleft()
        index = state_indexes[current_key]
        for label in ACTION_LABELS:
            successor = observations[label][index]
            if successor is None:
                continue
            successor_key = state_key(successor)
            if successor_key not in reachable:
                reachable.add(successor_key)
                pending.append(successor_key)

    result["candidate_transition_count"] = total_candidate_transitions
    result["frame_violations"] = total_frame_violations
    result["frame_violation_fields"] = frame_fields
    result["transition_sound"] = (
        total_false_positive == 0 and total_wrong_successor == 0
    )
    result["transition_complete"] = (
        total_false_negative == 0 and total_wrong_successor == 0
    )
    result["rooted_reachable_state_count"] = len(reachable)
    result["rooted_state_exact"] = reachable == all_state_keys
    result["exact"] = bool(
        result["initial_exact"]
        and result["transition_sound"]
        and result["transition_complete"]
        and result["rooted_state_exact"]
    )

    return _finish(
        result, started, EXACT if result["exact"] else SEMANTIC_MISMATCH
    )
