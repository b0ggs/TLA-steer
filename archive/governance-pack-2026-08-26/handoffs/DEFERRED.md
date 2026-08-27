# Deferred list

Companion to PLAN_OF_RECORD_2026-08-26.md (invariant I8). One line per
item. Items here are recorded, not scheduled; nothing on this list is
authorized work.

Source tags: [W] Wade/conversation, [RT] red-team memo,
[AUD1] three-auditor review of plan rev 1
(AUDIT_PLAN_OF_RECORD_REV1_2026-08-26.md), [AUD3] three-report review of
plan rev 3 (PLAN_OF_RECORD_2026-08-26_AUDIT_{FACTS,INVARIANTS,EXECUTION}.md).

"(adopted)" marks a recommendation the plan implemented rather than
merely logged. I8 permits adoption only where required to fix an (a) or
(b) finding; adoptions that exceed that are marked "flagged" and are
open questions for Wade, not settled decisions. [AUD3] lines are
deduplicated across the three reports by substance; no recommendation
was dropped.

## Scope deferrals (out of scope for this phase)

- [W] Challenge site / competition front end (Stage 1 marketing layer; perishable, gated behind probe results).
- [W] Task factory (generalized automated task generation; parked since Aug 21).
- [W] Failure-mining platform (automated incident harvesting from repos).
- [RT] Failure-mode detector product — gated behind arm-separation evidence plus 2-3 buyer conversations.
- [W] New confirmatory experiments (M2 protocol machinery stays closed until one is actually scheduled).
- [W] Runner, tooling, and src/ source modifications of any kind (I1).
- [W] Attempt-count extensions beyond the runner's hardcoded 3 per arm per task (rev-3 audit showed 6 is unexecutable without code changes).
- [W] real-* task probes (sealed baselines search-contaminated; outside the containment cohort).
- [W] Repo-specific MD arm (one MD per repository, authored from public snapshot).
- [W] Any-MD / mismatched-MD priming control arm (Guardrails study makes it central for attribution).
- [W] Incumbent arm for keep-or-replace decisions (product-definition three-arm design).
- [W] One-repo-many-sealed-tasks challenge pack (Aug 21 selected direction; superseded by D5).
- [W] Power-derived pre-registered n with equivalence margins (TOST) for any confirmatory cost claim.
- [W] Claude session transcript preservation (lives outside repo; Wade's call on mechanism and timing).

## Tooling capability gaps

- [AUD1] Runner support for per-task arm files and parameterized attempt counts.
- [AUD1] Sealed-batch comparator support for cost, time, and trajectory outcomes.
- [AUD1] Timestamp instrumentation in the subject event stream (enables time-to-first metrics).
- [AUD1] Price schedule / backend fingerprint preservation for dollar-cost claims.

## From the rev-1 audit

- [AUD1] Enumerate exact Step 1 archive and tombstone paths.
- [AUD1] Name every sub-agent deliverable path before launch.
- [AUD1] Verifiable Wade-authorship mechanism and hook installation path.
- [AUD1] State sealed vs host-run for Step 2a and the applicable combined preflight specification.
- [AUD1] Pre-register a compliance rubric for champion/subject-wrapper conflicts.
- [AUD1] Both possible request sizes under the batch-global 900s timeout option (batch-global nature adopted in rev 3; request sizes still deferred).
- [AUD1] Pre-registered timeout, missing-usage, task-blocking, and aggregation policies.
- [AUD1] Name batch ID, seed, evaluator profile, container configuration, and complete CLI invocation before queue.
- [AUD1] Use capture.json and diff.patch as the edit-scope evidence sources. (adopted in rev 3, untagged at the time)
- [AUD1] Designate either TAXONOMY.md or TAXONOMY_REVISED.md as canonical. (adopted in rev 3, untagged at the time — assigned to Step 0)
- [AUD1] Define Step 2b clock start relative to approval and batch completion. (adopted in rev 3, untagged at the time — clock starts at batch approval)
- [AUD1] Preserve Wade decisions and auditor outputs as independent artifacts before supersession. (partially adopted: audits saved to disk; an independent decision artifact is still deferred — see [AUD3] first line)
- [AUD1] Exclude volatile .mdseval-codex-home/tmp paths from full-repo copy tests (suite showed 216 tests, 6 copy errors, 6 skips).

## From the rev-3 audit

- [AUD3] Preserve D2/D3/D5 and the rev-3 rulings in an independent dated, Wade-signed artifact before the supersession commit, rather than only in the plan they authorize.
- [AUD3] Define all decision-rule terms numerically: envelope formula, majority denominator, direction rule, narrow/wide, plausible effect, feasible-n bound, borderline interval, multi-metric aggregation. (adopted in rev 4 — required to fix contradiction (b)6, non-exhaustive rule conflicting with I2)
- [AUD3] Use a contemporaneous randomized null arm if the result is intended to support a treatment-effect rather than directional interpretation.
- [AUD3] Pre-register handling for missing usage, timeout censoring, invalid attempts, correctness regressions, task exclusion, denominators, unequal per-task counts, and cross-task aggregation. (partially adopted in rev 4 — flagged: not clearly required by any (a)/(b) finding; Wade to confirm or revert)
- [AUD3] Name before execution: archive/tombstone set, batch ID, seed, evaluator profile, container specification, timeout, request size, probe-control path, complete queue CLI, deliverable/output paths and formats, and every sub-agent output path.
- [AUD3] Specify a mechanical isolation and provenance mechanism proving the probe-MD author never inspected task names, manifests, checkers, or reference solutions.
- [AUD3] Define how "net instruction text" decrease is measured, and whether archived text and tombstones count toward it.
- [AUD3] Either define a mechanically verifiable meaning of "non-Wade edit" for the optional hook or omit that check; prefer replacement-only semantics over commit-author identity. (adopted in rev 4 — flagged: (b)7 required only narrowing the hook to I4 scope; the replacement-only wording exceeds that)
- [AUD3] Place and name the standalone analysis code at a path outside the I1-frozen scripts/, tooling/, and src/ trees.
- [AUD3] Define a metric schema mapping each Step 2b behavior to its exact preserved artifact and computation, and operationalize each metric before prototyping.
- [AUD3] Define a measurable success/failure criterion for Purpose question 2, since Step 2b designs but does not run a controlled governance experiment.
- [AUD3] Commit a baseline-eligibility matrix before requesting any new subject-model spend.
- [AUD3] Record the live Codex CLI identity/version and rendered wrapper hash alongside the historical fingerprints.
- [AUD3] Re-run the full unit suite after archive relocation and the AGENTS rewrite.
- [AUD3] Exclude .mdseval-codex-home/tmp from repository-copy test fixtures (duplicate of the [AUD1] line above; raised independently in round 2).
