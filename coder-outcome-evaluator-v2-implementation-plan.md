# CODER Outcome Evaluator V2 — Active Feasibility Program

## Authority and claim boundary

This file is the sole active V2 authority. It defines a bounded CODER feasibility
pilot, but does **not** itself authorize implementation, live calls, a commit,
push, merge, promotion, or champion replacement. Each such action requires fresh
user authorization. V1 specifications and reports remain historical and V1-only.

The prior 907-line design remains recoverable from snapshot
`a4fe6e5dffa7e037fd1d92338a7ce357df902863`; its file SHA-256 is
`71f2ad3bbdadaa43f70903859974a8993be21730eadd5ff426c1e8e2ca6cba8b`.
It is evidence and deferred-design input, not competing active authority.

The goal is to compare complete `CODER.md` files by objective outcomes on tasks
for the CODER role. A whole-file comparison supports only “A performed better
than B under this frozen pilot.” A claim that “Karpathy style caused the result”
requires a separately predeclared matched ablation whose only intended treatment
difference is the frozen style intervention.

## Non-negotiable invariants

- Preserve raw run evidence and record hashes for every instruction and task.
- Never mutate a target, candidate, contract, fixture, or check during a run.
- Author tasks independently of candidate contents and observed candidate wins.
- Blind variant identity wherever optional qualitative judging later occurs.
- Mechanical outcome or integrity failures cannot be overridden by an LLM judge.
- Use the Python standard library only; unit tests and CI make no live calls.
- Separate subject failure from infrastructure failure and freeze deterministic
  retry/invalidation rules before any subject call.

## Current phase and permitted conclusion

This phase tests only whether objective tasks and thin scoring are feasible. It is
not a benchmark, representative sample, validation set, lockbox, promotion run,
or proof of a generally best MD. Its only outcomes are `PILOT` and
`INCONCLUSIVE`; `PROMOTE` and qualitative promotion do not exist in this phase.

The target workload, estimand, sampling frame, task weights, practical effect
threshold, and powered confirmatory design are unresolved gates. The pilot must
not silently answer them.

## Feasibility content gate

Author exactly four mechanics-only tasks in exactly two coherent synthetic Python
repositories: one bug fix, one feature, one integration change, and one refactor.
They are deliberately not representative evidence.

Every task must have:

- a visible acceptance outcome;
- a hidden check that fails on the pristine fixture and passes on a correct patch;
- hidden regression checks that pass before and after the patch;
- a deterministic reference solution used only for authoring validation; and
- a contract that states observable outcomes, never preferred process, style,
  target files, root cause, reproduction ceremony, or solution shape.

Checks must distinguish a correct solution from at least one plausible wrong
solution. If this cannot be shown without prescribing behavior, stop and redesign.

## Thin scoring contract

Keep four fields separate:

1. `observation_valid`: runner and evidence channel operated correctly.
2. `objective_resolved`: required acceptance and regression checks passed.
3. `subject_integrity`: protected inputs and run boundaries remained intact.
4. `diagnostics`: commands, diff, files, response, tokens, duration, and errors.

An infrastructure outage, evaluator defect, or corrupt/missing evidence invalidates
the observation and never counts against a subject. A subject-caused timeout,
noncompletion, incorrect patch, or boundary violation is unresolved. Before calls,
freeze which failures are retryable, the symmetric retry count, paired-observation
invalidation, and the rule forbidding discretionary or one-sided retries.

No diagnostic, stylistic preference, or qualitative judgment changes objective
resolution.

## Explicit exclusions

This program does not build concealed or external validation, a lockbox, custody
or authenticated receipts, Node/JavaScript tasks, public/real repository imports
or license handling, a generalized role framework, an optimizer, or a dashboard.
It does not implement multiple agents or evaluate other roles.

## Hard caps

These caps cannot be raised silently:

- Changed paths: at most 14 total, including at most 8 task/fixture/check paths.
- Total added lines across all changed paths: at most 1,100; deletions do not offset additions.
- New production modules: at most 2.
- Net new production code: at most 250 lines.
- Task fixture and check code: at most 600 lines total.
- Implementation agents: at most 2 concurrently and at most 3 total.
- Review: exactly 2 reviewer passes total; exactly 1 is blocker-only.
- Repair: at most 1 repair cycle; no recursive audits.
- Full unit-test attempts: at most 2 before repair and at most 1 after repair.
- Live calls during implementation: exactly 0.
- Any later live pilot requires fresh explicit authorization and is capped at 16
  subject calls: 2 MDs × 4 tasks × 2 repeats. It makes 0 qualitative-judge calls.
- Implementation wall clock: at most 4 hours from recorded start to handoff.
- Any authorized live pilot: at most 2 hours and at most the user-approved dollar
  ceiling recorded before launch.

If any cap binds, stop. Only the user may expand scope or a cap.

## Ordered implementation stages

Implementation begins only after fresh user authorization. At the end of every
stage, report changed paths, line counts, elapsed time, agent/review counts, and
remaining caps. A failed gate stops the program. Root orchestrates and reviews but
does not code. Agents may not spawn recursive audits or change scope.

### Stage 0 — Restore candidate extensibility only

Fix only these stale assumptions without weakening validation semantics:

- `tests/test_config.py::test_candidate_registry_accepts_sorted_versions_and_schema_is_open`
- `tests/test_config.py::test_reserved_roles_and_at_least_one_candidate_are_required`
- `tests/test_cli.py::test_validate`

Gate: arbitrary valid candidate rows no longer require test rewrites; all reserved
role, schema, path, duplicate-byte, and candidate-specific integrity rules remain.

### Stage 1 — Prove task and check feasibility first

Create the two repositories and four tasks. Validate pristine inversion, reference
solutions, regression preservation, wrong-solution rejection, isolation of hidden
material, and outcome-only contracts before writing production scoring code.

Gate: all four tasks satisfy the feasibility content gate within the path/LOC caps.

### Stage 2 — Add only the minimum scorer and wiring

Only after Stage 1 passes, add the separated scoring fields, deterministic check
execution, evidence capture/wiring, and a fake offline comparison. Reuse existing
infrastructure; do not add future benchmark, lockbox, role, or optimizer seams.

Gate: correct code resolves regardless of ceremony; incorrect code does not;
infrastructure invalidity is not charged to either MD; diagnostics cannot promote.

### Stage 3 — Offline verification and handoff

Run the repository-mandated full unit suite within the attempt cap, then the two
fixed reviews, one of which is blocker-only. Permit at most one bounded repair and
one post-repair full-suite attempt. Verify diff, caps, raw-evidence behavior, and
that no live-call path ran.

Gate: hand off evidence and a feasibility recommendation; do not run the pilot.

## Exit report and re-entry

The exit report must include authoring difficulty, hidden-check quality, failure
classifications, elapsed time, cost, all cap usage, and any process/style leakage.
If a later live pilot is separately authorized, also report ties, repeat variance,
noise, invalid observations, per-task resolution, calls, tokens, duration, and
actual spend.

The only go/no-go conclusion is `STOP/REDESIGN` or a justification for a separate
expanded phase. It is never promotion. At every phase exit, re-entry review must
test whether any deferred trigger below is satisfied and update **this same file**.
Never create a competing active V2 plan.

## Deferred register

