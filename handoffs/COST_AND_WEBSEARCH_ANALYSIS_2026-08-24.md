# CODER.md cost and maximum-difficulty web-search analysis

Date: 2026-08-24

Evidence scope: the four existing batches named below. No live call or new
experiment was made for this analysis.

## Answer in one paragraph

The existing evidence does **not** establish that a CODER.md instruction file
changes run cost beyond ordinary run-to-run variation. It does show different
observed costs in the one direct comparison. On the single SignalNest task, with
three attempts per arm, the MD arm's median used 63,488 more cached input tokens,
104 more output tokens, and 3.968 more wall-clock seconds; the bare arm was
cheaper on those measures. The MD arm's median used 970 fewer uncached input
tokens and 25 fewer reasoning tokens; the MD arm was cheaper on those measures.
The uncached, output, reasoning, and duration ranges overlap between arms. Among
the requested component measures, cached input is the visibly separated pilot
metric; total input is also separated. The cached-input gap is within the
raw-token cache variation in the matched null repetitions and only 0.82
percentage point above their largest relative 3-vs-3 shift. The supplied null
evidence therefore does not cleanly separate any pilot gap from trajectory or
batch noise. This is a description of one task and is not a general CODER.md
effect estimate.

## Evidence and accounting

The direct comparison is
`runs/dev-v2/pilot-signalnest-pager-v1/`: one task, a zero-byte bare arm and a
3,059-byte treatment installed as `CODER.md`, with three attempts per arm. The
three context batches are:

- `runs/dev-v2/maximum-difficulty-sealed-v1/`: four tasks, three null-arm
  attempts each;
- `runs/dev-v2/phase3-real-null-sealed-v1/`: four tasks, three null-arm attempts
  each; and
- `runs/dev-v2/phase3-real-null-sealed-replication-v1/`: a fresh three-attempt
  null replication of the same four Phase 3 tasks.

All 42 expected attempt directories are complete. Every event stream has exactly
one `turn.completed` record with complete usage, and all attempt-manifest hashes
and ledger entries reconcile to disk. Every attempt records `valid=true`, return
code zero, no timeout, and no interruption. Every usage record reports zero
cache-write input tokens.

The calculations use these on-disk fields:

- input, cached input, output, and reasoning: the final
  `turn.completed.usage` object in `events.jsonl`;
- uncached input: `input_tokens - cached_input_tokens`, calculated per attempt;
  and
- wall clock: `result.json.duration_seconds`, the monotonic elapsed time around
  the subject invocation. It excludes separately recorded checker time.

The 36 sealed result files repeat the token values under `token_totals`; they
match the event streams exactly. Pilot result files omit that convenience copy,
so their event streams are authoritative. Cached input is already part of input,
and reasoning is a detail within output; neither is an extra category to add.
The repository's total-token convention is input plus output. No pricing schedule
or backend fingerprint is recorded, so “cheaper” below means fewer reported
tokens in the named category or less recorded wall time, not fewer dollars.

## Direct pilot comparison

### Per attempt

