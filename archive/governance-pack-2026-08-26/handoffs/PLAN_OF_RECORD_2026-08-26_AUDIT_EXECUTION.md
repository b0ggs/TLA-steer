# Independent execution audit — PLAN_OF_RECORD_2026-08-26.md rev 3

Audited plan SHA-256: `5440c7b2c2633df55a5bc870d1a1a225a63d40cc3f7b3a9e05566db8ed03da04` at repository commit `a72fd07a76ab4ba44d82b4fd217f45b487acd951`.

## (a) Factual errors

1. **The named real-task baseline is not a usable search-disabled, contamination-filtered baseline for the named cohort.** Applying the plan's own rule—exclude every attempt whose `events.jsonl` contains a `web_search` item—excludes 16 of the 24 real-task attempts. It leaves Boltons 6/6, Enum 2/6, Doctest 0/6, and Tomli 0/6. Thus two named tasks have no historical baseline at all, and Enum has only one surviving observation in each batch. The phase-3 requests also lack the later container-level `web_search: disabled` binding, and the events prove that search actually occurred. Evidence: plan lines 103-107 and 184-202; `runs/dev-v2/phase3-real-null-sealed-v1/REQUEST.json:1`; `runs/dev-v2/phase3-real-null-sealed-replication-v1/REQUEST.json:1`; both campaign trees' `events.jsonl` files; for concrete examples, `runs/dev-v2/phase3-real-null-sealed-v1/real-cpython-doctest-notes/null/attempt-1/events.jsonl:18-19` and `runs/dev-v2/phase3-real-null-sealed-replication-v1/real-tomli-dotted-keys/null/attempt-1/events.jsonl`.

2. **The named full-task baseline cannot supply the claimed between-batch noise envelope.** The plan names only `maximum-difficulty-search-disabled-v2` for every `full-*` task, and that campaign has three attempts in one batch. There is no across-batch spread for Full Boltons, Full Flask, or optional Full Click from the stated baseline. Evidence: plan lines 189-196 and 203-214; `runs/dev-v2/maximum-difficulty-search-disabled-v2/REQUEST.json:1`; `runs/dev-v2/maximum-difficulty-search-disabled-v2/*/null/attempt-*/result.json`.

3. **The statement that every rev-1 recommendation was logged to `DEFERRED.md` “unchanged” is false.** The rev-1 recommendations to use `capture.json`/`diff.patch` and to designate a canonical taxonomy are not present as Deferred lines; they were instead incorporated into this plan, while several Deferred entries contain added qualifications. Evidence: plan lines 3-6, 141-145, and 215-222; `handoffs/AUDIT_PLAN_OF_RECORD_REV1_2026-08-26.md:118-142`; `handoffs/DEFERRED.md:8-29`.

## (b) Internal contradictions

1. **Step 0 violates I1's one-new-MD invariant.** I1 allows exactly one newly authored MD, the probe MD, and says no other MD authoring; Step 0 mandates authoring `handoffs/SPECIMEN_INDEX.md`. Evidence: plan lines 41-47 and 137-146.

2. **Step 2a's config-matched mixed cohort cannot be produced within I1 and I2.** The real baseline is timeout 300 with container spec `b18ec...`; the full baseline is timeout 600 with spec `129e...`, and its own request labels 600 seconds a comparability boundary. The runner gives a batch one global timeout and one container object. Current containment code hard-codes `scripts/contain/contamination-spec.json`, which contains only the four `full-*` tasks, while sealed queueing requires batch-local, tracked, clean preflights bound to the request's common spec and task images. A host batch would not match the sealed baselines. Satisfying the plan therefore requires changing frozen containment source/specification or splitting the cohort into multiple batches, forbidden respectively by I1 and I2. Evidence: plan lines 41-50, 103-107, and 174-202; `runs/dev-v2/phase3-real-null-sealed-v1/REQUEST.json:1`; `runs/dev-v2/maximum-difficulty-search-disabled-v2/REQUEST.json:1`; `scripts/run_batch.py:100-137`; `scripts/run_batch.py:173-206`; `scripts/contain/runtime.py:6-7`; `scripts/contain/contamination-spec.json:1`.

