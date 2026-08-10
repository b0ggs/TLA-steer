# CODER beneficial-sensitivity protocol

Status: revised once after one statistical audit and one construct/scope audit;
approved for Milestone 2 planning

Protocol version: 0.2

Roadmap authority: `MD_EVAL_PROJECT_ROADMAP.md`

Applies to: Milestone 1 and the one-shot Milestone 2 diagnostic experiment

## 1. Purpose and claim boundary

The long-term project question is:

> For a fixed model, agent configuration, runtime, and coding-task population,
> does changing only the complete project-level `CODER.md` change how often the
> agent fully resolves the requested coding task, and at what measured cost?

This protocol does not compare candidate CODER files or select a champion. Its
smaller purpose is to establish that the evaluator can detect a deliberately
strong helpful instruction effect after correctly handling identical and
harmful controls. That is a manipulation check for the measurement system.

A passing experiment permits only this claim:

> Under the frozen diagnostic conditions, identical null files did not produce
> a winner under the predeclared decision rule, the harmful instruction lost in
> the expected direction, and the helpful instruction produced an observed
> macro-average increase in complete task resolution of at least 0.20 while
> rejecting the taskwise no-effect/exchangeability null at exact two-sided
> `p <= 0.05`.

It does not establish that:

- the helpful control is a good general-purpose `CODER.md`;
- any current candidate is better than another candidate;
- the diagnostic tasks represent ordinary coding work;
- a smaller practically useful effect would be detected;
- file content, file presence, length, and formatting have been separated; or
- the result generalizes to another model, role, runtime, or agent topology.

## 2. Authority and scope

This is a scientific protocol, not an implementation plan. Approval freezes the
scientific choices below but authorizes no production code, task creation,
treatment creation, or live model calls.

Before Milestone 2 work begins, one bounded implementation plan must name this
protocol and explicitly supersede the older V2 implementation plan for new
work. The older specifications, code, and evidence remain historical; they are
not silently reinterpreted. There may be only one active implementation plan.

Allowed Milestone 2 outputs are limited to:

1. one helpful control and its authorship record;
2. one frozen, checker-qualified diagnostic task pool;
3. the smallest runner/report changes required by this protocol;
4. calibration, control, and helpful-comparison evidence; and
5. one replayable report with the claim boundary above.

Candidate optimization, representative evaluation, confirmation holdouts,
leaderboards, dashboards, other roles, bundles, topology experiments, autonomous
generation, and security-platform work are deferred.

## 3. Construct and task population

### 3.1 Fixed construct

The positive-control construct is **complete coverage of explicit coding-task
requirements**: when a request contains several concrete deliverables and
constraints, the agent finishes all of them rather than completing only the
most salient code change.

This is a component of coding-task success, not a writing-style preference. The
helpful control may encourage systematic requirement coverage and verification,
but it may not encode task-specific APIs, filenames, literals, solutions, or
test commands.

### 3.2 Diagnostic population

The diagnostic population is small, original, self-contained Python repositories
using only the standard library. Each task must be feasible in one agent session
and must request three to five explicit, objectively checkable requirements. A
task should allow plausible partial completion but count as resolved only when
every required behavior and regression constraint passes.

The pool contains five candidate tasks in each of four strata:

- bug repair;
- feature addition;
- integration or executable behavior; and
- behavior-preserving refactoring or data handling.

Each task uses its own repository. Reused problem statements, shared code
templates that make failures dependent, and variants of the same underlying
task are prohibited. Natural requirement lists are permitted; prompts must not
tell the solver to use a checklist or reproduce the helpful control's wording.

This population is intentionally enriched for informative difficulty and
multi-requirement work. It is diagnostic, not representative.

## 4. Treatments and fixed runtime

### 4.1 Treatments

The complete project-level instruction file is the treatment.

- `N` — the operational null: a present, zero-byte `CODER.md`.
- `H` — the generic harmful control: the existing instruction that tells the
  agent not to change or implement anything, provided its bytes and hash remain
  frozen before any new task exists.
- `P` — a short, independently authored helpful `CODER.md` targeting only the
  construct in Section 3.1.

