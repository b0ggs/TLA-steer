# Plan of Record — 2026-08-26 (DRAFT rev 5)

Status: DRAFT. Wade must approve this revision before implementation or live
model spend. Rev 5 replaces rev 4; the prior audit reports are historical
inputs, not requirements.

## Outcome

This is a finite exploratory work order, not a new governance system. It does
four things:

1. retires the old governance pack while preserving it as history;
2. replaces the Section 12–14 preflight process with a deterministic mechanical
   preflight that completes in 60 seconds or less;
3. runs one paired null-versus-probe batch to see whether a short general-purpose
   instruction file changes token cost, wall-clock time, or execution trajectory;
4. produces a small, zero-spend design note for experiments on process-building
   failure modes.

This phase does not develop tasks, hunt for more correctness headroom, build an
instruction optimizer, or create replacement governance.

## Boundaries

- Preserve all existing `runs/` evidence and git history.
- `tooling/taskcheck.py` remains the sole task-admission mechanism. No manual
  review or second admission layer may be added.
- Pre-exposure mechanical failures may be repaired and retried. Once the first
  usable subject attempt launches, the selected tasks and both arm files are
  immutable. An exposed defective task is retired rather than edited.
- Live subject calls require the existing `REQUEST.json` / `APPROVED.json`
  spend approval. There is no other execution approval.
- Do not make live model calls from tests or CI. Production code remains Python
  standard-library only.
- Do not create another plan, audit, gate, role, hook, receipt system, specimen
  index, tombstone set, or deferred-recommendation ledger.

## Fixed experiment decisions

- Cohort: `full-boltons-wraps-forwarding`,
  `full-click-stream-lifecycle`, `full-flask-automatic-options`, and
  `full-starlette-websocket-denial`. These four tasks are already admitted and
  are the exact cohort in `scripts/contain/contamination-spec.json`.
- Arms: the existing zero-byte `controls/coder/null-m2.md` and one new short
  cost/time probe at `controls/coder/cost-time-probe-v1.md`.
- The probe may contain only general workflow and efficiency guidance. It may
  not name or hint at a cohort task, repository, bug, expected fix, checker, or
  private requirement. It is committed before queueing; `REQUEST.json` then
  records and binds its SHA-256.
- Batch: `cost-time-probe-v1`, task-order seed `20260826`, three attempts per
  arm per task, 24 nominal calls and 32 maximum calls under the runner's
  existing one-infrastructure-replacement-per-task-arm policy.
- Runner: `gpt-5.6-sol`, high reasoning, workspace-write sandbox, approval
  policy `never`, sub-agents disabled, agent-command network disabled, web
  search disabled, serial execution, and a **900-second subject-attempt
  timeout**. The container images, interpreter pins, and contamination-spec
  hash are copied unchanged from
  `runs/dev-v2/maximum-difficulty-search-disabled-v2/REQUEST.json`.
- The preflight deadline is **60 seconds for the complete four-task cohort**.
  It is unrelated to the 900-second subject-attempt timeout.
- This is one exploratory batch. There is no attempt-count extension, second
  batch, selective retry, or confirmatory claim.

## Step 1 — Retire the governance pack

Move the following existing material, without changing its contents, under
`archive/governance-pack-2026-08-26/`, preserving each current relative path
beneath that directory:

- `TASK_TOOLING_V2_PLAN.md`
- `CODER_BENEFICIAL_SENSITIVITY_*.md`
- `M2_INDEPENDENT_SCIENTIFIC_REVIEW.md`
- `MD_EVAL_EXPERIMENT_REDESIGN_REQUIREMENTS.md`
- `MD_EVAL_PROJECT_ROADMAP.md`
- `coder-outcome-evaluator-v2-*.md`
- `codex-cloud-handoff-*.md`
- `docs/bad-control-20260731-2-audit.md`
- `docs/coder-single-file-mvp-spec.md`
- `docs/multi-candidate-implementation-plan.md`
- `docs/stage-1-qualification-and-reusable-evaluator.md`
- `handoffs/M2_INDEPENDENT_REVIEW_PROMPT.md`
- `handoffs/SECTION_12_PREBUILD_AUDIT_2026-08-22.md`
- `handoffs/SECTION_13_PROBE_LIST_REVIEW_2026-08-23.md`
- `handoffs/SECTION_14_PREFLIGHT_REVIEW_2026-08-24.md`
- `handoffs/TASK_FACTORY_V2_PROPOSAL.md`
- `handoffs/AUDIT_PLAN_OF_RECORD_REV1_2026-08-26.md`
- `handoffs/PLAN_REDTEAM_2026-08-26.md`
- `handoffs/PLAN_OF_RECORD_2026-08-26_AUDIT_FACTS.md`
- `handoffs/PLAN_OF_RECORD_2026-08-26_AUDIT_INVARIANTS.md`
- `handoffs/PLAN_OF_RECORD_2026-08-26_AUDIT_EXECUTION.md`
- `handoffs/DEFERRED.md`

Leave `docs/historical-evidence-v1-inventory.json` at its current path because
the active historical-evidence verifier reads it there. Commit every currently
untracked Markdown file either at its current active path or at its archive
destination; do not leave the evidence set only in a working tree.

In `AGENTS.md`, replace the current long document-authority bullet with the
short statement that archived planning and review documents are historical
evidence only and authorize no work. Keep the product definition and the
remaining mechanical safety/workflow bullets, including taskcheck-only
admission and the ban on extra enforcement or receipt infrastructure. Update
the active `README.md` and `OVERVIEW.md` only as needed to remove stale
authority language and repair links to moved files.

Do not delete historical material, alter run evidence, add tombstones, create an
index, or install a hook. Git history and the archive are the preservation
mechanism.

## Step 2 — Build the fast deterministic preflight

The current preflight is not the target. It recursively scans host/container
filesystems, reruns task checkers, requires six separately committed evidence
files per task, and treats `timeout_seconds == 600` as a proxy for Section 14
mode. That last coupling makes a valid 900-second request fail in
`scripts/run_batch.py::_launch_record`.

Replace that path; do not add a wrapper around it.

### Required interface

Add a `preflight` subcommand to `scripts/run_batch.py` using the same task,
container, runner, and arm inputs as `queue`. `queue` must invoke the same
preflight function before writing `REQUEST.json`, and `run` must invoke it once
again before the first subject attempt of that invocation.

The preflight performs only these mechanical checks:

1. request shape, task IDs, arm paths and hashes;
2. admitted task bytes against each existing manifest and ledger, using the
   hash-only `taskcheck.verify(..., md_filename=None)` path;
3. Docker availability, exact content-addressed image IDs, interpreter pins,
   and a readable isolated auth source;
4. one sealed-runtime smoke check per unique image/interpreter pair proving the
   intended mounts, interpreter identity, sandbox/network policy, and effective
   `web_search="disabled"` setting;
5. targeted checks of the contamination specification's named answer-bearing
   modules and fix signatures inside the sealed runtime.

It must not recursively scan the host, recursively scan the whole container,
run public/reference task checkers, make a model request, or require pre-existing
or git-tracked `preflight/` files. Preserve old batches' preflight files as
historical run evidence, but remove `_launch_record` as a prerequisite for new
batches. Remove the `timeout_seconds == 600` / Section 14 coupling; any positive
attempt timeout accepted by the runner must use the same preflight semantics.

New requests use an explicitly identified batch-request schema v3 for this fast
preflight contract. Keep existing v1 and v2 requests and their verification path
read-only and working; do not rewrite historical requests or preflight evidence.

Compute the needed runtime seals once per `run` invocation and reuse them for
that invocation's attempts rather than repeating the policy probe before every
subject call. Normal attempt evidence may include the compact seal summary; do
not create a separate receipt system.

The tool uses one monotonic 60-second deadline for the complete cohort. It emits
one final JSON object containing `status`, `duration_seconds`, and any failed
check names, then exits zero on pass and nonzero on failure.

### Step 2 acceptance

