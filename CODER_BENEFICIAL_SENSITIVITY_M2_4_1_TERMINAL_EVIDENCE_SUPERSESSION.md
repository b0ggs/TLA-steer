# CODER beneficial-sensitivity M2.4.1 terminal-evidence supersession

Status: **AUTHORIZED — user-approved prospective authority**

## 1. Purpose and narrow supersession

This authority prospectively supersedes only the M2.4 terminal FAIL/no-repair barrier for corrected implementation bytes. It permits one bounded pre-freeze repair whose sole purpose is to make `qualify()` reliably terminalize catchable failures after qualification starts. It does not reopen task, oracle, treatment, candidate, statistical, live-run, or broader evaluator design.

The existing M2.4 preflight and closure FAIL records remain historically valid because they accurately describe the procedural violation and stopping decision for that specific attempt under its then-frozen conditions. They, the M2.4 engine-authorship record, and all associated raw or packet evidence are immutable: never overwrite, delete, reclassify, pool with M2.4.1, or represent them as PASS. Corrected bytes and all resulting evidence belong only to the distinct M2.4.1 lineage.

## 2. Authorized implementation

One implementer may make one initial repair, followed by at most two bounded pre-freeze repair cycles under `AGENTS.md`. The production change is limited to catchable post-start terminal evidence in `qualify()` and directly necessary local helpers. Tests may change only to prove that behavior, and the experiment config may change only to bind the resulting evaluator/test hashes and this authority.

Catchable scope means ordinary Python `Exception` outcomes after the M2.4.1 PASS freeze has been accepted and qualification has started, including capability/setup, workspace materialization, checker invocation, evidence construction or publication, cleanup/deletion, matrix iteration, and result construction. Where the evidence destination remains usable, each such failure must converge on one atomic, create-once terminal FAIL attempt, followed best-effort by a repository qualification FAIL and closure FAIL that bind only evidence actually created.

This authority does not claim recovery or durable terminal evidence after `BaseException`, interpreter or machine death, forced process termination, storage loss, or failure of the evidence-I/O path itself. Those cases may receive only a best-effort atomic FAIL attempt and can never be reported as preserved, complete, or PASS.

## 3. Exact writable scope and caps

The only existing writable paths are:

- `src/mdseval/beneficial_sensitivity.py`
- `tests/test_beneficial_sensitivity.py`
- `experiments/coder-beneficial-sensitivity-m2.json`

The only new writable paths are this authority and these six canonical one-line records governed by the finalization rules below:

- `experiments/coder-beneficial-sensitivity-m2-4-1-preflight.json`
- `experiments/coder-beneficial-sensitivity-m2-4-1-software-review.json`
- `experiments/coder-beneficial-sensitivity-m2-4-1-experimental-review.json`
- `experiments/coder-beneficial-sensitivity-m2-4-1-freeze.json`
- `experiments/coder-beneficial-sensitivity-m2-4-1-qualification.json`
- `experiments/coder-beneficial-sensitivity-m2-4-1-closure.json`

No other path may change. Production remains at most 980 physical lines, and may exceed the prior 950-line cap only if necessary for the terminal-evidence repair. Tests remain at most 590 physical lines. The config remains one canonical line. Cumulative implementation churn across the three existing paths is at most 100 additions plus deletions; deletion does not create extra allowance. No new module, dependency, framework, runner, record class, or provenance artifact is authorized.

If implementation proceeds, the config's existing `m2_4_authority_sha256` binding must bind this M2.4.1 authority instead of the old M2.4 authority hash. The old authority and FAIL records remain preserved historical evidence and are not rewritten.

## 4. Validation and independent review

Each implementation state receives one bounded focused validation covering the known terminalization behavior, config-bound evaluator/test hashes, canonical config, line caps, and path/churn caps. Only a focused PASS permits one full offline suite: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`. A failed focused or full-suite validation may consume the next available repair cycle automatically; at most three focused and three full-suite invocations are possible across the initial implementation and two repairs. Exhaustion without a breach writes preflight FAIL and closure FAIL if those writes remain authorized, then stops. Any scope, path, or cap breach follows `AGENTS.md`: stop immediately without further writes and report any absent terminal records.

Before either reviewer is invoked, root finalizes the preflight by verifying its canonical bytes and hash. Draft creation or atomic replacement before that boundary is permitted and does not invalidate M2.4.1. From finalization onward, the preflight is immutable, and both reviews and the freeze must bind its finalized hash. Review records are immutable upon reviewer return. The freeze and every post-freeze evidence record are atomic, create-once, and immutable from their first publication.

After focused and full-suite PASS, create preflight PASS binding the exact reviewed bytes and validation results. Exactly two independent reviewers then inspect byte-identical, read-only inputs: one software-correctness reviewer and one experimental-validity reviewer. Each review record binds the reviewed bytes and reports PASS or FAIL. Any review FAIL or disagreement creates closure FAIL and stops; reviewers do not repair, execute tests, or see each other's output before both decisions are final.

## 5. Freeze, qualification, and terminal boundary

Only PASS preflight and both PASS reviews permit the nonauthoritative M2.4.1 freeze. The freeze binds this authority, exact implementation/config/test bytes, governed corpus and controls, preflight, both reviews, environment, and output schemas. All six M2.4.1 records state `authoritative:false`; none is a final live-run authorization.

The new PASS freeze is the true no-retry boundary. After it is created, frozen bytes cannot change and no repair, rerun, replacement, or second qualification is permitted. Only then may exactly one offline, nonauthoritative, no-model, no-candidate, no-judge, no-network qualification invoke the frozen checker matrix in task/state/repeat order: 20 tasks × 5 states × 3 repeats, at most 300 executions and exactly 300 for PASS.

On qualification PASS, atomically create qualification PASS binding the freeze and all 300 ordered execution records, then closure PASS binding qualification. On any post-freeze failure, stop at the first failure, preserve available raw evidence, atomically attempt terminal FAIL, create qualification FAIL and closure FAIL best-effort from existing dependencies, and never repair or rerun. Pre-freeze gate failure produces the corresponding FAIL record when defined plus closure FAIL and no freeze or qualification.

M2.4.1 ends after closure PASS or FAIL. It authorizes no live work, model/subject/judge call, candidate access, network call, commit, push, merge, release, or publication.
