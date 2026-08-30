# Revised preregistration: Starlette-scoped correctness-first wall-clock and token confirmation

- **Original date:** 2026-08-29
- **Revised:** 2026-08-30
- **Status:** Draft for review and prospective power validation; **not authorization to make live calls**
- **Scope:** One candidate MD versus a zero-byte no-MD control on a prospectively frozen, ordered pool of new Starlette-type tasks
- **Decision target:** Correctness first, followed by conditional wall-clock and token efficiency on paired repetitions that both arms complete and resolve

This revision replaces the earlier text in this file. It removes the proposed
12-worker runner, the 24-call live concurrency calibration, raw-resource scoring
of failed attempts, and invented wall/token failure penalties. It does not become
a final frozen preregistration until the task pool, prospective power report,
schedule, analyzer, and runtime fields in Section 13 are populated and hashed.
The later live-call request and approval bind to the frozen preregistration; they
are not self-referential fields inside it.

## 1. Registered design

The working design is:

- candidate MD versus the zero-byte no-MD control;
- a prospectively frozen ordered pool of at most 20 candidate-unexposed tasks;
- a working target of 12 resource-eligible tasks;
- 3 fresh, paired repetitions per arm on every activated task;
- serial, back-to-back execution of the two arms in every pair;
- all scientific attempts included in correctness;
- wall time and tokens compared only within paired repetitions in which both
  arms complete normally and resolve mechanically;
- an observed aggregate correctness qualification for any overall favorable
  decision;
- wall time as the primary conditional resource endpoint; and
- tokens as a fixed-sequence conditional endpoint tested confirmatorily only if
  the complete wall criterion passes.

Each activated task consumes six planned subject calls. The campaign stops after
the task that produces the 12th resource-eligible task or after all 20 frozen
tasks have been activated, whichever comes first. The maximum planned scientific
call count is therefore 120, plus only the separately frozen ceiling for proven
infrastructure replacements.

The values `12` and `20` are working design values, not yet launch-ready power
claims. Before any live confirmation call, the prospective simulation in
Section 9 must validate them. If it does not, this draft must be amended and
refrozen before candidate exposure. After the first usable confirmation attempt
launches, the target, pool ceiling, pool order, and stopping rule may not change
in either direction.

No historical, development, admission, or infrastructure-qualification call
enters the confirmation analysis.

## 2. What this experiment can and cannot claim

### 2.1 Conditional resource estimand

The resource estimands are conditional on realized joint normal completion and
mechanical resolution. They compare the candidate and no MD only within
scheduled repeat pairs in which both arms completed normally and resolved, and
only across tasks satisfying the frozen resource-eligibility rule.

A favorable wall result permits wording such as:

> Among the first 12 resource-eligible tasks reached under the frozen pool and
> activation rules, and using only scheduled paired repetitions in which both
> arms completed normally and resolved mechanically, the candidate's task- and
> arm-order-balanced geometric-mean paired wall-time ratio was X% lower than no
> MD. The registered joint-sharp-null randomization test rejected in that
> direction (two-sided p = ...).

A favorable token result permits wording such as:

> Among the same resource-eligible tasks and jointly completed-and-resolved
> paired repetitions, the candidate's task- and arm-order-balanced
> geometric-mean paired uncached-input-plus-output token-proxy ratio was X% lower
> than no MD. The registered joint-sharp-null randomization test rejected in
> that direction (two-sided p = ...).

Neither template states that an isolated resource-only null was rejected. The
joint-null limitation in Section 2.3 must appear immediately after either claim.

These statements do **not** estimate:

- resource consumption per arbitrary attempted task;
- resource consumption over unresolved attempts;
- unconditional time or tokens per correct solution;
- performance on every task in the ordered pool;
- performance on a fixed set of 12 identities known before execution; or
- performance on Starlette work generally.

The first 12 resource-eligible task identities are outcome-dependent under a
fully prospective mechanical rule. The frozen benchmark object is the complete
ordered pool, not a preknown set of 12 resource tasks.

### 2.2 Correctness interpretation

Correctness uses every scientific attempt on every activated task. The
correctness qualification is an observed benchmark rule, not a statistical
non-inferiority test. Passing it does not establish correctness preservation and
does not rule out regressions on individual tasks or task types.