`N1` and `N2` are different blinded labels for byte-identical copies of `N`.
Every occurrence of a treatment uses the same frozen bytes. The champion and
all candidate CODER files are excluded.

`N` must have SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
`H` is the existing `controls/coder/no-implementation-v2.md` with SHA-256
`aaf88530c73385ad6d38a45dae67be4872e650afc27d620a8d640430e2ec5606`.
`P` must be UTF-8 Markdown of at most 250 words and 4,096 bytes. It may contain
only general CODER-role guidance directed at Section 3.1 and must not mention
the evaluator, arms, controls, benchmarks, task families, or hidden evidence.

The estimand is the operational whole-file effect. This protocol does not use a
length-matched placebo and therefore does not isolate helpful semantic content
from file presence, format, or length. A later study making that narrower claim
must justify and preregister an active placebo.

### 4.2 Subject runtime

All subject calls use the same existing Codex adapter and the following frozen
condition:

- model alias `gpt-5.6-sol`, reasoning effort `high`;
- one fresh ephemeral session and fresh Git workspace per attempt;
- one subject agent, with subagents disabled;
- workspace-write sandbox and a 300-second per-attempt timeout;
- agent-command network access off, using the existing runner setting;
- no evaluator source, hidden checks, other treatments, or prior evidence in
  the subject workspace; and
- no LLM qualitative judge calls.

The exact Codex CLI version, evaluator commit, wrapper hash, runtime arguments,
and service-reported model metadata are recorded and held constant throughout
the run. Disabling network is a condition of this self-contained diagnostic,
not a claim that network access cannot help on a representative workload.

The shared wrapper supplies only the coding request, workspace authority, and
ordinary execution rules. It must not teach the target construct, disclose an
arm, suggest a solution, or require a process that duplicates `P`.

## 5. Independent authorship and access boundaries

People or fresh agents may fill more than one role only when their prior access
does not violate the boundary for the later role. Each role receives the
minimum packet below and signs an access attestation.

| Role | May see | Must not see before freeze |
| --- | --- | --- |
| Protocol owner | This protocol and historical public evidence | Exact new tasks or `P` while making protocol choices |
| Helpful-treatment author | Sections 1, 3.1, 4.1, and the file-size/content restrictions | Candidate tasks, checks, solutions, mutants, calibration, or scored outcomes |
| Task-pool author | Sections 1, 3, and checker requirements | Exact `P`, candidate/champion files, or treatment outcomes |
| Task validator | Candidate tasks, checks, correct solutions, and mutants | Exact `P` and all live outcomes |
| Operator | Frozen artifacts and a generated blinded schedule | Unblinding information not needed to execute the schedule |
| Subject solver | One task workspace, shared wrapper, and one treatment file | Other arms, hidden checks, evaluator source, prior evidence, or experiment labels |
| Analyst | Frozen analysis program and locked raw evidence | Outcome-dependent discretion; treatment mapping is revealed only after mechanical outcomes are locked |

The treatment and task authors work independently from the same public
construct, not from each other's artifacts. `P`, `H`, the twenty-task pool,
checks, wrapper, and analysis rules are hashed before calibration begins.
Neither author may revise an artifact after seeing calibration or treatment
outcomes. Alignment between tasks and the construct is documented only after
both sides are frozen; a gap is reported rather than repaired in place.

## 6. Objective qualification before model calls

Every candidate task must pass deterministic qualification without a model
call. Its checker must:

1. fail the pristine repository on at least one requested behavior while its
   own environment/self-checks pass;
2. accept two materially different correct implementations;
3. reject two plausible partial or incorrect implementations, with each
   requested behavior exercised by at least one negative case;
4. preserve unrelated behavior through explicit regression checks;
5. depend on observable behavior rather than an exact reference patch unless
   the user-facing requirement itself is structural;
6. produce the same result on three repeated executions of pristine, correct,
   and mutant states; and
7. keep checks, reference solutions, mutants, and their paths outside the
   subject workspace.

