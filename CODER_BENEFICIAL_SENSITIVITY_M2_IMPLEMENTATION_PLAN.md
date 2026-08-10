# CODER beneficial-sensitivity Milestone 2 implementation plan

Status: proposed correction; one offline implementation authorization and four
stage-specific live authorizations are required below
Scientific authority: `CODER_BENEFICIAL_SENSITIVITY_PROTOCOL.md` version 0.2
Roadmap stage: Milestone 2 only — demonstrate beneficial measurement sensitivity

## 1. Authority, outcome, and scope

For every new Milestone 2 action, this plan supersedes
`coder-outcome-evaluator-v2-implementation-plan.md`. The older plan, repairs,
code, experiment, and raw evidence remain immutable historical evidence only.
This is the sole active Milestone 2 implementation plan.

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
Requested and service-observed model/reasoning identity must both be present and
match; otherwise the experiment is `INVALID`.
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

The historical module cannot express smoke, 20-by-6 null calibration,
model-bound 16-task selection, three stage-specific fallbacks, four helpful
rounds, 297/314 calls, power, or stratified bootstrap without changing historical
replay. One new `beneficial_sensitivity.py` module is therefore allowed. It is a
thin orchestrator over the named functions, not a runner, capture/evidence
framework, judge, or generalized experiment platform. Copying their logic is a
cap violation and blocker.
## 3. Exact path allowlist and hard budgets

No packet may touch a path absent below. `/**` is limited to the stated subtree;
every generated or hand-written line counts. Existing unrelated dirty/untracked
paths remain untouched.

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

### Modify

- `README.md` — exact M2 offline, staged-live, stop, and replay commands only

### New

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
Added physical lines are counted from the authorized starting commit; deletions
do not offset additions. Blank/comment lines and generated/copied fixture/JSON
lines count. There is no hidden exception.

| Category | Expected target | Hard cap |
| --- | ---: | ---: |
| Production module | <=500 | 600 |
| Tests | <=550 | 650 |
| Full 20-task corpus, checkers, oracle, validation | <=2,400 | 2,750 |
| Config, README, treatments, access/authorship | <=250 | 300 |
| **Total** | **<=3,700** | **4,300** |

Any category/total breach stops before write or commit for a new user decision.
Expected targets are below caps; unused capacity cannot justify work or scope.
## 4. Access, provisional artifacts, and final freeze

Root orchestrates only: assign packets, enforce access, record hashes/counts,
integrate authorized local commits, and run gates. Root writes no implementation
content.

Sequence is mandatory:

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
7. After closure, freeze final artifact bytes in an authorized clean local commit;
   perform post-freeze alignment (any gap stops without edits); then run the authoritative 300-case qualification on that exact commit, issue its create-once receipt,
   create the initial manifest, and stop for smoke authorization.
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

Operator schedules and pre-unblinding evidence use opaque arm IDs only. Each
stage mapping and hash is created before schedules but withheld from the operator
and analyst until that stage's mechanical outcomes are locked.
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
All 20 must pass after the sole correction; no task is substituted or repaired.
After mechanical closure, freeze final bytes in an authorized clean local commit
and perform post-freeze alignment; any gap stops without edits. Then run all 300
cases on that exact commit and issue the create-once receipt binding results,
identities, final hashes/config/commit; create the manifest and stop for smoke.
## 6. Frozen all-20 schedules, selection, and retry

Config is strict and has no CLI runtime override. It pins all protocol settings,
hashes, seeds, invalidity table, and caps. Current-runtime strictness comes from
the frozen config plus receipt hash, not a model-name branch in evaluator logic.
Any changed/non-Sol design or requested override fails validation.

Before smoke, freeze base and fallback schedules for all 20 task IDs for every
stage. Calibration contains six rounds of all 20 under null with task order varied
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
or invalid replacement is `INVALID`. Smoke is never retried.
Resume is allowed only after an intact completed scheduled attempt in calibration,
after a complete three-arm task unit in controls, or after a complete consecutive
pair in helpful. A partial unit/attempt, changed remaining schedule, missing byte,
or failed sentinel is `INVALID`. Whole task-stage supersession still governs retry.

