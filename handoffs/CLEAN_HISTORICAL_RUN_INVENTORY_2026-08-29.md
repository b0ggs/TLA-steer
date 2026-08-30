# Clean historical run inventory for the four time/token tasks

- **Date:** 2026-08-29
- **Status:** Read-only evidence audit; not an experimental result,
  significance claim, or approved roadmap

## Direct answer

Yes. The two latest evidence-bounded-MD failures on Click were **not** the first
failures in clean historical runs, and failures were not confined to that arm.
Before the latest `evidence-bounded-vs-null-v2` batch, clean mechanically scored
attempts already included:

- one Click failure and one Starlette failure with **no MD**;
- one Click failure and two Starlette failures with the **old MD**; and
- one Click failure and three Starlette failures with the **new MD**.

The latest batch added two more new-MD Click failures. Boltons and Flask had no
clean mechanical failures in the preserved attempts audited here. This is a
descriptive inventory, not evidence that any MD caused or prevented a failure:
the batches differ in date and runtime details, the tasks were repeatedly
exposed, and contamination exclusions leave unequal arm counts.

## Requested aggregate table

`Runs` includes every usable subject attempt with no observed answer-bearing
runtime retrieval, whether it passed or failed. `Fails` is the subset for which
the preserved mechanical checker says `resolved: false`.

| Task | No-MD runs | Old-MD runs | New-MD runs | No-MD fails | Old-MD fails | New-MD fails |
|---|---:|---:|---:|---:|---:|---:|
| Boltons wraps forwarding | 15 | 6 | 9 | 0 | 0 | 0 |
| Flask automatic options | 14 | 6 | 9 | 0 | 0 | 0 |
| Starlette websocket denial | 11 | 6 | 9 | 1 | 2 | 3 |
| Click stream lifecycle | 11 | 3 | 9 | 1 | 1 | 3 |
| **Total** | **51** | **21** | **36** | **2** | **3** | **6** |

Thus the clean-at-runtime corpus contains **108 usable subject attempts: 97
passes and 11 failures**. The raw totals above should not be treated as a pooled
MD comparison because the clean subsets are unbalanced and come from different
development batches.

## What the three arm names mean

Classification uses the exact SHA-256 recorded in each `launch.json` and
`result.json`, not the directory's arm label.

| Name used here | Injected file | Bytes | SHA-256 | Historical arm labels |
|---|---|---:|---|---|
| No MD | [`controls/coder/null-m2.md`](../controls/coder/null-m2.md) | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `null` |
| Old MD | [`controls/coder/cost-time-probe-v1.md`](../controls/coder/cost-time-probe-v1.md) | 473 | `beecdb31396701c6712391f1cdcaea34ba49e8d2cffe77c7adc95ba77faf50ec` | `probe`, `previous` |
| New MD | [`controls/coder/evidence-bounded-v1.md`](../controls/coder/evidence-bounded-v1.md) | 949 | `c0d56e29ade34c24278b976e84b29e47324c11a23399ca882239daffc9762c74` | `evidence-bounded` |

All 125 relevant preserved launches use exactly one of these three hashes.
There is no second materially different old-MD hash to merge or separate.

## Inclusion and exclusion rule

The audit enumerated every `launch.json` under `runs/` whose task ID is one of:

- `full-boltons-wraps-forwarding`;
- `full-flask-automatic-options`;
- `full-starlette-websocket-denial`; or
- `full-click-stream-lifecycle`.

Only `runs/dev-v2` contains such launches. The classification rule was:

1. **Include** a launched attempt when a subject produced a usable solution and
   its trace contains no observed successful answer-bearing retrieval.
2. **Exclude for contamination** an attempt with completed web search,
   answer-bearing GitHub MCP retrieval, private checker/reference/evaluator or
   previous-attempt access, or another successful answer-bearing lookup.
3. **Include but flag** an external lookup attempt that returned no external
   information.
4. **Exclude separately as non-attempt evidence** a pre-response authentication,
   launch, or infrastructure failure with no usable subject solution. It is
   neither a run nor a coding failure, even if an old result file mechanically
   scored the unchanged baseline.
5. Count a usable, mechanically incorrect subject solution as both one run and
   one fail. Mechanical `checker.json`/`result.json` evidence controls the
   outcome; final prose does not.

Three search-disabled-v2 subject processes timed out after creating solutions
(Click no-MD attempt 1 and Starlette no-MD attempts 1 and 3). Their preserved
checkers resolved the submitted solutions, so they remain included runs and are
not failures.

This definition is deliberately limited to **observed runtime leakage**.
Possible memorization in model weights is unobservable from these traces, is
not classified as runtime cheating, and could affect every arm.

## Arithmetic reconciliation

