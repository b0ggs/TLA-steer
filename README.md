# TLA+ -> Python: an exploratory, verifier-checked comparison

> Status: experiment design. The generation harness and evaluator have not yet
> been implemented.

The project's pitch is a **DisCIPL-style, semantic-step sequential Monte Carlo
system using hosted black-box Followers**.

This project compares two ways of translating a finite TLA+ model into an
executable Python transition model:

1. `gpt-5.6-sol` at `xhigh` effort working directly in a sandboxed Codex
   environment, with internal subagents disabled.
2. A DisCIPL-style system in a separate sandbox, where a `gpt-5.6-sol`
   `xhigh` Planner writes an inference program and an inference engine runs it
   over many `gpt-5.6-luna` `low` Follower instances. All model calls use Codex
   OAuth, and internal subagents are disabled.

Both arms receive the same TLA+ source, target contract, and final correctness
check. The experiment records everything the environments expose: token use,
OpenAI API-price-equivalent cost, wall time, calls, retries, verifier activity,
failures, intermediate errors, and final correctness.

This is deliberately exploratory. There is no primary or secondary metric, no
claim of statistical significance, and no assumption that either arm will win.
The interesting result is the complete comparison, including how each system
fails when it does not produce correct Python.

## Question

Can a Planner-generated inference program enable a population of hosted
Follower instances to produce a verifier-approved Python translation of a TLA+
model, and how does that process compare with asking a frontier model to
produce the same artifact directly?

"Translation" has a deliberately narrow meaning in the first version of this
project. The input is a TLA+ module plus one finite TLC configuration. The
output is a pure Python representation of that configuration's initial state
and labeled next-state relation. Passing the verifier establishes bounded
transition-system equivalence for that instance. It is not a proof about all
constant values, all TLA+ modules, or a deployed concurrent implementation.

## What this borrows from DisCIPL

The method comes from Grand, Tenenbaum, Mansinghka, Lew, and Andreas,
*Self-Steering Language Models* (COLM 2025). DisCIPL separates two roles:

- A capable **Planner** reads the task and writes a task-specific inference
  program in LLaMPPL/Python.
- An inference engine uses a population of cheaper **Follower instances** to
  extend and score candidate outputs under that program.

Under sequential Monte Carlo (SMC), the candidates are particles containing
partial generations. The inference engine repeatedly advances them, updates
their cumulative weights, and resamples when appropriate so that more work is
allocated to promising partial outputs. The paper also evaluates importance
sampling (IS), which generates complete weighted samples without intermediate
resampling, and rejection sampling (RS), which checks only completed outputs.

For this project, useful generation steps are semantic units such as a guard,
an update expression, a frame condition, or a complete action function. The
particles should contain partial Python programs, not merely independent
completed functions that are ranked after the fact. Generating `K` completed
candidates and keeping the best would be verifier-guided best-of-`K`, not SMC
or importance sampling.

The paper used GPT-4o as the Planner and primarily Llama-3.2-1B as the
Follower. It evaluated constrained text generation, not TLA+ translation. Its
results motivate this experiment but do not predict its outcome. On COLLIE
sentence tasks, for example, weighted Pass@1 was 0.76 for SMC, 0.84 for IS,
and 0.20 for RS. SMC's advantage over IS was better coherency rather than
higher Pass@1. Python translation has no identical coherency objective, so the
value of SMC is something to observe rather than assume.

The paper's cost result also needs a narrow reading. Its generated inference
programs used 40.1% fewer tokens and were 80.2% cheaper to generate than o1's
reasoning traces under prices dated 2025-05-31. That 80.2% applies only to the
program/reasoning component. The reported end-to-end totals were $4.26 for
DisCIPL and $4.75 for o1 per 100 COLLIE sentence tasks, about a 10% difference.

## Architecture

The trusted Python harness owns authentication, model calls, particle
state, cumulative weights, effective-sample-size calculations, resampling,
telemetry, and the final verifier. The direct sandbox contains one Sol worker.
The DisCIPL sandbox contains a Planner-generated restricted inference program
and a queue of logical Follower particles.

