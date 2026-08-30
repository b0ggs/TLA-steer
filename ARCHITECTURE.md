# Architecture

> Status: design for an exploratory implementation. Model aliases, model
> availability, prices, and limits must be captured again when a run starts.

The project's architectural pitch is:

> **A DisCIPL-style, semantic-step sequential Monte Carlo system using hosted
> black-box Followers.**

It uses a capable Planner to generate task-specific inference logic, then uses
that logic to steer a population of partial TLA+-to-Python translations. The
system preserves DisCIPL's Planner/Follower separation, cumulative particle
weights, and intermediate resampling. It does not claim to reproduce the
paper's token-level LLaMPPL inference.

## Fixed design commitments

- The direct frontier arm uses `gpt-5.6-sol` at `xhigh` effort.
- The Planner uses `gpt-5.6-sol` at `xhigh` effort.
- The all-OAuth Followers use `gpt-5.6-luna` at `low` effort.
- Internal Codex subagent spawning is disabled in the frontier, Planner, and
  OAuth Follower turns. The experiment harness owns all parallelism.
- The DisCIPL arm maintains partial programs and resamples between semantic
  translation steps. Ranking completed programs is a different baseline.
- Both arms receive the same source, target contract, and final trusted
  verifier.
- Generated inference code and generated target code receive neither OAuth
  credentials nor unrestricted network access.
- Model fallback and substitution are disabled. A returned model identifier
  that differs from the frozen request makes the run nonconforming.
- Every exposed measurement is retained without declaring a primary or
  secondary metric.
- A recorded comparison freezes all model identifiers, prompts, efforts,
  service routes, particle budgets, concurrency, timeouts, and stopping
  rules.

## Trust boundaries and components

```text
Trusted host process
├── durable Codex OAuth owner
├── hardened codex exec --json worker launcher
├── App Server effective-policy preflight (no model turns)
├── experiment controller and telemetry logger
├── trusted semantic-step scorer and SMC engine
└── independent final TLA+/Python verifier
     │
     ├── direct sandbox
     │   └── gpt-5.6-sol xhigh → one complete Python candidate
     │
     └── DisCIPL sandbox
         ├── gpt-5.6-sol xhigh Planner → restricted inference program
         ├── N gpt-5.6-luna low logical particles
         └── C concurrent hosted Follower requests
```

The trusted host is ordinary deterministic software. It owns authentication,
contained model-worker launches, the particle population, cumulative weights,
resampling, timeouts, and telemetry. The Planner-generated program runs without
network access in a resource-limited sandbox and can invoke only a narrow
inference interface supplied by the host. It cannot call either Codex launch
surface directly.

Candidate Python runs in a second resource-limited sandbox. The final verifier
is neither generated nor modifiable by either model arm.

## Execution flow

Before either arm runs, the controller records the available Codex model
catalog, CLI/App Server version, public OpenAI API rate card, allowance state,
and effective configuration.

### Direct frontier arm

1. Start a fresh contained `codex exec --json` worker with `gpt-5.6-sol`,
   `xhigh`, and internal subagents disabled.
2. Supply the TLA+ module, finite TLC configuration, and Python target
   contract.
3. Allow one direct generation attempt under the frozen tool and timeout
   policy.
4. Preserve the complete output and send it to the final verifier.

Retries, repair turns, or access to verifier feedback would be separately
named direct-arm configurations rather than silently added to this one.

### DisCIPL-style arm

1. The Planner receives the task, the restricted inference-program API, and
   examples. It emits a task-specific controller.
2. The host validates and starts the controller in its sandbox. Runtime errors
   may be returned to the Planner for a fixed number of repair attempts.
3. The controller initializes N logical particles. A particle contains the
   partial Python artifact, completed semantic steps, cumulative log weight,
   ancestry, and any bounded Follower context.
4. At each step, no more than C particles concurrently request a proposal from
   the hosted Follower.
5. A proposal extends one semantic unit, such as an initial-state expression,
   guard, update, frame condition, complete action, or proof obligation.
6. Trusted code parses the proposal, applies hard checks, measures partial
   semantic agreement, and updates the particle's cumulative weight.
7. The engine computes effective sample size and resamples when the generated
   controller's frozen policy requires it.
8. The process stops at a fixed step, call, token, or wall-time budget. Final
   candidates are evaluated by the same independent verifier as the direct
   arm.

Every Follower proposal uses a fresh contained worker. When resampling creates
multiple descendants, the trusted host supplies each child with the bounded
particle state and Follower context defined by the frozen controller. No model
history or filesystem is implicitly shared between workers.

## Model strategy

The all-OAuth MVP models are decided.

| role | current decision | rationale |
|---|---|---|
| direct frontier | `gpt-5.6-sol`, `xhigh` | fixed comparison arm |
| Planner | `gpt-5.6-sol`, `xhigh` | fixed; DisCIPL intentionally uses a capable Planner, and the paper used GPT-4o both as Planner and as a direct baseline |
| all-OAuth Follower | `gpt-5.6-luna`, `low` | fixed; lowest-cost durable OAuth option and an engineering proxy, not a known 1B SLM |