3. **The 3-to-6 attempt extension violates I1/I2 and is unsupported by the frozen runner.** `launch()` executes exactly `range(3)`; request validation fixes nominal calls at three per task/arm and total approved calls at four per task/arm including the one infrastructure-replacement allowance; verification rejects more than four launches. Six usable attempts therefore require runner/tooling changes or a second batch and approval, violating I1's freeze, I2's one-batch/no-rerun rule, and the single-checkpoint design. Evidence: plan lines 41-50, 63-66, 103-112, 184-186, and 213-214; `scripts/run_batch.py:131-137`; `scripts/run_batch.py:499-528`; `scripts/run_batch.py:564-578`; `tooling/taskcheck.py:362-395`.

4. **The fresh-null fallback violates I2.** D3 first says the null baseline is not rerun, then permits a fresh null mini-batch when it is unusable; I2 permits one batch and no reruns regardless of outcome. The preserved evidence already triggers that contingency because required filtering eliminates every Doctest and Tomli baseline attempt. Evidence: plan lines 48-50 and 103-112, plus the contamination evidence in finding (a)(1).

5. **The mandatory determinate verdict conflicts with I2 and is not guaranteed by the stated rule.** I2 accepts an inconclusive final result, while D3 forbids an unknown ending. The three cases are not exhaustive: for example, some task medians may be outside their envelopes without a same-direction majority, while the remaining envelopes are neither demonstrably narrow enough for 15-30% nor so wide that “no plausible” effect can register. “Envelope,” “consistent direction,” “narrow enough,” “plausible,” “feasible n,” and “borderline” have no operational thresholds, and four named tasks lack the claimed between-batch envelope after the required filtering. Evidence: plan lines 48-50, 103-112, and 203-214.

## (c) Recommendations

- Commit a baseline-eligibility matrix before requesting any new subject-model spend.
- State sealed versus host execution and name the exact container/preflight construction.
- Name the batch ID, seed, timeout, probe-control path, evaluator profile, and complete queue command.
- Pre-register handling for missing token usage, timeouts, invalid live attempts, and tasks eliminated by baseline filtering.
- Define the envelope formula, majority denominator, direction rule, viability thresholds, feasible-n bound, and borderline interval numerically.
- Record the live Codex CLI identity/version and rendered wrapper hash alongside the historical fingerprints.
- Name the standalone analysis script and every Step 2/3 output path and file format.
- Operationalize each Step 2b metric before prototyping it over transcripts.
- Enumerate the exact Step 1 archive moves and tombstone destinations.
- Re-run the full unit suite after archive relocation and the AGENTS rewrite.

## Can a fresh session execute the plan as written?

**No.** It is currently pending Wade's approval, and assuming approval does not remove the mechanical blockers.

The exact blockers are:

- The required baseline filter is already known to leave no Doctest or Tomli baseline and only two Enum observations.
- No one-batch live configuration can match both the 300-second/`b18ec...` real baseline and the 600-second/`129e...` full baseline; no reusable combined sealed preflight/spec exists under the frozen source.
- The frozen runner cannot execute the permitted six-attempt extension, and its request/verifier schemas cap each task/arm at three usable attempts plus one infrastructure replacement.
- Repairing the unusable baseline with the authorized fresh-null contingency creates a second batch, contrary to I2.
- The decision rule has uncovered outcome regions, so it cannot guarantee the required verdict.
- Step 0 cannot create `SPECIMEN_INDEX.md` while obeying I1's exact-one-new-MD rule.

The revised `queue` subcommand, one-arm control path, six mandatory task IDs, and integer 900-second CLI timeout are individually accepted by the existing tooling; those rev-1 blockers are fixed. The remaining issue is that no accepted request can satisfy the full experimental design and its invariants simultaneously.
