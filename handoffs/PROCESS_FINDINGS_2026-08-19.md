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
