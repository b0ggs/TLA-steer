# CODER Outcome Evaluator V2 Remediation Plan

## Authority

Once separately authorized by the user, this plan is the sole remediation
implementation authority. `coder-outcome-evaluator-v2-implementation-plan.md`
remains the sole V2 experiment and CODER feasibility-pilot authority. This plan
overrides only its conflicting clauses identified below; every non-conflicting
requirement remains binding.

## Objective

Repair the V2 MVP's qualification, integrity, usage accounting, evidence capture,
CLI, and scope controls without changing the frozen experiment.
The result must be executable and reject invalid evidence rather than merely record
decorative assurances.

## Frozen/non-changeable experiment

The following are frozen and cannot change during remediation:

- all eight task manifests, prompts, fixtures, and intended task semantics;
- champion, candidate, and control contents;
- statistical method, alpha, delta, decision rules, and outcome definitions;
- labels, schedule, call caps, target model, and reasoning level;
- task allocation, treatment allocation, and blinding rules;
- dependencies, including the Python-standard-library-only constraint;
- V1, other roles, benchmarks, dashboards, and optimizer work.

No live model call is permitted in unit tests or CI, or under this plan.

## Seven repairs

1. **Remove the monetary gate.** Delete the dollar ceiling and every runtime
   argument, validation branch, receipt claim, and help entry that enforces it.
   Record only `ChatGPT OAuth` as the authentication mode. Preserve the finite
   three-hour wall-clock ceiling, 300-second per-call cap, and 60-call cap.
   Removed monetary arguments must be rejected, not silently ignored.

2. **Replace the oracle assertion with executable qualification.** Remove
   `--oracle-controls-passed`. A tracked `qualify` command must execute all eight
   frozen tasks against pristine state (fail), two distinct correct variants
   (pass), and two semantic mutants (fail), with three repeat runs per case.
   Authoritative `qualify` must emit one immutable receipt bound by hashes to the
   exact verified commit, evaluator, task/checker set, oracle data, command
   configuration, and results. Stage 3 exercises the same cases provisionally
   without issuing that receipt. `run` must reject a missing, failed, stale, or
   mismatched authoritative receipt.

3. **Make environment integrity executable.** Before authoritative qualification
   or live use, require and record a clean exact commit, an isolated-runner
   preflight, and `ChatGPT OAuth` login mode. Record and compare start/end hashes
   for evaluator, design, analysis, wrapper, tasks, and treatments. Any mismatch
   is a hard failure.

4. **Protect workspace contracts.** Hash the workspace `CODER.md` and
   `.issue-contract.md` before and after every subject call. Record both pairs and
   mark the call invalid on any change; never allow qualitative judging to override it.

5. **Honor observed usage.** Consume `capture.py`'s `usage_reported` signal.
   Missing token or tool evidence makes only the associated efficiency evidence
   incomplete; it does not invalidate an otherwise valid objective task observation
   and does not enter the winner rule. Do not impute missing usage as zero. A zero
   tool count is valid when capture explicitly reports no tool events. Preserve the
   raw capture supporting the classification.

6. **Use truthful integrity evidence and preserve reconstruction evidence.** Delete
   the misleading `git_integrity` field. Replace it with clearly named baseline and
   final tree hashes plus the explicit patch or diff. Enforce and verify
   `wave_hashes`, or remove that field entirely; it must never remain decorative.
   For every subject call also save the resulting workspace snapshot and raw evidence.

7. **Remove runtime scope configuration and make the CLI truthful.** Delete
   `implementation_paths` from runtime input, schemas, and help. Changed-path scope
   exists only in this plan. Expose tracked `qualify`, `run`, and `replay` commands;
   their parser help and README examples must be accurate and executable. Removed
   arguments must be absent from help and rejected by parsing. Readability cleanup
   is allowed only in touched `outcome_mvp` code: no semicolon compression, broad
   refactor, or unrelated formatting churn.

## Exact allowed paths

Only these existing paths may change:

- `coder-outcome-evaluator-v2-implementation-plan.md`
- `experiments/coder-outcomes-v2-mvp.json`
- `src/mdseval/outcome_mvp.py`
- `tests/test_outcome_mvp.py`
- `README.md`
- `evals/mvp/coder-outcomes-v2/workflow/check.py`
- `evals/mvp/coder-outcomes-v2/catalog/check.py`
- `evals/mvp/coder-outcomes-v2/notifier/check.py`
- `evals/mvp/coder-outcomes-v2/ledger/check.py`

At most these two new paths may be created, and only when needed:

- `evals/qualification/coder-outcomes-v2/oracle-variants.json`
- `tests/fixtures/outcome-mvp-qualification-receipt.json` for a tracked receipt
  schema/example fixture, only if essential to test receipt validation.