```text
trusted host
├── durable Codex OAuth owner
├── hardened codex exec --json worker launcher
├── App Server policy preflight (no model turns)
├── semantic-step scorer and SMC engine
├── telemetry
└── independent final verifier
     ├── direct sandbox: gpt-5.6-sol xhigh → complete Python
     └── DisCIPL sandbox: gpt-5.6-sol xhigh Planner → inference program
                              ↓
                 N gpt-5.6-luna low particles / C active calls
```

Generated inference code receives only a narrow proposal/scoring interface. It
never receives OAuth credentials, unrestricted network access, or authority to
modify the final verifier. Generated Python runs in a separate resource-limited
sandbox.

At each SMC step, a Follower extends one semantic unit such as an initial-state
expression, guard, update, frame condition, complete action, or proof
obligation. Trusted code parses and scores the extension, updates its
cumulative weight, calculates effective sample size, and resamples according
to the frozen controller policy. The complete design is documented in
[ARCHITECTURE.md](ARCHITECTURE.md).

## Model strategy

The model configuration for the all-OAuth MVP is fixed:

| role | current decision |
|---|---|
| direct frontier | `gpt-5.6-sol`, `xhigh`, internal subagents disabled |
| Planner | `gpt-5.6-sol`, `xhigh`, internal subagents disabled |
| all-OAuth Follower | `gpt-5.6-luna`, `low`, internal subagents disabled |

Alternative models and providers are out of scope for this implementation.
Any later use of one is a separately designed and named experiment, not a
substitution within these arms.

A capable Planner is faithful to the paper. It used GPT-4o as Planner and also
included GPT-4o direct and chain-of-thought baselines. Using the same capable
model for the direct arm and Planner therefore does not remove the
architectural comparison. The more important paper-like asymmetry is between
that Planner and a deliberately weak Follower.

OpenAI positions Luna as roughly corresponding to the nano tier from earlier
GPT-5 families, but publishes no parameter count. Low effort reduces reasoning
work; it does not make the underlying model smaller. A Luna result can validate
the hosted orchestration and instrumentation, but it cannot establish that a
known 1B-class model acquired compiler-like ability.

As observed on 2026-08-30, the published standard API rates are $4.00 input,
$0.40 cached input, and $20.00 output per million tokens for Sol, and $0.20,
$0.02, and $1.20 respectively for Luna. These rates normalize the OAuth token
counts into API-price-equivalent estimates; they are not the experiment's
actual marginal OAuth charges. The calculator will capture and use the current
rate card again when each recorded run begins.

### Selected all-OAuth configuration

The shortest implementation path is:

```text
direct    = gpt-5.6-sol, xhigh
Planner   = gpt-5.6-sol, xhigh
Follower  = gpt-5.6-luna, low
N         = 8 logical particles
C         = 4 active Follower turns
```

This is an architecture and instrumentation pilot. N=8 and C=4 are engineering
starting values, not benchmark commitments. If it is stable, N can increase to
16 while C remains independently bounded. A Luna-direct control and a
Luna-best-of-N control are needed to determine whether SMC adds anything over
repeated calls to the same already-capable model.

The audited initial model-turn surface is the hardened `codex exec --json`
worker path from the `MDs_EVAL` foundation. App Server remains useful for the
zero-spend effective-policy preflight, but moving real turns to shared App
Server threads would be a new integration requiring a separate isolation
audit. Internal Codex subagent spawning remains disabled so that the external
harness owns and measures all parallelism.

### Hosted black-box fidelity

No local language models will be installed. Every run records the requested
and returned Codex model identifiers, reasoning effort, service tier, tool and
client versions, supported parameters, and the dates on which the catalog and
OpenAI rate card were observed. A requested/returned model mismatch is logged
and handled by the frozen run policy rather than silently accepted.

The hosted system preserves:

- a Planner-generated inference program;
- partial candidates and cumulative weights at multiple semantic steps;
- intermediate resampling rather than final-only ranking;
- bounded traceback repair of inference-program failures; and
- concurrent Followers subject to a separately measured concurrency limit.

Semantic counterexamples from the TLA+ verifier are a project-specific source
of stepwise weights or Follower hints, not part of the paper's traceback-only
Planner repair loop. They are logged separately.

Full paper-style proposal/prior scoring and constrained-proposal correction
require arbitrary continuation probabilities, dynamic token masks, and masked
probability-mass corrections. The selected Codex interfaces do not document
those controls. This project therefore remains a **hosted semantic-step
DisCIPL approximation**.

