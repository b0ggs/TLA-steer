# Multi-candidate comparison implementation plan

Implementation plan only; no implementation is authorized by this document alone.

This is the strict Phase 1 authority for later, separately authorized implementation. If implementation needs a material design change, an unlisted file, or more lines than allowed here, work stops for user direction.

## 1. Objective and current limitation

Allow a human to preserve `karpathy-v1.md`, add multiple versioned candidate Markdown files, validate and list them offline, compare one selected candidate with the locked champion, and optionally bind a holdout run to that same candidate's completed development evidence.

The current evaluator supports only one candidate because the schema, runtime lock, comparison CLI, development-evidence lookup, and sealed-holdout lineage explicitly name `karpathy-v1`. Reports record the candidate hash but do not clearly name the selected candidate.

Phase 1 generalizes candidate identity and selection. It does not broaden what the evaluator measures or weaken any control.

## 2. Phase 1 control-evidence decision

Keep control evidence bound to the exact experiment SHA-256, evaluator commit/state, wrapper, schemas, runtime, seed, and current invariants. Adding or registering a candidate changes the committed state, so prior A/A and bad-control evidence becomes stale.

Candidate-independent calibration reuse is deferred to a separate future specification. This plan does not alter `current_control_context`, evaluator identity, clean-checkout requirements, experiment hashing, or control-binding semantics.

Several candidates registered in one commit may share controls produced afterward for that exact commit. Results, replicates, or retries from different candidates must never be pooled.

Manual retry ledgers or exploratory-verdict machinery, a holdout-exposure ledger or fresh-holdout engine, multiplicity corrections, candidate-independent calibration reuse, full snapshot/locking or runner refactors, a global live-call canary framework, raw duplicate-JSON-key hardening, and programmatic development-verdict gating are explicitly deferred. Phase 1 documents the retry, multiplicity, and holdout-exposure limitations but does not implement those systems.

## 3. Locked invariants

1. Preserve raw run evidence and historical artifacts.
2. Never modify a target or candidate during a run.
3. Never expose variant IDs, paths, filenames, or instruction contents to the qualitative judge.
4. Mechanical failures remain visible and cannot be overridden by an LLM judge.
5. Unit tests and CI make no live model calls.
6. Use only the Python standard library.
7. Keep the champion byte-locked to `CHAMPION_SHA256`.
8. Keep the deliberately-bad control byte-locked to its existing authorized construction.
9. Do not change suites, cases, contracts, checks, rubrics, wrapper, models, permissions, repeats, scoring, statistics, or promotion thresholds.
10. Live comparisons require a clean committed checkout.
11. Freeze and recheck the selected candidate hash before and after execution.
12. Promotion remains a human-facing recommendation; the evaluator never rewrites the champion.

## 4. Chosen flat-registry design

Keep `schema_version: 1` and the existing `variants` object in `experiments/coder-v1.json`. Do not add another registry.

Reserved role IDs are:

- `champion`
- `deliberately-bad`

Every other JSON-declared, validated entry is a candidate. `ExperimentConfig.candidate_ids` is a deterministic lexicographically sorted tuple of those IDs. The schema continues to require both reserved roles and at least one candidate while permitting additional safe candidate entries. Internal A/A aliases are execution-only aliases, not registry candidates.

Tiny example:

```json
"variants": {
  "champion": "targets/coder/champion.md",
  "karpathy-v1": "candidates/coder/karpathy-v1.md",
  "implementation-discipline-v2": "candidates/coder/implementation-discipline-v2.md",
  "deliberately-bad": "controls/coder/deliberately-bad.md"
}
```

Runtime integrity locks the champion and bad control. The focused historical test still proves that `karpathy-v1` equals its authorized block. Other candidates are trusted manual inputs identified by registered ID and exact SHA-256; they need not derive from that block.

The fake demo selects `karpathy-v1` when it is present. Otherwise it selects the lexicographically first validated candidate. An offline test must cover both branches.

## 5. Candidate identity and validation

A new candidate ID must:

- use lowercase kebab-case ending in a positive integer `-vN` suffix;
- match `^[a-z0-9]+(?:-[a-z0-9]+)*-v[1-9][0-9]*$`;
- not equal a reserved ID;
- equal its filename stem; and
- be unique in the registry.

For target role `<target-role>` and candidate ID `<id>`, the lexical path must be exactly:

```text
candidates/<target-role>/<id>.md
```

Candidate checks apply only while loading JSON-declared variants in `load_experiment`; `validate_locked_variants` checks the locked champion/control and must ignore internal A/A aliases. Inspect the unresolved lexical path with `lstat`/`is_symlink` before `resolve_within`, so resolution cannot hide a symlink.

