# Process & Science Findings — 2026-08-19

Status of record. Not a plan; nothing here authorizes anything. Written so findings
survive session resets and context compaction.

## 1. Complete live-result ledger (every task ever run against gpt-5.6-sol)

| Cohort | Task | Checker sound? | Live result | Meaning |
|---|---|---|---|---|
| M2 v0.4/v0.4.1 (240 calls) | 14 of 20 tasks | yes | 6/6 twice | ceiling |
| M2 v0.4/v0.4.1 | 6 of 20 tasks | NO (hidden reqs) | 0/6 | invalid floors |
| M2 v0.4/v0.4.1 | integration-01 | NO (byte-exact JSON) | 1/6, 2/6 | formatting lottery |
| scout-v1 (18 calls) | 4 tasks | yes | 3/3 | ceiling |
| scout-v1 | 2 tasks (author-a) | NO (scope routing) | 0/3 | invalid floors |
| rolling-01 | eventrollup | NO (counted git metadata) | invalid | checker defect |
| rolling-02 | — | NO (unpublished sys import) | invalid | checker defect |
| rolling-03 | badge tool | yes | 3/3, q=1.0 | ceiling |
| rolling-05 (= Claude trial task A, durafmt) | yes | 3/3 | ceiling |
| rolling-06 (= Claude trial task B, logscan) | NO (hidden constraint found at live disposition) | 1/3 | INVALID — but first intermediate result ever observed |

**Headline finding 1 (CORRECTED 2026-08-19 evening):** nearly every checker-sound
task ever run is a ceiling — but not all. scout-c-integration-01 is a sound task
(fidelity_defect: false) that scored q=0.9167, 1/3 resolved: the model omitted a
stated requirement (I7, an added test, published in tests/test_cli.py) on 2 of 3
attempts. This is the existence proof for a legitimate intermediate band.

**Headline finding 1b — the actual difficulty dial is CONTRACT SALIENCE, not
dispersion or time.** Regression across 153 live attempts: tasks whose contracts
enumerate every in-scope file and value → 100% requirement coverage regardless of
requirement count (rolling-06: 11 reqs across 9 files, 33/33). Contracts with a
general-but-honest pointer ("read every SCOUT-C-* note") → intermediate (22/24).
Contracts with no pointer at all → floor (scout-a: 9/24, 6/24 — but ruled a
scope-routing defect because the wrapper contradicted it). Time is NOT a dial:
zero timeouts in 153 attempts, worst case 66% of budget, ~10s per extra
requirement, budget binds only near ~20+ requirements.

**Headline finding 2:** the only intermediate result (rolling-06, 1/3) was produced
by a hidden checker constraint — i.e., so far "intermediate difficulty" has only
ever been an artifact of checker unsoundness. Untested hypothesis: low-salience
(untagged, prose-woven) requirements may produce legitimate intermediacy. Factory
tasks 07, 08, 09, 11, 12 are built this way and have never been run live.

**Headline finding 3:** checker defects survive layered review. Rolling-06 passed:
Claude's blind-solve gate, the gatekeeper's audit AND repair, and a second fresh
blind solve — and was still invalidated live. Blind solves catch most defects
(would have caught 6/20 of the v0.4 pool offline) but not all; the three live
null attempts double as the final fidelity probe. Plan for per-task attrition at
every stage; never assume admission = validity.

## 2. Throughput accounting (the process crisis)

Production (Claude factory, 2026-08-19): 12 parallel author lanes → 11 structurally
valid tasks in ~35 min wall-clock; 2 fully blind-validated. Marginal cost per valid
task ≈ minutes. Scripted gate (factory/gate.py) validates a task in seconds.

