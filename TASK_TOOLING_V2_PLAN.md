# Task Tooling & Process v2 — Implementation Plan (rev 2, post-audit)

Status: ACTIVE as of 2026-08-20.
Rev 2 incorporates all findings from two independent audits (2026-08-19).

The implementing session works on a NEW BRANCH (suggested: task-tooling-v2)
created from the branch containing this plan file. It never commits directly to
main or to any existing agent/* branch; Wade merges when acceptance (§7) passes.

ATOMIC ACTIVATION (audit: flipping ACTIVE before the AGENTS.md edit creates a
window where AGENTS.md forbids this plan): the status flip and ALL §5
documentation edits are ONE commit — the implementing session's first commit.
Until that commit, this plan is proposed and AGENTS.md's old sentence stands;
from that commit, authority is transferred with no contradictory intermediate
state. For confirmatory experiments the M2 protocol and its integrity
machinery remain fully binding — this plan claims development only.

Authority: on adoption this plan is the sole authority for TASK DEVELOPMENT.
Section 13 of CODER_BENEFICIAL_SENSITIVITY_M2_IMPLEMENTATION_PLAN.md is closed
(no promising task found; ledger in handoffs/PROCESS_FINDINGS_2026-08-19.md).
The M2 plan and all frozen evidence remain immutable history, and its
confirmatory-experiment machinery is retained for final experiments. §5 updates
AGENTS.md's authority sentence so no contradiction remains.

Vocabulary used throughout:
- ADMIT: pass the offline mechanical gate. Re-runnable any number of times.
  Admitted tasks may be freely repaired and re-admitted.
- EXPOSE / FREEZE: the first LAUNCHED subject attempt on a task (launched =
  subject process started, whether or not the attempt proves usable). Exposure
  is recorded as an append-only line in tasks/exposures.jsonl (same chain
  format as the admit ledger); from that line's existence the task's bytes are
  immutable forever, and `admit` MUST refuse any task id present in
  exposures.jsonl. RETIREMENT of a defective exposed task is another
  exposures.jsonl line ({task_id, retired_reason}) — manifests are never
  edited after exposure. A repaired copy is a new task recording its parent.
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
   scripts/run_null_batch.py ≤300; tests/test_run_null_batch.py ≤200 (uses a
   FAKE runner — zero live calls, matching the repo's existing fake-replay
   test pattern; must cover: exposure refusal, approval hash mismatch refusal,
   exclusive-create collision, omission-vs-incorrect classification).
   Total target ≤1,300, hard cap 1,600. Over cap ⇒ cut scope; never expand.
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
├── blind.provenance.json    # at task root, NOT inside blind/ (a file inside
│                            # blind/ would contaminate exact-file-set checkers);
│                            # required keys pinned in tooling/README.md; the
│                            # input_tree_sha256 MUST equal the public/ tree hash
├── requirements.json        # REQUIRED, machine-readable: for every checker key
│                            # {"R1": {"target_paths": [...], "omission_probe":
│                            #   {"type": "path_absent"|"text_absent",
│                            #    "path": "...", "text": "..."}}, ...}
│                            # The probe is a tiny declarative test of the FINAL
│                            # TREE ("this file doesn't exist" / "this string is
│                            # absent from this file") that fires when the
│                            # deliverable was never attempted. Probes are
│                            # AUTO-VALIDATED at admit: each must FIRE on
│                            # pristine public/ and NOT fire on reference/ —
│                            # semantic omission detection with zero mutant
│                            # authoring (see §4).
└── manifest.json            # written by admit: per-file SHA-256, gate results,
                             # salience: enumerated|pointer|none,
                             # parent_task_id: null|<id>
                             # (rewritable by re-admission ONLY pre-exposure;
                             # retirement lives in exposures.jsonl, never here)
```

Optional, never required: NOTES.md (free documentation), mutants.json
(machine-readable: requirement id → file → change; not consumed by v1 tooling).
No mutants.md exists anywhere and none is required — audit finding.

check.py contract: stdlib only; argv[1] = workspace path; lives outside the
workspace and writes nothing into it; MUST NOT read, list, or assert on
CODER.md in any way — the arm file is runtime-injected and is not part of the
task (admit enforces this mechanically: the checker is run twice on scratch
public/, once with no CODER.md and once with a nonzero sentinel CODER.md
present; outputs must be identical — the ARM-NEUTRALITY check. Checkers with
exact-file-set inventories must therefore exclude CODER.md); last stdout line
is JSON
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

- `admit <task-dir>` — offline gate, seconds, re-runnable (refuses any task id
  already present in exposures.jsonl):
  1. Layout: public/, check.py, reference/, blind/, blind.provenance.json, and
     requirements.json present; NO CODER.md inside public/ or blind/; no
     __pycache__/.pyc/.git junk anywhere. requirements.json must map every
     requirement key the checker emits to ≥1 target path and one omission
     probe; every target path must exist in reference/ (deliverables may be
     new files absent from public/).
  1b. Probe validation: every omission_probe FIRES on a scratch copy of
     public/ and does NOT fire on a scratch copy of reference/. A probe
     failing either direction fails admission.
  1c. Arm neutrality (§2): checker output on scratch public/ identical with
     and without a sentinel nonzero CODER.md present.
  2. Blind provenance: blind.provenance.json input_tree_sha256 equals the
     current public/ tree hash (tree hash = SHA-256 over sorted relative-path +
     per-file SHA-256 lines). Provenance is recorded when the blind solve is
     COMMISSIONED, never reconstructed afterward — a provenance whose input
     hash cannot be reproduced from the recorded tree is invalid.
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
- `batch <dir>` — admit or verify EVERY child directory containing a check.py
  (no name-pattern filter — audit: `task-*` would have missed the imported
  `fac-NN` tasks); summary table; exit nonzero on any failure.

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
5. Write everything under runs/dev-v2/<batch-id>/<task-id>/<arm>/attempt-N/
   (raw JSONL, stderr, final message, checker JSON, capture diff, hashes,
   durations). Every attempt directory is EXCLUSIVE-CREATE: if it exists, stop
   with an error — evidence is never overwritten or mixed across batches/arms.
   disposition.json is exclusive-create too. `run_null_batch verify <batch>`
   recomputes every attempt-manifest hash and the evidence-ledger chain —
   post-hoc edits and deletions become detectable, not just initial
   collisions.

Attempt lifecycle (atomic, crash-safe): (1) create the attempt dir
exclusive-create and write intent.json (task, arm, ordinal); (2) append the
task's exposure line to exposures.jsonl if absent — the freeze boundary is
this append, BEFORE spawn, so a crash after spawn can never leave an exposed
task unrecorded; (3) spawn the subject; (4) capture evidence; (5) write
attempt-manifest.json (SHA-256 of every evidence file) and chain it into
runs/dev-v2/<batch-id>/evidence-ledger.jsonl — an attempt without a finalized
manifest is INCOMPLETE.
Accounting: pre-spawn failure (no subject call) consumes nothing; delete-free
relaunch is allowed (the incomplete dir is kept, next ordinal used). An
attempt whose subject launched and whose evidence finalized is USABLE — never
retried, whatever its outcome. A post-spawn INFRASTRUCTURE failure (runner
crash, capture incomplete — no subject fault, manifest never finalized) is
preserved, labeled infra-invalid, and grants at most ONE replacement attempt
per task; a second infra failure on the same task marks the task's
disposition invalid. "Three attempts" means three usable attempts.

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
- A failed requirement is an OMISSION iff its validated omission_probe
  (requirements.json, admit-validated per §3 step 1b) fires on the attempt's
  final tree — the deliverable is semantically absent. The captured diff
  against target_paths is recorded as supplementary evidence but does not
  decide the label (audit: diff-touch is corrupted by shared files, whitespace,
  and work in alternative locations). An attempt is OMISSION-ONLY if every
  failed requirement is an omission and no regression failed.
- Labels, applied in order: invalid (evidence/determinism/protected-input
  defect prevents valid scoring) → wrong-failure-mode (any valid nonresolution
  not omission-only) → promising (0.55 ≤ q ≤ 0.90 AND s ∈ {1,2}, omission-only)
  → ceiling (s = 3, or s ∈ {1,2} and q > 0.90) → floor (s = 0, or s ∈ {1,2}
  and q < 0.55).
- fidelity_note: string, ≤200 chars, empty unless label is invalid.

Rules: invalid evidence is preserved and labeled, never deleted. Exposure
freezes the task (exposures.jsonl line). A retired task gets a retirement line
in exposures.jsonl — its manifest and bytes stay untouched; its repaired copy
is a new task with parent_task_id set, MUST NOT weaken or alter checker
semantics beyond the recorded defect, and the disposition report always counts
retired ancestors in denominators (no laundering).

THE human checkpoint, hash-bound (audit: an unbound approval is no approval):
the script writes runs/dev-v2/<batch-id>/REQUEST.json containing the batch id,
each task's id + manifest_sha256, the arm name + arm-file SHA-256, the exact
call count, and the pinned runner constants — then exits. It launches only
when APPROVED.json exists beside it containing {"request_sha256": <SHA-256 of
REQUEST.json's bytes>}, verified at launch. Any mismatch (request edited after
approval, wrong hash) is a refusal to launch. No other approval exists
anywhere in this system.

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
   everything under `docs/` has NO standing over TASK DEVELOPMENT — for
   development work their imperative language ('must', 'stop', 'prohibited',
   role, gate, and approval rules) binds nobody. Their evidence is immutable.
   For CONFIRMATORY experiments, `CODER_BENEFICIAL_SENSITIVITY_PROTOCOL.md`
   and the M2 integrity machinery remain fully binding.
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
   pointer, no scope contradiction.) FACT CORRECTIONS (rev 4, audit-verified):
   the trial tar's check.py has NO pinned protected-file constants — nothing
   to regenerate; the tar has no trial/task-a/blind/ (the old blind solution
   sits in trial/solve-a/workspace/ and is INVALID for the clone anyway, since
   the clone's public text differs). Build the clone, write requirements.json
   with probes, commission a FRESH blind solve of the edited public/ (with
   provenance), admit via taskcheck, queue REQUEST.json for 3 null attempts.
   q < 1.0 without a fidelity defect ⇒ the salience dial is real.
2. Low-salience batch (15 calls): import factory tasks 07, 08, 09, 11, 12 from
   handoffs/claude-factory-batch-01.tar (§8), admit, queue.
3. If a band appears: N-vs-P contrast (~24–32 calls) on band tasks — same task
   bytes, arm file injected per §4. This is the project's central question.
Rev-4 note on omission detection: rev 3's diff-based predicate was rightly
rejected by audit (shared files, whitespace, alternative-location work all
corrupt it). Adopted instead: declarative per-requirement omission probes in
requirements.json, auto-validated at admit against pristine (must fire) and
reference (must not fire) — semantic detection with near-zero authoring cost.
Full hand-authored mutants remain deliberately NOT required; the
pristine/reference validation provides the same per-requirement negative
coverage mutants gave, mechanically.

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
   concurrent). task-11's checker CRASHES at runtime (KeyError: a JSON brace
   colliding with a str.format template — it parses but cannot run; rev 3
   wrongly called it intact, the original findings note was right). Repair the
   format call or drop the task; ≥10 admitted tasks is the bar either way.
   Also fix `taskcheck batch tasks/` per §3 (any dir with check.py — imports
   are named fac-NN).
4. Documentation edits exactly as §5; no other governed file touched; runs/**
   existing evidence untouched. GUARD: the §5 status-header edit changes the M2
   plan file's SHA-256; recent history shows the test suite tolerates plan-file
   edits, but if any hash-binding test fails after the §5 edits, STOP and
   report to Wade — do not "fix" it by updating frozen configs or evidence.
5. Ledger + git anchoring works: `verify` detects a mutated manifest, a broken
   chain, and a deleted task; `admit` refuses a task id present in
   exposures.jsonl; run_null_batch refuses an unapproved or hash-mismatched
   request and refuses to overwrite an existing attempt directory (all proven
   by the fake-runner tests, no live calls).
6. The §6.1 salience-probe clone is admitted and its REQUEST.json is queued.
   (The goal is load-bearing: shipping tooling without queuing the probe fails
   acceptance.)

## 8. Factory import notes (one-time, helpers under scripts/import/, budget-exempt)

- Source: handoffs/claude-factory-batch-01.tar → factory/task-NN/{public/,
  check.py, reference/} → tasks/fac-NN/ in §2 layout.
- Strip all __pycache__/.pyc (23 entries exist, all inside task-01/blind/ and
  task-03/blind/). Remove CODER.md from public/ (it moves to arm injection).
- DELETE the existing blind/ dirs (tasks 01, 03) on import: their inputs
  included CODER.md, so honest provenance for the post-import tree cannot be
  reconstructed (audit) — fabricating it would be false provenance. ALL
  imported tasks get fresh blind solves by isolated agents against the
  imported public/ (no CODER.md), with provenance recorded at commissioning,
  ≤2 concurrent.
- trial/task-a in handoffs/claude-trial-tasks-ab.tar is the §6.1 source; its
  reference/ and blind/ are directories already (no materializer needed there).
  The rolling-v1 JSON task format (reference.json file-maps) is NOT being
  imported — ignore it.

## 9. CLI/JSON contracts (the underspecified corners, pinned)

- Task ids: `[a-z0-9-]{1,40}`. Ledger paths default to `<tasks-parent>/
  ledger.jsonl` and `<tasks-parent>/exposures.jsonl`, overridable via
  `--ledger` / `--exposures`. batch takes an explicit mode:
  `batch admit <dir>` / `batch verify <dir>`.
- Author-supplied inputs feeding the manifest: `task-meta.json` at task root
  (optional) carries `{"salience": ..., "parent_task_id": ...,
  "layout_version": 2|3}`; absent → salience "enumerated" (the conservative
  default), parent null, layout_version 2. Everything else in the manifest is
  computed by admit; manifest.json copies layout_version verbatim.
- manifest.json: {"task_id", "files": {relpath: sha256, ...}, "salience",
  "parent_task_id", "gate": {step: pass|fail detail, ...}, "requirements":
  <verbatim requirements.json>, "created": iso8601}.
- exposures.jsonl lines: {"task_id", "event": "exposed"|"retired",
  "batch_id", "reason": null|str, "prev_sha256"} — same canonical-JSON chain
  rules as the admit ledger.
- Resume: re-running a batch is idempotent — completed attempts (finalized
  manifest) are skipped; incomplete dirs are left in place and the next
  ordinal is used, subject to the §4 infra-replacement cap.

## 10. PHASE 2 — Task Factory + Measurement Bridge (rev 2, post-audit)

Status: Phase 2 ACTIVE as of 2026-08-20. New branch off the branch containing
this plan; Wade merges on acceptance (§10.6). §§1–9 remain in force EXCEPT
where §10 explicitly
supersedes them; every supersession is marked "SUPERSEDES". Two audits
(2026-08-20) are incorporated; their factual findings are stated inline so the
implementer does not rediscover them.

Layout version: Phase 2 introduces task-layout-v3 (adds stated_in fields and
new provenance keys, below). The ONE selector (audit: three passages
disagreed): "layout_version": 3 is authored in task-meta.json; admit reads it
there, applies v3 rules, and copies it into manifest.json; absent = v2
(legacy). §9's task-meta.json and manifest.json schemas are amended
accordingly. Updating tooling/README.md to document v3 is REQUIRED and
authorized (an edit, not a new document).

### 10.1 Deliverable A: taskgen — tooling/taskgen.py ≤250 lines

(roadmap.md calls this "make"; same thing.)
- Input: recipe JSON file with exactly these keys:
  {"task_id": "...", "family": "bug|feature|refactor|cli", "theme": "...",
   "requirement_count": 8-12, "salience": "enumerated|pointer|none",
   "md_filename": "CODER.md"}. md_filename is consumed ONLY by the driver
  (never rendered into the authoring prompt — public/ stays arm-invariant).
- Agent command template from CLI arg, e.g. ["claude","-p","{prompt}"] or
  ["codex","exec","{prompt}"]. Repo-agnostic, agent-agnostic.
- Runs the agent in an empty scratch dir; copies into tasks/<id>/ ONLY:
  public/, check.py, reference/, requirements.json, task-meta.json. HARD-FAILS
  if the agent emitted blind/, blind.provenance.json, or manifest.json —
  (audit) otherwise the generator can fake its own blind solve and walk
  through admit.
- Destinations are exclusive-create: taskgen refuses an existing tasks/<id>/.
- Output is untrusted; only `admit` makes it usable. Prompts live in
  tooling/prompts/ as versioned text files.

### 10.2 Deliverable B: blindsolve — tooling/blindsolve.py ≤180 lines

- Copies tasks/<id>/public/ to a scratch dir, records input_tree_sha256 FIRST,
  runs the solver agent there via the command template, copies the result to
  blind/, writes blind.provenance.json.
- Provenance keys (task-layout-v3, REQUIRED): {"solver_agent",
  "solver_command_sha256", "sandbox_flags", "timestamp", "input_tree_sha256"}.
  taskcheck's required-key set and README are updated to match (currently
  {solver_agent, timestamp, input_tree_sha256} — a breaking v3 change, which
  is why the layout version exists).
- HONESTY CLAUSE (audit): an empty scratch cwd is NOT a security barrier — a
  host agent can read the repo by absolute path or use the network. Therefore:
  the command template MUST include the strongest scoping flags the agent CLI
  offers (sandboxing/no-network where supported), those flags are recorded in
  sandbox_flags, and the design accepts that blind-solve fidelity is
  best-effort pre-exposure screening; the live null attempts remain the final
  fidelity probe. Per-task timestamps. ≤2 concurrent solvers.
- Mutation safety (audit): blindsolve refuses any task id present in
  exposures.jsonl; stages the solve in a temp dir and atomically replaces any
  existing pre-exposure blind/; rejects symlinks and special files in the
  solver output; re-verifies the public/ tree hash is unchanged afterward.

### 10.3 Deliverable C: spread check — inside taskcheck (+≤160 lines; file cap
SUPERSEDES §1.6: taskcheck.py ≤620 total; currently 451)

- requirements.json (v3) gains per requirement "stated_in": {"path": ...,
  "quote": "..."} — the exact public sentence stating the requirement. Quotes
  must be ≥1 full sentence and pairwise non-overlapping.
- admit under v3 verifies:
  (a) every quote appears verbatim in its declared public file;
  (b) MASTER-LIST SCAN (audit fix): for EVERY public file, count how many of
      the N requirement quotes occur verbatim anywhere in it — any file
      exceeding the per-file cap fails. The scan covers all files, not just
      declared paths, so a duplicated master list is caught;
  (c) salience "pointer"/"none" additionally requires statements spread
      across a minimum number of distinct files.
  Thresholds are CLI args with defaults (--max-stated-per-file 3,
  --min-statement-files 4) — policy stays out of the tool (audit).
- Layout selection (audit: the manifest cannot select the rules that produce
  it): "layout_version": 3 originates in task-meta.json, authored with the
  task; admit reads it there, applies v3 rules, and copies it into the
  manifest. Absent field = v2 (legacy). A v3 admit without stated_in fails —
  no opt-out hole.
- Arm filename: taskcheck gains --md-filename (default CODER.md) used by the
  arm-neutrality sentinel and the forbidden-name check (audit: three
  hardcoded sites, taskcheck.py:135 and :271-273).

### 10.4 Deliverable D: two-arm driver — scripts/run_batch.py

SUPERSEDES §1.6/§4 file facts: the Phase 1 file is 297/300 lines only via
compressed formatting (audit); Phase 2 REWRITES it as run_batch.py, cap 550
lines, NORMALLY FORMATTED — golfing to fit a budget is itself an acceptance
failure. tests/test_run_null_batch.py (190/200) is replaced by
tests/test_run_batch.py ≤300. Exactly one import-site rename exists (audit).
- Batches name ONE or TWO arms. Two-arm: per task, arm order alternates
  (paired); 3 usable attempts PER ARM per task (two-arm task = 6 calls);
  infra-replacement cap applies per (task, arm); a task whose arms end with
  unequal usable counts is EXCLUDED from the paired test and listed in the
  report (audit).
- REQUEST schema v2: {"batch_id", "tasks": [{id, manifest_sha256}...],
  "arms": [{name, path, sha256}...] (1 or 2), "call_count" = tasks × arms × 3,
  "replacement_call_cap" (per §4 infra rules), "max_total_calls" =
  call_count + replacement_call_cap — launch refuses any call beyond it
  (audit: approval must bound replacement spend, not just nominal),
  "md_filename" (validated: bare basename matching [A-Za-z0-9._-]+, no path
  separators; REQUEST is its single canonical source), "task_order_seed"
  (task order randomized per batch, seed recorded), "runner": {...}}. Arm
  names are distinct labels even when
  files are identical (A/A = two labels, one file — audit: same-label dirs
  would collide). verify accepts BOTH the v1 single-arm schema (existing
  frozen salience-probe-v2 evidence must keep verifying) and v2 (audit).
- md_filename end-to-end (audit): recorded in REQUEST and in every attempt's
  evidence; and the subject wrapper prompt must name the SAME file — since
  the frozen src wrapper hardcodes "CODER.md", run_batch owns a wrapper
  template (default = the existing wording with the filename substituted)
  and records the rendered wrapper's SHA-256 in evidence. Task files never
  carry md_filename (tasks stay arm-invariant).
- RUNNER constants become CLI args with current values as defaults; the arm
  filename becomes --md-filename (default CODER.md).
- SUPERSEDES the prior frozen-file edit authorization and the matching
  exception language in §10.6.6–7: authorization to edit
  src/mdseval/runner/codex_cli.py is WITHDRAWN because the edit breaks its
  frozen runner hash binding (18 full-suite test errors). That file remains
  byte-for-byte frozen and no frozen experiment hash binding changes.
  run_batch.py alone substitutes REQUEST.md_filename into the exact
  project_doc_fallback_filenames argument returned by build_codex_command;
  the default CODER.md produces the existing argument and behavior unchanged.

### 10.5 Deliverable E: compare + verdict — tooling/compare.py ≤300 lines

- Inputs (audit fix — pinned to what exists on disk): for each task and arm,
  <batch>/<task>/<arm>/disposition.json ({q, s, label, ...}); per-attempt
  result.json is NOT consumed. compare never recomputes q/s/label (no second
  source of truth).
- Per-task delta = s_B − s_A (resolved counts, 0–3). Effect = mean(delta)/3.
  Ties (delta 0) are excluded from the sign test; n_effective (nonzero
  deltas) is always reported; below --min-effective (default 6) the verdict
  is INCONCLUSIVE by rule. Exact two-sided sign test, own implementation
  (deliberate ~40-line duplication of src/ stats for repo-agnosticism —
  audit noted the duplication; it is accepted), enumeration cap 24 tasks.
- Integrity (audit: presence-checking is tamperable): run_batch appends each
  disposition.json's SHA-256 as its own evidence-ledger entry at write time;
  compare re-verifies the chain AND each disposition's bytes against its
  ledger entry. Any failure, any disposition label "invalid", or the two
  arms' recorded runner params differing → verdict INVALID.
- Verdict rules, pinned (rev-4 audit caught a REVERSED label): delta =
  s_B − s_A, so positive effect means arm B won. B_BETTER iff p ≤ alpha AND
  effect ≥ +threshold; A_BETTER iff p ≤ alpha AND effect ≤ −threshold;
  otherwise INCONCLUSIVE (unless INVALID). Defaults alpha 0.05, threshold
  0.20; both are CLI args and both are embedded in verdict.json.
- Attrition vs INVALID, reconciled (audit): a task whose disposition is
  labeled "invalid" (e.g. infra exhaustion) or whose arms have unequal usable
  counts is EXCLUDED from the test and listed in the report. Verdict-level
  INVALID is reserved for: ledger/chain or disposition-hash failure, arm
  runner-param mismatch, or more than 25% of the batch's tasks excluded.
- Disposition-ledger rows (audit: were undefined): same canonical-JSON chain,
  {"type": "disposition", "task_id", "arm", "sha256", "prev_sha256"}; exactly
  one per (task, arm), appended immediately after the disposition file is
  written exclusive-create; on crash-resume the append is made if missing
  (idempotent). disposition.json itself gains a "runner" object copied from
  its attempts so compare can check arm equality without reading attempts.
- verdict.json + markdown report MUST embed: thresholds used, both arm names
  + file SHA-256s, batch id, evidence-ledger head hash, task list with
  per-task deltas, n_effective, excluded/unbalanced tasks, resolved runner
  params (audit: nothing verdict-affecting may live only in CLI history).
- Verdicts: {A_BETTER, B_BETTER, INCONCLUSIVE, INVALID}.

### 10.6 Phase 2 acceptance criteria (all binding; SUPERSEDES §1.6/§7.1
budgets for Phase 2)

1. Budgets: taskgen ≤250; blindsolve ≤180; taskcheck ≤620 total; run_batch
   ≤550 (normally formatted); compare ≤300; tests (new/extended, all suites)
   ≤450. Phase 2 total new/changed target ≤1,700, hard cap ≤2,100 (includes
   the run_batch rewrite; prompts/docs/task content excluded). Combined
   post-Phase-2 tooling+scripts+tests budget: ≤3,000 lines.
2. Factory proof, zero live calls: taskgen with a scripted fake agent (a
   stdlib python script invoked via the command template that materializes a
   fixed task tree in cwd) produces a task; blindsolve with a scripted fake
   solver produces blind/ + v3 provenance; admit (v3) passes it; the
   master-list scan REJECTS a fixture task whose quotes are duplicated into
   one extra file; taskgen hard-fails a fake agent that emits blind/.
3. Measurement proof, fake runner: a two-arm batch runs end-to-end; compare
   emits verdict.json + report with all required embedded fields; A/A (two
   labels, one file) yields INCONCLUSIVE with n_effective reported; a
   KNOWN-WINNER fixture (fake runner scripted so arm B resolves strictly
   more tasks) yields B_BETTER — the direction test the reversed-label
   defect proved necessary; v1 single-arm evidence (salience-probe-v2) still
   verifies.
4. Real-agent demo: taskgen + blindsolve on ONE task via a real agent CLI
   (agent calls are not subject live calls; ≤2 concurrent), admitted under
   v3.
5. Low-salience batch prep (audit-corrected reality): the five tasks are
   fac-07, fac-08, fac-09, fac-11, fac-12; their manifests currently say
   "enumerated" (no task-meta.json exists) and sampled tasks put 4
   requirements' statements in one file, so EXPECT: public/ doc edits to
   spread statements, ~50 hand-copied stated_in quotes (authoring work, agent
   labor, budget-exempt), fresh blind solves after every public/ edit (tree
   hash changes), then v3 re-admission WITH task-meta salience "pointer" or
   "none" — a re-admitted task still labeled "enumerated" fails this
   criterion (audit: the target salience was never pinned). Then queue a
   NULL-ONLY calibration
   REQUEST (5 tasks × 3 calls) for Wade — calibration first; the salience
   probe FAILED (q = 1.0) and this batch is its real test, not a formality.
   (The previously mentioned "pending 15-call request" does not exist —
   audit — and hash-bound requests must be regenerated after re-admission.)
5b. The MD-vs-MD contrast is a SEPARATE, LATER measurement gate, out of
   Phase 2 implementation scope (audit: the plan may not jump past a failed
   calibration). Preconditions before its REQUEST may even be queued:
   calibration yields enough band tasks that the cohort is prospectively
   sized FROM CALIBRATION RATES (not a bare count: ≥8 tasks queued AND the
   calibration-measured tie rate implies ≥6 expected non-tied — 5 tasks can
   never reach significance: 5/5 wins gives p = 0.0625); the helpful-arm
   file is named
   and SHA-256-pinned in the REQUEST prospectively; and the report labels
   results DEVELOPMENT-ONLY, supporting no incumbent/candidate replacement
   claim.
6. All suites green; no governed file touched; no new documents
   (tooling/README.md and tooling/prompts/* edits are
   authorized); no live subject calls anywhere in Phase 2 implementation.
7. Boundary ruling, recorded so audits stop re-raising it: authoring and
   blind-solve agent invocations are NOT subject calls and need no
   REQUEST/APPROVED — the single human checkpoint (§1.2) covers live subject
   spend only. Requiring approvals for agent labor would reinstate
   per-candidate ceremony; Wade controls that spend by launching sessions.
   To remove the wording ambiguity audits keep citing, one clarifying edit
   to AGENTS.md is authorized: "live-call spend" → "live subject-model call
   spend". Likewise recorded: §10.4 withdraws the former codex_cli.py edit
   exception after its frozen hash binding failed; run_batch.py owns the
   development-only filename substitution, leaving confirmatory machinery
   and every frozen experiment binding unchanged.

### 10.8 Audit closure

Phase 2 has now had four independent audit rounds (two commissioned here, two
by Wade's other session) totaling ~45 findings, all dispositioned in-plan.
Round 4's sole functional defect was the reversed winner label — now fixed
and covered by a mandatory direction test. Findings-per-round is collapsing
into wording consistency and confirmatory-grade hardening that belongs to the
(already-retained) confirmatory machinery, which is this repository's known
failure spiral. Further document-level audits are DECLINED; residual risk is
owned by the §10.6 acceptance tests, which exercise every contract this
section pins. The scientific auditor's remaining recommendations (randomized
schedules beyond the recorded seed, formal power analysis, task-independence
controls, additional directional tests) are deferred to the confirmatory
protocol where they already exist.

### 10.7 Out of scope (recorded so nobody drifts)

PR-to-task mining, game domains (PD/SF2), challenge/submission operations,
CI packaging, the Stage-4 optimizer loop, any change to frozen confirmatory
machinery, and any statistics beyond the §10.5 sign test. See roadmap.md
"Tooling coverage note".

## 11. PHASE 3 — Real-Issue Sourcing: the Headroom Hunt (hours-scale)

Status: PROPOSED (flips to "Phase 3 ACTIVE as of <date>" on Wade's word).
Branch: off task-tooling-v2-phase2 (Phase 2 code is required). Timebox: ONE
working day of agent labor plus one approved live batch, then a decision.
No new tooling code is required; helper scripts go under scripts/import/
(budget-exempt). No new documents. ≤2 agents concurrent.

### 11.1 Why (one paragraph, so nobody re-litigates)

Synthetic tasks of every tested design saturate: the bare model solves 100%.
Published benchmarks show the same model class failing 25-40% of REAL
repository tasks. Phase 3 imports reality: agents reconstruct candidate tasks
from real open-source repos (revert a test-covered bugfix; the repo's own
tests anchor the checker), and the model's own runs filter them — keep what
it fails. This is the scalable form of "failure-derived": failures are
manufactured by running the model, not collected from history. Yield decides
everything; essays don't.

### 11.2 Deliverable A: 4-6 candidate tasks (agent labor, hours 0-3)

- Source rule: real, dependency-light Python repos (stdlib-preferred; small
  vendorable deps allowed — the runner sandbox has NO network). Pick a real
  closed issue whose fix commit includes tests. public/ = repo at the
  pre-fix commit, with .issue-contract.md adapted from the real issue text.
  reference/ = the real fix applied. check.py wraps the repo's own test
  commands (fix tests must fail on pristine, pass on reference).
- Format: existing task-layout-v3. PRAGMATIC RELAXATIONS for this cohort,
  recorded here so taskcheck expectations are clear: requirement keys map to
  the fix's named tests; omission probes may be trivial (text_absent of a
  fix identifier) because Phase 3 needs only resolved-counts (band
  measurement), not omission classification. Blind solves are OPTIONAL for
  null scouting but REQUIRED before any Phase 3 task is used in a treatment
  comparison.
- Provenance: failure-source.json per task (source repo, issue/commit ids,
  license note). Only permissively-licensed repos.

### 11.3 Deliverable B: null-scout batch (hours 3-5)

Admit candidates via taskcheck; queue ONE batch: every admitted candidate x 3
null attempts (12-18 calls). One REQUEST/APPROVED cycle. Read dispositions.

### 11.4 Decision gate (binding; the point of the phase)

| Yield after 3 attempts/task | Decision |
|---|---|
| >=2 tasks with any failure (s<3) | HEADROOM EXISTS. Scale the lanes (same recipe, more agents/days), build the first challenge pack from band tasks, then run the MD contrast per §10.6.5b. Record measured yield rate — scaling math is now arithmetic. |
| Exactly 1 | Weak signal: reconstruct 4-6 more from DIFFERENT repos before deciding (one more day max). |
| 0 — model solves real tasks too | Completion headroom is dead for this model, full stop. The product pivots to cost + regression scoring (both already measurable), and the roadmap's task-source/import decision is made with this data. No further synthetic cohorts of any design. |

### 11.5 Repo extraction note

The tooling stays in this repo for now. Extraction trigger: preparing the
Stage 1 open-source release (or a second consuming project), whichever comes
first — it is a git subtree split, ~minutes, and doing it earlier just adds
sync overhead while Phase 3 may still adjust the tools.
