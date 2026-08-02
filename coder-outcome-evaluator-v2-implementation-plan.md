# CODER Outcome Evaluator V2 — Demonstrable MVP Plan

## Authority and current state

This file is the sole active V2 implementation authority. It replaces the
feasibility-only version preserved at commit `74fe907d9a2aaf69b8395b5e1759df3aeab693e0`.
The earlier 907-line design remains preserved at commit
`a4fe6e5dffa7e037fd1d92338a7ce357df902863`; it is reference material, not a
second plan.

The research rationale in
`which-coder-md-is-better-literature-backed-evaluation.md` (source SHA-256
`f94dabfa83eb7e6af92648fc5aed8bd7ca18f19ac9df0e08c684d7c29a800d96`) informs
this plan but does not independently authorize work.

The completed feasibility run is preserved at
`runs/v2-pilot-20260802T020828Z-aeddd926`. It made 16 subject calls, preserved
raw evidence, recorded no invalid or infrastructure observations, and resolved
all four tasks in both arms. It established that the runner works and that the
four tasks have a ceiling effect. It did not establish a winner or equivalence.

This plan does not itself authorize implementation, commits, pushes, merges, or
live calls. Those require explicit user approval. Root orchestrates and verifies
scope but does not implement production or test code.

## Goal

Deliver a demonstrable evaluator MVP, not another infrastructure MVP:

> With model, harness, tools, runtime limits, and task pack fixed, the evaluator
> must detect a prospectively defined, generically harmful `CODER.md`, must not
> invent a winner between byte-identical A/A arms, and must issue an evidence-
> backed result for champion versus `karpathy-v1` on objective coding outcomes.

The final demonstration is one command that produces preserved raw evidence,
machine-readable results, and a compact human-readable report containing control
gates, per-task outcomes, estimated one-attempt success, exact decision evidence,
tokens, duration, and the exact claim boundary.

The MVP is successful only if the control demonstration works. The real A/B
result may be `A_BETTER`, `B_BETTER`, or `INCONCLUSIVE`. A valid evaluator cannot
promise that two competent files differ or force a winner when evidence is weak.

## Claim boundary

The experimental treatment is the exact hash-locked complete Markdown file. The
primary outcome is full task resolution, not resemblance to Karpathy's style.
The strongest permitted real-candidate claim is:

> On this frozen eight-task synthetic Python repository pack and configuration,
> file A or B produced higher estimated task-macro one-attempt resolution and met
> the predeclared rule.

This MVP cannot establish a universally best coder file, a Karpathy-style causal
effect, cross-language generality, or deployment-population performance. Those
require separately approved representative sampling and confirmation work.

## Non-negotiable invariants

- Preserve raw run evidence and immutable hashes for instructions, tasks,
  fixtures, checks, configuration, and analysis code.
- Never modify a candidate, control, task, checker, decision rule, retry rule, or
  resource limit after the first subject call.
- Never expose candidate identity to a qualitative judge; this MVP makes zero
  qualitative-judge calls.
- Mechanical failures cannot be overridden by any model or narrative score.
- Separate subject failure from infrastructure invalidity using frozen symmetric
  retry and pair-invalidation rules.
- Unit tests and CI make zero live calls and use only the Python standard library.
- Task authors and verifier reviewers may not inspect candidate contents, prior
  candidate trajectories, or candidate identities.
- Findings outside this plan are recorded as deferred; they do not create work.

## Demonstration design

### Frozen treatments

Freeze hashes and label bindings before task authoring begins:

1. `C1` and `C2`: control-wave blinded labels containing byte-identical champion
   bytes. The analysis must not special-case their equal hashes.
2. `H`: a short generic harmful control, written and frozen before task content,
   that instructs the agent not to modify code or implement the request. It may
   not mention task types, repositories, filenames, tests, or expected answers.
3. `A1` and `A2`: real-comparison blinded labels containing byte-identical fresh
   champion bytes. They are new calls, not reused control observations.
4. `B1` and `B2`: real-comparison blinded labels containing byte-identical frozen
   `karpathy-v1` bytes.

Every label is executed in an independent fresh session and workspace. The runner
may not deduplicate equal bytes, responses, or task states.

The existing `controls/coder/deliberately-bad.md` is ineligible because it names
specific legacy tasks and implementation shapes. No task-specific control may be
reused.

### Frozen task pack

Author exactly eight candidate-independent, moderate repository tasks across four
small synthetic Python-standard-library repositories: two bug fixes, two
features, two integration changes, and two compatibility-preserving refactors.
Each repository contributes at most two tasks. Do not reuse the four ceiling
pilot tasks as scored evidence.