| Stage | Base | Maximum fallback | Cumulative maximum |
| --- | ---: | ---: | ---: |
| Authenticated smoke | 1 | 0 | 1 |
| Null calibration: 20 x 6 | 120 | 6 | 127 |
| Controls: 16 x 3 | 48 | 3 | 178 |
| Helpful: 16 x 8 | 128 | 8 | 314 |
| **Total** | **297** | **17** | **314** |

Every launched attempt counts, including failed, invalid, interrupted, and
superseded attempts. No billing estimate exists.

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

## 8. Minimal immutable evidence and replay

For one predeclared instance ID, exactly two persisted create-once roots exist:

1. `runs/<instance-id>/live` — qualification, initial manifest, attempts, later
   receipts, stage reports, and final report; and
2. `runs/<instance-id>/replay` — one offline replay output.

No arbitrary root is accepted. Neither may preexist at instance initialization;
later stages only add exclusive-create entries to the initialized live root.
Offline provisional work uses a temporary external directory, not evidence.

After final qualification and before smoke, create the initial manifest once. It
binds final artifact/receipt hashes, unordered treatment hashes and mapping hash,
all-20 schedules/fallbacks/sentinels, seeds, runtime/Python identities, invalidity
table, wrapper, roots, and 297/314 caps. Never mutate it. Later access,
authorization, unblinding, selection, filtered-schedule, power, and stage results
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

Replay takes only frozen config and instance ID, validates exclusive roots,
manifest/receipt references, all hashes/sentinels, attempt ordering, deletions,
tampering, supersession, and caps, then creates the one replay root and regenerates
byte-identical JSON/Markdown without importing/instantiating a live runner or
using authentication, model, network, or judge. Reports include all calibration,
selection, task/arm/repeat outcomes, `d_t`, macro effect, exact p, bootstrap,
power, coverage, secondary metrics, invalid/superseded calls, deviations, gates,
and the exact claim boundary.

## 9. CLI, smoke, tests, audit, and commits

Python code invokes checkers/helpers with `sys.executable`; receipts record its
resolved path and version. README commands use `python3` for this repository/Mac.
The module exposes strict `validate`, `qualify`, `verify-power`, `simulate`,
`run-stage --stage smoke|calibration|controls|helpful`, and `replay`. `run-stage`
rejects missing stage authorization, out-of-order/prerequisite stages, reused
roots/attempt paths, changed hashes/sentinels, and every model/reasoning/timeout/
network/parallelism/output override. `replay` rejects any live option.

Smoke uses `N` in a fresh prepared repo and an embedded frozen contract requiring
exact final response `IMPLEMENTED\nSMOKE_READY`, with no changes. It passes only on
exit zero, no timeout/interruption, exact response, untouched tree, complete
capture, and matching requested/observed `gpt-5.6-sol/high`. Any failure is
`INVALID` and stops; it is not retried.

`tests/test_beneficial_sensitivity.py` is table-driven and stays within 650 lines:

| Required category | Cases |
| --- | --- |
| Config/hash/path | strict keys/hashes/safe paths; reject non-Sol design and all overrides |
| Blinding | opaque schedules/evidence; mapping unavailable until locked-outcome unblinding |
| Scheduling/caps | frozen all-20 filtering, balance, freshness, ordering, 297/314, stage order |
| Retry | every listed path, every nonlisted failure as `Y=0`, second invalid, invalid replacement |
| Objective | resolve iff every requirement, regression, integrity passes; no judge override |
| Evidence/replay | exclusive creation, tamper/deletion/reorder detection, exact resume boundaries, byte-identical replay |
| Runtime/offline | `sys.executable`, smoke cases, requested/observed equality, offline code never instantiates live runner |
| Analysis/history | exact selection, power grid, sign test, bootstrap endpoints, all verdicts, unchanged V2 hashes/tests |