If the candidate has fewer decision-resolved attempts, conditional wall and token estimates
and registered tests are still reported. They may establish a narrow conditional
resource result, but the candidate is ineligible for an overall favorable
project decision.

Required wording in that case is:

> On jointly completed-and-resolved paired repetitions, the candidate's task-
> and arm-order-balanced geometric-mean paired [wall-time / token-proxy] ratio
> was X% lower, while decision-resolving A of B scientific attempts versus C of
> B under no MD. The observed correctness qualification failed. Correctness
> non-inferiority was not tested, and this is not an overall better-MD result.

### 2.3 Randomization-test interpretation

The registered randomization test evaluates the sharp null under which applying
the candidate rather than no MD changes neither scientific validity, normal
terminal completion, decision-resolution eligibility, nor the resource outcomes
of the scheduled pairs. Because the resource cohort conditions on
treatment-affected completion and correctness, the p-value is not an isolated
causal test of resource use when correctness may change.

This limitation must accompany every significance claim. The permitted claim is
the realized conditional comparison in Section 2.1, not an unconditional claim
that the MD is generally faster or cheaper.

## 3. Treatment, control, and runtime freeze

### 3.1 Control

- Path: `controls/coder/null-m2.md`
- Required bytes: zero-byte file
- SHA-256:
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

### 3.2 Candidate

- Path: `controls/coder/evidence-bounded-v1.md`
- SHA-256:
  `c0d56e29ade34c24278b976e84b29e47324c11a23399ca882239daffc9762c74`

The candidate remains fixed for this experiment. Changing its bytes creates a
new candidate and requires a new prospective freeze. It does not require a live
candidate-specific concurrency calibration.

This candidate hash must be frozen before any confirmation-task contract,
checker, solution, or pool information is used to tune the candidate. Any later
candidate-byte change makes every revealed pool task development material for
that new candidate.

### 3.3 Runtime

Before live authorization, freeze and hash:

- requested model and reasoning effort;
- CLI, wrapper, serial runner, and analyzer versions;
- container image digests and interpreter versions;
- sandbox and network policy;
- tool and subagent availability;
- token-accounting implementation;
- subject timeout of 900 seconds;
- candidate and control bytes;
- ordered task-pool and checker hashes;
- arm-order schedule and random seed; and
- replacement ceiling and reason codes.

The intended runtime is requested `gpt-5.6-sol`, high reasoning, isolated
containers, Python 3.11.5, and `max_parallel_runs = 1`. Subject containment must
disable subject network access, built-in web search, MCP servers, apps/connectors,
and subagents. A frozen mount allowlist exposes only the public task snapshot,
public contract, applicable candidate/control file, and required runtime.
Private checkers, reference and blind solutions, sibling attempts, historical
evidence, and solution-bearing Git history remain outside the subject mount.
The existing containment preflight verifies these conditions; this protocol
does not authorize a new security system.

Requested and observed runtime identities must both be reported. A contradictory
served identity is handled by the frozen infrastructure rule, never silently
accepted.

## 4. Task construction, admission, and ordered pool

### 4.1 Task profile

Every pool task must be a new candidate-unexposed Starlette-type coding task
with:

- async framework work;
- a nontrivial or slow test surface;
- interacting behavioral requirements;
- a deterministic private mechanical checker; and
- a distinct underlying issue contract and solution path.

Cosmetic variants, cloned fixes, or repeated versions of one underlying issue
do not count as distinct tasks. The previously exposed Starlette development
task is excluded from confirmation.

### 4.2 Admission

`tooling/taskcheck.py` is the sole admission mechanism. No manual audit or new
admission process may be layered on top of it.

No live subject call is part of admission. Reference and blind solutions must be
written to disk with provenance. Admission may not depend on a candidate effect.

If a separately approved no-MD development call is made after taskcheck, its
first usable subject launch freezes that task. Such a call cannot override or
supplement taskcheck. If it reveals a defect, the exposed task is retired and is
never repaired in place.

Every task must pass taskcheck before entering the pool. Before the first
candidate confirmation call, freeze and hash all 20 task packages and their
taskcheck ledger entries. Generate the pool order afterward from its own saved
random seed; human ordering is forbidden. Freeze and hash the resulting order.
A task may not be edited after a usable subject attempt launches. An exposed
defective task is retired, never repaired in place.

