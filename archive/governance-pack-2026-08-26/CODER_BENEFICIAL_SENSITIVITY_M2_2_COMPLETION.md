# CODER beneficial-sensitivity M2.2 completion amendment

Status: user-authorized offline procedural amendment.
Authorities: the M2 protocol, M2 implementation plan, M2.1 remediation, and M2.1 closure record.
This amendment addresses only closure findings 8-11 and preserves V2.
Its only exceptions to M2.1 are one new bounded implementation pass and the administrative cap in Section 8.

## 1. Frozen scope and exact paths

Preserve every task, checker, treatment, prompt, model, runtime, statistic, threshold, seed, schedule rule, call cap, claim boundary, and V2 byte.
No live or network call, freeze commit, push, merge, leaderboard, optimizer, UI, dependency, new role, or experiment redesign is authorized.
The implementation owner may modify only:

- `src/mdseval/beneficial_sensitivity.py`;
- `tests/test_beneficial_sensitivity.py`; and
- `experiments/coder-beneficial-sensitivity-m2.json`, kept as one canonical line.

The only new repository files are:

- `CODER_BENEFICIAL_SENSITIVITY_M2_2_COMPLETION.md`;
- `experiments/coder-beneficial-sensitivity-m2-2-engine-authorship.json`, one canonical line; and
- `experiments/coder-beneficial-sensitivity-m2-2-closure.json`, one canonical line.

## 2. One isolated owner and one pass

Root creates one packet-only temporary directory and hashes every transferred input and returned output.
Inputs are AGENTS.md; all M2 authorities and closure/authorship/validation records; the three modifiable files; frozen M2 tasks, oracle, and treatments; and only the historical helper files already allowed by M2.1.
The owner may read only its packet and write only the three implementation returns plus the one-line M2.2 authorship return.
It may not access the repository, Git/history/diffs, other packets, unrelated documents, runs/reports/live outcomes, network, or live models.
The authorship record binds role, requested and observed model metadata, call count, packet/input hashes, output hashes, paths read/written, and packet-only, forbidden-access, and no-live-call attestations.
After the completed three-auditor plan wave, there is no further LLM audit, correction loop, or second implementation pass.
Root integrates bytes and performs one mechanical closure; any failure stops without repair.

## 3. Exact public initialization transition

Add public API `initialize(...)` and CLI:
`initialize --experiment <path> --instance <id> --verified-commit <sha> --freeze-authorization <path> --closure-record <path>`.
The API alone may also accept injected `runs_root` and checker/process seams for deterministic tests; the CLI exposes no runtime/output override.
Initialization requires the external freeze authorization, prior M2.2 closure `PASS`, exact clean HEAD, and nonpreexisting live/replay roots.
It exclusively creates `runs/<instance>/live`, then create-once `final-freeze-receipt.json` binding authorization, commit, config, evaluator, and governed artifacts.
It performs post-freeze alignment against that commit and create-once `post-freeze-alignment-receipt.json`; any gap stops before qualification.
It then runs the authoritative qualification in Section 4 and create-once its results and receipt.
Only after qualification PASS does it create all-20 base/fallback schedules, sentinels, and separate per-stage mapping records.
The initial manifest contains unordered treatment hashes and withheld per-stage mapping hashes, never plaintext semantic mappings.
It binds the freeze, alignment, and qualification receipts, Python/runtime identity, governed hashes, schedules, sentinels, seeds, invalidity table, wrapper, roots, and 297/314 caps.
The immutable `initial-manifest.json` is created last; every post-manifest receipt/report binds it and prerequisite hashes.
Premanifest receipts do not reference the manifest, avoiding a circular dependency.

## 4. Complete authoritative qualification

Run exactly 20 tasks by five canonical states by three repeats: exactly 300 executions using recorded `Path(sys.executable).resolve()` and `sys.version`.
For every repeat validate complete canonical checker JSON: environment/self-check, every requirement, regressions, integrity, and `resolved`.
Require byte-identical complete canonical checker JSON across the three repeats, not equality of summary booleans.
Enforce the oracle disposition and requirement-to-negative-case matrix for every task and state.
Pristine must fail requested behavior; both materially different correct variants must resolve and preserve regressions; both mutants must fail their declared reasons; their union must cover every requirement.
Reject nondeterminism, drift, symlinks, hidden paths, reused repositories, truncation, missing output, or any count other than 300.
The create-once qualification receipt binds commit, config/evaluator/artifact hashes, Python identity, complete canonical-results hash, and counts.

## 5. Executable stage machine and blinding

