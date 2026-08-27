# Section 14 independent pre-build review

Date: 2026-08-24

Branch: `section13-sealed-rerun`

Plan commits reviewed: `1e4f9ec` (the first Section 14 commit, changing only
`TASK_TOOLING_V2_PLAN.md`) and `becb1bc` (the narrow Section 13.4 probe-mode
amendment after the malformed-PEP-263-fixture contradiction).

Verdict: **GO ONLY TO THE CONTAINER-BUILD, IN-CONTAINER ADMISSION, PROBE, AND
REQUEST-PREPARATION GATE.** This is not a GO for a live subject call, does not
claim that an image or admitted task exists, and does not satisfy Section 14's
final approval-stop acceptance yet.

## Scope and independent provenance

I am the fresh independent review lane `/root/section14_independent_audit`, not
a task builder, blind solver, or containment implementer. I read the binding
vocabulary and Sections 1, 11, 13, and 14; inspected the exact current task and
tooling bytes; reconstructed upstream archive comparisons in temporary
directories; reran checkers, preflights, signature checks, and focused unit
tests; and inspected the blind and rejection evidence. I did not invoke Docker,
run a blind or subject model, admit a task, create a manifest, commit, or edit
any task/tooling byte. This report is my only workspace edit.

The first Section 14 commit satisfies the requested plan-first ordering: it
appended Section 14 to the one authoritative plan and touched no other file.
No additional plan document was created. The later `becb1bc` amendment followed
a mandatory stop on a genuine contradiction: CPython deliberately ships
malformed encoding fixtures, so container fail-closed decoding could not also
be applied unchanged to the host control. The amendment separates the two
modes while retaining fail-closed behavior in the sealed image.

## Final cohort: source and blind gate

The final cohort is exactly four task-layout-v3 tasks. Every task preserves the
complete pinned pre-fix Git archive plus the injected issue contract; reference
starts from that same tree and overlays only the exact upstream non-test fix;
fix-changed tests remain private and are overlaid only in checker scratch space.
I found no pruning, hidden task byte, symlink, cache, inherited evaluator
instruction, submodule, or private-test leak. License files and source/test
patch hashes reproduce the recorded provenance.

