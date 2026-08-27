# Independent invariant audit — Plan of Record rev 3

Scope: `handoffs/PLAN_OF_RECORD_2026-08-26.md`, read in full at 253
lines, checked against the current `AGENTS.md`, the relevant activation,
runner, and sealed-execution provisions of `TASK_TOOLING_V2_PLAN.md`, the
actual `scripts/run_batch.py` and `tooling/taskcheck.py` contracts, the named
baseline requests and event streams under `runs/dev-v2/`, and the rev-1 audit
and Deferred artifacts. No live model calls were made.

## (a) Factual errors

1. **The existing champion was made and locked as the repository's canonical
   champion.** D2's unqualified statement that it "was never made to be a
   champion" is contradicted by the implementation specification, which says
   to create `targets/coder/champion.md` from canonical bytes and lock its
   SHA-256; the README continues to call it the champion. Evidence:
   `handoffs/PLAN_OF_RECORD_2026-08-26.md:92-95`,
   `docs/coder-single-file-mvp-spec.md:47-65`,
   `docs/coder-single-file-mvp-spec.md:354-359`, `README.md:4-12`, and commit
   `ba1d396` (`implement MD evaluator MVP`). The narrower claim at plan
   lines 19-22 that it was not designed for this cost/time probe is not
   disproved; D2's broader wording is.

2. **The statement that every rev-1 recommendation was logged to Deferred
   "unchanged" is false.** The rev-1 audit recommends using `capture.json` and
   `diff.patch`, defining the Step 2b clock start, and designating a canonical
   taxonomy. Rev 3 implements those recommendations at lines 215-220,
   226-227, and 139-145. The first and third are absent from `DEFERRED.md`,
   while the clock entry was changed by adding "now fixed in plan."
   Evidence: `handoffs/PLAN_OF_RECORD_2026-08-26.md:3-6`,
   `handoffs/AUDIT_PLAN_OF_RECORD_REV1_2026-08-26.md:126-137`, and
   `handoffs/DEFERRED.md:18-28`.

3. **The prescribed contamination filter leaves no null baseline at all for
   two mandatory real tasks and only two clean observations for a third.** All
   six sealed doctest attempts and all six sealed tomli attempts contain
   `web_search` events. Four of six enum attempts contain them, leaving one
   clean attempt in each batch. Only Boltons retains three clean attempts in
   each batch. Consequently the asserted historical baseline cannot supply
   per-task medians for doctest or tomli after the plan's mandatory exclusion.
   Evidence: `handoffs/PLAN_OF_RECORD_2026-08-26.md:103-112,176-179,189-196`;
   `runs/dev-v2/phase3-real-null-sealed-v1/real-cpython-doctest-notes/null/attempt-1/events.jsonl:18`
   (and attempts 2-3),
   `runs/dev-v2/phase3-real-null-sealed-replication-v1/real-cpython-doctest-notes/null/attempt-1/events.jsonl:17`
   (and attempts 2-3),
   `runs/dev-v2/phase3-real-null-sealed-v1/real-tomli-dotted-keys/null/attempt-1/events.jsonl:18`
   (and attempts 2-3), and
   `runs/dev-v2/phase3-real-null-sealed-replication-v1/real-tomli-dotted-keys/null/attempt-1/events.jsonl:35`
   (and attempts 2-3). The only clean enum files are
   `phase3-real-null-sealed-v1/.../real-cpython-enum-lookup/null/attempt-1/events.jsonl`
   and
   `phase3-real-null-sealed-replication-v1/.../real-cpython-enum-lookup/null/attempt-2/events.jsonl`.

4. **The named full-task baseline cannot provide the claimed across-batch
   noise envelope.** The plan names only
   `maximum-difficulty-search-disabled-v2` for the full tasks. That is one
   batch with three attempts per task, so there is no between-batch spread for
   either `full-boltons-wraps-forwarding` or
   `full-flask-automatic-options`. Evidence:
   `handoffs/PLAN_OF_RECORD_2026-08-26.md:189-196,203-212` and
   `runs/dev-v2/maximum-difficulty-search-disabled-v2/REQUEST.json:1`.

5. **The historical baselines are not config-matched to one possible live
   batch.** Both real-task requests use a 300-second timeout and lack the
   provider-search-disabled container binding; the full-task request uses a
   600-second timeout and binds `container.web_search: "disabled"`. The live
   request has one batch-global `runner` object and therefore one timeout for
   every task. If Click is included as directed when 900 seconds is supported,
   the single live timeout becomes 900 seconds and matches neither historical
   cohort. Evidence: `handoffs/PLAN_OF_RECORD_2026-08-26.md:103-107,180-188`;
   `runs/dev-v2/phase3-real-null-sealed-v1/REQUEST.json:1`;
   `runs/dev-v2/phase3-real-null-sealed-replication-v1/REQUEST.json:1`;
   `runs/dev-v2/maximum-difficulty-search-disabled-v2/REQUEST.json:1`; and
   `scripts/run_batch.py:100-137`.

6. **Not every item declared out of scope is on the Deferred list.** The plan
   says all listed items live in `handoffs/DEFERRED.md`, but that file has no
   line for the challenge site, task factory, failure-mining platform, or new
   confirmatory experiments as such. Evidence:
   `handoffs/PLAN_OF_RECORD_2026-08-26.md:247-253` and
   `handoffs/DEFERRED.md:1-29`.

## (b) Internal contradictions