## Experimental arms

| arm | isolated environment | process |
|---|---|---|
| `frontier` | Codex OAuth, `gpt-5.6-sol` xhigh | produces one complete Python translation directly |
| `discipl_oauth` | Codex OAuth, `gpt-5.6-sol` xhigh Planner and `gpt-5.6-luna` low Followers | Planner writes an inference program; semantic-step SMC steers a population of partial translations |

Exposed model identifiers, prompts, parameters, budgets, concurrency, and
stopping rules are frozen before each comparison. Model fallback is disabled;
a mismatched returned model makes the run nonconforming. The two arms do not
see each other's outputs and both are graded by the same final checker.

Verifier feedback used internally by the DisCIPL arm is part of that method,
not hidden evaluation data. Every such call is reported so that the additional
information and work remain visible.

## The TLA+ instance

`TwoLights.tla` describes two traffic lights, A and B, on the same road. The
finite configuration in `TwoLights.cfg` fixes six constants. The model has five
variables and seven named actions.

Three features make it useful as a small translation exercise.

**The clock is shared.** `Tick` is the only action that changes it. Each of the
six light actions must preserve it, creating six opportunities to omit or
mis-copy a frame condition.

**A and B have matching action shapes.** Their actions differ in which
variables they read, write, and preserve. This creates useful copy/paste
failures. Equal A/B transition counts are only a smoke test, however; a swap
can preserve the counts, so correctness depends on labeled-edge comparison.

**The next-state relation is nondeterministic.** Several named actions can be
enabled in the same state, although each individual action in this particular
model has at most one successor for a given state. A phase may change after its
minimum duration. At `MaxPhase`, `Tick` is disabled until a required phase
change occurs; the clock cannot advance again until every light at
`MaxPhase` changes phase. This is not an unconditional temporal guarantee that
the light eventually changes: `Spec` permits stuttering and contains no
fairness condition. `Offset` establishes B's initial timer offset; it does not
preserve a fixed phase difference forever.

Independent enumeration of the configured `Init`/`Next` relation gives 3,528
reachable states and 6,960 labeled transitions:

```text
Tick             2592      AGreenToYellow    672      ARedToGreen      504
AYellowToRed     1008      BGreenToYellow    672      BRedToGreen      504
BYellowToRed     1008
```

All 3,528 type-correct states are reachable, and the graph is strongly
connected. That makes an explicit initial-state check essential: starting from
many incorrect but type-correct initial states can still produce the same
unrooted state and edge sets.

## Python target

For `TwoLights`, the target is one module with the configured constants, an
explicit initial state, and one pure function per named disjunct of `Next`.

```python
CYCLE_LENGTH, MIN_GREEN, MIN_YELLOW, MIN_RED, MAX_PHASE, OFFSET = 8, 3, 1, 4, 6, 2

INITIAL = {
    "clock": 0,
    "lightA": "green",
    "timerA": 0,
    "lightB": "red",
    "timerB": 2,
}

def a_green_to_yellow(state: dict) -> dict | None:
    """Return the unique successor, or None when the action is disabled.

    Do not mutate ``state``.
    """
```

This single-successor interface is specific to the current example. General
TLA+ actions are relations and may yield zero, one, or many successors; `Init`
may also describe multiple states. A broader translator would need interfaces
such as `initial_states()` and `successors(state)` that return sets or iterables.

The generated module is an executable transition model, not production traffic
light software. TLA+ and TLC can already execute, simulate, and explore the
specification. Python is useful here as the common target artifact for the
translation experiment and for later integration with ordinary tooling.
Neither representation supplies probabilities, timing, or throughput by
itself; those require an explicit scheduler and quantitative model.

## How correctness is decided

TLC supplies the reference states and labeled `Next` transitions for the fixed
configuration. A separate harness loads the generated Python inside a
resource-limited sandbox, checks its interface and behavior, and constructs its
transition system. Planner-generated `check()` code is never trusted as the
final oracle.

A translation is accepted only when:

1. The module parses, imports under the allowlist, and terminates within its
   limits. Repeated calls to each named action on the same state produce the
   same result and do not mutate their input; nondeterminism remains in the
   choice among enabled named actions.
