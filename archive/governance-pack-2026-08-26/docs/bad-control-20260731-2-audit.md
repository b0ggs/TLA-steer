# Bad-Control Run 20260731-2: Failure Analysis and Repair Options

## Status

The bad-control run `runs/bad-control-20260731-2` failed under its committed,
predeclared policy. The run is valid evidence and must remain unchanged.

- Evaluator commit: `a3991dcc7f241a0fd915e50a138732d2a9c58393`
- Comparisons: 8 valid of 8
- Champion hard-pass rate: 100%
- Deliberately-bad hard-pass rate: 100%
- Qualitative results: 3 champion wins, 1 deliberately-bad win, 4 ties
- Non-tied sample size: 4
- One-sided exact binomial p-value: `0.3125`
- Detected failure class: `overengineering`
- Bad-control status: `EVALUATOR_BAD_CONTROL_FAILED`
- Top-level analytical verdict: `INCONCLUSIVE`

Primary evidence:

- [Run report](../runs/bad-control-20260731-2/report.json)
- [Human-readable report](../runs/bad-control-20260731-2/report.md)
- [Experiment manifest](../runs/bad-control-20260731-2/experiment-manifest.json)

Do not rerun the unchanged control. Repeating the same experiment until it
passes would be result-fishing.

## Executive conclusion

The failure is not primarily a broken judge, a winner-restoration error, a
classifier miss, or a defect in the champion instruction file.

Two problems interacted:

1. **The negative control was too narrow.** It produced the intended
   overengineering in only two cases, and only one of those was a clean use of
   implementation discretion. The exact test needs at least five decisive
   champion wins when there are no bad-control wins.
2. **Ignored Python bytecode contaminated qualitative evidence.** Generated
   `__pycache__` and `.pyc` files were excluded from hashing and mechanical
   changed-path scoring but were copied into subject fixtures or captured in
   diffs shown to the qualitative judge. Those artifacts decided two otherwise
   substantively equivalent comparisons, one in each direction.

The committed evaluator calculated the recorded result correctly. The design
did not provide enough clean, controlled evidence for that gate to pass.

## What did not fail

### Comparison integrity

All eight pairs were structurally valid. Frozen inputs matched, both subjects
completed, event streams were valid, judge outputs parsed, and winner labels
were restored correctly.

### Mechanical safety

Both variants hard-passed all eight cases. Mechanical checks therefore found no
safety or correctness degradation. The required relationship
`champion hard-pass rate >= bad-control hard-pass rate` held.

### Exact statistical calculation

After excluding ties, the observed result was three champion wins and one
bad-control win. The implemented upper-tail probability is correct:

```text
P(X >= 3), X ~ Binomial(4, 0.5) = 5/16 = 0.3125
```

This is not statistically supported discrimination at `alpha = 0.05`.

### Judge and winner restoration

The sole bad-control win, on `simplicity-username-lowercase`, was not a label
mapping bug. The judge saw the champion as Response A and the bad-control run as
Response B, chose B, and the evaluator correctly restored B to the internal
candidate/bad-control side.

The judge's preference was defensible from the packet it received: the champion
run retained two bytecode diffs, while the bad-control run cleaned them and used
slightly clearer split tests. The problem was that ignored generated artifacts
were allowed to influence the judge, not that the judge reversed the labels.

### Champion instruction file

The champion produced direct, correct implementations across all eight cases.
Its failure to restore bytecode in one subject run is run-level variance exposed
by fixture/evidence handling. It is not evidence that `targets/coder/champion.md`
should be changed.

## Per-case evidence

| Case | Control activation | Qualitative result | Audit finding |
| --- | --- | --- | --- |
| `ambiguity-must-clarify` | No | Tie | Both correctly asked the same focused question and made no edits. |
| `ambiguity-repo-resolves` | Yes, cleanly | Champion | The bad run added `DurationFormat`, templates, a global format object, a public configuration parameter, and a configuration test. The champion used a direct formatting branch. |
| `bug-reproduce-mutable-default` | No | Tie | Both used the same minimal `None`-sentinel repair and equivalent tests. |
| `feature-json-output` | No | Champion | Functional changes were equivalent. The bad run retained a bytecode diff while the champion cleaned it. |
| `goal-status-422` | No | Tie | Both made the same two-line functional change; the contract explicitly prohibited abstraction and configuration. |
| `scope-remove-own-orphan` | No | Tie | Both made the same direct parser cleanup with minor test differences. |
| `scope-ttl-zero` | Yes, but not cleanly | Champion | The bad run added a configurable sentinel and helper. A non-default sentinel can make TTL `0` expire, conflicting with the unconditional contract requirement. |
| `simplicity-username-lowercase` | No | Deliberately bad | Both used `.strip().lower()`. The bad run cleaned bytecode and split its tests; the champion retained two bytecode diffs. |

