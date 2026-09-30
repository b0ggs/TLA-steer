# Guarded checker phase

This phase fixes checker defects and supplies one fail-closed Linux execution
adapter for both partial scoring and final verification. It does not establish
live-model performance, savings, or a verified hostile-code boundary on every
host. The previous r2 offline milestone remains a separate reviewed baseline.

## Common conformance contract

The direct prompt is also the artifact contract supplied to Planner/Followers.
All arms must use its documented guard/update subset: local assignments, guards,
returns, scalar arithmetic/conditions, literal dictionaries, field access and
explicitly allowed pure builtins/dictionary methods. `dict(state)` and
`state.copy()` are supported. Writes are allowed only through statically known
fresh local dictionaries or their local aliases. Input aliases, persistent
module state, global/nonlocal writes, defaults, decorators, reflection,
executable annotations and arbitrary calls are rejected.

This is a deliberately limited conformance check, not a proof of purity for
arbitrary Python and not a security sandbox. Unsupported syntax yields a
contract failure/INVALID_CANDIDATE, not SEMANTIC_MISMATCH. It prevents the
known delayed-history variants from passing just because two observed calls
happen to agree. Both runtime observers additionally compare input value types
and snapshot the first result before the second call; Python's `False == 0`
and `0.0 == 0` no longer hide mutation or shared-result aliasing.

## Execution boundary

Unknown candidate bytes require system Python, bubblewrap and prlimit on a
compatible Linux host. A real isolated-launch preflight must succeed before
any provider call or credential-profile lookup. Standalone verification also
preflights unknown bytes. Failure never selects an unguarded fallback.

Both scorers use the same launcher. It clears the environment, permits only a
locale setting, creates private user/PID/network/IPC/UTS/cgroup namespaces,
drops capabilities, disables further user namespaces, and binds only system
Python/runtime libraries plus a temporary candidate/runner directory read-only.
Application package directories are masked. Repository files, user home,
credentials and the parent oracle are not mounted. Requests contain only
required input states, symbols and public constants, never private expected
successors. Filesystem roots, proc and dev are remounted read-only; the writable
temporary filesystem is capped at 16 MiB.

Configured limits: 256 MiB address space and 15 CPU seconds per process,
32 processes, 64 descriptors, no core dumps, 8 MiB per output file, and the
caller's wall timeout (5 seconds partial, 30 seconds final). These are per-process
limits rather than a cgroup-wide aggregate resource guarantee. Output is
file-backed and limited during writes, with bounded reads and process-group
cleanup. No claims about untested kernel escape resistance are made.

Only exact pinned reviewed fixture bytes, or exact fixed host assemblies of
pinned golden/frame-copy fragments, may use the local fixture path. That path
is labeled `reviewed_fixture_local`, is not a hostile-code boundary, and exposes
no arbitrary-source unsafe switch. Local fixture mode is for regression tests;
its timings and synthetic usage are not live measurements.

## Verification status and user-run prerequisite

In the implementation cloud workspace, bubblewrap 0.12.0 is present but a real
namespace preflight fails: creating a NETLINK_ROUTE socket is not permitted.
No setting was changed and network isolation was not weakened. Thus actual
isolated candidate execution and hostile filesystem/network/credential probes
remain unvalidated here. Unit tests verify command construction, routing,
fail-closed behavior, reviewed-byte enforcement, local fixture resource limits
and the checker regressions; those tests do not substitute for an isolation pass.

On a compatible Linux host, the non-provider preflight is:

```sh
PYTHONPATH=src python3 -c 'from tla_steer.execution import preflight; print(preflight())'
```

A successful launch is only the first host check. Before generated code or a
live three-arm screen is authorized, independently test filesystem/credential
inaccessibility, private-answer separation, network denial, resource limits and
process cleanup there. Current provider integration and real usage capture also
remain unvalidated. No model call is made by preflight. No platform-portability
work, security-setting changes, TLC, broad benchmark or historical test repair
is included in this phase.

Scoped aggregate:

```sh
PYTHONPATH=src python3 -m unittest tests.test_oracle tests.test_verifier tests.test_smc tests.test_worker_fake tests.test_execution -v
```

Also run the repository-required full unittest discovery and report inherited
errors/skips separately. The user's Scope Gate waiver remains in effect; no
formal gate approval is claimed.
