# Repository instructions

## Product definition

We are building a controlled benchmark and regression system for coder.md: it runs the same LLM on a validated suite of coding tasks with no coder.md, with the current coder.md, and with a candidate replacement, then uses objective checkers to determine whether coder.md beats the bare model and whether the candidate beats the incumbent without regressions. The finished product is the reusable task suite, runner, checkers, preserved evidence, and comparison report needed to make reliable keep-or-replace decisions.

This repository evaluates instruction files. It is not an instruction optimizer yet.

- `coder-outcome-evaluator-v2-implementation-plan.md` governs only its historical frozen feasibility-pilot evidence; `CODER_BENEFICIAL_SENSITIVITY_M2_IMPLEMENTATION_PLAN.md` is the sole active Milestone 2 authority, and no competing active plan may be created.
- Preserve raw run evidence.
- Never modify a target or candidate during a run.
- Never expose variant identity to the qualitative judge.
- Mechanical failures cannot be overridden by an LLM judge.
- Do not run live model calls in unit tests or CI.
- Use the Python standard library only unless the specification is explicitly amended.
- Run `python3 -m unittest discover -s tests -v` before handoff.

## Delegated-work orchestration controls

- Before the first delegated turn, root records the complete Git dirty/untracked baseline and posts a concise brief naming the objective, roles, exact writable paths or read-only status, forbidden actions, expected output, validation, milestones, and repair approach. An editing brief sets task-proportionate hard caps for changed/new deliverable paths and total textual churn; without both caps, delegated work is read-only.
- Use one editor at a time. Optional auditors and reviewers are read-only. An agent may not delegate unless the user-approved brief names the child role and topology. Preserve unrelated user changes and stay within the authorized objective, paths, caps, dependencies, live-call authority, and integration authority; expansion requires prior user approval.
- Pre-subject authoring, tool, path, hash, checker, and capture failures are ordinary retryable engineering failures and do not consume experimental versions. Experimental freezing and no-selective-retry begin only when a usable subject attempt launches or authoritative initialization begins, whichever occurs first. During captured attempts, tasks, targets, and candidates remain immutable.
- After a repair, run a focused offline validation for the observed failure before broader validation. Before a code handoff, run the repository unit command once after focused checks pass. Never put live model calls in validation.
- At handoff, report the exact baseline-to-current diff: changed, new, and deleted paths; additions and deletions; replacement-file final line counts; binary changes; validations and results; deviations; and blockers.
- These are behavioral controls. Do not build enforcement or receipt infrastructure unless the user separately authorizes it.
