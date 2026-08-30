# Planner task

Read the supplied `TwoLights.tla`, `TwoLights.cfg`, fixed Python artifact
contract, and `controller.schema.json`. Return only one JSON object conforming
exactly to `tla-steer-controller/0.1`; do not return Markdown or Python code.

The object is a restricted declarative inference program with exactly eight
uniquely targeted semantic steps. It must cover each target exactly once:

1. `INITIAL`
2. `Tick`
3. `AGreenToYellow`
4. `AYellowToRed`
5. `ARedToGreen`
6. `BGreenToYellow`
7. `BYellowToRed`
8. `BRedToGreen`

For each step, choose its order, give one precise Follower proposal
instruction, and provide only the schema-bounded probe states and expected
successors. Every action step must include at least one expected enabled probe
and one expected disabled probe. Preserve the exact five-field state shape.

Before returning, audit the complete object against these mechanical host
requirements:

- Include each exact `(kind, target, python_symbol)` tuple once: the initial
  tuple `(initial, INITIAL, INITIAL)` and the seven action tuples implied by
  the fixed artifact contract. Never duplicate a target or omit `INITIAL`.
- For every action, use exactly two distinct probe states. The first must make
  that action's TLA+ guard true and have its exact non-null successor. The
  second must make the guard false and have `expected_successor` set to null.
- Give every step a unique `id` and keep the target paired with its required
  fixed Python symbol.

Do not emit executable controller code, imports, extra targets, repair policy,
final-verifier feedback, or unconstrained requirements. The host validates and
executes the declarative object but does not correct your expected answers.