The preserved corpus contains 125 relevant launches:

| Disposition | Attempts | Passes | Mechanical fails | Counted in requested table? |
|---|---:|---:|---:|---|
| Usable subject attempt, no observed answer-bearing retrieval | 108 | 97 | 11 | Yes |
| Usable subject attempt, answer-bearing web/MCP retrieval | 12 | 11 | 1 | No |
| Authentication/infrastructure/launch failure before a usable subject solution | 5 | N/A | N/A | No |
| **Total launches** | **125** |  |  |  |

There are 123 `result.json` files: the two remaining launch-only/infrastructure
Starlette directories have no result. The arm totals in the requested table
also reconcile: `51 + 21 + 36 = 108`, and `2 + 3 + 6 = 11` failures.

## Per-batch reconciliation

Each populated cell is `clean runs / clean fails`. A dash means that arm was
not part of the batch. Contaminated and no-subject exclusions appear after this
table.

| Batch | Task | No MD | Old MD | New MD |
|---|---|---:|---:|---:|
| `maximum-difficulty-sealed-v1` | Boltons | 3 / 0 | — | — |
|  | Flask | 2 / 0 | — | — |
|  | Starlette | 0 / 0 | — | — |
|  | Click | 0 / 0 | — | — |
| `maximum-difficulty-search-disabled-v2` | Boltons | 3 / 0 | — | — |
|  | Flask | 3 / 0 | — | — |
|  | Starlette | 3 / 0 | — | — |
|  | Click | 3 / 0 | — | — |
| `cost-time-probe-v1` | Boltons | 3 / 0 | 3 / 0 | — |
|  | Flask | 3 / 0 | 3 / 0 | — |
|  | Starlette | 2 / 0 | 3 / 1 | — |
|  | Click | 3 / 1 | 2 / 1 | — |
| `evidence-bounded-probe-v1` | Boltons | — | 3 / 0 | 3 / 0 |
|  | Flask | — | 3 / 0 | 3 / 0 |
|  | Starlette | — | 3 / 1 | 3 / 1 |
|  | Click | — | 1 / 0 | 3 / 0 |
| `evidence-bounded-vs-null-v1` | Boltons | 3 / 0 | — | 3 / 0 |
|  | Flask | 3 / 0 | — | 3 / 0 |
|  | Starlette | 3 / 1 | — | 3 / 2 |
|  | Click | 2 / 0 | — | 3 / 1 |
| `evidence-bounded-vs-null-v2` | Boltons | 3 / 0 | — | 3 / 0 |
|  | Flask | 3 / 0 | — | 3 / 0 |
|  | Starlette | 3 / 0 | — | 3 / 0 |
|  | Click | 3 / 0 | — | 3 / 2 |

Batch-level totals provide a second reconciliation:

| Batch | Clean usable | Clean fails | Contaminated usable | No usable subject |
|---|---:|---:|---:|---:|
| `maximum-difficulty-sealed-v1` | 5 | 0 | 7 | 0 |
| `maximum-difficulty-search-disabled-v1` | 0 | 0 | 0 | 5 |
| `maximum-difficulty-search-disabled-v2` | 12 | 0 | 0 | 0 |
| `cost-time-probe-v1` | 22 | 3 | 2 | 0 |
| `evidence-bounded-probe-v1` | 22 | 2 | 2 | 0 |
| `evidence-bounded-vs-null-v1` | 23 | 4 | 1 | 0 |
| `evidence-bounded-vs-null-v2` | 24 | 2 | 0 | 0 |
| **Total** | **108** | **11** | **12** | **5** |

## Exact clean mechanical failures

Every clean failure below has `resolved: false` in the linked preserved
checker. In all 11 cases the checker records `R1: false`, `R2: true`, and
`G1: true`.

