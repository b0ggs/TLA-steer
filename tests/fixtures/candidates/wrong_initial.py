CYCLE_LENGTH = 8
MIN_GREEN = 3
MIN_YELLOW = 1
MIN_RED = 4
MAX_PHASE = 6
OFFSET = 2

INITIAL = {
    "clock": 0,
    "lightA": "green",
    "timerA": 0,
    "lightB": "red",
    "timerB": 0,
}


def tick(state: dict) -> dict | None:
    if state["timerA"] >= MAX_PHASE or state["timerB"] >= MAX_PHASE:
        return None
    successor = dict(state)
    successor["clock"] = (state["clock"] + 1) % CYCLE_LENGTH
    successor["timerA"] = state["timerA"] + 1
    successor["timerB"] = state["timerB"] + 1
    return successor


def a_green_to_yellow(state: dict) -> dict | None:
    if state["lightA"] != "green" or state["timerA"] < MIN_GREEN:
        return None
    successor = dict(state)
    successor["lightA"] = "yellow"
    successor["timerA"] = 0
    return successor


def a_yellow_to_red(state: dict) -> dict | None:
    if state["lightA"] != "yellow" or state["timerA"] < MIN_YELLOW:
        return None
    successor = dict(state)
    successor["lightA"] = "red"
    successor["timerA"] = 0
    return successor


def a_red_to_green(state: dict) -> dict | None:
    if state["lightA"] != "red" or state["timerA"] < MIN_RED:
        return None
    successor = dict(state)
    successor["lightA"] = "green"
    successor["timerA"] = 0
    return successor


def b_green_to_yellow(state: dict) -> dict | None:
    if state["lightB"] != "green" or state["timerB"] < MIN_GREEN:
        return None
    successor = dict(state)
    successor["lightB"] = "yellow"
    successor["timerB"] = 0
    return successor


def b_yellow_to_red(state: dict) -> dict | None:
    if state["lightB"] != "yellow" or state["timerB"] < MIN_YELLOW:
        return None
    successor = dict(state)
    successor["lightB"] = "red"
    successor["timerB"] = 0
    return successor


def b_red_to_green(state: dict) -> dict | None:
    if state["lightB"] != "red" or state["timerB"] < MIN_RED:
        return None
    successor = dict(state)
    successor["lightB"] = "green"
    successor["timerB"] = 0
    return successor


ACTIONS = {
    "Tick": tick,
    "AGreenToYellow": a_green_to_yellow,
    "AYellowToRed": a_yellow_to_red,
    "ARedToGreen": a_red_to_green,
    "BGreenToYellow": b_green_to_yellow,
    "BYellowToRed": b_yellow_to_red,
    "BRedToGreen": b_red_to_green,
}
