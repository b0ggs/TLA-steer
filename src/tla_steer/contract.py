"""Fixed declarative contracts for the TwoLights prototype.

The Planner produces data, not executable controller code.  This module keeps
the accepted data surface deliberately small and performs the semantic checks
that JSON Schema cannot express (complete target coverage, target/symbol
matching, and balanced action probes).
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping


CONTROLLER_SCHEMA_VERSION = "tla-steer-controller/0.1"
PROPOSAL_SCHEMA_VERSION = "tla-steer-proposal/0.1"
MAX_PROBES_PER_ACTION = 16

STATE_KEYS = ("clock", "lightA", "timerA", "lightB", "timerB")
COLORS = frozenset(("red", "green", "yellow"))

# Insertion order is the canonical presentation order.  The Planner may choose
# a different execution order, but it must cover this exact set once.
TARGET_SPECS: dict[str, tuple[str, str]] = {
    "INITIAL": ("initial", "INITIAL"),
    "Tick": ("action", "tick"),
    "AGreenToYellow": ("action", "a_green_to_yellow"),
    "AYellowToRed": ("action", "a_yellow_to_red"),
    "ARedToGreen": ("action", "a_red_to_green"),
    "BGreenToYellow": ("action", "b_green_to_yellow"),
    "BYellowToRed": ("action", "b_yellow_to_red"),
    "BRedToGreen": ("action", "b_red_to_green"),
}
SEMANTIC_TARGETS = tuple(TARGET_SPECS)

_STEP_ID = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


class ContractError(ValueError):
    """A Planner or Follower document violates the frozen prototype contract."""


@dataclass(frozen=True, slots=True)
class State:
    clock: int
    lightA: str
    timerA: int
    lightB: str
    timerB: int

    def as_dict(self) -> dict[str, int | str]:
        return {
            "clock": self.clock,
            "lightA": self.lightA,
            "timerA": self.timerA,
            "lightB": self.lightB,
            "timerB": self.timerB,
        }


@dataclass(frozen=True, slots=True)
class Probe:
    state: State
    expected_successor: State | None

    @property
    def expected_enabled(self) -> bool:
        return self.expected_successor is not None

    def as_dict(self, *, include_expected: bool = True) -> dict[str, object]:
        result: dict[str, object] = {"state": self.state.as_dict()}
        if include_expected:
            result["expected_successor"] = (
                None
                if self.expected_successor is None
                else self.expected_successor.as_dict()
            )
        return result


@dataclass(frozen=True, slots=True)
class ControllerStep:
    id: str
    kind: str
    target: str
    python_symbol: str
    proposal_instruction: str
    expected_initial: State | None = None
    probes: tuple[Probe, ...] = ()

    def follower_view(self) -> dict[str, object]:
        """Return the step data a Follower may see, excluding expected answers."""

        result: dict[str, object] = {
            "id": self.id,
            "kind": self.kind,
            "target": self.target,
            "python_symbol": self.python_symbol,
            "proposal_instruction": self.proposal_instruction,
        }
        if self.kind == "action":
            result["probe_states"] = [probe.state.as_dict() for probe in self.probes]
        return result

    def as_dict(self) -> dict[str, object]:
        result = self.follower_view()
        result.pop("probe_states", None)
        if self.kind == "initial":
            assert self.expected_initial is not None
            result["expected_initial"] = self.expected_initial.as_dict()
        else:
            result["probes"] = [probe.as_dict() for probe in self.probes]
        return result


@dataclass(frozen=True, slots=True)
class Controller:
    schema_version: str
    steps: tuple[ControllerStep, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "steps": [step.as_dict() for step in self.steps],
        }


@dataclass(frozen=True, slots=True)
class Proposal:
    schema_version: str
    step_id: str
    python_fragment: str

    def as_dict(self) -> dict[str, str]:
        return {
            "schema_version": self.schema_version,
            "step_id": self.step_id,
            "python_fragment": self.python_fragment,
        }


def _object(value: object, location: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ContractError(f"{location} must be an object")
    if not all(isinstance(key, str) for key in value):
        raise ContractError(f"{location} keys must be strings")
    return value


def _exact_keys(
    value: Mapping[str, object], required: set[str], location: str
) -> None:
    actual = set(value)
    missing = sorted(required - actual)
    unknown = sorted(actual - required)
    if missing:
        raise ContractError(f"{location} missing keys: {', '.join(missing)}")
    if unknown:
        raise ContractError(f"{location} unknown keys: {', '.join(unknown)}")


def _integer(value: object, location: str, minimum: int, maximum: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ContractError(f"{location} must be an integer")
    if not minimum <= value <= maximum:
        raise ContractError(f"{location} must be in {minimum}..{maximum}")
    return value


def validate_state(value: object, *, location: str = "state") -> State:
    source = _object(value, location)
    _exact_keys(source, set(STATE_KEYS), location)

    light_a = source["lightA"]
    light_b = source["lightB"]
    if not isinstance(light_a, str) or light_a not in COLORS:
        raise ContractError(f"{location}.lightA must be a TwoLights color")
    if not isinstance(light_b, str) or light_b not in COLORS:
        raise ContractError(f"{location}.lightB must be a TwoLights color")

    return State(
        clock=_integer(source["clock"], f"{location}.clock", 0, 7),
        lightA=light_a,
        timerA=_integer(source["timerA"], f"{location}.timerA", 0, 6),
        lightB=light_b,
        timerB=_integer(source["timerB"], f"{location}.timerB", 0, 6),
    )


def _text(value: object, location: str, *, maximum: int) -> str:
    if not isinstance(value, str):
        raise ContractError(f"{location} must be a string")
    if not value.strip():
        raise ContractError(f"{location} must not be blank")
    if len(value) > maximum:
        raise ContractError(f"{location} exceeds {maximum} characters")
    return value


def _validate_step(value: object, index: int) -> ControllerStep:
    location = f"controller.steps[{index}]"
    source = _object(value, location)
    common = {
        "id",
        "kind",
        "target",
        "python_symbol",
        "proposal_instruction",
    }
    kind = source.get("kind")
    if kind == "initial":
        _exact_keys(source, common | {"expected_initial"}, location)
    elif kind == "action":
        _exact_keys(source, common | {"probes"}, location)
    else:
        raise ContractError(f"{location}.kind must be initial or action")

    step_id = _text(source["id"], f"{location}.id", maximum=64)
    if not _STEP_ID.fullmatch(step_id):
        raise ContractError(f"{location}.id is not a valid step identifier")
    target = _text(source["target"], f"{location}.target", maximum=64)
    if target not in TARGET_SPECS:
        raise ContractError(f"{location}.target is not a required TwoLights target")
    expected_kind, expected_symbol = TARGET_SPECS[target]
    if kind != expected_kind:
        raise ContractError(f"{location}.kind does not match target {target}")
    python_symbol = _text(
        source["python_symbol"], f"{location}.python_symbol", maximum=64
    )
    if python_symbol != expected_symbol:
        raise ContractError(
            f"{location}.python_symbol must be {expected_symbol} for {target}"
        )
    instruction = _text(
        source["proposal_instruction"],
        f"{location}.proposal_instruction",
        maximum=4000,
    )

    if kind == "initial":
        return ControllerStep(
            id=step_id,
            kind=kind,
            target=target,
            python_symbol=python_symbol,
            proposal_instruction=instruction,
            expected_initial=validate_state(
                source["expected_initial"],
                location=f"{location}.expected_initial",
            ),
        )

    raw_probes = source["probes"]
    if not isinstance(raw_probes, list):
        raise ContractError(f"{location}.probes must be an array")
    if not 2 <= len(raw_probes) <= MAX_PROBES_PER_ACTION:
        raise ContractError(
            f"{location}.probes must contain 2..{MAX_PROBES_PER_ACTION} probes"
        )
    probes: list[Probe] = []
    seen_states: set[State] = set()
    for probe_index, raw_probe in enumerate(raw_probes):
        probe_location = f"{location}.probes[{probe_index}]"
        probe_source = _object(raw_probe, probe_location)
        _exact_keys(
            probe_source, {"state", "expected_successor"}, probe_location
        )
        state = validate_state(
            probe_source["state"], location=f"{probe_location}.state"
        )
        if state in seen_states:
            raise ContractError(f"{location}.probes contains a duplicate state")
        seen_states.add(state)
        raw_successor = probe_source["expected_successor"]
        successor = (
            None
            if raw_successor is None
            else validate_state(
                raw_successor,
                location=f"{probe_location}.expected_successor",
            )
        )
        probes.append(Probe(state=state, expected_successor=successor))
    if not any(probe.expected_enabled for probe in probes):
        raise ContractError(f"{location}.probes needs an expected-enabled case")
    if not any(not probe.expected_enabled for probe in probes):
        raise ContractError(f"{location}.probes needs an expected-disabled case")

    return ControllerStep(
        id=step_id,
        kind=kind,
        target=target,
        python_symbol=python_symbol,
        proposal_instruction=instruction,
        probes=tuple(probes),
    )


def validate_controller(value: object) -> Controller:
    """Validate and freeze one Planner-produced controller object."""

    if isinstance(value, Controller):
        # Round-tripping also protects callers from constructing an invalid
        # dataclass directly.
        value = value.as_dict()
    source = _object(value, "controller")
    _exact_keys(source, {"schema_version", "steps"}, "controller")
    if source["schema_version"] != CONTROLLER_SCHEMA_VERSION:
        raise ContractError("controller.schema_version is unsupported")
    raw_steps = source["steps"]
    if not isinstance(raw_steps, list) or len(raw_steps) != len(TARGET_SPECS):
        raise ContractError("controller.steps must contain exactly eight steps")
    steps = tuple(_validate_step(value, index) for index, value in enumerate(raw_steps))
    step_ids = [step.id for step in steps]
    if len(set(step_ids)) != len(step_ids):
        raise ContractError("controller step IDs must be unique")
    targets = [step.target for step in steps]
    if len(set(targets)) != len(targets) or set(targets) != set(TARGET_SPECS):
        raise ContractError("controller must cover every semantic target exactly once")
    return Controller(schema_version=CONTROLLER_SCHEMA_VERSION, steps=steps)


class _DuplicateKey(ValueError):
    pass


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey(key)
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _parse_json(document: str | bytes, location: str) -> object:
    try:
        return json.loads(
            document,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (_DuplicateKey, json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        raise ContractError(f"{location} is not strict JSON: {exc}") from exc


def controller_from_json(document: str | bytes) -> Controller:
    return validate_controller(_parse_json(document, "controller"))


def validate_fragment(proposal: Proposal, step: ControllerStep) -> None:
    """Check the one-fragment shape without executing generated Python."""

    try:
        module = ast.parse(proposal.python_fragment, mode="exec")
    except (SyntaxError, ValueError) as exc:
        raise ContractError(f"proposal fragment is invalid Python: {exc}") from exc
    if len(module.body) != 1:
        raise ContractError("proposal must contain exactly one top-level statement")
    root = module.body[0]

    if step.kind == "initial":
        if not isinstance(root, ast.Assign) or len(root.targets) != 1:
            raise ContractError("INITIAL proposal must be exactly one assignment")
        target = root.targets[0]
        if not isinstance(target, ast.Name) or target.id != "INITIAL":
            raise ContractError("INITIAL proposal must assign INITIAL")
        try:
            literal = ast.literal_eval(root.value)
        except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError) as exc:
            raise ContractError("INITIAL value must be a literal state dictionary") from exc
        validate_state(literal, location="proposal.INITIAL")
        return

    if not isinstance(root, ast.FunctionDef):
        raise ContractError("action proposal must be exactly one function definition")
    if root.name != step.python_symbol:
        raise ContractError(
            f"action proposal must define {step.python_symbol}, not {root.name}"
        )
    if root.decorator_list:
        raise ContractError("action proposal must not use decorators")
    arguments = root.args
    if (
        len(arguments.posonlyargs) + len(arguments.args) != 1
        or arguments.kwonlyargs
        or arguments.vararg is not None
        or arguments.kwarg is not None
        or arguments.defaults
        or arguments.kw_defaults
    ):
        raise ContractError("action function must accept exactly one state argument")
    validate_guard_update_function(root)
    argument = (arguments.posonlyargs + arguments.args)[0]
    if argument.arg != "state":
        raise ContractError("action function argument must be named state")
    for node in ast.walk(root):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.ClassDef, ast.AsyncFunctionDef)):
            raise ContractError("proposal contains a forbidden definition or import")
        if isinstance(node, ast.FunctionDef) and node is not root:
            raise ContractError("proposal contains a nested function definition")


def validate_proposal(
    value: object, *, step: ControllerStep | None = None
) -> Proposal:
    """Validate one Follower result and optionally bind it to its current step."""

    if isinstance(value, Proposal):
        source: Mapping[str, object] = value.as_dict()
    else:
        source = _object(value, "proposal")
    _exact_keys(
        source,
        {"schema_version", "step_id", "python_fragment"},
        "proposal",
    )
    if source["schema_version"] != PROPOSAL_SCHEMA_VERSION:
        raise ContractError("proposal.schema_version is unsupported")
    step_id = _text(source["step_id"], "proposal.step_id", maximum=64)
    if not _STEP_ID.fullmatch(step_id):
        raise ContractError("proposal.step_id is not a valid step identifier")
    fragment = _text(
        source["python_fragment"], "proposal.python_fragment", maximum=16000
    )
    proposal = Proposal(
        schema_version=PROPOSAL_SCHEMA_VERSION,
        step_id=step_id,
        python_fragment=fragment,
    )
    if step is not None:
        if proposal.step_id != step.id:
            raise ContractError(
                f"proposal step {proposal.step_id} does not match current step {step.id}"
            )
        validate_fragment(proposal, step)
    return proposal


def proposal_from_json(
    document: str | bytes, *, step: ControllerStep | None = None
) -> Proposal:
    return validate_proposal(_parse_json(document, "proposal"), step=step)


def initial_state_from_fragment(proposal: Proposal, step: ControllerStep) -> State:
    """Extract the already-validated literal INITIAL state for scoring."""

    validate_fragment(proposal, step)
    root = ast.parse(proposal.python_fragment, mode="exec").body[0]
    assert isinstance(root, ast.Assign)
    return validate_state(ast.literal_eval(root.value), location="proposal.INITIAL")


# A documented conformance subset for this one guard/update task. This is not
# a Python purity proof or a hostile-code security boundary.
_CONSTANT_NAMES = frozenset({"CYCLE_LENGTH", "MIN_GREEN", "MIN_YELLOW", "MIN_RED", "MAX_PHASE", "OFFSET"})
_PURE_CALLS = frozenset({"dict", "abs", "min", "max", "int", "bool"})
_READ_METHODS = frozenset({"copy", "get"})
_WRITE_METHODS = frozenset({"update", "pop", "setdefault"})


def _annotation(node: ast.expr | None) -> None:
    if node is None or isinstance(node, ast.Constant) and node.value is None:
        return
    if isinstance(node, ast.Name) and node.id in {"dict", "int", "str", "bool"}:
        return
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        _annotation(node.left)
        _annotation(node.right)
        return
    raise ContractError("executable or unsupported annotation")


def validate_guard_update_function(function: ast.FunctionDef) -> None:
    """Accept local guard/update code; reject persistent state and input aliases."""

    args = function.args
    positional = args.posonlyargs + args.args
    if (function.decorator_list or len(positional) != 1 or args.defaults or args.kw_defaults
            or args.kwonlyargs or args.vararg or args.kwarg or function.type_params):
        raise ContractError("action must have one argument, no defaults, decorators or type parameters")
    argument = positional[0].arg
    _annotation(positional[0].annotation)
    _annotation(function.returns)

    def expression(node: ast.expr, locals_: set[str], copies: set[str]) -> None:
        if isinstance(node, ast.Constant) and type(node.value) in {int, float, str, bool, type(None)}:
            return
        if isinstance(node, ast.Name) and node.id in locals_ | _CONSTANT_NAMES:
            return
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if key is None:
                    raise ContractError("dictionary unpacking is outside the guard/update contract")
                expression(key, locals_, copies)
                expression(value, locals_, copies)
            return
        if isinstance(node, ast.Subscript):
            expression(node.value, locals_, copies)
            expression(node.slice, locals_, copies)
            return
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Mod, ast.FloorDiv)):
            expression(node.left, locals_, copies)
            expression(node.right, locals_, copies)
            return
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.Not, ast.USub, ast.UAdd)):
            expression(node.operand, locals_, copies)
            return
        if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
            for value in node.values:
                expression(value, locals_, copies)
            return
        if isinstance(node, ast.Compare) and all(isinstance(op, (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Is, ast.IsNot)) for op in node.ops):
            for value in [node.left, *node.comparators]:
                expression(value, locals_, copies)
            return
        if isinstance(node, ast.IfExp):
            for value in (node.test, node.body, node.orelse):
                expression(value, locals_, copies)
            return
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id not in _PURE_CALLS or node.func.id in locals_:
                    raise ContractError("arbitrary calls are outside the guard/update contract")
            elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                receiver = node.func.value.id
                if receiver not in locals_ or node.func.attr not in _READ_METHODS | _WRITE_METHODS:
                    raise ContractError("attribute/reflection access is outside the guard/update contract")
                if node.func.attr in _WRITE_METHODS and receiver not in copies:
                    raise ContractError("input_mutation_contract: method may mutate input or its alias")
            else:
                raise ContractError("arbitrary calls are outside the guard/update contract")
            for value in node.args:
                expression(value, locals_, copies)
            for keyword in node.keywords:
                if keyword.arg is None:
                    raise ContractError("keyword unpacking is outside the guard/update contract")
                expression(keyword.value, locals_, copies)
            return
        raise ContractError(f"forbidden {type(node).__name__} is outside the guard/update contract")

    def is_copy(node: ast.expr, copies: set[str]) -> bool:
        return (isinstance(node, ast.Dict)
                or isinstance(node, ast.Name) and node.id in copies
                or isinstance(node, ast.Call) and (
                    isinstance(node.func, ast.Name) and node.func.id == "dict"
                    or isinstance(node.func, ast.Attribute) and node.func.attr == "copy"))

    def statements(nodes: list[ast.stmt], locals_: set[str], copies: set[str]) -> tuple[set[str], set[str]]:
        locals_, copies = set(locals_), set(copies)
        for node in nodes:
            if isinstance(node, ast.Return):
                if node.value is not None:
                    expression(node.value, locals_, copies)
            elif isinstance(node, ast.If):
                expression(node.test, locals_, copies)
                left_names, left_copies = statements(node.body, locals_, copies)
                right_names, right_copies = statements(node.orelse, locals_, copies)
                locals_ |= left_names & right_names
                copies = left_copies & right_copies
            elif isinstance(node, (ast.Assign, ast.AugAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if len(targets) != 1:
                    raise ContractError("chained assignment is outside the guard/update contract")
                expression(node.value, locals_, copies)
                if isinstance(node, ast.AugAssign) and not isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Mod, ast.FloorDiv)):
                    raise ContractError("unsupported augmented assignment")
                target = targets[0]
                if isinstance(target, ast.Name):
                    if target.id == argument or target.id in _CONSTANT_NAMES | _PURE_CALLS:
                        raise ContractError("cannot rebind input, constants or allowed builtins")
                    if isinstance(node, ast.AugAssign):
                        expression(target, locals_, copies)
                        if not isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Mod, ast.FloorDiv)):
                            raise ContractError("unsupported augmented assignment")
                    copy = isinstance(node, ast.Assign) and is_copy(node.value, copies)
                    locals_.add(target.id)
                    copies.discard(target.id)
                    if copy:
                        copies.add(target.id)
                elif isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
                    if target.value.id not in copies:
                        raise ContractError("input_mutation_contract: subscript may mutate input or its alias")
                    expression(target.slice, locals_, copies)
                else:
                    raise ContractError("assignment target is outside the guard/update contract")
            elif isinstance(node, ast.Expr) and isinstance(node.value, (ast.Constant, ast.Call)):
                expression(node.value, locals_, copies)
            else:
                raise ContractError(f"forbidden {type(node).__name__} is outside the guard/update contract")
        return locals_, copies

    statements(function.body, {argument}, set())


def validate_guard_update_source(source: str, *, complete: bool) -> None:
    """Validate module shape before either partial or final execution."""

    if len(source.encode("utf-8")) > 128 * 1024:
        raise ContractError("candidate exceeds the fixed source size limit")
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, RecursionError) as exc:
        raise ContractError(f"invalid candidate syntax: {exc}") from exc
    seen = set()
    functions = {symbol for kind, symbol in TARGET_SPECS.values() if kind == "action"}
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and type(node.value.value) is str:
            continue
        if isinstance(node, ast.FunctionDef) and node.name in functions:
            name = node.name
            validate_guard_update_function(node)
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in _CONSTANT_NAMES:
                if not isinstance(node.value, ast.Constant) or type(node.value.value) is not int:
                    raise ContractError("constants must be integer literals")
            elif name == "INITIAL":
                if not isinstance(node.value, ast.Dict):
                    raise ContractError("INITIAL must be a literal state dictionary")
                for value in [*node.value.keys, *node.value.values]:
                    if not (isinstance(value, ast.Constant) and type(value.value) in {int, str}
                            or isinstance(value, ast.Name) and value.id in _CONSTANT_NAMES):
                        raise ContractError("INITIAL may contain only literals and configured constants")
            elif name == "ACTIONS":
                if not isinstance(node.value, ast.Dict) or any(
                    not isinstance(key, ast.Constant) or type(key.value) is not str
                    or not isinstance(value, ast.Name) or value.id not in functions
                    for key, value in zip(node.value.keys, node.value.values)
                ):
                    raise ContractError("ACTIONS must be a literal label-to-function mapping")
            else:
                raise ContractError("extra module state is outside the guard/update contract")
        else:
            raise ContractError("module statement is outside the guard/update contract")
        if name in seen:
            raise ContractError(f"duplicate definition: {name}")
        seen.add(name)
    required = _CONSTANT_NAMES | {"INITIAL"} | (functions | {"ACTIONS"} if complete else set())
    if not required <= seen:
        raise ContractError("candidate is missing required definitions")
