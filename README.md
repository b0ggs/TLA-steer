# TLA-Steer: one verifier-checked TwoLights comparison

Paused as of 2026-10-05. See [NEXT_STEPS.md](NEXT_STEPS.md) for the preserved
checkpoint and conditional resume steps.

The original two-arm prototype is implemented and has deterministic offline
coverage. Live provider integration and isolated execution on a compatible user
host still require validation. Start with the [two-arm run guide](docs/TWO_ARM_RUN_GUIDE.md).

The finite goal is one reproducible comparison:

1. A frontier model produces one complete Python translation
2. The same frontier model plans eight semantic steps; cheaper Followers extend
   partial programs under sequential Monte Carlo (SMC)

Both selected artifacts are frozen before the same final checker grades them.
Incorrect outputs, particle collapse and higher orchestration cost are valid
experimental results. Infrastructure errors and missing evidence are reported,
not treated as a successful comparison.

## Implemented scope

Only the exact pinned `TwoLights.tla` and `TwoLights.cfg` are supported. There is
no general TLA+ compiler. The Planner emits validated declarative JSON, not
executable inference code. Followers propose `INITIAL` and seven action
functions in the shared guard/update subset. The Planner may order those eight
targets freely.

The harness owns partial scoring, cumulative weights, ESS-triggered multinomial
resampling, ancestry and seeded weighted final selection. It records attempted
and failed calls, raw redacted JSONL, artifacts, usage, timing, model identifiers
when returned, selection evidence and verification results. Model artifacts are
never hand-repaired or selected using their final grades.

The independent checker uses a hand-written TwoLights oracle over 3,528 states,
6,960 labeled edges and 24,696 state/action pairs. It checks exact initial state,
enabledness, successors, input mutation and observed determinism, with a shared
source-conformance restriction for both arms. It does **not** invoke TLC.
An `EXACT` result is agreement with this fixed oracle and artifact contract;
it is not a general TLA+ correctness proof.

## Frozen comparison

| Role or setting | Value |
|---|---|
| Direct frontier | `gpt-5.6-sol`, `xhigh`, one call |
| Planner | `gpt-5.6-sol`, `xhigh`, at most one schema repair |
| Followers | `gpt-5.6-luna`, `low`, no proposal retries |
| Intended comparison | `N=8`, `C=4`, eight steps |
| Smoke only | `N=2`, `C=2` |
| Normal / maximum comparison calls | 66 / 67 |
| Normal / maximum smoke calls | 18 / 19 |

These are configured identifiers, not a claim that the user's current account
can access them. Verify availability through the user-run smoke; do not silently
substitute models. Each worker has a 300-second timeout. Call-count limits are
not token, dollar or OAuth-credit limits.

`compare` and `smoke` run the original two arms. An existing optional
`offline-screen` exercises a cheap-alone control using reviewed fixtures and
synthetic usage. That control and the separate three-arm pilot are not required
to complete this prototype.

## Run and reproduce

From the repository root, after the run guide's prerequisites:

```sh
# Offline unit/integration checks; no provider calls
PYTHONPATH=src python3 -m unittest tests.test_oracle tests.test_verifier tests.test_smc tests.test_worker_fake tests.test_execution tests.test_capture -v

# User-run live stages, only after compatible-host and CLI checks
PYTHONPATH=src python3 -m tla_steer smoke --config configs/prototype.json
PYTHONPATH=src python3 -m tla_steer compare --config configs/prototype.json

# Reproduce a saved report without model calls or candidate execution
PYTHONPATH=src python3 -m tla_steer report runs/<run-id>
```

The [run guide](docs/TWO_ARM_RUN_GUIDE.md) gives the pinned checkout procedure,
credential-free prerequisite checks, host validation, OAuth setup, exact
commands and stopping criteria. No live calls run in the unit tests or CI.
The required full unittest discovery currently has seven inherited
`test_scout` errors caused by absent historical evidence and seven skips;
these are disclosed separately from the focused prototype checks.

## Execution and evidence limits

Generated candidate code requires the existing fail-closed Linux launcher:
system Python, bubblewrap, prlimit and working unprivileged namespaces. Direct
macOS execution is unsupported. Only exact reviewed fixture bytes may execute
through the labeled local test path; static source checks are not a sandbox.

The Codex generation worker remains labeled `prototype_local`, using the Codex
workspace sandbox rather than the sealed MDs_EVAL runtime. Candidate execution
uses a separate boundary for both partial and final checking. Read
[guarded execution](docs/GUARDED_EXECUTION.md) for the precise limits.

The latest credential-free [Linux runner attempt](https://github.com/b0ggs/TLA-steer/actions/runs/36803529525)
failed at preflight with `RTM_NEWADDR: Operation not permitted`; later isolation
probes were not run. Host-specific validation and real OAuth/model/usage capture
remain unverified. Do not bypass a failed preflight or weaken host security to
force a comparison.

Each run freezes a copy of the configured rate card. Reports use that snapshot
for API-price-equivalent estimates, not actual subscription charges. Unknown
usage or incomplete accounting stays unknown; failed calls with complete usage
still count. Synthetic fixture counters are not measured model usage or savings.

## Finish line and background

Implementation ends with the two audited integration repairs, scoped offline
verification, this corrected README and a pinned user-test handoff. User
validation is one host check, one smoke, one intended comparison and offline
report replay. A model need not win or produce correct Python.

The [finite completion plan](https://github.com/b0ggs/TLA-steer/pull/2#issuecomment-5932685011)
reconciles the current work with the [original implementation plan](IMPLEMENTATION_PLAN.md).
TLC extraction, additional specifications, required control arms, repeated
studies, platform adapters and further CI work are outside this finish line.
[ARCHITECTURE.md](ARCHITECTURE.md) preserves the broader design background;
it is not a claim that every proposed component is implemented.
The preserved MDs_EVAL package supplies the worker/capture foundation.