This is a balanced MVP pack, not a claim of deployment representativeness. The
task author and verifier reviewer are spawned with `fork_turns="none"`, receive
only the workload/checker packet and an exact allowed-path list, are forbidden
from candidate, control, and prior-trajectory paths, and must attest that they did
not access them.

Every task must have, before any live call:

- an outcome-only contract that does not prescribe process, style, target files,
  root cause, reproduction ceremony, or solution shape;
- a pristine fixture that fails hidden acceptance while passing relevant
  pre-existing regression checks;
- a deterministic reference change that passes acceptance and regressions;
- at least one structurally different correct change that also passes;
- at least two plausible semantic mutants that fail for the intended reason;
- anti-tampering and protected-input checks; and
- deterministic repeatability across three offline checker executions.

If eight tasks cannot meet these requirements inside the caps, stop. Do not weaken
the checks, duplicate trivial tasks, or add infrastructure to reach the count.

### Primary outcome and repeat handling

For run `r`, task `t`, and MD `m`, `Y[m,t,r]` is one only when the observation is
valid, subject integrity holds, and all acceptance and regression checks pass.
Otherwise a valid subject attempt is zero. Infrastructure-invalid observations
are excluded and handled only by the frozen symmetric retry policy.

For each MD and task, estimate ordinary one-attempt reliability as the arithmetic
mean of its independent `Y` values. Macro `pass@1` is the unweighted mean of those
per-task estimates. Repetitions are nested observations, never additional tasks.
The existing all-repeats-must-pass aggregation must be replaced and regression-
tested before live use. All-runs reliability and at-least-one retry success may be
reported separately but cannot decide the winner.

### MVP decision rules

Before implementation, the user must approve a practical effect threshold
`delta_mvp`, expressed as an absolute task-resolution percentage-point gain. The
recommended default is 10 percentage points; it is a deployment choice, not a
number supplied by literature. With eight tasks and two attempts per real MD,
macro differences occur in 6.25-point increments, so a nominal 10-point threshold
has an effective smallest observable passing value of 12.5 points.

The decision implementation must be completely exercised on synthetic data and
frozen before calls. For each task, let `d_t` be B's mean resolution minus A's
mean resolution, and let `T` be the mean of the eight `d_t` values. Exhaustively
enumerate all `2^8` task-block sign flips, carrying every repetition within a task
together. The exact two-sided p-value is the fraction whose absolute flipped mean
is at least `abs(T)`. Alpha is 0.05. Call this an exact paired sign-flip test under
task-block exchangeability; do not call it a randomization test merely because
run slots are randomized.

This task-level test supports only the frozen-pack claim. It assumes every task's
subject calls use independent fresh sessions and workspaces, that A/B outcomes are
exchangeable within a task under the null, and that no shared run state couples
outcomes across tasks. Two tasks may use separate snapshots of one synthetic
repository because repository similarity is fixed content, not shared execution
state. If those execution assumptions do not hold, the task-level test is invalid
and the MVP stops. Any inference to a repository or deployment population must
instead preserve repository clustering and remains deferred.

- `B_BETTER`: `T >= delta_mvp`, the exact two-sided p-value is at most 0.05, and
  no integrity disqualification occurred.
- `A_BETTER`: `T <= -delta_mvp`, the same two-sided p-value is at most 0.05, and
  no integrity disqualification occurred.
- `INCONCLUSIVE`: every other valid real-candidate result.
- `INVALID`: a frozen validity/integrity gate prevents interpretation.

The eight-task MVP does not declare statistical equivalence. Non-significance is
not a tie. A later powered study may add equivalence only after defining a target
population and deriving its task count prospectively.

### Control gates

The complete decision path must pass all of these before a real A/B result is
eligible:

1. **Offline null calibration:** for every attainable eight-task difference-
   magnitude pattern, enumerate every sign assignment and verify that the full
   gated workflow's chance of returning either winner cannot exceed alpha.
2. **Live A/A:** applying the ordinary decision code to `C1` versus `C2` must not
   declare either byte-identical label better. A false winner stops the MVP; do
   not rerun it away. This one live A/A comparison is an end-to-end symmetry
   diagnostic, not an empirical estimate of the false-positive rate.
3. **Live known-better control:** the same ordinary comparator used for real MDs
   must return `A_BETTER` for `C1` bound as A versus `H` bound as B. At least six
   tasks must favor `C1`, with zero favoring `H`; six unanimous discordances have
   exact two-sided probability 0.03125. This proves gross outcome sensitivity,
   not fine discrimination between competent files or general validity.
4. **Oracle controls:** every task's pristine/reference/alternative/mutant and
   repeatability checks must pass before live calls.

No task or control may be edited after observing a failed gate. A failed gate
produces `STOP/REDESIGN` and ends spending.