Reject missing, nested, outside-root, mismatched, non-`.md`, symlink, empty, whitespace-only, or non-UTF-8 candidate files. Reject candidate bytes identical to the champion or bad control. Also reject duplicate bytes across any two registered candidate IDs; version labels may not alias identical content. Candidate-ID uniqueness is the parsed JSON object's normal mapping property; raw duplicate JSON member detection is deferred. Tests must cover every required rejection, including duplicate candidate bytes.

After a candidate has evidence, humans create a new version instead of editing that file. If current bytes differ from development evidence, holdout fails closed.

## 6. Exact file and function scope

Only these production/configuration areas may change:

- `schemas/experiment.schema.json`: permit safe additional candidates while retaining reserved roles.
- `src/mdseval/variants.py`: reserved constants and `validate_locked_variants` baseline/control behavior.
- `src/mdseval/config.py`: `ExperimentConfig.candidate_ids` and candidate checks in `load_experiment`.
- `src/mdseval/cli.py`: Stage 0 holdout guard plus `_command_validate`, `_command_demo`, `_load_prior_dev`, `_command_compare`, report call sites, and candidate identity in development evidence.
- `src/mdseval/report.py`: `build_report` and `render_markdown` candidate identity.
- `src/mdseval/execution.py`: the narrow Stage 0 pre-judge drift guard and minimal report identity plumbing; no snapshot, locking, runner, or orchestration refactor.
- `README.md`: exact workflow, cost, and stop warnings.
- `docs/coder-single-file-mvp-spec.md`: only clauses directly conflicting with this extension.

Only these tests may change:

- `tests/test_config.py`
- `tests/test_cli.py`
- `tests/test_fake_e2e.py`
- `tests/test_report.py`
- `tests/test_hashing.py`
- `tests/test_qualitative.py`

Do not change `experiments/coder-v1.json` merely to implement support. Adding a real candidate is a separate onboarding action. Add no production module.

Do not refactor comparison statistics, promotion, mechanical scoring, capture, runners, fixtures, case definitions, judge parsing, or winner restoration.

## 7. Staged implementation

### Stage 0: narrow integrity prerequisites

Scope: `cli.py`, `execution.py`, `test_cli.py`, and `test_fake_e2e.py`, only for these two defects:

1. `_command_run` rejects every single-variant `holdout` request before `_require_live`; focused mocks prove no doctor, runner, or judge boundary is reached. Maximum 15 changed implementation/test lines.
2. Immediately before packet construction, read each selected instruction file once as bytes, hash those exact bytes against its frozen snapshot, decode those verified bytes for the blinding inputs, and on mismatch or decode failure mark the comparison invalid, skip the judge, stop further experiment work, and retain completed raw evidence. Maximum 35 changed implementation/test lines.

Stage 0 adds no generalized snapshot, locking, runner, retry, or live-call framework. Maximum 50 changed lines total.

### Stage 1: registry and validation

Scope: schema, `variants.py`, `config.py`, `test_config.py`, and `test_hashing.py`.

Deliver reserved roles, deterministic candidate IDs, JSON-registry-only naming/path/content/hash-uniqueness checks, lexical symlink rejection, explicit A/A-alias exemption, unchanged locked-byte checks, and focused tests. Maximum 120 changed lines.

### Stage 2: generic comparison and lineage

Scope: `cli.py`, `report.py`, minimal report call sites in `execution.py`, `test_cli.py`, and `test_report.py`.

Deliver validate listing, exact demo selection, generic registered-candidate comparison, champion-first enforcement, unchanged bad-control behavior, current-control preflight, top-level report `candidate_id`, candidate-specific development evidence, interleaving-safe lookup, and fully bound four-source holdout lineage. Maximum 145 changed lines.

Stage 2 final exception: after the failed sole-repair verification, the user approved exactly one final test-only correction in `tests/test_cli.py`. Final Stage 2 limits remain at most 145 changed lines and 56 net-new lines; the current 138 changed and +54 net leave at most 7 changed and 2 net-new lines. Production edits and all other files are forbidden. The correction may cover only post-run control mutation and the four sealed report/manifest source path/hash assertions. One final read-only verification follows; any failure requires reverting and stopping, with no further repair or audit loop.

### Stage 3: reporting, blinding, and fake E2E

Scope: `test_fake_e2e.py` and `test_qualitative.py` only.

Deliver arbitrary-candidate blinding regression coverage and the unchanged complete fake-E2E artifact contract. Maximum 50 changed lines.

