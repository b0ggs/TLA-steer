# Section 13 probe-list pre-build review

Date: 2026-08-23

Reviewed commit: `90ebf503fa4dc0f32c7699d57a31b6b6b554d18c`

Verdict: **GO ONLY AFTER EXACT CORRECTIONS**

## Scope and provenance

I reviewed only `TASK_TOOLING_V2_PLAN.md` §13 and directly relevant current runner,
verifier, Codex-command, task-checker, request, and evidence code. I did
not activate §13, build containment, run a subject/model call, create a branch,
or change a task, target, candidate, or prior evidence.

I am a fresh isolated follow-up OUTSIDE REVIEWER, not the original reviewer who found
the leak and not a resumable instance of that identity. I therefore did
not independently reproduce the original trace audit. I accepted this supplied,
previously verified finding as input: 7/12 Phase 3 attempts read installed fixed implementations
through `inspect.getsource(tomllib._parser)`,
`inspect.getsource(enum.Enum.__new__)`, or host-install searches for `doctest.py`.
As a non-model feasibility check, the reviewed host's Python 3.11.5 still lets
`inspect.getsource(tomllib._parser)` expose the fix marker `finalize_pending()`.

Because §13's opening gate names "the OUTSIDE REVIEWER who found the leak," this
report cannot satisfy that sentence literally. Before accepting this report,
replace that phrase with:

> One audit round: an isolated OUTSIDE REVIEWER reviews this section and the
> probe list; if the original leak reviewer is unavailable, a fresh reviewer
> must disclose that fact and the provenance of the leak finding in the report.

## Blocking findings

### B1. "Exactly three mounts" is not mechanically defined

§13.2 says mounts are exactly workspace, interpreter, and `$CODEX_HOME`, while §13.4.2
permits an undefined "virtual" allowlist. A normal Linux container also
has its image root, proc/sys/dev/cgroup mounts and often runtime-provided files;
counting all mountinfo rows makes three impossible, while counting an undefined
subset can hide an extra bind mount. The host-path list is not a substitute: a
host tree can be mounted at an arbitrary destination. `$HOME` also cannot be
required to fail listing if it is used as the agent-home destination. Current
`scripts/run_batch.py:190-195` checks only `auth.json`; current
`src/mdseval/runner/codex_cli.py:156-165` checks only two root instruction names.
Neither enforces the proposed mounted-home topology.

This is a false-green/false-red defect. Define three **external bind mounts**, fixed
canonical destinations and modes, and a closed list of permitted
image/runtime mount classes. Reject every other mountinfo row; do not use prefix
matching. Fix the container `$HOME`/`CODEX_HOME` destinations explicitly. The
agent home must be a non-symlink directory containing exactly a non-symlink
`auth.json` and one newly empty, non-symlink session directory; recursively
reject every other entry. Mountinfo parse/traversal/stat errors fail closed.
Record the normalized mount table and exact runtime arguments in the probe, and launch
attempts through the same wrapper and security arguments.

### B2. The agent-command network test has no zero-spend, policy-identical path

§13.4.3 correctly rejects a bare-container socket test, but it does not say how
the socket command enters the confinement layer used by agent commands.
`build_codex_command` sets `--sandbox workspace-write` and
`sandbox_workspace_write.network_access=false`
(`src/mdseval/runner/codex_cli.py:44-78`), but `run_batch` has no command-sandbox
probe hook. A `codex exec` probe would require a model call, contradicting
§13.6's "Probe fails ... No calls happen" and the approved 12/16 call budget.

Require a no-model Codex sandbox-helper invocation which replays the exact resolved
workspace-write policy used by the subject command. Capture its argv,
resolved-policy hash, socket target, denial, and exit status. Assert that the
policy hash equals the subject command's policy hash. If the pinned Codex CLI
cannot expose and replay that policy without a model call, `BUILD_REJECTED`.
A mere socket failure, DNS failure, unroutable address, or container-level deny
does not pass this leg.

### B3. Checker/interpreter identity is stated but not bound to scoring