| Arm | Attempt | Total input | Uncached input | Cached input | Output | Reasoning | Wall clock (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| bare | 1 | 149,323 | 41,547 | 107,776 | 2,301 | 599 | 66.229 |
| bare | 2 | 163,922 | 36,178 | 127,744 | 2,922 | 969 | 80.878 |
| bare | 3 | 129,497 | 24,793 | 104,704 | 3,035 | 955 | 77.071 |
| MD | 1 | 207,827 | 34,771 | 173,056 | 3,026 | 930 | 81.039 |
| MD | 2 | 211,843 | 40,579 | 171,264 | 3,292 | 1,002 | 90.885 |
| MD | 3 | 173,192 | 35,208 | 137,984 | 2,884 | 689 | 75.437 |

### Arm medians and ranges

| Metric | Bare median [range] | MD median [range] |
|---|---:|---:|
| Total input | 149,323 [129,497–163,922] | 207,827 [173,192–211,843] |
| Uncached input | 36,178 [24,793–41,547] | 35,208 [34,771–40,579] |
| Cached input | 107,776 [104,704–127,744] | 171,264 [137,984–173,056] |
| Output | 2,922 [2,301–3,035] | 3,026 [2,884–3,292] |
| Reasoning | 955 [599–969] | 930 [689–1,002] |
| Wall clock | 77.071 s [66.229–80.878] | 81.039 s [75.437–90.885] |

Uncached values were calculated per attempt before taking the median. Component
medians can come from different attempts, so median cached plus median uncached
need not equal median total input.

### MD-minus-bare median deltas, with direction

Percentages use the bare median as denominator.

| Metric | MD minus bare | Plain direction |
|---|---:|---|
| Total input | +58,504 (+39.2%) | **Bare was cheaper:** 58,504 fewer total input tokens. |
| Uncached input | −970 (−2.7%) | **MD was cheaper:** 970 fewer uncached input tokens. |
| Cached input | +63,488 (+58.9%) | **Bare was cheaper:** 63,488 fewer cached input tokens. |
| Output | +104 (+3.6%) | **Bare was cheaper:** 104 fewer output tokens. |
| Reasoning | −25 (−2.6%) | **MD was cheaper:** 25 fewer reasoning tokens. |
| Wall clock | +3.968 s (+5.1%) | **Bare was cheaper:** 3.968 seconds faster. |

Every MD attempt had more total and cached input than every bare attempt. The
uncached-input, output, reasoning, and duration ranges overlap. Attempt ordinals
are repeats, not matched pairs.

### Three-attempt totals

The requested median reading is sensitive to one run when each arm has only
three attempts. Summing the three attempts gives a different direction for
uncached input and reasoning than comparing medians:

| Metric | Bare, all 3 | MD, all 3 | MD minus bare | Direction over all 3 runs |
|---|---:|---:|---:|---|
| Total input | 442,742 | 592,862 | +150,120 (+33.9%) | Bare used fewer. |
| Uncached input | 102,518 | 110,558 | +8,040 (+7.8%) | Bare used fewer. |
| Cached input | 340,224 | 482,304 | +142,080 (+41.8%) | Bare used fewer. |
| Output | 8,258 | 9,202 | +944 (+11.4%) | Bare used fewer. |
| Reasoning | 2,523 | 2,621 | +98 (+3.9%) | Bare used fewer. |
| Wall clock | 224.179 s | 247.361 s | +23.183 s (+10.3%) | Bare was faster. |

These totals do not supersede the requested medians. They show how unstable a
directional label is at three attempts per arm.

## Comparison with natural null variation

There are 36 sealed null attempts arranged as 12 same-task, same-batch
triplicates. The maximum-difficulty batch contributes four triplicates. The two
Phase 3 batches contribute eight triplicates and, more importantly, four
same-task original-versus-replication comparisons with three attempts on each
side.

Two descriptive noise views are reported:

1. **Within-triplicate span:** maximum minus minimum among three nominally
   identical attempts. This describes ordinary trajectory spread but is not the
   same statistic as a 3-vs-3 median delta.
2. **Matched 3-vs-3 drift:** absolute difference between each Phase 3 task's
   original three-run median and its replication three-run median. This is the
   closest available null analogue to the pilot comparison. It can include
   between-batch drift as well as stochastic trajectory variation.

### Absolute comparison

“At least pilot” counts null spans or null median shifts whose absolute size is
at least the absolute pilot MD-minus-bare median gap.

| Metric | Absolute pilot gap | Within-triplicate span: min / median / max | Cells at least pilot | Matched null 3-vs-3 gap: min / median / max | Tasks at least pilot |
|---|---:|---:|---:|---:|---:|
| Uncached input | 970 | 11,815 / 28,460.5 / 61,855 | 12/12 | 7,483 / 21,386 / 29,308 | 4/4 |
| Cached input | 63,488 | 41,728 / 291,072 / 2,231,040 | 10/12 | 50,176 / 140,544 / 333,056 | 3/4 |
| Output | 104 | 670 / 1,570 / 5,107 | 12/12 | 13 / 207.5 / 394 | 3/4 |
| Reasoning | 25 | 162 / 1,251.5 / 3,854 | 12/12 | 211 / 435 / 614 | 4/4 |
| Wall clock | 3.968 s | 17.463 / 55.261 / 232.757 s | 12/12 | 18.935 / 24.138 / 54.481 s | 4/4 |

### Proportional comparison

Absolute token variation scales with task length, so the same comparison in
percentages is also material. Pilot percentages use the bare median. Null
within-triplicate spans use the cell median; matched null gaps use the original
batch median.

| Metric | Absolute pilot gap | Within-triplicate relative span: min / median / max | Cells at least pilot | Matched null relative gap: min / median / max | Tasks at least pilot |
|---|---:|---:|---:|---:|---:|
| Uncached input | 2.68% | 12.11% / 51.23% / 86.76% | 12/12 | 10.62% / 40.65% / 81.60% | 4/4 |
| Cached input | 58.91% | 20.36% / 46.13% / 141.68% | 5/12 | 25.09% / 43.72% / 58.09% | 0/4 |
| Output | 3.56% | 10.38% / 24.77% / 67.42% | 12/12 | 0.21% / 3.41% / 6.06% | 2/4 |
| Reasoning | 2.62% | 7.17% / 38.44% / 115.84% | 12/12 | 5.88% / 12.95% / 21.83% | 4/4 |
| Wall clock | 5.15% | 12.79% / 29.05% / 57.71% | 12/12 | 11.37% / 15.93% / 28.95% | 4/4 |

The cached-input percentage is the only pilot gap just outside the four matched
relative null shifts: 58.91% versus a 58.09% maximum, a difference of 0.82
percentage point. Its raw-token gap lies inside the matched-null range; five of
12 within-triplicate relative cache spans and 10 of 12 raw cache spans are
larger. Cached-input share across the 36 null attempts ranges from 74.392% to
95.665%, and cached counts rise, fall, and reverse across attempt ordinals rather
than showing a consistent warm-up pattern.

Against the like-for-like repetitions, the pilot uncached-input, reasoning, and
wall-time gaps are smaller than every matched null gap. Output is inside the null
range. Cached input is inside the raw-token null range and only marginally past
the small four-task relative range. On these data, none is cleanly beyond noise.

### Signed Phase 3 original-to-replication shifts

This table shows the actual replication median minus original median, rather
than only absolute values.

| Task | Uncached input | Cached input | Output | Reasoning | Wall clock |
|---|---:|---:|---:|---:|---:|
| `real-boltons-indexed-slice` | +16,255 | +50,176 | −13 | −211 | +18.935 s |
| `real-cpython-doctest-notes` | +29,308 | +333,056 | +394 | +614 | +54.481 s |
| `real-cpython-enum-lookup` | +26,517 | +145,152 | −105 | −267 | +19.877 s |
| `real-tomli-dotted-keys` | +7,483 | −135,936 | +310 | −603 | +28.399 s |

Replication has higher uncached-input and wall medians on all four tasks, so
this comparator includes a possible common between-batch shift. Cached, output,
and reasoning directions are mixed. It is contextual evidence, not an
inferential null distribution.

### Null task-by-batch medians and ranges

| Batch | Task | Uncached median [range] | Cached median [range] | Output median [range] | Reasoning median [range] | Wall median [range], s |
|---|---|---:|---:|---:|---:|---:|
| maximum | `full-boltons-wraps-forwarding` | 71,298 [68,228–130,083] | 900,352 [444,672–1,084,928] | 13,514 [12,998–15,689] | 7,036 [7,022–8,433] | 427.810 [334.024–566.780] |
| maximum | `full-click-stream-lifecycle` | 120,043 [98,952–157,859] | 1,574,656 [1,252,864–3,483,904] | 9,979 [9,396–13,530] | 5,054 [4,481–6,616] | 318.783 [280.161–429.571] |
| maximum | `full-flask-automatic-options` | 52,627 [43,092–67,451] | 326,912 [231,936–423,680] | 5,076 [4,598–5,268] | 2,623 [1,610–2,702] | 142.741 [135.202–159.113] |
| maximum | `full-starlette-websocket-denial` | 97,560 [90,116–101,931] | 1,206,272 [1,045,504–1,319,168] | 9,654 [6,564–9,906] | 3,981 [2,417–4,175] | 259.783 [175.005–263.158] |
| Phase 3 original | `real-boltons-indexed-slice` | 41,208 [32,013–59,482] | 164,608 [131,072–172,800] | 6,145 [5,507–6,886] | 3,588 [2,731–4,526] | 166.596 [135.909–174.226] |
| Phase 3 original | `real-cpython-doctest-notes` | 70,036 [61,842–89,137] | 584,704 [546,816–665,856] | 6,500 [5,728–7,489] | 2,812 [2,246–3,237] | 188.196 [167.309–197.026] |
| Phase 3 original | `real-cpython-enum-lookup` | 32,495 [20,250–46,516] | 249,856 [179,456–263,424] | 4,125 [4,119–5,312] | 2,527 [2,345–2,890] | 116.648 [115.328–143.523] |
| Phase 3 original | `real-tomli-dotted-keys` | 70,449 [68,010–97,462] | 541,696 [422,400–1,115,648] | 7,265 [6,584–7,338] | 3,930 [3,202–4,000] | 191.501 [178.319–221.913] |
| Phase 3 replication | `real-boltons-indexed-slice` | 57,463 [32,516–63,198] | 214,784 [184,832–247,296] | 6,132 [5,156–6,216] | 3,377 [2,819–3,675] | 185.531 [150.991–217.919] |
| Phase 3 replication | `real-cpython-doctest-notes` | 99,344 [70,567–125,681] | 917,760 [627,712–936,192] | 6,894 [6,133–8,960] | 3,426 [2,350–4,990] | 242.677 [176.247–283.113] |
| Phase 3 replication | `real-cpython-enum-lookup` | 59,012 [28,589–79,743] | 395,008 [157,184–489,728] | 4,020 [3,926–4,619] | 2,260 [2,244–2,406] | 136.525 [124.111–141.575] |
| Phase 3 replication | `real-tomli-dotted-keys` | 77,932 [62,709–81,483] | 405,760 [338,688–797,440] | 7,575 [5,745–10,852] | 3,327 [2,692–6,546] | 219.900 [175.114–302.015] |

## Web-search audit of all 12 maximum-difficulty attempts

### Verdict

The web-search subsystem was **not behaviorally inert**, but its preserved
evidence is incomplete. There are 51 completed `web_search` calls in seven of
the 12 attempts. Every actual call is a same-ID `item.started` /
`item.completed` pair. The started record has placeholder `query:""` and
`action:{"type":"other"}` values; the completed record contains the real action
and is what is counted below.

Across all 51 completed items, the item keys are exactly `action`, `id`, `query`,
and `type`. Actions contain only `type` and, for searches, `query` or `queries`.
There is no `results`, `content`, `output`, `text`, response body, snippet, title,
source, citation, status, or error field; there is no separate result event; and
the relevant `stderr.txt` files are empty. Therefore **no raw web-response
content was serialized into the preserved JSONL transcript, and the exact pages
or snippets returned cannot be reconstructed from disk**.

Nevertheless, the sequence strongly indicates that returned information entered
the model's working context and then affected recorded behavior. Generic
searches are followed by previously absent PR numbers, commit identifiers, and
exact API URLs, and the agent explicitly attributes technical conclusions to
upstream material. The clearest trace is
Starlette attempt 2: a broad search is followed by PR 3189, a short commit URL,
and then the previously unseen full SHA
`9ee951980bae776103715b66305f807d9e8245da` in a GitHub API request. The next
agent message describes the “authoritative upstream fix.” Thus the careful
answer is: **raw returned text in the on-disk transcript, no; response-derived
identifiers and paraphrased conclusions later in the transcript, strongly
indicated; overall verdict, non-inert**.

### All-attempt coverage

| Task | Attempt | Completed calls | Persisted raw return | Behavioral reading |
|---|---:|---:|---|---|
| `full-boltons-wraps-forwarding` | 1 | 0 | N/A | No web interaction. |
| `full-boltons-wraps-forwarding` | 2 | 0 | N/A | No web interaction. |
| `full-boltons-wraps-forwarding` | 3 | 0 | N/A | No web interaction. |
| `full-click-stream-lifecycle` | 1 | 6 | None; query/action metadata only | Non-inert evidence. |
| `full-click-stream-lifecycle` | 2 | 10 | None; query/action metadata only | Non-inert evidence. |
| `full-click-stream-lifecycle` | 3 | 16 | None; query/action metadata only | Non-inert evidence. |
| `full-flask-automatic-options` | 1 | 3 | None; query/action metadata only | Non-inert as recorded behavior; exact web contribution is not isolatable from local evidence. |
| `full-flask-automatic-options` | 2 | 0 | N/A | No web interaction. |
| `full-flask-automatic-options` | 3 | 0 | N/A | No web interaction. |
| `full-starlette-websocket-denial` | 1 | 4 | None; query/action metadata only | Non-inert evidence. |
| `full-starlette-websocket-denial` | 2 | 7 | None; query/action metadata only | Non-inert; strongest hidden-context trace. |
| `full-starlette-websocket-denial` | 3 | 5 | None; query/action metadata only | Non-inert evidence. |

### Exact Click call inventory

Path prefix:
`runs/dev-v2/maximum-difficulty-sealed-v1/full-click-stream-lifecycle/null/`.
Each row reports the completed item's exact query and/or action payload. “Other”
is the event exporter's label; the evidence does not preserve a more specific
operation or a response body.

#### Click attempt 1 — 6 calls

| Event lines | Exact query or action |
|---|---|
| 18–19 | Search: ``site:github.com/pallets/click "Preserve CliRunner stream lifecycles"``; ``site:github.com/pallets/click StreamMixer _NamedTextIOWrapper detach close buffer CliRunner`` |
| 20–21 | Other: ``https://github.com/pallets/click/pull/3139/files`` |
| 22–23 | Search: ``pallets click PR 3139 _NamedTextIOWrapper close detach source code``; ``pallets click PR 3140 _NamedTextIOWrapper close source code`` |
| 24–25 | Other: ``https://github.com/pallets/click/blob/8.3.2/src/click/testing.py`` |
| 32–33 | Other: ``https://raw.githubusercontent.com/pallets/click/8.3.2/src/click/testing.py`` |
| 38–39 | Search: ``"test_stream_mixer" "_NamedTextIOWrapper" click 3139``; ``"logging" "StreamMixer" "CliRunner" "3139"``; ``"sequential invocation isolation" "CliRunner" tests`` |

The initial search does not contain `3139`; the next completed action opens PR
3139. Later the agent says:

> “I’ve matched the upstream ownership model: `StreamMixer` must not finalize
> buffers that callers still hold, and `_NamedTextIOWrapper.close()` must be
> intentionally non-owning.”

No upstream body or citation is preserved.

#### Click attempt 2 — 10 calls

| Event lines | Exact query or action |
|---|---|
| 15–16 | Search: ``site:github.com/pallets/click "Preserve `CliRunner` stream lifecycles"``; ``site:github.com/pallets/click _NamedTextIOWrapper detach StreamMixer __del__`` |
| 17–18 | Other: ``https://github.com/pallets/click/pull/3139`` |
| 19–20 | Other: ``https://github.com/pallets/click/pull/3139/files`` |
| 21–22 | Search: ``site:github.com/pallets/click/pull/3139 _NamedTextIOWrapper``; ``site:github.com/pallets/click/pull/3140 _NamedTextIOWrapper``; ``site:github.com/pallets/click "test_stream_mixer" "logging"``; ``site:github.com/pallets/click "def close(self)" "_NamedTextIOWrapper"`` |
| 23–24 | Search: ``"Add comprehensive tests for `CliRunner` stream lifecycle"``; ``"Prevent `_NamedTextIOWrapper` from closing streams owned by `StreamMixer`"``; ``"sequential invocation isolation" "CliRunner"`` |
| 27–28 | Other: ``https://github.com/pallets/click/issues/3110`` |
| 29–30 | Other: empty recorded query. |
| 31–32 | Other: empty recorded query. |
| 33–34 | Search: ``github pallets click d8e987eae723fbb0ccc355d125d0e179a1bf5fd8``; ``github pallets click 777a89e232d5771141be545ff749a7ad2eaa5fc2``; ``github pallets click ae46cfd NamedTextIOWrapper`` |
| 35–36 | Search: ``site:github.com/pallets/click/blob/8.3.2/tests "StreamMixer" "gc.collect"``; ``site:github.com/pallets/click/blob/8.3.2/tests "CliRunner" "ThreadPoolExecutor"``; ``site:github.com/pallets/click/blob/8.3.2/tests "stream lifecycle"``; ``site:github.com/pallets/click/blob/8.3.2/tests "test_runner_logger"`` |

The full hashes at line 34 occur nowhere earlier in this attempt's transcript or
recorded command output. The next agent message says:

> “Upstream confirms the root cause is dual ownership: both
> `StreamMixer.__del__` and `TextIOWrapper` finalization close the same buffers.”

#### Click attempt 3 — 16 calls

| Event lines | Exact query or action |
|---|---|
| 17–18 | Search: ``site:github.com/pallets/click _NamedTextIOWrapper detach StreamMixer``; ``site:github.com/pallets/click "Preserve CliRunner stream lifecycles"``; ``site:github.com/pallets/click "I/O operation on closed file" CliRunner`` |
| 19–20 | Other: ``https://github.com/pallets/click/pull/3482`` |
| 21–22 | Other: empty recorded query. |
| 23–24 | Search: ``site:github.com/pallets/click/pull "does not close its underlying buffer"``; ``site:github.com/pallets/click "prevent the default __del__ implementation"``; ``site:github.com/pallets/click/pull StreamMixer "_NamedTextIOWrapper" close`` |
| 25–26 | Other: empty recorded query. |
| 27–28 | Search: ``site:github.com/pallets/click "NamedTextIOWrapper" "versionadded:: 8.3.2"``; ``site:github.com/pallets/click "underlying buffer" CliRunner 8.3.2``; ``site:github.com/pallets/click/pull "StreamMixer" "close" 8.3`` |
| 29–30 | Search: ``site:github.com/pallets/click/commit "does not close its underlying buffer"``; ``site:github.com/pallets/click/pull "GC" "_NamedTextIOWrapper"``; ``site:github.com/pallets/click/issues "multiple wrappers" "buffer" CliRunner`` |
| 53–54 | Search: ``"StreamMixer-owned" stdout stderr mixed-output buffers``; ``"multiple wrappers share that buffer" Click``; ``"CliRunner" "logging handlers" "closed file" Click`` |
| 55–56 | Other: ``https://github.com/pallets/click/pull/3139`` |
| 57–58 | Other: ``https://github.com/pallets/click/commit/ae46cfd.patch`` |
| 59–60 | Other: ``https://raw.githubusercontent.com/pallets/click/8.3.2/tests/test_testing.py`` |
| 61–62 | Other: empty recorded query. |
| 63–64 | Search: ``"test_runner_logger" "test_testing_logging.py" Click``; ``"Add regular and stress tests" "CliRunner" stream lifecycle``; ``"777a89e232d5771141be545ff749a7ad2eaa5fc2"`` |
| 65–66 | Other: ``https://api.github.com/repos/pallets/click/commits/777a89e232d5771141be545ff749a7ad2eaa5fc2`` |
| 67–68 | Search: ``api.github.com repos pallets click commits 777a89e`` |
| 69–70 | Other: ``https://github.com/pallets/click/issues/3110`` |

This attempt queried the full upstream commit ID
`777a89e232d5771141be545ff749a7ad2eaa5fc2` verbatim and then used it in an
exact API URL. The agent's messages include:

> “Upstream’s current lifecycle model is clear: the named text wrapper’s
> `close()` is intentionally a no-op because it borrows its buffer, and
> `StreamMixer` no longer owns a destructor that closes captured buffers.”

and later:

> “The upstream regression history confirms this exact fix also addresses the
> retained logging-handler and threaded-finalization failures.”

### Exact Flask call inventory

Only `full-flask-automatic-options/null/attempt-1/events.jsonl` has calls.

| Event lines | Exact query or action |
|---|---|
| 16–17 | Search: ``site:github.com/pallets/flask "Make explicit automatic `OPTIONS` enablement effective"``; ``site:github.com/pallets/flask "PROVIDE_AUTOMATIC_OPTIONS" "provide_automatic_options"`` |
| 18–19 | Other: empty recorded query. |
| 20–21 | Other: ``'required_methods.add'`` |

Line 22 says:

> “Upstream confirms the intended registration rule: derive the global default
> only when no explicit value exists, then add `OPTIONS` whenever the resolved
> value is true.”

The agent treated the calls as confirmation and acted next. That rule is also
inferable from the locally inspected source and contract, so the exact web
contribution cannot be isolated. Flask attempts 2 and 3 have no web calls.

### Exact Starlette call inventory

Path prefix:
`runs/dev-v2/maximum-difficulty-sealed-v1/full-starlette-websocket-denial/null/`.

#### Starlette attempt 1 — 4 calls

| Event lines | Exact query or action |
|---|---|
| 14–15 | Search: ``site:github.com/encode/starlette "Preserve streamed WebSocket denial responses"``; ``site:github.com/encode/starlette StreamingResponse websocket.http.response.start FileResponse denial``; ``site:github.com/encode/starlette websocket denial StreamingResponse FileResponse`` |
| 16–17 | Search: ``site:github.com/Kludex/starlette "_wrap_websocket_denial_send"``; ``site:github.com/Kludex/starlette/pull "websocket denial" FileResponse StreamingResponse``; ``site:github.com/Kludex/starlette/commit "_wrap_websocket_denial_send"`` |
| 18–19 | Other: ``https://github.com/Kludex/starlette/pull/3189`` |
| 20–21 | Other: empty recorded query. |

After only a local `git status/diff` at lines 22–23, line 24 says:

> “Upstream’s merged fix (#3189) matches the contract exactly.”

The message then describes the shared send wrapper, direct streaming denial
path, one-time background execution, and HTTP-only HEAD/pathsend gating.

#### Starlette attempt 2 — 7 calls

| Event lines | Exact query or action |
|---|---|
| 33–34 | Search: ``site:github.com/Kludex/starlette "Preserve streamed WebSocket denial responses"``; ``site:github.com/Kludex/starlette websocket denial StreamingResponse FileResponse``; ``site:github.com/Kludex/starlette "websocket.http.response.body" "FileResponse"`` |
| 35–36 | Search: ``site:github.com/Kludex/starlette "_wrap_websocket_denial_send"``; ``site:github.com/Kludex/starlette/pull "websocket denial" StreamingResponse FileResponse``; ``site:github.com/Kludex/starlette/commit "_wrap_websocket_denial_send"`` |
| 37–38 | Other: ``https://github.com/Kludex/starlette/pull/3189`` |
| 39–40 | Other: ``https://github.com/Kludex/starlette/commit/9ee9519.patch`` |
| 41–42 | Other: empty recorded query. |
| 43–44 | Search: ``site:github.com/Kludex/starlette/blob/main/tests/test_websockets.py "StreamingResponse"``; ``site:github.com/Kludex/starlette/blob/main/tests/test_websockets.py "FileResponse"``; ``site:github.com/Kludex/starlette "test_send_denial_response" "background"`` |
| 45–46 | Other: ``https://api.github.com/repos/Kludex/starlette/commits/9ee951980bae776103715b66305f807d9e8245da`` |

The full 40-character SHA first appears at line 46, after the broad searches, PR
navigation, short commit URL, and opaque action. It is absent from lines 1–45 and
the attempt's other artifacts. Line 47 says:

> “The authoritative upstream fix centralizes event translation in `Response`,
> gives `StreamingResponse` a WebSocket-specific path that avoids HTTP
> disconnect polling, and gates `FileResponse`’s HEAD/pathsend checks to HTTP
> scopes.”

This is the clearest evidence supporting the inference that unpersisted
web-return content supplied information used later in the run.

#### Starlette attempt 3 — 5 calls

| Event lines | Exact query or action |
|---|---|
| 18–19 | Search: ``site:github.com/Kludex/starlette "Preserve streamed WebSocket denial responses"``; ``site:github.com/Kludex/starlette StreamingResponse FileResponse websocket denial response`` |
| 20–21 | Other: ``https://raw.githubusercontent.com/Kludex/starlette/main/starlette/responses.py`` |
| 22–23 | Other: ``'websocket'`` |
| 24–25 | Search: ``site:github.com/Kludex/starlette "_wrap_websocket_denial_send"``; ``site:github.com/Kludex/starlette "test_streaming_response_runs_background_on_websocket_scope"`` |
| 26–27 | Other: ``https://github.com/Kludex/starlette/commit/9ee9519`` |

Lines 28–29 inspect only local tests. Line 30 says:

> “Upstream’s correction centralizes protocol translation in `Response`:
> specialized responses keep their established HTTP send paths, while a
> WebSocket scope wraps `send` to translate only `http.response.start/body`
> into `websocket.http.response.start/body`.”

It then describes response-event translation, the WebSocket-specific streaming
path, and HTTP-only `FileResponse` gates. No raw upstream response is present.

## Caveats

- The only direct with-MD versus without-MD evidence is one task with three
  attempts per arm. It is too small to estimate repeatability or a population
  effect.
- The pilot used deterministic interleaving—bare 1, MD 1, MD 2, bare 2, bare 3,
  MD 3—not randomized arm assignment. With one task, its task-order seed does
  not meaningfully randomize arms.
- The pilot ran unsealed on the host. It had the Codex `workspace-write`
  sandbox and agent-command network disabled, but no sealed container or sealed
  preflight. The 36 context attempts ran in sealed containers. Their variance
  is context, not a matched pilot control.
- Maximum-difficulty used different tasks and a 600-second timeout; its own
  request records this as a comparability boundary with the 300-second pilot and
  Phase 3 batches.
- The Phase 3 original and replication are the closest null repetitions: same
  task manifests, null arm, model label, reasoning effort, wrapper, container
  digest/spec/interpreter bindings, and 300-second runner settings. They are
  still only four task-level comparisons and can include between-batch drift.
- Within-run behavior is stochastic. Whole-run cumulative token usage reflects
  both static context and the agent's chosen trajectory, repeated context,
  commands, and messages. It cannot isolate the direct ingestion cost of the
  401-word instruction file from behavior that the file may have changed.
- The evidence does not distinguish within-run prefix-cache reuse from
  cross-attempt cache state. Cached-input counts are especially volatile in the
  supplied nulls.
- Reasoning tokens are part of output accounting and must not be added again.
  Component medians are not additive.
- The evidence records a model name but no backend revision, fingerprint, or
  price schedule. It supports token and elapsed-time descriptions, not dollar
  costs or future-model claims.
- Raw web-return bodies were not captured. The non-inert verdict rests on event
  sequences, previously absent identifiers in later calls, and explicit agent
  attribution. Exact returned snippets/pages and their precise contribution to
  each patch cannot be reconstructed.
- Nothing here generalizes beyond this task, this treatment file, this recorded
  model/configuration, and these batches.

## Appendix: all 36 null attempts

| Batch | Task | Attempt | Uncached input | Cached input | Output | Reasoning | Wall (s) |
|---|---|---:|---:|---:|---:|---:|---:|
| maximum | `full-boltons-wraps-forwarding` | 1 | 68,228 | 1,084,928 | 15,689 | 7,022 | 427.810 |
| maximum | `full-boltons-wraps-forwarding` | 2 | 130,083 | 900,352 | 12,998 | 7,036 | 566.780 |
| maximum | `full-boltons-wraps-forwarding` | 3 | 71,298 | 444,672 | 13,514 | 8,433 | 334.024 |
| maximum | `full-click-stream-lifecycle` | 1 | 98,952 | 1,252,864 | 9,979 | 5,054 | 318.783 |
| maximum | `full-click-stream-lifecycle` | 2 | 120,043 | 1,574,656 | 9,396 | 4,481 | 280.161 |
| maximum | `full-click-stream-lifecycle` | 3 | 157,859 | 3,483,904 | 13,530 | 6,616 | 429.571 |
| maximum | `full-flask-automatic-options` | 1 | 67,451 | 423,680 | 4,598 | 1,610 | 135.202 |
| maximum | `full-flask-automatic-options` | 2 | 43,092 | 326,912 | 5,076 | 2,623 | 159.113 |
| maximum | `full-flask-automatic-options` | 3 | 52,627 | 231,936 | 5,268 | 2,702 | 142.741 |
| maximum | `full-starlette-websocket-denial` | 1 | 90,116 | 1,045,504 | 6,564 | 2,417 | 175.005 |
| maximum | `full-starlette-websocket-denial` | 2 | 97,560 | 1,206,272 | 9,906 | 3,981 | 259.783 |
| maximum | `full-starlette-websocket-denial` | 3 | 101,931 | 1,319,168 | 9,654 | 4,175 | 263.158 |
| Phase 3 original | `real-boltons-indexed-slice` | 1 | 32,013 | 164,608 | 6,886 | 4,526 | 174.226 |
| Phase 3 original | `real-boltons-indexed-slice` | 2 | 41,208 | 131,072 | 5,507 | 2,731 | 135.909 |
| Phase 3 original | `real-boltons-indexed-slice` | 3 | 59,482 | 172,800 | 6,145 | 3,588 | 166.596 |
| Phase 3 original | `real-cpython-doctest-notes` | 1 | 70,036 | 546,816 | 5,728 | 2,246 | 167.309 |
| Phase 3 original | `real-cpython-doctest-notes` | 2 | 61,842 | 584,704 | 7,489 | 3,237 | 188.196 |
| Phase 3 original | `real-cpython-doctest-notes` | 3 | 89,137 | 665,856 | 6,500 | 2,812 | 197.026 |
| Phase 3 original | `real-cpython-enum-lookup` | 1 | 20,250 | 263,424 | 5,312 | 2,890 | 143.523 |
| Phase 3 original | `real-cpython-enum-lookup` | 2 | 46,516 | 249,856 | 4,125 | 2,527 | 116.648 |
| Phase 3 original | `real-cpython-enum-lookup` | 3 | 32,495 | 179,456 | 4,119 | 2,345 | 115.328 |
| Phase 3 original | `real-tomli-dotted-keys` | 1 | 68,010 | 541,696 | 7,265 | 4,000 | 191.501 |
| Phase 3 original | `real-tomli-dotted-keys` | 2 | 70,449 | 422,400 | 6,584 | 3,202 | 178.319 |
| Phase 3 original | `real-tomli-dotted-keys` | 3 | 97,462 | 1,115,648 | 7,338 | 3,930 | 221.913 |
| Phase 3 replication | `real-boltons-indexed-slice` | 1 | 32,516 | 214,784 | 6,216 | 3,675 | 185.531 |
| Phase 3 replication | `real-boltons-indexed-slice` | 2 | 63,198 | 247,296 | 6,132 | 3,377 | 217.919 |
| Phase 3 replication | `real-boltons-indexed-slice` | 3 | 57,463 | 184,832 | 5,156 | 2,819 | 150.991 |
| Phase 3 replication | `real-cpython-doctest-notes` | 1 | 70,567 | 627,712 | 6,133 | 2,350 | 176.247 |
| Phase 3 replication | `real-cpython-doctest-notes` | 2 | 125,681 | 917,760 | 6,894 | 3,426 | 242.677 |
| Phase 3 replication | `real-cpython-doctest-notes` | 3 | 99,344 | 936,192 | 8,960 | 4,990 | 283.113 |
| Phase 3 replication | `real-cpython-enum-lookup` | 1 | 59,012 | 489,728 | 4,619 | 2,260 | 141.575 |
| Phase 3 replication | `real-cpython-enum-lookup` | 2 | 28,589 | 157,184 | 4,020 | 2,406 | 124.111 |
| Phase 3 replication | `real-cpython-enum-lookup` | 3 | 79,743 | 395,008 | 3,926 | 2,244 | 136.525 |
| Phase 3 replication | `real-tomli-dotted-keys` | 1 | 62,709 | 338,688 | 10,852 | 6,546 | 302.015 |
| Phase 3 replication | `real-tomli-dotted-keys` | 2 | 77,932 | 405,760 | 5,745 | 2,692 | 175.114 |
| Phase 3 replication | `real-tomli-dotted-keys` | 3 | 81,483 | 797,440 | 7,575 | 3,327 | 219.900 |