Stage 3 final exception: after the initial audit, the user approved exactly one final test-only rewrite in `tests/test_qualitative.py`. Final Stage 3 limits remain at most 50 changed lines and 20 net-new lines; the current diff is 49 changed and net -1. Production, configuration, and all other test edits are forbidden. The rewrite must capture and inspect the actual `packet.json` at the mocked `run_live_judge` boundary for a non-Karpathy candidate, use JSON-escape-aware forbidden-content checks, and keep judging stably mocked. One final read-only verification follows; any failure requires reverting and stopping, with no further repair or audit loop.

### Stage 4: documentation and offline verification

Scope: README and directly conflicting MVP-spec clauses. Document the exact workflow, retry/multiplicity/holdout caveats, costs, and deferred machinery. A bounded verifier then runs the full offline suite and diff checks. Maximum 35 changed lines.

Stage ceilings are not targets. They total 400 changed lines; overall limits in Section 16 always control.

## 8. Exact user and CLI workflow

There is no new mutating add command or separate list command. A human:

1. creates `candidates/coder/<candidate-id>.md` under a new version;
2. adds one mapping to the flat `variants` object without changing old entries;
3. validates and reviews the deterministic candidate list;
4. commits the candidate and mapping locally;
5. runs controls for that exact clean commit;
6. runs development for one selected candidate; and
7. considers holdout only after reviewing development and explicitly approving the calls.

Offline validate/list:

```bash
python3 -m mdseval validate --experiment experiments/coder-v1.json
```

It prints candidate ID, repository-relative path, and SHA-256 in sorted order:

```text
VALID: coder-single-file-v1; 10 cases; 4 variants
CANDIDATES:
- implementation-discipline-v2  candidates/coder/implementation-discipline-v2.md  sha256=<hash>
- karpathy-v1                   candidates/coder/karpathy-v1.md                   sha256=<hash>
```

Non-live doctor:

```bash
python3 -m mdseval doctor --experiment experiments/coder-v1.json --runner codex
```

Do not add `--live-smoke` without separate approval.

`mdseval run --suite holdout` is always rejected before live-runner preflight. The only allowed holdout execution path is the sealed pair-comparison command below.

Exact controls:

```bash
python3 -m mdseval calibrate \
  --experiment experiments/coder-v1.json --suite dev --repeats 2

python3 -m mdseval compare \
  --experiment experiments/coder-v1.json \
  --variant-a champion --variant-b deliberately-bad \
  --suite dev --repeats 1
```

Stop on either failure; never retry automatically.

Selected-candidate development:

```bash
python3 -m mdseval compare \
  --experiment experiments/coder-v1.json \
  --variant-a champion --variant-b implementation-discipline-v2 \
  --suite dev --repeats 2
```

Stop and present the report. Holdout is never automatic.

Explicitly approved holdout:

```bash
python3 -m mdseval compare \
  --experiment experiments/coder-v1.json \
  --variant-a champion --variant-b implementation-discipline-v2 \
  --suite holdout --repeats 2 --seal-candidate
```

No command automatically commits, pushes, opens a PR, merges, promotes, retries, or starts another stage.

## 9. Evidence, reporting, and sealed holdout

New candidate-development evidence-index entries add `candidate_id` and retain `candidate_hash`. Candidate-comparison reports add the exact top-level field `"candidate_id": "<registered-id>"` while retaining `variant_hashes.candidate` unchanged. Markdown renders that same ID and hash. This is additive under report schema version 1.

Holdout may start only when all four identity sources agree exactly:

1. requested CLI candidate ID and current file hash;
2. evidence-index candidate ID and hash;
3. development report top-level `candidate_id` and `variant_hashes.candidate`; and
4. the dynamic candidate key and hash in the development manifest.

Those identities must also match the same experiment SHA-256, evaluator state, control binding, dev suite, case set, repeats, complete subject/judge evidence, and intact report/manifest hashes. Paths must remain inside `runs/`. Holdout metadata binds candidate ID/hash and source report/manifest paths/hashes.

Lookup selects the latest completed entry for the requested candidate ID, not the latest candidate globally. Development for B cannot displace or satisfy A. Existing pre-run and post-run lineage rechecks remain; a change between them fails closed.

Tests must tamper each identity boundary, including the evidence-index candidate ID and evidence-index candidate hash, and prove holdout stops before live execution. Use localized mocks at `_require_live`, execution, and judge boundaries; do not introduce a global live-call canary framework.

## 10. Blinding, mechanical, and statistical safeguards