The sole order is initialize -> smoke -> calibration -> selection/power -> controls -> helpful -> terminal report.
Each `run-stage` validates a separate external user authorization and exclusive-copies a manifest-bound authorization receipt into the live root before its first call.
No stage infers authorization, accepts an override, or runs before all prerequisite hashes and receipts validate.
Schedules exposed to execution contain opaque arm IDs only; semantic mappings remain unavailable through CLI, schedules, reports, and analysis until that stage's outcomes lock.
Smoke uses raw final-message bytes and passes only on exact `IMPLEMENTED\nSMOKE_READY\n`, exit zero, untouched tree, complete capture, and matching requested/observed identity; it is never retried.
Calibration runs only the frozen all-20 null schedule and create-once locks its stage result.
Its transition derives all 20 counts from locked attempts, then create-once selection, power, and filtered control/helpful schedule receipts without rerandomization.
Selection or power failure terminalizes `SENSITIVITY_NOT_DEMONSTRATED` and prohibits later stages.
Controls consume only those receipts, lock outcomes, then create control-only unblinding and A/A/harmful gate receipts.
Failed A/A or harmful gates terminalize `SENSITIVITY_NOT_DEMONSTRATED`; helpful mapping remains withheld and helpful cannot launch.
Helpful locks outcomes before helpful-only unblinding, derives its gate and full statistics, and terminalizes the allowed final verdict.
Any integrity failure terminalizes `INVALID`; every terminal branch remains reportable and replayable.
Enforce complete task units, frozen sentinels, resume boundaries, whole-block supersession/replacement rules, stage order, all launched calls, 297 base calls, and 314 absolute maximum.

## 6. Evidence, terminal locking, reports, and replay

Every attempt directory is exclusive-create and retains all raw runner, final-byte, identity, checker, capture, command, usage, timing, path, patch, status, and hash evidence required by the governing plan.
Stage-result and outcome-lock receipts are immutable intermediates; there is exactly one terminal `locked-evidence-manifest.json`, never one per stage.
Terminal assembly derives `raw-evidence.json`, selection, power, gates, coverage, secondary metrics, deviations, verdict, and canonical JSON/Markdown reports only from validated raw attempts and receipts.
Caller-supplied outcomes or summaries are never accepted.
Unblinding is create-once, stage-specific, post-lock, and bound to mapping plus prerequisite hashes.
Terminal assembly runs for smoke/integrity invalidity, selection/power stop, controls stop, and helpful completion.
Replay accepts only frozen config and instance ID, never constructs a runner, and uses no authentication, model, network, or judge.
It validates roots, manifest/receipt DAG, hashes, sentinels, ordering, deletion/insertion/tampering, supersession, resume, and caps before creating the one replay root.
Valid replay regenerates canonical JSON and Markdown byte-for-byte; any mismatch fails.

## 7. Acceptance tests that exercise public boundaries

The positive fake lifecycle invokes actual public `initialize`, all four `run_stage` calls with injected deterministic checker/runner seams, terminal assembly, and `replay`.
It asserts the complete create-once file graph, 300 qualification executions, opaque schedules, staged unblinding, successful gates, terminal evidence, and byte-identical replay without constructing a live runner.
Separate public-entry tests cover every valid early stop and `INVALID` terminal path.
Negative tables reject dirty/drifted commits; absent/failed closure or alignment; incomplete/noncanonical qualification; duplicate roots/receipts; premature/global unblinding; missing/reordered/tampered evidence; sentinel drift; invalid transitions/resume/retry; 297/314 breaches; and smoke newline variants.
Tests prove reports are derived from raw evidence rather than supplied summaries and retain the existing selection, power-grid, sign-test, bootstrap, verdict, line-cap, and unchanged-V2 checks.

## 8. Mechanical closure, budgets, and stopping

Run once: full unit suite, validate, non-authoritative external-temp 300-case qualification rehearsal, power verification, simulation, complete fake lifecycle/replay, diff check, exact allowlist, V2 hashes/history, authorship, and line counts.
The M2.2 closure record marks findings 8-11 PASS/FAIL, cites command results and hashes, and records zero live calls and whether any prohibited access occurred.
Caps from `bfda5f78e418784f6390cc4aead927bbd7b896ff` remain production 900, tests 800, corpus 1,200, and total 3,200; deletions do not offset additions and capacity is not reallocated.
Only the other-file cap changes from 300 to exactly 386: the existing 283 lines plus this 101-line amendment and two one-line records.
On complete PASS, stop before freeze commit, authoritative qualification receipt, initial manifest, push, merge, or live stage and request the next explicit authorization.