| Batch | Task | Arm | Attempt and mechanical evidence |
|---|---|---|---|
| `cost-time-probe-v1` | Click | No MD | [`attempt-3/checker.json`](../runs/dev-v2/cost-time-probe-v1/full-click-stream-lifecycle/null/attempt-3/checker.json) |
| `cost-time-probe-v1` | Click | Old MD | [`attempt-2/checker.json`](../runs/dev-v2/cost-time-probe-v1/full-click-stream-lifecycle/probe/attempt-2/checker.json) |
| `cost-time-probe-v1` | Starlette | Old MD | [`attempt-3/checker.json`](../runs/dev-v2/cost-time-probe-v1/full-starlette-websocket-denial/probe/attempt-3/checker.json) |
| `evidence-bounded-probe-v1` | Starlette | Old MD | [`attempt-2/checker.json`](../runs/dev-v2/evidence-bounded-probe-v1/full-starlette-websocket-denial/previous/attempt-2/checker.json) |
| `evidence-bounded-probe-v1` | Starlette | New MD | [`attempt-2/checker.json`](../runs/dev-v2/evidence-bounded-probe-v1/full-starlette-websocket-denial/evidence-bounded/attempt-2/checker.json) |
| `evidence-bounded-vs-null-v1` | Click | New MD | [`attempt-3/checker.json`](../runs/dev-v2/evidence-bounded-vs-null-v1/full-click-stream-lifecycle/evidence-bounded/attempt-3/checker.json) |
| `evidence-bounded-vs-null-v1` | Starlette | No MD | [`attempt-1/checker.json`](../runs/dev-v2/evidence-bounded-vs-null-v1/full-starlette-websocket-denial/null/attempt-1/checker.json) |
| `evidence-bounded-vs-null-v1` | Starlette | New MD | [`attempt-1/checker.json`](../runs/dev-v2/evidence-bounded-vs-null-v1/full-starlette-websocket-denial/evidence-bounded/attempt-1/checker.json) |
| `evidence-bounded-vs-null-v1` | Starlette | New MD | [`attempt-3/checker.json`](../runs/dev-v2/evidence-bounded-vs-null-v1/full-starlette-websocket-denial/evidence-bounded/attempt-3/checker.json) |
| `evidence-bounded-vs-null-v2` | Click | New MD | [`attempt-1/checker.json`](../runs/dev-v2/evidence-bounded-vs-null-v2/full-click-stream-lifecycle/evidence-bounded/attempt-1/checker.json) |
| `evidence-bounded-vs-null-v2` | Click | New MD | [`attempt-2/checker.json`](../runs/dev-v2/evidence-bounded-vs-null-v2/full-click-stream-lifecycle/evidence-bounded/attempt-2/checker.json) |

The historical pattern is therefore broader than the latest two Click misses.
Click has clean failures under all three arms. Starlette has clean failures
under all three arms. Only Boltons and Flask are clean historical ceilings.

## Exact contamination exclusions

The event scan found 51 completed provider `web_search` calls across seven
attempts and 42 completed GitHub MCP calls across five attempts. Completed web
calls in the older sealed batch did not persist response bodies, but subsequent
agent messages attributed specific solution facts to upstream results. The MCP
events persist answer-bearing GitHub structured content directly. The audit
therefore excludes all 12 attempts rather than attempting to estimate how much
each retrieval influenced the patch.

| Batch | Task | Arm | Attempt trace | Retrieval | Checker outcome |
|---|---|---|---|---:|---|
| `maximum-difficulty-sealed-v1` | Flask | No MD | [`attempt-1/events.jsonl`](../runs/dev-v2/maximum-difficulty-sealed-v1/full-flask-automatic-options/null/attempt-1/events.jsonl) | 3 web calls | Pass |
| `maximum-difficulty-sealed-v1` | Click | No MD | [`attempt-1/events.jsonl`](../runs/dev-v2/maximum-difficulty-sealed-v1/full-click-stream-lifecycle/null/attempt-1/events.jsonl) | 6 web calls | Pass |
| `maximum-difficulty-sealed-v1` | Click | No MD | [`attempt-2/events.jsonl`](../runs/dev-v2/maximum-difficulty-sealed-v1/full-click-stream-lifecycle/null/attempt-2/events.jsonl) | 10 web calls | Pass |
| `maximum-difficulty-sealed-v1` | Click | No MD | [`attempt-3/events.jsonl`](../runs/dev-v2/maximum-difficulty-sealed-v1/full-click-stream-lifecycle/null/attempt-3/events.jsonl) | 16 web calls | Pass |
| `maximum-difficulty-sealed-v1` | Starlette | No MD | [`attempt-1/events.jsonl`](../runs/dev-v2/maximum-difficulty-sealed-v1/full-starlette-websocket-denial/null/attempt-1/events.jsonl) | 4 web calls | Pass |
| `maximum-difficulty-sealed-v1` | Starlette | No MD | [`attempt-2/events.jsonl`](../runs/dev-v2/maximum-difficulty-sealed-v1/full-starlette-websocket-denial/null/attempt-2/events.jsonl) | 7 web calls | **Fail** |
| `maximum-difficulty-sealed-v1` | Starlette | No MD | [`attempt-3/events.jsonl`](../runs/dev-v2/maximum-difficulty-sealed-v1/full-starlette-websocket-denial/null/attempt-3/events.jsonl) | 5 web calls | Pass |
| `cost-time-probe-v1` | Click | Old MD | [`attempt-1/events.jsonl`](../runs/dev-v2/cost-time-probe-v1/full-click-stream-lifecycle/probe/attempt-1/events.jsonl) | 8 MCP calls | Pass |
| `cost-time-probe-v1` | Starlette | No MD | [`attempt-3/events.jsonl`](../runs/dev-v2/cost-time-probe-v1/full-starlette-websocket-denial/null/attempt-3/events.jsonl) | 4 MCP calls | Pass |
| `evidence-bounded-probe-v1` | Click | Old MD | [`attempt-1/events.jsonl`](../runs/dev-v2/evidence-bounded-probe-v1/full-click-stream-lifecycle/previous/attempt-1/events.jsonl) | 10 MCP calls | Pass |
| `evidence-bounded-probe-v1` | Click | Old MD | [`attempt-2/events.jsonl`](../runs/dev-v2/evidence-bounded-probe-v1/full-click-stream-lifecycle/previous/attempt-2/events.jsonl) | 11 MCP calls | Pass |
| `evidence-bounded-vs-null-v1` | Click | No MD | [`attempt-2/events.jsonl`](../runs/dev-v2/evidence-bounded-vs-null-v1/full-click-stream-lifecycle/null/attempt-2/events.jsonl) | 9 MCP calls | Pass |