§13.3 requires the container interpreter and checker interpreter to be the
same. Today `tooling/taskcheck.py:121-144` invokes every checker with its own
`sys.executable`, and `scripts/run_batch.py:224-232` calls that host-side path.
All four task checkers then launch nested tests with their own `sys.executable`
(for example `tasks/real-tomli-dotted-keys/check.py:17-31`). Merely putting a
pinned interpreter on the subject's PATH would leave scoring on the host
interpreter and can change outcomes.

Require both the pre-spend checks and production attempt scoring to run through the
container wrapper under the selected per-task interpreter. The probe must
record and compare the canonical executable path, `sys.version`, executable
SHA-256, image digest, and PATH resolution used for subject commands and
`check.py`; any mismatch is `BUILD_REJECTED`. Define "reference twice
byte-identically" as equal exit status, stdout bytes, and stderr bytes, with both
parsed results resolved. The same run must show public unresolved with every
regression true and `taskcheck verify` passing. The current four tasks pass those
logical checks on host 3.11.5; the required 3.10.x tomli run remains a build-time
gate, not something this review could assume.

### B4. The request schema cannot represent the permitted multi-image choice

§13.7.2 prescribes `runner.container.image_digest` (singular) and then permits
per-task images with "all digests" in that object. Those requirements cannot both
be represented. Current `_runner` constructs `RunnerConfig(**value)`
(`scripts/run_batch.py:81-98`), so the nested object must also be separated before
construction, as §13 already intends by leaving `RunnerConfig` unchanged.

Use this single exact schema instead:

```json
"container": {
  "image_digests": {"<task_id>": "sha256:<64 lowercase hex>"},
  "spec_sha256": "<64 lowercase hex>",
  "interpreter_pins": {"<task_id>": "<exact version>"}
}
```

The three maps must have exactly the REQUEST task-id set; repeat one digest for all
tasks when one image is used. Before `RunnerConfig` construction, validate
and remove `container`; never pass it to the dataclass. Probe output is per task.
Queue, launch, every attempt's intent/launch/result, and verify must compare the
same object verbatim, and runtime inspection must equal that task's approved
content-addressed digest. Tag equality is insufficient.

### B5. The attack oracle and red/green control admit false results

§13.4 does not define whitespace normalization, scan error handling, minimum
spec contents, or what proves the old host went red *because of contamination*.
On the macOS host, `/proc/self/mountinfo` alone fails, so an aggregate nonzero
status could satisfy "red on host" without detecting any answer. Conversely,
ignored traversal/decode errors or run-collapsing whitespace can miss a
format-only copy. Calling only `inspect.getsource(<module>)` also is not the
literal enum exploit supplied above.

Make the probe emit named, per-check JSON records. Validate the spec has exactly the
four task IDs, nonempty import/attribute targets and nonempty discriminative
signatures. Include the literal targets `tomllib._parser` and
`enum.Enum.__new__`, plus the doctest filesystem search. Define normalization as
PEP-263 decoding followed by removal of every Unicode whitespace code point from
both source and signature; scan every reachable regular `.py` file outside the
exact workspace mount without following symlinks, and fail closed on any
unexpected walk/stat/read/decode error. Log every skipped root and file count.
The host control passes only as `EXPECTED_RED` when at least one literal target
or global signature produces an explicit `CONTAMINATION_FOUND` record; unrelated
structural failures do not prove the control. The container passes only when all
legs are green. Both modes must use the same probe code and hashed contamination
spec; the container mode must use the same wrapper/options as an attempt.

## Feasibility and disposition

The corrections do not require task edits, new admission machinery, a live preflight
call, or wider experiments. `scripts/run_batch.py` is 549 lines, so its
610-line cap leaves 61 lines; keeping container execution, checker invocation,
and token extraction behind `scripts/contain/` is the viable route already
allowed by §13.7. The four current task manifests verify, public trees are
unresolved with regressions passing, and references resolve repeatably under the
current host interpreter. No container runtime is present in this review
environment, so image, mount, Linux sandbox, and 3.10.x claims remain acceptance
tests rather than reviewed facts.

Final verdict: **GO ONLY AFTER EXACT CORRECTIONS**. Apply the provenance edit and
B1-B5 above before activating §13 or beginning the build. After those narrow
corrections, the proposed probe remains appropriately scoped to sealing and
detecting this leak class; broader bytecode/disassembly scanning, new receipt
systems, task changes, and additional experiments are not required here.