### 4.3 Frozen ordered pool and activation

The full ordered pool is part of the experiment. Reserve activation is not a
claim that an earlier task was defective and is not a retry of its scientific
outcome.

For each task in frozen order:

1. Run all three planned MD/no-MD pairs.
2. Preserve every launch and all evidence.
3. Determine resource eligibility using only the frozen completion, resolution,
   and arm-order rules in Section 5.
4. If fewer than 12 eligible tasks exist, activate the next task automatically.
5. Stop immediately after completing the task that produces the 12th eligible
   task or after task 20.

Activation must never depend on wall time, token use, effect direction,
p-values, qualitative impressions, or human choice.

If fewer than 12 tasks qualify after task 20, both resource endpoints are
confirmatorily inconclusive. Do not analyze a smaller cohort, lower the
eligibility threshold, add repeats, extend the pool, or add newly constructed
tasks to this experiment.

All activated tasks, including resource-ineligible tasks, remain in correctness
and in the published raw evidence.

## 5. Attempt, pair, and task outcomes

### 5.1 Scientific attempt and correctness

Freeze these mechanical definitions:

```text
valid_scientific_attempt = usable subject launch
                           AND preserved contained final tree
                           AND deterministic checker result

normal_terminal_record = no timeout or interruption
                         AND clean subject-process return
                         AND valid terminal lifecycle record

mechanically_passing_tree = complete private checker passes
                            AND protected-input integrity passes
                            AND final-tree integrity passes

decision_resolved = valid_scientific_attempt
                    AND normal_terminal_record
                    AND mechanically_passing_tree
```

Validity does not require correctness or complete token telemetry. The mechanical
result controls correctness; subject prose does not. A timeout whose preserved
final tree passes is reported separately as a mechanically passing timed-out
tree, but it is not `decision_resolved` and receives no correctness credit in the
aggregate qualification.

Normal incorrect completion, incomplete work, refusal, `BLOCKED`, voluntary
early exit, subject timeout, and subject-attributable protocol violation are
scientific outcomes. They occupy their planned slots, enter correctness, and are
never selectively rerun.

### 5.2 Jointly completed-and-resolved pair

For task `t` and repeat `i`, the pair is resource-usable exactly when both arms:

1. are valid scientific attempts;
2. have normal terminal records before the 900-second timeout;
3. are `decision_resolved`; and
4. have finite positive monotonic wall-duration evidence.

Let `J_t` be the set of resource-usable repeat indices. If either arm fails any
condition, neither arm from that pair enters either confirmatory resource
estimator. Both attempts remain in correctness, raw evidence, and exclusion
reporting.

The same `J_t` must be used for wall and tokens. Resource values may never decide
membership.

### 5.3 Resource-eligible task

Each task receives a prospectively randomized arm-order sequence:

```text
MNM  or  NMN
```

`M` means candidate-first and `N` means no-MD-first for that repeat. The sequence
for every pool task is generated by an independent fair random bit and frozen
before the first live confirmation call.

A task is resource-eligible only when:

```text
len(J_t) >= 2
AND J_t contains at least one candidate-first pair
AND J_t contains at least one no-MD-first pair
```

Every pair in `J_t` is used. If all three qualify, all three enter the estimator.
No one may select the fastest, cheapest, or otherwise most favorable two.

### 5.4 Missing token telemetry

For a pair outside `J_t`, missing token telemetry is reported but does not alter
pair or task eligibility.

For the final resource cohort `E`, every arm in every pair `i in J_t` must have
reconstructible registered token telemetry. Required components are nonnegative
integer `input_tokens`, `cached_input_tokens`, and `output_tokens`, with
`cached_input_tokens <= input_tokens`, and the derived `T` must be finite and
strictly positive. Other token components are auxiliary and are preserved when
reported but are not required to reconstruct `T`.

If any selected value is missing, inconsistent, nonfinite, or nonpositive, the
complete confirmatory token endpoint is **INCONCLUSIVE**. This rule applies only
to `t in E` and `i in J_t`; telemetry on other pairs cannot invalidate the token
endpoint. Do not delete the selected pair from tokens, impute a value, substitute
zero, activate another task because of the value, or rerun the attempt. The wall
endpoint remains separately interpretable.

