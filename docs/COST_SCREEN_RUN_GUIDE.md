# Offline three-arm cost screen

Run from this checkout with Python 3.12 or later:

```sh
PYTHONPATH=src python3 -m tla_steer offline-screen
PYTHONPATH=src python3 -m tla_steer report runs/offline-cost-screen-r2/<run-id>
```

No OAuth profile, API key, provider access, or paid call is needed. The command
uses the real coordinator, worker capture, SMC, and final verifier with fixed,
hash-pinned local fixtures and invented token counters. It validates machinery;
it does not measure model quality, real usage, charges, or savings. Wall times
measure local fixture execution only. Legacy `compare` and `smoke` commands are
live two-arm paths and are outside this offline milestone.

The three arms are frontier-alone (`direct`), cheap-alone (`cheap_alone`), and
frontier-planned cheap followers (`discipl`). Cheap-alone uses the same direct
code path, source bytes, prompt, output contract and final checker. Only its
model and reasoning effort policy differ, aside from bookkeeping identifiers.
The screen fixes N=2, concurrency=2, and seed=20260830. It does not accept
candidate files, alternative fixtures, or arbitrary model outputs.

Both TwoLights files must match the approved SHA-256 values in
`configs/prototype.json` and the coordinator before any worker starts. The
run saves those exact inputs. Executed candidate fragments must come from the
pinned reviewed `golden.py` and `frame_copy_error.py` fixtures. This restriction
is for the offline fixture path; it is not a general sandbox for generated code.

The fixture deliberately gives one SMC particle a wrong frame-copy action.
Final weights are 1/3 and 2/3; the seeded draw selects the less likely, incorrect
particle 0. Expected outcomes are EXACT, EXACT, SEMANTIC_MISMATCH. The checker
must preserve that result rather than pick the best-graded artifact. Every
available official artifact and selection record is frozen before final grading.

Expected synthetic call counts: 1 frontier-alone, 1 cheap-alone, 1 Planner,
16 Followers. Each completed fixture call reports input=101, cached=41,
cache-write=7, output=23 and reasoning-output=11. The dated frozen rates yield
$0.00213989 across all 19 invented calls. These are test inputs, not observed
provider usage or this assistant's billed usage.

Reporting reconciles coordinator attempted counts with both intent and result
spools. Failed calls with complete usage remain charged. Missing, malformed,
duplicated or inconsistent evidence makes affected totals UNKNOWN (JSON null),
never zero/free. The report distinguishes attempted calls from observed records.
The run-local rate card is frozen; changed prices are rejected during replay.
Old evidence without coordinator counts cannot establish complete accounting.

## Validation

```sh
PYTHONPATH=src python3 -m unittest tests.test_oracle tests.test_verifier tests.test_smc tests.test_worker_fake -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The first command is the one mapped scope check, covering all six agreed risks.
The full discovery command also covers inherited MDs_EVAL tests. Historical
scout-evidence failures and skips must be reported separately, not repaired in
this phase. No test may call a live provider.

The frozen phase contract is
`.scope-gate/contracts/tla-steer-cost-screen-r2.json`. On September 30, 2026,
the user explicitly waived the unavailable Scope Gate evaluator for this work.
The contract bounds and independent adversarial review still apply; no formal
Scope Gate approval is claimed. Historical instructions are preserved.

Stop after this offline milestone. Live model comparison remains unvalidated
and requires separate approval, real usage evidence, statefulness/type-mutation
verifier work, and an actual execution boundary before generated code runs.
