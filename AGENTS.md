# Repository instructions

## Active TLA-Steer project

The active product and approved hackathon scope are defined by `README.md` and
`IMPLEMENTATION_PLAN.md`. The MDs_EVAL product instructions below govern the
preserved foundation; they do not redefine TLA-Steer's approved prototype.

## Product definition

We are building a controlled benchmark and regression system for coder.md: it runs the same LLM on a validated suite of coding tasks with no coder.md, with the current coder.md, and with a candidate replacement, then uses objective checkers to determine whether coder.md beats the bare model and whether the candidate beats the incumbent without regressions. The finished product is the reusable task suite, runner, checkers, preserved evidence, and comparison report needed to make reliable keep-or-replace decisions.

This repository evaluates instruction files. It is not an instruction optimizer yet.

- Archived planning and review documents are historical evidence only and authorize no work.
- Preserve raw run evidence.
- Never modify a target or candidate during a run.
- Never expose variant identity to the qualitative judge.
- Mechanical failures cannot be overridden by an LLM judge.
- Do not run live model calls in unit tests or CI.
- Use the Python standard library only unless the specification is explicitly amended.
- Run `python3 -m unittest discover -s tests -v` before handoff.

## Development workflow controls

- Every artifact is written to disk at creation; nothing lives only in an agent's conversation. Blind solutions carry on-disk provenance.
- Task admission is mechanical: `tooling/taskcheck.py`. No manual audit substitutes for it and no process may be layered on top of it.
- Pre-exposure failures are ordinary and repairable without limit. Experimental freezing and no-selective-retry begin only when a usable subject attempt launches; during captured attempts, tasks, targets, and candidates remain immutable. Exposed defective tasks are retired, never edited; repaired copies are new tasks that record their parent.
- The only human approval in development is live subject-model call spend (REQUEST.json/APPROVED.json).
- Sub-agent concurrency is unlimited for implementing sessions (per Wade, 2026-08-23).
- Do not build enforcement or receipt infrastructure beyond taskcheck's manifest and ledger unless Wade separately authorizes it.
- Audit and review findings do not expand the requested scope; recommendations are advisory unless Wade explicitly adopts them.

<!-- BEGIN SCOPE-GATE GUARDRAIL -->
## Audit and review scope guardrail

- Audit and review findings do not expand the approved task. Recommendations
  are advisory unless Wade explicitly adopts them.
- The orchestrator/controller freezes a per-task Scope Gate contract containing
  approved requirement and invariant IDs, exclusions, allowed paths, and
  mapped checks. An explicit user instruction or accepted roadmap supplies
  approval; creating its matching contract requires no additional approval
  ceremony.
- Auditors may submit structured findings only. They may not change the
  contract or mappings, mark results trusted, determine changed paths, dispatch
  work, or create requirements.
- Only the orchestrator/controller runs trusted checks, determines changed
  paths, constructs the evaluation bundle, invokes `scope-gate evaluate`, and
  obeys the result.
- Exit 0 means no Scope Gate blocker; it does not prove task completion. Exit 2
  blocks completion. Exit 3, malformed output, or an unexpected process
  failure fails closed as an integration error.
- Completion independently requires every required controller-run check to
  pass against the final artifact.
- Once work begins, the active contract, revision, and digest are immutable.
  Any scope change requires Wade's approval and a new revision and digest.
<!-- END SCOPE-GATE GUARDRAIL -->