| Task | Closed issue and full scale | Exact fix partition | Mechanical checker and blind |
|---|---|---|---|
| `full-boltons-wraps-forwarding` | [boltons #343](https://github.com/mahmoud/boltons/issues/343), closed `2026-07-18T00:44:26Z`; 111 base files; 3-file diff, `+93/-71` | Reference: `boltons/funcutils.py`; private: 2 changed test files | Public `R1=F,R2=F,G1=T`; reference twice byte-identical resolved; blind launch 1, xhigh, resolved |
| `full-click-stream-lifecycle` | [Click #3110](https://github.com/pallets/click/issues/3110), closed `2026-03-01T16:20:13Z`; 146 base files; 5-file diff, `+587/-12` | Reference: 2 non-test paths; private: 3 test/configuration paths | Public `R1=F,R2=F,G1=T`; reference twice byte-identical resolved; blind launch 1, xhigh, resolved |
| `full-flask-automatic-options` | [Flask #5916](https://github.com/pallets/flask/issues/5916), closed `2026-02-12T21:07:52Z`; 235 base files; 7-file diff, `+96/-86` | Reference: 3 non-test paths; private: 4 changed test paths | Public `R1=F,R2=F,G1=T`; reference twice byte-identical resolved; blind launch 1, xhigh, resolved |
| `full-starlette-websocket-denial` | [Starlette #3048](https://github.com/Kludex/starlette/issues/3048), closed `2026-03-15T11:59:17Z`; 126 base files; 3-file diff, `+100/-23` | Reference: `starlette/responses.py`; private: 2 changed test paths | Public `R1=F,R2=F,G1=T`; reference twice byte-identical resolved; blind launch 1, xhigh, resolved |

All four are BSD-3-Clause repositories, closed after January 2026, use the real
pytest framework, pin CPython `3.11.5`, and have exact on-disk dependency
artifact sets and hashes in `image-lock.json`. Those lock files describe the
future images; this review does not claim the artifacts have yet been unpacked
or executed inside an image.

For every selected task, the current public tree hash equals
`blind.provenance.json.input_tree_sha256`; provenance records the four expected
isolation flags; the blind checker resolves; and `blind-calibration.json` is
exactly `{"seal_status":"UNSEALED","use":"calibration-only"}`. These solves
are calibration only. They prove neither sealed fair-solvability nor difficulty
and may not support evidentiary claims.

## Final contamination spec and containment implementation

`scripts/contain/contamination-spec.json` has SHA-256
`129e6dd45d57c4c735e33b33e4b81e5404cd8249b64be8c65973047eba2749fc`.
`load_spec` passes and returns exactly the four cohort IDs. Each configured
signature has zero whitespace-normalized occurrences in public, exactly one in
reference, and the reference target source contains it:

| Task | Literal target | Signature result |
|---|---|---|
| boltons | `boltons.funcutils.FunctionBuilder.get_invocation_str` | public target/global `0/0`; reference target/global `1/1`, only `boltons/funcutils.py` |
| Click | `click.testing._NamedTextIOWrapper.close` | public source unavailable/global `0`; reference target/global `1/1`, only `src/click/testing.py` |
| Flask | `flask.sansio.app.App.add_url_rule` | public target/global `0/0`; reference target/global `1/1`, only `src/flask/sansio/app.py` |
| Starlette | `starlette.responses.Response._wrap_websocket_denial_send` | public source unavailable/global `0`; reference target/global `1/1`, only `starlette/responses.py` |

The implementation is within the exact Section 14 budgets:

- `scripts/contain/Dockerfile`: 6 lines.
- `scripts/contain/contamination-spec.json`: 1 line.
- `scripts/contain/probe.py`: 150 lines.
- `scripts/contain/runtime.py`: 293 lines.
- `scripts/contain/` aggregate: exactly 450 lines.
- `scripts/run_batch.py`: exactly 610 lines.
- `tooling/taskcheck.py`: 660 lines, below the later 700-line cap; its Section
  14 change is the minimal request-key validation amendment.

`runtime.py` contains no semicolon-separated or compressed multi-statement
lines. The runner binds the exact task manifest through queue, preflight,
launch, scoring, result, and verify; sealed scoring goes through the wrapper on
the image's pinned interpreter; host/container JSONL requires a terminal
summary; the Section 14 task/spec/image/interpreter/security maps are exact and
fail closed. Host mode discovers and records interpreter prefixes and
site-packages and records malformed PEP-263 fixtures without treating them as
contamination; container mode scans from `/` and fails on every structural or
decode error.

The final non-Docker focused suite passed 34/34 in 93.651 seconds:

```text
python3 -B -m unittest \
  tests.test_containment \
  tests.test_run_batch \
  tests.test_section14_preflight -v
```

A scoped `git diff --check` passes for the implementation, tests, and handoff
changes. An unscoped cached check is intentionally not claimed: the complete
upstream task trees retain their original trailing whitespace and documentation
lines that Git heuristically labels conflict markers, and Section 14 forbids
normalizing those full-scale source bytes. All four explicit finalized Section
14 preflights pass; a final checker sweep reproduced public red, reference green
twice, and blind green. The complete repository suite also now passes:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
# 213 tests in 334.934s; OK (skipped=6)

PYTHONDONTWRITEBYTECODE=1 python3 tooling/test_taskcheck.py -v
# 14 tests; OK
```

Every Docker-dependent assertion remains a later acceptance gate.

## Blind launch ledger and exclusions

There were exactly 22 blind launches. The selected tasks account for four
single-launch resolved solves. The remaining 18 launches were bounded
calibration failures or mechanically rejected work:

| Candidate | Launch accounting and terminal disposition |
|---|---|
| `full-packaging-marker-pickle` | 3: xhigh contradiction-stop interrupt/no output; xhigh 900-second timeout/no output; high materialized `R1=T,R2=T,R3=F,G1=T`. Dropped unresolved. |
| `full-packaging-prerelease-bounds` | 3: xhigh contradiction-stop interrupt/no output; xhigh 900-second timeout/no output; high materialized `R1=F,R2=F,R3=F,G1=T`. Dropped unresolved. |
| `full-tabulate-jsonl-cli` | 3: first materialized `R1=F,R2=T,R3=F,G1=T` and cache junk; second interrupted at the mandatory contradiction stop; third terminated when the trackability conflict was confirmed. Dropped because the retained upstream `.gitignore` line `.*` hides task-owned dotfiles including `.issue-contract.md`; full-scale rules forbid editing it. |
| `full-pytest-fixture-closure` | 3: high materialized `R1=T,R2=F,G1=T`; xhigh materialized the same; max timed out at 900 seconds with no replacement. The timeout cleanup reported a non-empty temporary workspace, which was preserved. Dropped unresolved. |
| `full-attrs-field-aliases` | 3: xhigh materialized `R1=F,R2=F,G1=T`; max remained alive at 25:29 wall time despite the 900-second wrapper timeout and was interrupted (`exit=1`, 72,368 tokens, no replacement), with possible system-sleep versus monotonic-clock ambiguity; high materialized the same unresolved tuple. Dropped. |
| `full-filelock-async-cancel-atomicity` | 3: xhigh exact 900-second timeout/no output; high materialized `R1=T,R2=F,R3=T,G1=T`; high exact 900-second timeout/no replacement. Dropped at the cap. Its source gate itself passed: the public PR-652 pre-stack head `63a038a...` isolates issue #640 before dependent issue #634 was stacked, whereas the eventual main squash bundled both. That non-main-ancestry caveat is explicit in provenance and was not the rejection reason. |

The packaging source-eligibility ruling is **non-blocking PASS, with disclosure**.
The adopted plan says real, closed, test-covered “issue” and mechanically
requires an HTTPS `issue_url`; it contains no standalone-non-PR discriminator.
GitHub PR [#1171](https://github.com/pypa/packaging/pull/1171) and
[#1311](https://github.com/pypa/packaging/pull/1311) are closed/merged,
test-covered issue-model work items. Inventing a standalone-tracker-only rule
would add a requirement absent from the plan and validator. Both tasks were
dropped solely at their blind caps, and the final cohort does not depend on
this interpretation.

Available rejected raw evidence is durable:

- `handoffs/SECTION14_REJECTED_BLIND_EVIDENCE_2026-08-24.tar.gz`:
  SHA-256 `b257760588fb47ff9138a18a5b980a524dc565820f89ef74b2a041db78de9c65`,
  1,307 entries. It contains available terminal trees/provenance for tabulate,
  both packaging tasks, pytest, and attrs, plus pytest's timeout scratch.
- `handoffs/SECTION14_FILELOCK_BLIND_ATTEMPT2_2026-08-24.tar.gz`:
  SHA-256 `90ffaaddfe4a895757853b0291334db682be969b054af9ca27cb7870a009474b`,
  96 entries. A fresh rescore reproduces the recorded partial tuple.
- The rejected working trees remain recoverable under
  `/private/tmp/mdseval-section14-rejected/` for this environment.

Blindsolve's atomic replacement semantics did not preserve every earlier
overwritten materialization. The exact launch/outcome ledger above is
preserved. For overwritten or no-output launches, no raw tree, captured
stdout/stderr, or durable output hash exists.

## Yield and screened-source decisions

The mechanically defensible pre-build yield is:

| Stage | Count |
|---|---:|
| Unique repositories screened | 31 |
| Substantive issues considered | at least 83 |
| Tasks reconstructed/built | 11 |
| Source+blind selected cohort | 4 |
| Mechanically admitted at this pre-build review | 0 |

The issue count is intentionally a floor: 83 unique substantive decisions have
preserved counts, while the original HTTPX screening count was not preserved.
No larger number may be inferred. The 11 reconstructions were boltons, Click,
tabulate, two packaging tasks, pytest, attrs, Flask, Starlette, filelock, and
virtualenv.

Major non-blind source decisions were ordinary mechanical yield, not manual
waivers: virtualenv's tracked `.dockerignore` hid task bytes; urllib3's root
`.*` ignore rule was incompatible with trackability; Django, Uvicorn, and
jsonschema had tracked symlinks; Rich depended on an unfair generated
Unicode-data reconstruction; Typer lacked strong close/fix attribution; and
AnyIO and pip remained promising but unbuilt after stronger candidates were
available. None was forced into a weakened or pruned task.

## Development-stage corrections and audit trail

- Click's first checker budget nested `15+15+30=60` seconds beneath a 60-second
  outer limit. It was corrected before finalization to `12+12+25=49`; repeated
  public/reference/blind scores are deterministic.
- A first independent import-target check omitted `-B` and created eight cache
  directories in boltons/Click task trees. This was disclosed immediately;
  all were removed before admission or any subject attempt, and the exact
  public hashes were restored. Subsequent subprocesses used
  `-B`/`PYTHONDONTWRITEBYTECODE`.
- Premature builder cache/calibration placeholders in attrs and Flask were
  removed before their first blind calls. Flask's current calibration marker is
  a distinct post-solve artifact in the required order.
- Tabulate's trackability contradiction caused a stop and rejection, not an
  edit to its full upstream `.gitignore`.
- The original filelock reconstruction was corrected before blind exposure
  from the bundled main squash to the public issue-640-only pre-stack commit;
  its provenance records why.

These were development-stage repairs or explicit rejections. No selected
source, contract, checker, provenance, or captured subject-attempt byte was
changed; the disclosed transient cache directories were removed and hashes
rechecked.

## Gates still outstanding

This review deliberately precedes image construction. The following facts are
**not yet established** and remain mandatory:

1. Build each sealed per-task image offline from its exact lock, then record
   the content-addressed image digest.
2. Run the final hashed four-task spec through the same probe code. For each
   task the host control must be explicit `EXPECTED_RED`, or exact `N/A` with
   reason and positive absence evidence. Every container leg must be green,
   including mounts, global scan, network policy, agent home, interpreter set,
   sealed dependencies, runtime/security identity, and scoring identity.
3. Run taskcheck admission and verify **inside** each task's image on the pinned
   interpreter. Only then may the admitted count move from zero to four. Commit
   manifests, ledger, image digests, and complete probe evidence without
   changing task bytes.
4. Queue one unapproved/unlaunched v2 `REQUEST.json` for the four admitted
   tasks: 3 attempts each, 12 nominal calls, the standard replacement cap,
   `runner.timeout_seconds: 600`, exact image/spec/interpreter bindings, and
   the required top-level comparability note marking the boundary with prior
   300-second batches. Then stop for Wade.

If an image, admission, or probe gate fails, the result is operational
`BUILD_REJECTED`, not a difficulty reading. No live subject call is authorized
by this report. Only a later verified usable batch may produce
`HEADROOM_OBSERVED_AT_FULL_DIFFICULTY` or
`NO_HEADROOM_OBSERVED_AT_FULL_DIFFICULTY`; neither label grants standing
permission. The dated result and final yield ledger belong in
`handoffs/PROCESS_FINDINGS` after that result exists, not before it.

Final verdict: **GO TO THE REMAINING MECHANICAL PRE-SPEND BUILD PATH ONLY.**
The source, blind-calibration, checker, contamination-spec, and non-Docker
tooling gates are ready. Images, admission, probes, and the 600-second REQUEST
remain outstanding, and subject execution remains prohibited until Wade
approves that exact queued request.
