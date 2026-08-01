# Repository instructions

This repository evaluates instruction files. It is not an instruction optimizer yet.

- The sole active V2 program and CODER feasibility-pilot authority is `coder-outcome-evaluator-v2-implementation-plan.md`; do not create a competing active V2 plan.
- Preserve raw run evidence.
- Never modify a target or candidate during a run.
- Never expose variant identity to the qualitative judge.
- Mechanical failures cannot be overridden by an LLM judge.
- Do not run live model calls in unit tests or CI.
- Use the Python standard library only unless the specification is explicitly amended.
- Run `python -m unittest discover -s tests -v` before handoff.
