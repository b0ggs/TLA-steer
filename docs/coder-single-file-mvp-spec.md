# Codex Cloud Handoff: Single-File Agent Instruction Evaluator MVP

**Working project name:** MD Eval  
**Suggested repository name:** `mds-eval`  
**Date:** 2026-07-29  
**Status:** Implementation authority for the MVP  
**First locked target:** `CODER.md`  
**First locked subject runtime:** Codex CLI, single agent  

## 1. What Codex Cloud is being asked to build

Build a small, local, harness-independent evaluation system that compares two versions of one agent instruction file against the same coding tasks.

The first experiment compares:

1. The current `CODER.md` champion.
2. One manually written candidate that adds assumption management, simplicity, surgical-editing, and verification guidance.

The system must answer:

> Under one fixed Codex runtime, does the candidate `CODER.md` improve correctness, assumption handling, simplicity, scope discipline, and verification without causing unnecessary clarification, underbuilding, or material cost growth?

This is an evaluator MVP, not an OpenClaw module and not an autonomous prompt optimizer.

## 2. Locked decisions

These decisions are not open for redesign during implementation:

- The first target is one file: `CODER.md`.
- The first subject runner is `codex exec`.
- Every subject run uses one agent. Subagents are disabled.
- The initial model is `gpt-5.6-sol`.
- The initial reasoning effort is `high`.
- Champion and candidate use the same model, reasoning effort, Codex version, permissions, task prompt, fixture, timeout, and run count.
- The evaluator runs outside OpenClaw.
- Mechanical checks outrank LLM judgment.
- Raw run artifacts are retained.
- The qualitative judge is blinded to variant identity and sees candidates in randomized order.
- No candidate may edit the evaluator, tasks, checks, rubrics, promotion policy, or run history.
- The first candidate is written manually and frozen before its evaluation.
- No autonomous candidate generation is part of this MVP.
- No role bundles or topology comparison are part of this MVP.
- No web UI, database server, queue, plugin framework, or hosted service is part of this MVP.
- A single aggregate score may be reported for convenience, but it must never hide per-case hard failures or cause promotion by itself.
- Valid comparison verdicts are `PROMOTE`, `REJECT`, `INCONCLUSIVE`, and `INVALID_COMPARISON`.

## 3. Source baseline

The champion comes from:

```text
Archive: openclaw-overlay-main.zip
Archive SHA-256:
0555a5cd2bae651a7d17a5289886a363ed5d14d620b80e9e81d3d0f30e06cd4e

Path inside archive:
openclaw-overlay-main/modules/prompt-pack/src/CODER.md

CODER.md SHA-256:
e72791366f3a3c20780a3ece63b0b8c1a0b7862c7c5ffd1d8ea8d3dd6eed92b0
```

The complete canonical contents are included in Appendix A. Create
`targets/coder/champion.md` from those exact bytes and add a test that verifies
the SHA-256 above.

The source file says `GPT-5.5 @ xhigh`. Do not silently rewrite that line in the
champion. Runtime selection belongs to the experiment configuration, not to a
baseline mutation. The report should note this mismatch as baseline metadata.

## 4. Larger roadmap

Build one evaluator whose experimental unit expands over time.

| Stage | Experimental unit | Fixed during comparison | Question |
| --- | --- | --- | --- |
| 1. Single file | One instruction MD | Model, runner, topology, tasks, budgets | Does this wording improve this role? |
| 2. Role bundle | Several cooperating MDs and handoffs | Model, topology, tasks, budgets | Which combination of role instructions works best? |
| 3. Fixed topology | Solo, primary plus checker, specialist pair, or bounded swarm | Model, tasks, success criteria, comparable budgets | Which configured execution pattern works best for each task class? |

### Stage 1 exit gate

- Champion versus identical champion does not create a systematic winner.
- A deliberately bad instruction file reliably loses.
- Run-to-run variance is visible and bounded enough to interpret results.
- A candidate can be evaluated on development and sealed holdout cases.
- The report preserves hard failures, raw evidence, quality, latency, and token use separately.

### Stage 2 direction

The versioned experimental unit becomes a bundle such as:

- `ORCHESTRATOR.md`
- `CODER.md`
- A general code checker
- Shared handoff contracts

Add cross-role cases for delegation, information transfer, duplicated work,
disagreement, and integration. Begin with one-file-at-a-time changes and
ablation tests. Do not implement Stage 2 now.

### Stage 3 direction

Compare only a bounded menu at first:

- Solo agent
- Primary plus general checker
- Specialist primary plus specialist reviewer
- Adversarial swarm plus mediator

Report recommendations by task class, not one universal winning harness. Do not
optimize prompts and topology simultaneously at first. Do not implement Stage 3
now.

## 5. MVP boundaries

### In scope

- A versioned single-file target registry.
- A Codex CLI subject adapter.
- A deterministic fake adapter for tests.
- Clean fixture creation for each run.
- Ten small coding-evaluation cases.
- Champion, candidate, and deliberately bad control variants.
- Raw transcript/event, final-response, diff, check, usage, duration, and environment capture.
- Mechanical scoring.
- A blinded pairwise qualitative judge.
- A/A calibration, bad-control validation, and champion-versus-candidate comparison.
- JSON and Markdown reports.
- Explicit comparison and promotion gates.
- Unit tests and one fake-run end-to-end test.

### Out of scope

- OpenClaw integration or fidelity testing.
- Multi-file instruction bundles.
- Multiple agents or topology selection.
- Autonomous candidate generation or self-editing.
- A general benchmark marketplace.
- Adversarial security isolation for untrusted instruction files.
- A production service, web dashboard, database server, distributed execution,
  or user-account system.
- Automatic PR creation, deployment, or publication.
- Claiming one universally optimal instruction file.

## 6. Important Codex Cloud execution boundary

Codex Cloud should build and test the evaluator. It must not assume that the
credentials for the outer Cloud task are available to a nested `codex exec`
process.

Cloud completion therefore means:

- All source, fixtures, checks, schemas, reports, and documentation are built.
- Unit tests pass.
- A deterministic fake-run experiment passes end to end.
- The exact live Codex command can be constructed and inspected.
- `mdseval doctor` accurately reports whether a live runner is available.

Live completion additionally requires:

- An independently authenticated Codex CLI profile.
- Successful A/A calibration.
- Successful bad-control validation.
- A completed champion-versus-candidate run.

If live authentication is unavailable in Cloud, report
`LIVE_RUNNER_UNAVAILABLE` and still finish the Cloud-complete implementation.
Do not request, print, copy, or commit credentials.

Codex Cloud facts relevant to this design:

- Cloud checks out a repository in an isolated container and runs its setup
  script before the agent phase.
- Cloud secrets are available to setup scripts but removed before the agent
  phase.
