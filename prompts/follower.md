# Follower semantic-step task

You receive the full `TwoLights.tla` and `TwoLights.cfg`, the fixed Python
artifact contract, the current partial artifact, and exactly one Planner step.
The probe inputs are visible; their expected successors are not.

Return only this JSON shape, with no Markdown or explanation:

```json
{
  "schema_version": "tla-steer-proposal/0.1",
  "step_id": "the supplied step id",
  "python_fragment": "the requested assignment or function"
}
```

For the `INITIAL` step, `python_fragment` must contain exactly one assignment to
`INITIAL` whose dictionary uses only literal integer and string values. Do not
reference configured constant names such as `OFFSET`; write their integer
values literally. For an action step, it must contain exactly one function
definition with the required fixed symbol. An action accepts one state
dictionary and returns one exact successor dictionary or `None` when disabled.

Do not add imports, helpers, extra assignments or definitions, classes, I/O,
tests, Markdown, or prose. Never mutate the input. Preserve all unchanged state
fields exactly. There is no proposal retry.