## 6. Correctness qualification

Correctness includes all three final scientific slots per arm on every activated
task. Superseded pre-subject infrastructure launches do not enter the denominator.
Completed denominators must be equal:

```text
attempts_per_arm = 3 * number_of_activated_tasks
C_MD             = total decision-resolved candidate attempts
C_noMD           = total decision-resolved no-MD attempts
```

The observed correctness qualification is:

```text
C_MD >= C_noMD
```

Report overall and per-task counts, absolute and percentage-point differences,
timeouts, discordant pairs, and reasons for nonresolution.

This is a decision gate, not a p-value. The experiment does not claim statistical
correctness non-inferiority. If that stronger claim is later required, it needs a
separate margin, power analysis, and preregistration; it is not added to this
experiment after results exist.

Aggregate equality permits task-level tradeoffs. The report must show those
tradeoffs and may not describe the gate as proof of “no regressions.”

## 7. Conditional resource endpoints and analysis

### 7.1 Raw measurements

For every valid attempt, preserve raw wall time:

```text
W = subject_end_monotonic - subject_start_monotonic
```

Queue time, workspace setup, and post-run checker time are excluded. Provider
stalls, retries, or rate limits inside the subject process remain in `W`. For a
timeout, preserve the actual monotonic elapsed duration as raw evidence and
record `timeout_limit_seconds = 900` separately. The timeout is outside `J_t`;
no 900-second failure score is inserted into the conditional estimator.

Preserve the registered token proxy:

```text
T = input_tokens - cached_input_tokens + output_tokens
```

Also preserve gross input, cached input, cache-write input, output, reasoning,
and total token components. Reasoning tokens must not be double-counted if they
are already included in output. Failed-attempt tokens are reported but are
outside the conditional estimator. No token failure penalty or cap is invented.

### 7.2 Task effects

For endpoint `X` in `{W, T}`, task `t`, and usable pair `i`, define:

```text
z_X[t,i] = log(X[t,MD,i] / X[t,noMD,i])
```

For each eligible task, separate `J_t` by observed randomized order:

```text
J_M[t] = usable pairs in which MD ran first
J_N[t] = usable pairs in which no MD ran first

d_X[t] = 0.5 * mean(z_X[t,i] for i in J_M[t])
       + 0.5 * mean(z_X[t,i] for i in J_N[t])
```

This gives candidate-first and no-MD-first observations equal weight within each
task while using every usable pair. The confirmatory cohort `E` is the first 12
resource-eligible tasks under the frozen pool rule:

```text
D_X         = mean(d_X[t] for t in E)
R_X         = exp(D_X)
reduction_X = 100 * (1 - R_X)
```

Every eligible task receives equal top-level weight. Report all pair log ratios,
task effects, raw arithmetic arm means, `D_X`, `R_X`, and the percentage change.

### 7.3 Registered randomization test

The frozen analyzer performs a two-sided task-level sign-randomization test on
the 12 `d_X[t]` values, reflecting the independent prospective `MNM`/`NMN`
assignment. Under the registered joint sharp null, complementing a task's
`MNM`/`NMN` assignment leaves joint eligibility and the first-12 stopping path
unchanged, while the equal-order task effect changes from `d_X[t]` to `-d_X[t]`.

For a 12-value vector `d`, define the sample standard deviation with denominator
`11` and:

```text
S(d) = abs(mean(d)) / (sample_sd(d) / sqrt(12))

if sample_sd(d) = 0 and mean(d) = 0: S(d) = 0
if sample_sd(d) = 0 and mean(d) != 0: S(d) = +infinity
```

Enumerate all `2^12` sign assignments, recompute `S` for each signed vector, and
set the exact two-sided p-value to the fraction with `S_signed >= S_observed`.
All ties count as at least as extreme. The frozen synthetic fixture must cover
both zero-variance cases.

No confirmatory confidence interval is registered. Holding the realized selected
cohort fixed under nonzero treatment effects would require additional assumptions
about treatment effects on completion and eligibility. Report the point estimate,
all 12 task effects, their range, and the exact joint-null p-value without
presenting a model-dependent interval as ordinary 95% coverage.