2. Its initial state exactly matches the reference initial state.
3. Its reachable states and labeled action transitions exactly match the TLC
   reference for this configuration.

The comparison records several views of correctness because a single Boolean
can hide useful failures:

| metric | meaning |
|---|---|
| `initial_exact` | generated and reference initial states are identical |
| `transition_sound` | every generated labeled transition is allowed by the reference |
| `transition_complete` | every reference labeled transition is generated |
| `state_exact` | the rooted reachable-state sets match |
| `exact` | all acceptance conditions hold |
| `frame_violations` | an action changes a variable that its TLA+ relation preserves |
| `runtime_failure` | import, exception, timeout, mutation, nondeterminism, or sandbox failure |

`transition_complete` is one-step relation completeness, not temporal
liveness. Exactness here is a decision about the terminating generated module
and this finite TLC instance. It should not be described as unrestricted TLA+
refinement or as correctness of the original specification.

The checker compares the explicit `Init` predicate and decomposed `Next`
relation. The implicit stuttering allowed by `[Next]_vars` is not emitted as a
named Python action, and this experiment does not check fairness or liveness.
Matching action labels is an intentional extra translation-contract check
beyond equality of the union of all `Next` transitions.

For intermediate steering, raw accuracy over all states is not sufficient.
Most actions are disabled in most states, so a function that always returns
`None` can receive a deceptively high score. Stepwise weights should separate
enabledness precision and recall from successor agreement on enabled states.

## What is recorded

There is no hierarchy among these measurements. The experiment captures every
useful quantity the environments expose, including:

- Planner, Follower, and frontier-model usage fields, including input,
  cached-input, cache-write, output, reasoning-output, and total tokens when
  the service reports them. The raw fields and applicable OpenAI documentation
  will be retained.
  Cached or reasoning subcounts will not be counted twice.
- The exact published OpenAI API rate card and access date used to calculate
  `api_price_equivalent_usd`.
- Total and per-call wall time, concurrency, and latency.
- Model calls, particle counts, inference steps, resampling events, retries,
  timeouts, and stopping reason.
- Verifier calls and verifier wall time.
- Final correctness metrics and the complete final Python artifact.
- Intermediate candidates when practical, plus syntax errors, runtime errors,
  tracebacks, counterexamples, graph differences, and other interesting
  failures encountered during generation.
- Model identifiers, versions, prompts, inference programs, parameters,
  budgets, seeds when supported, and sandbox/tool versions needed to interpret
  a run.

Codex JSONL-reported token counts are preferred. Any locally counted or
estimated tokens will be marked as estimates. The selected calls use Codex
OAuth and are not billed at public API per-token rates. The field
`api_price_equivalent_usd` is therefore a counterfactual normalization using
the dated public OpenAI API rate card, not an actual bill or marginal charge.
A versioned OpenAI calculator maps raw usage into the published input,
cached-input, cache-write, and output categories. It charges output once;
reasoning-output subcounts are not added again unless the rate card explicitly
bills them as a separate category.

Runs may be repeated to expose variability and interesting failure modes, but
the output will be descriptive: raw runs, ranges, and examples rather than a
significance claim.

## Errors are experiment artifacts

Intermediate outputs will be retained when practical so the comparison can
show more than a final pass or fail. Interesting categories include incorrect
initial states, loose or tight guards, missing or extra successors, wrong
updates, dropped frame conditions, A/B copy mistakes, accidental
determinization, invalid Python, target-contract violations, Planner inference
program failures, particle collapse, ineffective resampling, timeouts, and
sandbox or service errors.

These categories are descriptive. Prompts, scores, and acceptance rules will
not be changed retroactively within a reported comparison to hide a newly
observed failure.

## Current repository state

The repository currently contains the experiment description and source
materials, not a completed harness:

```text
README.md                          experiment design
ARCHITECTURE.md                    system, model, and OAuth design
MDSEVAL_FOUNDATION_AUDIT.md        pinned foundation and containment audit
TwoLights.tla                      TLA+ module
TwoLights.cfg                      finite TLC configuration
943_Self_Steering_Language_Mod.pdf DisCIPL paper
```

See [MDs_EVAL foundation audit](MDSEVAL_FOUNDATION_AUDIT.md) for the pinned
upstream commit, verified containment mechanisms, known defects, and required
evolution into this experiment's coordinator and verifier.