The blinded-packet builder continues receiving selected IDs, artifact IDs, source paths, and full instruction contents as forbidden material. A test uses a new candidate ID and unique content marker and proves neither appears in serialized judge input.

Mechanical results remain gate-first and non-overridable. Raw artifacts and invariant mismatches remain visible.

Statistical behavior does not change. A/A rules, bad-control activation/veto, the exact one-sided sign test and alpha, targeted cases, replicate accounting, regression gates, token gate, and promotion thresholds remain unchanged.

There is no multiplicity adjustment across multiple candidates. `PROMOTE` is a heuristic policy recommendation under the fixed gates, not a claim of family-wise statistical significance. Results from different candidates, repeated attempts, or retries must not be pooled.

A manual rerun is a separate preserved attempt. A quality-motivated rerun, post-hoc choice among attempts, or retry informed by prior results is exploratory and must be disclosed; Phase 1 adds no retry ledger or exploratory-verdict enforcement.

Holdouts are reusable only as long as they remain genuinely unseen for the decision process. If holdout results inform tuning or selection of a later candidate, evaluation of that later candidate against the same holdouts is exploratory, not confirmatory. A new confirmatory claim would require fresh undisclosed holdouts under a separate approved specification.

## 11. Backward compatibility and historical evidence

- Keep `candidates/coder/karpathy-v1.md`, its registry ID, bytes, commands, and authorized-block test unchanged.
- Keep champion and bad-control files unchanged.
- Keep experiment and report schema versions at 1.
- Never edit or delete historical runs, reports, manifests, or raw evidence.
- New development evidence includes explicit candidate ID/hash.
- Legacy evidence remains readable and untouched but is ineligible for a new sealed holdout because it lacks the new explicit four-source identity and belongs to an older evaluator state.
- Do not infer a missing legacy candidate ID or rewrite legacy evidence to add fields.
- Old controls cannot authorize the new evaluator commit; run fresh controls.

## 12. Required failures

Configuration, control, selection, and sealed-lineage preflight failures occur before any model invocation and explain that no call was made. Runtime drift can only be detected after completed subject calls; it must state which work already occurred, invalidate the comparison, and stop before the judge or any further subject work.

Required failure facts include:

- reserved, unsafe, or unversioned candidate ID;
- ID/filename/path mismatch;
- unregistered candidate, with direction to run `validate`;
- empty, invalid UTF-8, symlinked, locked-role-identical, or duplicate candidate bytes;
- wrong comparison order, with champion-first syntax;
- missing, failed, or stale controls, explicitly stating no candidate call occurred;
- absent development evidence for the requested ID/hash;
- disagreement among CLI, evidence index, report, or manifest candidate identity;
- changed candidate hash; and
- missing, escaped, modified, or incomplete development lineage.

Never fall back to another candidate or start a retry. Focused rejection tests use localized mocks and assert the relevant live boundary was not reached; no global canary infrastructure is added.

## 13. Offline test matrix

| Area | Required coverage |
| --- | --- |
| Existing config | Current experiment and `karpathy-v1` still load; locked roles remain required |
| Holdout prerequisite | Single-variant holdout is rejected before `_require_live`; only sealed pair holdout remains |
| Pre-judge drift | Verified frozen bytes provide redaction text; drift invalidates, skips judge, stops further work, and preserves completed evidence |
| IDs and paths | Accept exact `candidates/<target-role>/<id>.md`; reject reserved, unsafe, unversioned, nested, outside, mismatched, missing, non-Markdown, or lexically symlinked input |
| Bytes | Accept distinct nonempty UTF-8; reject empty, non-UTF-8, champion/control matches, and duplicate bytes across candidate IDs |
| Registry/A/A | Candidate rules apply to JSON entries; internal duplicate champion A/A aliases remain valid |
| Listing/demo | Sorted ID/path/hash listing; demo chooses Karpathy when present and lexicographically first validated candidate otherwise |
| Compare | Any registered candidate reaches fake/mocked execution as variant B; unknown ID and wrong order stop first |
| Controls | Current passing controls permit development; missing, failed, or stale controls stop it |
| Evidence | Development records selected ID/hash; interleaved A/B histories remain independent |
| Holdout | Matching four-source identity succeeds; tamper CLI selection, evidence-index ID/hash, top-level report ID/hash, manifest dynamic ID/hash, binding, path, hashes, coverage, or bytes and fail closed |
| Legacy evidence | Remains readable/unchanged but cannot satisfy new sealed holdout |
| Reporting | JSON/Markdown clearly show selected candidate ID/hash |
| Blinding | Candidate ID, path, and unique instruction marker are absent from judge packet |
| Fake E2E | Dynamic candidate and demo retain complete artifacts and frozen-input checks |
| Live safety | Mocks/fakes only; any attempted live subject or judge call fails the test |

