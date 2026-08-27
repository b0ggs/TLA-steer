# Independent factual audit of `PLAN_OF_RECORD_2026-08-26.md` rev 3

Date: 2026-08-26. This audit read the 253-line plan in full and checked its
claims against the working tree, `runs/dev-v2/`, task ledgers, runner and
containment code, Git history, handoffs, and committed handoff archives. It did
not treat the plan or its prior audit as evidence for their own claims.

## (a) Factual errors in the document

1. **The existing champion was explicitly made and designated as the canonical champion.** D2 says it "was never made to be a champion" (`handoffs/PLAN_OF_RECORD_2026-08-26.md:92-95`). The original locked MVP specification calls it "the current CODER.md champion," identifies its source baseline, and requires creation of `targets/coder/champion.md` from exact canonical bytes (`docs/coder-single-file-mvp-spec.md:14-17,47-65`). The experiment configuration maps the `champion` variant to that path (`experiments/coder-v1.json:24-27`), and commit `ba1d396` added it as part of the evaluator MVP. It may never have been optimized for cost/time, but the narrower statement in D2 is factually false.

2. **The named historical null evidence cannot supply the claimed per-task between-batch envelope after the plan's required contamination filter.** Step 2a says the analysis excludes every baseline attempt containing `web_search` and then uses spread across baseline batches (`handoffs/PLAN_OF_RECORD_2026-08-26.md:189-196`). In each Phase 3 sealed batch, all three Doctest attempts and all three Tomli attempts are contaminated; only one of three Enum attempts and all three Boltons attempts are clean. Thus the combined clean counts are Boltons 6, Doctest 0, Enum 2, and Tomli 0, with Enum represented by one observation per batch. The repository's existing audit records exactly eight contaminated attempts in each batch and identifies the clean attempts (`handoffs/COST_AND_WEBSEARCH_ANALYSIS_2026-08-24.md:436-495`; raw evidence under `runs/dev-v2/phase3-real-null-sealed-v1/` and `runs/dev-v2/phase3-real-null-sealed-replication-v1/`). For each selected `full-*` task, the plan names only `maximum-difficulty-search-disabled-v2`, which is one batch, so an across-batch envelope does not exist there either (`runs/dev-v2/maximum-difficulty-search-disabled-v2/REQUEST.json`). Four of the six mandatory tasks therefore lack the asserted between-batch baseline, and two lack any contamination-free baseline attempt.

3. **The preserved baseline is not "config-matched" to any possible single live batch over the selected mixed cohort.** The two Real baselines use 300 seconds and container spec `b18ec65...` with no disabled-search binding; the Full baseline uses 600 seconds, container spec `129e6d...`, and `web_search: "disabled"` (`runs/dev-v2/phase3-real-null-sealed-v1/REQUEST.json`, `runs/dev-v2/phase3-real-null-sealed-replication-v1/REQUEST.json`, and `runs/dev-v2/maximum-difficulty-search-disabled-v2/REQUEST.json`). Timeout is one batch-global runner field (`scripts/run_batch.py:28-29,126-137`), so one live batch cannot match both 300- and 600-second baselines; the optional 900-second Click setting matches neither. The current containment runtime hardcodes one current contamination spec (`scripts/contain/runtime.py:6-8,27-28`), and the current spec contains only the four `full-*` tasks (`scripts/contain/contamination-spec.json`); Git shows that the old Real and current Full specs are distinct commits and hashes. Filtering observed searches cannot retroactively turn a search-enabled configuration into the live disabled-search configuration. The plan's categorical "config-matched" description (`handoffs/PLAN_OF_RECORD_2026-08-26.md:103-107`) is false.

4. **The repository does not preserve the developer-session evidence needed for two claimed governance specimens or for `directive-override events`.** The plan calls cross-session state hallucination and the August 21 overridden-directive incident evidence to be indexed, then calls directive-override events computable from preserved evidence (`handoffs/PLAN_OF_RECORD_2026-08-26.md:137-151,229-233`). A repository and archive scan finds only secondary assertions about those incidents in the plan/red-team prose, not the underlying developer-session transcripts. The local evaluator profile has zero rows in `.mdseval-codex-home/state_5.sqlite:threads`, zero rows in `.mdseval-codex-home/logs_2.sqlite:logs`, and no session files; no developer-session transcript is in the committed handoff archives. The plan itself concedes that Claude session transcripts are outside the repository and deferred (`handoffs/PLAN_OF_RECORD_2026-08-26.md:147-151`; `handoffs/DEFERRED.md:29`). Git can support plan-growth measurements, but it cannot establish what directive was presented and overridden or what state an agent hallucinated. Those claimed preserved/computable evidence classes are absent.

5. **Not everything listed as out of scope is on the Deferred list.** The plan says all listed items live in `handoffs/DEFERRED.md` (`handoffs/PLAN_OF_RECORD_2026-08-26.md:247-253`). That file does not list the challenge site, task factory, failure-mining platform, broad source modifications, or new confirmatory experiments; it contains narrower related entries such as the challenge pack, specific runner features, and powered confirmatory cost claims (`handoffs/DEFERRED.md:8-29`).

## (b) Internal contradictions