Consumption (other session's admission): ~hours per candidate. Observed stages:
re-audit of provenance, re-run of blind solves under role-rotation rows (candidate 5
was blind-solved 3 separate times), checker repair serialization behind a single
gatekeeper, per-candidate cap/authorization requests to the user, one candidate lost
entirely to context compaction (candidate 4 — bytes lived only in conversation).

**Conclusion: the bottleneck is consumption, not production, by ~2 orders of
magnitude.** Producing more tasks (including the 11 waiting in the factory) changes
nothing until the consumption path is replaced.

Also real: session usage limits. A 12-wide agent burst exhausted the session budget
instantly. Sustainable cadence is ~2 concurrent agents, or metered API billing for
lane work.

## 3. What the process should become

Development phase needs exactly two things per task; everything else is overhead:
1. OFFLINE VALIDITY, scripted, seconds: checker vs pristine (must fail), vs
   reference (must resolve), vs a contract-only blind solution (must resolve),
   plus per-requirement omission mutants. Hash the frozen bytes. Done.
2. LIVE CALIBRATION, three null attempts, batched: label promising/ceiling/floor,
   preserve raw logs and denominators, no retries, frozen bytes after exposure.

Explicitly dropped for development (each caused a documented stall): single
gatekeeper as sole editor; role-rotation rows; per-candidate user approvals;
narrative receipts; re-audits of already-scripted gates; terminal stops for
pre-exposure issues; conversation-held artifacts. Confirmatory experiments keep
the full v0.4 evidence machinery — it worked; it belongs there, not in development.

The other session's remaining useful role: run live calls (it holds the runner and
egress authorization) on tasks that arrive pre-validated, and record dispositions.
If its admission cannot shrink to "verify hashes, run 3 calls, record label," move
the runner instead.

## 4. The open scientific question (process cannot answer it)

ANSWERED in part (2026-08-19 evening investigations):
- A legitimate band exists (scout-c-integration-01, sound, q=0.9167). The dial is
  contract salience: general-honest-pointer contracts, not enumerated ones.
- Time/repo-size dials are REJECTED by evidence (zero timeouts in 153 attempts).
- The +0.20 M2 gate is unreachable: sound-task null rates ~1.0 bound the effect
  at ≤0 on current pools, and literature effect sizes (+0.05 typical, positive
  directives weakest) sit ~4x below the gate. Gate was set with no pilot.

Remaining probes, in cost order:
1. ~3 calls: clone rolling-v1-05 (durafmt, sound, 30/30) minus ONLY the contract
   sentence enumerating docs/upgrading.md as in scope; checker/reference bytes
   unchanged. If q drops below 1.0 → salience dial confirmed and calibratable.
2. 15 calls: the 5 low-salience factory tasks (07,08,09,11,12 — general pointer,
   no tags/enumeration) → measures the band's width across families/authors.
3. ~24-32 calls: mini N-vs-P contrast on whatever lands in band — the first
   direct test of whether an instruction file moves omission-driven resolution.
   Mechanism-matched treatment: the observed failure mode is "peripheral files
   never read", which is exactly what a coverage instruction targets; but Zhang/
   Khatri predict small effects for positive directives, so this is a genuine
   coin-flip, not a formality.

