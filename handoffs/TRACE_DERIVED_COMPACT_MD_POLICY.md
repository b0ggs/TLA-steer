# Trace-derived compact MD policy

## Conclusion

The strongest supported policy is not another request to be focused. It is a
small set of completion gates: decompose the request into separately observable
invariants, trace the real execution path for each invariant, and require direct
evidence for every row before claiming completion. This targets both substantive
current-batch failures and is compatible with the successful trajectories.

The evidence supports this as a high-probability candidate for another
controlled test, not as a proven causal improvement. The corpus contains no run
of the incumbent full `coder.md` on these four tasks.

## Corpus inventory

I mechanically searched the working tree, all repository Git history under
`runs/`, and every `.tar`/`.tar.gz` handoff member name for these exact task IDs:

- `full-boltons-wraps-forwarding`
- `full-click-stream-lifecycle`
- `full-flask-automatic-options`
- `full-starlette-websocket-denial`

For every located attempt I parsed the available `intent.json`, `launch.json`,
`events.jsonl`, `final.txt`, `diff.patch`, `capture.json`, `checker.json`,
`checker-runtime.json`, `result.json`, `disposition.json`, and
`attempt-manifest.json`. The two complete historical batches and the current
batch were also reverified offline with `scripts/run_batch.py verify`.

| Batch | Bound instruction | Attempt evidence | Mechanical outcome |
|---|---|---:|---|
| [`cost-time-probe-v1`](../runs/dev-v2/cost-time-probe-v1/REQUEST.json) | 12 empty-MD attempts and 12 probe-MD attempts | 24 complete attempt directories | 21 resolved; 3 valid unresolved; no timeout or infrastructure failure |
| [`maximum-difficulty-sealed-v1`](../runs/dev-v2/maximum-difficulty-sealed-v1/REQUEST.json) | Empty MD | 12 complete attempt directories | 11 resolved; 1 valid unresolved |
| [`maximum-difficulty-search-disabled-v1`](../runs/dev-v2/maximum-difficulty-search-disabled-v1/REQUEST.json) | Empty MD | 5 partial/failed launch directories | No usable model trajectory; expired authentication or incomplete launch |
| [`maximum-difficulty-search-disabled-v2`](../runs/dev-v2/maximum-difficulty-search-disabled-v2/REQUEST.json) | Empty MD | 12 complete attempt directories | 12 mechanically resolved; 3 subject timeouts have incomplete trajectories |

The exact arm bindings are recorded in the requests and repeated in each
intent/launch/result:

- Empty MD: `controls/coder/null-m2.md`, SHA-256
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- Probe MD: `controls/coder/cost-time-probe-v1.md`, SHA-256
  `beecdb31396701c6712391f1cdcaea34ba49e8d2cffe77c7adc95ba77faf50ec`.

The per-task inventory is:

| Task | Attempt directories | Substantive coding trajectories | Resolved | Valid unresolved | Infrastructure-only/incomplete |
|---|---:|---:|---:|---:|---:|
| Boltons | 12 | 12 | 12 | 0 | 0 |
| Click | 15 | 12 | 10 | 2 | 3 |
| Flask | 12 | 12 | 12 | 0 | 0 |
| Starlette | 14 | 12 | 10 | 2 | 2 |
| **Total** | **53** | **48** | **44** | **4** | **5** |

All 48 substantive trajectories have the full attempt evidence set listed
above. The five failed `maximum-difficulty-search-disabled-v1` launches are:

- Click [`attempt-1`](../runs/dev-v2/maximum-difficulty-search-disabled-v1/full-click-stream-lifecycle/null/attempt-1/events.jsonl),
  [`attempt-2`](../runs/dev-v2/maximum-difficulty-search-disabled-v1/full-click-stream-lifecycle/null/attempt-2/events.jsonl),
  and [`attempt-3`](../runs/dev-v2/maximum-difficulty-search-disabled-v1/full-click-stream-lifecycle/null/attempt-3/events.jsonl): authentication request failures before an agent message or edit. The first two were historically finalized as valid omissions; the third was invalid because its checker was unscoreable. None is a coding failure.
- Starlette [`attempt-1`](../runs/dev-v2/maximum-difficulty-search-disabled-v1/full-starlette-websocket-denial/null/attempt-1/infra-invalid.json): infrastructure-invalid before a model response; and [`attempt-2`](../runs/dev-v2/maximum-difficulty-search-disabled-v1/full-starlette-websocket-denial/null/attempt-2/launch.json): intent/launch only.