### 7.4 Endpoint sequence and practical threshold

The planning alternative is a 30% conditional reduction:

```text
log(0.70) = -0.35667494
```

The practical observed-effect floor is a 20% conditional reduction. The floor
is a decision threshold, not proof that the true reduction is at least 20%.

The complete wall criterion is:

```text
registered two-sided p < 0.05
AND D_W < 0
AND observed reduction_W >= 20%
```

Wall is primary. The token endpoint is tested confirmatorily at two-sided
`alpha = 0.05` only if the complete wall criterion passes. Its complete criterion
is:

```text
registered two-sided p < 0.05
AND D_T < 0
AND observed reduction_T >= 20%
```

Wall is always estimated. Token status follows this frozen precedence:

1. If selected-pair token telemetry is incomplete or invalid, mark
   `TOKEN_INCONCLUSIVE`; no complete token estimate or p-value exists.
2. Otherwise, if wall fails, mark `NOT_TESTED_FIXED_SEQUENCE`; publish the token
   point estimate descriptively but no token p-value or confirmatory claim.
3. Otherwise, perform the registered confirmatory token test.

This fixed sequence controls the wall/token family-wise error rate without
building an omnibus “either endpoint wins” rule.

### 7.5 Decision labels

Use the following mechanical labels:

- `CORRECTNESS_ELIGIBLE`: `C_MD >= C_noMD`.
- `WALL_JOINT_NULL_REJECTED_WITH_CONDITIONAL_REDUCTION`: 12 eligible tasks exist
  and the complete wall criterion passes.
- `TOKEN_JOINT_NULL_REJECTED_WITH_CONDITIONAL_REDUCTION`: the wall label passes,
  token telemetry is complete, and the complete token criterion passes.
- `OBSERVED_CORRECTNESS_AND_CONDITIONAL_RESOURCE_ELIGIBLE`: all three labels
  above pass.

The final label is an internal finite-benchmark decision label. It must never be
shortened externally to “better MD.” It is not a claim of statistical correctness
preservation, unconditional efficiency, or general superiority.

## 8. Serial execution and arm order

The runner uses `max_parallel_runs = 1`. There is no live concurrency calibration
and no new concurrent pair-job system.

For every activated task and repeat:

1. create a fresh isolated workspace for the first arm;
2. run it and durably preserve complete evidence;
3. create a different fresh isolated workspace for the second arm;
4. run it immediately;
5. durably preserve complete evidence; and
6. bind both records to the task ID, repeat ID, and frozen order.

Task order, all `MNM`/`NMN` sequences, and the random seed are frozen before
launch. The sequence is never rebalanced after eligibility is observed. Every
task completes all three pairs before the next reserve decision.

## 9. Prospective power and pool adequacy

The former 85.1% wall and 83.3% token figures do not apply to this revision.
They assumed three unconditional resource observations on every fixed task, a
task-level t-test, and no correctness or fixed-sequence decision rule.

Before this draft can become final, run and preserve a standard-library-only
prospective simulation of the complete registered algorithm. It must model at
least:

- arm-specific task and repeat resolution probabilities;
- normal-terminal probabilities separately from checker-passing probabilities;
- within-pair dependence in resolution;
- association between resolution, wall time, and tokens;
- the probability that two or three pairs qualify;
- the two-order task-eligibility condition;
- ordered activation and stopping at 12 eligible tasks or task 20;
- task-to-task and repeat-level resource variation;
- wall/token correlation;
- missing or invalid selected-pair token telemetry;
- exhaustion of the frozen infrastructure-replacement rule;
- the exact randomization tests;
- the 20% observed-effect floors;
- fixed-sequence wall/token testing; and
- the observed correctness qualification.

The frozen power report must name one exact primary planning scenario and a
candidate-independent sensitivity grid. It must also freeze the PRNG algorithm,
seed, simulation count of at least 100,000 per scenario, and a one-sided 95%
Wilson lower-bound acceptance rule for each simulated probability threshold.
The point estimate alone cannot pass a launch threshold.

The frozen power report must provide:

- probability of reaching 12 eligible tasks by task 20;
- `P(G_W) = P(complete wall criterion | reach 12 eligible tasks)`;
- `P(G_W and G_T | reach 12 eligible tasks, joint planning effects)`, where
  `G_T` is the complete fixed-sequence token criterion;
