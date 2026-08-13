# CODER beneficial-sensitivity protocol v0.3: timeout-v1 reliability amendment

Status: user-authorized protocol version 0.3 for new experiment `coder-beneficial-sensitivity-m2-timeout-v1`.
This document inherits v0.2 except for the explicit operational-oracle exception in Section 2; it never resumes the terminal M2 experiment.
Historical authorities are `CODER_BENEFICIAL_SENSITIVITY_PROTOCOL.md` (`4384a005b7d934b86ef91dd7d7fa6b9b46c2374fd7790bd89f8ed1a2222c6b0d`) and
`CODER_BENEFICIAL_SENSITIVITY_M2_IMPLEMENTATION_PLAN.md` (`896f01fadf0ca9e575af8593305d3a0fc42919308dc49fa07ddfd1770f2e7f06`),
`CODER_BENEFICIAL_SENSITIVITY_M2_1_REMEDIATION.md` (`85a7618b58623194f6a7bfdd42e7a3ebe2947c3678e3a446fbc657e776b36fa2`) and its closure (`e6421d03921c1f3d45bc4f805c8aa1da34961f2f5d95b095cd22c597f3e79442`), and
`CODER_BENEFICIAL_SENSITIVITY_M2_2_COMPLETION.md` (`bd02f51b1ca9095c4b4d9cadcd89099c32229e9f215beb310cee2ce459fb0a7e`) and its closure (`d77d7e1cbe8f320470237e15dd9e205fe19d8f2610d93fcd6e47ae5c56d98b0f`).
`AGENTS.md` (`cb4168f9fbc1436d34220ba843de9f5bb657bd45665242a8847047426ce33634`) remains repository authority.
The failed M2 and M2.2 experiments, closures, implementation returns, and evidence remain terminal historical records.

## 1. Scientific boundary and preservation

Inherit the v0.2 construct, treatments, tasks, model/runtime, statistics, seeds, schedules, retry rules, call caps, gates, and claim boundary for this separately identified experiment.
The sole scientific exception is the uniform internal checker subprocess timeout change declared below; it is not evidence from, or continuation of, M2.
Preserve `/private/tmp/m2-qual.3dUiYW/qualification-results.json` byte-for-byte at SHA-256 `aba5b72679ff6c6b6b48283dfd0fafb8863436d42846fa1058e03051787c5759` with `authoritative:false`, `status:"FAIL"`, and 300 executions.
That failed evidence is never overwritten, deleted, pooled, reclassified, presented as PASS, or used as an outcome or observation in timeout-v1.
Preserve old `authorship.json`, `oracle-variants.json`, contracts, fixtures, treatments, all M2 authority/closure/validation records, raw evidence, and every V2 byte.
No subject, judge, live experimental, network, commit, freeze, authoritative qualification, push, merge, release, or publication action is authorized.
Administrative model calls, if any, are disclosed with role, requested/observed model metadata, call count, packet hash, and output hashes; they are never subject calls.

## 2. Operational-oracle exception and exact task writes

The exact IDs are `bug-01`–`bug-05`, `feature-01`–`feature-05`, `integration-01`–`integration-05`, and `refactor-data-01`–`refactor-data-05`.
Each current checker has one `timeout=4` literal governing four sequential outer subprocess subchecks R1, R2, R3, and G1; change that literal uniformly to `timeout=10` in all 20 checkers while outer checker timeout remains 60 seconds.
The nominal subcheck ceiling is four times 10 = 40 seconds under the unchanged 60-second outer ceiling.
This arithmetic makes no claim that 10 is minimal, sufficient, deterministic, or inferred from the censored four-second timeout observation.
Existing task writes are exactly:
- the 20 `evals/m2/coder-beneficial-sensitivity/<exact-id>/check.py` files, literal-only `timeout=4` to `timeout=10`;
- their 20 `task.json` files, changing only consequent `checker_sha256`; and
- `evals/m2/coder-beneficial-sensitivity/master.json`, changing only consequent checker/task hashes.
Keep `evals/m2/coder-beneficial-sensitivity/authorship.json` (`82436929419e8a69ec92355786297406f6c8db274db623a8ed946c0bbf3b5788`) immutable.
The new one-line task-reliability authorship record alone attributes these derived corpus bytes and binds owner, packet, authorities, exact paths, old/new hashes, model disclosure, and literal-only scope.

## 3. Packet-local direct-checker validation