Final offline verification:

```bash
python3 -m unittest discover -s tests -v
git diff --check
```

Also inspect `git diff --stat`, `git diff --numstat`, and worktree status.

## 14. Orchestration and audit protocol

Root orchestrates and does not write implementation code.

For each stage:

1. Root assigns one bounded implementer the exact files, behavior, and line cap.
2. The implementer makes only that stage's changes, runs focused offline tests, reports diffs, and stops.
3. Root assigns one separate read-only initial audit for that stage.
4. If it finds a concrete defect, root may authorize at most one bounded repair pass.
5. A separate read-only verification checks that repair.
6. Failed verification stops all work for user direction; there is no second repair or audit loop.

After all stages, one final whole-diff read-only audit checks scope, invariants, tests, and caps. Any defect found there stops for user direction. The final audit does not trigger an automatic repair loop.

Subagents do not expand scope, launch implementation swarms, begin later stages early, or audit indefinitely.

## 15. No-live policy, prohibited scope, and stop conditions

Implementation, audits, repairs, and acceptance make zero live model calls. Do not run `doctor --live-smoke`, `mdseval run`, `mdseval calibrate`, live `compare`, or direct subject/judge `codex exec`. Use mocks and `FakeAdapter`.

Prohibited: files outside Section 6; new dependencies/modules; UI; generation/optimization; automatic discovery outside the registry; mutating add/list commands; batch/tournament behavior; automatic Git/live actions; unrelated cleanup; and implementation of calibration reuse, retry/exploratory ledgers or verdicts, holdout ledgers/fresh-holdout engines, multiplicity corrections, development-verdict gating, global live-call canaries, raw duplicate-key parsing, or generalized snapshot/locking/runner changes.

Stop and report if a cap is near, a listed invariant cannot be kept, schema version 2 or migration appears necessary, unrelated worktree changes overlap, a test exposes an out-of-scope design issue, a stage fails repair verification, the final audit finds a defect, or live calls/new authority are required. Do not improvise or launch more agents.

## 16. Diff limits and live-cost implications

Measure each stage's changed lines as additions plus deletions introduced relative to the immediately preceding audited stage. Measure overall changed and net-new lines relative to the clean commit containing this plan, excluding this plan and future user-authored candidate contents. Later deletions do not erase earlier per-stage churn, while the final whole-diff must independently satisfy the global caps.

- Hard stop: 400 changed lines total, additions plus deletions.
- Hard stop: 225 net-new lines total.
- Hard stop: 150 changed lines under `src/mdseval/`.
- Tests and docs count; no exception without an approved replacement plan.

Default maximum model invocations for a clean state are:

- A/A: 48;
- bad control: 24;
- one candidate development run: 48; and
- one candidate holdout: 12.

Controls cost 72. A complete one-candidate cycle costs at most 132. Multiple candidates registered before calibration may share those controls but never pool candidate outcomes. A later candidate-changing commit requires fresh controls. No failure is retried automatically.

## 17. Acceptance and handoff checklist

Implementation is ready for handoff only when root confirms:

- [ ] Only Section 6 files changed and all diff caps pass.
- [ ] Single-variant holdout is blocked before live preflight, and verified frozen instruction bytes stop pre-judge drift without a broader refactor.
- [ ] A second candidate requires only a new versioned Markdown file and additive registry mapping; old candidates remain unchanged.
- [ ] Validation lists deterministic candidate ID/path/hash and rejects all specified identity/content errors, including duplicate bytes.
- [ ] Generic development remains champion-first and requires current controls.
- [ ] The four candidate identity sources agree for holdout; interleaving and every tamper test fail closed.
- [ ] Reports identify the candidate; judge packets do not.
- [ ] Mechanical, statistical, promotion, runtime, and evidence policies are unchanged.
- [ ] `karpathy-v1` and historical evidence remain intact; legacy evidence is not inferred or accepted for new sealed holdout.
- [ ] Full offline tests and `git diff --check` pass with zero live calls.
- [ ] Focused stage audits, any single repair verification, and final whole-diff audit followed Section 14.
- [ ] Worktree status, changed paths, line counts, tests, and absence of live calls are disclosed.
- [ ] No commit, push, merge, live controls, development, or holdout occurred without separate authorization.

Passing offline acceptance means implementation is review-ready, not live-calibrated.
