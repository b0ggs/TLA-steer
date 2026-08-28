# Active-run hardening scope — 2026-08-28

This checklist records Wade's approved scope correction for the uncommitted
hardening work. It is an implementation checklist, not authority for new
experiments, tasks, checker redesign, or live model spend.

## Keep

Keep only changes used by the active schema-v3 `run_batch` path that protect
capability isolation, evidence validity, or the time/token measurements:

- exact subject capability and permission configuration that disables MCP,
  apps, web/browser, plugins, skills, and sub-agents;
- launch-time verification of the resolved capability configuration;
- active-container denial of subject access to authentication/session data,
  evaluator output, `/proc`, the network, and mutable `.git` state;
- the fixed subject shell/PATH and pinned interpreter/pytest behavior;
- fail-closed cleanup of per-attempt containers and networks;
- strict event-stream parsing and rejection of unapproved tool/event types;
- evidence-chain, redaction, token-consistency, terminal-state, and
  no-selective-retry protections in schema-v3 batches; and
- subject-only `duration_seconds`, with separately recorded total attempt time.

Retain only the focused tests required for those behaviors.

## Revert

Revert changes that are not required by the active experiment:

- shutdowns or behavior changes in legacy CLI, judge, scout, and live-run paths;
- changes to the registered cost/time analysis definitions or eligibility
  policy;
- new task-admission rules and their tests;
- expanded fixture size, depth, readability, and special-file defenses;
- CPU, memory, file-size, and descriptor caps that alter the measured runtime;
- interpreter-tree/launch rehashing, inherited-file-descriptor checks, and
  Docker-socket probes; and
- tests or historical configuration changes needed only by reverted behavior.

## Dependencies and verification

- Recompute the four self-hashes in
  `experiments/coder-beneficial-sensitivity-m2.json` from the final retained
  files; do not preserve temporary hash values blindly.
- Run focused tests for capture, runner, containment, and schema-v3 batch
  behavior.
- Run the repository-required full unit suite.
- Do not make live model calls or launch a benchmark batch while trimming.

The exposed-checker design limitation is recorded but is not repaired here;
repair would require new task/checker work outside this scope.

## Completion record

The trim was completed against this checklist. Verification after the final
retained code and recomputed hashes:

- focused runner/capture/containment/batch tests: 70 passed;
- historical hash-bound experiment tests: 35 passed, 6 skipped;
- full repository unit suite: 247 passed, 6 skipped; and
- current four-task offline preflight: `PASS` in 36.373825804 seconds.

No live model call or benchmark launch was made, and no task, arm, control, or
preserved run-evidence bytes were changed.