Root makes no clean-baseline claim; it records an exact path/mode/SHA-256 manifest of the present M2.1 worktree inputs and a separate exact manifest of the preserved M2.2 return, then transfers root-hashed packet copies.
The one-pass task-reliability owner receives only the authorities, failed-evidence hash, the 20 checker/task pairs, master, and immutable authorship/oracle/contracts/fixtures needed for binding.
It writes only the 41 authorized existing paths plus its one-line authorship return, returns exact old/new manifests, and stops.
Its authorship attests packet-only access, prohibited-path nonaccess, unchanged protected bytes, requested/observed model identity, call count, and input/output root hashes.
An independent validator receives a fresh read-only-authority packet containing the returned corpus, actual `oracle-variants.json` (`2ffb2764ce63c07b9c96fee37e1fb5285d1cc6a3d46054b732498c05ece8e9cd`), and no owner workspace.
For each execution it copies the frozen fixture to a fresh workspace and applies the selected oracle variant's exact `remove` and `files` entries; pristine applies none.
It invokes the task's actual `check.py` directly with recorded `Path(sys.executable).resolve()`, `sys.version`, isolated environment, and outer timeout 60, without a model or generic validator artifact.
Require canonical stdout and schema `mdseval.coder-beneficial-sensitivity-m2-check-v1` with exact `task_id`, `environment`, `requirements`, `regressions`, `integrity`, and Boolean `resolved` fields.
Environment and integrity must pass; requirement/regression key sets must exactly equal `task.json`; pristine is unresolved with a failed requirement, byte-distinct correct-a/correct-b both resolve with regressions passing, and each mutant is unresolved with every oracle-declared failure.
Require every requirement-to-negative-case mapping to fail in each named mutant and the observed mutant-failure union to equal all requirement IDs.
Require complete canonical checker payload bytes to match across three repeats within each task/state, never merely exit status or summary booleans.
Iterate master order, then `pristine`, `correct-a`, `correct-b`, `mutant-a`, `mutant-b`, then repeats 1–3: exactly 300 real checker executions, once, with no retry or replacement.
Require task-source tree identity before/after, fresh nonreused workspaces, and no symlink, hidden-path, unexpected-file, truncation, crash, timeout, schema, count, hash, or mutation failure.
Write one canonical-line corpus record `experiments/coder-beneficial-sensitivity-m2-3-task-validation.json` binding all inputs, order, Python identity, 300 results/payload hashes, trees, counts, and PASS/FAIL; any failure preserves evidence and stops.

## 4. Conditional preserved-return rebind and closure

Only validation PASS permits derivation from preserved M2.2 return engine `6e8582b3c55bb8f82b1922f22cca8eb2ddf93c52dcd3939a0c3ad93d1391ec01`, tests `ae1a5c9aa2d517d307fd5928bb4b38ba8c8b29837f62d6ad2b199e58154ab6a0`,
config `570771dd7f08d6f53b6d30f2058ec35c8ef3d602f7f64fa30765678a611a8d87`, and authorship `938b8019f758b91849eb17e98eba347dc22a260a7e2c2b4fa716eae3d36bf59f`.
The raw return remains byte-preserved; derived outputs are exactly `src/mdseval/beneficial_sensitivity.py`, `tests/test_beneficial_sensitivity.py`, `experiments/coder-beneficial-sensitivity-m2.json`, and one-line M2.3 rebind authorship.
Only new experiment ID, protocol-v0.3 authority, artifact paths/hashes, and consequent integrity metadata may differ; executable lifecycle/statistical logic and test logic may not change or weaken.
Root alone verifies packets, ancestry, exact diffs/hashes/allowlists, authorship, history, and caps; there is no further LLM audit, audit record, reviewer, correction wave, or second role pass.
Root then runs one engine-mediated non-authoritative 20×5×3 rehearsal with the same semantics/order and no retry; task validation plus rehearsal total exactly 600 real checker executions, while unit/static tests use injected fakes and add zero.
Any validation, rebind, unit/static, rehearsal, provenance, history, path, hash, or accounting failure is final for v0.3 preparation and preserves all evidence without repair.

## 5. Exact new files, accounting, and stop

New repository files are exactly this amendment; `experiments/coder-beneficial-sensitivity-m2-3-task-reliability-authorship.json`; `experiments/coder-beneficial-sensitivity-m2-3-task-validation.json` (corpus); `experiments/coder-beneficial-sensitivity-m2-3-rebind-authorship.json`; and `experiments/coder-beneficial-sensitivity-m2-3-closure.json`, each JSON one canonical physical line.
The closure records commands, both 300-execution hashes/counts, exact paths/diffs, packet/return ancestry, disclosures, zero subject/judge/live/network calls, immutable-history checks, and PASS/FAIL; no other new path is authorized.
The validation record is the sole new corpus file and increases corpus by exactly one physical line.
Literal checker edits, one-line task/master hash rebinding, and one-line derived config do not add physical lines.
The preserved M2.2 authorship remains raw-return evidence and is neither rewritten nor counted as a new v0.3 record.
Every created record uses exclusive creation and binds its prerequisite manifest hashes.
Unused category capacity never authorizes another artifact, role, execution, correction, or experiment.
Caps remain production 900, tests 800, corpus 1,200, total 3,200; with this 72-line amendment and three one-line other records, the exact other cap is `386 + 72 + 3 = 461`, with no offsets or reallocation.
PASS closes only timeout-v1 offline preparation and stops before integration commit, freeze, authoritative qualification, initial manifest, live stage, push, or merge to request separate explicit authorization; FAIL remains terminal.