This plan file is excluded from implementation path and size counts.
No other file may be created, deleted, renamed, or edited.
Generated test, oracle, qualification, and raw evidence may be written only beneath
designated ignored run directories or temporary directories; it is excluded from
tracked implementation path and size counts and must not be committed.

## Five stages/gates

1. **Freeze and baseline.** One implementer records the exact baseline commit,
   status, CLI help, hashes, and baseline result from
   `python -m unittest discover -s tests -v`. Confirm the frozen experiment and
   path allowlist. Gate: no unexplained baseline failure or frozen-content drift.

2. **Implement offline repairs.** The implementer completes only the seven repairs,
   adds deterministic unit tests including all negative cases below, and measures
   paths, bytes, Python AST statements, and formatting-only growth. Gate: all
   offline targeted tests pass and every cap is satisfied.

3. **Provisional oracle cases.** In the implementation worktree, execute all eight
   tasks, five required cases per task, and three repeats per case. Preserve all raw
   outputs, but do not issue or require the authoritative commit-bound receipt.
   Gate: every expected pass/fail repeats correctly without any live call.

4. **Full tests and independent verification.** Run
   `python -m unittest discover -s tests -v`. One independent verifier performs a
   read-only review of diff, scope, caps, frozen hashes, commands, negative tests,
   provisional oracle evidence, and raw outputs. Root orchestrates and writes no
   code. Gate: tests pass and the verifier accepts the exact tree as ready for
   separate commit authorization. If not, the same implementer gets at most one
   bounded repair pass, followed by affected provisional cases and one full-suite
   repeat. Across the plan, full-suite executions are capped at three: baseline,
   pre-verifier, and at most one post-repair repeat.

5. **Clean pre-live handoff.** This stage is conditional on separate user commit
   authorization. Preserve the current untracked
   `docs/stage-1-qualification-and-reusable-evaluator.md`; the user must approve
   whether it is committed, stashed, or moved, and this plan does not choose. Commit
   only the verifier-accepted tree, then verify its clean exact tree and commit plus
   authentication and isolated-runner preflight. Without another full-suite run,
   execute authoritative `qualify`, issue the commit-bound receipt, and hand off the
   evidence index and exact commands for a separate LIVE authorization decision.

## Negative acceptance tests

Automated tests must prove rejection or invalidation for:

- missing, failed, stale, or hash-mismatched oracle qualification receipts;
- a dirty worktree or a commit different from the receipt's exact commit;
- failed isolated-runner preflight or non-`ChatGPT OAuth` authentication mode;
- changed workspace `CODER.md` or `.issue-contract.md`;
- missing token or tool evidence, which must mark only efficiency evidence
  incomplete without invalidating objective outcomes or entering the winner rule;
- an explicit report of no tool events, which must preserve a valid zero tool count;
- evaluator, design, analysis, wrapper, task, or treatment start/end hash drift;
- missing explicit patch/diff, missing workspace snapshot, or missing raw capture;
- a present but incorrect `wave_hashes`, any retained `git_integrity` field, or
  missing/mismatched baseline or final tree hashes and explicit patch/diff;
- any removed dollar-ceiling, `--oracle-controls-passed`, or
  `implementation_paths` argument, which must be absent from help and rejected.

## Caps

- No more than 10 changed existing paths and two new paths; this plan is excluded.
- No more than 120 net-new Python AST statements.
- No more than 24 KiB net-new non-oracle source, test, and documentation bytes.
- Oracle variant data must not exceed 32 KiB.
- Physical line count is reporting only and cannot be met by semicolon compression.
- Report net bytes, net Python AST statements, and formatting-only growth separately.

## Stop conditions

Stop immediately on any frozen experiment drift, disallowed path, cap breach,
second repair pass, failed oracle case, failed full test, missing required evidence,
or dirty-commit/auth/preflight mismatch before live use.
Preserve all evidence and report the exact stopping condition; do not waive it.

## Final acceptance

Stage 4 implementation acceptance requires all seven repairs, all negative tests,
successful provisional oracle cases for all eight tasks and repeats, the full-suite
limit honored, caps met, no frozen drift, reconstructable evidence, and independent
read-only verifier acceptance after no more than one repair. Conditional Stage 5
pre-live acceptance additionally requires the clean exact committed tree, successful
auth/preflight, and its authoritative commit-bound qualification receipt. Neither
acceptance authorizes or executes a live run.

## Authorization boundary

This document grants no authorization to implement, commit, push, publish, or make
live model calls. Those actions require separate explicit user approval. The root
agent may coordinate only and must not write code. Once implementation is authorized,
one implementer owns all edits, one independent verifier remains read-only, and the
same implementer may perform at most one bounded repair pass.
