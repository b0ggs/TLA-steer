# TLA-Steer: four-hour prototype implementation plan

> Status: implementation-ready scope for the hackathon prototype.
>
> Deadline: four hours from the start of implementation.
>
> This plan deliberately optimizes for build, test, run, and one focused
> iteration. It is not a production-hardening plan.

## Outcome

Build one complete `TwoLights` comparison:

1. One `gpt-5.6-sol` `xhigh` direct translation.
2. One `gpt-5.6-sol` `xhigh` Planner-generated declarative inference program.
3. A semantic-step SMC run using `gpt-5.6-luna` `low` Followers.
4. The same independent exhaustive verifier applied to both selected Python
   artifacts.
5. A durable comparison containing tokens, timings, calls, errors, SMC traces,
   artifacts, and verifier results.

The prototype is successful even if neither arm produces correct Python. The
success condition is that the complete path runs, the official artifact from
each arm is selected without looking at final verifier results, correctness is
decided reliably, and the evidence is preserved.

The intended command is:

```bash
python -m tla_steer compare --config configs/prototype.json
```

An offline report command must reproduce the comparison without model calls:

```bash
python -m tla_steer report runs/<run-id>
```

## Where the project is now

`TLA-steer` currently contains design documents, `TwoLights.tla`,
`TwoLights.cfg`, the DisCIPL paper, and the installed `.scope-gate-venv`. It
does not yet contain a Git repository, Python package, model runner, SMC
engine, oracle, verifier, test suite, or run artifacts.

The correct foundation exists separately at:

```text
/Users/wade/Documents/MDs_EVAL
branch: time-token-challenge
commit: b6db4d3544f0d6fb026c6d9bf68203eae7d5e391
```

That checkout has unrelated working-tree changes. The implementation must be
based on the clean commit object, not copied from the live dirty tree. The new
repository should preserve that commit as its base history or import the exact
commit as a pinned subtree. The current TLA-Steer documents and inputs are then
added on top.

Immediate readiness facts:

- Docker Desktop is installed, but its daemon is not currently running.
- The foundation's configured `/private/tmp/mdseval-interpreters-sealed` tree
  is absent.
- No `tla2tools.jar` is present.
- The current host CLI is `codex-cli 0.151.0-alpha.7.2`.
- `scope-gate 0.1.0` works, but it is a contract evaluator, not the model
  sandbox or dispatcher.

These facts create a 20-minute runtime gate. They do not justify rebuilding
the missing infrastructure during the hackathon.

## Frozen prototype scope

### Input

Only:

- `TwoLights.tla`
- `TwoLights.cfg`
- the six fixed configuration values already in that file

There is no generic TLA+ parser in this prototype.

### Python artifact contract

Every generated artifact is a single `candidate.py` containing:

- the six configured constants;
- an exact `INITIAL` dictionary;
- seven pure action functions;
- an `ACTIONS` dictionary mapping the original TLA+ labels to those functions.

The required functions are:

```text
tick
a_green_to_yellow
a_yellow_to_red
a_red_to_green
b_green_to_yellow
b_yellow_to_red
b_red_to_green
```

Each action accepts one state dictionary and returns either one exact successor
dictionary or `None`. It must not mutate its input. Implicit TLA+ stuttering is
not a named action in this contract.

Trusted code supplies constants, imports-free module boilerplate, and the
`ACTIONS` mapping. Followers generate only `INITIAL` and the seven action
fragments.

### Experimental arms

```text
direct     = gpt-5.6-sol,  xhigh, one complete candidate
Planner    = gpt-5.6-sol,  xhigh, at most two schema attempts
Followers  = gpt-5.6-luna, low,   no proposal retries
N          = 8 logical particles
C          = 4 active Follower calls
steps      = 8 semantic units
ESS gate   = N / 2
```

`N=2, C=2` is permitted only for smoke tests. The intended comparison remains
`N=8, C=4`. If service latency or allowance prevents that run, the smaller run
is reported honestly with its actual configuration; it is never relabeled.

Internal Codex subagents and all provider-side retrieval surfaces remain
disabled. Each turn is ephemeral and receives a fresh workspace and only the
files and prompt required for its role.

## Foundation adoption

Preserve these `MDs_EVAL` components rather than designing replacements:

- `src/mdseval/runner/codex_cli.py`: strict ephemeral `codex exec --json`
  command construction and capability shutdown;
- `src/mdseval/processutils.py`: process-group timeout and cleanup;
- `src/mdseval/capture.py`: redaction, JSONL validation, and usage parsing;
- `src/mdseval/fixtures.py`: fresh workspaces and symlink rejection;
- `scripts/contain/runtime.py`: contained subject launch when its sealed assets
  are actually available;
- the focused tests for those components.

Do not adapt the serial `scripts/run_batch.py` loop. Do not reuse its checker,
which co-locates candidate code and private evaluation assets. TLA-Steer adds a
small role-aware coordinator and a separate verifier beside the intact
foundation.

### Runtime Gate 0

Spend at most 20 minutes on the following:

1. Start Docker Desktop and inspect the existing images.
2. Check for the required foundation image, interpreter pin, dedicated OAuth
   profile, and valid fast seal.
3. Run the focused offline foundation tests.
4. Attempt one contained Luna call returning a tiny structured result.
5. Confirm strict JSONL parsing, reported usage, and cleanup.

If this passes, record `containment_mode = "mdseval_sealed"` and use the
contained subject launcher for all model turns.

If it fails because the external image or interpreter assets are absent, stop
at 20 minutes. Use a `prototype_local` adapter that still preserves the
foundation's explicit capability shutdown, clean ephemeral Git workspaces,
Codex sandbox, process cleanup, JSONL capture, and redaction. Record the weaker
containment mode prominently. Do not claim that this fallback reproduces the
anti-cheating boundary of the sealed MDs_EVAL environment.

No Docker image reconstruction, OAuth refresh redesign, or containment
hardening enters the four-hour critical path.

## Planner-generated inference program

The Planner emits JSON conforming to
`schemas/controller.schema.json`. This JSON is the prototype's restricted,
declarative inference program; arbitrary Planner-generated Python is not
executed.

It must contain exactly eight unique semantic targets:

1. `INITIAL`
2. `Tick`
3. `AGreenToYellow`
4. `AYellowToRed`
5. `ARedToGreen`
6. `BGreenToYellow`
7. `BYellowToRed`
8. `BRedToGreen`

For each step, the Planner chooses:

- ordering;
- a Follower proposal instruction;
- bounded probe states;
- expected probe successors used for incremental scoring.

The host validates schema, complete target coverage, unique symbols, state
shape, and probe limits. It does not correct the Planner's expected answers.
Incorrect Planner constraints are an experimental failure, not a harness bug.
The Follower receives the probe states and instruction, but not their expected
successors.

One Planner repair turn is allowed only after schema-validation failure. The
repair receives the validation error, not final-verifier feedback.

## Follower proposal contract

Each stateless Follower receives:

- the full TLA+ source and configuration;
- the frozen Python contract;
- the current partial Python artifact;
- the current controller step;
- the Planner's proposal instruction and probe inputs.

It returns structured JSON:

```json
{
  "schema_version": "tla-steer-proposal/0.1",
  "step_id": "tick",
  "python_fragment": "def tick(state: dict) -> dict | None:\n    ..."
}
```

The host accepts exactly one assignment for `INITIAL` or exactly one function
with the required symbol for an action. Imports, extra definitions, wrong
symbols, invalid syntax, mutation, exceptions, nondeterminism, and timeouts
make the proposal's incremental weight zero.

## SMC algorithm

Each particle contains:

```text
particle_id
parent_id
ancestry
completed_step_index
fragments
partial_artifact
current_log_weight
score_history
status
```

Use a synchronous barrier at every semantic step:

1. Extend all live particles with fresh Luna calls, capped by one host
   semaphore at `C`.
2. Parse and attach exactly one new fragment per particle.
3. Score only that new semantic unit. Do not rescore the full prefix and
   double-count earlier evidence.
4. Add `log(q)` to the current log weight.
5. Normalize weights and compute `ESS = 1 / sum(w_i ** 2)`.
6. If the step is not final and `ESS < N/2`, draw `N` ancestors independently
   from the normalized weights, clone them with new IDs, record ancestry, and
   reset algorithmic weights uniformly.

Use paper-style multinomial resampling with a recorded PRNG seed.

### Incremental score

For `INITIAL`:

```text
q = number of fields matching the Planner's expected initial state / 5
```

