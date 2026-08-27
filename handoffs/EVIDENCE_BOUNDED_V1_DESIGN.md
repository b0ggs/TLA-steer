# Evidence-bounded v1 design basis

## Decision

[`controls/coder/evidence-bounded-v1.md`](../controls/coder/evidence-bounded-v1.md)
is an efficiency treatment, not a claimed replacement. It targets subject wall
time as the real outcome, trajectory length as a controllable diagnostic, and
mechanical correctness as a hard gate. Primary token cost is secondary because
the success-only trace evidence does not show a consistent token benefit.

No wording can guarantee statistical significance. The MD is designed to
maximize the probability of a real effect; a fresh, prospectively powered
experiment must establish that effect.

## Why this target

The published exploratory comparison included every valid attempt, including
cheap failed submissions. Restricting the descriptive medians to mechanically
resolved attempts changes the efficiency picture:

| Metric | Tasks with a lower probe median | Interpretation |
|---|---:|---|
| Trajectory length | 3/4 | Strongest directly controllable diagnostic |
| Wall time | 3/4 | Primary outcome with direct practical value |
| Primary token cost | 1/4 | Too inconsistent to optimize as primary |

The slow successful traces repeatedly contained nonzero command exits, broad
filesystem or environment searches, Git archaeology, large command output,
and repeated post-edit validation. The cheapest Starlette probe attempt failed
a product requirement, so unconstrained early stopping is not an acceptable
optimization. The candidate therefore combines hard exploration/retry/output
limits with one direct proof for every requested behavior.

## Current exploratory comparison

Wade selected a narrow exploratory comparison on 2026-08-27. It reuses the
same four development tasks and compares the previous efficiency probe
(`cost-time-probe-v1.md`) directly with this candidate. There are three planned
attempts per arm and task: 24 nominal calls, with the existing bounded
infrastructure-replacement allowance only.

This comparison answers the immediate question: on these tasks, does the new
MD show a materially better observed efficiency profile than the previous MD
without losing mechanical correctness? The report will show:

- checker resolution and requirement results as the quality guardrail;
- primary token cost (uncached input plus output), wall time, and trajectory
  length for every attempt;
- per-task and pooled descriptive medians and percentage differences; and
- both all-valid-attempt and mechanically-resolved-only summaries, so a cheap
  failure cannot be presented as an efficiency win.

This screen makes no significance or generalization claim. It requires no new
tasks and authorizes no task development.

## Deferred confirmatory claim boundary (not current scope)

The four traced tasks are development data and cannot confirm the MD derived
from them. They are also too few for a task-level exact significance claim:
even four favorable task medians give two-sided sign-test `p = 0.125`.

A future confirmatory efficiency experiment could freeze these bytes and
declare, before any new subject exposure:

- **Fixed design:** 35 fresh independent tasks, four planned attempts per arm,
  balanced arm order, and no outcome-dependent enrollment or extension.
- **Primary endpoint:** candidate-minus-null task-level median subject wall
  time across all planned valid attempts. Assign every mechanically unresolved
  valid attempt the fixed 900-second attempt-timeout penalty rather than its
  cheap early-exit duration.
- **Correctness gate:** no task may have fewer resolved candidate attempts than
  null. A failed gate forbids an efficiency claim.
- **Practical effect:** at least a 15% reduction in the median task-level wall
  time ratio.
- **Inference:** exact two-sided sign test at `p <= 0.05` on the fixed fresh
  cohort. With 35 non-tied task differences, at least 24 must favor the
  candidate (`p = 0.04096`). At a true 75% probability that a task favors the
  candidate, this test has 85.8% power before ties; ties reduce power and may
  make the result inconclusive.
- **Secondary diagnostics:** primary token cost, trajectory length, command
  failures, and captured command-output characters. They do not substitute for
  the primary result.

That design is retained only as a boundary on any future significance claim.
It is not the current experiment and authorizes no cohort or task work. The
current exploratory batch still requires a request binding both MD hashes and
Wade's matching live-spend approval. No historical run evidence is modified.

## Offline validation

- Candidate SHA-256:
  `c0d56e29ade34c24278b976e84b29e47324c11a23399ca882239daffc9762c74`.
- Complete sealed four-task preflight: `PASS` in 21.583s, 24.429s, and
  20.706s. Each run used the final candidate bytes and made no subject-model
  call.
- `python3 -m unittest discover -s tests -v`: 236 tests passed, 6 skipped, in
  278.521s.
- Independent factual audit and policy red-team: no remaining discrepancy or
  must-fix finding after revision.
- `python3 tooling/taskcheck.py batch verify tasks`: all 23 current task
  packages passed mechanical verification.

No live model call was made during authorship or validation.

## Live-test readiness

The candidate bytes are frozen and the complete four-task preflight is below
the 60-second launch gate. The next artifact is the hash-bound request for the
24-call exploratory comparison described above. Queueing that request performs
offline preflight only; it makes no subject-model call. Execution remains
blocked until Wade approves the exact resulting request hash.
