"""Trusted executable oracle for the one frozen ``TwoLights.cfg`` instance.

This module is intentionally not a TLA+ parser.  It is a hand-derived relation
for the hackathon fixture, with an exhaustive self-check against the state and
edge counts recorded for that fixture.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterator


CYCLE_LENGTH = 8
MIN_GREEN = 3
MIN_YELLOW = 1
MIN_RED = 4
MAX_PHASE = 6
OFFSET = 2

CONSTANTS = {
    "CYCLE_LENGTH": CYCLE_LENGTH,
    "MIN_GREEN": MIN_GREEN,
    "MIN_YELLOW": MIN_YELLOW,
    "MIN_RED": MIN_RED,
    "MAX_PHASE": MAX_PHASE,
    "OFFSET": OFFSET,
}

STATE_KEYS = ("clock", "lightA", "timerA", "lightB", "timerB")
COLORS = ("red", "green", "yellow")

ACTION_LABELS = (
    "Tick",
    "AGreenToYellow",
    "AYellowToRed",
    "ARedToGreen",
    "BGreenToYellow",
    "BYellowToRed",
    "BRedToGreen",
)

ACTION_SYMBOLS = {
    "Tick": "tick",
    "AGreenToYellow": "a_green_to_yellow",
    "AYellowToRed": "a_yellow_to_red",
    "ARedToGreen": "a_red_to_green",
    "BGreenToYellow": "b_green_to_yellow",
    "BYellowToRed": "b_yellow_to_red",
    "BRedToGreen": "b_red_to_green",
}

EXPECTED_STATE_COUNT = 3_528
EXPECTED_TRANSITION_COUNT = 6_960
EXPECTED_ACTION_COUNTS = {
    "Tick": 2_592,
    "AGreenToYellow": 672,
    "AYellowToRed": 1_008,
    "ARedToGreen": 504,
    "BGreenToYellow": 672,
    "BYellowToRed": 1_008,
    "BRedToGreen": 504,
}

INITIAL = {
    "clock": 0,
    "lightA": "green",
    "timerA": 0,
    "lightB": "red",
    "timerB": OFFSET,
}

State = dict[str, object]
StateKey = tuple[int, str, int, str, int]


class OracleError(RuntimeError):
    """The fixed oracle failed one of its own consistency checks."""


@dataclass(frozen=True)
class OracleSummary:
    state_count: int
    transition_count: int
    reachable_state_count: int
    action_counts: tuple[tuple[str, int], ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "state_count": self.state_count,
            "transition_count": self.transition_count,
            "reachable_state_count": self.reachable_state_count,
            "all_type_correct_states_reachable": (
                self.reachable_state_count == self.state_count
            ),
            "action_counts": dict(self.action_counts),
        }


def initial_state() -> State:
    """Return a fresh copy of the configured initial state."""

    return dict(INITIAL)


def is_type_correct_state(value: object) -> bool:
    """Return whether ``value`` is exactly a state in the configured domain."""

    if type(value) is not dict or set(value) != set(STATE_KEYS):
        return False
    state = value
    return (
        type(state["clock"]) is int
        and 0 <= state["clock"] < CYCLE_LENGTH
        and type(state["lightA"]) is str
        and state["lightA"] in COLORS
        and type(state["timerA"]) is int
        and 0 <= state["timerA"] <= MAX_PHASE
        and type(state["lightB"]) is str
        and state["lightB"] in COLORS
        and type(state["timerB"]) is int
        and 0 <= state["timerB"] <= MAX_PHASE
    )


def state_key(state: State) -> StateKey:
    """Convert a validated state dictionary to its canonical hashable key."""

    if not is_type_correct_state(state):
        raise ValueError("state is outside the configured TwoLights domain")
    return (
        state["clock"],
        state["lightA"],
        state["timerA"],
        state["lightB"],
        state["timerB"],
    )


def state_from_key(key: StateKey) -> State:
    """Convert a canonical key back to a fresh state dictionary."""

    return dict(zip(STATE_KEYS, key))


def iter_type_correct_states() -> Iterator[State]:
    """Yield every state in the finite configured domain in stable order."""

    for clock in range(CYCLE_LENGTH):
        for light_a in COLORS:
            for timer_a in range(MAX_PHASE + 1):
                for light_b in COLORS:
                    for timer_b in range(MAX_PHASE + 1):
                        yield {
                            "clock": clock,
                            "lightA": light_a,
                            "timerA": timer_a,
                            "lightB": light_b,
                            "timerB": timer_b,
                        }


def tick(state: State) -> State | None:
    if state["timerA"] >= MAX_PHASE or state["timerB"] >= MAX_PHASE:
        return None
    successor = dict(state)
    successor["clock"] = (state["clock"] + 1) % CYCLE_LENGTH
    successor["timerA"] = state["timerA"] + 1
    successor["timerB"] = state["timerB"] + 1
    return successor


def a_green_to_yellow(state: State) -> State | None:
    if state["lightA"] != "green" or state["timerA"] < MIN_GREEN:
        return None
    successor = dict(state)
    successor["lightA"] = "yellow"
    successor["timerA"] = 0
    return successor


def a_yellow_to_red(state: State) -> State | None:
    if state["lightA"] != "yellow" or state["timerA"] < MIN_YELLOW:
        return None
    successor = dict(state)
    successor["lightA"] = "red"
    successor["timerA"] = 0
    return successor


def a_red_to_green(state: State) -> State | None:
    if state["lightA"] != "red" or state["timerA"] < MIN_RED:
        return None
    successor = dict(state)
    successor["lightA"] = "green"
    successor["timerA"] = 0
    return successor


def b_green_to_yellow(state: State) -> State | None:
    if state["lightB"] != "green" or state["timerB"] < MIN_GREEN:
        return None
    successor = dict(state)
    successor["lightB"] = "yellow"
    successor["timerB"] = 0
    return successor


def b_yellow_to_red(state: State) -> State | None:
    if state["lightB"] != "yellow" or state["timerB"] < MIN_YELLOW:
        return None
    successor = dict(state)
    successor["lightB"] = "red"
    successor["timerB"] = 0
    return successor


def b_red_to_green(state: State) -> State | None:
    if state["lightB"] != "red" or state["timerB"] < MIN_RED:
        return None
    successor = dict(state)
    successor["lightB"] = "green"
    successor["timerB"] = 0
    return successor


ORACLE_ACTIONS = {
    "Tick": tick,
    "AGreenToYellow": a_green_to_yellow,
    "AYellowToRed": a_yellow_to_red,
    "ARedToGreen": a_red_to_green,
    "BGreenToYellow": b_green_to_yellow,
    "BYellowToRed": b_yellow_to_red,
    "BRedToGreen": b_red_to_green,
}


def oracle_successor(label: str, state: State) -> State | None:
    """Evaluate one labeled oracle action on a fresh copy of ``state``."""

    if label not in ORACLE_ACTIONS:
        raise KeyError(f"unknown TwoLights action: {label}")
    if not is_type_correct_state(state):
        raise ValueError("state is outside the configured TwoLights domain")
    return ORACLE_ACTIONS[label](dict(state))


@lru_cache(maxsize=1)
def self_check() -> OracleSummary:
    """Exhaustively establish the fixed oracle's expected finite graph facts."""

    states = tuple(iter_type_correct_states())
    if len(states) != EXPECTED_STATE_COUNT:
        raise OracleError(
            f"state count mismatch: expected {EXPECTED_STATE_COUNT}, got {len(states)}"
        )

    all_keys = {state_key(state) for state in states}
    if len(all_keys) != EXPECTED_STATE_COUNT:
        raise OracleError("state enumeration contains duplicate canonical states")

    counts = {label: 0 for label in ACTION_LABELS}
    for state in states:
        for label in ACTION_LABELS:
            before = dict(state)
            successor = oracle_successor(label, state)
            if state != before:
                raise OracleError(f"oracle action {label} mutated its input")
            if successor is None:
                continue
            if not is_type_correct_state(successor):
                raise OracleError(
                    f"oracle action {label} produced an out-of-domain successor"
                )
            counts[label] += 1

    if counts != EXPECTED_ACTION_COUNTS:
        raise OracleError(
            f"labeled transition counts mismatch: expected "
            f"{EXPECTED_ACTION_COUNTS}, got {counts}"
        )
    transition_count = sum(counts.values())
    if transition_count != EXPECTED_TRANSITION_COUNT:
        raise OracleError(
            f"transition count mismatch: expected {EXPECTED_TRANSITION_COUNT}, "
            f"got {transition_count}"
        )

    start = state_key(initial_state())
    reachable = {start}
    pending = deque([start])
    while pending:
        current = state_from_key(pending.popleft())
        for label in ACTION_LABELS:
            successor = oracle_successor(label, current)
            if successor is None:
                continue
            key = state_key(successor)
            if key not in reachable:
                reachable.add(key)
                pending.append(key)

    if reachable != all_keys:
        raise OracleError(
            f"reachability mismatch: expected {len(all_keys)} states, "
            f"reached {len(reachable)}"
        )

    return OracleSummary(
        state_count=len(states),
        transition_count=transition_count,
        reachable_state_count=len(reachable),
        action_counts=tuple(counts.items()),
    )