Missing or extra keys make `q = 0`.

For an action, execute every Planner probe twice on fresh input copies. The
probe set must include an expected enabled and disabled case. Compute:

```text
q = 0.25 * enabledness_precision
  + 0.25 * enabledness_recall
  + 0.50 * exact_successor_rate_on_expected_enabled_cases
```

This prevents an always-`None` action from receiving a high score. Exact
successor comparison also catches dropped frame conditions.

A structural/runtime failure or `q=0` gives zero weight. If all particles have
zero weight, record `particle_collapse` and stop. Do not add a recovery
algorithm to the prototype.

### Official final selection

After the eighth step:

1. Sample one official DisCIPL artifact proportional to final particle
   weights.
2. Freeze its bytes and hash.
3. Only then run the independent final verifier.

Do not choose the highest-weight or verifier-passing artifact after seeing
verification results. Other distinct final particles may be verified afterward
for diagnostics and reported separately as `highest_weight_exact` and
`any_particle_exact`.

## Independent correctness verifier

The prototype uses a trusted, hand-derived executable oracle for the fixed
`TwoLights.cfg` instance. It must not be called TLC-backed until a real TLC
extractor is implemented.

Before grading any candidate, the oracle must self-check:

- 3,528 type-correct states;
- 6,960 labeled transitions;
- per-action edge counts of `2592, 672, 1008, 504, 672, 1008, 504`;
- BFS from the exact initial state reaches all 3,528 states;
- every oracle successor is type-correct.

An oracle self-check failure is `EVALUATOR_ERROR`, and no candidate is graded.

For each candidate, compare all `3,528 * 7 = 24,696` state/action pairs. Call
each candidate action twice on fresh inputs and check:

- exact `INITIAL`;
- API and constant contract;
- determinism;
- no input mutation;
- result shape and types;
- exact enabledness;
- exact labeled successor;
- rooted reachable-state equality.

Keep the oracle and expected results in the trusted host. The candidate runner
receives only inputs and returns observed outputs. When the sealed foundation
is available, run it in a networkless scratch container containing no oracle.
The fallback uses an isolated `python -I -S` subprocess and records that it is
prototype containment, not a hostile-code security boundary.

Top-level outcomes are:

```text
EXACT
SEMANTIC_MISMATCH
INVALID_CANDIDATE
EVALUATOR_ERROR
```

Also retain initial exactness, transition soundness/completeness,
rooted-state exactness, per-action false-positive/false-negative/wrong-
successor counts, frame violations, runtime/contract failures, and capped
concrete counterexamples.

## Evidence and metrics

Each call writes an isolated spool. Only the trusted coordinator creates the
aggregate run summary after workers finish.

```text
runs/<run-id>/
  manifest.json
  direct/
    calls/<call-id>/{intent.json,events.jsonl,stderr.txt,final.json}
    candidate.py
    verification.json
  discipl/
    planner/{intent.json,events.jsonl,controller.json}
    calls/<call-id>/{intent.json,events.jsonl,stderr.txt,final.json}
    trace.jsonl
    selected-candidate.py
    verification.json
  rate-card.json
  summary.json
  summary.md
```

Persist raw exposed usage without projection loss:

```text
input_tokens
cached_input_tokens
cache_write_input_tokens
output_tokens
reasoning_output_tokens
usage_reported
```

Also record:

- role, arm, model, effort, particle, parent, step, and call IDs;
- requested model and returned model when exposed;
- call duration, queue duration, verifier duration, arm makespan, and run wall
  time;
- calls, retries, timeouts, failures, and maximum observed concurrency;
- prompts, outputs, hashes, fragments, candidate artifacts, errors, scores,
  weights, ESS, ancestry, resampling, selection, and stopping reason;
- final correctness metrics;
- API-price-equivalent totals from the dated static rate card.

Cached input is subtracted from total input before applying the ordinary input
rate. Reasoning-output tokens are retained as a diagnostic subcount and are not
charged a second time when they are already included in output tokens.

Do not implement a database, dashboard, live pricing fetch, first-token
instrumentation, or a broad error classifier. Raw events are retained so more
measurements can be extracted later.

## Minimal source layout

Add only:

