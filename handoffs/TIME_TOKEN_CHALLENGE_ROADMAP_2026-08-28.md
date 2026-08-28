# Time/token challenge roadmap — 2026-08-28

Status: Active roadmap for the `time-token-challenge` branch. It supersedes
`PLAN_OF_RECORD_2026-08-26.md` only as the forward plan for this branch. The old
plan and all run evidence remain preserved as history. This roadmap authorizes
no live model calls; every live batch still requires its own hash-bound approval
from Wade.

## Branch charter

This branch is a deliberately separate development track for a
correctness-qualified time/token coding challenge. On the existing four
admitted tasks, it asks whether a short, task-neutral MD can reduce primary
tokens, subject wall time, or execution trajectory without reducing mechanical
task completion.

Optimization for this fixed task set is intentional. Results are development
results for this challenge, not evidence that an MD is generally better, a
causal explanation of model behavior, or a statistical claim about other task
populations.

The governance/process-failure task track continues separately on
`governance-tasks`. Neither branch is presumed to merge into the other.

## Checked-in checkpoint

- The branches diverge at commit `f8077a6`.
- The latest hardened comparison and its raw evidence are committed at
  `53bf48b`.
- `evidence-bounded-vs-null-v2` is the first complete paired cohort in this
  line whose runtime capabilities were hardened and whose trace review found
  no successful external or hidden-answer retrieval.
- Null resolved 12/12 attempts. `evidence-bounded-v1.md` resolved 10/12.
- Raw primary-token totals were 1,088,214 for null and 709,917 for the MD,
  34.8% lower for the MD.
- Raw subject wall-time totals were 4,249.436 seconds for null and 2,787.407
  seconds for the MD, 34.4% lower for the MD.
- The two MD misses were genuine Click R1 misses: both substituted finalizer
  behavior for the separately required explicit `close()` behavior.
- Because correctness regressed, the candidate did not qualify as an
  efficiency winner and is not promoted. Its efficiency profile remains useful
  development evidence.
- Historically contaminated attempts remain preserved but are not clean
  comparison evidence.

The detailed result is in
`handoffs/EVIDENCE_BOUNDED_VS_NULL_V2_RESULT.md`; machine-readable and raw
evidence is under `runs/dev-v2/evidence-bounded-vs-null-v2/`.

## Fixed evaluation contract

Until Wade explicitly changes the challenge, retain:

- the same four admitted tasks;
- the same zero-byte null control;
- the same model, reasoning level, runner, containment, task bytes, checker
  bytes, and registered metric definitions;
- mechanical correctness as the qualification gate;
- primary tokens and subject wall time as the two efficiency outcomes, with
  trajectory length as a diagnostic; and
- complete task-level reporting, including failed attempts.

A failed or prematurely ending attempt cannot create an efficiency win. A
candidate must first match its paired null arm on mechanical correctness before
its lower resource use can qualify as an improvement.

## Ordered roadmap

### 1. Close the current milestone — complete

Keep the latest result, raw evidence, trace-audit conclusion, and contamination
caveats at the committed checkpoint. Do not rerun the identical 24 calls merely
to replicate them.

### 2. Draft one compact v2 candidate offline

Create one immutable successor to `evidence-bounded-v1.md`. Preserve the
efficiency discipline that shortened successful trajectories, but strengthen
the general completion gate: each distinct observable requirement must receive
direct proof through its actual trigger or path; adjacent or analogous proof
does not cover it.

The candidate must remain short and task-neutral. Change only the versioned MD
file, then commit its exact bytes before exposure. Do not modify tasks,
checkers, the runner, metrics, or historical evidence while designing it.

### 3. Use a cheap paired development screen

For a serious candidate, predeclare one attempt per arm on each of the same four
tasks: eight nominal live calls total. Use a fresh null arm so wall-time and
runtime conditions are contemporaneous. This screen is exploratory triage, not
a significance test or a keep/replace result.

Advance a candidate only if it matches null correctness across the screen and
its complete tokens/time/trajectory table remains promising. Preserve every
outcome, use no correctness-driven retries, and make any advancement an explicit
Wade decision. A rejected candidate remains immutable evidence; a revision is a
new candidate.

Changing only an MD does not trigger another hardening audit, system rebuild,
or full 24-call comparison. It requires only the normal complete preflight,
which must still pass in 60 seconds or less, followed by a new exact
`REQUEST.json` and Wade's matching `APPROVED.json` before any live call.

### 4. Reserve the full paired batch for a finalist

Only after a candidate survives the cheap screen should Wade decide whether it
merits the normal three-attempt, two-arm, four-task comparison: 24 nominal
calls. That later batch uses the unchanged evaluation contract and supports the
next challenge keep/replace decision. It is not an automatic consequence of a
screen and is not required for every MD draft.

If the finalist matches null correctness and improves the efficiency outcomes,
freeze it as this branch's challenge incumbent. Otherwise retain the evidence
and either design a new version or stop; do not selectively rerun unfavorable
task/arm results.

### 5. Decide whether to productize this challenge

Only after a qualifying finalist exists should a separate, explicitly approved
milestone consider packaging this fixed evaluation as an open-source or
competition challenge. Until then, spend effort on the MD signal rather than a
site, leaderboard, submission system, or generalized optimizer.

## Explicitly outside this roadmap

- governance, drift, instruction-growth, or process-failure tasks;
- new tasks, a task factory, or cohort expansion;
- causal ablations, a power study, or a significance campaign;
- checker or task redesign, including the exposed-checker limitation;
- another admission layer, receipt system, gate, hook, or enforcement system;
- changes to historical evidence or relabeling contaminated runs as clean;
- a competition site, accounts, submissions, or leaderboard; and
- repeated full 24-call runs for each MD draft.

## Branch discipline

Challenge candidates, requests, results, and roadmap changes stay on
`time-token-challenge`. Governance work stays on `governance-tasks`. If either
track later produces a genuinely shared machinery fix, isolate it in its own
commit and deliberately cherry-pick it; do not merge the divergent product
tracks by default.

The immediate next step is Step 2, performed offline. No experiment is queued
or authorized by this roadmap.