Goal verdict: as specified (+0.20 helpful gate), M2 fails on arithmetic. The
product (keep-or-replace benchmark, AGENTS.md) remains ~2/3 deliverable today:
harm/regression detection works at ceilings (gross harm only — a subtly-bad MD
produced zero mechanical harm in runs/bad-control-20260731-2), cost/efficiency
comparison is already in the telemetry (token_duration_comparison existed in v1),
and the null bound ("coder.md cannot improve resolution on saturated task
classes") is a clean product finding needing only an equivalence-margin amendment.
The beneficial-sensitivity claim proper is OPEN pending probes 1-3 (~50 calls).

## 5. Asset inventory (where things are)

- 11 valid factory tasks + gate script: scratchpad factory/ (session-local; copy
  out before session end if wanted) — task-11 checker truncated, needs small repair.
- 2 fully-validated trial tasks: handoffs/claude-trial-tasks-ab.tar (A=rolling-05
  ran ceiling; B=rolling-06 invalidated — both now outcome-exposed, dev-only).
- Factory process spec: handoffs/TASK_FACTORY_V2_PROPOSAL.md.
- Campaign evidence: runs/development/coder-beneficial-sensitivity-m2/rolling-v1/.
- Full postmortem of the pre-reset era: M2_INDEPENDENT_SCIENTIFIC_REVIEW.md plus
  the failure ledger reconstructed 2026-08-18 (13 failures: 3 scientific, 4
  task/checker, 6 infra/process; 258 live calls, 93% yielding no usable evidence).

## 6. Phase 3 real-issue headroom hunt — 2026-08-22

Yield: 6 repositories screened → 56 issues considered → 5 candidates
reconstructed → 4 admitted → 0 showing provisional headroom. The fifth
reconstruction, real-cpython-urljoin-relative, exhausted the three-run blindsolve
cap before exposure and was not admitted.

The admitted cohort was run in the hash-approved null scout
`phase3-real-null-scout-v1` (`REQUEST.json` SHA-256
`cc9bacd05bbb506455cee9b7feae439ce74dba9666dd1fc110732555dee6f12c`).
The batch used exactly 12 subject calls and no replacements. `run_batch verify`
passed before interpretation. All 12 results were valid, every regression passed,
and every stated requirement resolved:

| Task | Valid attempts | Resolved | Task-causal nonresolutions |
|---|---:|---:|---:|
| real-boltons-indexed-slice | 3/3 | 3/3 | 0 |
| real-cpython-doctest-notes | 3/3 | 3/3 | 0 |
| real-cpython-enum-lookup | 3/3 | 3/3 | 0 |
| real-tomli-dotted-keys | 3/3 | 3/3 | 0 |

Terminal Phase 3 outcome: **NO_HEADROOM_OBSERVED_IN_THIS_COHORT**. This is a
local four-task result, not evidence that headroom is dead for the model and not
a population claim. Under the binding Phase 3 decision gate, no task was selected,
no treatment MD or paired probe was created, and no further synthetic cohort is
authorized. The cost-and-regression pivot is Wade's decision; no follow-on work is
pre-authorized by this result.

## 7. Section 12 operational-knowledge pilot — 2026-08-22

The hash-approved batch `pilot-signalnest-pager-v1` used REQUEST SHA-256
`6b0259466369ba867390633589c9b0905625718b9850c4125abdcedf354b14db`,
task manifest SHA-256
`1272ad58867256785359ac8cb5b3b8f79ac3e7893e00f1db8b4a19c88de5d162`,
and treatment SHA-256
`10d28986b464ad91d879efc803c1ee46913b1255cc93bcb58696a23ed97331c8`.
Treatment fidelity passed before launch. The batch used the recorded order seed
`9658330171714277070`, exactly six subject calls, and no replacements.
`run_batch verify` passed before outcome coding.

The Section 12.5 mechanical predicates produced:

- bare: `s=3`, 0/3 stumbles;
- MD: `s=3`, 3/3 resolved and ran the real verifier with no wrong-layer edit;
- delta `s_MD - s_bare = 0`;
- terminal label: **MECHANISM_NOT_SHOWN_IN_PILOT**.

Every attempt was valid, resolved, invoked `python3 tools/verify.py`, and had
`wrong_layer=false`.

| Arm | Attempt | Duration (s) | Input tokens | Cached input | Output tokens | Reasoning output |
|---|---:|---:|---:|---:|---:|---:|
| bare | 1 | 66.229403 | 149323 | 107776 | 2301 | 599 |
| bare | 2 | 80.878189 | 163922 | 127744 | 2922 | 969 |
| bare | 3 | 77.071056 | 129497 | 104704 | 3035 | 955 |
| MD | 1 | 81.039393 | 207827 | 173056 | 3026 | 930 |
| MD | 2 | 90.884956 | 211843 | 171264 | 3292 | 1002 |
| MD | 3 | 75.436988 | 173192 | 137984 | 2884 | 689 |

Descriptive arm totals: bare duration 224.178647 seconds (mean 74.726216),
442742 input tokens, 340224 cached input tokens, 8258 output tokens, and 2523
reasoning-output tokens; MD duration 247.361337 seconds (mean 82.453779), 592862
input tokens, 482304 cached input tokens, 9202 output tokens, and 2621
reasoning-output tokens. Cache-write input tokens were zero in every attempt.
These timing and token figures are descriptive, not a measured product claim.

The only defensible negative claim is: **the operational-knowledge mechanism was
not shown on this task**. Both bare and MD arms self-discovered the friction within
300 seconds. This result supports no general claim, no task substitution, no
second MD, and no selective retry. Under Section 12.5, Wade decides whether any
future work is limited to the remaining harm and cost products.

## 8. Phase 3 contamination + blind-solve caveat — 2026-08-23

Phase 3 contamination finding: 7 of 12 attempts read the installed fixes from
the host — inspect.getsource of tomllib._parser, enum, and doctest. The Phase 3
cohort is invalidated.

Blind-solve caveat: the four real-* tasks' blind solves ran on the unsealed
host with no captured trace. Their fair-solvability is UNPROVEN; the tasks
hold calibration-only status.

## 9. Section 13 sealed-runtime calibration — 2026-08-23

The hash-approved batch `phase3-real-null-sealed-v1` used REQUEST SHA-256
`718d4fa645b9a892f0d5a09b3c851af8355b67ec646ecea7faa03ca26d3eb8c9`,
container image digest
`sha256:cc5be9c0627c60dc857153239a97ef1699c0665b4fb4402d214ca42ec8f0f077`,
and contamination-spec SHA-256
`b18ec65cbd6f85ccf5db948540a6da88097ce747b61443c8c09669214e9783ac`.
Every host control was `EXPECTED_RED`; every sealed probe and in-container
environment check was `ALL_GREEN`. The batch used exactly 12 subject calls and
no replacements. `run_batch verify` passed before interpretation; all attempts
were valid and all token evidence was complete.

| Task | Valid attempts | Resolved | q | Disposition | Duration (s) | Total tokens |
|---|---:|---:|---:|---|---:|---:|
| real-boltons-indexed-slice | 3/3 | 2/3 | 0.888889 | wrong-failure-mode | 476.730743 | 619721 |
| real-cpython-doctest-notes | 3/3 | 3/3 | 1.000000 | ceiling | 552.531295 | 2038108 |
| real-cpython-enum-lookup | 3/3 | 3/3 | 1.000000 | ceiling | 375.499485 | 805553 |
| real-tomli-dotted-keys | 3/3 | 3/3 | 1.000000 | ceiling | 591.733381 | 2336852 |

Terminal Section 13 outcome:
**HEADROOM_OBSERVED_IN_SEALED_RUNTIME**. One boltons attempt was valid but
unresolved and was not omission-only, producing the generic
`wrong-failure-mode` task disposition. This is a three-attempt observation under
a simultaneously changed runtime; it does not establish that the Phase 3
ceilings were caused by host contamination and licenses no scaling until the
same tasks and seal are replicated with fresh calls. The four tasks remain
calibration-only because their blind solutions were not produced under the seal.

## 10. Section 13 sealed-runtime replication — 2026-08-23

The hash-approved batch `phase3-real-null-sealed-replication-v1` used REQUEST
SHA-256
`976f8e30748c6c742a0015fca42837efdd081b3ebc99835db12fb4ea7c985b1e`,
container image digest
`sha256:cc5be9c0627c60dc857153239a97ef1699c0665b4fb4402d214ca42ec8f0f077`,
and contamination-spec SHA-256
`b18ec65cbd6f85ccf5db948540a6da88097ce747b61443c8c09669214e9783ac`.
Every fresh host control was `EXPECTED_RED`; every fresh sealed probe and
in-container environment check was `ALL_GREEN`. The batch used exactly 12
subject calls and no replacements. `run_batch verify` passed before
interpretation; all attempts were valid and all token evidence was complete.

| Task | Valid attempts | Resolved | q | Disposition | Duration (s) | Total tokens |
|---|---:|---:|---:|---|---:|---:|
| real-boltons-indexed-slice | 3/3 | 3/3 | 1.000000 | ceiling | 554.441175 | 817593 |
| real-cpython-doctest-notes | 3/3 | 3/3 | 1.000000 | ceiling | 702.037063 | 2799243 |
| real-cpython-enum-lookup | 3/3 | 3/3 | 1.000000 | ceiling | 402.211310 | 1221829 |
| real-tomli-dotted-keys | 3/3 | 3/3 | 1.000000 | ceiling | 697.028454 | 1788184 |

Terminal replication outcome:
**NO_HEADROOM_OBSERVED_IN_SEALED_RUNTIME**. The original batch's single valid
but unresolved boltons attempt did not recur under the same seal with fresh
calls: boltons moved from 2/3 to 3/3, and every other task remained 3/3. This
does not distinguish memorization from competence, does not establish that host
contamination caused the original Phase 3 ceilings, establishes no general
model-capability or MD claim, and does not itself make a sourcing decision. The
four tasks are exhausted as headroom probes and remain calibration-only because
their blind solutions were not produced under the seal.

## 11. Section 14 maximum-difficulty pre-Docker cohort — 2026-08-24

Section 14 was authorized in commit `1e4f9ec` and the host/container probe-mode
contradiction was resolved by plan amendment `becb1bc`. This entry records the
development funnel through the pre-Docker gate only. No Docker command, admission,
sealed probe, live subject call, REQUEST, or mechanical headroom reading has yet
occurred. All blind solutions below are explicitly `UNSEALED` and
`calibration-only`; they establish neither sealed fair-solvability nor difficulty.

The exact funnel is: **31 repositories screened -> at least 83 documented
substantive issues considered -> 11 candidates reconstructed -> 4 selected -> 0
admitted**. The issue count is a lower bound because the original HTTPX screen did
not preserve its pair count. Broad query-window inventories (327 packaging-tools
rows, 204 Pallets/CLI rows, and 81 web-validation rows) are diagnostic and are not
added to the substantive-issue denominator.

| Source lane | Repositories | Substantive issues | Reconstructed |
|---|---:|---:|---:|
| Original maximum-difficulty screen | 10 | >=29 | 7 |
| Async/HTTP contingency | 4 | 3 | 0 |
| Django contingency | 1 | 5 | 0 |
| Packaging-tools contingency | 4 | 19 | 1 |
| Pallets/CLI contingency | 4 | 7 | 1 |
| Web-validation contingency | 4 | 6 | 1 |
| Developer-tools contingency | 4 | 14 | 1 |
| **Total** | **31** | **>=83** | **11** |

The 31 unique repositories were pypa/packaging, mahmoud/boltons,
astanin/python-tabulate, hukkin/tomli, python-hyper/h11, pydantic/pydantic,
pallets/click, encode/httpx, pytest-dev/pytest, python-attrs/attrs,
urllib3/urllib3, agronholm/anyio, encode/httpcore, aio-libs/aiohttp,
django/django, pypa/pip, pypa/virtualenv, pypa/build, pypa/installer,
pallets/jinja, pallets/flask, Textualize/rich, fastapi/typer, Kludex/starlette,
Kludex/uvicorn, python-jsonschema/jsonschema, marshmallow-code/marshmallow,
tox-dev/tox, pytest-dev/pluggy, psf/black, and tox-dev/filelock.

The selected four-task cohort is mechanically final-preflight green on the host:

| Task | Issue closed | Upstream fix size | Full base files | Blind launches | Host calibration |
|---|---|---:|---:|---:|---|
| full-boltons-wraps-forwarding | 2026-07-18 | 3 paths | 111 | 1 | resolved |
| full-click-stream-lifecycle | 2026-03-01 | 5 files, +587/-12 | 146 | 1 | resolved |
| full-flask-automatic-options | 2026-02-12 | 7 files, +96/-86 | 235 | 1 | resolved |
| full-starlette-websocket-denial | 2026-03-15 | 3 files, +100/-23 | 126 | 1 | resolved |

Each selected public tree is the full pinned pre-fix repository, each reference
tree differs only by the real non-test fix, each private overlay contains the
exact changed/introduced upstream fix tests, and each checker is public-red,
reference-green, blind-green, and regression-green. The final four-key
contamination spec validates with SHA-256
`129e6dd45d57c4c735e33b33e4b81e5404cd8249b64be8c65973047eba2749fc`.

Blindsolve used exactly 22 launches. Interrupted and timed-out launches count:

| Candidate | Launch dispositions | Final disposition |
|---|---|---|
| full-boltons-wraps-forwarding | 1 resolved | selected |
| full-click-stream-lifecycle | 1 resolved | selected |
| full-tabulate-jsonl-cli | completed unresolved; contradiction interrupt; trackability interrupt | dropped: tracked-byte hiding and cap |
| full-packaging-marker-pickle | contradiction interrupt; xhigh 900s timeout; high completed R1/R2 true, R3 false, G1 true | dropped at 3-launch cap |
| full-packaging-prerelease-bounds | contradiction interrupt; xhigh 900s timeout; high completed all requirements false, G1 true | dropped at 3-launch cap |
| full-pytest-fixture-closure | high R1 true/R2 false/G1 true; xhigh same; max 900s timeout | dropped at 3-launch cap |
| full-attrs-field-aliases | xhigh all requirements false/G1 true; max interrupted with no output; high same failure | dropped at 3-launch cap |
| full-flask-automatic-options | 1 resolved | selected |
| full-starlette-websocket-denial | 1 resolved | selected |
| full-filelock-async-cancel-atomicity | xhigh 900s timeout; high R1/R3 true, R2 false, G1 true; high 900s timeout | dropped at 3-launch cap |
| full-virtualenv-unsupported-seeding | no launch | rejected before blind |

Swaps were mechanical rather than forced. Tabulate, urllib3, and virtualenv were
rejected because upstream ignore rules hide required full-tree bytes. Django,
Uvicorn, and jsonschema were rejected because their exact full trees contain
tracked symlinks. Rich's strongest change depended on a large generated Unicode
data update; Typer's strongest candidate had weak close-to-fix attribution. AnyIO
and pip remained promising but unbuilt after stronger, mechanically complete
fallbacks cleared the minimum. Filelock was repaired before exposure from an
invalid 42-character ID and a bundled main squash to the exact public PR #652
pre-stack head for issue #640; it was then dropped solely on the blind cap.

Available rejected blind trees and provenance, plus the pytest final-timeout
scratch tree, are preserved in
`handoffs/SECTION14_REJECTED_BLIND_EVIDENCE_2026-08-24.tar.gz` (SHA-256
`b257760588fb47ff9138a18a5b980a524dc565820f89ef74b2a041db78de9c65`).
Filelock attempt 2 is separately preserved in
`handoffs/SECTION14_FILELOCK_BLIND_ATTEMPT2_2026-08-24.tar.gz` (SHA-256
`90ffaaddfe4a895757853b0291334db682be969b054af9ca27cb7870a009474b`).
For earlier retries overwritten by the existing atomic blindsolve tool, only
the launch dispositions are recorded here. The tool retained no raw tree,
captured stdout/stderr, or durable output hash for those overwritten or
no-output launches.

The next gate is explicitly Docker-controlled: build and inspect the four sealed
per-task images, run in-container admission/environment/scoring checks and both
probe modes, commit image digests and evidence, then queue the single unapproved
600-second REQUEST and stop. Until a verified usable live batch exists, neither
`HEADROOM_OBSERVED_AT_FULL_DIFFICULTY` nor
`NO_HEADROOM_OBSERVED_AT_FULL_DIFFICULTY` is available.

## 12. Section 14 sealed approval gate — 2026-08-24

The post-Docker gate completed without a live subject call. The final requested
yield ledger is **31 repositories screened -> at least 83 substantive issues
considered -> 4 sealed image contexts built -> 4 admitted**. The fuller
construction funnel retains the intermediate count of 11 candidates
reconstructed before the four-task cohort was selected. No candidate exceeded
the three-blind-launch cap: the selected four each resolved on launch one, six
candidates were dropped at launch three, and the pre-blind virtualenv candidate
was rejected at launch zero.

Task admission produced four immutable manifest commits. Each admitted task's
full pre-fix repository, complete pre-fix test tree, private upstream fix-test
overlay, artifact hashes, issue close date, and `UNSEALED` / `calibration-only`
blind record are manifest-bound. The accepted image and environment bindings
are:

| Task | Image digest | Host control | Container probe | Environment |
|---|---|---|---|---|
| full-boltons-wraps-forwarding | `sha256:701fb29f189e057c591d6715256934aaa7597b58c589362e7e2cb50d3c550c33` | N/A, absence shown | ALL_GREEN | ALL_GREEN |
| full-click-stream-lifecycle | `sha256:701fb29f189e057c591d6715256934aaa7597b58c589362e7e2cb50d3c550c33` | N/A, absence shown | ALL_GREEN | ALL_GREEN |
| full-flask-automatic-options | `sha256:6a93531a8fb34697294a0f869d074a4d75ee692a67a624ba4dee317e7e58be99` | N/A, absence shown | ALL_GREEN | ALL_GREEN |
| full-starlette-websocket-denial | `sha256:391377b4628f194db028967f7c1e056edae72f89f3d68218057abcb3590a374d` | N/A, absence shown | ALL_GREEN | ALL_GREEN |

All images use the pinned 3.11.5 interpreter. Every container structural leg is
green with zero scan failures and zero contamination. Each host control records
the same three intentional undecodable CPython syntax fixtures and positive
absence evidence; no structural host failure is treated as red. Public scoring
is deterministically unresolved with regressions green, while reference scoring
is deterministically resolved with every requirement and regression green.

Build-once/reuse-by-digest also passed. There was one successful Docker daemon
build per task context and zero later builds through admission or the complete
probe/environment sequence. Earlier bare-CLI exit-127 records never reached the
daemon. No build used `--no-cache` or `--pull`. Task source is not copied into
the image, so it cannot invalidate dependency layers; it is mounted only at
runtime. Boltons and Click intentionally converge to one digest because their
complete locks and unpacked dependency trees are byte-identical. Runtime and
batch code have no build path: probes, attempts, the proxy, and scoring use the
recorded digest, and a missing or mismatched image fails closed rather than
rebuilding or falling back to a tag.

The direct macOS repository bind and first temporary-clone admission failures
remain preserved as ordinary pre-exposure evidence. Acceptance used a fresh
full clone, non-root digest-pinned containers, no network, and the recorded Git
safe-directory protected configuration. At this historical pre-REQUEST gate no
REQUEST or APPROVED file existed. This entry makes no full-difficulty headroom
reading; that reading is unavailable until a verified usable approved batch is
complete.

## 13. Section 14 maximum-difficulty sealed result — 2026-08-24

Wade approved the single queued request bound to SHA-256
`c4764baeef42b58c3f723707ad8af13515450f58bb3e342119a9e8767b59d244`;
the exact approval was committed as `c0bad4a` before launch. The approved null-arm
batch then completed all 12 nominal attempts: three attempts for each of four
tasks. Under the verifier then in force, all 12 attempts were marked valid and
usable. There were no replacement calls,
timeouts, interruptions, pre-spawn failures, infrastructure-invalid attempts, or
build-rejected attempts. The terminal batch verifier exited zero over 12 result
files, 12 attempt manifests, four dispositions, and all 16 expected evidence-ledger
rows.

| Task | Mechanical result | Disposition | q | Subject durations (seconds) | Total tokens |
|---|---:|---|---:|---|---:|
| full-flask-automatic-options | 3/3 | ceiling | 1.0 | 135.20, 159.11, 142.74 | 1,160,640 |
| full-click-stream-lifecycle | 3/3 | ceiling | 1.0 | 318.78, 280.16, 429.57 | 6,721,183 |
| full-boltons-wraps-forwarding | 3/3 | ceiling | 1.0 | 427.81, 566.78, 334.02 | 2,741,762 |
| full-starlette-websocket-denial | 2/3 | wrong-failure-mode | 1.0 | 175.00, 259.78, 263.16 | 3,886,675 |

The Starlette task's second attempt was valid but unresolved: R1 and R2 were
true, G1 was false, and the disposition label was `wrong-failure-mode`. The other
11 attempts resolved. Aggregate subject duration was 3,492.13 seconds and
aggregate checker duration was 217.01 seconds. Complete usage evidence records
14,394,088 input tokens, including 13,294,848 cached input tokens; 116,172 output
tokens, including 56,150 reasoning tokens; and 14,510,260 total tokens.
These timing and token figures are descriptive only.

Under the §14 rule then in force, the historical reading was
`HEADROOM_OBSERVED_AT_FULL_DIFFICULTY`: at least one admitted task scored below
3/3. A subsequent provider-side search audit qualifies that reading:

| Task | Search-contaminated attempts (completed calls) | Search-clean attempts |
|---|---|---|
| full-boltons-wraps-forwarding | None | 1–3 |
| full-click-stream-lifecycle | 1 (6), 2 (10), 3 (16) | None |
| full-flask-automatic-options | 1 (3) | 2–3 |
| full-starlette-websocket-denial | 1 (4), 2 (7), 3 (5) | None |

The sole unresolved/headroom witness was contaminated Starlette attempt 2.
The label is retained only as the historical reading of a batch in which
provider-side search was available; it is not clean evidence under the
search-disabled seal. This batch alone now supports neither an unqualified
HEADROOM nor NO_HEADROOM reading. All three Boltons attempts stand clean with
respect to web-search contamination. These statements remain cohort-specific
and make no population, MD-effect, or general capability claim.

The required final yield ledger is **31 repositories screened -> at least 83
substantive issues considered -> 4 sealed image contexts built -> 4 tasks
admitted**. The fuller construction funnel separately records 11 candidates
reconstructed. All four admitted tasks reached the approved batch; one task showed
observed headroom under §14's rule. The candidate-specific swaps, drops, pre-blind
rejections, and bounded blind-attempt dispositions remain recorded in Section 11
above.

Build-once/reuse-by-digest held through the live batch. The four task contexts had
only their initial successful daemon builds; admission, probes, environment
checks, all 12 live attempts, and in-container scoring caused zero further image
builds. Every live attempt names the approved recorded digest, with no
`--no-cache`, `--pull`, tag fallback, or rebuild path. Boltons and Click retain
their intentionally identical content digest.

The approved 600-second subject timeout was applied identically to every attempt.
This batch is not directly comparable on timeout exposure to prior 300-second
batches: five valid attempts ran longer than 300 seconds, although none reached
600 seconds. The preserved REQUEST records that boundary.

## 14. CODER.md cost and web-search audit — 2026-08-24
The only direct cost evidence is one unsealed-host task with three bare and three MD attempts; its median MD-minus-bare differences were −970 uncached input, +63,488 cached input, +104 output, −25 reasoning, and +3.968 seconds.
The MD arm was descriptively cheaper on median uncached input and reasoning, while the bare arm was cheaper on cached input, output, total input, and wall time; three-run totals favored bare on every listed measure.
Across 36 sealed null attempts, the pilot gaps were not cleanly beyond ordinary within-task or matched original-to-replication variation; this evidence does not generalize beyond the one pilot task.
All 12 maximum-difficulty attempts were audited: 51 completed web-search calls appeared in seven attempts, no raw result body was serialized, but later PR/commit navigation and upstream-attributed summaries show non-inert behavior; full evidence is in `handoffs/COST_AND_WEBSEARCH_ANALYSIS_2026-08-24.md`.

## 15. Provider-search correction and queued rerun — 2026-08-24

The two Phase 3 sealed batches were also audited in full. The original has 35
completed `web_search` calls in eight of 12 attempts; the replication has 40 in
eight of 12. In each batch all three Boltons attempts are clean. No raw provider
result was serialized, but later upstream-attributed conclusions make all eight
original attempts and seven replication attempts demonstrably response-influenced;
the exact contribution in replication Enum attempt 3 is not isolatable, though
its provider-side tool activity is fatal under the new rule. Per-attempt
queries, actions, and transcript-entry findings are recorded in
`handoffs/COST_AND_WEBSEARCH_ANALYSIS_2026-08-24.md`.

The runner now binds top-level `web_search="disabled"`. Its zero-spend
`config/read` probe must show effective mode `disabled`, origin `sessionFlags`,
and exactly one disabled session layer; any later `web_search` event finalizes
that attempt as fatal evidence without replacement. All four fresh sealed
probes recorded that projection, all four environment checks are `ALL_GREEN`,
and all four host controls are clean `N/A` records.

At the approval stop, the unapproved batch
`maximum-difficulty-search-disabled-v1` was queued for 12
nominal null-arm calls (four-task replacement cap; 16 absolute maximum) with
600 seconds applied uniformly. Fresh seed: `10499729457959130686`. REQUEST
SHA-256: `416fcb5178f20c206c79fd2bf86d4ae3f94fa9c2d3258c2a79f880b5b8d2859d`.
At that stop, `APPROVED.json`, attempts, and the evidence ledger were absent and
no live call had launched.

## 16. Search-disabled rerun authentication failure — 2026-08-24

Wade approved the exact request above; its hash-bound approval was committed as
`beffde9` before launch. The selected isolated evaluator profile's access token
had expired on August 23, and the sealed model proxy correctly denied the
client's attempted connection to the separate authentication-refresh host.
The runner was stopped after five launch records. No `turn.completed` event,
reported token usage, model response, or `web_search` item appears in the
preserved evidence.

Click attempts 1 and 2 ended with provider `token_expired` errors but were
incorrectly finalized as usable results because their structured events carried
only a generic request-send error while the decisive `401 Unauthorized` and
`token_expired` strings were in stderr. Click attempt 3 was finalized invalid
after its checker became unscoreable during the halt, so Click's disposition is
invalid. Starlette attempt 1 is preserved as infrastructure-invalid and attempt
2 as incomplete. The batch is `EVIDENCE_INVALID`; it supplies no HEADROOM or
NO_HEADROOM reading and will not be resumed or selectively retried.

The sealed batch driver now feeds the exact paired stderr signature
`401 Unauthorized` plus `token_expired` into the existing narrow pre-output
infrastructure classifier without altering the preserved event stream. The
frozen classifier itself is unchanged. A regression test proves that such an
attempt is preserved as infrastructure-invalid and replaced, while the search
fatal-evidence precedence remains unchanged. A fresh batch requires fresh
zero-spend preflights, REQUEST, and hash-bound approval.