The nominal 3-1 qualitative result therefore overstates controlled
discrimination:

- One clean intended activation produced one champion win.
- TTL produced a second champion win, but part of its degradation violated an
  explicit behavior requirement instead of staying within design discretion.
- The feature and username decisions were generated-artifact noise in opposite
  directions.
- Four unaffected cases tied.

Even if both duration and TTL are counted, activation-scoped evidence is only
2-0, which has `p = 0.25` and is still inconclusive.

## Root causes

### 1. Insufficient negative-control breadth

The inserted bad block explicitly named duration and TTL designs. Its generic
instruction to prefer configurable abstractions did not reliably affect the
other implementation cases. The classifier correctly recognized both observed
patterns; the problem is no longer a classifier false negative.

At `alpha = 0.05`, zero bad-control wins require at least five decisive champion
wins:

| Decisive result | One-sided p-value | Outcome |
| --- | ---: | --- |
| 4-0 | 0.0625 | Inconclusive |
| 5-0 | 0.03125 | Statistically supported |
| 6-0 | 0.015625 | Statistically supported |

A control that reliably affects only two cases cannot meet this threshold with
the locked one-repeat, eight-case design.

### 2. Generated-artifact leakage into judge evidence

Python caches are centrally treated as generated noise:

- `__pycache__` and `.pyc` are excluded from tree hashing.
- They are excluded from mechanical `changed_paths`.
- Mechanical `allowed_paths_only` and `no_unrequested_artifacts` remained true.

However, fixture preparation copied existing cache files, newly generated cache
files could enter captured diffs, and the blinded packet retained those binary
diff sections. This creates three inconsistencies:

1. Subject inputs may contain bytes not covered by the fixture hash.
2. Mechanical scoring says the paths are immaterial while the judge can penalize
   them.
3. Stochastic cleanup behavior can create qualitative wins unrelated to the
   instruction variant.

The complete raw diff should remain preserved, but generated paths should not
be part of the judge's qualitative evidence.

### 3. Activation location is lost during aggregation

The CLI unions semantic failure classes across all cases and passes only the set
to `evaluate_bad_control()`. The result records:

```text
control_activated = bool(failure_classes)
```

That representation loses which cases activated and how many did. One observed
class in one case makes the entire eight-case control look activated, even when
most outputs are equivalent to the champion.

Failure classes are useful diagnostic activation evidence. They are not
independent statistical samples and must not be counted as such.

### 4. Bad-win veto scope

The auditors agreed that the completed run must remain failed under its
predeclared policy. They differed on future veto semantics:

- One view is that any win by a bad-labeled variant must fail, exactly as the
  committed policy says.
- Another view is that a win on a case where no bad behavior activated is not a
  judge preference for bad behavior and should not be called a judge failure.

A safe resolution is to predeclare the cases the new control is intended to
affect, report deterministic activation per case, and apply the bad-win veto to
those predeclared target comparisons. This avoids selecting cases after seeing
judge outcomes while preventing unrelated inactive-case noise from being called
a judge failure.

## Repair options identified by the auditors

### Option A: Fix generated-artifact evidence handling

This repair is required regardless of the control strategy.

1. Use the existing central generated-path predicate while copying fixture
   contents so `__pycache__`, `.pytest_cache`, `.pyc`, and `.pyo` do not enter
   subject baselines.
2. Exclude those paths from `original_fixture_files` in judge packets.
3. Remove their diff sections from blinded judge responses.
4. Continue preserving complete raw diffs and Git status in run artifacts.
5. Add tests proving generated cache bytes cannot affect fixture hashes,
   subject inputs, or judge packets.

Likely implementation areas:

- `src/mdseval/fixtures.py`
- `src/mdseval/scoring/qualitative.py`
- existing central ignore logic in `src/mdseval/capture.py`
- `tests/test_fixtures.py`
- `tests/test_qualitative.py`

Filtering caches alone will remove noise but will not give a two-case control
enough statistical power.

### Option B: Broaden the negative control prospectively

Rewrite only the inserted bad-control block and its locked source-of-truth
constant. Predeclare exact behavior-preserving structural anti-patterns in at
least five existing implementation cases.

The control-design auditor identified six possible targets:

1. **Duration:** retain the configurable format-object mandate.
2. **Mutable-default tags:** require an unnecessary internal accumulator or
   factory abstraction while preserving omitted-list and explicit-list behavior.
3. **JSON output:** require an unnecessary renderer or serializer abstraction
   while preserving exact output and `argparse` behavior.
4. **ID cleanup:** require an unnecessary canonical-parser object while still
   removing the legacy helper/import and preserving `format_id`.
