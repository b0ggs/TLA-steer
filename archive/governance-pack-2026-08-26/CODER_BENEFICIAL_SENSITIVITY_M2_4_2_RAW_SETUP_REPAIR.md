# CODER beneficial-sensitivity M2.4.2 raw-setup repair

Status: **AUTHORIZED — user-approved prospective authority**

## 1. Purpose and preserved evidence

This authority creates a narrow M2.4.2 lineage. All M2.4 and M2.4.1 authorities, preflights, reviews, closures, raw evidence, and related records remain immutable historical evidence and must not be overwritten, deleted, reclassified, pooled with M2.4.2, or represented as PASS.

M2.4.1 failed because its software review found that, after qualification starts, a catchable failure while creating `output/raw` can escape without a best-effort terminal record even when the output directory remains usable. M2.4.2 prospectively authorizes only correction of that defect, one direct regression test, and necessary evaluator, test, and authority hash rebinding in the existing canonical config.

After the freeze is accepted and `output` has been created, a catchable `output/raw` creation failure must attempt exactly one atomic, create-once FAIL publication at `output/terminal.json` when `output` remains usable, with zero execution records; if `output` or terminal-evidence I/O is unusable, the failure must propagate and no terminal-evidence preservation or recovery may be claimed.

No task, oracle, control, candidate, statistic, live design, dependency, module, framework, runner, schema family, or unrelated behavior may change.

## 2. Writable scope and hard caps

The only existing writable paths are `src/mdseval/beneficial_sensitivity.py`, `tests/test_beneficial_sensitivity.py`, and `experiments/coder-beneficial-sensitivity-m2.json`.

The only new writable paths are this authority and:

- `experiments/coder-beneficial-sensitivity-m2-4-2-preflight.json`
- `experiments/coder-beneficial-sensitivity-m2-4-2-software-review.json`
- `experiments/coder-beneficial-sensitivity-m2-4-2-experimental-review.json`
- `experiments/coder-beneficial-sensitivity-m2-4-2-freeze.json`
- `experiments/coder-beneficial-sensitivity-m2-4-2-qualification.json`
- `experiments/coder-beneficial-sensitivity-m2-4-2-closure.json`

The evaluator must remain at most 980 physical lines, tests at most 590, and config exactly one canonical line. Cumulative churn across the three existing paths is at most 30 additions plus deletions. This authority is initially at most 60 lines and permits at most one consolidated post-audit revision totaling at most 20 additions plus deletions.

One implementer turn and at most two pre-freeze repair cycles are permitted under `AGENTS.md`; no descendant agents are authorized. Any scope, path, cap, or turn breach follows the repository stop rule.

## 3. Validation and preflight

At most three focused and three full-suite invocations are permitted. Focused validation must directly cover raw-root creation failure with usable output, terminal-publication failure semantics, config-bound hashes, canonical config, and line/path/churn caps. Only focused PASS permits the exact full-suite command `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`; an in-scope failure may use the next authorized repair cycle.

The preflight is draft-replaceable until root verifies its canonical bytes and hash and explicitly finalizes it before either reviewer starts. From finalization onward it is immutable and binds this authority, exact evaluator/test/config bytes, preserved prior evidence, validation results, and zero model, candidate, judge, live, and network calls.

Validation exhaustion without a breach writes preflight FAIL and closure FAIL when those writes remain authorized, then stops. A prohibited breach stops immediately without further writes and reports any absent terminal records.

## 4. Independent review, freeze, and qualification

Exactly two independent, mutually blinded, read-only reviewers inspect byte-identical finalized inputs: one software-correctness reviewer and one experimental-validity reviewer. They do not run tests, repair, or see each other's output before both decisions are final. Their canonical review records become immutable upon return; any FAIL or disagreement creates closure FAIL and stops.

Both PASS reviews permit one immutable, nonauthoritative freeze binding all governed inputs, preflight, reviews, environment, and output schemas. The freeze is the no-retry boundary: after publication there is no repair, rerun, replacement, or second qualification.

Exactly one offline, nonauthoritative qualification may then execute the frozen checker matrix in task/state/repeat order: 20 tasks × 5 states × 3 repeats, at most 300 executions and exactly 300 for PASS. It makes no model, candidate, judge, live, or network call.

Qualification PASS atomically creates qualification PASS binding the freeze and all ordered executions, followed by closure PASS. Any post-freeze failure stops at the first failure, preserves available evidence, best-effort atomically creates terminal FAIL plus qualification FAIL and closure FAIL from existing dependencies, and never repairs or retries. All M2.4.2 records state `authoritative:false`.

M2.4.2 authorizes no live work, commit, push, merge, release, or publication.