- `codex exec` is the supported non-interactive interface and can emit JSONL.
- `AGENTS.md` and configured fallback instruction filenames are loaded at the
  start of a Codex run.

Official references:

- [Cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environment)
- [Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)
- [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

## 7. Operator setup for Codex Cloud

1. Create or select a private GitHub repository named `mds-eval`.
2. Use Python 3.12 or the closest available Python 3 version.
3. Leave agent internet access off. The implementation must use the Python
   standard library only.
4. Use this optional Cloud setup script:

   ```bash
   if [ -f pyproject.toml ]; then
     python -m pip install -e .
   fi
   ```

5. Attach this specification to the Codex Cloud task or commit it as
   `docs/coder-single-file-mvp-spec.md`.
6. Paste the prompt below.

## 8. Exact prompt to paste into Codex Cloud

```text
Implement the attached "Codex Cloud Handoff: Single-File Agent Instruction
Evaluator MVP" as the authority for this task.

This is an implementation task, not another planning task. Read the entire
specification before editing. Build only the Stage 1 single-file MVP. The locked
target is CODER.md and the locked subject adapter is single-agent `codex exec`.

Keep the implementation small and standard-library-only. Do not add a web UI,
database server, autonomous optimizer, OpenClaw integration, role bundles,
topology selection, or generic plugin framework.

First inspect the repository and preserve any existing user work. Then implement
the repository structure, champion/candidate/control files, ten cases, runner,
capture, mechanical scorer, blinded pairwise-judge packet and parser, reports,
CLI, tests, and documentation required by the specification.

Run:

python -m unittest discover -s tests -v
python -m mdseval validate --experiment experiments/coder-v1.json
python -m mdseval demo --experiment experiments/coder-v1.json

The demo must use the deterministic fake adapter and complete without external
credentials or network access.

Check whether a live nested Codex runner is available only through the
non-mutating doctor command defined by the spec. Do not search for, copy, print,
or request credentials. If live authentication is unavailable, record
LIVE_RUNNER_UNAVAILABLE and continue. Do not claim the candidate won without
real live runs.

Review the final diff against the specification. Finish with:

- files created or changed
- exact validation commands and results
- whether LIVE_RUNNER_AVAILABLE or LIVE_RUNNER_UNAVAILABLE
- any unmet acceptance criterion
- the next exact local command for the operator
```

## 9. Required implementation stack

- Python 3.12 compatible.
- Python standard library only at runtime and in tests.
- `argparse` for the CLI.
- `dataclasses` plus explicit JSON validation helpers for configuration models.
- `subprocess` for Git, check scripts, and Codex CLI execution.
- `unittest` for tests.
- JSON and JSONL for machine-readable files.
- Markdown for human reports.
- No PyYAML, Pydantic, Typer, Click, database, task queue, or web framework.

Use `pyproject.toml` only for packaging and the `mdseval` console entry point.

## 10. Required repository tree

```text
mds-eval/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── .gitignore
├── docs/
│   └── coder-single-file-mvp-spec.md
├── src/
│   └── mdseval/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── config.py
│       ├── hashing.py
│       ├── fixtures.py
│       ├── capture.py
│       ├── compare.py
│       ├── promotion.py
│       ├── report.py
│       ├── runner/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── codex_cli.py
│       │   └── fake.py
│       └── scoring/
│           ├── __init__.py
│           ├── mechanical.py
│           └── qualitative.py
├── targets/
│   └── coder/
│       └── champion.md
├── candidates/
│   └── coder/
│       └── karpathy-v1.md
├── controls/
│   └── coder/
│       └── deliberately-bad.md
├── experiments/
│   └── coder-v1.json
├── evals/
│   ├── dev/
│   │   └── <eight case directories>
│   └── holdout/
│       └── <two case directories>
├── schemas/
│   ├── case.schema.json
│   ├── experiment.schema.json
│   └── judge-output.schema.json
├── tests/
│   ├── data/
│   ├── test_capture.py
│   ├── test_cli.py
│   ├── test_compare.py
│   ├── test_config.py
│   ├── test_fake_e2e.py
│   ├── test_fixtures.py
│   ├── test_hashing.py
│   ├── test_mechanical_scoring.py
│   ├── test_promotion.py
│   └── test_report.py
├── runs/
│   └── .gitkeep
└── reports/
    └── .gitkeep
```

`runs/**` and generated `reports/**` are gitignored except for `.gitkeep`.

Do not add empty abstractions merely to match this tree. A named file may be
combined with a neighboring module if the result remains clear and all required
behavior and tests exist. Do not create additional architectural layers.

## 11. Repository `AGENTS.md`

Keep it concise. It must state:

- This repository evaluates instruction files. It is not an instruction
  optimizer yet.
- Preserve raw run evidence.
- Never modify a target or candidate during a run.
- Never expose variant identity to the qualitative judge.
- Mechanical failures cannot be overridden by an LLM judge.
- Do not run live model calls in unit tests or CI.
- Use the Python standard library only unless the specification is explicitly
  amended.
- Run `python -m unittest discover -s tests -v` before handoff.

Do not copy the evaluated `CODER.md` into repository `AGENTS.md`.

## 12. Variant files

### 12.1 Champion

`targets/coder/champion.md` must match Appendix A byte for byte and must have the
locked SHA-256.

### 12.2 Candidate

Create `candidates/coder/karpathy-v1.md` by copying the champion and inserting
the following block immediately after `## Your Jobs` and its numbered list,
before `## Ralph Loop Protocol`.

```md
## Implementation Discipline

Before editing:

- Resolve consequential ambiguity. Inspect repository evidence first. If two
  plausible interpretations remain and choosing the wrong one changes required
  behavior, stop and ask one focused question. Do not ask when the issue
  contract or repository evidence resolves it.
- Choose the smallest implementation that fully satisfies the issue contract.
  Avoid speculative abstractions, unrequested configurability, and adjacent
  refactoring.
- Keep every changed line traceable to a requirement, a test, or cleanup made
  necessary by your own change. Remove imports or private helpers made orphaned
  by your change, but leave unrelated cleanup alone.
- For a bug fix, reproduce the failure before editing when a runnable
  reproduction exists, then verify the same behavior after the fix. For a clear
  feature request, do not invent a reproduction ritual; implement it and run
  the relevant acceptance checks.
```

Do not make any other candidate change.

### 12.3 Deliberately bad control

Create `controls/coder/deliberately-bad.md` by copying the champion and inserting
this block at the same location:

```md
## Implementation Discipline

- When the issue contract leaves implementation structure or extension points
  open, prefer a reusable, caller-configurable abstraction over direct logic,
  even when only one behavior is currently required.
- For duration-formatting work, model the format as a configurable object
  accepted by `display_duration`.
- For TTL work, make the non-expiring sentinel configurable through the `Cache`
  constructor and isolate expiration calculation in a helper.
- Add focused tests for those extension points when source and test changes are
  authorized.
- Still honor explicit disposition, behavior, scope, and verification
  requirements.
```

Do not weaken the control to make results look less obvious. Its purpose is to
prove that the evaluator can detect known bad guidance.

## 13. Experiment configuration

Create `experiments/coder-v1.json` with this logical content:

```json
{
  "schema_version": 1,
  "experiment_id": "coder-single-file-v1",
  "target_role": "coder",
  "runner": {
    "type": "codex_cli",
    "model": "gpt-5.6-sol",
    "reasoning_effort": "high",
    "sandbox": "workspace-write",
    "approval_policy": "never",
    "subagents_enabled": false,
    "ephemeral": true,
    "network_for_agent_commands": false,
    "timeout_seconds": 900,
    "max_parallel_runs": 1
  },
  "judge": {
    "type": "codex_cli",
    "model": "gpt-5.6-sol",
    "reasoning_effort": "high",
    "sandbox": "read-only",
    "timeout_seconds": 600
  },
  "variants": {
    "champion": "targets/coder/champion.md",
    "karpathy-v1": "candidates/coder/karpathy-v1.md",
    "deliberately-bad": "controls/coder/deliberately-bad.md"
  },
  "suites": {
    "smoke": [
      "ambiguity-must-clarify",
      "ambiguity-repo-resolves",
      "scope-ttl-zero",
      "bug-reproduce-mutable-default"
    ],
    "dev": [
      "ambiguity-must-clarify",
      "ambiguity-repo-resolves",
      "simplicity-username-lowercase",
      "scope-ttl-zero",
      "scope-remove-own-orphan",
      "bug-reproduce-mutable-default",
      "feature-json-output",
      "goal-status-422"
    ],
    "holdout": [
      "breadth-layered-settings",
      "goal-real-entrypoint"
    ]
  },
  "run_order_seed": 20260729,
  "default_repeats": 2
}
```

The loader must reject unknown top-level keys, missing required keys, duplicate
case IDs, nonexistent paths, unsupported disposition values, and nonpositive
timeouts or repeat counts.

Every comparison manifest must freeze:

- Experiment file SHA-256.
- Variant file SHA-256.
- Case definition and fixture tree SHA-256.
- Constant wrapper-prompt SHA-256.
- Git commit of the evaluator.
- Codex CLI version.
- Python version.
- OS and architecture.
- Model and reasoning effort.
- Sandbox and approval settings.
- Run-order seed.
- Start and end timestamps.

Refuse to issue a comparison verdict when frozen fields differ between paired
runs. Mark it `INVALID_COMPARISON`; do not silently normalize mismatches.

## 14. Case format

Each case directory contains:

```text
<case-id>/
├── case.json
├── contract.md
├── fixture/
│   └── <tiny repository files>
├── checks/
│   └── check.py
└── rubric.md
```

The subject receives only:

- A fresh copy of `fixture/`.
- The selected variant copied to repository root as `CODER.md`.
- `contract.md` copied to repository root as `.issue-contract.md`.
- The fixed wrapper prompt.

The subject must not receive `case.json`, `checks/`, `rubric.md`, other cases,
other variants, evaluator source, or prior run results.

`case.json` must support:

```json
{
  "schema_version": 1,
  "id": "example-id",
  "suite": "dev",
  "expected_disposition": "IMPLEMENTED",
  "allowed_changes": ["src/example.py", "tests/test_example.py"],
  "forbidden_changes": ["CODER.md", ".issue-contract.md"],
  "required_post_run_checks": [
    ["python", "checks/check.py", "--repo", "{repo}"]
  ],
  "verification_evidence": {
    "pre_edit_failure_required": false,
    "post_edit_check_required": true,
    "command_patterns": ["python -m unittest"]
  },
  "unchanged_regions": [],
  "qualitative_dimensions": [
    "assumption_handling",
    "simplicity",
    "scope_discipline",
    "verification_quality"
  ],
  "limits": {
    "timeout_seconds": 900
  }
}
```

Allowed disposition values:

- `IMPLEMENTED`
- `NEEDS_CLARIFICATION`
- `BLOCKED`

The JSON schemas in `schemas/` are documentation and fixtures for validation.
The runtime validator must remain standard-library code and must not depend on a
JSON Schema package.

## 15. Fixed wrapper prompt

Use the same wrapper for every subject variant and case:

```text
Read CODER.md and .issue-contract.md completely before acting.

Execute only the issue contract in this disposable evaluation repository.
Repository inspection is allowed. Commits, branches, pushes, pull requests,
deployments, and publication artifacts are not authorized. Do not create or
update issue-status, workpad, task-status, packet, checklist, or handoff files.

At the end, the first non-empty line of your final response must be exactly one
of:

IMPLEMENTED
NEEDS_CLARIFICATION
BLOCKED

If CODER.md requires TASK_COMPLETE after successful implementation, place
TASK_COMPLETE later in the response. Briefly state what you changed or the one
specific clarification or blocker. Do not include secrets.
```

Store this wrapper in source as one constant. Hash it into every run manifest.
Do not vary it by variant.

## 16. The ten required cases

All fixtures must be tiny, deterministic, offline, and standard-library-only.
Each repository must initialize and run in under five seconds excluding the
agent.

### 16.1 `ambiguity-must-clarify` - development

- Python module: `src/duration.py`.
- Current behavior displays `65 min`.
- Contract: replace displays over one hour with the newly approved compact
  format. It says stakeholders narrowed the choice to `1h 05m` or `1:05`, but
  does not say which was approved.
- No repository file resolves the choice.
- Expected disposition: `NEEDS_CLARIFICATION`.
- Hard requirements: no source, test, config, documentation, or untracked file
  change; final response asks one focused format question.
- Purpose: consequential ambiguity should not be guessed.

### 16.2 `ambiguity-repo-resolves` - development

- Same small duration module.
- Add `docs/ADR-004-duration-format.md`, which authoritatively selects `1h 05m`
  and specifies examples.
- Contract uses the same shorthand "approved compact format" but tells the agent
  to use repository authority.
- Expected disposition: `IMPLEMENTED`.
- Hidden checks: values below 60 minutes remain unchanged, 60 follows the ADR,
  65 becomes `1h 05m`, and 125 becomes `2h 05m`.
- Purpose: the candidate must inspect context instead of reflexively asking.

### 16.3 `simplicity-username-lowercase` - development

- Python module with `normalize_username(value)` currently returning
  `value.strip()`.
- Contract: normalized usernames must also be lowercase.
- The file contains an existing generic policy class that is unrelated and
  tempting to extend.
- Expected disposition: `IMPLEMENTED`.
- Hidden checks: surrounding whitespace and ASCII case combinations.
- Allowed changes: implementation file and its focused test file.
- Qualitative focus: smallest sufficient change, no new configuration or
  abstraction.

### 16.4 `breadth-layered-settings` - holdout

- Python `src/settings.py` currently loads two settings from an optional JSON
  file.
- Contract explicitly requires:
  - defaults;
  - optional JSON-file overrides;
  - `APP_TIMEOUT_SECONDS` and `APP_DEBUG` environment overrides;
  - precedence of defaults, then file, then environment;
  - integer and boolean conversion;
  - clear errors for invalid values and unknown JSON keys.
- Expected disposition: `IMPLEMENTED`.
- Hidden checks cover every required layer, precedence, missing file, false
  boolean values, invalid integer, and unknown keys.
- Purpose: simplicity guidance must not cause underbuilding.

### 16.5 `scope-ttl-zero` - development

- Python `src/cache.py`.
- Bug: TTL `0` expires immediately; contract states `0` means no expiration.
- The same file contains an ugly but working legacy key-normalization block and
  unrelated TODO comments.
- Expected disposition: `IMPLEMENTED`.
- Hidden checks cover TTL `0`, positive TTL, and expired entries.
- Add an `unchanged_regions` assertion for the unrelated legacy block.
- Purpose: fix the bug without drive-by cleanup.

### 16.6 `scope-remove-own-orphan` - development

- Python `src/ids.py` accepts a legacy prefix through private helper
  `_strip_legacy_prefix` and an import used only by that helper.
- Contract removes legacy-prefix acceptance and points to the existing canonical
  parser.
- Expected disposition: `IMPLEMENTED`.
- Hidden checks require canonical IDs to work and legacy IDs to fail.
- Static checks require removal of the now-unused private helper and import but
  preservation of unrelated `format_id`.
- Purpose: surgical scope still includes cleanup made necessary by the change.

### 16.7 `bug-reproduce-mutable-default` - development

- Python tag-merging function has a mutable-default leak.
- A focused visible regression test is present and initially fails.
- Contract asks to fix the leak.
- Expected disposition: `IMPLEMENTED`.
- Event-sequence requirement: a command running the focused failing test occurs
  before the first source-file edit, and a relevant passing test command occurs
  after the edit.
- Hidden checks repeat calls in different orders.
- Purpose: verify real failure reproduction and post-fix proof.

### 16.8 `feature-json-output` - development

- Tiny Python CLI with text output.
- Contract fully specifies a new `--json` flag, exact JSON keys, exit behavior,
  and preservation of default text output.
- No preexisting failing regression test is supplied.
- Expected disposition: `IMPLEMENTED`.
- A pre-edit failing test is not required. A post-edit CLI check is required.
- Purpose: do not turn a clear feature into unnecessary clarification or bug
  reproduction ceremony.

### 16.9 `goal-real-entrypoint` - holdout

- A package function and its unit tests already pass.
- The actual executable `bin/sample-export` calls a stale function name.
- Contract says the real command `bin/sample-export --format json` must work.
- Expected disposition: `IMPLEMENTED`.
- Hidden check invokes the executable as a subprocess and validates stdout and
  exit code.
- Unit tests alone are insufficient.
- Purpose: detect "tests pass but requested behavior remains broken."

### 16.10 `goal-status-422` - development

- Tiny validation-error status mapping currently returns `400`.
- Contract clearly requires `422` while preserving all other mappings.
- Expected disposition: `IMPLEMENTED`.
- Allowed changes: mapping source and focused test only.
- Hidden checks cover the changed and unchanged statuses.
- No docs, changelog, new config, abstraction, or status artifact is needed.
- Purpose: complete a straightforward task without extra output.

## 17. Fixture preparation algorithm

For every subject run:

1. Create a unique temporary directory.
2. Copy only the selected case's `fixture/` contents.
3. Copy the selected variant to root as `CODER.md`.
4. Copy the case contract to root as `.issue-contract.md`.
5. Verify that no `AGENTS.md`, `AGENTS.override.md`, `.codex/`, `.agents/`,
   evaluator check, or other variant exists in the copied repository.
6. Initialize Git.
7. Configure a disposable local Git identity.
8. Add all initial files and create one baseline commit.
9. Record the baseline commit SHA and fixture tree hash.
10. Run the subject.
11. Record final `HEAD`, status, tracked diff against the baseline commit,
    untracked paths, and bounded untracked-file contents.
12. Run hidden checks only after the subject process exits.
13. Write run artifacts.
14. Delete the temporary subject repository only after all required artifacts
    have been copied into the run directory.

If the subject commits despite the contract, the comparison still captures its
changes by diffing the complete final tree against the recorded baseline commit.
Also record `unauthorized_commit: true` as a mechanical failure.

Path handling must reject absolute paths, `..`, symlink escapes, and any
resolved path outside the case or temporary run root.

## 18. Codex subject adapter

### 18.1 Required preflight

`mdseval doctor --runner codex` must check:

- `codex` exists.
- `codex --version` succeeds.
- Git exists.
- The configured isolated Codex home exists.
- The isolated Codex home does not contain `AGENTS.md` or
  `AGENTS.override.md`.
- The model and reasoning settings are present in the experiment.
- The exact command can be constructed.

By default, doctor must not make a model call. Add `--live-smoke` for an
explicit, minimal authenticated call in a disposable Git repository.

The live runner uses an operator-provided `MDSEVAL_CODEX_HOME`. The evaluator
must never copy authentication from another profile. Recommended one-time local
setup:

```bash
mkdir -p "$HOME/.codex-mdseval"
CODEX_HOME="$HOME/.codex-mdseval" codex login
export MDSEVAL_CODEX_HOME="$HOME/.codex-mdseval"
```

The runner sets `CODEX_HOME` to `MDSEVAL_CODEX_HOME` only for the child process.
It must not print authentication files or environment-variable values.

API-key support may be documented as an advanced alternative, but is not
required for the MVP. Never store a key in an experiment file, run artifact,
fixture, command log, or report.

### 18.2 Required command semantics

Construct the equivalent of:

```bash
codex exec \
  --ephemeral \
  --json \
  --sandbox workspace-write \
  --ask-for-approval never \
  --ignore-user-config \
  --ignore-rules \
  --model gpt-5.6-sol \
  --config 'model_reasoning_effort="high"' \
  --config 'project_doc_fallback_filenames=["CODER.md"]' \
  --config 'project_doc_max_bytes=65536' \
  --config 'agents.enabled=false' \
  --config 'sandbox_workspace_write.network_access=false' \
  --cd <subject-repository> \
  --output-last-message <run-directory>/final.txt \
  -
```

Pass the fixed wrapper prompt on stdin.

Implementation requirements:

- Use an argument array, never `shell=True`.
- Set the working directory explicitly.
- Capture stdout as `events.jsonl`.
- Capture stderr separately as `stderr.txt`.
- Enforce the case timeout.
- On timeout, terminate the process, record partial output, and mark the run
  failed.
- Record the process exit code.
- Reject malformed JSONL but preserve the raw file.
- Parse token usage from `turn.completed` when present.
- Do not silently retry a failed model run. A later experiment-level repeat is
  a new recorded run.
- Disable subagents through configuration.
- Start a fresh ephemeral thread for every case and variant.
- Do not resume conversations across cases or variants.
- Do not use `--dangerously-bypass-approvals-and-sandbox`.
- Do not use `--skip-git-repo-check`.

If the installed CLI rejects a required flag or configuration key, doctor must
return a specific incompatibility error. Do not silently drop isolation or
comparability settings.

### 18.3 Instruction loading

The subject repository must contain `CODER.md` but no `AGENTS.md`. Configure
`CODER.md` as a project instruction fallback filename for the run.

Add a command-construction test that proves:

- The selected variant is copied as `CODER.md`.
- `project_doc_fallback_filenames` contains only `CODER.md`.
- `--ignore-user-config` and `--ignore-rules` are present.
- Subagents are disabled.
- Model and reasoning effort are explicit.
- The two variant commands differ only in the variant hash and resulting copied
  bytes, not in runtime settings.

## 19. Isolation claim

This MVP evaluates trusted, manually written candidate instructions. It is not
a security boundary for hostile instruction files.

Still enforce these practical protections:

- The subject repository contains only the fixture, selected instruction file,
  and issue contract.
- Hidden checks run only after the subject exits.
- Paths to checks, rubrics, other variants, and prior results never appear in
  the subject prompt.
- Agent-command network access is off.
- Every run is a fresh temporary Git repository.
- The subject cannot mutate the source target, evaluator, or recorded results
  through evaluator-provided paths.

Before autonomous candidate generation is added in a future stage, hidden
holdouts and evaluator code must move behind a stronger process or container
boundary. Document this limitation clearly. Do not market the MVP as secure
against prompt injection or deliberate test discovery.

## 20. Raw run artifact contract

Use:

```text
runs/<experiment-run-id>/
├── experiment-manifest.json
├── variants/
│   └── <variant-id>/
│       └── <case-id>/
│           └── <replicate-number>/
│               ├── manifest.json
│               ├── events.jsonl
│               ├── stderr.txt
│               ├── final.txt
│               ├── git-status.txt
│               ├── diff.patch
│               ├── untracked.json
│               ├── commands.json
│               ├── checks.json
│               ├── mechanical-score.json
│               └── run-summary.json
├── comparisons/
│   └── <case-id>-<replicate-number>.json
├── report.json
└── report.md
```

Every artifact is append-only within one completed experiment. Refuse to reuse a
nonempty run directory. Interrupted runs remain present with
`status: "INTERRUPTED"` or `status: "TIMEOUT"`.

Do not redact ordinary code or commands. Redact environment-variable values and
any string matching an explicitly configured secret-value list before writing
logs. Never include environment dumps in judge packets.

Record `input_tokens`, `cached_input_tokens`, `output_tokens`, and
`reasoning_output_tokens` separately when the event stream supplies them.
Define reported `total_tokens` as `input_tokens + output_tokens`; do not add
`cached_input_tokens` a second time because it is a subset of input usage.

## 21. Mechanical scoring

Mechanical scoring happens before qualitative judgment.

### 21.1 Hard-failure fields

Record each separately:

- `runner_completed`
- `runner_exit_zero`
- `valid_event_stream`
- `valid_disposition`
- `expected_disposition`
- `hidden_behavior_passed`
- `allowed_paths_only`
- `forbidden_paths_untouched`
- `required_unchanged_regions_preserved`
- `no_unauthorized_commit`
- `required_pre_edit_evidence`
- `required_post_edit_evidence`
- `no_unrequested_artifacts`

Do not let one passing field overwrite another failure.

### 21.2 Convenience mechanical score

Also calculate a 0 to 100 score:

| Dimension | Points |
| --- | ---: |
| Hidden requested behavior | 40 |
| Correct `IMPLEMENTED` versus `NEEDS_CLARIFICATION` disposition | 20 |
| Allowed and forbidden scope | 15 |
| Required pre-edit and post-edit verification evidence | 15 |
| No unrequested artifacts or unauthorized commits | 10 |

The score is diagnostic. A hidden-behavior, disposition, forbidden-path, or
required-verification failure is a hard failure regardless of total score.

### 21.3 Verification sequence

Parse command and file-change events in order. For
`bug-reproduce-mutable-default`, require:

1. A relevant test command before the first source file-change event.
2. That command indicates the supplied regression fails.
3. A relevant test command after the change.
4. The evaluator's hidden post-run check passes.

Do not require pre-edit failure reproduction for the clear feature case.

### 21.4 Scope and artifacts

Changed paths include:

- Tracked working-tree changes.
- Staged changes.
- Commits after the baseline commit.
- Untracked files.

Case-generated caches such as `__pycache__` may be excluded only through one
central explicit ignore list. Do not ignore Markdown, JSON, shell, source,
config, or test files generically.

## 22. Blinded qualitative comparison

Mechanical results decide correctness and hard gates. The judge assesses only
qualities not fully captured mechanically:

- Assumption handling.
- Simplicity proportional to the contract.
- Scope discipline.
- Verification quality.

For each paired case and replicate:

1. Use the configured seed to randomize which variant becomes `Response A` or
   `Response B`.
2. Create a judge packet containing:
   - case contract;
   - relevant original fixture files;
   - each response's final answer;
   - each response's diff;
   - summarized command sequence;
   - mechanical check outcomes;
   - token and duration metadata.
3. Do not include:
   - variant IDs or filenames;
   - target instruction contents;
   - directory paths containing variant names;
   - prior aggregate scores;
   - candidate rationale;
   - promotion status.
4. Ask for structured output conforming to `schemas/judge-output.schema.json`.
5. Restore the randomized labels to internal variant IDs only after validation.

Run the judge in a separate fresh temporary Git repository containing only the
blinded packet and output schema. Use `--ephemeral`, `--ignore-user-config`,
`--ignore-rules`, `--sandbox read-only`, `--ask-for-approval never`,
`project_doc_fallback_filenames=[]`, and `agents.enabled=false`. Do not copy
`CODER.md` or any repository `AGENTS.md` into the judge repository.

Required judge output:

```json
{
  "schema_version": 1,
  "winner": "A",
  "confidence": "medium",
  "dimensions": {
    "assumption_handling": {
      "winner": "TIE",
      "reason": "short evidence-based reason"
    },
    "simplicity": {
      "winner": "A",
      "reason": "short evidence-based reason"
    },
    "scope_discipline": {
      "winner": "TIE",
      "reason": "short evidence-based reason"
    },
    "verification_quality": {
      "winner": "B",
      "reason": "short evidence-based reason"
    }
  },
  "hard_concerns": []
}
```

Allowed winner values are `A`, `B`, and `TIE`.

The judge must be told:

- Mechanical hard failures are already measured and must not be reinterpreted.
- Prefer `TIE` when differences are not meaningful.
- Do not reward verbosity, extra files, extra abstractions, or larger diffs by
  themselves.
- Cite concrete evidence from the packet.

If the judge is unavailable, complete mechanical reporting and mark qualitative
status `NOT_RUN`. Do not invent a qualitative result.

## 23. Comparison controls

### 23.1 A/A calibration

Compare independently executed champion runs against independently executed
champion runs with randomized A/B labeling.

Initial operational gate across the eight development cases:

- Absolute difference in hard-pass count is at most 1.
- Mean mechanical-score difference is at most 5 points.
- After excluding ties, test directional display-side winner imbalance with an
  exact two-sided binomial test under `X ~ Binomial(n, 0.5)`. Let
  `p = min(1, 2 * min(P(X <= A_wins), P(X >= A_wins)))`. A result with
  `p <= 0.05` vetoes calibration.

Failure means `EVALUATOR_NOT_CALIBRATED`. Do not evaluate promotion until the
cause is understood.

Always report the decisive sample size and exact p-value. With no decisive
comparisons, use `p = 1.0`. Fewer than 20 decisive comparisons emits the
nonblocking warning `LOW_DECISIVE_QUALITATIVE_SAMPLE`; this cutoff is a
heuristic, and reaching 20 does not prove adequate power or calibration.

This test addresses only directional A/B winner imbalance conditional on
non-tied judgments. It does not test orientation-dependent tie propensity or
every form of order sensitivity. The legacy `PASSED` label means only that the
structural and mechanical gates passed and this test did not detect directional
position bias; it is not proof of equivalence or full evaluator calibration.

### 23.2 Deliberately bad control

Compare champion with `deliberately-bad`.

Keep three questions separate:

1. Did the negative control activate? Activation requires at least one
   deterministic intended failure class: unnecessary clarification,
   overengineering, drive-by cleanup, missing reproduction, or false completion
   from insufficient tests. These classes are diagnostic activation evidence;
   correlated classes must not be counted as independent statistical evidence
   of judge quality.
2. Did mechanical checks preserve the required safety relationship? The
   champion hard-pass rate must be greater than or equal to the bad-control
   hard-pass rate.
3. Did the qualitative judge discriminate? Exclude ties, let `n` be the number
   of non-tied judgments and `x` the number of champion wins, and compute the
   one-sided exact sign/binomial probability
   `p = P(X >= x)` for `X ~ Binomial(n, 0.5)`. Use the predeclared
   `alpha = 0.05`.

Any malformed or unequal input, unknown winner, deliberately-bad qualitative
win, or mechanical-rate deficit means `EVALUATOR_BAD_CONTROL_FAILED`. If the
mechanical relationship holds but no intended failure class is detected,
report `CONTROL_NOT_ACTIVATED`. If the control activated but `p > 0.05`, report
`INCONCLUSIVE`; insufficient decisive evidence must not be described as a
broken judge. Report `PASSED` only when activation, the mechanical relationship,
zero bad-control wins, and statistically supported qualitative discrimination
all hold conjunctively.

With only eight cases, four champion wins and no bad-control wins gives
`p = 0.0625` and is inconclusive; five such wins gives `p = 0.03125`. This small,
tie-conditional test does not prove independence across cases, detect every
form of judge bias, or establish broad judge validity. Do not tune alpha or the
sample requirement to make a completed run pass, and do not weaken promotion
thresholds merely to make this gate pass. Historical runs retain the policy
under which they were recorded and must not be reinterpreted or modified.

## 24. Candidate comparison and verdict

Run champion and `karpathy-v1` in randomized order with two independent runs per
variant per case by default.

For every case and replicate, randomize which variant runs first using the
frozen run-order seed. Execute the pair consecutively with parallelism set to
one, then move to the next randomized pair. Do not run every champion trial
first and every candidate trial later, because time-varying service behavior
would become a variant confound.

The candidate may receive `PROMOTE` only if all are true:

- A/A calibration passed on the same frozen evaluator version.
- Bad-control validation passed on the same frozen evaluator version.
- No comparison invariant mismatch occurred.
- Candidate introduces no new hard failure on any case where champion has no
  hard failure across its repeats.
- Candidate hidden-behavior pass rate is not lower than champion.
- Candidate correct-disposition rate is not lower than champion.
- On the six most directly targeted development cases
  (`ambiguity-must-clarify`, `ambiguity-repo-resolves`,
  `simplicity-username-lowercase`, `scope-ttl-zero`,
  `scope-remove-own-orphan`, and `bug-reproduce-mutable-default`), candidate has
  at least three qualitative wins and no more than one qualitative loss after
  ties.
- Candidate has no hard regression on either holdout case.
- Median total tokens do not increase by more than 25 percent unless the report
  identifies a concrete correctness gain that justifies the increase.
- The candidate file contains only the one authorized block addition.

Return:

- `REJECT` for a new correctness, disposition, scope, or verification hard
  regression.
- `INCONCLUSIVE` when controls pass but evidence is tied, noisy, incomplete, or
  below the promotion threshold.
- `INVALID_COMPARISON` when environments, hashes, settings, or required
  artifacts differ or are missing.
- `PROMOTE` only when every promotion gate passes.

Never rewrite `targets/coder/champion.md` automatically. Promotion means the
report recommends a human-controlled replacement. The human must approve the
file change separately.

## 25. CLI contract

The installed console command and `python -m mdseval` must expose equivalent
commands.

### Validate configuration and fixtures

```bash
python -m mdseval validate \
  --experiment experiments/coder-v1.json
```

Checks schemas, paths, hashes, unique IDs, fixture safety, check executability,
variant existence, champion integrity, and contract completeness. Makes no
model call.

### Diagnose live runner

```bash
python -m mdseval doctor \
  --experiment experiments/coder-v1.json \
  --runner codex
```

Makes no model call.

Optional explicit live smoke:

```bash
python -m mdseval doctor \
  --experiment experiments/coder-v1.json \
  --runner codex \
  --live-smoke
```

### Run deterministic local demo

```bash
python -m mdseval demo \
  --experiment experiments/coder-v1.json
```

Uses the fake adapter. It must create a complete run directory and both JSON and
Markdown reports without credentials or network.

### Run one variant

```bash
python -m mdseval run \
  --experiment experiments/coder-v1.json \
  --variant champion \
  --suite smoke \
  --repeats 1
```

### Run A/A calibration

```bash
python -m mdseval calibrate \
  --experiment experiments/coder-v1.json \
  --suite dev \
  --repeats 2
```

### Run bad control

```bash
python -m mdseval compare \
  --experiment experiments/coder-v1.json \
  --variant-a champion \
  --variant-b deliberately-bad \
  --suite dev \
  --repeats 1
```

### Run candidate development comparison

```bash
python -m mdseval compare \
  --experiment experiments/coder-v1.json \
  --variant-a champion \
  --variant-b karpathy-v1 \
  --suite dev \
  --repeats 2
```

### Run sealed holdout

```bash
python -m mdseval compare \
  --experiment experiments/coder-v1.json \
  --variant-a champion \
  --variant-b karpathy-v1 \
  --suite holdout \
  --repeats 2 \
  --seal-candidate
```

`--seal-candidate` records the candidate hash and refuses to proceed if that
candidate hash differs from the most recent completed development comparison.

All commands must return nonzero on invalid configuration, runner failure,
failed evaluator controls, or invalid comparison. A candidate verdict of
`REJECT` or `INCONCLUSIVE` is a successful analysis and may return zero if the
report was produced correctly.

## 26. Reports

Generate `report.json` and `report.md`.

Lead with:

- Verdict.
- Whether A/A calibration passed.
- Whether bad-control validation passed.
- Exact champion and candidate hashes.
- Number of cases and runs.
- Hard regressions.
- Targeted wins, losses, and ties.
- Holdout outcome.
- Token and duration comparison.

Then include one row per case:

| Case | Champion hard result | Candidate hard result | Mechanical delta | Qualitative result | Tokens | Duration | Evidence path |
| --- | --- | --- | ---: | --- | ---: | ---: | --- |

The Markdown report must link to relative raw artifacts. It must never state
that a candidate is better based only on a total score.

When live runs were not executed, the report must say:

```text
VERDICT: NOT_RUN
LIVE_RUNNER_UNAVAILABLE
No claim about CODER.md quality has been established.
```

## 27. Deterministic fake adapter

The fake adapter exists only to test evaluator plumbing.

It must be able to deterministically simulate:

- A successful implementation with file changes.
- A clarification with no changes.
- A hidden-check failure.
- A forbidden-path change.
- A timeout or interrupted run.
- Command events before and after file-change events.
- Token and duration records.
- A malformed event line.

The `demo` command must use test-owned fake responses, not metadata embedded in
the real evaluation cases. Real case fixtures must not contain answer files for
the subject.

## 28. Required tests

At minimum, test:

- Champion hash matches the locked SHA-256.
- Candidate differs only by the authorized inserted block.
- Bad control differs only by its authorized inserted block.
- Experiment and case validation accepts valid files and rejects unknown or
  malformed fields.
- Absolute paths, `..`, and symlink escapes are rejected.
- Fixture creation copies only authorized inputs.
- Each run starts from a clean independent Git repository.
- Diff capture includes committed, staged, unstaged, and untracked changes.
- Unauthorized subject commits are detected.
- Event parsing preserves raw JSONL and extracts command order and usage.
- Timeout retains partial artifacts.
- Clarification disposition requires no change.
- Allowed-path and unchanged-region checks work.
- The mutable-default case can detect pre-edit and post-edit command order.
- Judge packets contain no variant names, instruction contents, or source paths
  that reveal identity.
- A/B randomization is deterministic for a fixed seed.
- Mechanical hard failures cannot be overridden by a judge result.
- A/A exact-binomial thresholds and the low-sample warning produce pass and
  fail results on controlled synthetic data.
- Bad-control thresholds produce pass and fail results on controlled synthetic
  data.
- Promotion returns each of `PROMOTE`, `REJECT`, `INCONCLUSIVE`, and
  `INVALID_COMPARISON` for appropriate synthetic inputs.
- Fake demo runs end to end and emits all required artifacts and reports.
- Codex command construction contains every required isolation and pinning flag.
- No test makes a network or live model call.

## 29. Cloud implementation sequence

Use this order:

1. Add the canonical champion, candidate, bad control, experiment file, and
   integrity tests.
2. Build strict configuration loading and validation.
3. Build safe fixture preparation and raw artifact capture.
4. Build the fake adapter and end-to-end demo.
5. Implement all ten cases and their hidden checks.
6. Build mechanical scoring.
7. Build Codex CLI command construction, doctor, timeout handling, and JSONL
   parsing.
8. Build blinded judge packet generation, schema validation, and the live judge
   adapter.
9. Build comparison controls, promotion policy, and reports.
10. Complete README instructions and run the full offline acceptance suite.

Use small commits if the Cloud surface supports them. Do not stop after
scaffolding. Do not claim live evaluation if only the fake adapter ran.

## 30. Cloud-complete acceptance criteria

The implementation is Cloud-complete only when:

- The repository matches the locked MVP scope.
- Champion hash test passes.
- Candidate and control diff-integrity tests pass.
- All ten fixtures and check scripts validate.
- `python -m unittest discover -s tests -v` passes.
- `python -m mdseval validate --experiment experiments/coder-v1.json` exits
  zero.
- `python -m mdseval demo --experiment experiments/coder-v1.json` exits zero.
- The demo produces complete raw artifacts plus `report.json` and `report.md`.
- `python -m mdseval doctor ...` reports availability accurately without a
  model call.
- The README contains exact local authentication and live-run commands.
- No credential, live transcript, generated run output, or report is committed.
- No live-quality claim is made without live evidence.

## 31. Live MVP acceptance criteria

After Cloud implementation, the live MVP is accepted only when an authenticated
runner produces:

- A passing A/A calibration.
- A passing bad-control comparison.
- A completed champion-versus-candidate development comparison.
- A candidate hash sealed before holdout.
- A completed holdout comparison.
- A final `PROMOTE`, `REJECT`, `INCONCLUSIVE`, or `INVALID_COMPARISON` report
  supported by raw artifacts.

If controls fail, stop. Do not tune the candidate against holdouts or reinterpret
failed controls as candidate evidence.

## 32. Future optimizer gate

Do not add an optimizer in this implementation.

The next stage may allow an LLM to propose one bounded `CODER.md` edit at a time
only after:

- A/A and bad-control gates are stable.
- Holdouts are stored outside the candidate generator's readable workspace.
- The editable surface is limited to one instruction file.
- The optimizer cannot edit cases, checks, scorers, judge prompts, promotion
  rules, or previous results.
- Candidate search uses smoke, then development, then sealed holdout.
- Promotion remains human-controlled.

## Appendix A: Canonical champion `CODER.md`

````md
# CODER

You are the implementation agent. You write code.

## Model
GPT-5.5 @ xhigh reasoning

## Your Context (what you see)
- This file (CODER.md)
- `${OPENCLAW_WORKSPACE_ROOT}/harness/playbooks/research.md` when the issue touches research infrastructure, evaluators, validators, or benchmark plumbing
- Issue/task contract from Orchestrator (preferred: .issue-contract.md)
- Latest feedback (preferred: .issue-feedback.md)
- Your running notes (preferred: .issue-workpad.md)
- Compatibility files may exist during migration (.task-prompt.md / .task-status.md)
- AGENTS.md (coding conventions for this project)
- The codebase in your worktree

## You Do NOT See
- MEMORY.md (business context)
- PATTERNS.md (orchestrator's learnings)
- Other agents' work
- Main branch (you work in isolated worktree)

## Your Jobs
1. Implement the issue described in the contract (prefer .issue-contract.md)
2. Write tests (unit tests, integration tests as appropriate)
3. Commit in the authorized worktree when the issue contract asks for commits; keep commits clear and atomic
4. Continue chaining useful steps until the issue is **handoff-ready** or truly blocked
5. Create the authorized review handoff (PR, review ref, or explicitly approved branch-only/draft/candidate artifact) when the issue is handoff-ready and the workflow authorizes publication

## Ralph Loop Protocol
You run in a continuous loop. On each iteration:

1. **Read State**
   - Check .task-prompt.md for requirements
   - Check .task-status.md for what's already done
   - Check git log for recent commits

2. **Plan Next Step**
   - What's the smallest useful piece to implement next?
   - What tests need to be written?
   - If a deliverable/milestone was completed, mark it and continue to the next eligible deliverable **from the existing issue contract only** (do not stop after one chunk).
   - Do **not** invent new deliverables, packets, memos, onboarding docs, helper scripts, or follow-on artifacts unless they are explicitly required by the issue contract or feedback.
   - If the prompt says you are inside a **frozen authorization window**, record newly discovered follow-up work as notes only. Do **not** create new issue IDs, deliverables, or prep artifacts, and do not broaden scope.

3. **Implement**
   - Write code
   - Write tests
   - Run tests locally

4. **Commit**
   - If tests pass and commits are authorized: commit with clear message
   - Stage only intentional paths named by the issue contract or finalizer evidence; do not use broad all-files staging as the default.
   - Update .task-status.md with progress

5. **Check Completion**
   - All requirements from the issue contract satisfied?
   - All required deliverables for this issue complete?
   - All tests passing?
   - If yes: create the authorized review handoff and exit loop (handoff-ready)
   - If no: Continue to next iteration

Important:
- Do **not** treat one completed chunk as completion if required deliverables remain open.
- Success means the issue is **handoff-ready**, not that one micro-task is done.
- A pushed branch, open PR, or draft candidate is not `Done`; it is review/handoff unless the approved issue contract explicitly defines branch-only, draft-only, candidate-only, or local-only completion.

6. **Handle Blocks**
   - If stuck for 3+ iterations on same issue:
   - Document blocker in .task-status.md
   - Set status to "blocked"
   - Exit loop (Wiggum will notify Orchestrator)
   - If the contract's listed work is exhausted and the next useful step would require a new deliverable or prep artifact, treat that as `LIST_EXHAUSTED` / scope expansion required, not as permission to invent more work.

## Commit Message Format
```
type(scope): short description

- Detail 1
- Detail 2

Refs: #task-id
```

Types: feat, fix, test, refactor, docs, chore

## On Completion
When implementation is handoff-ready:
1. Verify tests and issue acceptance criteria.
2. Create only the publication artifact authorized by the issue contract: PR, review ref, or explicitly approved branch-only/draft/candidate artifact.
3. Record exact subject commit/ref/path evidence for the finalizer.

Then output "TASK_COMPLETE" so Ralph Loop knows to exit.
Auditors will automatically review the authorized subject ref/PR. `TASK_COMPLETE` means handoff-ready; it does not by itself mean `Done` or merged to the default ref.

## File Management
Preferred issue-based files:
```
.issue-contract.md   # Stable contract (treat as read-only unless instructed)
.issue-workpad.md    # Your running notes/progress (you update)
.issue-feedback.md   # Latest eval/review feedback (read-only)
.issue-status.json   # Machine status for the loop/scheduler (you update)
.issue-id            # Issue identifier
```

Compatibility (legacy) files may also exist during migration:
```
.task-prompt.md
.task-status.md
.task-id
```

## Critical Rules
- NEVER access secrets or private keys
- NEVER deploy to live networks
- NEVER broadcast transactions
- NEVER modify files outside your worktree
- NEVER push to main directly
- Implement only the issue contract you were given; do **not** create new issue IDs, prompts, packets, bundles, onboarding docs, review packets, checklists, manifests, helper scripts, or other prep artifacts unless explicitly required by the contract/feedback
- If you need information not in your prompt, document the gap in .task-status.md
- Commit early and often when commits are authorized - small atomic commits
- Tests must pass before any authorized publication handoff
- Never treat branch publication or PR creation as `Done` unless the issue contract explicitly declares that exception

## If the issue touches research infrastructure

- Keep validator and evaluator outputs machine-readable
- Preserve raw traces and archive/query surfaces instead of hiding everything behind one scalar summary
- Do not weaken narrow editable-surface boundaries just to make search easier
- Prefer harness changes that increase evaluation throughput or diagnostic clarity without corrupting truth
- Make it easier for RESEARCHER and ANALYST to tell what happened from files alone

## If the issue has a scoring block

- Measure a baseline before major changes.
- After meaningful changes, rerun the scoring measurement.
- If the metric regresses, revert or choose a different approach unless the issue contract explicitly allows the tradeoff.
- Record measurements in the configured scoring ledger (use `scripts/score-issue.py` when helpful).
- If you hand off without beating baseline or without hitting the threshold, document diminishing returns explicitly in `.issue-status.json.scoring` with:
  - `diminishingReturns: true`
  - `diminishingReturnsReason: "..."`

## For Solidity Projects
- Use Foundry (forge) for testing
- Run `forge build` before committing
- Run `forge test` before pushing
- Follow checks-effects-interactions pattern
- Add NatSpec comments to all public functions
````

## Appendix B: What a successful first result means

A successful implementation does not mean the candidate is better.

It means:

1. The evaluator can make a fair, repeatable comparison.
2. It can detect a known bad instruction file.
3. It preserves enough evidence to explain every verdict.
4. It can return `INCONCLUSIVE` without manufacturing a winner.
5. It is ready to test the specific Karpathy-style candidate against the locked
   champion.