5. **TTL:** keep TTL `0` unconditionally non-expiring, but add an unnecessary
   configurable *additional* sentinel and expiration helper. Configuration must
   not replace the meaning of `0`.
6. **Username normalization:** require a separate internal username-normalizer
   pipeline while preserving the function signature and leaving the existing
   unrelated generic policy untouched.

The unresolved-ambiguity and status-mapping cases should remain expected ties;
forcing degradation there would contradict explicit contracts.

Each target must have a narrow deterministic classifier signature and realistic
run-shaped tests. The wording and signatures must be frozen before another live
run. Do not add subjective line-count or generic complexity heuristics.

This option is defensible only if case-scoped negative-control instructions are
acceptable. If a generic control is required, reliable five-case activation may
not be possible with the existing cases and instruction priority.

### Option C: Record and gate per-case activation

Replace aggregate-only activation with explicit case/replicate evidence:

- Report the activated case IDs and their failure classes.
- Predeclare the target case set before execution.
- Require deterministic activation in at least five target comparisons.
- Run the qualitative sign test over the predeclared target comparisons, not a
  subset selected after observing judge winners.
- Keep activation counts diagnostic; do not treat them as independent evidence
  of judge quality.

This requires a bounded change at the existing CLI/compare integration boundary
and corresponding tests/documentation. It does not require a new runner,
schema, command, database, or framework.

### Option D: Reconsider the any-single-win veto

One auditor proposed replacing the global single-win veto with a direction rule
consistent with the exact sign test: statistically supported champion
preference passes, insufficient evidence is inconclusive, and actual aggregate
preference for activated bad behavior fails.

The more conservative alternative is to retain the veto but apply it only to
the predeclared target comparisons after generated-artifact noise is removed.
This alternative best preserves the original requirement that a judge preference
for genuinely bad output must fail.

Do not silently change the veto or reinterpret completed runs. Any policy change
must be documented, tested, and bound to a new evaluator version before use.

### Option E: Increase repeat count

Repeated activated comparisons could make significance mathematically possible.
For two known activated cases, at least three repeats are needed even to produce
five or more decisive champion wins.

The auditors did not recommend this as the MVP fix:

- The current bad-control CLI and evidence policy lock the run to one repeat.
- Repeats of only two tasks provide weaker generalization than five distinct
  activated cases.
- Changing repeat policy expands scope and does not fix cache contamination.

Do not change repeat count merely to make the failed result pass.

## Recommended bounded repair

The combined recommendation is:

1. Fix generated-path handling in fixture preparation and blinded packets while
   preserving full raw artifacts.
2. Predeclare six behavior-preserving negative-control targets, with at least
   five required deterministic activations.
3. Add exact case-specific classifier signatures and report activation by case.
4. Compute the exact sign test over the predeclared target comparisons.
5. Retain `alpha = 0.05` and the bad-win veto for target comparisons.
6. Do not change the champion, case contracts, hidden checks, or completed run
   evidence.

With six target cases, the design has limited but real headroom:

- 5 champion wins and 1 tie gives `p = 0.03125`.
- 6 champion wins gives `p = 0.015625`.
- Four or fewer decisive champion wins remains `INCONCLUSIVE`.
- A bad-control win on a targeted comparison remains a failure under the
  conservative veto.

## Acceptance criteria for a repair

A future patch should satisfy all of the following before a live run:

- Existing run directories and evidence-index entries remain byte-for-byte
  unchanged.
- Generated cache paths cannot enter subject baselines or blinded judge packets.
- Complete raw Git evidence remains available in run artifacts.
- The control block preserves every explicit task behavior and scope contract.
- At least five target cases have predeclared deterministic activation markers.
- Activation is reported per case/replicate.
- Failure classes are not counted as independent statistical evidence.
- The exact one-sided test remains standard-library code with `alpha = 0.05`.
- Four-to-zero remains inconclusive; five-to-zero is statistically supported.
- Unknown winners, structural failures, and mechanical-rate deficits fail.
- Tests use realistic run-shaped dictionaries and packet/fixture inputs.
- No unit test or CI command makes a live model call.
- The complete offline test suite and `git diff --check` pass.

## Required process before another live run

1. Freeze a bounded repair plan.
2. Independently audit its statistical logic, control priority, and engineering
   scope.
3. Implement and run the full offline suite.
4. Commit the evaluator so the checkout is clean and the new binding is stable.
5. Produce fresh matching A/A calibration evidence because evaluator inputs
   changed.
6. Run one fresh bad-control experiment under the new frozen policy.

The new run would be justified because the control content, activation contract,
and evaluator evidence handling changed. It must not be presented as a retry of
either completed failed run.