```text
src/tla_steer/
  cli.py             compare, smoke, verify, and report commands
  contract.py        fixed candidate and controller/proposal validation
  oracle.py          trusted TwoLights relation and self-check
  verifier.py        candidate runner protocol and exact comparison
  worker.py          role-aware adapter over the MDs_EVAL runner/capture
  smc.py             particle state, weights, ESS, and resampling
  evidence.py        per-call spools, aggregation, and report

schemas/
  controller.schema.json
  proposal.schema.json

prompts/
  direct.md
  planner.md
  follower.md

configs/
  prototype.json
  rate-card-2026-08-30.json

tests/
  test_oracle.py
  test_verifier.py
  test_worker_fake.py
  test_smc.py
  fixtures/candidates/
```

No web service or UI is needed.

## Four-hour build, test, and iteration schedule

| Time | Build | Acceptance gate | Cut if blocked |
|---|---|---|---|
| `0:00-0:20` | Establish clean pinned foundation; run Runtime Gate 0; freeze `candidate.py` contract | One structured Luna smoke result has valid JSONL, usage, timing, and cleanup | Switch to labeled `prototype_local`; do not rebuild Docker or sealed interpreters |
| `0:20-1:00` | Implement oracle, golden candidate, candidate runner, and exhaustive verifier | Oracle counts pass; golden candidate is `EXACT`; wrong initial, loose/tight guard, A/B frame-copy, and mutation fixtures fail correctly | No TLC, generic parser, hidden-test framework, or broad sandbox work |
| `1:00-1:35` | Implement generic role-aware worker, call spool, usage aggregation, and direct arm | Fake worker and one live structured call persist artifact, raw JSONL, usage, duration, and verifier result | Reuse foundation parser; no new telemetry framework |
| `1:35-2:15` | Implement schemas, Planner validation, particle state, scoring, ESS, multinomial resampling, and fake Followers | Deterministic fake run shows eight partial steps, cumulative weights, an ESS decision, ancestry, weighted final selection, and exact verification | Fixed controller DSL only; no generated Python controller |
| `2:15-2:50` | Launch real Planner; integrate Luna; run `N=2,C=2` smoke | Controller validates; two particles complete at least two steps with valid trace and usage | One Planner schema repair only; no Follower repair loop |
| `2:50-3:35` | Run intended `N=8,C=4` comparison; inspect the first concrete failure; make at most one prompt or parser correction and rerun from scratch | Both official artifacts are frozen before verification; totals reconcile with call records; report renders | If service limits block target, retain actual smaller configuration; never hand-repair model artifacts |
| `3:35-4:00` | Freeze prompts/config, run focused tests, generate offline report, rehearse demo | Tests pass; offline report reproduces summary; limitations and containment mode are visible | No features after `3:35` |

The direct Sol call and Planner call can run while deterministic verifier and
SMC code is being built, once their prompts and schemas are frozen.

## Focused test suite

Run only tests that protect the demo path:

```bash
python -m pytest -q \
  tests/test_oracle.py \
  tests/test_verifier.py \
  tests/test_worker_fake.py \
  tests/test_smc.py
```

Required fixtures:

- golden exact candidate;
- wrong initial `Offset`;
- loose `Tick` guard producing an extra edge;
- tight or always-disabled action producing missing edges;
- A/B copy or frame-condition error;
- input-mutating action;
- deterministic fake Planner and Followers that force a resampling event.

One live smoke test validates OAuth/model/JSONL integration. Live calls are not
part of the default unit-test command.

## Explicitly deferred

- General TLA+ parsing or compilation.
- TLC installation, DOT parsing, and reference extraction.
- More specifications or arbitrary constants.
- Multiple initial states or multi-successor individual actions.
- Liveness, fairness, and explicit stuttering checks.
- Arbitrary Planner-generated Python or LLaMPPL execution.
- Token-level particles, token masks, continuation log probabilities, and
  proposal/prior importance correction.
- Counterexample-driven repair and MCMC rejuvenation.
- Luna-direct, best-of-N, or other control arms.
- Repeated trials and statistical claims.
- Production OAuth refresh ownership and concurrency soak tests.
- Reproducible image construction, new App Server integration, seccomp work,
  resource hardening, orphan reapers, generalized anti-cheating certification,
  and portability work.
- Dashboards, databases, CI, packaging polish, and deployment.

Those are follow-on work. None may displace the end-to-end comparison,
verifier, evidence, tests, or offline demo during the four-hour build.
