# Volunteer badge manifest

Build an active volunteer badge manifest from attendee records and a small
door-access policy.

## R1 — Exact API and input preservation

`badge_manifest.py` must export exactly these public definitions:

```python
class BadgeManifestError(ValueError):
    pass

def build_manifest(
    attendees: list[object],
    policy: dict[str, object],
) -> list[dict[str, object]]:
    ...
```

`BadgeManifestError` must directly subclass `ValueError` and use the inherited
`ValueError` constructor. `build_manifest` has exactly two required
positional-or-keyword parameters, in the order `attendees`, then `policy`, with
no defaults.

The function must not mutate either argument or anything nested inside either
argument. For an empty attendee list and valid policy, the exact result is `[]`.

## R2 — Attendee contract

After policy validation succeeds, `attendees` must be an exact built-in `list`.
Every element must be an exact built-in `dict` with exactly these keys and no
others:

```text
id
name
role
active
late_shift
```

`id`, `name`, and `role` must each be exact built-in `str` values containing at
least one character. Whitespace-only strings are allowed. `active` and
`late_shift` must each be exact built-in `bool` values. Attendee IDs must be
unique. Each role must be a key in the validated policy's `role_area` mapping.

Any violation raises `BadgeManifestError`. Error text is unscored. R2 scoring
uses only records whose `active` value is `true`; active/inactive selection is
exclusively R4.

The exhaustive public R2 negative-scoring values are:

1. The top-level value `"not-a-list"`.
2. This extra-key record:

   ```json
   {
     "id": "V-200",
     "name": "Kai Reed",
     "role": "runner",
     "active": true,
     "late_shift": false,
     "note": "desk"
   }
   ```

3. The same valid `V-200` record with integer `1` replacing boolean `true` for
   `active`.
4. Two otherwise valid active records both having ID `"V-200"`.
5. An otherwise valid active record having role `"usher"`.

Each listed value must raise `BadgeManifestError`.

## R3 — Policy contract

Policy validation happens before attendee validation.

`policy` must be an exact built-in `dict` with exactly these keys and no others:

```text
common_area
late_shift_area
role_area
```

`common_area` and `late_shift_area` must each be exact built-in `str` values
containing at least one character.

`role_area` must be a nonempty exact built-in `dict`. Every role key and every
area value in it must be an exact built-in `str` containing at least one
character. Whitespace-only strings are allowed. No additional uniqueness or
cross-field constraint applies.

Any violation raises `BadgeManifestError`. Error text is unscored. The complete
repository policy is public in `badge_policy.json`.

The exhaustive public R3 negative-scoring values are:

1. The public policy plus the extra key/value `"version": 1`.
2. The public policy with integer `7` replacing `"lobby"` as `common_area`.
3. The public policy with `role_area` replaced by `{}`.
4. The public policy with `role_area` replaced by `{"checkin": 9}`.

Each listed value must raise `BadgeManifestError`.

## R4 — Active selection

After all R2 validation succeeds, return one entry for every attendee whose
`active` value is `true` and no entry for an attendee whose `active` value is
`false`.

R4 scoring uses only schema-valid attendees and checks only the set of returned
`badge_id` values; it does not score area values, display values, entry field
sets, or result order.

For `fixtures/attendees.json`, the exact expected R4 ID set is:

```text
V-099
V-101
V-104
```

`V-120` is the public valid inactive example and must be omitted.

## R5 — Area grants

For one active attendee, construct `areas` in exactly this order:

1. `policy["common_area"]`
2. `policy["role_area"][attendee["role"]]`
3. `policy["late_shift_area"]`, only when `late_shift` is `true`

Do not sort, deduplicate, or add other values. Repeated strings therefore remain
repeated if a valid policy uses the same string more than once.

R5 scoring uses one valid active attendee and checks only its `areas` value. The
exact public scored attendee is:

```json
{
  "id": "V-500",
  "name": "Noah Green",
  "role": "runner",
  "active": true,
  "late_shift": true
}
```