| ID | Idea | Invalid/unresolved specifics not to copy | Evidence trigger | Snapshot anchor | Status |
| --- | --- | --- | --- | --- | --- |
| `POP-001` | Target population and sampling | Arbitrary 24-task quotas, language weights, and “representative” labels without a workload frame | User approves deployment workload, estimand, weights, and independent sampling owner | §5.1–5.5 | DEFERRED |
| `STAT-001` | Power, statistics, and controls | Eight-task sign test, two repeats, 10-point lift, non-significant A/A, and undefined “material” control | Feasibility outcomes plus repeat-noise evidence support a prospective clustered power plan | §4.3–4.5, §7 | DEFERRED |
| `LOCK-001` | Concealed validation and lockbox | Champion-piloted “unused” tasks, fixed 6/8 counts, and unpowered one-use verdict | Sampling and power gates pass and user authorizes a confirmatory phase | §5, §8 | DEFERRED |
| `CUST-001` | Isolation, custody, receipts, evidence release | Unproven container/account boundary, receipt authority, hash-chain freshness, and post-spend reproduction | A real custodian and tested isolation boundary exist for an authorized lockbox | §6.3–6.4, §8 | DEFERRED |
| `CTRL-001` | Candidate-independent controls | Control-core hashing and gates before the primary scorer and failure taxonomy stabilize | Thin scorer is stable and a powered control purpose is predeclared | §7.1–7.3 | DEFERRED |
| `LANG-001` | Languages and ecosystems | Unsupported 16 Python/8 JavaScript ratio, Node requirement, and package-free generalization | Approved workload sampling shows language/ecosystem demand | §5.1–5.2 | DEFERRED |
| `CAUS-001` | Karpathy-style causal ablation | Inferring style from arbitrary whole-file differences | User asks the causal question and freezes a matched treatment/control contrast | §1, §4 | DEFERRED |
| `ROLE-001` | Future role evaluators | Reusing binary repository resolution or single-agent topology for unlike roles | CODER feasibility exits and a role-specific outcome/topology charter is approved | §1, §14 | DEFERRED |
| `REAL-001` | Real repositories | Public-solution memorization, dependency, license, provenance, and issue-selection bias | Synthetic feasibility passes and external-validity scope is approved | §5.2, §5.4 | DEFERRED |
| `OPT-001` | Optimizer and dashboard | Candidate search, automatic editing, hosted service, and UI before measurement is valid | Multiple role evaluators have valid development and confirmatory protocols | §13–14 | DEFERRED |

## Future horizon only

Preserve the conceptual seam of immutable instructions/tasks, raw evidence,
observation validity, role outcome, integrity, diagnostics, and blinded optional
judgment. Build no generalized framework now. A later role plan must define:

- AUDITOR: defect precision, recall, severity calibration, and evidence fidelity.
- RESEARCHER: factual correctness, source authority, coverage, and citation fidelity.
- ORCHESTRATOR: delegation, handoff, integration, completion, and budget adherence,
  with agent topology frozen as a separate experimental factor.

## Decision log

- Construct/claim audit: objective role outcomes replace Karpathy-like behavior;
  whole-file results do not establish a style cause.
- Statistics/controls audit: population, independence, power, effect, A/A, negative
  control, and invalid-observation rules were blockers, not implementation details.
- Scope/feasibility audit: the 907-line design bundled benchmark, custody, language,
  role, and optimization work before proving four objective tasks and thin scoring.
- Governance decision: preserve exact snapshot
  `a4fe6e5dffa7e037fd1d92338a7ce357df902863`, maintain one active file and one
  `AGENTS.md` pointer, use exactly two reviews and at most one revision cycle.

## Stop conditions and protocol

Stop immediately if authorization is absent; the worktree is not the designated
clean implementation worktree; another path is modified; a cap would be exceeded;
a new dependency, network access, live call, concealed pack, public repository, or
future-role abstraction is proposed; a contract prescribes process/style; checks
cannot prove baseline inversion and regression preservation; infrastructure and
subject failures cannot be classified deterministically; a reviewer requests a
second repair cycle; or evidence would be discarded or rewritten.

On stop, preserve current evidence, report the exact gate and cap, and request a
user decision. Do not weaken a check, expand scope, start another plan, retry a
live observation, commit, push, merge, or promote to force progress.