A separate validator reviews prompt clarity, requirement-to-check coverage,
checker independence, repository isolation, and task uniqueness. One bounded
author correction pass is allowed before the entire pool is frozen. A task that
still fails is removed before calibration; it is not repaired after outcomes.
All twenty qualified tasks must exist before calibration starts.

## 7. Null-only calibration and task selection

Calibration uses `N` only. It is selection evidence, never comparison evidence.

1. Run six fresh `N` attempts on each of the twenty frozen candidate tasks:
   120 subject calls.
2. Randomize task order within each of six replicate rounds using the frozen
   schedule seed.
3. Mark a task diagnostically eligible only when `N` resolves it in one through
   five of six attempts. This screens observed complete ceilings and floors;
   it does not establish the task's true solve probability.
4. Within each of the four strata, select exactly four eligible tasks. Rank by
   distance from three successes, then by the ascending SHA-256 of
   `selection_seed || task_id` to break ties.
5. If any stratum has fewer than four eligible tasks, stop the experiment. Do
   not add, edit, or recalibrate tasks under this protocol version.

The result is sixteen selected tasks from sixteen independent repositories.
Their calibration attempts are excluded from every scored null estimate.

After selection, the frozen power simulation is rerun using each selected
task's Laplace-smoothed null rate `(successes + 1) / 8` and a hypothetical
+0.30 helpful effect capped at 1.00. If estimated power is below 0.80, stop
before either scored wave. No treatment outcome may influence selection or the
power check.

The widened eligibility band prevents a six-attempt pilot from discarding
nearly all otherwise centered task pools by chance. Ranking still prefers three,
then two or four, then one or five successes. Any passing claim conditions on
the realized null-selected set, which may contain fallback tasks with one or
five calibration successes. Under independent `Binomial(6, 0.5)` calibration,
this rule gives a 0.9638 probability that all four strata contain at least four
eligible tasks; that is a feasibility calculation, not end-to-end power.

## 8. Fresh scored observations and randomization

### 8.1 Control wave

For every selected task, collect one fresh attempt under each of `N1`, `N2`,
and `H`: 48 subject calls. Within each task block, randomize the three-call
order. Randomize task-block order with the frozen schedule seed.

- A/A uses `N1` versus `N2`.
- Harmful sensitivity uses the predesignated `N1` observation versus `H`.
- `N2` is not pooled into the harmful comparison because unequal arm sizes
  would invalidate the specified task-level sign-flip test.

The helpful wave does not start unless both control gates pass.

### 8.2 Helpful wave

For every selected task, collect four fresh `N` and four fresh `P` attempts:
128 subject calls. Use four replicate rounds. Within each round, randomize task
order; within each task, run one `N`/`P` pair consecutively and randomize which
arm runs first. Run with parallelism one.

No calibration or control observation is reused. Treatments, task files,
checks, wrapper, runtime, analysis, seeds, and decision rules remain frozen.

## 9. Outcomes and estimand

### 9.1 Primary outcome

For treatment `m`, task `t`, and fresh attempt `r`, define:

`Y[m,t,r] = 1` only if the final workspace passes every task-specific functional
and regression check; otherwise `Y[m,t,r] = 0`.

Timeouts, false completion, missing deliverables, agent-caused test failures,
and subject-process failures after a usable turn are failed attempts, not
infrastructure retries. Mechanical failure cannot be overridden by a judge.

For each selected task `t`, let `p[m,t]` be the probability that a fresh attempt
under treatment `m` and the frozen runtime has `Y = 1`. For arms `A` and `B`,
the finite selected-set estimand is
`theta[A-B] = mean_t(p[A,t] - p[B,t])`. Claims condition on the realized
selected diagnostic set.

Estimate it with the within-task difference
`d_t = mean(Y[A,t,*]) - mean(Y[B,t,*])` and the equally task-weighted
macro-average `hat_Delta = mean(d_t)` across the sixteen tasks. Repeated
attempts are nested measurements, not extra tasks.

### 9.2 Secondary outcomes

Report separately, without changing a gate:

- mechanically verified requirement-coverage fraction;
- input, cached-input, output, and reasoning tokens when available;
- wall time, tool calls, failed commands, and timeout status;
- files changed, added, or removed and patch size;
- verification commands executed; and
- task, stratum, and repeat-level outcomes.