Alternative models and providers are out of scope for this implementation.
Any later use of one is a separately designed and named experiment.

Using Sol for both the direct arm and Planner does not erase the comparison.
The Planner produces an inference program rather than the final translation,
and its cost is recorded separately. This mirrors the paper's use of GPT-4o
as both Planner and direct baseline. The capacity asymmetry that matters most
to the DisCIPL claim is between the capable Planner and the small Follower.

OpenAI describes Luna as roughly corresponding to the nano tier from earlier
GPT-5 families, but publishes no parameter count. Low effort reduces its
reasoning work; it does not turn Luna into a smaller base model or change its
per-token price. A Luna result can support the hosted orchestration claim, but
not a claim that a 1B-class model acquired the capability.

As observed on 2026-08-30, the published standard API rates are $4.00 input,
$0.40 cached input, and $20.00 output per million tokens for Sol, and $0.20,
$0.02, and $1.20 respectively for Luna. The harness uses the rate card current
at run start to calculate API-price-equivalent cost from OAuth token usage. It
does not describe that estimate as actual marginal OAuth spend.

## Selected all-OAuth configuration

### Six-hour all-OAuth MVP

This is the shortest route to a working end-to-end system:

```text
direct    = gpt-5.6-sol, xhigh
Planner   = gpt-5.6-sol, xhigh
Follower  = gpt-5.6-luna, low
N         = 8 logical particles
C         = 4 active Follower turns
```

The audited initial model-turn path is hardened `codex exec --json`, inherited
from the `MDs_EVAL` foundation. App Server is used for the zero-spend
effective-policy preflight, not for experimental model turns. Moving real
turns to App Server would require a separate isolation audit. N=8 and C=4 are
engineering starting points, not claims that they are optimal.

This configuration validates the harness, semantic decomposition, scoring,
resampling, telemetry, sandboxing, and final comparison. Its limitation is
explicit: Luna may be substantially more capable than the paper's 1B
Follower.

## What black-box semantic-step SMC preserves

- A model-generated inference controller.
- A population of partial candidate programs.
- Proposal steps aligned with translation semantics rather than arbitrary
  token counts.
- Hard and soft symbolic scores accumulated over time.
- Effective-sample-size monitoring and intermediate resampling.
- Bounded traceback repair of invalid inference programs.
- Optional counterexample hints, recorded as a project-specific extension.

The selected Codex interfaces do not reproduce arbitrary teacher-forced
continuation scoring, dynamic token masks, masked probability mass, or the
paper's exact proposal/prior importance corrections. The system must therefore
continue to identify itself as a semantic-step DisCIPL approximation.

## Particle and concurrency accounting

N and C are independent:

- N is the population size maintained by the inference algorithm.
- C is the maximum number of Follower requests in flight at once.

The controller queues particles when N exceeds C. Concurrency is a measured
service capability rather than a promised entitlement. Each run records queue
delay, active concurrency, throttles, retry hints, failed requests, and the
requested and returned model identifiers.

The native Codex subagent limit is not used as the algorithm's particle
definition. The external harness controls contained `codex exec --json`
workers and applies one global semaphore across all model calls.

## Telemetry contract

Every model call is tagged with experiment, arm, role, task, attempt, particle,
semantic step, and parent-particle identifiers. Raw records preserve:

- requested and returned model identifiers, effort, route, and service tier;
- input, cached-input, cache-write, output, reasoning-output, and total tokens
  when exposed;
- request, queue, first-token, generation, tool, verifier, and end-to-end wall
  times when observable;
- prompts or prompt hashes, outputs, finish reasons, retries, errors, and
  rerouting;
- particle ancestry, per-step scores, cumulative weights, ESS, resampling
  decisions, and stopping reason;
- Planner program source, runtime tracebacks, and repair attempts;
- final Python artifacts and complete verifier results.

Raw usage remains authoritative. A versioned OpenAI calculator maps those
fields to the public API rate card observed on the run date without
double-counting cached or reasoning tokens. The resulting field is named
`api_price_equivalent_usd`; it is a counterfactual normalization of OAuth token
usage, not an invoice or actual marginal charge.

## Decisions still open

- Freeze semantic step boundaries, score functions, ESS threshold, repair
  count, and stopping budgets.
- Define the OAuth concurrency probe before attempting larger particle
  populations.

## Current source links

- OpenAI Codex App Server:
  https://learn.chatgpt.com/docs/app-server
- OpenAI Codex non-interactive mode:
  https://learn.chatgpt.com/docs/non-interactive-mode
- OpenAI Codex models:
  https://learn.chatgpt.com/docs/models
- OpenAI GPT-5.6 Luna:
  https://developers.openai.com/api/docs/models/gpt-5.6-luna
- OpenAI API pricing:
  https://developers.openai.com/api/docs/pricing
- Pinned MDs_EVAL foundation audit:
  MDSEVAL_FOUNDATION_AUDIT.md
