# TLA-Steer: paused checkpoint and next steps

Status: paused on 2026-10-05 at the user's request. Preserve this checkpoint
and stop work. The steps below are for an explicit future restart; they do
not authorize background work, model calls, merges, or further implementation.

## Start here

The original finite two-arm TwoLights prototype is implemented and has
recorded offline coverage. A successful live experiment has not been established.

- Implementation branch: `dot/two-arm-completion`
- Implementation PR: [#4](https://github.com/b0ggs/TLA-steer/pull/4), open draft
- Tested implementation commit:
  `7904ccb0ee35fc7a411b446f7f0ecb726e318f90`
- Tested implementation tree:
  `6a4086ad8e8e18d03a9b5d6224ab3cdc81b5f210`
- Operational instructions: [two-arm run guide](docs/TWO_ARM_RUN_GUIDE.md)

Any documentation-only checkpoint commit after this revision does not create
new test evidence. The validation record below belongs to the implementation
commit above.

## Preserved branch and PR state

Verified on 2026-10-05:

- `main`: `57578486ecea6ffbe836292462e462dc24ff6bcc`
- [PR #1](https://github.com/b0ggs/TLA-steer/pull/1):
  `dot/offline-cost-screen-r2`,
  `b13aff5855f3c07241e00315a7ab4bb0f76326ff`
- [PR #2](https://github.com/b0ggs/TLA-steer/pull/2):
  `dot/guarded-checker-r3`,
  `32af88241a5762e87a3ea9b1745a0b2b3c0cd8bf`
- PR #4 is based on #2 and includes #1; all are unmerged drafts
- [PR #3](https://github.com/b0ggs/TLA-steer/pull/3):
  `dot/three-arm-pilot-r4`,
  `dde4f18d74b915b0e3203547fb309c6d42e82501`
  is an optional sibling of #4, excluded from the original two-arm handoff

Preserve these branches, PRs, and existing evidence. Merging drafts is not
required to test the pinned implementation.

## Completed implementation

- Direct frontier generation versus frontier-planned, cheaper-Follower SMC
  for the fixed TwoLights input
- Eight semantic steps, cumulative weights, ESS-triggered resampling,
  ancestry, and weighted official selection before final grading
- A hand-written exhaustive oracle, evidence capture, failed-call accounting,
  and offline report replay
- Two final integration repairs: action-first partial modules can precede
  INITIAL; the TLA worker accepts the documented reasoning-event shape while
  retaining malformed-event and forbidden-tool rejection
- A corrected README and Linux user-test runbook

The checker is fixed-instance and hand-written, not TLC-backed.

## Recorded validation and remaining limits

The October 1 handoff recorded 79 passing focused tests. Full discovery
recorded 311 tests, seven inherited test_scout errors from missing historical
evidence, seven skips, and no assertion failures. The full suite is not green.

The credential-free CLI doctor passed local parsing with Codex
0.159.0-alpha.7. This did not validate provider access or effective isolation.

On October 5, GitHub still showed zero workflow runs, check runs, or commit
statuses for the tested implementation commit. These results are local
offline evidence, not a passing GitHub CI result.

The latest [Linux isolation attempt](https://github.com/b0ggs/TLA-steer/actions/runs/36803529525)
failed at preflight with RTM_NEWADDR EPERM. Later isolation probes did not
run, and the responsible host policy is unconfirmed.

Still unvalidated: actual user-host isolation, current account/model access,
live OAuth execution, real response/usage capture, and model performance.
No real-model savings claim follows from synthetic fixture usage.
Direct macOS candidate execution is unsupported.

## Only if explicitly resumed

1. Read this file and the two-arm run guide. Start from the exact tested
   commit above, preserving local work and existing evidence.
2. On a compatible ordinary-user Linux host, perform the run guide's offline
   checks and credential-free isolation probes. Stop on failure; do not
   weaken security or use an unguarded fallback.
3. Check the installed CLI using an empty temporary profile. Retain the
   frozen settings and model IDs; do not silently substitute models.
4. Only after those checks pass and live model use is authorized, use the
   user's dedicated OAuth profile and run one N=2/C=2 two-arm smoke.
5. If integration is valid, run one intended N=8/C=4 comparison, then replay
   its report offline. Preserve complete run evidence and actual outcomes.

The smoke normally uses 18 calls, at most 19 with one Planner repair.
The intended comparison normally uses 66, at most 67. Each call has a
300-second timeout. These are not token, dollar, or subscription-credit caps.

Wrong candidates, particle collapse, and higher steering cost are legitimate
experimental outcomes. Missing usage, evaluator failure, or pipeline errors
do not establish a successful end-to-end comparison. Never hand-repair model
artifacts or repeat runs until a model wins.

## Scope remains finite

No required third arm, TLC integration, new specifications, statistical study,
native Mac adapter, broader CI work, refactoring, or branch deletion is needed
for this pause.

README.md and the two-arm run guide describe the implemented scope.
IMPLEMENTATION_PLAN.md records the original build plan; its initial-state
and runtime-fallback passages are historical, not current operating guidance.
ARCHITECTURE.md preserves broader design ideas. OVERVIEW.md, roadmap.md, and
older MDs_EVAL planning documents describe the preserved foundation.

Next action now: none. Leave the project paused until the user asks to resume.