No post-hoc weighted score is permitted. Missing usage telemetry remains
missing and never changes correctness. Dollar cost is neither estimated nor
gated because ChatGPT OAuth does not expose a per-call API charge here.

## 10. Statistical analysis and prospective power

### 10.1 Exact test

For each comparison, discard zero `d_t` values only from the sign enumeration,
not from the effect estimate. Enumerate every sign assignment to the absolute
nonzero task effects and compute the exact two-sided probability of a signed
sum at least as extreme in absolute value as the observed sum. Use `alpha =
0.05`. Report the exact p-value, all `d_t`, `hat_Delta`, and the number of
nonzero task effects.

This is an exact conditional test only under the sharp taskwise distributional
no-effect null: within each task the complete arm labels are exchangeable under
independent, equiprobable arm-order randomization, with no interference across
tasks. It is not an exact test of the weak null `theta = 0` alone. Service drift
is mitigated, not eliminated, by paired randomization. Unrecorded arm-dependent
runtime differences or inter-task interference break exchangeability and
therefore the integrity gate.

Also report a 95% stratified percentile task-bootstrap interval for `hat_Delta`:
resample four tasks with replacement inside each of the four strata, use
100,000 resamples,
and use a frozen analysis seed. Sort the bootstrap estimates and use the values
at zero-based indices `floor(0.025 * (B - 1))` and
`ceil(0.975 * (B - 1))`, where `B = 100000`. The interval is descriptive
stability evidence for the selected set; it does not support population
generalization. The exact test and observed effect floor define the gate.

### 10.2 Prospective design

The helpful manipulation check uses sixteen tasks and four attempts per arm.
Its observed effect floor is `hat_Delta >= +0.20`; because outcomes advance in
units of `1/64`, the smallest attainable passing estimate is `13/64 =
0.203125`. The planning alternative is a strong +0.30 absolute increase in
resolution probability; this is not a claim that smaller effects are
unimportant.

A 100,000-simulation standard-library Monte Carlo calculation used seed
`20260810`, independent Bernoulli attempts, sixteen independent tasks, four
attempts per arm, the exact test above, and the joint pass rule
`hat_Delta >= 0.20` and `p <= 0.05`. It used one continuous Python
`random.Random` stream; for each null rate in the listed order and each
simulation, it drew four helpful Bernoulli attempts followed by four null
attempts for tasks 1 through 16. The prespecified grid and results are:

| Null rate | Helpful rate | Estimated gate power |
| ---: | ---: | ---: |
| 0.20 | 0.50 | 0.8726 |
| 0.25 | 0.55 | 0.8589 |
| 0.30 | 0.60 | 0.8482 |
| 0.40 | 0.70 | 0.8468 |
| 0.50 | 0.80 | 0.8730 |
| 0.60 | 0.90 | 0.9184 |
| 0.65 | 0.95 | 0.9445 |

Monte Carlo standard error was at most 0.0012. The implementation must
reproduce each value within 0.005. The post-calibration check uses 100,000
simulations, seed `20260811`, the selected tasks' individual smoothed null
rates in ascending task-ID order, a per-task +0.30 effect capped at 1.00, and
the same draw order and gate.

This power calculation is conditional power for the helpful gate under its
independent-Bernoulli and effect assumptions. It is not the probability that
the calibration and all conjunctive controls will pass, and the plug-in
post-calibration calculation does not remove uncertainty in six-attempt null
rates. It supports only a deliberately strong diagnostic effect.
It does not show 80% power for a +0.20 effect and must not be cited to justify a
later candidate comparison. Milestone 4 requires a new power analysis for its
smallest practically worthwhile candidate effect and representative sampling
frame.

The one-attempt-per-arm harmful gate is deliberately a gross-harm check. With
sixteen tasks and a two-sided exact test, it cannot pass unless at least six
tasks favor `N1`, so its smallest attainable passing effect is `6/16 = 0.375`.
If `H` always fails, its pass probability is approximately 0.190, 0.593, and
0.895 at homogeneous null rates 0.25, 0.375, and 0.50, respectively. This may
cause an honest false stop at low baseline rates; it cannot create evidence for
a harmful-control win and is not covered by the helpful-gate power statement.

