# Repository instructions

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