With `badge_policy.json`, its exact expected `areas` value is:

```json
["lobby", "supply-room", "staff-exit"]
```

## R6 — Result shape, display, and ordering

Return an exact built-in `list`. Each returned item must be an exact built-in
`dict` with exactly these four keys:

```text
badge_id
display
areas
late_shift
```

The non-area fields are:

- `badge_id`: the attendee `id`, unchanged.
- `display`: exactly `name + " [" + role + "]"`.
- `late_shift`: the attendee boolean, unchanged.

Sort entries by `badge_id` using ascending Python string ordering. Dictionary
insertion order is unscored.

R6 scoring uses only valid active attendees. It checks exact container types,
the exact four-key set, `badge_id`, `display`, `late_shift`, and entry order. It
does not inspect the contents of `areas`, so it does not rescore R5. Its exact
public input records are `V-9` followed by `V-2`, and its exact projected result
is:

```text
V-2 | Ana Fox [checkin] | true
V-9 | Zed Wu [runner]   | false
```

## R7 — CLI success

`badge_cli.py` must export:

```python
def main(argv: Sequence[str] | None = None) -> int:
    ...
```

It has one optional positional-or-keyword parameter named `argv`, defaulting to
`None`. `None` means parse `sys.argv[1:]`. The script guard must be exactly
behaviorally equivalent to:

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

The command-line order is exactly:

```text
python3 badge_cli.py ATTENDEES_JSON POLICY_JSON
```

On success:

1. Read `ATTENDEES_JSON` first as UTF-8 JSON.
2. Read `POLICY_JSON` second as UTF-8 JSON.
3. Call `build_manifest(attendees, policy)`.
4. Serialize only after the call succeeds.
5. Return integer status `0`.
6. Emit nothing to stderr.
7. Write stdout exactly as:

   ```python
   json.dumps(
       result,
       ensure_ascii=True,
       sort_keys=True,
       separators=(",", ":"),
   ) + "\n"
   ```

R7 has two isolated public probes. The direct-entry probe runs the script with
`fixtures/empty-attendees.json` followed by `badge_policy.json`; its exact
stdout is `[]` followed by one newline.

The serialization probe calls `main` in-process with those same two paths while
patching only the already-public `badge_cli.build_manifest` callable to return
this exact value:

```python
[
    {
        "zeta": "café",
        "alpha": "雪",
        "nested": {"b": 2, "a": 1},
    }
]
```

The serialization probe must return `0`, emit nothing to stderr, and emit this
exact stdout line followed by one newline:

```text
[{"alpha":"\u96ea","nested":{"a":1,"b":2},"zeta":"caf\u00e9"}]
```

The patched value intentionally bypasses manifest construction. Thus this probe
observes `ensure_ascii=True`, recursive `sort_keys=True`, compact separators,
and the final newline without rescoring R4–R6. It does not patch or require any
other `badge_cli` module attribute.

## R8 — CLI failures

For each listed failure, `main` must return integer status `2`, stdout must be
exactly empty, and stderr must be nonempty. Error wording is unscored.
`main` must return rather than propagate `SystemExit` for argument errors.

The exhaustive R8 scoring probes are:

1. `main([])`, which has a missing positional argument.
2. Attendee path `fixtures/missing-attendees.json`, which does not exist, with
   policy path `badge_policy.json`.
3. Attendee path `fixtures/malformed-attendees.json`, whose exact bytes are
   public below, with policy path `badge_policy.json`.
4. A temporary attendee file containing exact bytes `ff` in hexadecimal, with
   policy path `badge_policy.json`.
5. Valid paths `fixtures/empty-attendees.json` and `badge_policy.json`, while
   the imported `build_manifest` callable is replaced by a test double that
   raises `BadgeManifestError("forced application failure")`.

Probe 5 is the only application-error probe. It checks conversion of an already
raised `BadgeManifestError`; it does not exercise or rescore R2 or R3.
