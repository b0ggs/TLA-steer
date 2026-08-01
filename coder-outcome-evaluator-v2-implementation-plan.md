# CODER Outcome Evaluator V2 — Implementation Plan

**Repository:** [b0ggs/MDs_EVAL](https://github.com/b0ggs/MDs_EVAL)  
**Base branch:** [`agent/multi-candidate-support`](https://github.com/b0ggs/MDs_EVAL/tree/agent/multi-candidate-support)  
**Inspected head:** `bf1b0b5c4d1d86f2068e709de32b7277b6b2f8d0`  
**Status:** Implementation plan only. It does not authorize live model calls, commits, pushes, a PR, or a promotion claim.

## 1. Objective

Build a reusable evaluator that answers:

> For a fixed model, reasoning effort, runner, permissions, budget, and coding-task distribution, which `CODER.md` causes the agent to complete more coding tasks correctly without regressions?

For this MVP:

- The target role is only **CODER**.
- The experimental unit is one complete `CODER.md`.
- The subject is single-agent Codex CLI.
- The runtime remains `gpt-5.6-sol` at `high` reasoning.
- Subagents and agent-command network access remain disabled.
- The primary result is deterministic coding-task resolution.
- Assumption handling, simplicity, scope discipline, reproduction behavior, verification behavior, tokens, and duration are secondary diagnostics. They cannot turn equal coding success into `PROMOTE`.

The V2 claim must be:

> Candidate X produced better coding-task outcomes than the champion on the CODER Outcome V2 lockbox under the frozen runtime.

It must not claim that the candidate is universally best across all repositories, languages, models, or harnesses.

## 2. Confirmed defect in the current branch

The multi-candidate plumbing is useful and should be retained: immutable candidate hashes, randomized paired order, clean disposable fixtures, blinding, raw evidence, controls, and sealed lineage.

The measurement target is wrong for the research question.

### 2.1 Current promotion can occur with no coding-success improvement

[`src/mdseval/promotion.py`](https://github.com/b0ggs/MDs_EVAL/blob/agent/multi-candidate-support/src/mdseval/promotion.py) can return `PROMOTE` when champion and candidate have identical:

- hidden-behavior pass rates;
- expected-disposition rates;
- hard passes;
- token use; and
- coding results.

The positive promotion threshold is instead at least three qualitative wins and at most one loss on six Karpathy-derived targeted cases.

The repository already contains a direct proof. [`tests/test_promotion.py::test_promote_requires_complete_bound_evidence`](https://github.com/b0ggs/MDs_EVAL/blob/agent/multi-candidate-support/tests/test_promotion.py) gives both variants equal correctness, assigns qualitative wins to the candidate, and expects `PROMOTE`.

### 2.2 Mechanical correctness is mixed with desired behavior

[`src/mdseval/scoring/mechanical.py`](https://github.com/b0ggs/MDs_EVAL/blob/agent/multi-candidate-support/src/mdseval/scoring/mechanical.py) puts these into one all-or-nothing `hard_pass`:

- deterministic functional checks;
- exact disposition wording;
- a focused clarification shape;
- a required pre-edit reproduction;
- a required post-edit command;
- exact allowed paths;
- literal unchanged regions;
- absence of broadly named artifacts; and
- runtime/evidence validity.

This makes a functionally correct patch fail because it did not exhibit the selected process, while a candidate can later be promoted through qualitative preference without solving more tasks.

### 2.3 The ten cases are a behavioral probe suite

The current cases are all tiny synthetic Python fixtures. Several contracts reveal the desired process or root cause:

- ask one focused question;
- read a named ADR;
- avoid a nearby abstraction;
- preserve an exact legacy block;
- remove a named helper and import;
- run a named failure before and after editing;
- avoid documentation/configuration/abstraction work; or
- fix a specifically identified stale function call.

These cases are useful diagnostics for the Karpathy-inspired intervention. They are not a representative primary benchmark for coding-agent success.

### 2.4 The current holdout is exposed

The two holdout contracts, fixtures, checks, and rubrics are committed in the same repository. They are no longer unseen for any candidate written after repository inspection.

### 2.5 Three multi-candidate tests remain brittle

Adding another real candidate currently breaks assumptions in:

1. `tests/test_config.py::test_candidate_registry_accepts_sorted_versions_and_schema_is_open`, which expects an exact Karpathy-only tuple plus its temporary candidates.
2. `tests/test_config.py::test_reserved_roles_and_at_least_one_candidate_are_required`, which assumes removing `karpathy-v1` removes the only candidate.
3. `tests/test_cli.py::test_validate`, which assumes the Karpathy row appears immediately after the `CANDIDATES:` heading.

The historical test proving that `karpathy-v1.md` equals its one authorized inserted block is intentionally candidate-specific and must remain.

## 3. Compatibility decision

Do not reinterpret V1 evidence.

- Leave `experiments/coder-v1.json`, its ten cases, current control, schemas, reports, and historical runs intact.
- Label V1 in documentation as **behavioral diagnostic evidence**.
- Add a parallel V2 outcome path with new schema/report versions.
- V1 evidence can never authorize V2 calibration, development, validation, or lockbox execution.
- Every V2 change invalidates earlier V2 control evidence when a control-relevant hash changes.
- Candidate-only additions should not invalidate outcome controls; Section 9 defines the safe binding.

Suggested implementation branch:

```text
agent/coder-outcomes-v2
```

Create it from the inspected multi-candidate head. Do not rewrite the existing branch.

## 4. Locked V2 measurement model

### 4.1 Separate four concepts

Every subject result must expose four separately reported components:

| Object | Meaning | Promotion relevance |
| --- | --- | --- |
| `run_valid` | The runner completed within budget and evidence/invariants are intact | Required |
| `task_resolved` | The final repository passes all required acceptance and regression checks | Primary outcome |
| `integrity_pass` | Protected evaluator/contract/instruction inputs were not changed and no unauthorized commit occurred | Required veto |
| `diagnostics` | Process, scope, commands, final response, diff size, tokens, duration, and optional judge feedback | Report only |

The reported primary boolean is derived, not a fifth judgment:

```text
task_resolved =
    run_valid
    AND all required fail-to-pass checks pass
    AND all required pass-to-pass checks pass
    AND all required post-only checks pass
    AND integrity_pass
```

Keeping the component fields separate explains whether a failure came from the code, the runtime, or experimental integrity while ensuring that a timed-out or boundary-violating run cannot count as a coding success.

`task_resolved` must not depend on:

- whether the response looks Karpathy-inspired;
- whether the agent ran a prescribed command;
- whether the failure was reproduced before editing;
- an exact first-line disposition;
- changing only an anticipated file allowlist;
- producing the smallest diff;
- avoiding abstractions unless the public contract requires a particular architecture;
- winning an LLM judgment; or
- token cost, provided the fixed timeout/budget was respected.

### 4.2 Required deterministic checks

Each V2 task has typed checks:

- **fail-to-pass:** acceptance behavior that must fail on the pristine fixture and pass after a correct implementation;
- **pass-to-pass:** existing behavior that must pass both before and after the change;
- **post-only:** integration, mutation, or integrity checks that only make sense after the subject acts.

Before any subject model call:

1. Every fail-to-pass check must fail on the pristine fixture.
2. Every pass-to-pass check must pass.
3. The full fixture and check-pack hashes must match the frozen manifest.

After the subject exits:

1. Every required fail-to-pass check must pass.
2. Every required pass-to-pass check must still pass.
3. Every required post-only check must pass.
4. Protected inputs and the evaluator boundary must be intact.

Then and only then is `task_resolved = true`.

Partial assertion counts may be recorded for diagnosis, but promotion uses the binary task result.

### 4.3 Unit of inference

The statistical unit is the **task**, not each repeated rollout.

For each task:

- candidate task win: candidate resolves more repeats than champion;
- champion task win: champion resolves more repeats than candidate;
- tie: equal resolved-repeat counts.

Run the existing exact one-sided sign test over decisive task wins and losses. Do not treat repeated runs of one task as independent benchmark items.

### 4.4 Formal verdict

A confirmatory lockbox result returns:

- `PROMOTE` only when all evidence and control gates pass, candidate task wins exceed champion task wins, the exact one-sided test is at or below `alpha = 0.05`, and the absolute resolved-run-rate lift is at least 10 percentage points;
- `REJECT` when the candidate is significantly worse by the symmetric rule or has a critical integrity violation;
- `INCONCLUSIVE` for equal success, a small or statistically unsupported difference, incomplete decisive evidence, or an efficiency-only advantage;
- `INVALID_COMPARISON` for missing, mismatched, exposed, mutated, or incomplete evidence.

Qualitative wins can never change one of these verdicts.

Development and validation may return `ADVANCE_TO_VALIDATION`, `ELIGIBLE_FINALIST`, or `DO_NOT_ADVANCE`, but never `PROMOTE`.

### 4.5 Efficiency and secondary quality

Report separately:

- total and median tokens;
- runtime;
- tool errors;
- files inspected and changed;
- repeat disagreement;
- deterministic protocol violations;
- optional blinded maintainability preference when both variants resolve the task.

An equal-success, lower-cost candidate is a Pareto/operational option, not evidence that it codes better.

## 5. Benchmark structure

Use three information boundaries:

| Split | Candidate author access | Use |
| --- | --- | --- |
| Development | Full contracts, fixtures, outcomes, and trajectories | Candidate creation and trace-derived iteration |
| Validation | Concealed pack; return aggregate/category results | Select a single finalist; exploratory only |
| Lockbox | Concealed, unused pack; one frozen finalist only | Confirmatory verdict |

The current V1 holdout is not reusable in either concealed split.

### 5.1 MVP task count and balance

Create 24 primary tasks:

| Task family | Dev | Validation | Lockbox | Total |
| --- | ---: | ---: | ---: | ---: |
| Bug fixes | 2 | 2 | 2 | 6 |
| Feature implementation | 3 | 1 | 2 | 6 |
| Integration/entrypoint | 2 | 1 | 1 | 4 |
| Refactor/migration | 2 | 1 | 1 | 4 |
| Tests/tooling | 1 | 1 | 2 | 4 |
| **Total** | **10** | **6** | **8** | **24** |

The committed experiment also declares two subsets of the ten development tasks:

- `smoke`: four cases, one run, plumbing only;
- `calibration`: six cases stratified across task family, complexity, and language.

These are subsets, not additional benchmark tasks.

Complexity requirements:

- 6 small, 12 medium, and 6 large tasks;
- at least 16 tasks require changes in two or more files;
- at least 8 tasks require changes across three or more production/test/interface files;
- repository families are disjoint across development, validation, and lockbox;
- no near-duplicate issues cross a split;
- both overbuilding and underbuilding can fail through objective outcome checks, not prose preferences.

Preferred language mix:

- 16 Python tasks using only the standard library and `unittest`;
- 8 JavaScript tasks using only the installed Node runtime and `node:test`;
- no package installation and no network access.

Predeclare the split balance:

| Split | Python | JavaScript | Small | Medium | Large |
| --- | ---: | ---: | ---: | ---: | ---: |
| Development | 7 | 3 | 3 | 5 | 2 |
| Validation | 4 | 2 | 1 | 3 | 2 |
| Lockbox | 5 | 3 | 2 | 4 | 2 |
| **Total** | **16** | **8** | **6** | **12** | **6** |

The V2 doctor must verify Python and Node before accepting this mixed-language pack. If the canonical runtime lacks Node, stop for a user decision; do not install it or silently reduce the suite. A Python-only fallback must narrow the claim to Python coding.

### 5.2 Repository fixture requirements

Use several small but coherent repository snapshots rather than 24 one-function toys.

Each fixture should generally contain:

- 4–15 source/test/interface files;
- approximately 300–1,500 relevant lines;
- a real test command already present in the repository;
- more than one plausible edit location;
- enough unrelated working behavior for regression checks;
- no hidden answer or reference patch in Git history; and
- no dependency download at runtime.

Prefer curated, permissively licensed real repository snapshots or candidate-independent synthetic repositories modeled on real issue classes. Record provenance, upstream commit, and license when real source is used.

### 5.3 Contract rules

Contracts describe observable goals and genuine interface constraints. They must not prescribe desired agent behavior.

Ban unless it is a real user requirement:

- “use the smallest implementation”;
- “do not overengineer”;
- “ask one focused question”;
- “read this ADR before deciding”;
- “run this command before editing”;
- “do not modify nearby code”;
- a revealed root cause such as “the executable calls a stale function”;
- exact target-file lists that reveal the solution; or
- prohibitions on documentation, configuration, helpers, or refactors added only to favor one MD philosophy.

Exact outputs, public API rules, security constraints, compatibility requirements, and reproducible user-visible symptoms are appropriate.

### 5.4 Task-author independence

- Development task authors must use this task taxonomy, not candidate content, as their source.
- Validation and lockbox authors must not inspect champion or candidate MD contents.
- Candidate writers may inspect development only.
- The lockbox must be authored and stored outside the candidate-authoring checkout.
- Reference patches, hidden checks, and mutants never enter the subject fixture.
- Task inclusion cannot depend on which existing MD wins.

### 5.5 Task authoring acceptance gate

Every task must pass all of these before inclusion:

1. The fixture runs without network access or new packages.
2. Pass-to-pass checks succeed on the baseline.
3. Fail-to-pass checks fail on the baseline for the intended reason.
4. A separately stored reference patch passes every check.
5. At least two plausible incorrect patches or mutants fail.
6. Reverting the reference patch returns the exact baseline tree hash.
7. No check, reference patch, candidate text, alternative instruction file, or answer marker reaches the subject fixture.
8. A second reviewer confirms every hidden assertion follows from the contract.
9. Neutral/champion pilot runs do not show a complete floor or ceiling across the whole pack.
10. A contract linter finds no process prescriptions or candidate-specific phrases.

Test-authoring cases have an extra gate: agent-authored tests must pass correct code and kill at least two concealed mutants. Empty, assertion-free, or implementation-coupled tests cannot resolve the task.

## 6. V2 case and pack formats

### 6.1 Production case layout

```text
<case-id>/
├── case.json
├── contract.md
├── fixture/
└── checks/
    ├── acceptance.py
    ├── regression.py
    └── post.py
```

Reference patches, alternate solutions, review notes, and mutants live in a separate authoring workspace:

```text
<authoring-workspace>/<case-id>/
├── reference.patch
├── review.json
└── mutants/
```

That workspace is never committed with development cases, included in validation/lockbox production packs, copied to the subject, or made readable to the candidate-writing process.

### 6.2 Case schema example

```json
{
  "schema_version": 2,
  "id": "bug-pagination-cursor",
  "suite": "dev",
  "task_family": "bug_fix",
  "language": "python",
  "complexity": "medium",
  "repository_family": "catalog-service",
  "provenance": {
    "kind": "curated_real_commit",
    "upstream_repository": "owner/repository",
    "base_commit": "full-sha",
    "license": "MIT"
  },
  "protected_paths": ["CODER.md", ".issue-contract.md"],
  "checks": {
    "fail_to_pass": [
      {
        "id": "pagination-acceptance",
        "command": ["python3", "checks/acceptance.py", "--repo", "{repo}"]
      }
    ],
    "pass_to_pass": [
      {
        "id": "existing-regressions",
        "command": ["python3", "checks/regression.py", "--repo", "{repo}"]
      }
    ],
    "post_only": []
  },
  "diagnostics": {
    "expected_change_paths": [],
    "verification_patterns": [],
    "unchanged_regions": []
  },
  "limits": {
    "timeout_seconds": 1800
  }
}
```

For validation and lockbox packs, `suite` is verified against the external pack manifest.

### 6.3 External pack layout

```text
<external-pack>/
├── manifest.json
└── cases/
    └── <case-id>/
```

The manifest freezes:

- pack ID and split;
- objective and measurement version;
- ordered case IDs;
- task-family, complexity, language, and repository-family balance;
- every contract, fixture, check, and case-definition hash;
- full tree hash;
- authoring/reviewer attestations; and
- creation timestamp.

The real validation and lockbox packs are never committed to this repository. They are stored as immutable archives in a separately access-controlled custodian workspace with a stable pack ID and retained bytes. Unit tests use synthetic temporary packs outside the checkout.

### 6.4 Confirmatory isolation and custody

An external directory is not, by itself, a secrecy boundary. A `workspace-write` subject may still be able to read parent or unrelated filesystem paths. Therefore:

- Development may use the current trusted local isolation model.
- Concealed validation and confirmatory lockbox execution require a subject filesystem boundary that exposes only the sanitized subject repository plus the minimum runtime files.
- Contracts and fixtures are copied into that boundary one case at a time.
- Checks, manifests, reference material, other cases, evaluator source, pack paths, and custody records remain in the evaluator/custodian process and are not mounted or readable by the subject.
- An approved mechanism may be an already-available container/VM boundary or a separate OS account with proven filesystem permissions. The implementation must not install a new isolation product automatically.
- Before the first real concealed run, a canary exercise must prove that a subject commanded to find known files outside its repository cannot read or enumerate them.
- If the canonical environment cannot prove this boundary, V2 may run development but must report `CONFIRMATORY_ISOLATION_UNAVAILABLE` and refuse validation/lockbox claims.

The custodian retains the exact immutable pack archive, manifest, and SHA-256 so an authorized independent reviewer can reproduce or audit the result after the pack is spent. A claimed hash without retained bytes is insufficient.

Custodian receipts use a strict JSON schema and contain:

- receipt kind: `reservation` or `consumption`;
- stable pack ID and archive SHA-256;
- finalist seal ID and hash;
- one-use reservation nonce;
- custodian authority ID;
- issue timestamp;
- immutable external record identifier; and
- for consumption, the completed run-manifest hash.

The evaluator validates identity and hash agreement but does not pretend it can prove the custodian's organizational independence. That remains an attested research control.

## 7. Controls

### 7.1 Outcome A/A

Run champion versus byte-identical champion aliases on a six-task stratified development subset with three repeats.

The gate checks:

- complete and valid evidence;
- no statistically significant side/order advantage in task resolution;
- absolute side resolution-rate difference no greater than 10 percentage points;
- repeat disagreement and per-case variance reported; and
- no qualitative-judge requirement.

### 7.2 Outcome negative control

Add a hash-locked `controls/coder/nonimplementing-v1.md` that consistently declines implementation or makes no code changes. It must not contain case-specific answers or markers.

The control passes only if the champion materially and significantly outperforms it on task resolution across the same calibration subset. Do not reuse the V1 overengineering-marker control as evidence that the V2 primary selector works.

### 7.3 Candidate-independent control binding

Candidate experimentation should not require rerunning controls merely because a new candidate file and registry row were added.

Create a V2 `control_core_sha256` from:

- evaluator production code;
- outcome schemas;
- wrapper;
- fixed runtime configuration;
- ordered development/calibration case catalog and hashes;
- decision policy;
- champion bytes; and
- outcome-negative-control bytes.

Normalize candidate registry entries out of the experiment material used for this hash. Still record the full evaluator commit/state and candidate-registry hash in every run.

Required behavior:

- adding only a distinct candidate file and its valid registry entry preserves `control_core_sha256`;
- changing source, scoring, schemas, wrapper, runtime, cases, champion, control, or decision policy changes it and makes controls stale;
- candidate outcomes and evidence never pool across candidate IDs or hashes.

## 8. Candidate-selection and lockbox protocol

1. Register one or more immutable versioned candidates.
2. Run V2 validation and current V2 controls.
3. Compare candidates on development. Candidate authors may use full failures and trajectories to create new versions.
4. Compare a bounded shortlist on concealed validation. Return aggregate and category results; treat all validation-informed edits as exploratory.
5. Select exactly one finalist and create a finalist seal containing:
   - candidate ID and SHA-256;
   - experiment and control-core hashes;
   - source development and validation report/manifest paths and hashes;
   - selection timestamp; and
   - operator acknowledgment that the lockbox has not been accessed.
6. Materialize the external lockbox only after the seal exists.
7. Run champion versus the sealed candidate once.
8. Append the pack hash, candidate hash, seal, result, timestamp, previous-record hash, and current-record hash to a local tamper-evident exposure cache.
9. Require an external custodian receipt that atomically binds the stable pack ID and archive hash to the finalist seal and marks that pack reserved before execution, then spent after execution.
10. Refuse a second confirmatory use of that lockbox hash. An explicit `--exploratory` override may preserve another run, but it must force `INCONCLUSIVE` and state that the pack was already exposed.

The local hash chain detects modification of retained records but cannot prove that a ledger was not deleted, truncated, or rolled back. The external custodian receipt is authoritative for confirmatory freshness; without it, the report must be exploratory.

The locally authored candidate informed by the current visible tests may still be evaluated on development. It can become confirmatory only against a fresh V2 lockbox that neither its author nor its generating context saw.

## 9. Exact repository changes

### 9.1 Preserve unchanged

- `experiments/coder-v1.json`
- `evals/dev/**`
- `evals/holdout/**`
- `candidates/coder/karpathy-v1.md`
- `targets/coder/champion.md`
- `controls/coder/deliberately-bad.md`
- all historical runs and reports
- V1 interpretation of schema/report version 1

### 9.2 Add

| Path | Purpose |
| --- | --- |
| `docs/coder-outcomes-v2-spec.md` | Normative V2 measurement specification |
| `docs/task-authoring-standard.md` | Contract, fixture, check, provenance, mutation, and review rules |
| `docs/lockbox-protocol.md` | Independence, custody, subject isolation, sealing, exposure, reuse, and claim rules |
| `experiments/coder-outcomes-v2.json` | V2 outcome experiment and candidate registry |
| `schemas/experiment-v2.schema.json` | Strict V2 experiment schema |
| `schemas/case-v2.schema.json` | Strict outcome-case schema |
| `schemas/case-pack-v1.schema.json` | External validation/lockbox manifest schema |
| `schemas/custodian-receipt-v1.schema.json` | Strict external reservation/consumption receipt contract |
| `schemas/outcome-report-v2.schema.json` | Machine-readable result contract |
| `controls/coder/nonimplementing-v1.md` | V2 objective negative control |
| `evals/coder-outcomes-v2/dev/<case>/` | Ten committed development cases |
| `case-packs/manifests/validation-policy.json` | Required validation count/balance, not case content |
| `case-packs/manifests/lockbox-policy.json` | Required lockbox count/balance, not case content |
| `src/mdseval/casepacks.py` | Safe external pack loading, validation, hashing, and materialization |
| `src/mdseval/scoring/outcome.py` | Deterministic baseline/post checks and `task_resolved` |
| `src/mdseval/outcome_decision.py` | Task-level aggregation, exact test, effect gate, verdict |
| `src/mdseval/outcome_controls.py` | Outcome A/A and negative-control gates |
| `src/mdseval/outcome_lineage.py` | V2 evidence kinds, finalist seal, local exposure cache, and external receipt validation |
| `tests/test_casepacks.py` | External-pack safety and hash tests |
| `tests/test_outcome_scoring.py` | Baseline inversion and resolution tests |
| `tests/test_outcome_decision.py` | Exact task-level decision tests |
| `tests/test_outcome_controls.py` | V2 control boundary tests |
| `tests/test_outcome_lineage.py` | Seal, tamper, and spent-pack tests |

### 9.3 Modify

| Path | Required change |
| --- | --- |
| `src/mdseval/config.py` | Read schema version first; dispatch V1 or V2; retain V1 `LOCKED_SUITES`; add typed V2 case/check/pack models and non-hardcoded catalogs |
| `src/mdseval/variants.py` | Keep current locks; add objective-profile control ID/hash; make reserved control IDs profile-aware |
| `src/mdseval/capture.py` | Add labeled typed check results while keeping V1 `run_hidden_checks` unchanged |
| `src/mdseval/fixtures.py` | Add pristine-fixture preflight and safe external-pack materialization; checks and authoring material stay outside subject repo |
| `src/mdseval/execution.py` | Dispatch scorer by objective; preserve randomized order/raw evidence/frozen bytes; record baseline checks and pack hashes; make judge optional/secondary |
| `src/mdseval/compare.py` | Retain V1 aggregation; expose shared exact-stat helpers and V2 task-level outcome aggregation |
| `src/mdseval/scoring/qualitative.py` | Reuse blinding for optional V2 maintainability diagnostics; no promotion influence; remove or wire any inert V2 rubric/dimension fields |
| `src/mdseval/promotion.py` | Preserve V1 function; dispatch V2 to outcome decision; no hardcoded V2 case IDs or qualitative thresholds |
| `src/mdseval/report.py` | Preserve V1 builder; add V2 report led by tasks resolved, paired task outcomes, effect, exact p-value, controls, and exposure state |
| `src/mdseval/cli.py` | Dispatch commands by objective; add `preflight`, `validate-pack`, `seal-finalist`, `finalize-lockbox`, external pack/receipt arguments, and versioned evidence lookup |
| `src/mdseval/wrapper.py` | Keep execution authority neutral; remove no V1 behavior, but do not add coding-style prescriptions to V2 |
| `tests/helpers.py` | Support isolated V1/V2 checkouts and temporary external packs without hardcoded candidate counts |
| `tests/test_config.py` | Fix the two candidate-count assumptions; add V1/V2 dispatch and non-hardcoded V2 cases |
| `tests/test_cli.py` | Parse candidate rows generically; test V2 commands and no-call preflights |
| `tests/test_fake_e2e.py` | Preserve V1 fake run; add complete V2 outcome fake run |
| `tests/test_promotion.py` | Keep V1 history tests; add explicit proof that V2 equal correctness cannot promote |
| `tests/test_report.py` | Test V2 primary/secondary separation and claim language |
| `README.md` | Explain V1 diagnostics versus V2 coding outcomes and exact operator workflow |

## 10. Staged implementation

No stage makes a live model call.

### Stage 0 — Preserve the base and fix candidate extensibility

1. Create the implementation branch from the inspected head.
2. Record base commit, worktree status, and the current offline test result.
3. Preserve any user-owned uncommitted candidate; do not silently include, rewrite, or delete it.
4. Fix the three brittle multi-candidate assertions in Section 2.5.
5. Add a test proving that one new candidate file plus one registry entry passes without modifying test expectations.
6. Run the full V1 offline suite.

Gate: V1 behavior is unchanged and an arbitrary second candidate validates.

### Stage 1 — Freeze V2 schemas and configuration

1. Add the normative V2 spec and strict schemas.
2. Add version-dispatched config models.
3. Exercise V2 loading with test-owned temporary configurations during this stage; do not commit an empty or placeholder production experiment.
4. Prove V1 configs still load identically.
5. Prove V1 evidence cannot satisfy any V2 command.

Gate: schemas and config are strict, non-hardcoded, backward-compatible, and make zero model calls.

### Stage 2 — Build case-pack safety and objective scoring

1. Implement external pack validation and tree hashing.
2. Implement baseline fail-to-pass/pass-to-pass preflight.
3. Implement typed post-run checks.
4. Implement `run_valid`, `task_resolved`, `integrity_pass`, and diagnostics separately.
5. Add a small synthetic V2 pack only under test fixtures.
6. Preserve all current raw evidence.

Gate: a correct patch resolves a task regardless of reproduction ceremony; a behaviorally polished but incorrect patch does not.

### Stage 3 — Build controls, statistics, and reports

1. Add outcome A/A and negative control.
2. Add task-level aggregation and exact sign test.
3. Add the 10-point minimum effect gate.
4. Add V2 JSON/Markdown reports.
5. Keep optional qualitative output explicitly secondary.

Gate: equal coding success plus a qualitative sweep returns `INCONCLUSIVE`; objective superiority can return `PROMOTE` even if the qualitative judge prefers the champion.

### Stage 4 — Build lineage, sealing, and exposure protection

1. Add candidate-independent control binding.
2. Add versioned development/validation evidence.
3. Add immutable finalist seals.
4. Add external pack pre/post hash checks.
5. Add the hash-chained local exposure cache and spent-pack refusal.
6. Add strict validation for custodian reservation/consumption receipts; do not invent or self-issue them.
7. Make a lockbox subject run produce `PENDING_CUSTODIAN_FINALIZATION`, never a confirmatory verdict, until `finalize-lockbox` validates a matching consumption receipt without another model call.
8. Fail every mismatch before subject execution when it is knowable before execution.

Gate: no candidate or mutated candidate can reach a confirmatory lockbox without exact lineage and an external reservation receipt; a spent or unreceipted lockbox cannot produce a confirmatory verdict.

### Stage 5 — Author and validate development content

1. Create ten development tasks matching Section 5.
2. Run the authoring acceptance gate on every task.
3. Independently audit contracts for process/style leakage.
4. Pilot difficulty with neutral/champion baselines only after all task content is frozen.
5. Replace tasks only for objective authoring defects, complete floor/ceiling failure, or violated balance—not based on candidate performance.
6. Add the production `experiments/coder-outcomes-v2.json` only after all referenced development, smoke, and calibration IDs exist and validate.

Gate: all ten tasks pass authoring validation and the committed pack matches its declared balance.

### Stage 6 — Independently create concealed packs

This stage is performed in a separate account/workspace by a task author and custodian who have not read candidate contents.

1. Create six validation and eight lockbox tasks in disjoint repository families.
2. Run the same authoring and independent review gates.
3. Store immutable pack archives outside the candidate-authoring checkout under stable custodian IDs.
4. Retain exact archive bytes for later authorized review or reproduction.
5. Commit only policy manifests and, when appropriate, pack IDs/hashes—not contracts, fixtures, checks, reference patches, or mutants.
6. Record separate author, reviewer, and custodian attestations. The evaluator can validate those records but cannot prove what a person previously read.

Gate: only the custodian/evaluation environment can validate real pack structure and hashes; the candidate-writing environment can validate public policy manifests but has no capability to open a concealed pack.

### Stage 7 — Final offline audit and live handoff

1. Run all offline commands in Section 12.
2. Audit the full diff for V1 regression, V2 outcome alignment, leakage, live-call absence, and hidden-pack absence.
3. In the final evaluation environment, prove subject filesystem isolation with concealed canaries before mounting a real validation or lockbox pack.
4. Stop on any defect; do not compensate by weakening a test or promotion threshold.
5. Only after offline acceptance and the isolation canary may the operator run the live sequence.

## 11. Required test matrix

### Backward compatibility

- Current V1 config, schemas, cases, fake E2E, reports, controls, and hashes still pass.
- Historical V1 evidence remains readable but cannot authorize V2.
- No existing run or report is rewritten.

### Candidate extensibility

- Any safe versioned candidate can be added with one file and one registry row.
- Tests derive expected candidate sets instead of assuming Karpathy is alone.
- Karpathy's authorized-block integrity test remains exact.
- Duplicate bytes, bad IDs, symlinks, and path mismatches still fail.

### Outcome correctness

- A correct final repository with no pre-edit reproduction is resolved.
- A polished final response cannot rescue failed acceptance.
- Passing acceptance while regressing existing behavior is unresolved.
- Modifying visible tests cannot defeat external hidden checks.
- Exact disposition wording does not alter task resolution.
- Extra unrelated files are diagnostic unless they cross a protected boundary or cause regression.
- A timeout, invalid evidence stream, protected-path change, or unauthorized commit fails closed.

### Baseline and task authoring

- Already-solved fail-to-pass checks reject a case.
- Broken baseline regressions reject a case.
- Reference patches pass and concealed mutants fail.
- Reference material never reaches the subject fixture.
- Pack traversal, absolute paths, symlinks, duplicate IDs, unsafe interpreters, and hash drift fail.

### Statistics and promotion

- Equal task resolution plus all qualitative candidate wins is `INCONCLUSIVE`.
- Lower resolution plus all qualitative candidate wins cannot promote.
- Higher resolution plus qualitative losses can promote when exact/effect gates pass.
- Repeats aggregate within a task.
- Duplicate, missing, or wrong repeats invalidate.
- Development and validation outcomes are never pooled into the confirmatory test.
- Cost-only improvement cannot establish better coding.
- Boundary tests cover exact p-values immediately above and below 0.05 and effect immediately below/at 0.10.

### Controls

- Outcome A/A passes and fails at deterministic boundaries.
- Outcome negative control passes and fails at deterministic boundaries.
- The V1 overengineering control cannot authorize V2.
- Candidate-only registry changes preserve the control-core hash.
- Evaluator, task, schema, wrapper, runtime, champion, control, or policy changes invalidate controls.

### Lineage and lockbox

- CLI candidate, evidence index, report, manifest, and finalist seal all agree on ID/hash.
- Development and validation sources are complete and hash-bound.
- Pack hash is checked before and after execution.
- Candidate or evaluator drift stops.
- A spent pack is rejected for confirmatory reuse.
- Missing, invalid, mismatched, or replayed custodian receipts prevent a confirmatory verdict.
- A completed subject run remains `PENDING_CUSTODIAN_FINALIZATION` until a matching consumption receipt is attached.
- Deleting or truncating the local exposure cache cannot manufacture freshness because the external receipt is authoritative.
- `--exploratory` preserves evidence but cannot return `PROMOTE`.
- Every knowable preflight error proves no subject or judge call occurred.

### Concealed-pack isolation

- Subject inventory contains only the sanitized case fixture, `CODER.md`, contract, and required runtime files.
- A subject cannot enumerate or read external pack manifests, checks, sibling cases, reference patches, evaluator source, or custody receipts.
- Real `validate-pack` access is unavailable in the candidate-authoring environment.
- A failed isolation canary returns `CONFIRMATORY_ISOLATION_UNAVAILABLE` before a concealed pack is mounted.

### Blinding and reporting

- Candidate IDs, paths, and instruction fragments remain absent from optional judge packets.
- V2 report leads with tasks resolved, paired task outcomes, effect, and exact p-value.
- Process/qualitative diagnostics are visibly secondary.
- `quality_claim_established` is replaced or supplemented with explicit `claim_scope`, `confirmatory`, and `lockbox_fresh` fields.
- Fake V2 E2E emits all required raw artifacts with zero live calls.

## 12. Acceptance commands

### Offline implementation acceptance

```bash
python3 -m unittest discover -s tests -v
python3 -m mdseval validate --experiment experiments/coder-v1.json
python3 -m mdseval demo --experiment experiments/coder-v1.json

python3 -m mdseval validate --experiment experiments/coder-outcomes-v2.json
python3 -m mdseval preflight \
  --experiment experiments/coder-outcomes-v2.json \
  --suite dev
python3 -m mdseval demo \
  --experiment experiments/coder-outcomes-v2.json

python3 -m mdseval validate-pack \
  --experiment experiments/coder-outcomes-v2.json \
  --suite validation \
  --case-pack /absolute/path/to/test-validation-pack

git diff --check
git status --short
```

The validation-pack command in automated tests uses a temporary synthetic pack. Do not require the real concealed pack for source-code acceptance.

The real `validate-pack`, concealed validation, sealing receipt, and lockbox commands are run only by the isolated evaluation/custodian environment after candidate bytes are frozen. They are not available to the candidate-authoring process.

### Live sequence after offline acceptance

```bash
# 1. Outcome A/A on the stratified calibration subset.
python3 -m mdseval calibrate \
  --experiment experiments/coder-outcomes-v2.json \
  --suite calibration \
  --repeats 3

# 2. Objective negative control.
python3 -m mdseval compare \
  --experiment experiments/coder-outcomes-v2.json \
  --variant-a champion \
  --variant-b nonimplementing-v1 \
  --suite calibration \
  --repeats 1

# 3. Candidate development.
python3 -m mdseval compare \
  --experiment experiments/coder-outcomes-v2.json \
  --variant-a champion \
  --variant-b <candidate-id> \
  --suite dev \
  --repeats 2

# 4. Concealed validation for a bounded shortlist.
python3 -m mdseval compare \
  --experiment experiments/coder-outcomes-v2.json \
  --variant-a champion \
  --variant-b <candidate-id> \
  --suite validation \
  --case-pack /absolute/path/to/validation-pack \
  --repeats 2

# 5. Freeze one finalist before lockbox access.
python3 -m mdseval seal-finalist \
  --experiment experiments/coder-outcomes-v2.json \
  --candidate <candidate-id> \
  --source-dev-run <dev-run-id> \
  --source-validation-run <validation-run-id>

# 6. One confirmatory lockbox run.
python3 -m mdseval compare \
  --experiment experiments/coder-outcomes-v2.json \
  --variant-a champion \
  --variant-b <candidate-id> \
  --suite lockbox \
  --case-pack /absolute/path/to/fresh-lockbox-pack \
  --seal-id <seal-id> \
  --reservation-receipt /absolute/path/to/reservation-receipt.json \
  --repeats 2

# 7. After the custodian marks the exact pack/run spent, finalize without a model call.
python3 -m mdseval finalize-lockbox \
  --experiment experiments/coder-outcomes-v2.json \
  --run-id <lockbox-run-id> \
  --consumption-receipt /absolute/path/to/consumption-receipt.json
```

No command automatically edits the champion, retries a failure, selects another candidate, reuses a lockbox, commits, pushes, or opens a PR.

## 13. Stop conditions

Stop and request user direction if:

- V1 behavior or historical evidence must be mutated to implement V2;
- Node is absent and the language mix would change;
- a new package or network access appears necessary;
- a real validation/lockbox pack would enter the candidate-authoring repository;
- concealed checks or sibling cases are readable from the subject process;
- no existing container/VM or separate-account boundary can pass the isolation canary;
- the custodian cannot retain exact immutable pack bytes or issue authoritative reservation/consumption receipts;
- a task cannot pass its reference/mutant/reversion gates;
- task inclusion is being chosen based on candidate performance;
- a qualitative result is needed to produce `PROMOTE`;
- repeats would be counted as independent tasks;
- a spent lockbox would be reused for a confirmatory claim;
- any offline test invokes a live model; or
- implementation requires autonomous prompt optimization, a UI, a service, a database, role bundles, multiple agents, or topology comparison.

## 14. Explicitly deferred

- Automatic GEPA/ACE/OPRO-style candidate generation.
- Multi-file role bundles.
- Orchestrator, auditor, or researcher evaluation.
- Agent-topology comparison.
- Cross-model transfer claims.
- Package-dependent language ecosystems.
- Hosted dashboards or benchmark services.

V2 must preserve enough raw trajectories and per-check evidence for later trace-derived candidate optimization, but it does not implement that optimizer.

## 15. Literature-to-design traceability

| Evidence | Design consequence |
| --- | --- |
| [Evaluating AGENTS.md](https://arxiv.org/abs/2602.11988) | Do not assume longer or generated context helps; compare complete files on held-out coding outcomes. |
| [Probe-and-Refine repository guidance](https://arxiv.org/abs/2606.20512) | Preserve development failures and trajectories so later candidates can be derived from actual repository-task failures. |
| [`p1`: Better Prompt Optimization with Fewer Prompts](https://arxiv.org/abs/2604.08801) | Measure repeated-run noise, retain discriminative development tasks, and do not confuse stochastic variance with an MD effect. |
| [GEPA](https://arxiv.org/abs/2507.19457) | Keep candidate hashes, localized failure evidence, and multiple development candidates; defer optimization until evaluation is aligned. |
| [SWE-agent](https://proceedings.neurips.cc/paper_files/paper/2024/file/5a7c947568c1b1328ccc5230172e1e7c-Paper-Conference.pdf) | Put deterministic correctness and regression requirements into tools/checks rather than prose-style judgment. |
| [Anthropic prompt postmortem](https://www.anthropic.com/engineering/april-23-postmortem) | Treat every instruction change as model-specific and require broad held-out ablation before promotion. |

## 16. Definition of done

The CODER Outcome V2 MVP is complete only when:

- V1 remains reproducible and explicitly diagnostic.
- Adding a candidate requires one immutable MD and one registry entry.
- V2 task resolution is determined by final-repository acceptance and regression checks.
- Equal coding success cannot promote through qualitative behavior.
- Ten development, six concealed validation, and eight fresh lockbox tasks pass authoring gates.
- Outcome A/A and objective negative controls pass.
- Candidate, evaluator, task-pack, decision-policy, and lineage hashes remain frozen.
- One finalist is sealed before lockbox access.
- A fresh lockbox is used once.
- The subject cannot read concealed pack material outside its sanitized repository.
- A separate custodian retains the exact pack bytes and issues authoritative reservation/consumption receipts.
- The report states the exact coding-outcome effect, uncertainty, costs, and claim boundary.
- No winner is claimed when the result is equal, noisy, underpowered, exposed, or invalid.

The central acceptance sentence is:

> In V2, `PROMOTE` is impossible unless the candidate resolves more objective coding tasks than the champion with the predeclared confirmatory evidence.
