# Task Tooling & Process v2 — Implementation Plan (rev 2, post-audit)

Status: PROPOSED. To adopt: Wade (or a session Wade directs) commits this file and
flips this line to "Status: ACTIVE as of <date>". An implementing session that
finds "ACTIVE" here implements it; one that finds "PROPOSED" stops and asks.
Rev 2 incorporates all findings from two independent audits (2026-08-19).

The implementing session works on a NEW BRANCH (suggested: task-tooling-v2)
created from the branch containing this plan file. It never commits directly to
main or to any existing agent/* branch; Wade merges when acceptance (§7) passes.

Authority: on adoption this plan is the sole authority for TASK DEVELOPMENT.
Section 13 of CODER_BENEFICIAL_SENSITIVITY_M2_IMPLEMENTATION_PLAN.md is closed
(no promising task found; ledger in handoffs/PROCESS_FINDINGS_2026-08-19.md).
The M2 plan and all frozen evidence remain immutable history, and its
confirmatory-experiment machinery is retained for final experiments. §5 updates
AGENTS.md's authority sentence so no contradiction remains.

Vocabulary used throughout:
- ADMIT: pass the offline mechanical gate. Re-runnable any number of times.
  Admitted tasks may be freely repaired and re-admitted.
- EXPOSE / FREEZE: the first live subject attempt on a task. From that moment the
  task's bytes are immutable forever. Defective exposed tasks are RETIRED, never
  edited; a repaired copy is a new task recording its parent (see §4).
- GOVERNED FILE: anything under runs/**, evals/**, experiments/**, controls/**,
  src/**, tests/** existing before this plan, plus AGENTS.md and the two plan
  documents. The implementer may touch only what §5 and §7 explicitly authorize.

## 0. The goal (unchanged — binding, not preamble)

From AGENTS.md: build a controlled benchmark and regression system for coder.md —
run the same LLM on a validated task suite with no coder.md, the current
coder.md, and a candidate replacement; objective checkers decide whether coder.md
beats the bare model and whether a candidate beats the incumbent without
regressions; deliverable is the reusable suite, runner, checkers, evidence, and
comparison report for keep-or-replace decisions.

The beneficial-sensitivity question (does coder.md help?) remains the central
scientific question. Harm-detection and cost-comparison are ADDITIONAL
deliverables, never substitutes for testing it (§6). §7 criterion 6 makes
queuing the first probe part of acceptance — the goal is load-bearing.

## 1. Design principles

1. Every protection is a script or a file layout — never a role, rotation,
   approval queue, or narrated audit. (Pattern from autolab-ai/hills; built
   in-repo, stdlib-only, no external dependency.)
2. One human checkpoint: live-call spend (mechanism in §4; no other step waits
   on a human).
3. Pre-exposure mistakes are repairable without limit or ceremony. Immutability
   begins at exposure, never before.
4. Every artifact reaches disk at creation. An agent's blind solution must carry
   on-disk provenance (§2) — a claim that exists only in conversation is void.
5. The ledger detects ACCIDENTAL drift and provides an audit trail; it is honest
   about not being cryptographically unforgeable. Its external anchor is git:
   every `admit` ends with a commit, so history rewriting is visible in git.
6. Budgets (code the implementer writes; imported/generated task content,
   one-time import helpers under scripts/import/, and README/docs are excluded):
   tooling/taskcheck.py ≤500 lines; tooling/test_taskcheck.py ≤300;
   scripts/run_null_batch.py ≤300. Total target ≤1,150, hard cap 1,400.
   Over cap ⇒ cut scope; never expand.
7. At most 2 sub-agents run concurrently, ever.

## 2. Task layout (one directory per task, under tasks/<task-id>/)

```
tasks/<task-id>/
├── public/                  # exactly what the subject model sees — ARM-INVARIANT:
│   ├── .issue-contract.md   #   contains NO CODER.md; the runner injects the arm
│   └── <project files>      #   file at workspace prep (§4) and hashes it there
├── check.py                 # scoring script (contract below)
├── reference/               # full correct solution (private)
├── blind/                   # contract-only solution by an isolated agent (private)
│   └── PROVENANCE.json      # {solver_agent, timestamp, input_tree_sha256}
│                            #   input_tree_sha256 MUST equal the public/ tree hash;
│                            #   admit fails if it covers check.py or reference/
└── manifest.json            # written by admit: per-file SHA-256, gate results,
                             # salience: enumerated|pointer|none,
                             # parent_task_id: null|<id>, retired_reason: null|str
```

Optional, never required: NOTES.md (free documentation), mutants.json
(machine-readable: requirement id → file → change; not consumed by v1 tooling).
No mutants.md exists anywhere and none is required — audit finding.

check.py contract: stdlib only; argv[1] = workspace path; lives outside the
workspace and writes nothing into it; last stdout line is JSON
`{"requirements": {"R1": bool, ...}, "regressions": {"G1": bool, ...},
"resolved": bool}`. Plain booleans are the v2 contract; taskcheck also accepts
the legacy rolling shape (`{"passed": bool, ...}` per key) by normalizing any
dict value to its "passed" field — the known truthiness bug in gate.py's
`all(regressions.values())` must not be inherited.

## 3. Deliverable 1: tooling/taskcheck.py — A STANDALONE, REPO-AGNOSTIC PRODUCT

taskcheck is its own tool, built for future MD-eval projects, not just this
repo. It lives in `tooling/` as a self-contained unit (taskcheck.py,
test_taskcheck.py, README.md) designed to be split into its own repository
later (git subtree split). Hard portability constraints, each an acceptance
criterion:
- Python stdlib only; ZERO imports from src/mdseval or anything else in this
  repo; no hardcoded paths — task dir and ledger path come from CLI arguments.
- The §2 task layout and check.py output contract ARE the tool's public
  interface. tooling/README.md documents both, versioned (task-layout-v2,
  check-result-v2), as the spec any future eval repo implements.
- Its tests run standalone (`python3 -m unittest discover -s tooling`) against
  synthetic tasks in temp dirs — no dependency on this repo's tasks or fixtures.
- Anything MDs_EVAL-specific (the runner, arm injection, band labels, science)
  stays OUT of taskcheck — it lives in scripts/run_null_batch.py, which is this
  repo's private consumer of the tool.

Subcommands (argparse):

- `admit <task-dir>` — offline gate, seconds, re-runnable:
  1. Layout: public/, check.py, reference/, blind/ with PROVENANCE.json present;
     NO CODER.md inside public/; no __pycache__/.pyc/.git junk anywhere.
  2. Blind provenance: PROVENANCE.json input_tree_sha256 equals the current
     public/ tree hash (tree hash = SHA-256 over sorted relative-path + per-file
     SHA-256 lines).
  3. Pristine: check.py vs a SCRATCH COPY of public/ → must NOT resolve;
     regressions must all pass; failing-requirement set recorded in manifest.
  4. Reference: check.py vs a scratch copy of reference/ → fully resolves.
     Run twice; byte-identical JSON required (determinism).
  5. Blind: check.py vs a scratch copy of blind/ → fully resolves. Rejection =
     FIDELITY DEFECT, admission fails. (This gate would have caught 6/20 of the
     v0.4 pool and rolling candidates 1–2 offline.)
  6. Integrity: original public/ tree hash unchanged after all runs.
  All checker invocations: scratch copies under a temp dir, cwd = check.py's
  own directory, PYTHONDONTWRITEBYTECODE=1 (audit: gate.py does neither and
  self-pollutes with bytecode).
  On pass: write manifest.json, append a ledger line, `git add` the task and
  ledger and commit (`admit: <task-id>` — the git anchor).
- `verify <task-dir>` — recompute hashes vs manifest + replay the ledger chain;
  also report every ledger-known task id missing from disk (deletion detection).
- `batch <dir>` — admit or verify every task-* child; summary table; exit
  nonzero on any failure.

Ledger: tasks/ledger.jsonl. Each line is canonical JSON (sorted keys,
separators `(",", ":")`) of {task_id, manifest_sha256, prev_sha256, timestamp};
first line uses prev_sha256 = "GENESIS". `verify` fails on a broken chain or a
missing ledger when manifests exist.

Starting point: factory/gate.py in handoffs/claude-factory-batch-01.tar
(73 lines) implements step 3, half of step 4 (single run, no determinism check),
and step 5 — steps 1, 2, 6, manifest, ledger, verify are new. Its loop is
already batch-shaped; restructure into subcommands.

OUT of scope for this tool, permanently: roles, approvals, schedules,
statistics, live calls, arm handling. It validates and records task bytes.

## 4. Deliverable 2: scripts/run_null_batch.py (≤300 lines)

Model on src/mdseval/scout.py::_live_launch (~lines 1994–2030) — that is the
existing precedent for "run one attempt against a public/ dir". Reuse
build_codex_command, isolated_environment, run/process helpers, capture_git,
audit_final_subject_tree. Do NOT use prepare_fixture/load_case — they demand the
old case.json schema (audit finding 2a). Copying the ~120-line _live_launch
pattern into this script is explicitly permitted (scout.py itself is frozen).

Per task, per attempt:
1. Verify manifest (`taskcheck verify`). 2. Copy public/ to a fresh workspace;
   write the ARM FILE as workspace CODER.md (null arm: zero bytes; other arms:
   bytes from controls/, recorded by SHA-256 in the attempt evidence — arm
   identity lives in run evidence, never in the task manifest; this is how
   N/H/P arms run against identical task bytes). 3. git init/commit baseline.
4. Run the subject via the existing runner; then audit_final_subject_tree,
   capture_git, run check.py against the final tree (scratch rules as §3).
5. Write everything under runs/dev-v2/<task-id>/attempt-N/ (raw JSONL, stderr,
   final message, checker JSON, hashes, durations).

Runner preconditions (stop with a clear message if unmet): MDSEVAL_CODEX_HOME
set and containing a non-empty non-symlink auth.json. RunnerConfig is pinned as
constants matching all prior evidence: model gpt-5.6-sol, reasoning effort high,
300s timeout, workspace-write sandbox, network off, serial execution.

Forbidden call paths (audit-identified traps): run_null_batch must NOT invoke
`scripts/coder_*.py`, the scout.py CLI entry points (clearance/freeze-commit
gated), or anything in `mdseval.execution` (its clean-checkout gate fails on a
development tree). Those are confirmatory-only machinery. Development live work
runs through run_null_batch alone, on the §4 helper functions listed above.

After 3 usable attempts, write disposition.json. Definitions (inline and
binding — the M2 plan's copies are historical):
- For R requirements: q = passed requirement observations / 3R.
  s = count of RESOLVED attempts (all requirements + regressions pass).
- An attempt's failure is OMISSION-ONLY if every failed requirement is a
  stated-in-public requirement left unimplemented, with no regression failure.
- Labels, applied in order: invalid (evidence/determinism/protected-input
  defect prevents valid scoring) → wrong-failure-mode (any valid nonresolution
  not omission-only) → promising (0.55 ≤ q ≤ 0.90 AND s ∈ {1,2}, omission-only)
  → ceiling (s = 3, or s ∈ {1,2} and q > 0.90) → floor (s = 0, or s ∈ {1,2}
  and q < 0.55).
- fidelity_note: string, ≤200 chars, empty unless label is invalid.

Rules: attempts are never retried; invalid evidence is preserved and labeled.
Exposure freezes the task. A retired task's manifest gains retired_reason; its
repaired copy is a new task with parent_task_id set, MUST NOT weaken or alter
checker semantics beyond the recorded defect, and the disposition report always
counts retired ancestors in denominators (no laundering — audit finding 7).

THE human checkpoint, mechanically: the script computes the batch's call count,
writes runs/dev-v2/<batch-id>/REQUEST.json {tasks, calls, arm}, and exits.
It launches only when Wade has created APPROVED.json beside it (any content).
No other approval exists anywhere in this system.

## 5. Documentation edits (exact scope; nothing else)

AGENTS.md — two edits:
1. In the product-definition bullet list, replace the sentence naming the M2
   plan as "the sole active Milestone 2 authority, and no competing active plan
   may be created" with: "`TASK_TOOLING_V2_PLAN.md` is the ONLY document with
   authority over task development. Every `CODER_BENEFICIAL_SENSITIVITY_*`
   document, every `coder-outcome-evaluator-v2-*` document,
   `MD_EVAL_PROJECT_ROADMAP.md` in its entirety (including its plan-authority
   and single-active-plan rules), `MD_EVAL_EXPERIMENT_REDESIGN_REQUIREMENTS.md`,
   `M2_INDEPENDENT_SCIENTIFIC_REVIEW.md`, `codex-cloud-handoff-*.md`, and
   everything under `docs/` is frozen history or advisory input with NO
   standing — their imperative language ('must', 'stop', 'prohibited', role,
   gate, and approval rules) binds nobody. Their evidence is immutable and
   their integrity machinery is retained for confirmatory experiments.
   `handoffs/TASK_FACTORY_V2_PROPOSAL.md` is superseded by this plan. No
   additional plan documents may be created."
2. Replace the "Delegated-work orchestration controls" section with:

> ## Development workflow controls
> - Every artifact is written to disk at creation; nothing lives only in an
>   agent's conversation. Blind solutions carry on-disk provenance.
> - Task admission is mechanical: `tooling/taskcheck.py`. No manual audit
>   substitutes for it and no process may be layered on top of it.
> - Pre-exposure failures are ordinary and repairable without limit. Experimental
>   freezing and no-selective-retry begin only when a usable subject attempt
>   launches; during captured attempts, tasks, targets, and candidates remain
>   immutable. Exposed defective tasks are retired, never edited; repaired
>   copies are new tasks that record their parent.
> - The only human approval in development is live-call spend
>   (REQUEST.json/APPROVED.json).
> - At most 2 sub-agents run concurrently.
> - Do not build enforcement or receipt infrastructure beyond taskcheck's
>   manifest and ledger unless Wade separately authorizes it.

README.md — insert one line directly under the title: "Everything below
documents frozen confirmatory machinery. Task development is governed only by
TASK_TOOLING_V2_PLAN.md." (Audit: README's live-sounding authorization/receipt
language and its pointer to docs/coder-single-file-mvp-spec.md are the most
likely way a fresh session re-derives the old process. README is not
hash-governed; this edit is safe.)

.gitignore — add `!runs/dev-v2/` after the `runs/*` rule so new evidence is
tracked (audit: everything §4 writes is currently ignored; the negation works
because `runs/*` matches only direct children). Existing runs/** content is
otherwise untouched.

CODER_BENEFICIAL_SENSITIVITY_M2_IMPLEMENTATION_PLAN.md — Status header only:
append "Section 13 closed <date> with no promising task (ledger:
handoffs/PROCESS_FINDINGS_2026-08-19.md). Task development authority:
TASK_TOOLING_V2_PLAN.md." Do not rewrite history; do not delete sections.

## 6. Science sequence (prepared by the implementer, launched on approval)

All results are development-only: every task below is or becomes
outcome-exposed and can never join a confirmatory suite.

1. Salience probe (~3 calls). Source bytes: trial/task-a (durafmt) in
   handoffs/claude-trial-tasks-ab.tar (already exposed as rolling-v1-05 →
   ceiling; the clone is a new task id with parent recorded). Build the clone in
   §2 layout, then LOWER SALIENCE FOR REAL — the audit showed deleting one
   contract sentence is useless because pointers are duplicated in five files.
   Delete: the contract's enumeration sentence, README's two pointer lines, and
   the per-file "Acceptance note TRIAL-A-n (full wording in docs/upgrading.md)"
   breadcrumb comments in examples/ and tests/. Keep: the full requirement
   statements in docs/upgrading.md and README, and add one honest general
   clause to the contract: "Additional acceptance criteria appear in the
   project documentation; all of it is in scope." (salience: enumerated →
   pointer, no scope contradiction.) The old checker pins protected-file hashes
   and file sets — regenerate those constants for the clone's bytes; assertion
   logic must not change. Admit via taskcheck, queue REQUEST.json for 3 null
   attempts. q < 1.0 without a fidelity defect ⇒ the salience dial is real.
2. Low-salience batch (15 calls): import factory tasks 07, 08, 09, 11, 12 from
   handoffs/claude-factory-batch-01.tar (§8), admit, queue.
3. If a band appears: N-vs-P contrast (~24–32 calls) on band tasks — same task
   bytes, arm file injected per §4. This is the project's central question.
4. OUT OF SCOPE for the implementing session: amending the M2/protocol gates.
   That is a separate scientific decision Wade makes after probe data exists.
   Equally: harm-detection and cost-comparison studies are additional future
   deliverables and never replace probes 1–3.

## 7. Acceptance criteria (all binding)

1. Scope discipline: no roles, approvals, schedules, or receipt systems beyond
   what §3–§4 specify; no new dependencies; budgets of §1.6 held.
2. tooling/ is self-contained and repo-agnostic: no imports from src/**, no
   hardcoded repo paths, `python3 -m unittest discover -s tooling` green using
   only synthetic temp-dir tasks, and tooling/README.md documents the
   task-layout-v2 and check-result-v2 contracts. The repo suite
   (`python3 -m unittest discover -s tests -v`) also stays fully green
   (baseline: 179 tests, 6 skipped, ~4 min — audit-verified). Expect the suite
   to run SLOWER after import: tests/test_config.py copies the repo tree six
   times and will now include tasks/ and tooling/ — slower is expected, not a
   failure.
3. Factory import (§8) done; `taskcheck batch tasks/` admits ≥10 tasks, each
   with a provenance-carrying blind solution from an isolated agent (≤2
   concurrent). Run the gate on task-11 before "repairing" it — the audit found
   its checker intact (356 lines, parses, complete); the truncation note in
   PROCESS_FINDINGS appears stale.
4. Documentation edits exactly as §5; no other governed file touched; runs/**
   existing evidence untouched. GUARD: the §5 status-header edit changes the M2
   plan file's SHA-256; recent history shows the test suite tolerates plan-file
   edits, but if any hash-binding test fails after the §5 edits, STOP and
   report to Wade — do not "fix" it by updating frozen configs or evidence.
5. Ledger + git anchoring works: `verify` detects a mutated manifest, a broken
   chain, and a deleted task.
6. The §6.1 salience-probe clone is admitted and its REQUEST.json is queued.
   (The goal is load-bearing: shipping tooling without queuing the probe fails
   acceptance.)

## 8. Factory import notes (one-time, helpers under scripts/import/, budget-exempt)

- Source: handoffs/claude-factory-batch-01.tar → factory/task-NN/{public/,
  check.py, reference/} → tasks/fac-NN/ in §2 layout.
- Strip all __pycache__/.pyc (23 entries exist, all inside task-01/blind/ and
  task-03/blind/). Remove CODER.md from public/ (it moves to arm injection).
- Existing blind/ dirs (tasks 01, 03) predate PROVENANCE.json — regenerate
  their provenance or re-run their blind solves; the other tasks need fresh
  blind solves by isolated agents (public/ only, ≤2 concurrent).
- trial/task-a in handoffs/claude-trial-tasks-ab.tar is the §6.1 source; its
  reference/ and blind/ are directories already (no materializer needed there).
  The rolling-v1 JSON task format (reference.json file-maps) is NOT being
  imported — ignore it.
