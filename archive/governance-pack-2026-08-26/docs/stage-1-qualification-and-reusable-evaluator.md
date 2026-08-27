# Stage 1 Qualification and the Reusable Evaluator

## Status of this note

This explanatory note records why the live demonstration is necessary, how that
differs from routine candidate evaluation, and how it fits the research program.

It is **not** an implementation authority, active specification, or competing V2
plan. The sole active V2 program and CODER feasibility-pilot authority is
[`coder-outcome-evaluator-v2-implementation-plan.md`](../coder-outcome-evaluator-v2-implementation-plan.md).
If this note and that plan differ, the active plan governs.

## The apparent contradiction

Two different requirements were being discussed as though they were one:

1. qualifying the evaluator as a credible measurement instrument; and
2. using a qualified evaluator to compare later candidates.

The expensive run is necessary now to qualify the MVP under frozen conditions.
That does not require rerunning it blindly for every candidate under those conditions.

In short:

> The current 56-call run is necessary now, once, to qualify the MVP. The complete
> procedure is not necessarily required for every later candidate comparison.

## What the current 56-call demonstration establishes

The demonstration combines two experiments:

| Component | Calls | Purpose |
| --- | ---: | --- |
| Evaluator qualification | 24 | Test A/A behavior and verify that an intentionally harmful control reliably loses |
| Initial real comparison | 32 | Compare the current champion with `karpathy-v1` using downstream task outcomes |

The 24 qualification calls ask whether the evaluator behaves sensibly on known controls:

- Identical MDs should not produce a spurious winner.
- An intentionally harmful MD should reliably lose.

The 32 comparison calls ask whether the champion or `karpathy-v1` performs better on
the frozen task set under the frozen runtime conditions.

Offline unit tests cannot establish live model behavior. Qualification is necessary
to satisfy the Stage 1 exit gate and treat the evaluator as usable evidence.

Passing controls can qualify the evaluator even if the real comparison is inconclusive.
If they fail, Stage 1B should wait until the failure is understood and corrected.

## Why future candidates need not repeat all 56 calls

The demonstrator couples qualification and comparison in one command, so rerunning
it repeats all 56 calls. This is an MVP limitation, not the intended architecture.

Stage 1B should separate qualification from candidate comparison. Its immutable,
hash-bound qualification record should identify at least:

- evaluator and repository revision;
- runner and invocation settings;
- target model and reasoning level;
- task-pack identity and hashes;
- checks, rubrics, and control identities;
- date and relevant runtime metadata;
- raw-evidence locations and result status.

While conditions remain valid, comparisons may reference the record instead of
repeating every control. Each still requires its own live calls and evidence.

Requalification is warranted when:

- the target model or reasoning level changes;
- the runner, evaluator, checks, rubric, or task pack changes;
- a different role or topology is introduced;
- enough time passes that model or runtime drift is plausible; or
- anomalous results create reason to doubt the measurement instrument.

Qualification may repeat periodically or between major batches. Repetition should
follow a validity reason, not automatically tax every candidate.

## Stage 1B: reusable CODER.md evaluation

After the demonstration passes, Stage 1B should:

- accept any manually supplied candidate MD;
- freeze a candidate ID and content hash before evaluation;
- bind the comparison to a valid qualification record;
- compare the candidate with the current champion;
- preserve comparison history and all raw evidence; and
- rotate or add fresh holdouts so repeated development does not contaminate
  confirmation evidence.

Once outcomes influence candidate design, those tasks become development evidence,
not fresh confirmation evidence.

## Stage 1C: controlled CODER.md optimization

Start with small, single-change variants and ablations. Change one thing at a time:

1. inexpensive smoke screening;
2. repeated development evaluation; and
3. fresh finalist holdout confirmation.

Promotion remains human-controlled. Reused tasks can guide iteration, but a
finalist claim should rest on fresh confirmation tasks that did not shape it.

## Later stages

Stage 1D should cover roles such as orchestrator, checker, and researcher. Each
needs its own tasks, mechanical checks, and rubric, not one universal MD score.

Stage 2 should evaluate multi-file role bundles and handoffs, initially changing
one file at a time so causal interpretation remains possible.

Stage 3 should compare frozen topologies: solo, primary-plus-checker,
specialist-plus-specialist-reviewer, and bounded swarm-plus-mediator. MD contents
remain frozen so instruction effects are not conflated with coordination effects.

## Why the target model matters

A cheaper model can support labeled smoke screening, but cannot qualify claims
about a different target model.

Model and reasoning level are treatment context, not merely billing settings. Final
qualification must use the intended configuration; changing it creates a new system.

## Academic positioning

Prior research examines context files, rule strategies, and iterative guidance
tuning. Comparators include Zhang et al., [arXiv:2604.11088](https://arxiv.org/abs/2604.11088),
and Shepard & Albrecht, [arXiv:2606.20512](https://arxiv.org/abs/2606.20512).

The defensible MDs_EVAL contribution is therefore narrower:

> A contamination-aware, controlled procedure for selecting among complete,
> role-specific instruction documents using downstream task success, known
> controls, repeated attempts, preserved history, and fresh confirmation
> tasks, later extended without conflating instruction content with agent
> topology.

The pilot validates the measurement instrument; alone it is not publishable evidence.
A contribution needs controls, repeats, preserved evidence, interventions, and fresh tasks.

## Operational note for the live run

The demonstration must execute as one continuous process. It is not resumable:
stopping it, closing its terminal, losing the host session, or otherwise
interrupting it invalidates that attempt as a complete 56-call demonstration.

Preserve partial raw evidence and mark an interrupted attempt incomplete. Restart
the entire demonstration in a new run directory; never combine separate attempts
into one nominal run.

The preserved 16-call feasibility pilot averaged about 86 seconds per subject
call and took about 23 minutes. Linear scaling suggests roughly 80–90 minutes
for 56–60 calls; 1.5–2 hours is a prudent expectation, while the three-hour
limit is a safety ceiling rather than a required duration.

Keep the Mac plugged in, awake, with its lid open and a stable network connection.
Screen lock is fine if it does not put the Mac to sleep. What matters is
uninterrupted completion under one frozen invocation with preserved evidence,
not that the run lasts exactly three hours.

## Recommendation

Run the current 56-call demonstration unchanged on the intended target model and
let it complete continuously. If controls pass, proceed to Stage 1B and separate
hash-bound qualification records from routine candidate comparisons.