### 10.3 Multiplicity and equivalence

The three gates are conjunctive: all must pass for the allowed claim. No gate is
selected after observing another. Secondary metrics are descriptive and are
not tested for a winner, so no multiplicity correction is applied to them.

Failure to reject in A/A is not evidence of equivalence. This protocol never
returns `EQUIVALENT` and defines no equivalence margin.

## 11. Predeclared gates and verdict

Apply the same directional winner rule to each nonidentical comparison: the
expected better arm must have observed `hat_Delta >= +0.20` and exact two-sided
`p <= 0.05`. This rule does not establish that the true `theta` is at least
0.20; doing so would require a test or lower confidence bound against
`theta <= 0.20`.

1. **Integrity/oracle gate:** every frozen hash, runtime invariant, checker
   qualification, task count, stratum balance, schedule, and evidence field is
   present and valid.
2. **A/A gate:** applying the winner rule in either direction to `N1` versus
   `N2` returns no winner. Record this as `NO_FALSE_WINNER`, not equivalence.
3. **Harmful gate:** `N1` beats `H` under the directional winner rule.
4. **Helpful gate:** `P` beats fresh `N` under the directional winner rule.

The experiment verdict is `SENSITIVITY_DEMONSTRATED` only if all four gates
pass. Any integrity failure yields `INVALID`. Any valid control or helpful gate
that does not pass yields `SENSITIVITY_NOT_DEMONSTRATED`, with the observed
effect and uncertainty reported. An effect in the unexpected direction fails;
it is not relabeled after inspection.

If any stratum has fewer than four eligible tasks, or if the valid
post-calibration power gate fails, the result also is
`SENSITIVITY_NOT_DEMONSTRATED` and terminates before scored waves. It is not
`INVALID` and authorizes no replacement, recalibration, or another run.

## 12. Call ceiling, invalid runs, and stopping

A subject call is one launched Codex solver attempt, whether it succeeds,
fails, times out, or returns unusable output. The full base experiment is:

| Stage | Base subject calls |
| --- | ---: |
| One authenticated smoke attempt | 1 |
| Null calibration: 20 tasks x 6 | 120 |
| Control wave: 16 tasks x 3 | 48 |
| Helpful wave: 16 tasks x 8 | 128 |
| **Full base maximum** | **297** |

Only a failure attributable to the evaluator, machine, authentication, or model
service before a usable subject turn is infrastructure-invalid. Preserve it and
rerun the entire affected task block, never only the preferred arm. Before any
call, freeze both the complete fallback schedule and an arm-blind mechanical
invalidity table. On an allowed infrastructure invalidity, mark every
observation in the original affected block `SUPERSEDED`, exclude the whole
block from analysis, and analyze exactly one complete replacement block in its
predesignated fallback position. Every nonlisted failure is `Y = 0`; an invalid
replacement makes the experiment `INVALID`.

At most one block may be replaced in each live stage: six calibration calls,
three control calls, and eight helpful calls. The absolute ceiling is therefore
314 subject calls. The smoke attempt is not retried. Authoring or validation
model calls, if used, are disclosed separately and never counted as subject
observations.

Stop immediately, preserving evidence, when any of these occurs:

- smoke, oracle, hash, isolation, balance, or authorship validation fails;
- any stratum has fewer than four diagnostically eligible tasks, or the
  post-calibration simulated helpful-gate power is below 0.80;
- a stage needs a second infrastructure block replacement;
- the A/A or harmful gate fails;
- a frozen artifact would need to change;
- the 314-call ceiling would be exceeded; or
- the helpful wave finishes, whether it passes or fails.

There is no automatic tuning, replacement task, second positive control, or
repeat-until-pass loop. A later attempt requires a newly versioned protocol and
must be described as a new experiment. Pauses or machine restarts do not by
themselves invalidate a run if hashes, the untouched schedule, and append-only
evidence prove an exact block-boundary resume.

