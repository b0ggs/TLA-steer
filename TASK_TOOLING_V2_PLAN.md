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

## 11. PHASE 3 — Real-Issue Headroom Hunt + Local MD-Sensitivity Probe
(consensus rev: merged from both AIs' versions by two-auditor adjudication, 2026-08-22)

Status: Phase 3 ACTIVE as of 2026-08-22.
Branch: off task-tooling-v2-phase2. Timebox: 4-5 candidates, 1-2.5 working
days of agent labor (audit-verified estimate; "one day" was optimistic) plus
TWO hash-approved live batches, each a mandatory stop. ≤2 agents concurrent.
Helper scripts only under scripts/import/ (budget-exempt but CAPPED: <=300
lines total, single-repo scope, no generalized issue-mining framework). §11
narrowly supersedes §10.7's mining exclusion for these 4-5 manually
reconstructed candidates only. No new documents —
task content, provenance, controls, REQUEST/APPROVED, and run evidence are
artifacts, not documents. blindsolve/taskgen agent invocations are agent
labor, not live subject calls, and sit outside the two-batch limit.

### 11.1 Why, and the permitted claim

Synthetic tasks of every tested design saturate (one historical exception:
scout-c-integration-01 resolved 1/3 once, never replicated) — the bare model
otherwise solves 100%.
Published benchmarks show this model class failing 25-40% of REAL repository
tasks. Phase 3 reconstructs candidate tasks from real repos and lets the
model's own runs filter them. Yield decides everything; essays don't.

A pass permits exactly: "this frozen MD produced a local development signal
on this selected task under gpt-5.6-sol/high." It does NOT establish a
population effect, statistical significance, general MD benefit, or behavior
under another model. This phase does not invoke §10.6.5b (its cohort/sizing
preconditions are untouched; an n=1 probe simply isn't that contrast).
compare's verdict on a 1-task paired batch is expected INCONCLUSIVE
(min_effective=6) — PROVIDED nothing is excluded; one invalid disposition or
unequal usable counts yields INVALID on a 1-task batch. Cost is not measured
in Phase 3 (dispositions carry duration only); this is a Phase 3 scope note,
not a project claim — cost remains a roadmap Stage 2 deliverable.

### 11.2 Deliverable A: 4-5 candidates (the bulk of the labor)

Source: a real, closed, test-covered issue from a small permissively-licensed
Python repo. public/ = pre-fix tree + .issue-contract.md adapted from the
real issue; reference/ = the real fix applied.

Eligibility (merged rule): checker is stdlib-only (HARD — taskcheck runs it
with a fixed 60s timeout); pure-Python vendored deps inside public/ are
allowed; scripted rejection scan for installs, build hooks, native code,
pytest plugins, submodules, LFS, symlinks, networked tests. Prefer
unittest-native sources — most real suites are pytest-based and CANNOT run
here; porting the fix's tests into a stdlib checker is budgeted work
(~45-90 min/candidate). Best-fit sources (audit): CPython stdlib single-module
extractions (Lib/x.py + Lib/test/test_x.py — unittest-native, PSF license,
thousands of test-carrying fixes), tomli, packaging, tabulate, boltons, h11.

Mandatory mechanics (each audit-traced to the tooling):
1. PRIVATE FIX TESTS: tests introduced by the fix never enter public/ or the
   subject workspace. check.py pattern (verbatim): copy argv[1] to a temp
   dir, overlay the private test files there (they live in the task dir,
   e.g. tasks/<id>/private/, auto-hashed into the manifest), run with
   PYTHONDONTWRITEBYTECODE=1 and cwd=temp dir, never write into argv[1] or
   the task dir, one JSON last line, total runtime under 60s. "Private"
   means not-in-workspace, not unreadable — the subject has no pointer to it.
2. INSTRUCTION NEUTRALITY: strip every inherited CODER.md, AGENTS.md,
   AGENTS.override.md, .agents/, .codex/ at any depth (codex auto-loads
   AGENTS.md — an inherited one contaminates both arms). Enforced by a
   scripts/import/ preflight (reuse fixtures.FORBIDDEN_SUBJECT_INPUTS);
   output recorded in failure-source.json. Nothing in taskcheck checks this.
3. TREE HYGIENE: no symlinks, no .git/__pycache__/.pyc anywhere in
   public//reference//blind/; package at tree root (python -m works from
   workspace root); no .gitignore that hides source from git add --all.
4. BLIND SOLVE, required per candidate but ASYMMETRIC BY DESIGN: blindsolve
   may use a stronger/different agent, its 900s timeout, and unlimited
   pre-exposure retries. It proves the task is fairly solvable from public
   text; it is NOT a difficulty filter — the candidates we want are exactly
   those the 300s subject fails, so never discard a candidate because the
   blind solve needed retries. CAP (audit: unlimited retries defeat the
   timebox): at most 3 blindsolve runs per candidate, then swap candidates.
   If fewer than 4 candidates admit within the timebox, record the terminal
   outcome SOURCE_FEASIBILITY_NOT_SHOWN and stop — that too is an answer.
5. PROBE HONESTY: text_absent probes on real tasks are solution-shaped
   (a different-but-correct fix can look like an "omission"). Therefore:
   omission/wrong-failure-mode labels are NOT evidence in Phase 3;
   qualification uses only per-requirement/regression booleans + valid from
   result.json. At least one requirement must be a contracted artifact
   (e.g. a named regression test) with an honest probe. Salience config:
   "enumerated", ≤3 requirements, quotes in .issue-contract.md (the
   pragmatic route; noted openly: that is the high-salience condition —
   real-code difficulty, not salience, is what Phase 3 tests).
6. PROVENANCE: failure-source.json is SOURCE-ONLY and BYTE-FINAL before
   admit (the manifest hashes it; any later edit bricks verify, and after
   first exposure there is no re-admission; every task byte is final before
   the null batch). Exact schema, validated by the preflight script:
   {source_url, issue_url, base_sha, fix_sha, solution_patch_sha256,
   fix_test_patch_sha256, checker_command, spdx_id, license_paths+hashes,
   removed_instruction_paths, extraction_note}. Treatment provenance NEVER
   goes in this file (audit: that mutation would break the frozen hashes) —
   it lives in controls/phase3/<task-id>.provenance.json, created at MD
   authoring time and hash-bound inside the paired REQUEST.
7. YIELD LEDGER (restored): count repos screened → issues considered →
   candidates reconstructed → admitted → showing headroom. The counts are
   recorded; extrapolating them to a population rate is forbidden. This is
   the number the roadmap's Stage 1 task-source decision needs.

AUTHORIZED ONE-LINE CODE FIX (audit finding, severity-critical): the subject
env does not suppress bytecode and run_batch copies the final workspace with
only ".git" ignored, so leftover __pycache__ makes taskcheck's checker run
raise, the attempt scores invalid (not infrastructure — no replacement), and
one dirty attempt voids a 1-task paired batch. Fix: run_batch.py workspace
copy adds "__pycache__" and "*.pyc" to ignore_patterns. This is the sole
Phase 3 edit to Phase 2 code; tests updated accordingly; everything else in
taskcheck/run_batch/compare stays untouched.

### 11.3 Treatment MD (one, post-selection, blinded author)

After selection (§11.4), a FRESH-CONTEXT agent (new instance; its prompt
contains only a mechanically generated packet) authors ONE treatment MD for
the selected task at controls/phase3/<task-id>.md. The packet, built by a
scripts/import/ script, contains the pre-fix upstream tree and its ordinary
public docs and NOTHING else — never .issue-contract.md, requirements.json,
check.py, reference/, blind/, the issue/PR/fix, private tests, or any scout
evidence. (Audit: same-agent authoring cannot be trusted to forget.) Content: stable public repository knowledge
(commands, architecture, source-of-truth locations, generated-file policy);
MUST NOT name the task/issue/PR/commit, hidden test, intended patch, or a
task-specific file/symbol; every concrete fact carries a public path+quote.
Exactly one version, ever: no outcome-driven edit, replacement, or retry.
Record in controls/phase3/<id>.provenance.json: MD sha256, its public
supports, and the author's prediction stated as a task-level BEHAVIOR in
plain words (the author cannot know requirement ids — audit-caught
contradiction); a separate custodian step maps that behavior to a
requirement id afterward and records the mapping. All of it REPORTED in the
final write-up, never a pass/fail gate. Manual cross-check before the paired
REQUEST (no tool does this): provenance md_sha256 ==
sha256(controls/phase3/<id>.md) == the REQUEST's arm-B sha256.

### 11.4 Null scout — first STOP

One batch: every admitted candidate × 3 null attempts (12-15 nominal calls;
existing replacement policy). Runner: existing contract; --timeout-seconds
may exceed 300 for a real suite ONLY if set identically for all Phase 3
batches and recorded in the REQUEST. Write REQUEST.json, STOP for
APPROVED.json.

PROVISIONAL HEADROOM for a candidate = at least one TASK-CAUSAL
nonresolution: result valid, every regression passes, a public checker
requirement fails. Infra failures, checker defects, hidden requirements, or
contamination never count. Qualification reads attempt result.json booleans
plus disposition.json — raw trajectories/final messages/diffs may NOT be
inspected before selection. Selection: most qualifying nonresolutions,
tiebreak lexicographically smallest task id. Scout attempts are calibration
evidence and are never reused as the paired bare arm.

### 11.5 Decision gate (binding)

PHASE 3 TERMINATES after the scout plus at most one paired probe, with a
terminal outcome recorded in handoffs/PROCESS_FINDINGS. The table's
follow-ons are STANDING PERMISSIONS, not automatic continuations: each
starts only on Wade's explicit go-word, uses this identical frozen recipe,
requires no new plan document, and every live batch still requires its own
REQUEST/APPROVED.

| Scout outcome | Standing permission (Wade-triggered, no new document) |
|---|---|
| ≥2 tasks with task-causal nonresolutions | HEADROOM. (a) record yield; (b) run the §11.6 paired probe; (c) reconstruct a second cohort of 6-10 tasks from DIFFERENT repos under this identical frozen recipe, same two-stop pattern; (d) when ≥8 band tasks exist, queue the §10.6.5b contrast under its own preconditions. NOT authorized: pack/leaderboard/site work, generalized mining, population claims. |
| Exactly 1 | Run the §11.6 probe on it; reconstruct 4-6 more candidates from different repos (one more day max) before any further decision. |
| 0 | Record NO_HEADROOM_OBSERVED_IN_THIS_COHORT. The cost+regression pivot becomes Wade's decision, informed by this record — no work is pre-authorized (audit: cost measurement needs its own scoping). No further synthetic cohorts of any design. NOT authorized: the claim that headroom is dead for the model — 4-5 tasks is weak evidence. |

### 11.6 Paired probe (conditional on headroom) — second STOP

One task, fresh attempts only: 3 bare + 3 MD, alternating order (automatic).
REQUEST arm order is load-bearing: --arm bare controls/coder/null-m2.md
--arm md controls/phase3/<id>.md, in that order, so compare records
delta = s_MD − s_bare. REQUEST binds task manifest, both arm hashes, MD
filename, runner, order seed, spend cap (6 nominal, 8 max). STOP for
APPROVED.json.

Run `run_batch verify` after EVERY batch (both stops); if verification
fails, the terminal outcome is EVIDENCE_INVALID and no arm comparison is
made. Pinned in the REQUEST: bare arm = controls/coder/null-m2.md (zero
bytes, sha recorded), model gpt-5.6-sol, effort high, exactly 3 usable
attempts per arm.

PRELIMINARY_LOCAL_SIGNAL iff: all 6 usable attempts valid, all regressions
pass, ≥1 task-causal nonresolution in the FRESH bare arm, and
s_MD > s_bare. This label is deliberately weak — with 3 attempts per arm,
s_MD > s_bare occurs by chance ~34% of the time even for identical arms
(audit-verified); it is a mechanism hint, never evidence of benefit.
Otherwise HEADROOM_NOT_REPLICATED (bare arm ceilinged) or
MD_SENSITIVITY_NOT_SHOWN (headroom recurred, MD didn't move it). The
predicted-behavior outcome is reported alongside. compare's formal verdict
stays INCONCLUSIVE (or INVALID if anything was excluded — report why).
Forbidden in every outcome: a second MD, task substitution, selective
retry, arm reuse, any general claim.

### 11.7 Acceptance and boundaries

1. Every candidate passes taskcheck admit + verify with fresh blind and
   complete provenance BEFORE the null REQUEST; the eligibility, hygiene,
   and instruction-neutrality scans are scripted and their outputs recorded.
2. The only Phase 2 code change is the §11.2 authorized ignore_patterns fix
   (plus its test); all suites green before the first REQUEST.
3. Live subject calls occur only inside the two approved REQUESTs.
4. Yield ledger and the terminal outcome label are written into
   handoffs/PROCESS_FINDINGS (appended, dated) — findings survive sessions.
5. Tooling extraction deferred to Stage 1 release prep or a second consumer.

## 12. OPERATIONAL-KNOWLEDGE PILOT (same-day; the mechanism-correct test)

Status: Pilot ACTIVE as of 2026-08-22.
Branch: off phase3. Timebox: REQUEST queued within ~2.5 hours of activation;
ONE live batch (6 nominal calls, 8 max); ONE approval stop. One audit round
maximum before build, and the audit report is SAVED to handoffs/ (Phase 3
lesson: audits that live only in chat are unverifiable). No other documents.

### 12.1 Why (binding context)

CONFLICT RESOLUTION (audit): §12 supersedes §11's "no further synthetic
cohorts" for this single fictional task, and CLOSES §11's historical-issue
lane (its standing permissions lapse). Phase 3 is hereby framed as
motivating hypothesis, not established causal fact: it showed four
real-origin micro-bug ceilings under bare scouting; it never tested an MD.

Phase 3's construct error: it measured coding skill, which MDs do not
improve. MDs supply OPERATIONAL KNOWLEDGE — commands, source-of-truth
locations, conventions (see the advisory research landscape doc). This pilot
tests that mechanism directly, at tripwire fidelity. The repo is FICTIONAL,
built for this pilot — contamination-proof by construction.

### 12.2 Deliverable A: one friction repo + one task (agent labor, ~90 min)

One fictional Python repo: stdlib-only, ~10-15 files, multi-directory.
Mandatory friction, both instances:
1. NONSTANDARD TEST COMMAND: the correct verification runs via a runner
   script (or equivalent) documented inside the repo; the obvious
   `python -m unittest` discovers only a DECOY suite that passes on the
   pristine tree. A solver that verifies with the obvious command believes
   it is done.
2. GENERATED FILE: one file is generated from a source-of-truth elsewhere in
   the repo; editing the output directly (not the source) is a scored
   regression (the checker regenerates and compares).

One task: a small feature/fix whose correct completion REQUIRES both facts
(the real suite exercises it; the change touches the generated artifact).

BINDING MECHANISM GATE (the constraint Phase 3 lost — now an admission rule;
admission stays 100% mechanical per AGENTS.md — the semantic review of this
section happened in the completed pre-build audit round, not at admission):
- Every scored requirement is publicly stated (fairness rules unchanged).
- TWO decoy solutions, one per fact, both private in the task dir, both
  machine-REJECTED at admission alongside pristine/reference/blind (audit:
  one bundled decoy cannot isolate which fact failed):
  DECOY-1 (wrong layer): correct behavior change made by editing the
  generated file directly — checker rejects via regeneration mismatch.
  DECOY-2 (wrong verification): a solve that leaves the decoy suite passing
  while the real behavior is absent — checker rejects via the real suite.
- tasks/<id>/mechanism.json, structure machine-validated: {facts: [{fact,
  public_support_path, required_md_substrings: [...],
  predicted_bare_behavior, affected_requirement}], nondisclosure_note}.
- TREATMENT FIDELITY (audit: an unfaithful MD voids a null result): before
  the REQUEST is queued, a script verifies the authored CODER.md contains
  each fact's required_md_substrings. If absent: record
  TREATMENT_UNFAITHFUL and permit exactly one fresh blinded re-author
  (pre-exposure repair, principle §1.3); a second failure ends the pilot.
- Fictional names/content only; no real project's code or identity.
- Budget grants for this section: taskcheck.py cap 620 -> 700 (decoy
  rejection + structure checks); outcome-coding helper (§12.5) <=150 lines
  under scripts/import/, additional to the Phase 3 helper cap.

Blind solve: required as usual (fresh agent, public/ only, generous limits) —
it proves the task is fairly solvable by a solver who READS EVERYTHING. The
300s subject may not. That asymmetry is the experiment.

### 12.3 Deliverable B: the blinded MD (~20 min)

A fresh-context agent that sees ONLY the repo tree (never the task contract,
checker, reference, decoy, or mechanism.json) writes CODER.md documenting
the repo's commands, source-of-truth locations, and conventions — exactly
what a real maintainer's MD contains. One version, hash-pinned in the
REQUEST, no outcome-driven edits. Stored controls/pilot/<task-id>.md with a
provenance file recording the author's input hash.

### 12.4 Deliverable C: the batch — the ONE approval stop

One two-arm batch: --arm bare controls/coder/null-m2.md --arm md
controls/pilot/<task-id>.md (that order; delta = s_MD − s_bare), 3 usable
attempts per arm, alternating, existing runner contract. Write REQUEST.json,
STOP for Wade's APPROVED.json. After the run: run_batch verify (mandatory);
report per-arm resolution, per-attempt durations, and token usage from the
captured events (descriptive).

### 12.5 Readings (tripwire, not verdict — stated caveat: a 3-v-3 win occurs
by chance ~34% even for identical arms)

Arm execution order: one of the two balanced orders, selected by the
REQUEST's recorded task_order_seed, committed before launch (audit).

MECHANICAL OUTCOME PREDICATES (audit: no subjective labels), computed by a
<=150-line script from existing evidence only — checker booleans, the
captured command list in each attempt's events, capture diff, durations:
- ran_real(attempt): the real runner invocation appears in captured commands.
- wrong_layer(attempt): capture diff modifies the generated file with no
  matching source-of-truth change.
- stumble(attempt): NOT resolved, OR NOT ran_real, OR wrong_layer.
Labels, evaluated in this precedence:
1. EVIDENCE_INVALID: any attempt invalid or batch verify fails.
2. MECHANISM_SIGNAL: >=2 of 3 bare attempts stumble AND >=2 of 3 MD attempts
   are resolved AND ran_real AND NOT wrong_layer.
3. MD_WORSE: s_MD < s_bare (report prominently; first live harm observation).
4. MECHANISM_NOT_SHOWN_IN_PILOT: everything else (including both arms
   resolving with ran_real — the model self-discovers friction in 300s).
On MECHANISM_SIGNAL: standing permission (Wade-triggered, no new document)
to scale to the repository challenge — one repo, 3-5 sealed tasks, one MD,
prospective sizing. On MECHANISM_NOT_SHOWN: the completion thesis is in
genuine doubt on this task; only defensible negative claim is "mechanism
not shown on this task"; remaining honest products: harm + cost; Wade
decides. Durations/tokens reported descriptively in all cases.

All outcomes append one dated entry to handoffs/PROCESS_FINDINGS. Forbidden
in every outcome: second MD, task substitution, selective retry, general
claims. Cost numbers are descriptive, not a measured product claim.

AUDIT CLOSURE: the §12 one-audit-round requirement is SATISFIED by the
2026-08-22 three-auditor NO-GO round; its findings are incorporated above
(two decoys, mechanical-only admission, treatment-fidelity check, mechanical
outcome predicates, §11 conflict resolution, budget grants, randomized
balanced order). Its report must be committed under handoffs/ before build.
No further document audits precede implementation.

### 12.6 Acceptance (binding on the implementing session)

1. Task admitted via taskcheck INCLUDING the decoy-solution rejection check;
   mechanism.json present and structurally valid; blind solve recorded.
2. MD authored blind with provenance; REQUEST queued within the timebox.
3. No live calls outside the approved batch; ≤2 agents; all suites green;
   no new documents; helpers within existing scripts/import/ caps.
4. The pre-build audit round's report is committed under handoffs/.

## 13. SEALED EXECUTION + THE ISOLATED RERUN (the missing hills layer)

Status: PROPOSED (flips to "ACTIVE as of <date>" on Wade's word). Branch:
off pilot. One audit round: the OUTSIDE REVIEWER who found the leak reviews
this section and the probe list; their report is committed under handoffs/
before build. One live batch (12 nominal calls, 16 max), one approval stop.

### 13.1 Why (binding context)

Phase 3's ceilings are invalidated: traces show the subject reading the
tasks' published fixes from this machine (installed Python stdlib and
frameworks). The existing sandbox seals writes, network, and environment —
those walls have a zero-failure record — but READS of the host were never
sealed or verified. This section adds the missing layer and reruns the same
four real tasks under it. This is CALIBRATION ONLY: it measures whether the
model can fail real tasks when it cannot look up answers. It says nothing
about MDs.

### 13.2 Sealed execution requirement

Every subject attempt and every blind solve runs in a CONTAINER whose
filesystem contains ONLY:
- the task workspace (bind-mounted, so host-side evidence capture is
  unchanged — captured fields must be identical to current runs),
- one pinned Python interpreter (per-task pin, see 13.3),
- the agent runtime and its read-only auth (mounted outside the workspace;
  status-quo risk, recorded).
No host filesystem, no other interpreters, no site-packages beyond stdlib,
no network (unchanged). The container image digest is recorded in every
attempt's evidence. Implementation choice (Docker or equivalent) is the
implementer's; the PROBES define correctness, not the technology.

### 13.3 The stdlib trap (critical, audit this line hardest)

Isolation from the host does NOT remove answers that ship inside the
interpreter itself: any Python >=3.11 contains tomllib (tomli WITH the fix),
and any recent Python contains the fixed enum.py and doctest.py. Therefore:
- Each task's failure-source.json gains two fields: answer_bearing_modules
  (e.g. ["tomllib", "enum"]) and fix_signature_strings (2-3 distinctive
  literals from the real fix's diff).
- Per task, the container's interpreter is PINNED to a version whose stdlib
  PREDATES the fix (recorded per task). A task with no such available
  interpreter is excluded and recorded as such.

### 13.4 The contamination probe (mechanical; the build gate)

A scripted probe runs INSIDE the container before each batch and its full
output is committed as batch evidence. It must demonstrate, with failing
output, that:
1. The literal Phase 3 exploit fails: for each answer_bearing_module,
   `inspect.getsource(<module>)` either fails or the retrieved source
   contains NONE of the task's fix_signature_strings.
2. Host paths are unreachable: /Library/Frameworks, /Users, and this
   repository's absolute path all fail to list/read.
3. No network: a socket attempt fails.
4. No secondary interpreters or site-packages exist on PATH.
THE BUILD DOES NOT EXIST UNTIL THE PROBE FAILS THE REAL ATTACK: acceptance
requires running the probe against the OLD (host) runner configuration and
showing it DETECTS the leak there (probe red on host, green in container).
The probe is the permanent regression test for this leak class.

### 13.5 The rerun batch — one approval stop

The same four Phase 3 tasks, unmodified bytes (already exposed; this is a
new batch under a corrected runner, recorded as such — task content
unchanged, so no re-admission is required; the batch REQUEST records the
container image digests). 3 null attempts per task, 12 nominal calls,
existing REQUEST/APPROVED mechanism. Blind solves are NOT rerun (tasks
already admitted; their contamination caveat stands recorded).

Reporting: the batch summary now includes per-attempt duration AND token
totals (input/cached/output/reasoning — already captured in evidence, now
surfaced; <=40-line addition to the reporting path).

### 13.6 Readings (mechanical)

| Result | Label | Meaning |
|---|---|---|
| Probe fails in container | BUILD_REJECTED | No calls happen. Fix container. |
| Any task drops below 3/3 | HEADROOM_CONFIRMED_ISOLATED | The band exists; Phase 3's ceilings were the leak. Standing permission (Wade-triggered): scale real-issue sourcing under sealed execution; the challenge-pack design becomes buildable. |
| All tasks still 3/3, probes green | MEMORY_SUSPECTED | The model knows these public fixes from training. Sourcing must move to post-cutoff issues or planted bugs in real codebases — Wade decides which. |
| Evidence fails verification | EVIDENCE_INVALID | The 12 calls answered nothing; fix and re-request. |

All outcomes append a dated entry to handoffs/PROCESS_FINDINGS. Forbidden:
task edits, selective retries, any MD claim, any general capability claim.

### 13.7 Budgets and acceptance

1. Container wrapper: scripts/contain/ <=250 lines total. run_batch.py may
   grow <=60 lines (new cap 610) for the container execution path + token
   reporting. taskcheck.py untouched. Probe script <=150 lines, lives in
   scripts/contain/, runs identically on host (red) and container (green).
2. Acceptance: probe red-on-host/green-in-container outputs committed;
   image digests recorded; all suites green; evidence fields identical to
   prior batches; reviewer report in handoffs/ before build; REQUEST queued
   then STOP for Wade.
3. No other machinery, documents, or experiments. §12's standing
   permissions remain suspended until this section's result is recorded.