- probability the observed correctness qualification passes under each declared
  correctness scenario;
- unconditional probability of each decision label; and
- sensitivity results over defensible resolution and heterogeneity ranges.

Launch requires at least:

```text
one-sided 95% Wilson lower bound for P(reach 12 by task 20) >= 0.95
one-sided 95% Wilson lower bound for P(G_W | reach 12) >= 0.80
one-sided 95% Wilson lower bound for
    P(G_W and G_T | reach 12, joint 30% planning effects) >= 0.80
```

These gates apply to the frozen primary planning scenario. The power report must
show every sensitivity-grid result and identify any region that fails, but a
sensitivity point is not silently promoted into or removed from the launch gate
after simulation. The primary scenario and grid are incomplete until their
hashes are populated in Section 13.

The correctness qualification is reported in the power simulation but has no
80% target because this experiment does not make a statistical correctness
claim.

If the working `12`/`20` design fails these criteria, change the target and pool
size only in a new reviewed version made before any candidate confirmation call.
Increasing the reserve ceiling improves the chance of reaching the target; it
does not increase conditional resource power once the target is fixed.

After confirmation begins, do not add tasks because failures occurred, because
an endpoint missed significance, or because the observed effect was smaller
than expected.

## 10. Validity, failures, and replacement

The runner must separately record at least:

- task, repeat, arm, and order;
- `valid_scientific_attempt`;
- `normal_terminal_record`;
- `mechanically_passing_tree`;
- `decision_resolved`;
- `subject_timeout`;
- `termination_class` and mechanical reason code;
- raw wall and token components;
- resource-pair eligibility;
- task eligibility; and
- any superseded infrastructure launch.

Only a mechanically proven subject-independent infrastructure failure may be
replaced. The frozen narrow class is limited to failures such as authentication,
transport, spawn, container, or harness failure before subject-controlled output
or workspace change. Retry the same planned arm slot immediately, within the
frozen replacement ceiling, and preserve the superseded launch.

Allow at most one contingent subject-call replacement for each `(task_id, arm)`
across that task's three repeats, and no more than 40 across a fully activated
20-task pool. The live-call request may freeze a smaller global ceiling. A second
qualifying infrastructure failure for the same task-arm, or exhaustion of the
global ceiling, makes the campaign operationally inconclusive. No favorable
decision label is computed with an unfilled scientific slot or unequal arm
denominators.

The following are scientific outcomes, not infrastructure:

- incorrect, incomplete, refused, or blocked normal completion;
- subject timeout;
- protected-input or final-tree integrity violation attributable to the subject;
- subject-caused process failure; and
- any other outcome for which usable contained subject evidence and a
  deterministic checker result remain available.

Exactly one checker-only retry is allowed solely when the first checker execution
returns no result because the checker process itself failed. Run the identical
frozen checker against the same preserved immutable final tree. Never retry an
actual checker pass/fail result. If the second execution returns no result, the
two deterministic executions disagree, or the checker is proven defective after
exposure, the task is retired with all evidence preserved and the complete
campaign is operationally inconclusive. This is not an infrastructure subject
retry and cannot activate another reserve task to rescue the confirmation.

An abnormal termination that cannot be mechanically classified must fail closed.
If its planned slot cannot be completed under the frozen rule without selective
judgment, the campaign is operationally inconclusive.

No scientific outcome is rerun. The replacement rule and ceiling may not change
in either direction after launch.

## 11. Required focused implementation and preflight

This revision authorizes no implementation beyond what is necessary to execute
this registered design after separate development direction. The minimal runner
and analyzer support is:

- serial task-major execution with explicit repeat IDs;
- fresh workspaces and back-to-back arms;
- frozen ordered-pool activation and a hard task-20 stop;
- frozen `MNM`/`NMN` schedules;
- the registered scientific-validity, normal-terminal, timeout, and
  decision-resolution semantics;
- symmetric pair and task eligibility;
- aggregate correctness across every activated task;
- strict missing-token handling;
- the registered task-level estimator and randomization test;
- narrow infrastructure replacement; and
- fail-closed structural and hash validation.

Focused changes to the existing request-bound workflow must also:

- bind the resource target, pool order, per-task schedules, stopping rule,
  artifact hashes, and replacement rule in the existing `REQUEST.json` /
  `APPROVED.json` flow;
- stop after the task producing the 12th eligible task;
- verify that unactivated tasks have no evidence or dispositions;
- reject any post-stop launch;
- reconstruct the legitimate stopping point from evidence; and
- accept a smaller completed call count only when the frozen stop rule explains
  it.

Do not add:

- a 12-worker queue;
- live candidate-specific calibration;
- concurrency telemetry infrastructure;
- token-budget enforcement;
- formal correctness non-inferiority;
- a new receipt/enforcement system; or
- a manual admission layer beyond taskcheck.

Before approval, pass focused unit and synthetic analyzer tests, the repository's
full required unit suite, and three consecutive no-model timed preflight runs
bound to the final `REQUEST.json` and unchanged frozen stack. Each preflight must
complete in 60 seconds or less and must validate the taskcheck ledger, hashes,
ordered pool, schedule, containment, container/runtime identity checks, call
ceilings, stopping rule, and analyzer fixture. Any repair that changes a bound
artifact requires a newly hashed preregistration/request and three new qualifying
preflights.

Changing only candidate MD bytes in a later experiment requires a new candidate
hash and experiment freeze. It does not by itself require rebuilding the runner,
rerunning the full implementation qualification, or making live calibration
calls. The three-run qualification belongs to a runner/runtime protocol version;
a later candidate-only experiment on an unchanged qualified stack requires only
the ordinary single no-model launch preflight bound to its new request.

No unit test, CI job, dry run, or preflight may make live model calls.

## 12. Freeze boundary and order of work

1. Review this revised draft and the conditional claim language.
2. Freeze the candidate and control hashes before confirmation-task information
   can influence candidate development.
3. Freeze the prospective simulation code, primary planning scenario,
   sensitivity grid, and assumptions.
4. Validate or prospectively revise the working target of 12 and pool maximum of
   20 before confirmation exposure.
5. Build the complete task pool and admit every task through
   `tooling/taskcheck.py`.
6. Freeze all task packages, then generate and hash the pool order and arm-order
   schedules from separate saved random seeds.
7. Implement only the focused serial runner/analyzer changes in Section 11.
8. Pass focused tests and `python3 -m unittest discover -s tests -v`.
9. Populate the operational fields in Section 13, write the exact conditional
   claim templates and correctness warning, finalize this preregistration, and
   hash it with every bound artifact.
10. Create the live-call `REQUEST.json` binding `PREREGISTRATION_SHA256` and the
    artifact hashes, covering at most `6 * ORDERED_POOL_MAX_TASKS` planned
    scientific calls plus the frozen infrastructure-replacement ceiling.
11. Run the three request-bound timed preflights. If a bound artifact changes,
    return to step 9 and issue a new request.
12. Obtain Wade's `APPROVED.json` referencing the final `REQUEST.json` hash before
    any live subject call.
13. Execute the serial confirmation once under the automatic stopping rule.
14. Run the frozen analyzer without modification and publish every required
    result, including the external request/approval hashes.

The live-call approval is the only human approval in development. This document
does not supply it.

## 13. Required freeze fields

Populate these fields before changing status from draft:

```text
RESOURCE_TASK_TARGET=12
ORDERED_POOL_MAX_TASKS=20
MAX_PLANNED_SCIENTIFIC_CALLS=120

TASKCHECK_LEDGER_SHA256=
ORDERED_TASK_POOL_SHA256=
POOL_ORDER_RANDOMIZATION_SEED=
POOL_ORDER_SHA256=
RUNNER_SHA256=
ANALYZER_SHA256=
POWER_SIMULATION_CODE_SHA256=
POWER_REPORT_SHA256=
POWER_PRIMARY_SCENARIO_SHA256=
POWER_SENSITIVITY_GRID_SHA256=
POWER_PRNG_AND_SEED=
POWER_SIMULATION_COUNT=
RUNTIME_MANIFEST_SHA256=
ARM_ORDER_RANDOMIZATION_SEED=
ARM_ORDER_SCHEDULE_SHA256=
MAX_INFRASTRUCTURE_REPLACEMENT_CALLS=
REPLACEMENT_REASON_CODES_SHA256=
```