## 13. Evidence and report

Before the first call, preserve a manifest containing every artifact hash,
authorship attestation, access packet, role assignment, runtime setting, seed,
task stratum, qualification result, decision rule, call ceiling, and planned
schedule. Raw attempt evidence is append-only.

The final report must show:

- the exact question, construct, diagnostic population, and allowed claim;
- null, harmful, and helpful hashes without revealing labels before analysis;
- every calibration result and deterministic selection decision;
- every task-by-arm outcome, `d_t`, macro effect, exact p-value, bootstrap
  interval, and power result;
- all secondary efficiency and behavior metrics without a composite score;
- invalid calls, retries, pauses, missing telemetry, deviations, and failed
  gates; and
- explicit distinctions among diagnostic sensitivity, practical value, and
  candidate superiority.

Offline replay must regenerate the result from raw evidence without model calls.

## 14. Definition of done

Milestone 1 is complete when this protocol passes exactly one statistical audit
and one construct/scope audit, receives at most one bounded revision, and is
approved by the user.

The authorized Milestone 2 experiment is administratively closed when the
approved implementation:

- creates and freezes independent artifacts without an access violation;
- either obtains sixteen balanced eligible tasks or stops at the predeclared
  eligibility/power gate;
- runs no more than the declared call ceiling;
- preserves and replays all evidence; and
- stops with either `SENSITIVITY_DEMONSTRATED`,
  `SENSITIVITY_NOT_DEMONSTRATED`, or `INVALID`.

The Milestone 2 scientific exit gate passes only on
`SENSITIVITY_DEMONSTRATED`. Either other verdict closes this experiment without
satisfying the exit gate or authorizing another run.

A scientifically honest failure is a completed experiment, not permission to
iterate until a preferred result appears.

## 15. Literature foundation and local choices

| Source | Status | What it informs here |
| --- | --- | --- |
| [Chen et al., HumanEval](https://arxiv.org/abs/2107.03374) | Published benchmark paper | Functional correctness and repeated samples |
| [Jimenez et al., SWE-bench](https://arxiv.org/abs/2310.06770) | Published benchmark paper | Repository-level task resolution |
| [DeepSWE](https://arxiv.org/abs/2607.07946) | 2026 preprint | Original tasks and implementation-agnostic verification |
| [Bjarnason, Silva, and Monperrus](https://arxiv.org/abs/2602.07150) | 2026 preprint | Stochastic variation and repeated pass-at-one measurement |
| [Gloaguen et al.](https://arxiv.org/abs/2602.11988) | 2026 preprint | Context-file null comparisons and possible instruction costs |
| [Zhang et al.](https://arxiv.org/abs/2604.11088) | 2026 preprint | Controlled persistent-rule interventions |
| [Shepard and Albrecht](https://arxiv.org/abs/2606.20512) | 2026 preprint | Fixed-condition evaluation of repository guidance |
| [Khatri](https://arxiv.org/abs/2607.27250) | 2026 preprint | Agent-specific difficulty and null effects |
| [Cawley and Talbot](https://www.jmlr.org/papers/v11/cawley10a.html) | Peer-reviewed | Selection bias from tuning on evaluation data |
| [Dwork et al.](https://doi.org/10.1126/science.aaa9375) | Peer-reviewed | Risks from repeated adaptive holdout use |
| [Lakens](https://doi.org/10.1177/1948550617697177) | Peer-reviewed | Why non-significance is not equivalence |
| [Card et al.](https://aclanthology.org/2020.emnlp-main.745/) | Peer-reviewed | Prospective power analysis in NLP experiments |

The construct, four strata, synthetic task population, calibration band,
sixteen-task sample, four helpful repeats, effect floor, exact sign-flip test,
power model, retry rule, and call ceiling are local design choices. They are not
presented as requirements from the cited literature.

Unresolved questions intentionally deferred past this manipulation check are
external validity, sensitivity to smaller effects, representative task
sampling, active-placebo design, qualitative code quality, network-enabled
work, cross-model stability, and role-specific protocols beyond CODER.