The compiler/controller, TLC extractor, Python sandbox, verifier, model
adapters, metrics logger, and result artifacts still need to be implemented.
`tla2tools.jar` is not currently included.

With a TLA+ tools JAR available, the reference model can be checked and dumped
with commands of this form:

```bash
java -cp tla2tools.jar tlc2.TLC -nowarning -config TwoLights.cfg TwoLights.tla
java -cp tla2tools.jar tlc2.TLC -nowarning -config TwoLights.cfg \
  -dump dot,actionlabels g.dot TwoLights.tla
```

The DOT dump is a TLC visualization format, so the implementation must pin the
TLC version and parse it carefully or use a small TLC/Java adapter to serialize
canonical states and transitions.

`GreenWave` at the bottom of the specification is a state predicate, not an
invariant. It holds in 392 of the 3,528 reachable states, or 1/9 under uniform
state counting. That fraction is not the probability of observing two green
lights in an execution unless a scheduler and probability distribution are
defined separately.

## Limits

- `TwoLights` is a demonstration instance, not evidence of a general compiler.
- Exhaustive comparison applies only to the finite constants in
  `TwoLights.cfg`.
- The planned `discipl_oauth` arm is a semantic-step approximation because the
  selected Codex interfaces do not expose the full token-level probability and
  masking controls used by the paper's LLaMPPL implementation.
- Generated Python must be treated as untrusted and run with strict filesystem,
  network, process, time, and memory limits.
- The DisCIPL arm receives verifier feedback during search while the final
  frontier artifact is only graded afterward. That asymmetry is part of the
  method and will be made visible through the recorded calls and traces.
- API prices and model availability change. Every comparison must record the
  exposed model identifier and rate-card date used for
  `api_price_equivalent_usd`, pinning a snapshot only when one is available.
- Matching the specification does not establish that the specification itself
  is correct.

## Related work

FormaLLM (Bisharat et al., arXiv:2606.05792) evaluates the opposite direction:
natural language to TLA+. Across 30 models, it reports up to 26.6% syntactic
correctness and 8.6% semantic correctness. Its results reinforce the value of
parser and model-checker feedback, but its task is not this project's
TLA+-to-Python translation.

Specula (Cheng et al., arXiv:2607.25333) uses coding agents to derive TLA+
models and invariants from system code and then model-check those systems. It
is relevant as an agentic formal-methods system, but it also operates in a
different direction from this experiment.

## References

- Grand, Tenenbaum, Mansinghka, Lew, Andreas. *Self-Steering Language Models.*
  COLM 2025. https://openreview.net/forum?id=XvCBtm5PgF
- Official DisCIPL implementation:
  https://github.com/gabegrand/self-steering
- MIT News / CSAIL. *Enabling small language models to solve complex reasoning
  tasks.* 12 December 2025.
  https://news.mit.edu/2025/enabling-small-language-models-solve-complex-reasoning-tasks-1212
- Lew, Zhi-Xuan, Grand, Mansinghka. *Sequential Monte Carlo Steering of Large
  Language Models using Probabilistic Programs.* arXiv:2306.03081.
- LLaMPPL: https://github.com/genlm/llamppl
- Loula et al. *Syntactic and Semantic Control of Large Language Models via
  Sequential Monte Carlo.* ICLR 2025.
- Lamport. *Specifying Systems.*
  https://lamport.azurewebsites.net/tla/tla.html
- TLA+ tools: https://github.com/tlaplus/tlaplus
- OpenAI Codex non-interactive mode:
  https://learn.chatgpt.com/docs/non-interactive-mode
- OpenAI Codex App Server:
  https://learn.chatgpt.com/docs/app-server
- OpenAI Codex models:
  https://learn.chatgpt.com/docs/models
- OpenAI authentication for Codex:
  https://learn.chatgpt.com/docs/auth
- OpenAI GPT-5.6 Luna:
  https://developers.openai.com/api/docs/models/gpt-5.6-luna
- OpenAI API pricing:
  https://developers.openai.com/api/docs/pricing
- Bisharat et al. *Can LLMs Write Correct TLA+ Specifications?*
  arXiv:2606.05792.
- Cheng et al. *Specula: Scaling formal specifications for autonomous model
  checking of system code.* arXiv:2607.25333.