- Repair the existing repository-copy fixture in `tests/test_config.py` so it
  excludes `.mdseval-codex-home`. That live, volatile authentication directory
  is not test input and currently causes six `shutil.copytree` race errors.
- Unit tests cover pass/fail behavior, the global deadline, no-model-call
  behavior, 900-second timeout independence, and queueing without a
  batch-local `preflight/` directory.
- Against the fixed four-task cohort and the existing sealed images, one real
  invocation returns `PASS` in no more than 60 seconds on the execution host.
- `python3 -m unittest discover -s tests -v` passes.

If the real invocation exceeds 60 seconds, Step 2 is incomplete: report the
slow check and simplify or remove it. Do not restore the governance pack or
relax the deadline silently.

## Step 3 — Freeze and run the paired probe

Create `controls/coder/cost-time-probe-v1.md` in a clean context that receives
only the general efficiency brief and the destination path—not the cohort IDs,
contamination specification, task manifests, checkers, reference solutions, or
prior subject solutions. Its guidance should favor focused inspection, targeted
tests, minimal edits, and stopping once the requested behavior is verified. No
authorship receipt or review gate is needed. Commit the probe, the fast
preflight implementation, and the associated tests before queueing.

Queue `cost-time-probe-v1` with the fixed decisions above. The successful queue
creates `runs/dev-v2/cost-time-probe-v1/REQUEST.json`; commit that request and
ask Wade for the existing hash-based `APPROVED.json`. Do not launch before the
approval hash matches. After approval, run the batch serially and require
`python3 scripts/run_batch.py verify cost-time-probe-v1` to pass before
analysis.

An infrastructure failure is handled only by the runner's existing replacement
policy. A task or arm result is never selectively rerun for scientific reasons.

## Step 4 — Analyze the batch offline

Implement one standard-library analysis command at
`scripts/analyze_cost_time_probe.py`. For each task and arm, report all
attempts and the median of:

- primary token cost: `input_tokens - cached_input_tokens + output_tokens`;
- subject wall-clock `duration_seconds`, with a timeout shown as censored at
  900 seconds;
- trajectory length: the number of distinct completed item IDs in
  `events.jsonl` whose item type is `command_execution` or `file_change`.

Also report usage completeness, resolution/checker results, changed paths, and
the ordered tool-call categories. Do not report dollar prices or infer
time-to-first-action when the event data lacks timestamps.

Classify each numeric metric independently:

- `NOT MEASURABLE` if fewer than three tasks have at least two usable attempts
  in each arm for that metric;
- otherwise `DIRECTIONAL SIGNAL` if at least three tasks both (a) have an
  arm-median difference larger in magnitude than that task's null-arm range and
  (b) share the same nonzero sign;
- otherwise `NO DIRECTIONAL SIGNAL`.

These cases are mutually exclusive. They are descriptive triage, not a
significance test or causal claim. A correctness result below 3/3 in either arm
is reported prominently as a regression risk but does not change the metric
classification. A usable attempt is a finalized valid attempt; token cost also
requires `usage_reported == true`. The arm-median difference is probe minus
null; the null-arm range is its maximum usable value minus its minimum.

Write the machine-readable output to
`runs/dev-v2/cost-time-probe-v1/analysis.json` and a concise human summary at
`handoffs/COST_TIME_PROBE_RESULT.md`. Do not extend or rerun the batch because
of the result.

## Step 5 — Design the process-failure experiment

Using only already-preserved git and run evidence, write
`handoffs/PROCESS_FAILURE_EXPERIMENT_DESIGNS.md`. It contains:

- a small set of mechanically computable outcomes such as off-task file bytes,
  instruction/plan-text growth, and requested-product completion; and
- at most three short controlled experiment designs that could test whether an
  instruction file changes those outcomes.

This step makes no live calls and builds no task, detector, taxonomy, platform,
or enforcement mechanism. The file is a design input for Wade, not authority
for another phase.

## Finish

Run the full unit suite, commit the two result documents and preserved batch
evidence, and stop. Wade then decides whether to invest in cost/time instruction
work, process-failure experiments, both, or neither.