### Efficiency

Record input, cached-input, output, reasoning, and total tokens when available;
wall time; tool/model call counts; and failures for every attempt. Correctness is
the only MVP decision outcome. Tokens and time are separate descriptive results
and are never folded into a weighted score or used to rescue a correctness loss.

## Bounded live waves

Live execution requires one explicit user authorization recording the model,
reasoning setting, timeout, retry rule, maximum subject calls, maximum wall time,
and dollar ceiling. Zero qualitative-judge calls are permitted.

Run every wave as randomized complete task blocks, preserving blind labels:

- **Wave 1 — controls:** `C1`, `C2`, and `H` once on each task: exactly 24 planned
  subject calls. Stop unless every control gate passes.
- **Wave 2 — fresh real comparison:** `A1`, `A2`, `B1`, and `B2` once on each task:
  exactly 32 more planned subject calls. Interleave all four labels within each
  task block. Never reuse control-wave champion observations as real evidence.

Every launched subject invocation counts, including invalid, interrupted, and
failed calls. Base cap is 56 launched calls. If an observation is infrastructure-
invalid, preserve the entire affected task block as superseded evidence and rerun
that complete three- or four-label block once; never replace one arm selectively.
At most one block retry is allowed across the complete demonstration and it may
launch at most four calls. The absolute cap is 60 launched calls. A second invalid
block, an incomplete balanced block, or a cap breach produces `INVALID`; analysis
never averages unequal arm/task denominators.

## Implementation stages and gates

Implementation begins only after the user approves this audited plan and
`delta_mvp`. Root delegates bounded packets; agents may not spawn subagents.

### Stage 0 — Freeze contract and treatments

Before editing implementation or task content, run the repository's full offline
unit suite once at the exact starting commit in the designated worktree. It must
be green. The docs-only planning check found two pre-existing clean-worktree
errors: a fixture test assumes an ignored `.pyc` exists, and the historical-
inventory test assumes an ignored `reports/evidence-index.json` exists and matches
its canonical inventory. If either reproduces, stop before MVP implementation and
request a separate decision; do not copy, regenerate, or rewrite historical
evidence to force a green baseline.

Record the seven blind-label bindings and hashes, model/runtime configuration,
analysis rule, randomization seed derivation, retry/invalidation table, live caps,
and permitted paths. Create the generic harmful control before task authoring.

Gate: the exact starting baseline is green, task authors can work without
candidate/control access, and no unresolved measurement choice can change after
seeing outcomes.

### Stage 1 — Repair measurement and reporting offline

Implement only task-level pass@1 aggregation, the exact paired decision function,
control-gate evaluation, and compact JSON/Markdown reporting. Reuse the existing
runner/evidence plumbing; do not create a second runner or framework. Test the
complete gated workflow, null, superiority, inferiority, inconclusive, invalid,
repeat aggregation, deterministic reporting, and cap enforcement using synthetic
observations.

Gate: the old ceiling pilot replays as `INCONCLUSIVE`; synthetic known-better and
null cases produce the predeclared decisions; no live path runs in tests.

### Stage 2 — Author and audit the task pack offline

One candidate-blind agent authors the eight tasks. A different candidate-blind
reviewer checks outcome neutrality, tamper protection, and repeatability and must
independently produce at least one additional alternative correct change and one
additional plausible semantic mutant per task. Record all findings without a
repair at this stage. This verifier review is the first of the plan's exactly two
post-authoring review passes and also serves as the statistical/correctness review.

Gate: initial author checks pass and the reviewer has either found no blocker or
recorded every blocker for the single global repair. Candidate execution remains
forbidden. Final oracle acceptance occurs at the Stage 3 gate.

### Stage 3 — Repository verification and scope audit

Run `python -m unittest discover -s tests -v`, then conduct the second and final
post-authoring review pass: one blocker-only scope review. Collect its findings
with the Stage 2 verifier/statistical findings, permit exactly one global bounded
repair, and run the full suite exactly once afterward. No stage has a separate
repair allowance and no third review is permitted.

Gate: tests and every task oracle pass after the one allowed global repair (or
without repair), no live calls occurred, every cap holds, and the frozen run
manifest can be produced. Then stop and request explicit authorization to commit
the permitted implementation paths. After authorization, create the commit,
record its exact SHA and frozen input hashes, and verify the implementation
worktree is clean at that SHA. Only then may root request live authorization. This
gate authorizes neither a push nor a merge, and live execution from an uncommitted,
dirty, or different commit is forbidden.

### Stage 4 — Demonstrate controls live

After explicit authorization, execute Wave 1 once. Preserve all evidence and
produce the interim human-readable control report.

