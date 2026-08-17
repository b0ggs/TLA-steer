# CODER beneficial-sensitivity Milestone 2 implementation plan

Status: v0.4 closed `INVALID`; v0.4.1 closed
`SENSITIVITY_NOT_DEMONSTRATED` at selection. Sections 1--12 are frozen
historical lifecycle evidence; Section 13 is the sole prospective development
amendment and authorizes neither task creation nor live/model/API calls.
Scientific authority: `CODER_BENEFICIAL_SENSITIVITY_PROTOCOL.md` v0.4 governs
only its frozen campaigns; a future confirmatory protocol may be written only
after Section 13 development PASS.
Roadmap stage: Milestone 2 only — demonstrate beneficial measurement sensitivity

## 1. Authority, outcome, and scope

For every new Milestone 2 action, this plan supersedes
`coder-outcome-evaluator-v2-implementation-plan.md`. The older plan, repairs,
code, experiment, and raw evidence remain immutable historical evidence only.
This is the sole active Milestone 2 implementation plan.

Section 13 supersedes every prospective or active instruction in Sections
1--12. Their imperative wording records the frozen v0.4/v0.4.1 design and
completed lifecycle; it grants no current edit, role, commissioning,
qualification, campaign, retry, or live-call authority. The v0.4.1 verdict and
all raw evidence remain valid and immutable evidence about the old instrument.

The one-shot manipulation check compares complete project-level files:

- `N`: a present zero-byte `CODER.md`, SHA-256
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`;
- `H`: unchanged `controls/coder/no-implementation-v2.md`, SHA-256
  `aaf88530c73385ad6d38a45dae67be4872e650afc27d620a8d640430e2ec5606`;
  and
- `P`: one independently authored helpful control for complete coverage of
  explicit coding-task requirements.

The subject runtime is strictly `gpt-5.6-sol`, reasoning effort `high`, one
ephemeral agent, subagents off, workspace-write, agent-command network off,
300 seconds per attempt, serial execution, and zero qualitative-judge calls.
Freeze the requested model/effort, strict command/configuration, resolved CLI
path/SHA/version, isolated configuration, evaluator commit/hash, and wrapper
hash. Service-emitted identity must match when present; absence is recorded as
`not_reported`, disclosed, and nonfatal. Explicit contradictory or reroute
metadata is fatal. Claims concern the configured runtime as served, not
provider-attested backend identity.
The only successful verdict is `SENSITIVITY_DEMONSTRATED`. A valid failed
selection, power, control, or helpful gate is
`SENSITIVITY_NOT_DEMONSTRATED`; an integrity failure is `INVALID`. Either closes
this version without tuning or rerunning. The allowed claim is only that, under
the frozen diagnostic conditions, A/A produced no winner, the harmful control
lost, and `P` produced an observed macro-average increase of at least 0.20 while
rejecting the taskwise no-effect/exchangeability null at exact two-sided
`p <= 0.05`.

Allowed outputs are `P` and its provenance; one independently authored,
checker-qualified 20-task pool; the smallest M2 orchestration/tests/config;
frozen schedules; immutable evidence; and offline-replayable JSON/Markdown.
Prohibited: leaderboard, ranking/public submission, dashboard, optimizer,
candidate/champion comparison, another role, multi-model/cross-model experiment,
billing/dollar logic, judge, dependency, container/security platform, hosted
service, bundle/topology work, or autonomous generation. Production, tasks,
checkers, and tests are Python-standard-library-only. Tests/CI make zero live or
network calls. This plan authorizes no implementation, commit, push, merge, or
live call by itself.

`P`, `H`, tasks, checkers, wrapper, construct, and statistics are completed
read-only historical artifacts. No engineering or lifecycle path in Sections
1--12 remains active.

The existing `coder-beneficial-sensitivity-m2-ada7a71` and
`coder-beneficial-sensitivity-m2-b9c3a8e` roots remain byte-for-byte preserved,
excluded development diagnostics. They do not contribute observations, validate
this amendment, or authorize reuse. A future implementation adds one concise
external exclusion/deviation record without altering either root.

## 2. Reuse proof and one justified module

The implementation owner must record the actual call/import sites below. A new
abstraction requires a reproduced blocking mismatch.

| Existing component | Required use |
| --- | --- |
| `CodexCLI.run`, `RunnerConfig` | Subject execution and config-derived runtime; no copied runner code |
| `prepare_fixture` | Fresh isolated Git repo, exact fixture/treatment/contract inputs, baseline commit |
| `audit_final_subject_tree` | Reject subject-created symlinks before checks/capture |
| `capture_git`, `parse_event_stream` | Patch/untracked/command/usage evidence; no copied capture/evidence code |
| hashing, Git, and process helpers | Existing hash, safe Git, and process semantics |
| `WRAPPER_PROMPT` | One unchanged wrapper that neither teaches the construct nor reveals an arm |
| V2 checker/receipt pattern | Checks outside the workspace and clean-commit hash-bound qualification |
| `outcome_mvp.py` and V2 pack | Preserve read-only: hardcoded historical 8-task, 2-wave, 56/60-call replay |

The historical module cannot express commissioning, 20-by-6 null calibration,
model-bound 16-task selection, three stage-specific fallbacks, four helpful
rounds, 296/313 calls, power, or stratified bootstrap without changing historical
replay. The existing `beneficial_sensitivity.py` remains the sole M2-specific
module. It is a thin orchestrator over the named functions, not a runner, capture/evidence
framework, judge, or generalized experiment platform. Copying their logic is a
cap violation and blocker.
## 3. Exact path allowlist and hard budgets

The original construction paths below document existing M2 scope; they do not
authorize v0.4 edits. Existing unrelated dirty/untracked paths remain untouched.

### Reuse read-only

- `src/mdseval/runner/codex_cli.py`, `src/mdseval/config.py`
- `src/mdseval/fixtures.py`, `src/mdseval/capture.py`
- `src/mdseval/hashing.py`, `src/mdseval/gitutils.py`, `src/mdseval/processutils.py`
- `src/mdseval/wrapper.py`, `src/mdseval/outcome_mvp.py`
- `tests/test_outcome_mvp.py`, `experiments/coder-outcomes-v2-mvp.json`
- `evals/mvp/coder-outcomes-v2/**`, `evals/qualification/coder-outcomes-v2/**`
- `controls/coder/no-implementation-v2.md`
Historical preservation is checked from Git/hash inventories and existing tests;
implementation roles receive no access to existing `runs/**` or reports.

### Original construction modify path (closed)

- `README.md` — exact M2 offline, commissioning, campaign, stop, and replay commands only

### Original construction new paths (closed)

- `src/mdseval/beneficial_sensitivity.py`
- `tests/test_beneficial_sensitivity.py`
- `experiments/coder-beneficial-sensitivity-m2.json`
- `experiments/coder-beneficial-sensitivity-m2-access.json`
- `controls/coder/null-m2.md` — exactly zero bytes
- `controls/coder/helpful-requirement-coverage-m2.md`
- `controls/coder/helpful-requirement-coverage-m2.authorship.json`
- `evals/m2/coder-beneficial-sensitivity/master.json`
- `evals/m2/coder-beneficial-sensitivity/authorship.json`
- `evals/qualification/coder-beneficial-sensitivity-m2/oracle-variants.json`
- `evals/qualification/coder-beneficial-sensitivity-m2/validation.json`

The following brace expressions expand exactly to `01` through `05`. Each task
subtree may contain only `task.json`, `contract.md`, `check.py`, and `fixture/**`:

- `evals/m2/coder-beneficial-sensitivity/bug-{01,02,03,04,05}/**`
- `evals/m2/coder-beneficial-sensitivity/feature-{01,02,03,04,05}/**`
- `evals/m2/coder-beneficial-sensitivity/integration-{01,02,03,04,05}/**`
- `evals/m2/coder-beneficial-sensitivity/refactor-data-{01,02,03,04,05}/**`
### 3.1 Historical v0.4 implementation delta

The current code/config baseline is clean commit `b9c3a8e`. Implementation churn
is measured from the future clean commit containing the approved v0.4 document
amendment and no engineering changes. It may modify only
`src/mdseval/beneficial_sensitivity.py`, `tests/test_beneficial_sensitivity.py`,
`experiments/coder-beneficial-sensitivity-m2.json`, and `README.md`, and may add
only `experiments/coder-beneficial-sensitivity-m2-exclusions.json`. The new file
is the concise external exclusion/deviation record for the full
`coder-beneficial-sensitivity-m2-ada7a71` and
`coder-beneficial-sensitivity-m2-b9c3a8e` instance roots.
The target is at most 250 and the hard cap is 350 total textual churn (additions
plus deletions; untracked text counts as additions) across those five paths; the
final evaluator is at most 1,000 lines and its M2 test file at most 650. These are
ceilings, not entitlements. No binary, dependency, module, task, treatment,
checker, wrapper, runner, evidence-root, framework, statistic, or historical
artifact change is allowed. The exclusions JSON minimally records its schema,
the two full instance IDs, diagnostic-only reason, and inference exclusion; its
SHA-256 is bound by config, authoritative manifest, and final report. A need
outside this delta stops for a separate user decision.
## 4. Completed provenance and historical v0.4 lifecycle

Root orchestrates only: assign packets, enforce access, record hashes/counts,
integrate authorized local commits, and run gates. Root writes no implementation
content.

Steps 1–6 and the authorship/access text below record completed historical
provenance. They are read-only prerequisites, not active work or correction paths:

1. An access owner creates and hashes
   `experiments/coder-beneficial-sensitivity-m2-access.json` first. It contains
   exact role packets, identities, permitted paths, prohibited paths, starting
   source hashes, and attestation schema.
2. Helpful and task owners receive separate isolated packet-only directories,
   never repository worktrees. The directories contain only their protocol
   excerpts, output schema, and inputs expressly allowed below.
3. Returned `P`, tasks, checks, correct implementations, mutants, and authorship
   records are provisional and hash-locked; they are not protocol-frozen.
4. The independent task validator works in a third packet-only directory, records
   blockers without editing, and sees tasks/checks/solutions/mutants but not `P`
   or live outcomes.
5. The engine owner builds against the provisional hashes. One independent final
   adversarial auditor then reviews the complete implementation read-only.
6. Findings are consolidated once. Original owners receive only their original
   packet plus their own blockers and may make one correction pass. Mechanical
   closure follows; there is no second audit or correction.
The helpful owner receives only Protocol Sections 1, 3.1, and 4.1 plus size/content
rules. `P` is UTF-8 Markdown, at most 250 words and 4,096 bytes, general to the
construct, and may not mention evaluator, arms, controls, benchmarks, task
families, hidden evidence, APIs, filenames, literals, solutions, or test commands.
The helpful owner may not inspect tasks/checks/solutions/mutants, candidates, or
outcomes.
The task owner receives only Protocol Sections 1, 3, and 6 plus exact task paths.
It may not inspect exact `P`, candidate/champion files, or treatment outcomes. It
creates exactly 20 original, self-contained standard-library Python repositories:
five per stratum, one repository per task, three-to-five objectively checkable
requirements, plausible partial completion, and no shared problem/template or
underlying-task variant.
If model-assisted, every M2 treatment/task/engine author, task validator, and final
auditor uses `gpt-5.6-sol/high`. Requested identity, available observed metadata,
call count, role, and output hashes are disclosed in separate authorship/audit
receipts and never counted as subject calls. No cheap-model role is used.

The completed historical sequence was: five-path delta; focused then full tests; one final
read-only reviewer; at most one bounded code correction and its focused/full
validation; bounded commissioning; freeze the first passing clean commit;
external 300-case qualification once; fresh initialization; one-authorized
campaign; replay and terminal report. No treatment, task, checker, `P`, `H`,
wrapper, construct, scoring, or statistics correction is permitted.

Operator schedules and pre-unblinding evidence use opaque arm IDs only. At
authoritative initialization before any outcome, generate every nontrivial stage mapping exactly
once with standard-library system entropy plus a fresh nonce. Hash-bind every
mapping object in the initial manifest and campaign authorization; keep mapping
material outside operator/analyst packets until its outcome lock, then disclose.
“Sealed” means concealed and hash-committed, not plaintext in an accessible live
packet. Never regenerate or reuse nonce, entropy, or mapping bytes; a coincidentally
identical semantic permutation is allowed. Public deterministic seeds control
schedule order only.
Subjects see one file, never an arm ID. Analysis unblinds exactly once through a
create-once receipt; identity never reaches a qualitative judge because none runs.

## 5. Qualification and final receipt

Each `task.json` strictly binds ID, stratum, three-to-five requirement IDs,
contract/fixture/checker hashes, protected inputs, regressions, and the
requirement-to-negative-case matrix. A checker emits canonical JSON with
environment/self-check, each requirement, regressions, integrity, and `resolved`.
It checks observable behavior except where the prompt itself requires structure
and remains outside the subject workspace.
Using recorded `Path(sys.executable).resolve()` and `sys.version`, never hardcoded
`python`/`python3`, the qualifier runs pristine, two materially different correct
implementations, and two plausible partial/incorrect mutants three times each:
15 executions per task, 300 total. Pristine passes environment/self-checks and
fails at least one requested behavior; both correct states resolve; both mutants
fail for declared reasons; their union exercises every requested behavior;
correct states preserve regressions; all repeats are identical. Symlink, hidden
path, reused repository, nondeterminism, truncation, or hash drift fails.
All 20 frozen tasks must pass; none may be corrected, substituted, or repaired.
After commissioning PASS, the qualifier automatically creates the non-user
`<output>/freeze-record.json`, binding the PASS hash and exact clean commit, before
any checker execution. External qualification verifies
that commit and commissioning hash, executes the 300 cases once outside any live
root, and emits a complete receipt binding all 300 raw record hashes/results, its
terminal result, config/evaluator/tests/runtime hashes, commit, commissioning
PASS, and freeze record. Fresh `initialize` validates and copies that envelope
into a new authoritative root and executes zero checkers. Freeze and qualification
records are internal provenance, not either of the two user live authorizations.
## 6. Frozen all-20 schedules, selection, and retry

Config is strict and has no CLI runtime override. It pins all protocol settings,
hashes, seeds, invalidity table, and caps. Current-runtime strictness comes from
the frozen config plus receipt hash, not a model-name branch in evaluator logic.
Any changed/non-Sol design or requested override fails validation.

Before authoritative initialization, freeze base and fallback schedules for all
20 task IDs for every scored stage. Calibration contains six rounds of all 20 under null with task order varied
per round. The control master has, for every task, one three-arm opaque unit. The
helpful master has four rounds and one consecutive opaque pair per task/round.
After null-only selection, derive executable control/helpful schedules solely by
filtering the frozen all-20 masters to the selected 16; never rerandomize.

Use these UTF-8 canonical SHA-256 sentinels:

- task-order key: `seed|stage|round|task_id|BLOCK`;
- arm-order key: `seed|stage|round|task_id|opaque_arm_id|ARM`;
- block sentinel: hash of the ordered base plus fallback slot IDs for one
  task-stage block; and
- stage-order sentinel: hash of the ordered 20 block sentinels.

The initial manifest records every all-20 sentinel. A filtered-schedule receipt
records selected IDs, source stage sentinel, ordered filtered slots, and its hash.
Calibration/filtering seed is `coder-m2-selection-20260810-v1`; schedule seed is
`coder-m2-schedule-20260810-v1`.
The arm-blind invalidity table is frozen before calls. Only a listed evaluator,
machine, authentication, or service failure before a usable subject turn permits
replacement. Every nonlisted failure is `Y=0`, including timeout, false completion,
missing deliverables, agent-caused failure, post-usable nonzero exit, and failed
checks. No operator discretion may inspect arm or outcome.
For the first allowed invalidity in a live stage, complete unaffected base slots,
mark every original observation in that task-stage block `SUPERSEDED`, exclude all
of them, and run exactly its frozen replacement at stage end: six calibration,
three control, or eight helpful calls. Any second invalid task block in that stage
or invalid replacement is `INVALID`. Commissioning probes are governed
separately by Section 9 and are not scored.
Resume is allowed only after an intact completed scheduled attempt in calibration,
after a complete three-arm task unit in controls, or after a complete consecutive
pair in helpful. A partial unit/attempt, changed remaining schedule, missing byte,
or failed sentinel is `INVALID`. Whole task-stage supersession still governs retry.

| Stage | Base | Maximum fallback | Cumulative maximum |
| --- | ---: | ---: | ---: |
| Null calibration: 20 x 6 | 120 | 6 | 126 |
| Controls: 16 x 3 | 48 | 3 | 177 |
| Helpful: 16 x 8 | 128 | 8 | 313 |
| **Total** | **296** | **17** | **313** |

Every launched authoritative subject attempt counts, including failed, invalid,
interrupted, and superseded attempts. No billing estimate exists.

## 7. Selection, statistics, power, and verdicts

Calibration uses `N` only. A task is eligible at one through five successes of
six. Select four per stratum by
`(abs(successes-3), sha256(selection_seed || task_id))`. Fewer than four eligible
in any stratum stops `SENSITIVITY_NOT_DEMONSTRATED`; never add, edit, substitute,
or recalibrate. The create-once selected-subset receipt records all 20 counts,
eligibility/ranks, selected IDs/hashes/strata, and current runtime identity. It is
separate from the immutable master; calibration is never scored evidence.

Before controls, run 100,000 simulations with `random.Random(20260811)`, selected
tasks in ascending ID order, rates `(successes+1)/8`, per-task `+0.30` capped at
1.00, and four `P` then four `N` draws per task/simulation. Apply the helpful joint
gate; power below 0.80 stops. Before any live call, reproduce every Protocol 10.2
grid value within 0.005 with one continuous `random.Random(20260810)` stream and
its exact listed draw order. These are helpful-gate-only conditional power, not
end-to-end power or power for a +0.20 effect.

For task `t`, let `p[m,t]` be fresh-attempt success probability under the frozen
runtime. The finite selected-set estimand is
`theta[A-B] = mean_t(p[A,t]-p[B,t])`; estimate it by
`hat_Delta = mean_t(mean(Y[A,t,*])-mean(Y[B,t,*]))`. Claims condition on the
realized selected diagnostic set and concern the observed estimate, not proof
that true `theta >= 0.20`.

Use exact rational `d_t`. Remove zeros only from sign enumeration; count all sign
assignments of absolute nonzero effects and report nonzero count, exact fraction,
and two-sided probability of an absolute signed sum at least observed. Integer
dynamic programming may count the enumeration but must equal brute force for
every tested `k <= 16`. Exactness requires the sharp taskwise distributional
no-effect null, independent equiprobable task-block arm swaps, and no inter-task
interference; it is not an exact test of weak `theta=0`.

The directional rule is observed effect `>= +0.20` and exact two-sided
`p <= 0.05`: A/A permits neither direction and reports `NO_FALSE_WINNER`, never
equivalence; fresh `N1-H` must pass without pooling `N2`; and `P-fresh N` must
pass over four attempts/arm (minimum attainable `13/64 = 0.203125`).

For all three comparisons, a descriptive 95% stratified task bootstrap uses
`random.Random(20260812)`, 100,000 resamples, four tasks with replacement per
stratum, and sorted zero-based endpoints 2,499 and 97,500. It changes no gate and
supports no population claim. Report mechanically verified requirement coverage
and protocol secondary metrics separately; no composite score or judge override.

## 8. Minimal authoritative evidence and replay

For one predeclared authoritative instance ID, exactly two persisted create-once
roots exist:

1. `runs/<instance-id>/live` — qualification, initial manifest, attempts, later
   receipts, stage reports, and final report; and
2. `runs/<instance-id>/replay` — one offline replay output.

No arbitrary root is accepted. Neither may preexist at authoritative initialization;
later stages only add exclusive-create entries to the initialized live root.
Offline work and commissioning use one reusable external diagnostic root, never
these roots. Each launched probe exclusively creates
`<root>/<exact-clean-descendant-commit>/probe-N/`; it contains only labeled
non-authoritative raw JSONL, stderr, final response, runtime/tree result, and PASS
if earned—no scientific manifest, receipt DAG, replay, or instance.

Fresh initialization copies the validated commissioning/freeze/qualification
envelope and creates the initial manifest once. It binds those hashes, all
artifact/treatment and fresh mapping hashes, schedules/fallbacks/sentinels, seeds,
runtime/Python identities, invalidity table, wrapper, roots, and 296/313 caps.
Never mutate it. Later campaign authorization, unblinding, selection,
filtered-schedule, power, and stage results
are separate create-once receipts; each subsequent stage receipt references the
manifest and all prerequisite receipt hashes. Earlier evidence is never rewritten.
There are no block receipts and no new ledger.

Each attempt directory is exclusive-create and preserves the existing runner raw
JSONL/stderr/final, launch/runtime IDs, status, hashes before/after, checker
JSON/stdout/stderr, `capture_git` result, duration/timeout, parsed usage/commands,
failed and verification commands, tool calls, changed/added/removed paths, and
patch size. Call `audit_final_subject_tree` before the external checker/capture.
Reconstruct the final state only from frozen fixture plus captured diff/untracked
content; do not duplicate a workspace snapshot. Any capture truncation is
`INVALID`.

Commissioning alone requires exact final bytes and an unchanged synthetic tree;
authoritative coding patches are expected and external checkers/capture score
them. Structural row validation checks schema, slot, and evidence completeness.
A structurally complete row is published and deterministically classified under
the predeclared `Y=0`, infrastructure-invalid, or campaign-`INVALID` rule; outcome,
identity, response bytes, timeout, or tree-integrity failure never makes it throw.
Only corrupt/incomplete publication stops as preserved incomplete and is never
hand-repaired, resumed, or reused.

Replay takes only frozen config and instance ID, validates exclusive roots,
manifest/receipt references, all hashes/sentinels, attempt ordering, deletions,
tampering, supersession, and caps, then creates the one replay root and regenerates
byte-identical JSON/Markdown without importing/instantiating a live runner or
using authentication, model, network, or judge. Reports include all calibration,
selection, task/arm/repeat outcomes, `d_t`, macro effect, exact p, bootstrap,
power, coverage, secondary metrics, invalid/superseded calls, deviations, gates,
and the exact claim boundary.

## 9. CLI, commissioning, tests, audit, and commits

Python code invokes checkers/helpers with `sys.executable`; receipts record its
resolved path and version. README commands use `python3` for this repository/Mac.
The module exposes strict `validate`, `qualify`, `verify-power`, `simulate`,
`commission`, `initialize`, `run-stage --stage calibration|controls|helpful`, and
`replay`.
`run-stage` rejects missing campaign authorization, out-of-order/prerequisite stages, reused
roots/attempt paths, changed hashes/sentinels, and every model/reasoning/timeout/
network/parallelism/output override. `replay` rejects any live option.

`commission` creates a disposable sentinel and its zero-byte `CODER.md` locally;
it never imports M2 `N`, labels, tasks, treatments, or artifacts. Every probe uses
a fresh discarded session. Its authorization binds the starting clean commit,
five engineering paths and cumulative 350-churn cap, fixed config/runtime/CLI,
one reusable diagnostic root, at most three launched probes, and at most two
concrete repair cycles. Each probe path follows Section 8, records its exact clean
descendant commit and cumulative start-to-current diff, and, for `N>1`, cites the
prior concrete failure and proves relevant bytes changed. Unchanged reruns are
forbidden. A prelaunch/invocation-only failure with no model call or evidence may
be corrected without consuming a probe but remains within the repair limit.

Commissioning PASS binds the exact commit; config/evaluator/tests/wrapper hashes;
resolved CLI path/hash/version; exact command, strict config, requested
`gpt-5.6-sol/high`, and isolated-profile status without credentials; raw event,
stderr, and final hashes; expected no-trailing-newline bytes
`IMPLEMENTED\nSMOKE_READY`; and unchanged sentinel-tree result. Service identity
is collected only from `$.model`, `$.reasoning_effort`, `$.service.model`, and
`$.service.reasoning_effort` on event types `session.config`, `turn.started`, or
`response.completed`—never user/assistant/tool/command payloads. Collect all:
none is nonfatal `not_reported`, all consistent with the request is
`reported_match`, and any contradiction is failing `reported_mismatch`; none is
provider attestation. The first PASS ends commissioning. Repairs then require
focused and full tests; caps, repeated cause, no progress, or expansion stop it.

`tests/test_beneficial_sensitivity.py` is table-driven and stays within 650 lines:

| Required category | Cases |
| --- | --- |
| Config/hash/path | strict keys/hashes/safe paths; reject non-Sol design and all overrides |
| Blinding | opaque schedules/evidence; mapping unavailable until locked-outcome unblinding |
| Scheduling/caps | frozen all-20 filtering, balance, freshness, ordering, 296/313, stage order |
| Retry | every listed path, every nonlisted failure as `Y=0`, second invalid, invalid replacement |
| Objective | resolve iff every requirement, regression, integrity passes; no judge override |
| Evidence/replay | commissioning separation; terminal invalid attempts; corruption, tamper/deletion/reorder detection; exact resume; byte-identical replay |
| Runtime/offline | `sys.executable`; exact no-newline sentinel; frozen client identity; match-if-reported semantics; offline code never instantiates live runner |
| Analysis/history | exact selection, power grid, sign test, bootstrap endpoints, all verdicts, unchanged V2 hashes/tests |

The prior access/treatment/task/validator/engine packets, implementation
authorization, audit, and correction are completed read-only provenance. They
grant no current role, edit, review loop, or live authority. Root does not code.

For v0.4, one final read-only reviewer checked only the five-path delta against
that amendment; at most one bounded engineering correction could resolve its
in-scope blockers. It then followed the historical sequence in Section 4. An
unresolved blocker stopped; no audit loop or historical-artifact correction existed.

## 10. Offline gates, live authorization, and stopping

All commands are offline and use a temporary directory outside the repository:

```bash
python3 -m unittest discover -s tests -v
M2_OFFLINE_DIR="$(mktemp -d)"
PYTHONPATH=src python3 -m mdseval.beneficial_sensitivity validate \
  --experiment experiments/coder-beneficial-sensitivity-m2.json
PYTHONPATH=src python3 -m mdseval.beneficial_sensitivity verify-power \
  --experiment experiments/coder-beneficial-sensitivity-m2.json
PYTHONPATH=src python3 -m mdseval.beneficial_sensitivity simulate \
  --experiment experiments/coder-beneficial-sensitivity-m2.json \
  --output "$M2_OFFLINE_DIR/simulation"
git diff --check
git status --short
```

Historical gate order: five-path delta; focused/full tests; one final review and at
most one correction; bounded commissioning; automatic freeze of its first PASS
commit; external 300-case qualification once; fresh zero-checker initialization;
campaign authorization; calibration; controls only after selection/power PASS;
helpful only after both controls PASS; replay and terminal report.

Commissioning and authoritative contracts, with no output or runtime override:

```bash
PYTHONPATH=src python3 -m mdseval.beneficial_sensitivity commission \
  --experiment experiments/coder-beneficial-sensitivity-m2.json \
  --starting-commit <clean-development-commit> \
  --diagnostic-root <one-reusable-external-root> \
  --authorization-receipt <commissioning-authorization.json>
PYTHONPATH=src python3 -m mdseval.beneficial_sensitivity qualify \
  --experiment experiments/coder-beneficial-sensitivity-m2.json \
  --verified-commit <same-frozen-commit> \
  --commissioning-pass <external-commissioning-pass.json> \
  --output "$M2_OFFLINE_DIR/qualification"
PYTHONPATH=src python3 -m mdseval.beneficial_sensitivity initialize \
  --experiment experiments/coder-beneficial-sensitivity-m2.json \
  --instance <fresh-instance-id> --verified-commit <same-frozen-commit> \
  --qualification-receipt "$M2_OFFLINE_DIR/qualification/qualification-receipt.json"
PYTHONPATH=src python3 -m mdseval.beneficial_sensitivity run-stage \
  --experiment experiments/coder-beneficial-sensitivity-m2.json \
  --instance <instance-id> --stage <calibration|controls|helpful> \
  --authorization-receipt <campaign-authorization.json>
PYTHONPATH=src python3 -m mdseval.beneficial_sensitivity replay \
  --experiment experiments/coder-beneficial-sensitivity-m2.json \
  --instance <instance-id>
```

Commissioning and campaign are the only user live authorizations. Campaign schema
`mdseval.coder-beneficial-sensitivity-m2-campaign-authorization-v1` binds exact
instance, commit, manifest/config/runtime hashes, every mapping hash, ordered
stages, mechanical gates, frozen fallbacks, and 313 ceiling. One stage runs per
invocation; after mechanical PASS the operator automatically invokes the uniquely
eligible next stage with identical authorization bytes—no chat gate, outcome-based
choice, mapping regeneration, repair, or second campaign. Resume is only at the
exact Section 6 block boundaries. Manual noncompletion earns no favorable verdict.
A prelaunch environment failure that makes no call and mutates no authoritative
evidence permits invocation-only correction; after launch, frozen rules control.
Freeze, qualification, and stage receipts are non-user internal provenance.

Stop and preserve evidence on failed baseline/access/authorship/oracle/hash/
wrapper/isolation/runtime/balance/evidence/receipt/sentinel gate; frozen-byte
change; fewer than four eligible tasks per stratum; power `<0.80`; second invalid
block in a stage; invalid replacement; failed A/A or harmful gate; invalid resume;
cap/allowlist breach; a 314th call would launch; or helpful completion. Never retune, substitute,
change seeds/checkers, add a control, selectively retry, or repeat until pass.

## 11. Narrow portability and handoff

Future cheap-model portability exists through exactly two seams: runtime identity
is frozen config/receipt data passed to the existing runner rather than hardcoded
evaluator branching, and the immutable 20-task master is separate from the
runtime-bound selected-16 receipt. Current config/receipts accept only
`gpt-5.6-sol/high`. Another model requires a separately versioned future
experiment, calibration, subset, power, evidence roots, and authorization; no
cross-model command, comparison, pooling, ranking, or cheap-model machinery is
implemented now.

Authoritative-campaign readiness requires successful commissioning; all 20 tasks
and 300 qualification executions passing once on the same frozen commit; the
protocol grid reproduced; tests/fake replay green; access/authorship complete;
one implementation audit and optional correction mechanically closed; all
paths/caps satisfied; historical V2 and excluded diagnostic roots unchanged; and
deterministic proof of 296/313 ceilings. Milestone 2 is administratively complete
on one allowed verdict plus offline replay and scientifically passes only on
`SENSITIVITY_DEMONSTRATED`.

## 12. Frozen historical v0.4.1 capture-integrity remediation

This section governed the completed v0.4.1 remediation and no longer supersedes
Section 13. It did not change the scientific construct, tasks, treatments,
schedules, outcomes, statistics, gates, or claim boundary.

### 12.1 Frozen failure and diagnosis gate

The authoritative instance
`coder-beneficial-sensitivity-m2-v04-4ae8619` is permanently `INVALID`. Its 120
calibration calls and all live evidence remain immutable, excluded from every
future estimate, selection, power calculation, and qualification. Its existing
replay root is equally immutable; v0.4.1 may not complete or reinterpret it.

Four durably published rows had `mechanical_integrity=false` with
`infrastructure_invalid=false`: launch indices 20, 43, 79, and 102, all
`refactor-data-01`, rounds 1, 3, 4, and 6. In each corresponding
`attempts/calibration/calibration_base_r{1,3,4,6}_refactor-data-01_K0/runner/events.jsonl`,
line 8 ends immediately after `[REDACTED]` and is invalid JSON. No additional
historical payload inspection is needed or permitted for this remediation.

The historical runner did not preserve pre-redaction stdout, so the INVALID
evidence alone cannot prove whether the process emitted a truncated line. Before
implementation, reproduce the exact structural signature offline with a
synthetic, valid JSON event whose string contains escaped `key="id"`. Record
whether it parses before and after current `Redactor.text`:

- valid before and invalid after, ending after `[REDACTED]`, demonstrates a
  deterministic redactor defect capable of this signature and permits only the
  prospective fix below; it does not establish historical causality;
- no matching reproduction stops for a new user decision.

Raw-process truncation versus redactor corruption remains unresolved for all
four old rows. They remain irreducibly INVALID and are never laundered.

### 12.2 Exact implementation envelope

The engineering baseline is the future clean commit containing this accepted
plan amendment and no engineering edits; record its exact hash before work. No
new files are allowed. Modify at most these seven paths:

- `src/mdseval/capture.py`
- `src/mdseval/runner/codex_cli.py`
- `src/mdseval/beneficial_sensitivity.py`
- `tests/test_capture.py`
- `tests/test_runner.py`
- `tests/test_beneficial_sensitivity.py`
- `experiments/coder-beneficial-sensitivity-m2.json`

Target at most 180 and hard-cap 240 additions plus deletions from that commit.
The existing 1,000-line evaluator and 650-line M2-test ceilings remain. These are
ceilings, not entitlements. No authoritative task, fixture, checker, treatment,
wrapper, prompt, protocol statistic, seed, schedule, cap, mapping, dependency,
module, framework, dashboard, optimizer, model, historical evidence, or unrelated
path may change.

Config changes are binding-only. In
`experiments/coder-beneficial-sensitivity-m2.json`, replace
`protocol.implementation_plan_sha256` with the accepted Section 12 plan-file SHA
and update the evaluator's expected binding; keep the scientific protocol SHA
and version unchanged. Hash-bind `src/mdseval/capture.py`,
`src/mdseval/runner/codex_cli.py`, `src/mdseval/beneficial_sensitivity.py`,
`tests/test_capture.py`, `tests/test_runner.py`, and
`tests/test_beneficial_sensitivity.py`. The manifest and clean commit bind the
config itself. At every stage entry, before runner construction, require current
config SHA to equal `manifest.config_sha256` and all six files to match both the
config and `manifest.governed_hashes`. Add no receipt or provenance framework.

If the matching reproducer confirms the prospective defect, add one event-stream
sanitizer to existing capture code. For each raw stdout line, parse JSON first,
apply `Redactor.object` to the parsed value, and serialize it back to JSON. A
valid raw line must remain valid after redaction. A raw malformed line must stay
malformed at the same line position after safe text redaction; it must never be
converted into a usable event. Persist no unredacted stdout. `CodexCLI.run` uses
this helper instead of applying `Redactor.text` to the complete JSONL stream.

Use a distinct `fatal_evidence_defect` predicate, never
`mechanical_integrity=false`, for fail-fast behavior. It is true only for a
malformed event stream, structurally incomplete/noncanonical row, incomplete
capture/publication, explicit identity contradiction, or another evidence defect
predeclared in frozen config. Ordinary structurally valid task, checker,
mechanical, and agent-caused failures remain `Y=0` and never stop or censor the
schedule. The four legacy malformed streams are fatal evidence defects.

At `run-stage` entry/resume and after each exclusively created row, validate every
durable row in order before dispatch. This fatal scan precedes ordinary
block-boundary resume validation. On any `fatal_evidence_defect`, launch no new
call or fallback; publish the partial INVALID lock, unblinding/stage receipts,
terminal evidence/report with the fatal reason, then support byte-identical
JSON/Markdown replay. Infrastructure-invalid replacement semantics are unchanged.
Operator monitoring reports completed, infrastructure-invalid, and fatal-evidence
counts; it never treats ordinary `mechanical_integrity=false` as fatal.

For v0.4.1, the Section 9 commissioning envelope is superseded: use a fresh,
empty external diagnostic root; set `engineering_paths` to exactly the seven
Section 12 paths, `churn_cap=240`, `max_probes=1`, and `max_repairs=0`. Never
reuse a v0.4 diagnostic root. Validate this envelope and root before constructing
the runner; any mismatch or second invocation is a zero-call rejection.

### 12.3 Gates, validation, and stopping

The completed remediation proceeded in this order:

1. Hash and inventory the v0.4 terminal evidence and existing replay root; never
   write beneath that instance.
2. Pass the offline cause-reproduction gate in Section 12.1.
3. Implement only Section 12.2 within the seven-path and 240-churn caps.
4. Run focused tests proving valid structured redaction and malformed-line
   detection; ordinary mechanical failures stay `Y=0`; and table-driven config/
   six-file mutations reject before runner construction with zero dispatch. A
   crash/resume with a durable fatal row in an incomplete controls or helpful unit must
   terminalize before boundary validation, launch zero calls, and replay JSON/MD
   byte-identically. Infrastructure fallback remains unchanged. Table-driven
   commissioning tests reject `max_probes != 1`, `max_repairs != 0`, a nonempty
   diagnostic root, and a second invocation before runner construction.
5. Run `python -m unittest discover -s tests -v`, the existing M2 offline
   validation/simulation commands, `git diff --check`, and path/churn checks.
6. Complete one consolidated read-only review and only in-scope corrections;
   focused validation precedes one full-suite rerun after each correction.
7. Create one exact clean v0.4.1 engineering commit only after all offline gates
   pass; its config and manifest bindings freeze the capture and runner bytes.
8. Run exactly one predeclared non-authoritative commissioning call on that
   commit. Only its synthetic contract may request one harmless read-only command
   containing literal `key="id"`; every authoritative task, treatment, wrapper,
   and prompt stays byte-frozen. PASS requires the persisted redacted event to
   contain `[REDACTED]`, parse cleanly, retain its surrounding event fields, and
   satisfy the existing exact final-byte, identity, and tree gates.
9. Only that PASS freezes the new commit. Then run a new 300-case qualification
   once, initialize a new instance ID, and obtain one new campaign authorization
   before starting calibration from call 1. Reuse none of the v0.4 outcomes,
   mappings, receipts, nonce material, or instance paths.

Stop without another live call on diagnosis ambiguity, any offline or review
blocker, cap/allowlist breach, the commissioned call's failure, or altered frozen
inputs. A second live validation, design beyond the reproducer-bounded fix, any
protocol/scientific change, added dependency/module, expanded
paths/churn, historical replay or evidence mutation, or a new authoritative
campaign requires a new user decision. Ordinary in-scope offline corrections do
not. The same root cause after two targeted corrections stops under `AGENTS.md`.

Acceptance evidence is the cause reproduction; exact seven-path diff and churn;
focused and full command results; unchanged v0.4 live and replay hashes;
review disposition; clean commit hash; and one external commissioning PASS hash.
Qualification, fresh initialization, and campaign receipts remain separate later
gates and cannot rescue a failed predecessor.

## 13. Rapid instrument development before confirmation

### 13.1 Objective and authority

The objective is to discover a repeatable omission-sensitive task recipe before
building another pool. This development is neither an M2 verdict nor an
instruction-file comparison.

This plan self-authorizes no action. One bounded user authorization may cover the
full lab: three batches, 18 planned usable attempts, and at most two eligible
replacement launches per batch. It specifies exact roles, paths/churn caps,
evidence root, total launch cap, and one intended-confirmation target
model/runtime configuration across the lab: model/reasoning effort,
harness/wrapper bytes, timeout, tools, sandbox/network, CLI/runtime, prompt
construction, and repository preparation. Frozen mechanical rules advance
batches without new chat. Any outcome-relevant configuration change needs new
authority, restarts the consecutive-batch sequence, and makes prior batches
non-transferable to PASS while preserving their evidence. Expansion or a live
treatment comparison also needs new authority.

Task A v2/v3 evidence stays immutable, non-transferable, and outside any resumed
lineage; neither reached a usable subject attempt.

### 13.2 Phase A: repeatable engineering smoke

Before live calls, pass a repeatable zero-live-call smoke with a synthetic
fixture. Cover repository preparation, tools/paths, byte hashes, manifest,
wrapper/checker invocation, capture, evidence writing, and deterministic replay.
Repair and repeat; pre-exposure failures consume no version or attempt. Preserve
reproducible diagnostics.

### 13.3 Phase B: disposable two-task microbatches

A batch has exactly two disposable, different-family tasks, one task/checker
implementer, and one fresh independent contract-only solver/reviewer. The latter
submits implementations from public packets before inspecting checkers and
gates. Neither role receives current or candidate `CODER.md` content or outcomes.

Before each batch, freeze a concise versioned generation recipe and SHA-256
defining requirement count/dispersion, primary/secondary structure, task-family
criteria, and subject packet/wrapper construction. The two consecutive batches
used for recipe freeze must use byte-identical recipe bytes/hash. Any recipe
change starts a new consecutive-batch sequence and makes earlier batches
non-transferable to PASS without erasing evidence.

Before the first target launch, freeze each requirement's mapped assertions,
PASS predicate, and observable-omission predicate, plus regression/integrity pass
predicates and the infrastructure predicate. Each task then passes this minimal
offline gate:

1. Every public requirement maps to a checker assertion. Every score-affecting
   assertion—behavioral, structural, exact-byte, documentation, regression, or
   integrity—traces to explicit public text. Separately identified nonfunctional
   environment/integrity checks may lack that trace only when they add no scored
   behavior.
2. A reference implementation and the independent contract-only implementation
   both pass.
3. One omission mutant per requirement fails only its mapped requirement and
   fires its omission predicate; every nonmapped requirement and every
   regression/integrity check passes.
4. Two fresh-copy replays produce identical canonical results and leave all
   protected inputs unchanged.

A requirement is PASS iff all mapped assertions pass. An attempt is RESOLVED iff
all requirements and regression/integrity checks pass. A valid nonresolution is
omission-only iff every failed requirement fires its frozen omission predicate
and no regression/integrity failure occurs; every other valid failure is
wrong-failure-mode.

Gate failures are retryable before target exposure. Freeze each task's public
packet and checker at its first target launch; do not patch or rerun it as a
revised version within the batch.

Run three usable null-treatment target attempts per task in fresh workspaces,
each with a present zero-byte `CODER.md`: six per batch. Usable means captured
subject output and checker evidence suffice for frozen classification. At most
two replacement launches per batch are allowed, only when the frozen
infrastructure predicate fires before usable output. Preserve raw evidence and
reason. A timeout is usable only when frozen evidence mechanically scores it; an
unscoreable timeout is replaceable only under that preceding rule. Poor solutions,
failed checks, and other scoreable outcomes are usable and never selectively
retried.

For R requirements, q is passed requirement observations divided by 3R, and s is
the RESOLVED count across three usable attempts. Apply labels in order:

1. invalid: a trace, determinism, protected-input, or evidence defect prevents
   valid scoring;
2. wrong-failure-mode: any valid nonresolution is not omission-only;
3. promising: 0.55 <= q <= 0.90, s is 1 or 2, and every valid nonresolution is
   omission-only;
4. ceiling: s is 3, or s is 1 or 2 and q > 0.90;
5. floor: s is 0, or s is 1 or 2 and q < 0.55.

A bad task ends only itself; it does not stop development, permit changes to an
exposed version, or erase evidence.

Recipe freeze requires two consecutive completed batches, each with at least one
promising task, at least two families across those tasks, and no checker defect.
Complete compact evidence/accounting for both makes Section 13 development PASS,
not an M2 sensitivity verdict. Without that replicated signal after three
batches and 18 planned usable attempts, stop live discovery and return offline.
Three batches are the ceiling; an incomplete batch authorizes no extra live work.

### 13.4 Evidence and confirmation boundary

Each batch preserves one compact manifest covering authorization, roles,
families, hashes, runtime, launches, and replacement reasons; raw subject/checker
evidence; and one short summary. Create no per-role authorization or receipt
forest.

All exposed or outcome-informed prototypes and authors are development-only.
Discovery uses only null/no-coder; current and candidate files stay hidden and
untested. After recipe freeze, scale fresh development tasks only in pairs and
use measured admission/promising yield to plan fresh confirmatory inventory.
Base final pool size, feasibility, and power on measured task-level evidence,
not inherited rate assumptions.

Only then may fresh confirmatory authors create fresh tasks under a new bounded
authorization. Apply full two-blind-solver admission, immutable hashes, frozen
schedules, treatment blinding, deterministic replay, and provenance to those
tasks. Bare/current/candidate comparisons begin only after that fresh suite and
its evidence-preserving runner are frozen.