The only archive containing these run roots is
[`full-handoff-2026-08-25.tar`](full-handoff-2026-08-25.tar). Its 455 regular
files under the three pre-current run roots are byte-identical to the on-disk
copies, so it contributes no distinct attempt. No deleted or additional attempt
path appeared in Git history.

## Best controlled comparison

Only the current batch directly compares instructions under the same runner,
model, timeout, task versions, and search-disabled seal:

| Task | Empty MD | Probe MD |
|---|---:|---:|
| Boltons | 3/3 | 3/3 |
| Flask | 3/3 | 3/3 |
| Click | 2/3 | 2/3 |
| Starlette | 3/3 | 2/3 |

The probe therefore did not create a correctness advantage. The predefined
analysis also found no directional token, wall-time, or trajectory signal; see
[`analysis.json`](../runs/dev-v2/cost-time-probe-v1/analysis.json) and the
[`result report`](COST_TIME_PROBE_RESULT.md). This is descriptive evidence, not
a significance test or proof that the probe caused the Starlette miss.

## Trace findings

### 1. The repeated Click miss was failure to keep explicit requirements separate

The Click contract separately required behavior for an explicit wrapper
`close()` and for garbage collection/finalization. Both current failures
collapsed those into a single ownership/finalizer theory:

- Empty-MD [`attempt-3`](../runs/dev-v2/cost-time-probe-v1/full-click-stream-lifecycle/null/attempt-3/events.jsonl)
  added only `__del__` detachment; its added test used `del` plus
  `gc.collect()`. The [checker](../runs/dev-v2/cost-time-probe-v1/full-click-stream-lifecycle/null/attempt-3/checker.json)
  returned R1=false, R2=true, G1=true even after the trace reported 28 focused
  and 1,283 broad tests passing.
- Probe-MD [`attempt-2`](../runs/dev-v2/cost-time-probe-v1/full-click-stream-lifecycle/probe/attempt-2/events.jsonl)
  made the same source omission and tested finalization rather than calling
  `close()`. Its [checker](../runs/dev-v2/cost-time-probe-v1/full-click-stream-lifecycle/probe/attempt-2/checker.json)
  returned the same R1=false, R2=true, G1=true pattern.

Across all 12 substantive Click trajectories, the implementation distinction is
exact: every one of the 10 resolved diffs implemented explicit
`_NamedTextIOWrapper.close()` handling; neither failed diff did. Examples are
the current successful empty-MD
[`attempt-1`](../runs/dev-v2/cost-time-probe-v1/full-click-stream-lifecycle/null/attempt-1/diff.patch),
probe-MD
[`attempt-1`](../runs/dev-v2/cost-time-probe-v1/full-click-stream-lifecycle/probe/attempt-1/diff.patch),
and historical search-disabled
[`attempt-2`](../runs/dev-v2/maximum-difficulty-search-disabled-v2/full-click-stream-lifecycle/null/attempt-2/diff.patch).

**Evidence:** the omitted contract row exactly matches the failed requirement.
Broad or adjacent green tests did not compensate for the missing direct case.

**Inference:** an enforced request-to-evidence checklist would likely have made
this omission harder. The traces do not prove that an MD containing the rule
will change model behavior.

### 2. The Starlette probe miss patched the event surface, not the whole control path

Current probe
[`attempt-3`](../runs/dev-v2/cost-time-probe-v1/full-starlette-websocket-denial/probe/attempt-3/diff.patch)
renamed outgoing `http.response.*` messages for WebSockets and correctly gated
HTTP-only file fields. It did not bypass `StreamingResponse`'s legacy HTTP
disconnect-listener task group on a WebSocket scope. Its
[`checker.json`](../runs/dev-v2/cost-time-probe-v1/full-starlette-websocket-denial/probe/attempt-3/checker.json)
therefore records R1=false, R2=true, G1=true.

An offline replay of the preserved patch against the exact two R1 tests produced
`2 failed, 2 passed`: both direct streaming/background cases failed under
asyncio and Trio when `listen_for_disconnect()` read an empty WebSocket receive
message and raised `KeyError: "type"`; both integration denial cases passed.
This demonstrates why the attempt's analogous integration test was insufficient.

The resolved Starlette implementations handled three independent invariants:

1. Translate start/body event types.
2. Bypass HTTP disconnect polling so WebSocket streaming completes and its
   background task runs exactly once.
3. Avoid HTTP-only `method` and `pathsend` behavior for file denial responses.