Gate: A/A, known-better, oracle, integrity, and environment gates pass. Otherwise
stop permanently on this frozen pack and report the failed construct.

### Stage 5 — Compare the real MDs and finish the MVP

Only after Stage 4 passes, execute Wave 2 without modifying any frozen input.
Generate the final JSON and Markdown report and independently reproduce the
decision from raw observations.

Gate: the report shows that the ordinary comparator selected the known-better
control opponent, gives one honest real A/B outcome, includes per-task and
efficiency evidence, and states the narrow claim. It also states that eight tasks
with two attempts per real MD is intentionally low-powered and likely inconclusive
for modest competent-MD differences. This is the demonstrable MVP exit.

## Hard implementation caps

Caps exclude preserved/generated raw run evidence but include all hand-written
code, tests, fixtures, and documentation after this plan is approved:

- At most 20 changed implementation paths from an explicit predeclared allowlist.
- At most 2 new production modules and 350 net new production lines.
- At most 900 added task/fixture/check lines.
- At most 500 added unit-test lines.
- At most 1,750 total hand-written added lines; deletions do not offset additions.
- At most 2 implementation agents total, never concurrently editing the same path.
- Exactly 2 implementation review passes, at most 1 global repair cycle after all
  offline findings are collected, and no recursive audits.
- At most 3 full unit-suite executions before live authorization.
- Zero new dependencies, networked task execution, containers, public benchmark
  imports, dashboards, optimizers, generalized role abstractions, or other roles.
- Offline implementation wall time at most 6 hours; any overrun stops for user
  review rather than silently expanding.

Before each agent starts, root records its exact allowed paths and acceptance
criteria. After each stage, root reports changed paths, added-line counts, tests,
elapsed time, and remaining caps. Any requested work outside these bounds is
classified `MVP_BLOCKER`, `DEFER`, or `REJECT`; only `MVP_BLOCKER` may enter the
single repair pass.

## Demonstrable MVP acceptance checklist

The MVP is complete only when all are true:

- One documented command runs the frozen demonstration and another regenerates
  the report from raw evidence without model calls.
- The generic harmful control was frozen before tasks and the ordinary comparator
  selects champion over it under the predeclared decision rule and discordance
  gate.
- Byte-identical A/A arms use the ordinary analysis and produce no false winner.
- Eight tasks passed pristine/reference/alternative/mutant/repeatability audits.
- The real champion-versus-`karpathy-v1` comparison returns exactly one allowed
  outcome without qualitative override.
- Raw trajectories, patches, checks, hashes, tokens, durations, invalidity/retry
  records, and reports are preserved.
- The repository's full unit suite passes and no hard cap was exceeded.
- No champion replacement, merge, or generalized claim occurs automatically.

## Explicitly deferred after MVP

- A minimal/no-special-instruction baseline, deployment-representative sampling,
  multiple languages, public benchmark qualification, and real-repository
  dependency/container support.
- Prospective power analysis for a larger study, equivalence testing, and a fresh
  independently controlled confirmation lockbox.
- Candidate optimization, automatic MD editing, dashboards, publication work,
  and AUDITOR/RESEARCHER/ORCHESTRATOR evaluators.
- A matched Karpathy-style causal ablation; whole-file A/B results cannot answer
  that causal question.

These are potential next phases, not MVP incompleteness. None may be started from
an auditor suggestion or unused budget.

## Plan-audit dispositions

Three independent read-only audits were incorporated in one revision pass:

- Statistics: adopted a two-sided exact test, fresh contemporaneous real arms,
  balanced block retries, and a 60-launched-call absolute cap.
- Construct validity: required the ordinary chooser to select the known-better
  control, operational task-author blindness, independent verifier challenges,
  and narrower report language.
- Scope: expanded only the path allowlist from 16 to 20, consolidated all repairs
  into one global pass, and removed the nongating minimal baseline and bootstrap.

Requests for more tasks, external benchmarks, equivalence/power infrastructure,
qualitative judging, dashboards, generalized roles, and recursive reviews were
deferred or rejected for this MVP.

## Stop conditions

Stop immediately if the designated worktree is dirty outside permitted paths; a
candidate or frozen input changes; a task author sees candidate material; a task
checker cannot accept an alternative correct implementation or reject its
mutants; infrastructure and subject failures cannot be classified deterministically;
a control gate fails; a cap would be exceeded; a new dependency or live call is
proposed without authorization; evidence would be discarded; or a second repair
or audit loop is requested.

On stop, preserve evidence, identify the exact failed gate, and request one user
decision. Do not weaken checks, replace failed observations, add tasks, tune an MD,
or rerun controls to manufacture a successful demonstration.
