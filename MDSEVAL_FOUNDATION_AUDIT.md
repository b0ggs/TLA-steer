# MDs_EVAL foundation audit

> Status: repository audit, not an implementation record.
>
> Audited: 2026-08-30
>
> Authoritative upstream branch: `time-token-challenge`
>
> Authoritative upstream commit:
> [`b6db4d3544f0d6fb026c6d9bf68203eae7d5e391`](https://github.com/b0ggs/MDs_EVAL/tree/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391)

## Purpose

`MDs_EVAL` is intended to be the **foundation** for this project's execution,
containment, OAuth, cleanup, and evidence-capture architecture. The goal is not
to copy isolated snippets into an unrelated harness. The goal is to preserve
its hardened security model and evolve that evaluator into a role-aware
TLA+-to-Python experiment.

The selected model configuration remains:

```text
direct frontier = gpt-5.6-sol, xhigh
Planner         = gpt-5.6-sol, xhigh
Followers       = gpt-5.6-luna, low
```

All model calls use Codex OAuth. The trusted host owns SMC state, scheduling,
verification, and evidence. Model turns do not communicate directly with one
another or receive hidden verifier data or unrestricted network access. The
Codex client process inside a worker does receive a temporary copy of
`auth.json`; the evaluated shell/tool permission surface is denied access to
it. A compromise of the client process or container would still expose that
copy.

## Executive conclusion

The `time-token-challenge` branch is a strong foundation for one contained
Codex turn. It contains real defenses against the failure modes encountered in
the earlier evaluation, including host-source discovery and provider-side
search/MCP access. Its containment, process cleanup, capability policy,
preflight, sealing, strict event parsing, redaction, and evidence conventions
should remain the base architecture.

It is not yet the complete foundation required by this experiment. Before it
can support a long-running Planner/Follower population, the derived system
must address two critical defects:

1. OAuth refresh state is not durable across disposable model homes, and the
   proxy does not currently permit the refresh host.
2. The existing checker places candidate code and private evaluation assets in
   the same writable environment.

The current batch runner is also intentionally serial and domain-specific. It
must evolve into a trusted role-aware coordinator rather than merely having
its parallelism flag increased.

## Evidence classification

This audit distinguishes three kinds of claims:

- **Code-verified:** directly established by the pinned implementation.
- **Repository-recorded:** described by committed traces, findings, or run
  artifacts, but not independently replayed during this audit.
- **Inference:** a security or architectural consequence of verified code.

The audit ran 76 relevant unit tests successfully in 106.4 seconds. It did not
make a live model call or perform a full Docker replay because the sealed
interpreter tree and complete image-build inputs are external to the clone.

## Foundation mechanisms verified in code

### Explicit Codex capability shutdown

The subject command uses strict, ephemeral, JSONL execution and ignores user
configuration and ambient rules. It explicitly disables web search, MCP and
apps, plugins, skills, browser/computer surfaces, subagents, hooks, memories,
goals, and other remote or delegated capabilities.

Source:
[`src/mdseval/runner/codex_cli.py`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/src/mdseval/runner/codex_cli.py#L34-L129)

This policy is foundational. Shell-network denial alone is insufficient
because hosted search, MCP, apps, and browser tools execute outside the
subject's shell-network boundary.

The current JSONL evidence allowlist recognizes only `command_execution`,
`file_change`, `agent_message`, and `todo_list`. A pinned Codex upgrade can add
benign event types and invalidate a run. The foundation must pin the Codex
build, update allowlists only through a version-qualified review, and continue
to fail closed on unknown retrieval or tool surfaces.

### Fresh attempt state

Each attempt receives a fresh public fixture, workspace, Git repository,
temporary Codex home, session area, output area, container identity, and
network identity.

Sources:

- [`scripts/run_batch.py`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/scripts/run_batch.py#L421-L429)
- [`scripts/contain/runtime.py`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/scripts/contain/runtime.py#L375-L437)

For this project, the same rule applies to every direct, Planner, and Follower
turn. Logical particle state remains in the trusted coordinator and is passed
into a fresh turn through a narrow prompt/artifact contract.

### Container containment

Subject containers run with the host UID/GID, which is non-root only when the
host process is non-root. They also use dropped capabilities,
`no-new-privileges`, a 256-process limit, separate mounts, fixed environment,
random names, and explicit teardown.

Sources:

- [`runtime security configuration`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/scripts/contain/runtime.py#L17-L46)
- [`container construction`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/scripts/contain/runtime.py#L404-L518)

The current implementation also sets `seccomp=unconfined` and lacks CPU,
memory, disk, file-size, and file-descriptor limits. Those are known gaps, not
properties to preserve.

### Model-channel and command-channel separation

Every attempt receives an internal Docker network. A separate Tinyproxy is the
only outward path. The trusted Codex client can reach hosted model endpoints
through the proxy while subject shell commands remain network-denied.

Source:
[`network lifecycle`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/scripts/contain/runtime.py#L520-L553)

This split should remain. Planner and Follower turns do not need network access
beyond the trusted Codex transport and never need direct peer-to-peer access.

### Active zero-spend containment preflight

Before a paid subject call, the repository uses App Server to resolve the
effective capability surface and actively tests denial of credential/session
reads, `/proc`, protected Git writes, evaluator-output writes, profile changes,
TCP, UDP, DNS, and other forbidden actions. Workspace writes are also tested
to confirm that the intended capability still works.

Source:
[`active policy preflight`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/scripts/contain/runtime.py#L805-L917)

Fast seals then bind the approved image, interpreter, contamination checks,
policy, mounts, sandbox mode, and subject surface.

Source:
[`fast seal validation`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/scripts/contain/runtime.py#L919-L1029)

This fail-closed qualification is a central part of the foundation. Every
Codex CLI/image change must invalidate the seal and require requalification.
The current contamination checks are task- and signature-specific; they are
not a generic proof that the complete image contains no TLA+ oracle, reference
graph, or answer artifact. The derived preflight must add TLA+-specific image
inventory and answer-leak canaries.

### Process and artifact cleanup

The runner creates a separate process group, applies timeout handling, and
makes a best-effort TERM/KILL pass over that process group. Containers and
networks are removed during normal and caught-failure cleanup. It does not
perform a separate post-cleanup survivor proof.

Source:
[`src/mdseval/processutils.py`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/src/mdseval/processutils.py#L23-L93)

The derived system should add Docker labels and a startup orphan reaper for
machine crashes or a hard-killed host coordinator.

### Evidence validation and redaction

The event collector rejects malformed JSON, duplicate keys, unknown event and
item types, broken lifecycle ordering, and invalid usage fields. Separate
capture code redacts known credential values, while the batch runner assembles
token, execution, changed-path, and duration evidence.

Sources:

- [`JSONL and usage validation`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/src/mdseval/capture.py#L486-L657)
- [`credential redaction`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/src/mdseval/capture.py#L21-L123)
- [`attempt evidence assembly`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/scripts/run_batch.py#L503-L623)

The redactor replaces exact known secret values and recognized
credential-shaped assignments. It cannot guarantee removal of encoded,
fragmented, hashed, or otherwise transformed secrets. Raw stdout also exists
briefly in a trusted-host temporary file before redaction. Those files require
restrictive permissions, deterministic deletion, and a documented residual
risk.

These conventions should become the evidence layer for all frontier, Planner,
and Follower calls.

## What the historical cheating was

The committed history reports two distinct contamination classes.

### Host implementation discovery

The original workspace sandbox restricted writes and shell networking but did
not seal reads of the host environment. Models found installed fixed
implementations through source inspection and filesystem search.

Source:
[`host-read failure history`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/archive/governance-pack-2026-08-26/TASK_TOOLING_V2_PLAN.md#L1040-L1217)

### Provider-side search and MCP

Later attempts used provider-side web search and GitHub MCP even though the
subject shell could not reach the network. Those tools operate outside the
shell boundary and therefore bypassed a shell-only network policy.

Sources:

- [`provider-search findings`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/handoffs/PROCESS_FINDINGS_2026-08-19.md#L423-L494)
- [`GitHub MCP findings`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/handoffs/TIME_TOKEN_SIGNIFICANCE_AUDIT_2026-08-29.md#L485-L510)

These are repository-recorded findings, not independently reproduced kernel or
Docker escapes. Their lesson is still directly applicable: the experiment
must seal host reads and disable every provider-side retrieval surface.

## Foundation adoption matrix

| Upstream component | Role in the foundation | Required evolution |
|---|---|---|
| `src/mdseval/processutils.py` | Preserve almost unchanged | Add run-scoped orphan cleanup around it |
| `src/mdseval/capture.py` | Preserve strict event parsing and redaction | Add role, particle, semantic-step, ancestry, pricing, and complete token persistence |
| `src/mdseval/runner/codex_cli.py` | Preserve the explicit capability and permission policy | Parameterize exact role, model, effort, prompt, timeout, and output paths |
| `scripts/contain/runtime.py` | Core containment foundation | Fix OAuth lifecycle, portability, resource controls, checker boundary, and generic task sealing |
| containment preflight and seals | Preserve as mandatory gates | Add new TLA+/oracle canaries and fail closed on unknown Codex capabilities/events |
| `src/mdseval/fixtures.py` | Preserve fresh-copy and symlink protections | Generalize from the original task fixtures to public TLA+ inputs |
| `scripts/run_batch.py` | Source of evidence-writing conventions only | Replace its serial domain loop with a role-aware SMC coordinator |
| existing checker | Historical reference only | Replace with an isolated trusted verifier protocol |
| Dockerfile | Starting image design | Supply a reproducible build-context assembler, lock dependencies, and remove machine-specific assumptions |
| negative tests | Preserve and extend | Add OAuth refresh, concurrency, hidden-oracle, nested-Codex, Docker-socket, inherited-FD, and host-path probes |

## Critical issue 1: OAuth refresh ownership

### Verified current behavior

The host validates a dedicated Codex home, extracts secrets for redaction, and
copies only `auth.json` into a new temporary home with restrictive permissions.
The subject command sandbox is denied access to the copied credential.

Sources:

- [`host validation`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/scripts/run_batch.py#L386-L411)
- [`temporary OAuth home`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/scripts/contain/runtime.py#L375-L402)

This is a valuable credential-isolation pattern, but its lifecycle is not safe
for a six-hour, many-turn run:

- The proxy permits `chatgpt.com` and `api.openai.com`, but not
  `auth.openai.com`.
- Each temporary `auth.json` is destroyed after the invocation.
- Any refreshed credential written by Codex is therefore not persisted to the
  durable source.
- Concurrent disposable homes could independently attempt refresh and race.

The repository contains a real `401 token_expired` failure after a denied
request to `https://auth.openai.com/oauth/token`.

Sources:

- [`proxy configuration`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/scripts/contain/Dockerfile#L1-L6)
- [`recorded refresh failure`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/runs/dev-v2/maximum-difficulty-search-disabled-v1/full-starlette-websocket-denial/null/attempt-1/stderr.txt#L1-L14)
- [`maintainer diagnosis`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/handoffs/PROCESS_FINDINGS_2026-08-19.md#L523-L547)

Official Codex documentation states that ChatGPT credentials may be stored in
`auth.json` or the OS keyring. For trusted non-interactive automation, it
documents seeding `auth.json`, allowing in-place refresh, and persisting the
updated file.

Sources:

- [Codex authentication](https://learn.chatgpt.com/docs/auth)
- [Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)

### Required derived design

- Use a dedicated, revocable evaluation OAuth profile.
- Configure file credential storage explicitly.
- Keep durable refresh ownership in a trusted host component.
- Permit the trusted Codex transport, not the subject shell, to reach the
  observed OAuth refresh endpoint.
- Persist credential updates atomically under a lock.
- Do not launch multiple independently writable refresh-token copies until a
  `C=1 -> 2 -> 4` expiry/refresh soak test has passed.
- Redact both original and rotated secrets from all captured evidence.

The audited initial model-turn path is the repository's hardened
`codex exec --json` worker. Its App Server use is primarily for policy
preflight. Moving real model turns to an App Server coordinator would be new,
security-sensitive integration work rather than a property inherited from the
foundation. Official App Server documentation notes shared remote Code Mode
host state across threads and identifies WebSocket/remote-host modes as
experimental, so such a move requires a separate isolation audit.

Source:
[Codex App Server](https://learn.chatgpt.com/docs/app-server)

## Critical issue 2: trusted verifier isolation

The current checker copies `check.py`, private verifier assets, and generated
source into the same writable `/workspace`, then executes the checker against
that source.

Source:
[`current checker layout`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/scripts/contain/runtime.py#L1091-L1114)

Code co-location is verified. The consequence is an inference: candidate code
executed by the checker can attempt to discover or modify hidden evaluation
assets. Making those files read-only would prevent mutation but not discovery.

The derived architecture must instead:

1. Keep TLC, the reference graph, hidden traces, expected answers, and final
   acceptance policy exclusively in a trusted verifier process.
2. Freeze the candidate artifact before hidden evaluation.
3. Run generated Python in a second networkless container containing no hidden
   assets.
4. Exchange narrowly validated JSON inputs and outputs one case at a time.
5. Apply time, memory, output-size, process, and determinism limits.
6. Never feed hidden-test failures back to either experimental arm.

Development-time semantic feedback used by SMC must come from an explicitly
separate public/development oracle and be logged as information available only
to that arm.

## Coordinator and concurrency evolution

The upstream batch runner rejects `max_parallel_runs != 1` and launches
attempts serially.

Sources:

- [`serial invariant`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/scripts/run_batch.py#L73-L91)
- [`serial launch loop`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/scripts/run_batch.py#L748-L793)

Its evidence hash-chain append has no concurrency lock, so changing the flag
would introduce races rather than a valid parallel evaluator.

Source:
[`evidence-chain append`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/tooling/taskcheck.py#L288-L315)

The derived coordinator must:

- support `direct`, `planner`, and `follower` roles explicitly;
- keep particle population `N` distinct from active model-call concurrency
  `C`;
- start with `N=8` and `C=4` as engineering values, not claimed optima;
- assign a unique attempt, workspace, container, temporary home, spool, and
  evidence identity to every model turn;
- own particle state, weights, ESS, resampling, and bounded context centrally;
- let workers write isolated immutable attempt spools;
- use one trusted coordinator to validate and append finalized evidence;
- record queuing, throttling, retries, actual concurrency, and arm makespan;
- keep direct and DisCIPL sessions and outputs separate; and
- randomize or alternate arm order when comparing runs to expose time-of-day,
  allowance, and cache effects.

## Telemetry evolution

The upstream parser already recognizes input, cached-input,
cache-write-input, output, and reasoning-output token fields. The persisted
summary accidentally drops `cache_write_input_tokens`.

Sources:

- [`event and usage audit`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/src/mdseval/capture.py#L486-L657)
- [`lossy token projection`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/scripts/run_batch.py#L542-L550)

The derived evidence schema must preserve raw values and add:

- experiment, arm, role, task, attempt, model, and reasoning effort;
- particle, parent-particle, semantic-step, proposal, and resampling IDs;
- requested and returned model identifiers;
- accepted, rejected, resampled, stopped, timeout, and error reasons;
- queue, container startup, model, capture, verifier, and total elapsed times;
- arm makespan, sum of worker durations, and maximum active concurrency;
- tool trajectory, changed paths, exit status, and sandbox outcome;
- source, prompt, controller, specification, artifact, and verifier hashes;
- exact rate-card snapshot and access timestamp; and
- `api_price_equivalent_usd` calculated without double-counting cached or
  reasoning-token subfields.

OAuth usage is subscription access, not public API per-token billing.
`api_price_equivalent_usd` is therefore a counterfactual normalized estimate,
not actual spend.

## Portability and build gaps

The upstream Python package requires Python 3.10+ and declares no runtime
package dependencies.

Source:
[`pyproject.toml`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/pyproject.toml#L5-L10)

The surrounding runtime is not self-reconstructing:

- Docker Desktop paths, socket locations, and `/private/tmp` paths are
  machine-specific.
- The Docker build expects preassembled `codex-package` and `sealed-deps`
  contexts that are not produced by a committed generic build script.
- The image base is digest-pinned, but apt packages are not version-pinned.
- The root filesystem remains writable.
- `seccomp` is disabled.
- CPU, memory, disk, file-size, and descriptor limits are absent.
- There is no startup scavenger for resources left by host crash or SIGKILL.

The derived foundation needs a reproducible context assembler and lock
manifest, configurable platform discovery, tighter resources, a read-only root
where practical, a deliberate seccomp profile, Docker labels, and orphan
cleanup.

## Threat boundary that remains

The repository itself states that its isolation is practical evaluation
containment, not a security boundary for deliberately hostile prompt
injection.

Source:
[`README threat boundary`](https://github.com/b0ggs/MDs_EVAL/blob/b6db4d3544f0d6fb026c6d9bf68203eae7d5e391/README.md#L240-L259)

The derived project must retain that caveat unless the boundary is separately
security-reviewed. It must also acknowledge that runtime isolation cannot
prevent knowledge memorized in model weights.

Additional probes should test:

- Docker socket and daemon discovery;
- host-path and interpreter/package inventory;
- symlinks and mount-boundary traversal;
- inherited descriptors and environment secrets;
- nested Codex or other model invocation;
- provider-side search, apps, MCP, browser, computer, skills, and subagents;
- hidden-oracle discovery;
- DNS, UDP, proxy bypass, and alternate endpoint access;
- evidence-file mutation and hash-chain races; and
- background processes and crash residue.

## License and provenance

No root `LICENSE`, `COPYING`, or `NOTICE` was found, and `pyproject.toml` does
not declare a license. Public source availability does not itself define
copying or redistribution rights.

Before the derived project vendors code or is distributed publicly, the owner
should add or confirm an explicit license and preserve the upstream repository,
branch, commit SHA, and modification history. If this project and `MDs_EVAL`
have the same owner, this is primarily a provenance and downstream-clarity
task, but it should still be resolved explicitly.

## Recommended foundation sequence

1. Record the pinned upstream branch/SHA and resolve license/provenance.
2. Establish a derived foundation branch or vendored baseline without changing
   the security model during the initial import.
3. Create a reproducible, digest- and dependency-locked build pipeline.
4. Repair OAuth endpoint access, durable rotation, atomic persistence,
   redaction, and concurrent-refresh behavior.
5. Preserve and generalize the Codex deny policy, active preflight, seals,
   process cleanup, evidence parsing, and negative tests.
6. Replace the checker boundary with a trusted verifier plus a separate
   networkless candidate-execution protocol.
7. Replace the serial domain runner with the role-aware SMC coordinator and a
   single evidence writer.
8. Add complete role, particle, token, timing, failure, concurrency, and
   API-price-equivalent telemetry.
9. Run offline tests, Docker containment probes, OAuth expiry/refresh tests,
   and `C=1 -> 2 -> 4` concurrency soak tests.
10. Only then begin recorded Sol-direct versus Sol-Planner/Luna-Follower runs.

## Open architecture decisions

- The durable OAuth owner and safe credential-rotation protocol.
- The public development oracle available during SMC versus the hidden final
  verifier.
- Exact CPU, memory, disk, process, output, and wall-time limits.
- The first concurrency probe and failure/backoff policy.
- Whether the derived project is a branch/fork of `MDs_EVAL` or imports its
  foundation as a versioned component.

The initial model-turn surface is not open: it is the audited hardened
`codex exec --json` worker path. App Server model turns may be reconsidered only
as a separately audited later change.

These decisions should be resolved before implementation changes begin.