No other relevant trace contains an MCP or provider-web item. The scan also
found no successful access to a private checker, reference solution,
evaluator output, or previous attempt.

## Included but flagged blocked lookups

These are included because the preserved command output proves that no
external answer bytes were returned:

| Batch | Task / arm / attempt | Attempted lookup | Preserved result |
|---|---|---|---|
| `maximum-difficulty-search-disabled-v2` | Click / no MD / [`attempt-3`](../runs/dev-v2/maximum-difficulty-search-disabled-v2/full-click-stream-lifecycle/null/attempt-3/events.jsonl) | `git ls-remote` against GitHub | Exit 128: proxy name could not resolve |
| `evidence-bounded-vs-null-v2` | Click / no MD / [`attempt-3`](../runs/dev-v2/evidence-bounded-vs-null-v2/full-click-stream-lifecycle/null/attempt-3/events.jsonl) | GitHub raw-file request through `curl`, then Python `urllib` | `curl` was absent; `urllib` failed DNS resolution |

Both attempts subsequently passed mechanically. An attempted lookup is a
behavioral warning, but it is not successful runtime cheating when it returns
no information.

## Excluded launches with no usable subject solution

All five are in `maximum-difficulty-search-disabled-v1` and use the no-MD hash.
None is counted as a run or fail:

| Task | Path | Why it is not a coding attempt |
|---|---|---|
| Click | [`attempt-1/events.jsonl`](../runs/dev-v2/maximum-difficulty-search-disabled-v1/full-click-stream-lifecycle/null/attempt-1/events.jsonl) | Authentication request failed before an agent message or edit; zero reported tokens |
| Click | [`attempt-2/events.jsonl`](../runs/dev-v2/maximum-difficulty-search-disabled-v1/full-click-stream-lifecycle/null/attempt-2/events.jsonl) | Authentication request failed before an agent message or edit; zero reported tokens |
| Click | [`attempt-3/events.jsonl`](../runs/dev-v2/maximum-difficulty-search-disabled-v1/full-click-stream-lifecycle/null/attempt-3/events.jsonl) | Authentication request failed before an agent message or edit; checker also became unscoreable; zero reported tokens |
| Starlette | [`attempt-1/infra-invalid.json`](../runs/dev-v2/maximum-difficulty-search-disabled-v1/full-starlette-websocket-denial/null/attempt-1/infra-invalid.json) | Runner infrastructure failure before a model response |
| Starlette | [`attempt-2/launch.json`](../runs/dev-v2/maximum-difficulty-search-disabled-v1/full-starlette-websocket-denial/null/attempt-2/launch.json) | Intent/launch/wrapper only; no event trace, capture, result, or subject solution |

Click attempts 1 and 2 were historically finalized with `valid: true` and
`resolved: false`, but their zero-token authentication traces show that those
flags describe an unchanged workspace, not failed coding work. Counting them
as model failures would answer the wrong question.

## Audit method and limits

The audit:

- enumerated 125 relevant `launch.json` files and 123 `result.json` files;
- verified the arm hash on every launch and result;
- mechanically counted every completed `web_search` and `mcp_tool_call` item;
- inspected external-network commands and their preserved outputs;
- checked suspicious filesystem, Git-object, installed-package, process, and
  protected-path searches for answer-bearing output; and
- took pass/fail only from preserved mechanical checker/result evidence.

The inventory answers **which preserved attempts show no observed runtime
cheating and how often each mechanically failed**. It does not make those
attempts statistically independent, erase task/candidate tuning, prove absence
of model-weight memorization, or authorize pooling them into a significance
test.
