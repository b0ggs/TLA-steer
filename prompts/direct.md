# Direct translation task

Translate the supplied `TwoLights.tla` and `TwoLights.cfg` into exactly one
imports-free Python module. Return only its exact contents in the final
response, with no Markdown fence or explanation. The trusted coordinator will
freeze that response as `candidate.py`.

The module contract is fixed:

- Define exactly these constants with the configured integer values:
  `CYCLE_LENGTH`, `MIN_GREEN`, `MIN_YELLOW`, `MIN_RED`, `MAX_PHASE`, `OFFSET`.
- Define `INITIAL` as one exact dictionary with exactly the keys `clock`,
  `lightA`, `timerA`, `lightB`, and `timerB`.
- Define exactly these seven pure functions, each accepting one state dictionary
  and returning one exact successor dictionary or `None` when disabled:
  `tick`, `a_green_to_yellow`, `a_yellow_to_red`, `a_red_to_green`,
  `b_green_to_yellow`, `b_yellow_to_red`, and `b_red_to_green`.
- Define `ACTIONS` mapping the original TLA+ labels `Tick`, `AGreenToYellow`,
  `AYellowToRed`, `ARedToGreen`, `BGreenToYellow`, `BYellowToRed`, and
  `BRedToGreen` to the corresponding functions.
- Never mutate the input state. Preserve every unchanged field exactly.
- Do not add imports, classes, helper definitions, I/O, tests, or named
  stuttering actions.

Implement the finite transition relation in the supplied configuration, not a
traffic-light design inferred from intuition.