1. **Step 0 violates I1's phase-wide one-MD limit.** I1 permits exactly one
   newly authored MD, the probe, and says "no other MD authoring." Step 0
   expressly authors the new `handoffs/SPECIMEN_INDEX.md`; Step 1 also calls
   for one-line tombstones for archived Markdown plan/protocol paths. Evidence:
   `handoffs/PLAN_OF_RECORD_2026-08-26.md:35-47,137-145,162-165`. The specimen
   index does not currently exist, so this is not merely committing an existing
   untracked artifact.

2. **Step 1's queue acceptance is sequenced before the required arm exists,
   and creating it inside Step 1 violates I3.** D2 requires a fresh probe MD
   under `controls/`, but the repository presently has no such file; the live
   arm is placed in Step 2a while Step 1's sole acceptance test already requires
   queuing it. The runner refuses an arm unless its source is an existing file
   under `controls/`. Authoring the missing MD during Step 1 would violate I3's
   delete/archive/shorten-only scope and its sole script exception. Evidence:
   `handoffs/PLAN_OF_RECORD_2026-08-26.md:51-55,92-100,162-172,184-188`;
   `scripts/run_batch.py:100-123`; and the current files under `controls/`
   (`controls/coder/*.md` and `controls/pilot/pilot-signalnest-pager.md`), none
   of which is the new probe.

3. **The 3-to-6 extension violates I1 and I2 with the frozen runner.** The
   existing request schema hard-codes nominal calls as three per task/arm, its
   validator requires exactly that count, and `launch()` has exactly three
   rounds. It has no parameterized attempt count or in-batch extension path.
   Reaching six therefore requires a runner/tooling change forbidden by I1 or
   a second batch/rerun forbidden by I2. Evidence:
   `handoffs/PLAN_OF_RECORD_2026-08-26.md:41-50,103-112,174-186,213-214`;
   `scripts/run_batch.py:131-137,499-528`; and
   `tooling/taskcheck.py:362-395`.

4. **The fresh-null fallback violates I2 and I7.** I2 fixes Step 2a at one
   batch with no reruns, and Step 2a's I7 cap is also one batch. D3 nevertheless
   authorizes a fresh null-arm mini-batch if the historical baseline is
   unusable. That condition is already true under finding (a)(3). Evidence:
   `handoffs/PLAN_OF_RECORD_2026-08-26.md:48-50,69-70,103-112,174-175`.

5. **D3 rejects the inconclusive final state that I2 expressly permits.** I2
   says an inconclusive result is valid and final; D3 says "unknown" is not an
   acceptable ending and forces one of three determinate verdicts. No explicit
   Wade instruction names I2 as changed, which the invariant-change rule at
   lines 35-39 requires. Evidence:
   `handoffs/PLAN_OF_RECORD_2026-08-26.md:35-39,48-50,103-110,203-214`.

6. **The optional root-Markdown hook exceeds I3's only exception.** I3 permits
   one mechanical check only to enforce I4. I4 freezes the sole live plan; it
   does not prohibit creation of unrelated root-level Markdown. Step 1's
   proposed blanket rejection of every new root-level `.md` therefore creates
   enforcement beyond I4. Evidence:
   `handoffs/PLAN_OF_RECORD_2026-08-26.md:51-62,162-167`.

## (c) Recommendations

- State whether the live batch is sealed or host-run and name the exact combined preflight/configuration.
- Name the probe path, batch ID, seed, evaluator profile, timeout, request size, and every sub-agent output path before launch.
- Define numerically the envelope, narrow/wide, plausible effect, borderline, consistent direction, and multi-metric aggregation terms.
- Pre-register handling for correctness regressions, missing usage, censored attempts, contaminated baselines, and unequal per-task sample counts.
- Give the probe author a mechanically isolated input set that excludes task names as well as manifests, checkers, and references.
- Enumerate the exact archive moves and tombstone paths.
- Name and authorize the standalone analysis-code path without placing it in a directory frozen by I1.
- Define how net instruction-text decrease is counted when full documents are moved to `archive/` and tombstones are added.
- Preserve the rev-3 Wade rulings in an independent dated artifact rather than only in the plan they authorize.
- Make any freeze hook enforce replacement-only semantics instead of relying on commit-author identity.
- Define a measurable success/failure criterion for Purpose question 2, since Step 2b designs but does not run a controlled governance experiment.
- Exclude `.mdseval-codex-home/tmp` from repository-copy test fixtures; the required suite ran 216 tests with 6 copy errors and 6 skips.

## Fresh-session executability

**No.** Before approval, the document remains a draft and cannot activate.
After approval, a fresh session still cannot execute it while honoring all of
its invariants:

1. Step 0's required specimen-index MD already violates I1's one-new-MD rule.
2. Step 1 cannot pass its only acceptance test because the probe arm has not
   yet been authored; authoring it in Step 1 violates I3.
3. The existing immutable runner cannot perform the conditional six-attempt
   extension, while a second batch violates I2 and I7.
4. The prescribed historical baseline has zero clean observations for two
   mandatory real tasks, only one full-task batch, and mutually incompatible
   timeout/search configurations. Its authorized fallback is itself barred by
   I2 and I7.
5. I2 permits an inconclusive final answer while D3 prohibits one, so the
   executing session has no invariant-consistent terminal behavior when the
   baseline cannot support the three-way decision rule.

The first two blockers occur before any live call; the next three prevent the
required Step 2a verdict even if the queue gate is bypassed.