Multiple source shapes passed, so the evidence favors the invariant/control-path
model rather than a particular patch. Examples include current empty-MD
[`attempt-1`](../runs/dev-v2/cost-time-probe-v1/full-starlette-websocket-denial/null/attempt-1/diff.patch),
current probe-MD
[`attempt-1`](../runs/dev-v2/cost-time-probe-v1/full-starlette-websocket-denial/probe/attempt-1/diff.patch),
and search-disabled
[`attempt-2`](../runs/dev-v2/maximum-difficulty-search-disabled-v2/full-starlette-websocket-denial/null/attempt-2/diff.patch).

The other unresolved Starlette trajectory is a different failure class. The
sealed empty-MD
[`attempt-2`](../runs/dev-v2/maximum-difficulty-sealed-v1/full-starlette-websocket-denial/null/attempt-2/diff.patch)
passed both product requirements but failed G1. Offline replay of its broad
guard produced `197 passed, 2 failed, 4 deselected`: both failures came from the
attempt's newly added file-response test under asyncio and Trio. Its hand-built
WebSocket scope omitted the required `headers` field, causing
`KeyError: "headers"`. The source correction was not the cause of that outcome;
the changed test fixture was invalid.

**Evidence:** one failure missed a mode-specific control edge; the other did not
validate its own added test fixture.

**Inference:** direct per-invariant tests plus a requirement that every changed
test itself pass should address both mechanisms without prescribing
task-specific code.

### 3. The ceiling tasks support behavior modeling, but provide no failure contrast

All 12 Boltons trajectories independently reduced the request to the same
parameter-kind decision table: keyword-capable defaulted and keyword-only
parameters forward by name; positional-only parameters remain positional; and
parameters before nonempty `*args` remain positional. That model appears in
successful current empty-MD
[`attempt-1`](../runs/dev-v2/cost-time-probe-v1/full-boltons-wraps-forwarding/null/attempt-1/events.jsonl),
probe-MD
[`attempt-1`](../runs/dev-v2/cost-time-probe-v1/full-boltons-wraps-forwarding/probe/attempt-1/events.jsonl),
and historical search-disabled
[`attempt-1`](../runs/dev-v2/maximum-difficulty-search-disabled-v2/full-boltons-wraps-forwarding/null/attempt-1/events.jsonl)
traces.

All 12 Flask trajectories similarly modeled explicit true, explicit false,
global default, and self-handled `OPTIONS` before changing the one route
registration decision. Examples are current empty-MD
[`attempt-1`](../runs/dev-v2/cost-time-probe-v1/full-flask-automatic-options/null/attempt-1/events.jsonl),
probe-MD
[`attempt-1`](../runs/dev-v2/cost-time-probe-v1/full-flask-automatic-options/probe/attempt-1/events.jsonl),
and historical search-disabled
[`attempt-1`](../runs/dev-v2/maximum-difficulty-search-disabled-v2/full-flask-automatic-options/null/attempt-1/events.jsonl).

These traces support decision tables/state models as a compatible, low-risk
working method. Because both tasks are 12/12 ceilings, they cannot show that the
method caused success or distinguish a better policy on correctness.

### 4. Validation-tool failure needs a bounded branch, not repeated hunting or static success claims

The mounted interpreter was commonly absent from `PATH`. Many attempts repeated
equivalent `python`, `python3`, `pytest`, and `uv` failures, searched broad
filesystem regions, or declared tests unavailable even though the preserved
runtime binding names `/python/bin/python3.11`. This appears in both successful
and failed traces, so it is chiefly an efficiency and evidence-quality problem.

Examples include the failed Click probe
[`attempt-2`](../runs/dev-v2/cost-time-probe-v1/full-click-stream-lifecycle/probe/attempt-2/events.jsonl),
the failed Starlette probe
[`attempt-3`](../runs/dev-v2/cost-time-probe-v1/full-starlette-websocket-denial/probe/attempt-3/events.jsonl),
and successful Boltons probe
[`attempt-1`](../runs/dev-v2/cost-time-probe-v1/full-boltons-wraps-forwarding/probe/attempt-1/events.jsonl).