Task-specific admission records remain in the existing taskcheck ledger. The
experiment-level fields remain in this preregistration and are bound externally
by `PREREGISTRATION_SHA256` in the existing live-call request. Do not change the
taskcheck ledger schema or create a parallel receipt or enforcement system.

## 14. Deviations that invalidate confirmation

The resource result is not confirmatory if any of the following occurs:

- candidate, control, task, checker, runtime, endpoint, schedule, or analyzer
  bytes change after the confirmation freeze;
- a task outside the frozen pool is added;
- the resource target, pool maximum, pool order, or stopping rule changes in
  either direction after the first usable call;
- activation depends on resource values, effect direction, p-values, or human
  preference;
- a task is edited after exposure rather than retired;
- fewer than 12 eligible tasks are analyzed as though the target were met;
- a pair with only one resolved arm enters a resource estimator;
- a failed pair or ineligible task is omitted from correctness;
- only two favorable pairs are chosen when all three are usable;
- wall and token use different pair or task cohorts;
- missing selected-pair token telemetry is handled by deletion, imputation, or
  rerun rather than an inconclusive token endpoint;
- a scientific failure is selectively rerun;
- an unclassified abort is called infrastructure through discretionary review;
- a checker defect or nondeterminism triggers another subject call or reserve
  activation rather than the frozen inconclusive disposition;
- the infrastructure replacement rule or ceiling changes;
- the token endpoint is promoted after the wall criterion fails;
- tasks are added because a p-value or effect floor missed;
- historical, development, admission, or replaced-launch data enter the
  confirmation estimator;
- analysis code is modified after results exist; or
- structural, containment, taskcheck, or hash validation fails and analysis
  proceeds anyway.

## 15. Required report

Publish all results regardless of direction or significance:

- requested and observed model/runtime identity;
- all frozen hashes and the live-call approval binding;
- the complete ordered pool and which tasks were activated;
- the automatic stopping point and reason;
- raw attempt-level correctness, termination, wall, and token records;
- every excluded pair and its mechanical reason;
- every resource-ineligible task and its `J_t` membership;
- all activated-task overall and per-task correctness counts;
- the observed correctness-qualification decision;
- all 12 eligible-task pair ratios and order-balanced task effects;
- wall and token point estimates, task-effect ranges, applicable registered
  joint-null p-values, effect-floor results, and fixed-sequence status;
- missing telemetry, abnormal termination, and infrastructure replacements;
- prospective power assumptions and realized eligibility counts; and
- every deviation from this protocol.

Raw resource values for unresolved, discordant, timed-out, and otherwise excluded
pairs must remain visible even though they do not enter the conditional resource
estimator.

The report must place the correctness result before the conditional resource
results and reproduce the qualification in Section 2.3 immediately beside every
favorable resource statement. It must never shorten the final conclusion to “the
MD reduced time/tokens” or “the resource effect was statistically significant.”
It must instead state that the registered joint sharp null was rejected in the
direction of the reported realized conditional ratio.

## 16. Final interpretation

This revision deliberately answers two separate questions:

1. **Correctness:** Across every scientific attempt on every activated task, did
   the candidate decision-resolve at least as many attempts as no MD under the
   observed aggregate qualification?
2. **Conditional efficiency evidence:** On paired repetitions where both arms
   completed normally and decision-resolved, did the registered joint-sharp-null
   test reject in the direction of a practically meaningful lower realized
   conditional wall-time ratio and then token-proxy ratio?

Failures are not converted into artificial 900-second/large-token penalties, and
their raw low resource values do not enter as direct cheap wins. They remain fully
visible in correctness and raw evidence, while both arms of the affected pair are
excluded symmetrically from the narrow conditional resource comparison.
Symmetric exclusion does not remove treatment-dependent survivor selection;
aggregate correctness equality does not prevent failures from being redistributed
across tasks or pairs.

An overall `OBSERVED_CORRECTNESS_AND_CONDITIONAL_RESOURCE_ELIGIBLE` decision
requires observed correctness qualification plus both fixed-sequence conditional
resource criteria. Even then, the result applies only to this frozen ordered-pool
experiment and does not prove statistical correctness non-inferiority,
unconditional resource improvement, or a resource-only causal effect.