1. **The plan's handling of prior recommendations violates I8.** I8 says a category-(c) finding is appended to `DEFERRED.md` and changes nothing else (`handoffs/PLAN_OF_RECORD_2026-08-26.md:71-75`), while the status says all prior recommendations were logged unchanged (`handoffs/PLAN_OF_RECORD_2026-08-26.md:3-6`). The prior audit classified as recommendations: using `capture.json`/`diff.patch`, recording the batch-global timeout, defining the Step 2b clock, and designating a canonical taxonomy (`handoffs/AUDIT_PLAN_OF_RECORD_REV1_2026-08-26.md:118-142`). Rev 3 implements each in the live plan (`handoffs/PLAN_OF_RECORD_2026-08-26.md:145,180-183,215-221,226-227`); two are not even present in `DEFERRED.md`. Those Step 0/2 changes are exactly what I8 forbids for category-(c) findings.

2. **Step 0 violates I1's no-other-MD rule.** I1 applies for the entire phase and permits exactly one newly authored MD, the probe MD, with "no other MD authoring" (`handoffs/PLAN_OF_RECORD_2026-08-26.md:35-47`). Step 0 requires creation of the new `handoffs/SPECIMEN_INDEX.md` (`handoffs/PLAN_OF_RECORD_2026-08-26.md:137-145`). Both instructions cannot be obeyed.

3. **D3's extension to six attempts violates I1 and cannot be executed by the existing runner.** D3 and Step 2a permit extending the live arm from three to six attempts per task (`handoffs/PLAN_OF_RECORD_2026-08-26.md:103-105,184-186`), while I1 forbids runner/tooling changes (`handoffs/PLAN_OF_RECORD_2026-08-26.md:41-47`). The runner hardcodes three rounds, a nominal count of three per task/arm, at most one replacement, and no more than four launched calls per task/arm (`scripts/run_batch.py:131-137,496-528,569-575`; `tooling/taskcheck.py:390-395`). `handoffs/DEFERRED.md:14` explicitly defers parameterized attempt-count support. Six attempts cannot occur inside the one approved batch without the changes I1 prohibits; a second three-attempt batch would violate I2.

4. **D3's fallback null mini-batch violates I2 and the Step 2a cap.** I2 says Step 2a is one batch and allows no rerun regardless of outcome (`handoffs/PLAN_OF_RECORD_2026-08-26.md:48-50`), and Step 2a is capped at one batch (`handoffs/PLAN_OF_RECORD_2026-08-26.md:174`). D3 authorizes a fresh null-arm mini-batch if the historical baseline is unusable (`handoffs/PLAN_OF_RECORD_2026-08-26.md:111-112`). The actual baseline defect in finding (a)(2) makes this more than a hypothetical branch, but the two instructions contradict even without that fact.

5. **The mandatory six-task sealed cohort violates I1's frozen-tooling constraint.** Step 2a mandates six tasks before the optional Click task (`handoffs/PLAN_OF_RECORD_2026-08-26.md:174-183`), but the containment probe mechanically accepts only three-to-five-task specifications and rejects six (`scripts/contain/probe.py:33-40`; `tests/test_containment.py:23-42`). The runtime also hardcodes one spec path (`scripts/contain/runtime.py:6-8`). A config-matched sealed execution therefore requires changing frozen containment code or splitting the cohort, respectively violating I1 or I2; an unsealed batch would not repair the false config-match claim in (a)(3).

## (c) Recommendations

- Preserve D2, D3, and D5 in an independent Wade-authored or signed artifact before the supersession commit.
- Define numerical, collectively exhaustive thresholds for "consistent direction," "majority," "narrow enough," "plausible," "feasible n," and "borderline."
- Use a contemporaneous randomized null arm if the result is intended to support a treatment-effect interpretation.
- Pre-register missing-usage, timeout-censoring, task-exclusion, denominator, and cross-task aggregation policies.
- Name the exact archive/tombstone set, batch ID, seed, evaluator profile, container specification, CLI, and deliverable paths before execution.
- Specify an isolation and provenance mechanism proving that the probe-MD author did not inspect forbidden task material.
- Define how "net instruction text" is measured and whether archived text counts.
- Either define a mechanically verifiable meaning of "non-Wade edit" for the optional hook or omit that check.
- Place the standalone analysis code at a named path outside the I1-prohibited `scripts/`, `tooling/`, and `src/` trees.
- Define a metric schema mapping each Step 2b behavior to the exact preserved artifact and computation used.

## Can a fresh session execute the plan as written?

**No.** Before approval, the document is a draft and authorizes nothing beyond
Step 0. Even after approval, there is no invariant-compliant execution path:

- Step 0 must author `SPECIMEN_INDEX.md`, which I1 forbids.
- The prescribed contamination-filtered historical baseline has no clean data for two mandatory Real tasks and no between-batch envelope for either mandatory Full task, so the Step 2a decision rule cannot be applied as written.
- A single live batch cannot be config-matched to historical baselines that use different search settings, timeouts, and containment specs; the containment probe also rejects the mandatory six-task cohort, so sealing it requires prohibited code changes or multiple batches.
- The borderline extension to six attempts is unsupported by the frozen runner, and the fallback null mini-batch violates the one-batch/no-rerun invariant.
- The preserved developer-session evidence required for cross-session hallucination and directive-override metrics is not in the repository or committed archives.
- The plan has already applied category-(c) recommendations in violation of I8.

The existing CLI does support a one-arm, three-attempt request using a new
nonempty control under `controls/`; that repair from rev 1 is real. It does not
remove the blockers above.