The opposite failure also occurs: correct patches continued into repeated
hanging or equivalent validation attempts until the subject timeout. The
search-disabled-v2 Click
[`attempt-1`](../runs/dev-v2/maximum-difficulty-search-disabled-v2/full-click-stream-lifecycle/null/attempt-1/events.jsonl)
and Starlette
[`attempt-1`](../runs/dev-v2/maximum-difficulty-search-disabled-v2/full-starlette-websocket-denial/null/attempt-1/events.jsonl)
and
[`attempt-3`](../runs/dev-v2/maximum-difficulty-search-disabled-v2/full-starlette-websocket-denial/null/attempt-3/events.jsonl)
all mechanically resolved but timed out without a final subject message.

**Inference:** one bounded tooling diagnostic, one control run, and a two-sided
stop rule should reduce both premature static handoff and unbounded retry. The
repository-specific `/python` path should not be embedded in a general MD.

## Ranked policy mechanisms

1. **Per-requirement evidence gate — strongest.** Convert every explicit
   behavior, negative case, cleanup condition, and compatibility clause into a
   separate observable row. This directly targets the exact two repeated Click
   misses.
2. **Trace real modes and control edges.** Model state, ownership, and both send
   and receive paths before editing. This targets the Starlette event-renaming
   patch that left the incompatible HTTP control path active.
3. **Validate the proof itself.** A changed test must run and pass; an analogous
   integration test or broad green suite cannot stand in for an uncovered row.
   This targets both Starlette failure mechanisms and the Click false confidence.
4. **Small causal diff plus adjacent regressions.** Preserve nearby public and
   negative behavior after satisfying the matrix. The 12/12 Flask traces support
   this as compatible and low-risk, though not as a demonstrated differentiator.
5. **Bounded diagnostic and two-sided stop.** Diagnose missing/hanging tools
   once, use one control, and stop only after all gates pass—but then stop. This
   targets repeated static claims and the three mechanically resolved timeouts.

## Exact proposed short MD

The policy block below is 109 prose words (111 including its heading).

```markdown
# Completion gates

1. Before editing, list distinct observable invariants, including negative, cleanup, error, and compatibility cases.
2. Trace each invariant through the control, state, or ownership path; a nearby mode or analogous path is not evidence.
3. Make the smallest root-cause change. Preserve adjacent behavior and public interfaces.
4. Prove every invariant with a focused test or executable reproducer, then run adjacent regressions. A broad green suite does not cover an untested requirement.
5. If tooling is missing or hangs, make one bounded diagnostic and one control run; do not retry equivalent failures.
6. Stop only when every invariant has evidence, changed tests pass, and the diff is scoped. Otherwise report the gap; do not claim completion.
```

## Competing explanations and limits

- This is a four-task, one-model corpus with three substantive samples per
  task/arm/run. Boltons and Flask are correctness ceilings. The proposed policy
  has not been run.
- The exact Click implementation association partly restates the functional
  requirement: explicit close handling is necessary for R1. It does not prove
  that checklist language will cause the model to implement it.
- The current probe comparison is the only instruction-controlled comparison.
  Its Starlette 2/3 versus 3/3 difference is one attempt and is not causal or
  statistically significant evidence.
- Historical `maximum-difficulty-sealed-v1` traces allowed provider-side web
  search in seven of 12 attempts. They remain useful preserved process evidence,
  but search-derived decisions are not clean local-reasoning evidence. The
  strongest Click and Starlette mechanisms also appear in the current
  search-disabled batch.
- The three mechanically resolved v2 timeouts prove that their captured trees
  passed the checker, not that their subject trajectories completed cleanly.
- Private checkers reveal whether the submitted tree met the contract, but the
  proposed policy must remain task-neutral. It says to cover request invariants,
  not to predict hidden tests.
- The sealed Starlette failure was a bad added fixture, not a product-code
  regression. It supports validating changed tests; it should not be counted as
  evidence that the source strategy failed.
- No evidence here evaluates the incumbent full `coder.md`, a replacement for
  it, another model, or tasks outside these four repositories.

## Mechanical validation performed

- `python3 scripts/run_batch.py verify cost-time-probe-v1` — exit 0.
- `python3 scripts/run_batch.py verify maximum-difficulty-sealed-v1` — exit 0.
- `python3 scripts/run_batch.py verify maximum-difficulty-search-disabled-v2` — exit 0.
- All 53 attempt directories and their evidence-presence counts were enumerated
  from disk; all 48 substantive result/checker/capture/event/diff sets parsed.
- All 455 archived pre-current run files matched their on-disk SHA-256 values.
- Git history and handoff-archive member scans found no additional attempt path.
- The exact policy word count was checked mechanically and is at most 120 words.

No live model call was made, and no run evidence, task, target, control,
candidate, or existing document was modified.
