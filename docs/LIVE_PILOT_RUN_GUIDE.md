# Bounded three-arm pilot

This is a small TwoLights pilot, not a broad benchmark or a savings result.
It compares frontier-alone, cheap-alone, and frontier-planned cheap followers.
All arms use the same pinned source, output contract and final checker. The two
standalone arms also share the same prompt and direct-generation path.

## Preview safely

From the repository with Python 3.12 or later:

```sh
PYTHONPATH=src python3 -m tla_steer pilot --dry-run
```

`pilot` without flags has the same preview behavior. Preview validates the
frozen configuration/source and prints model roles, source/rate-card hashes,
seed and call limits. It performs no credential lookup, subprocess launch,
provider call, candidate execution, or run-directory write. Preview is not an
isolation or provider-readiness pass.

## Host readiness and execution

The generated-code boundary is still **unvalidated**. The implementation cloud
cannot create the required network namespace operations. The GitHub Ubuntu
24.04 validation at commit `32af882` fixed the pre-namespace thread-limit bug
but then stopped at `bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted`.
All later isolation probes were not run. The permission cause remains
unconfirmed. No host policy was weakened and no privileged fallback was used.

Use a compatible Linux host as an ordinary, unprivileged user. It needs system
Python, bubblewrap and prlimit, and must pass the controlled isolation checks
in `tooling/validate_isolation.py` before generated-code or model execution is
authorized. See `GUARDED_EXECUTION.md` for the boundary and limitations. Do not
disable security policy to make the checks pass. macOS is not supported by this
execution adapter.

The live provider path requires an installed compatible Codex CLI and an
existing dedicated Codex OAuth profile supplied through
`TLA_STEER_CODEX_HOME` (or the legacy `MDSEVAL_CODEX_HOME`). Credentials stay
outside the repository and run evidence. Current account access to the frozen
`gpt-5.6-sol`/`xhigh` and `gpt-5.6-luna`/`low` roles, provider response formats,
returned model identities and real usage capture remain unvalidated. The
program does not silently substitute other models.

After those prerequisites and authorization for actual model use:

```sh
PYTHONPATH=src python3 -m tla_steer pilot --execute --call-budget 20
PYTHONPATH=src python3 -m tla_steer report runs/<run-id>
```

Live execution performs a real isolation preflight before credential lookup or
any provider call. Failed preflight exits with code 3. There is no unguarded
fallback. These instructions do not claim that a live run has been performed.

## Fixed budget and interpretation

N=2, concurrency=2, seed=20260830. Each standalone arm receives one attempt.
The Planner gets one attempt and at most one repair for an invalid controller;
there are at most 16 Follower calls with no retry. A normal full run uses 19
calls, or 20 with Planner repair. Each call has a 300-second timeout.

`--execute` requires an explicit admission budget from 1 through 20. Failed
calls consume that budget. This is a call-count ceiling, **not a dollar/token
cap**. A lower budget may terminate an incomplete comparison. Admission is
atomic across concurrent Followers; rejected admissions never launch a worker.
Already-running calls retain their evidence. Budget exhaustion records
`pipeline_error` and prevents official grading; it is not a model-quality result.

Every available official candidate, digest and weighted SMC selection is saved
before final grading. The report reconciles admitted attempts with intent and
result records, includes failed calls, and leaves missing usage/cost UNKNOWN.
The frozen rate card permits replay of API-price-equivalent estimates; these
are not actual OAuth charges. Model correctness, research savings and actual
spending cannot be inferred from the synthetic fixture tests.

## Offline checks

```sh
PYTHONPATH=src python3 -m unittest tests.test_worker_fake.PilotTests -v
PYTHONPATH=src python3 -m unittest tests.test_oracle tests.test_verifier tests.test_smc tests.test_worker_fake tests.test_execution -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

All tests use reviewed fixtures/fake provider processes. Inherited scout tests
have seven historical errors and seven skips; report them separately. The user
waived the unavailable Scope Gate evaluator; no formal gate pass is claimed.