Packets and local commit boundaries are: `access` first; independent provisional
`treatment` and `tasks` plus validator record; `engine` plus tests/config/README;
then, only if needed, one consolidated correction commit. One explicit
offline implementation authorization covers these bounded local commits and the
sole correction. It authorizes no push, default-branch merge, or live call. Root
does not code. Keep only the task validator and one final adversarial audit—no
owner-reviewer layer, initial review loop, or second audit.

The final auditor checks the acceptance table, access isolation, allowlist/caps, copied-code absence, hashes, schedules, runtime, statistics, replay, history, and scope.
Findings are `M2_BLOCKER`, `DEFER`, or `REJECT`; only consolidated blockers enter
the one correction. After mechanical closure, freeze final bytes in an authorized
clean local commit, perform post-freeze alignment (gap stops without edits), run
the 300 cases on that commit, issue the receipt, create the manifest, and stop for
smoke authorization. An unresolved blocker stops for the user.

## 10. Offline gates, live authorization, and stopping

All commands are offline and use a temporary directory outside the repository:

```bash
python3 -m unittest discover -s tests -v
M2_OFFLINE_DIR="$(mktemp -d)"
PYTHONPATH=src python3 -m mdseval.beneficial_sensitivity validate \
  --experiment experiments/coder-beneficial-sensitivity-m2.json
PYTHONPATH=src python3 -m mdseval.beneficial_sensitivity qualify \
  --experiment experiments/coder-beneficial-sensitivity-m2.json \
  --output "$M2_OFFLINE_DIR/qualification"
PYTHONPATH=src python3 -m mdseval.beneficial_sensitivity verify-power \
  --experiment experiments/coder-beneficial-sensitivity-m2.json
PYTHONPATH=src python3 -m mdseval.beneficial_sensitivity simulate \
  --experiment experiments/coder-beneficial-sensitivity-m2.json \
  --output "$M2_OFFLINE_DIR/simulation"
git diff --check
git status --short
```

Gate order: known green baseline; offline authorization; access packet/hash;
independent provisional artifacts; task validation; engine/tests; power/fake
replay; final audit; at most one correction; mechanical closure; full command
block once; allowlist/line check; freeze final bytes in an authorized clean local
commit; post-freeze alignment (gap stops without edits); authoritative 300-case
qualification on that exact commit and create-once receipt; initial manifest;
then stop for smoke authorization. Any earlier failure blocks later gates.

Live contract, with no output or runtime override:

```bash
PYTHONPATH=src python3 -m mdseval.beneficial_sensitivity run-stage \
  --experiment experiments/coder-beneficial-sensitivity-m2.json \
  --instance <instance-id> --stage <smoke|calibration|controls|helpful> \
  --authorization-receipt <stage-specific-create-once-receipt.json>
PYTHONPATH=src python3 -m mdseval.beneficial_sensitivity replay \
  --experiment experiments/coder-beneficial-sensitivity-m2.json \
  --instance <instance-id>
```

Four separate explicit user decisions authorize: smoke; calibration after smoke;
controls after balanced selection and power `>=0.80`; and helpful after A/A and
harmful pass. Each is copied into a separate create-once live-root receipt before
its first call and cannot authorize another stage or artifact change.

Stop and preserve evidence on failed baseline/access/authorship/oracle/hash/
wrapper/isolation/runtime/balance/evidence/receipt/sentinel gate; frozen-byte
change; fewer than four eligible tasks per stratum; power `<0.80`; second invalid
block in a stage; invalid replacement; failed A/A or harmful gate; invalid resume;
cap/allowlist breach; a 315th call would launch; or helpful completion. Never retune, substitute,
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

Offline handoff requires all 20 tasks and 300 qualification executions passing;
the protocol grid reproduced; tests/fake replay green; access/authorship complete;
one audit and optional correction mechanically closed; all paths/caps satisfied;
historical V2 unchanged; and deterministic proof of 297/314 ceilings. Milestone 2
is administratively complete on one allowed verdict plus offline replay and
scientifically passes only on `SENSITIVITY_DEMONSTRATED`.
