# Time/token significance audit — external review packet

- Date: 2026-08-29
- Branch: `time-token-challenge`
- Status: **AUDIT AND RECOMMENDATION ONLY**

This document is a self-contained packet for independent statistical review. It
is not an approved roadmap, does not authorize task development or live calls,
and does not modify the candidate MD, runner, tasks, or evidence. In particular,
it does not adopt `TIME_TOKEN_CHALLENGE_ROADMAP_2026-08-28.md`, which Wade
explicitly rejected as an unapproved roadmap.

No benchmark or subject-model call was made for this audit. All calculations
below are offline calculations from preserved repository evidence.

## Project context for a cold-start reviewer

This section is intentionally redundant with repository documentation so that
someone receiving **only this Markdown file** can understand the project and
the statistical question.

### What MD Eval is

MD Eval is a controlled benchmark for repository instruction files. An “MD” in
this project is a Markdown file such as `CODER.md` that a coding agent reads in
addition to its ordinary platform, harness, task, tool, and permission
instructions. The benchmark asks whether changing only that repository
instruction file changes objective coding outcomes.

For every comparison, MD Eval holds the following fixed:

- coding task and repository snapshot;
- model and reasoning effort;
- system/harness instructions and task prompt;
- available tools, sandbox, network policy, and time limit;
- mechanical checker and scoring; and
- evidence-capture pipeline.

Only the bytes injected as `CODER.md` change between arms. “No MD” therefore
means a zero-byte `CODER.md`, not a model with literally no instructions.

The repository currently **evaluates manually supplied instruction files**. It
is not yet an automated instruction optimizer.

Key terms used throughout this packet:

| Term | Meaning in MD Eval |
|---|---|
| Subject | The coding agent/model being measured |
| Arm | One instruction condition, here zero-byte `CODER.md` or the candidate `CODER.md` |
| Task | One frozen repository snapshot, public issue contract, and private objective checker |
| Attempt | One fresh stochastic subject run on one task under one arm |
| Valid | The attempt's runtime and evidence are mechanically usable; it may still be an incorrect solution |
| Resolved | Every required behavior and regression check passed mechanically |
| Live call | A paid subject-model execution; offline checking, analysis, and preflight are not live calls |

### Long-term product goals and current branch

The project has three intended uses:

1. open-source software that lets anyone build validated coding tasks and test
   their own instruction file;
2. a competition in which people submit instruction files against a curated
   challenge; and
3. a personal-repository mode in which tasks are derived from a user's own code
   and pull requests to identify the best instruction file for that repository.

Those products can use different task distributions. The reusable machinery—
task packaging, runner, checkers, evidence, and statistics—must remain rigorous
and treatment-neutral.

This branch, `time-token-challenge`, has a much narrower purpose: determine
whether a short instruction file can reduce coding-agent wall time and token
use without unacceptable correctness loss, then design a statistically valid
confirmation. Governance/drift tasks and competition-site implementation are
separate future work. Wade's current ordering is to settle the significance
design before building the competition experience.

### The exact treatment and control

The control is a zero-byte file:

`controls/coder/null-m2.md`

SHA-256:

`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

The current candidate is a 949-byte, trace-derived efficiency policy:

`controls/coder/evidence-bounded-v1.md`

SHA-256:

`c0d56e29ade34c24278b976e84b29e47324c11a23399ca882239daffc9762c74`

Its complete contents are:

```markdown
# Fast correct completion

1. Privately map requirements to owner/path and direct proof.
2. Start with one batched search; follow concrete control/ownership edges and adjacent tests. Broaden only for unowned requirements; skip history/broad scans.
3. Bound runtime/output: native quiet, first-failure, short-traceback options; maximum 200 requested lines. Never print generated/binary data or pipe-truncate live processes. Report decisions/blockers only.
4. Make the minimal patch. Use one focused test/reproducer whose exit status covers all requirements; changed tests pass.
5. Missing/hanging tooling: check runner config/executable once, then one timed corrected retry—no equivalents or process hunts.
6. After narrower proof, run one non-overlapping adjacent regression, never an equivalent test. Review scope; stop. Full suite only if the task explicitly requires it, public signature/schema changed, or results show spillover. Report gaps.
```

This candidate was manually distilled from prior run traces. It tries to reduce
broad searches, repeated equivalent tests, environment/process hunts, and large
tool output while still requiring direct proof of every requested behavior. It
is an experimental treatment, not a confirmed champion or approved replacement.
An older generic `coder.md` was judged unsuitable for this efficiency question
and is not an arm in the current comparison.

### How a task and scored attempt work

Each task package contains:

- a public repository snapshot and public issue contract seen by the subject;
- a private mechanical checker and requirement-level outcomes;
- a known-correct reference solution;
- an independently produced blind solution; and
- manifests and ledgers binding the admitted bytes.

`tooling/taskcheck.py` is the sole task-admission mechanism. It mechanically
checks, among other things, that pristine code fails the new requirements,
known-correct solutions pass, existing behavior remains intact, and scoring is
deterministic. Manual judgment cannot override a mechanical failure.

For a scored attempt, the runner:

1. creates a fresh ephemeral workspace from the public task;
2. injects either the zero-byte control or candidate as `CODER.md`;
3. runs the same coding model under the frozen runtime;
4. captures the event stream, commands, edits, final patch, duration, and token
   telemetry;
5. runs the private checker twice after the subject finishes; and
6. writes hashes, checker results, and raw evidence to disk.

Raw evidence is preserved. Tasks, targets, checkers, and MD bytes cannot change
during captured attempts. Only predeclared infrastructure failures may be
replaced; scientific failures are not selectively retried.

The latest hardened comparison used:

- `gpt-5.6-sol`, high reasoning;
- isolated Docker containers pinned to content-addressed images;
- Python 3.11.5;
- workspace-write sandbox;
- web search disabled;
- agent-command network disabled;
- subagents disabled;
- serial execution; and
- a 900-second limit for each subject attempt.

The repository also requires a deterministic launch preflight for the complete
four-task cohort to finish within 60 seconds. That setup/preflight limit is
separate from model execution time and is not a claim that scored coding runs
finish within one minute.

Live subject spend is bound to an exact `REQUEST.json` hash and cannot start
without Wade's matching `APPROVED.json`. This audit grants no such approval.

### The four current development tasks

The present pilot contains four real-repository issue-resolution tasks:

| Task | Public coding problem | What makes the work nontrivial |
|---|---|---|
| Boltons wraps forwarding | Correct generated wrapper calls so keyword-supplied values remain keyword arguments while preserving positional-only, keyword-only, `*args`, and `**kwargs` behavior | Requires tracing generated invocation/signature rules and proving several signature shapes |
| Flask automatic options | Make an explicit `provide_automatic_options=True` override a globally disabled default for function and class views without breaking explicit false or custom `OPTIONS` handling | Requires finding route-registration precedence and covering interacting defaults |
| Starlette websocket denial | Make streaming and file responses emit valid WebSocket-denial events while preserving HTTP behavior and background-task semantics | Requires following specialized response call paths and dealing with difficult/hanging test behavior |
| Click stream lifecycle | Ensure closing/finalizing named text wrappers does not close shared buffers and repeated `CliRunner` invocations restore streams safely | Requires distinguishing explicit `close()` behavior from garbage-collection/finalizer behavior |

These are **task identities**, not necessarily the four categories intended for
the eventual expanded significance cohort. The archived correctness design used
four broader strata: bug repair, feature addition, integration/executable
behavior, and behavior-preserving refactoring/data handling. The external
review must determine whether those are also the intended time/token categories.

Every current task is already exposed development material. The candidate was
informed by traces from this cohort, especially repeated broad search/test
patterns and failure modes. That history matters when choosing between an
out-of-sample claim and a deliberately fixed-known-task claim.

### How the project reached the present question

| Stage | What happened | What it established |
|---|---|---|
| Correctness-oriented benchmark work | The bare model repeatedly reached or approached the correctness ceiling on the available clean tasks | There was little correctness headroom for a helpful MD; efficiency became the promising outcome |
| Initial generic and short-MD probes | Small paired runs examined correctness, tokens, wall time, and trajectories | Descriptive differences existed, but three attempts per arm and runtime contamination prevented a significance claim |
| Trace-derived candidate | Prior traces were reviewed to identify avoidable broad search, repeated verification, output, and process-hunting behavior | Produced the exact six-rule `evidence-bounded-v1.md` treatment above |
| Cheating/containment audit | Historical traces revealed web/MCP answer retrieval in some old attempts and one current blocked lookup attempt | Older cohorts cannot be pooled; the runtime was hardened against those capabilities |
| Hardened candidate-versus-null v2 | 24 fresh calls: four tasks × three attempts × two arms | First trustworthy paired pilot under current containment; raw time/tokens fell about 35%, but MD correctness was 10/12 versus no-MD 12/12 |
| Current significance audit | One read-only sub-agent and the primary session examined plans, traces, metrics, power, and failure handling | The old 16-task correctness power calculation cannot automatically justify time/token significance |

The two candidate failures in the hardened run occurred on Click. Both solutions
protected finalization but missed the explicit requirement that calling
`close()` itself leave the shared binary buffer open. The successful candidate
attempt implemented `close()` and took about the same time as the no-MD median.
This is why the raw efficiency totals cannot be treated as a win and why failure
handling is central to the new design.

### The decision this packet is asking the reviewer to make

The project is **not** currently asking whether the 24-call pilot is
statistically significant; it cannot be. It is asking how to construct one
future, frozen experiment that can terminate honestly with either a positive or
negative/inconclusive result.

The main candidate design inherited from earlier planning is:

- four task categories;
- four independent tasks per category, initially 16 total;
- four fresh attempts under no MD and four under the candidate for each task;
- 128 scored calls; and
- objective correctness, wall-time, and token evidence.

The audit must determine whether that is actually powered for the time/token
claim or whether more independent tasks are required. It must also solve the
fact that cheap incorrect attempts can look faster and cheaper. No task factory,
new task, runner change, MD revision, competition feature, or live run is
authorized by this packet.

## Requested external-review verdict

Please review the facts, calculations, and provisional choices below and return
a corrected, minimal preregistration for a time/token confirmation. In
particular, answer:

1. What exact claim and task population should the experiment support?
2. Should wall time, the registered token proxy, or both be confirmatory?
3. What is the correct task-level estimand and hypothesis test?
4. Should the test be one-sided or two-sided, and how should multiplicity be
   handled?
5. What correctness guardrail or non-inferiority margin is defensible?
6. How should failed attempts, timeouts, and missing token telemetry enter each
   endpoint?
7. Given those choices, how many independent tasks and how many repeats per arm
   are required for at least 80% joint power?
8. Are 16 tasks × 4 repeats × 2 arms defensible, or is a larger task cohort
   required?
9. Does the proposed task sourcing and freezing boundary prevent adaptive
   selection bias?
10. What is the smallest implementation change required before the frozen
    experiment can run?

Please distinguish a fixed curated-task-set claim from a population claim, and
do not propose a competition site, task factory, optimizer, governance layer,
or other product work. Those are outside this review.

## Executive conclusion

The repository does contain a **16-task, four-runs-per-arm** design, but its
power work concerned a large **binary correctness** improvement. It did not
power a time endpoint, a token endpoint, their joint success, or correctness
non-inferiority. Its power does not transfer automatically.

A defensible time/token campaign can retain four task categories and four
repeats per arm. The number of tasks still depends on choices that have not
been frozen:

- the claim and target task population;
- the primary endpoint and estimator;
- the smallest worthwhile reduction;
- one-sided versus two-sided inference;
- whether time and tokens must both pass;
- the correctness rule and treatment of failed attempts; and
- expected between-task heterogeneity and effect consistency.

Under a conservative two-sided task-direction sign test, 16 tasks have only
40.5% power if the MD truly wins on 75% of tasks. A previously deferred
efficiency design proposed 35 fresh tasks because 24/35 favorable tasks gives
85.8% power at that same 75% task-win assumption. The nearest balanced
four-category version is 36 tasks, nine per category, with 83.3% power.

A magnitude-sensitive analysis of task-level log ratios may need fewer tasks.
The one clean four-task pilot has encouraging variance and effect estimates,
but it is much too small, was used to derive the MD, and contains a correctness
regression. It cannot justify a precise 16-task power claim by itself.

The strongest provisional conclusion is therefore:

- **16 × 4 × 2 = 128 scored calls remains a possible design, not an established
  sample size.** It should launch only if a prospective power simulation for
  the exact frozen endpoint, correctness rule, and testing hierarchy reaches
  at least 80% under conservative assumptions.
- If a simple, two-sided, distribution-free task-direction result is desired,
  the current evidence supports planning closer to **36 × 4 × 2 = 288 scored
  calls**, not 128.
- All prior candidate-tuning **outcomes** remain development evidence and cannot
  enter a new confirmatory p-value. Under the repository's existing
  out-of-sample convention, the four task identities are excluded too. A
  deliberately narrower fixed-known-task claim could instead use wholly fresh
  attempts on them, but that would be a conditional replication on tuned tasks,
  not untouched confirmation or evidence of task-population generalization.

No wording or sample size can guarantee statistical significance. A powered
design maximizes the probability of detecting a real prespecified effect while
controlling false positives.

## 1. The three existing designs must not be conflated

The repository contains three materially different designs.

| Design | Purpose | Tasks and repeats | Nominal subject calls | What its statistics support |
|---|---|---:|---:|---|
| 2026-08-26 paired probe | Exploratory time/token/trajectory screen | 4 tasks, 3/arm | 24 | Descriptive direction only; explicitly no significance claim |
| Archived M2 helpful comparison | Binary correctness sensitivity | 16 selected tasks, 4/arm | 128 scored comparison calls | Large correctness-effect design; not time/token power |
| Deferred evidence-bounded efficiency proposal | Wall-time confirmation | 35 fresh tasks, 4/arm | 280 scored calls | 85.8% efficiency-only sign-test power under a 75% task-win assumption |

The 128 and 280 figures exclude any task authoring, offline validation,
calibration, and allowed infrastructure replacements.

### 1.1 The 24-call exploratory plan

The implemented [Plan of Record](PLAN_OF_RECORD_2026-08-26.md) fixed four
already admitted tasks, three attempts per arm, and 24 nominal calls. Its
analysis defined:

- primary token proxy: `input_tokens - cached_input_tokens + output_tokens`;
- wall time: recorded subject duration, described as censored at 900 seconds;
- trajectory: distinct completed command/file-change items; and
- descriptive directional classification only.

It explicitly prohibited an attempt-count extension, second batch, or
confirmatory claim. It was a pilot, not a power plan.

### 1.2 The 16-task correctness design

The archived correctness protocol used four strata:

1. bug repair;
2. feature addition;
3. integration or executable behavior; and
4. behavior-preserving refactoring or data handling.

It specified 20 candidate tasks, five per stratum, and six null calibration
attempts per task. It would select four eligible tasks per stratum, yielding 16
tasks. Its complete base campaign was:

| Stage | Arithmetic | Base calls |
|---|---:|---:|
| Null calibration | 20 × 6 | 120 |
| Three-arm controls | 16 × 3 | 48 |
| Helpful-versus-null comparison | 16 × 4 × 2 | 128 |
| **Complete base campaign** |  | **296** |

The absolute ceiling with frozen infrastructure replacements was 313 calls.

The helpful-comparison power simulation assumed binary success, independent
Bernoulli attempts, and a large `+0.30` absolute success-probability effect. The
gate also required an observed improvement of at least `+0.20` and an exact
two-sided task-block sign-flip `p <= .05`. The archived plan expressly states
that its reported power does **not** establish power for a `+0.20` true effect
or later candidate comparisons.

Sources:

- [active overview](../OVERVIEW.md), “How the confirmatory experiment
  establishes significance”;
- [archived protocol](../archive/governance-pack-2026-08-26/CODER_BENEFICIAL_SENSITIVITY_PROTOCOL.md);
- [archived implementation plan](../archive/governance-pack-2026-08-26/CODER_BENEFICIAL_SENSITIVITY_M2_IMPLEMENTATION_PLAN.md), Sections 6–7.

### 1.3 The deferred 35-task efficiency design

The [evidence-bounded design basis](EVIDENCE_BOUNDED_V1_DESIGN.md) separately
floated, without authorizing:

- 35 fresh independent tasks;
- four attempts per arm;
- wall time as the primary endpoint;
- 900 seconds assigned to unresolved attempts;
- no task with fewer candidate successes than null;
- an observed reduction of at least 15%; and
- an exact two-sided task-direction sign test.

With no ties, 24 favorable tasks out of 35 gives `p = 0.0409596`. If the true
probability that a task favors the MD is 0.75, the chance of reaching at least
24 favorable tasks is 85.8%.

That calculation is correct for the efficiency sign test alone. It does not
include the probability of surviving the proposed correctness gate, which is
extremely low under ordinary stochastic equality. Section 7 below quantifies
that problem.

## 2. What the latest hardened evidence actually shows

The first complete paired cohort under the current hardened runtime is:

`runs/dev-v2/evidence-bounded-vs-null-v2`

Its preserved result is committed in `53bf48b`. The human report and machine
analysis are:

- [EVIDENCE_BOUNDED_VS_NULL_V2_RESULT.md](EVIDENCE_BOUNDED_VS_NULL_V2_RESULT.md)
- [analysis.json](../runs/dev-v2/evidence-bounded-vs-null-v2/analysis.json)

### 2.1 Registered result

| Arm | Mechanical correctness | Registered primary-token total | Subject wall-time total | Trajectory total |
|---|---:|---:|---:|---:|
| No MD | 12/12 | 1,088,214 | 4,249.436 s | 339 |
| Evidence-bounded MD | 10/12 | 709,917 | 2,787.407 s | 223 |
| Raw MD change | −2 successes | −34.8% | −34.4% | −34.2% |

The quality gate failed. The lower totals cannot be called an efficiency
improvement because two MD attempts ended with incorrect Click solutions.

### 2.2 Per-task registered medians

| Task | No-MD tokens | MD tokens | No-MD time | MD time | No-MD trajectory | MD trajectory | Correctness, no MD / MD |
|---|---:|---:|---:|---:|---:|---:|---:|
| Boltons wraps forwarding | 71,843 | 80,601 | 334.376 s | 233.774 s | 18 | 20 | 3/3 / 3/3 |
| Flask automatic options | 56,260 | 35,772 | 170.383 s | 115.317 s | 21 | 10 | 3/3 / 3/3 |
| Starlette websocket denial | 111,354 | 73,313 | 606.671 s | 305.104 s | 38 | 22 | 3/3 / 3/3 |
| Click stream lifecycle | 86,371 | 56,540 | 276.797 s | 260.816 s | 31 | 23 | 3/3 / 1/3 |

The only successful MD Click attempt took 277.281 seconds, essentially the same
as the 276.797-second no-MD median. Click's raw time saving is therefore mostly
an artifact of two incorrect attempts ending earlier.

One Boltons no-MD attempt also recorded substantially more model-manager refresh
timeouts than its paired MD attempt. Because those delays occurred inside the
subject process, they are part of recorded latency, but they demonstrate why
contemporaneous randomized pairing is necessary.

### 2.3 Endpoint choice changes the apparent effect

Offline sensitivity calculations on the same 24 attempts produce:

| Summary chosen after the fact | Token result | Wall-time result |
|---|---:|---:|
| Raw totals | 34.8% lower | 34.4% lower |
| Task arm-median directions | MD lower on 3/4 tasks | MD lower on 4/4 tasks |
| Mean paired-log ratio | 32.9% lower; 4/4 favorable | 31.3% lower; 4/4 favorable |
| Replace the two unresolved Click durations with 900 s; raw total | — | 4.3% lower |
| Same penalty; geometric mean of task arm-mean ratios | — | 13.4% lower |
| Same penalty; mean paired-log ratio | — | 15.5% lower; 3/4 favorable |

These are sensitivity calculations, not alternative findings to choose among.
They show why the estimator and failure rule must be frozen prospectively. A
post-result choice would be researcher degrees of freedom.

### 2.4 Token accounting components

| Component | No MD | MD | Raw reduction |
|---|---:|---:|---:|
| Gross input + output | 12,698,582 | 4,678,173 | 63.2% |
| Uncached input | 949,201 | 603,996 | 36.4% |
| Output | 139,013 | 105,921 | 23.8% |
| Registered uncached-input-plus-output proxy | 1,088,214 | 709,917 | 34.8% |

Cached input represented 92.4% of no-MD input and 86.8% of MD input. Gross
tokens therefore show a much larger apparent effect than the already registered
proxy. Switching to gross tokens because this result is larger would be
outcome-driven endpoint selection.

### 2.5 What is clean and what is not

Trace audits found no successful runtime cheating or hidden-answer retrieval in
the hardened v2 cohort. One Click no-MD attempt tried GitHub through shell
network tools, but the tools/DNS were unavailable and no external bytes were
returned. The two Click MD misses were genuine semantic misses: they handled
finalization but did not implement the contract's explicit `close()` behavior.

The cohort's **outcomes** are development evidence only because:

- the candidate MD was derived from these tasks and their traces;
- the four tasks have been repeatedly exposed and tuned against;
- the candidate failed the correctness gate; and
- four tasks cannot support the intended overall task-level significance claim.

Under a different, explicitly finite claim, new independent attempts on these
known tasks could estimate the final MD's future stochastic performance on
these tasks. That would not make these tasks untouched confirmation data and
would support no claim about new tasks. No existing attempt may be reused in
the new p-value.

Model-weight memorization of public upstream fixes cannot be ruled out. It is
not runtime cheating and can affect both arms.

## 3. Historical evidence exclusion

Historical batches must remain preserved but must not be pooled into a clean
confirmatory estimate or used as if they were independent fresh observations.

Direct event inspection found 42 completed GitHub MCP calls across five later
attempts:

| Batch / task / arm / attempt | Completed MCP calls |
|---|---:|
| `cost-time-probe-v1` / Click / probe / 1 | 8 |
| `cost-time-probe-v1` / Starlette / null / 3 | 4 |
| `evidence-bounded-probe-v1` / Click / previous / 1 | 10 |
| `evidence-bounded-probe-v1` / Click / previous / 2 | 11 |
| `evidence-bounded-vs-null-v1` / Click / null / 2 | 9 |

The older `maximum-difficulty-sealed-v1` cohort also contains completed web
searches in Flask no-MD attempt 1, all three Click no-MD attempts, and all three
Starlette no-MD attempts. Boltons had none. See the preserved
[cost/web-search analysis](COST_AND_WEBSEARCH_ANALYSIS_2026-08-24.md) and raw
`events.jsonl` files.

This does **not** imply that all historical no-MD successes cheated. Numerous
older no-MD passes have clean traces, and the current hardened no-MD arm passed
12/12 without successful retrieval. It means the older comparison cohorts are
not clean enough to pool for confirmatory inference.

## 4. Claim, population, and selection boundary

The statistical claim must be written before a task count is selected.

Two different claims are possible:

1. **Finite curated-set claim:** this frozen MD lowers resource use for repeated
   stochastic runs over this exact balanced task set and runtime.
2. **Task-population claim:** this frozen MD lowers expected resource use over a
   declared population from which the tasks were independently sampled.

The first claim is narrower and fits a curated challenge. The second requires a
defensible sampling frame. Neither permits claiming that the MD is best “in
general.”

For either task-level claim, the independent unit is the underlying task.
Repeated attempts estimate stochastic performance within a task; they do not
turn 16 tasks into 64 independent tasks. Related tasks may be further clustered
by repository or issue family.

### 4.1 Keep the four categories

There is no statistical reason to collapse the four intended categories. A
balanced design gives each category equal representation and prevents a large
category from dominating the result.

Four tasks per category can support one overall balanced estimate. It cannot
support four separately significant category claims.

The current task metadata does not define a canonical four-category mapping.
If the intended categories are the archived strata—bug repair, feature
addition, integration/executable behavior, and behavior-preserving
refactoring/data handling—the protocol should say so. If Wade intends different
categories, their definitions and assignment rules must be written and frozen
before task authoring or selection.

### 4.2 Fresh tasks versus fresh attempts

For an out-of-sample confirmation or task-population claim about this
trace-derived MD:

- use new underlying issues/tasks;
- prefer one repository per task;
- prohibit cosmetic variants, cloned checker structures, shared solution
  templates, or multiple tasks from one underlying fix;
- freeze category assignment before exposure;
- keep task authors/validators blind to the candidate and its outcomes; and
- freeze the candidate before its author or tuning process sees confirmation
  tasks or results.

For a deliberately finite curated-set claim, task selection may use earlier
development evidence—including evidence that a candidate creates a large
difference—provided the final candidate and task set are then frozen and the
test uses wholly new, independent attempts. Conditional on that selected set,
such a test can address future stochastic performance on those exact known
tasks. It does not estimate performance on an unbiased task population, and it
must disclose that the candidate and set were adaptively selected.

What is invalid in either claim is pooling the selection/tuning outcomes into
the final test, continuing to search candidates or tasks after seeing the test,
or presenting a selected fixed-set result as population generalization.
Candidate-independent selection by source/category, taskcheck admission, or
null-only operational criteria is the cleaner route when out-of-sample
confirmation is the goal.

This distinction permits a future competition to use a deliberately curated
fixed set without pretending it is a random sample of coding work.

## 5. Repeats and execution schedule

Four repeats per arm remain a reasonable default:

- they reduce noisy task-level estimates;
- they permit exact arm-order balance—MD first twice and no MD first twice;
- they preserve more budget for independent tasks than a repeat-heavy design;
- they match the established 16-task comparison arithmetic.

More independent tasks usually improve power and generalization more than more
repeats once a task-level estimate is reasonably stable.

Recommended schedule:

1. Run four replicate rounds.
2. Randomize task order separately within each round.
3. Execute one no-MD/MD pair consecutively for each task.
4. Freeze exactly two MD-first and two no-MD-first pairs per task.
5. Execute serially to avoid local contention.
6. Use one reasonably continuous experiment window to limit provider drift.
7. Do not delete outliers or selectively rerun a scientific failure.

If an infrastructure failure occurs before a usable subject turn, replace the
**whole affected pair** in a frozen fallback slot. Preserve the superseded pair.
Replacing only one arm destroys temporal pairing.

The current exploratory runner cannot launch this design unchanged:

- [run_batch.py](../scripts/run_batch.py) hardcodes three rounds and traverses
  tasks outermost rather than four cohort-wide replicate rounds;
- [analyze_cost_time_probe.py](../scripts/analyze_cost_time_probe.py) hardcodes
  `EXPECTED_ATTEMPTS = 3`.

This is an implementation-readiness finding, not authorization to edit those
files.

## 6. Candidate efficiency estimand

The endpoint should give every task equal weight and compare relative rather
than raw resource use, so a single large repository does not dominate.

One defensible wall-time endpoint is:

1. For each valid planned attempt, define `W`:
   - mechanically resolved: recorded subject duration;
   - mechanically unresolved or subject timeout: 900 seconds.
2. For each task `t`, compute
   `d_t = log(mean(W_MD,t) / mean(W_null,t))`.
3. Compute the equally weighted overall effect
   `D = mean_t(d_t)`.
4. Report `exp(D)` as the geometric-mean task ratio and
   `100 × (exp(D) - 1)%` as the relative change.

This choice has useful properties:

- percentage effects are comparable across tasks;
- arithmetic means within a task retain operational slow-tail cost;
- each task receives equal weight;
- logs make ratios additive; and
- incorrect early exits cannot masquerade as speed.

Reasonable alternatives exist and would answer slightly different questions:

- mean of the four paired round-level log ratios, which uses temporal pairing
  directly;
- task-level arm medians, which are robust but discard magnitude and can hide a
  failure when four attempts are present;
- a pure task-direction sign endpoint, which is easy to audit but less powerful.

The external reviewer should select one before power is calculated. The current
result demonstrates that these choices cannot be made after outcomes are seen.

### 6.1 Effect threshold

The repository contains two historical numbers:

- approximately 20% as the minimum cost difference discussed in the archived
  red-team decision; and
- 15% as the observed wall-time floor in the deferred efficiency design.

Neither is currently approved for this experiment. The smallest worthwhile
reduction must be chosen for practical reasons, not because it produces a
convenient sample size.

Testing against no change at `p <= .05` and separately requiring an observed
15% or 20% reduction supports:

> statistically lower resource use, with an observed reduction at least as
> large as the chosen floor.

It does **not** prove that the true reduction exceeds that floor. That stronger
claim requires testing against the margin itself or requiring a confidence
bound beyond it, which requires more power.

## 7. Correctness is the central unresolved design problem

A time/token MD is useful only if it preserves acceptable task completion. A
non-significant correctness difference is not equivalence.

All planned attempts must enter the correctness analysis. A success-only
efficiency endpoint is post-treatment conditioning and is biased.

### 7.1 Why the deferred every-task gate is brittle

The deferred 35-task design required candidate successes to be at least no-MD
successes on **every task**. This is safe in spirit but has a very high
false-negative rate under ordinary stochastic equality.

If both arms truly have 95% success probability and each receives four
attempts:

- probability that candidate successes are at least no-MD successes on one
  task: 84.65%;
- probability across all 16 independent tasks: 6.95%;
- probability across all 35 independent tasks: 0.293%.

Even if both arms truly succeed 99% of the time, the gate passes on all tasks
only about 53.9% of 16-task experiments and 25.9% of 35-task experiments.

Therefore, the published 85.8% efficiency-only power for 35 tasks is nowhere
near 85.8% **joint** power after that gate.

### 7.2 Two honest correctness choices

**Strict observed guardrail**

Require no observed task-level regression. This makes no equivalence claim and
accepts that many genuinely neutral candidates will be rejected by chance.

**Formal correctness non-inferiority**

Freeze a maximum tolerated macro correctness loss `delta` and require a
one-sided confidence bound or test to exclude losses worse than `-delta`. This
is statistically coherent but needs its own power analysis and a defensible
margin.

For scale only, assume independent attempts, equal true success `p = .95`, four
attempts per arm, and 16 independent tasks. A simple normal approximation gives:

| Correctness non-inferiority margin | Approximate power at true equality |
|---:|---:|
| 5 percentage points | 36% |
| 10 percentage points | 83% |

These are planning approximations, not a proposed final test. Task clustering,
heterogeneity, and multiplicity can lower power.

If no correctness loss is acceptable, use the strict guardrail and acknowledge
its low power. Statistical design cannot simultaneously promise zero observed
regressions and high acceptance probability under stochastic outcomes without
substantially more evidence or a different rule.

### 7.3 Token failures need their own rule

Wall failures have a natural enforced cap: 900 seconds. Tokens do not currently
have an analogous registered failure penalty. If a correctness rule permits
some failures, using their actual, often lower token counts can still reward
incorrect early stopping.

Defensible choices include:

- a task-level token cost-per-success estimand, with a frozen rule for zero
  successes;
- a fixed failure penalty tied to a real enforced token budget; or
- actual token use only under a strict correctness-equality qualification.

Resolved-only token analysis is not defensible as the primary endpoint. The
external reviewer should select a rule before token power is computed.

## 8. Current timeout semantics are internally inconsistent

The analyzer says a timed-out attempt is shown at 900 seconds. The hardened
runner, however, marks a non-infrastructure subject timeout invalid, and the
analyzer excludes invalid attempts from every metric.

As implemented, a timeout would therefore be labeled 900 seconds and then
excluded rather than analyzed.

Relevant code:

- [run_batch.py](../scripts/run_batch.py), `_attempt`;
- [analyze_cost_time_probe.py](../scripts/analyze_cost_time_probe.py),
  `_attempt_record`.

Recommended semantics for external review:

- evidence validity and task success are different fields;
- a usable subject timeout is a scoreable failed outcome with wall endpoint
  exactly 900 seconds;
- an infrastructure failure before a usable subject turn is replaceable under
  the frozen whole-pair policy; and
- subject timeouts are never silently excluded from wall-time analysis.

Under this rule, the estimand is resource use under a 900-second operating cap.
It is not latent uncensored completion time, so survival analysis is unnecessary.

## 9. Wall-time noise and service drift

Subject wall time is measured monotonically around the subject process; setup
and checker durations are recorded separately. Provider stalls inside that
process are part of end-to-end user latency and should not be removed after
arm identity or outcomes are known.

Controls should be limited to:

- consecutive randomized arm pairs;
- exact balance of arm-first order;
- serial execution;
- separately randomized task order each round;
- fixed attempt cap;
- one reasonably continuous run window;
- no outcome-dependent outlier deletion;
- predeclared model/runtime mismatch invalidation; and
- frozen whole-pair infrastructure replacement.

The model and effort are client-configured but not fully provider-attested in
the current evidence. The claim must remain scoped to the requested runtime as
served, and any contradictory reported identity must invalidate the affected
pair under the prospective rule.

## 10. Token definition, caching, and missing usage

The currently registered metric is:

`primary token proxy = input_tokens - cached_input_tokens + output_tokens`

This is an uncached-input-plus-output proxy. It is not gross model work and not
dollar cost. Cached input is not literally free, and provider cache policy can
change.

Provisional recommendation:

- retain this proxy for continuity unless the product objective is explicitly
  changed before fresh tasks;
- name it accurately rather than calling it billed cost;
- always report gross input, cached input, uncached input, output, reasoning,
  and total tokens as secondary components;
- do not add reasoning tokens again if they are already included in output;
- freeze CLI/runtime/token-accounting versions; and
- do not switch endpoints based on the larger 63.2% gross-token pilot result.

If any scored pair lacks required usage telemetry, preserve the attempt and
make the token endpoint inconclusive under a frozen rule rather than selectively
rerunning or dropping the inconvenient arm. Wall time and correctness may
remain separately interpretable.

A price-weighted dollar endpoint should be introduced only if dollar cost is
the stated product goal and all weights are frozen prospectively.

## 11. Primary outcome and multiplicity

Choosing whichever of time or tokens produces the smaller p-value is invalid.

The cleanest provisional hierarchy is:

1. correctness qualification;
2. failure-penalized wall-time primary test;
3. only if wall time passes, registered token proxy as a key secondary test;
4. trajectory and token components remain descriptive.

This matches the evidence-bounded MD's original target: practical wall time was
primary, trajectory was a controllable diagnostic, and token cost was
secondary.

Other valid claim structures are possible:

- If the claim requires **both** time and tokens to improve, require both tests
  to pass. This conjunctive/intersection-union claim does not inflate type-I
  error by testing each at `alpha = .05`, but joint power must be simulated.
- If a win means **either** time or tokens improves, use Holm/Bonferroni or
  another frozen multiplicity correction.
- If only one endpoint is primary, the other can remain secondary without
  supporting an independent “winner” claim.

A one-sided lower-resource test is defensible when direction is frozen in
advance. However, the repository's prior confirmatory convention and deferred
efficiency proposal were two-sided, and favorable exploratory data are already
known. Retaining a two-sided convention is the less contestable choice for this
candidate.

Category-specific effects, trajectory, commands, changed paths, and raw token
components should remain secondary unless separately powered and multiplicity
controlled.

## 12. Exact task-direction power calculations

The following are exact binomial calculations. They assume independent tasks,
no ties, a two-sided or one-sided task-direction sign test at `alpha = .05`, and
do not include the probability of passing correctness or telemetry gates.

### 12.1 Sixteen tasks

For a two-sided test:

- 13/16 favorable tasks: `p = 0.0212708`;
- 12/16 favorable tasks: `p = 0.0768127`.

| True probability a task favors MD | Power to obtain at least 13/16 |
|---:|---:|
| 0.75 | 40.5% |
| 0.80 | 59.8% |
| 0.85 | 79.0% |
| 0.90 | 93.2% |

For a predeclared one-sided test, 12/16 favorable tasks gives
`p = 0.0384064`.

| True probability a task favors MD | Power to obtain at least 12/16 |
|---:|---:|
| 0.75 | 63.0% |
| 0.80 | 79.8% |
| 0.85 | 92.1% |

Thus, under a conservative direction-only endpoint, 16 tasks require an
assumption that the MD wins on roughly 80% of tasks for one-sided 80% power, or
roughly 85% for two-sided 80% power.

### 12.2 Balanced alternatives

| Tasks | Tasks/category | Scored calls at 4/arm | Test and critical count | Planning task-win probability | Power |
|---:|---:|---:|---|---:|---:|
| 16 | 4 | 128 | two-sided, at least 13 favorable | 0.75 | 40.5% |
| 20 | 5 | 160 | two-sided, at least 15 favorable | 0.80 | 80.4% |
| 28 | 7 | 224 | one-sided, at least 19 favorable | 0.75 | 86.2% |
| 35 | unbalanced | 280 | two-sided, at least 24 favorable | 0.75 | 85.8% |
| 36 | 9 | 288 | two-sided, at least 25 favorable | 0.75 | 83.3% |

The 35-task design is slightly more powerful than 36 only because exact sign
tests have discrete critical values. Thirty-six is the clean balanced option.

## 13. Magnitude-sensitive planning calculations

A task-level log-ratio endpoint uses magnitude and can be more powerful than a
direction-only sign test. Let the smallest worthwhile ratio be `0.80`, so the
planning effect magnitude is:

`abs(log(0.80)) = 0.2231`

Under a simple normal approximation for 80% power, the approximate independent
task counts are:

| SD of task-level log effects | One-sided `alpha=.05` | Two-sided `alpha=.05` |
|---:|---:|---:|
| 0.25 | 8 | 10 |
| 0.35 | 16 | 20 |
| 0.50 | 32 | 40 |
| 0.70 | 61 | 78 |

Formula:

`n ≈ ((z_alpha + z_0.80) × SD / abs(log(0.80)))²`

The clean four-task pilot's task-level arm-median log-ratio SDs were
approximately 0.274 for the token proxy and 0.257 for wall time. Those values
make 16 tasks look plausible. They are not safe plug-in estimates because:

- there are only four tasks;
- the same tasks informed the MD;
- the task mix may understate future category heterogeneity;
- two candidate attempts failed correctness;
- failure penalties materially change the effect distribution;
- the calculation omits within-task noise and correctness-gate power; and
- time and token joint power depends on their correlation.

The final power analysis should therefore be a prospective, standard-library
simulation over the exact frozen analysis pipeline. It should include:

- four categories and their weights;
- between-task and within-task variation;
- four paired repeats;
- time/token correlation;
- failures and the chosen correctness rule;
- 900-second caps;
- missing token telemetry;
- ties;
- the exact testing hierarchy and multiplicity policy; and
- the planned effect and conservative variance scenarios.

Freeze its assumptions, random seed, iteration count, code hash, and minimum
80% **joint** power rule before a live request is approved. Do not increase the
sample after seeing an inconclusive result.

## 14. Test choice and current implementation limits

Three task-level tests deserve external review:

1. **Exact task-direction sign test.** Most robust and transparent; ignores
   magnitude and therefore often needs more tasks.
2. **Task-block sign-flip/randomization test on log effects.** Uses magnitude
   and can be more powerful, but its exchangeability assumptions and numerical
   implementation must match the actual randomized schedule.
3. **Model-based or studentized log-ratio test.** Potentially efficient, but
   relies more heavily on distributional assumptions with a small number of
   tasks.

The existing archived exact sign-flip implementation in
[beneficial_sensitivity.py](../src/mdseval/beneficial_sensitivity.py) accepts at
most 16 task effects and was written for exact rational correctness
differences. It cannot simply analyze 36 continuous log effects unchanged.

A simple binomial direction test scales to 36 tasks using the standard library.
A magnitude-sensitive 36-task analysis needs a prospectively specified
implementation—such as a valid randomization algorithm with frozen numerical
rules—not an after-the-fact substitution.

## 15. What must be frozen before any live confirmation

- exact allowed claim and task population;
- the four category definitions, assignment rule, and weights;
- fresh task IDs, manifests, checker bytes, and admission ledger;
- evidence that tasks are independent underlying issues/repositories;
- exact null and MD bytes/hashes;
- treatment/task authorship separation;
- model, reasoning effort, CLI/runtime, wrapper, container images,
  interpreters, capability isolation, and 900-second cap;
- complete task/round/arm order and randomization seed;
- four repeats per arm, if retained;
- whole-pair infrastructure replacement rule and absolute call ceiling;
- scoreable-subject-timeout semantics;
- correctness guardrail or non-inferiority margin;
- wall-time failure rule;
- token definition, failure rule, cache treatment, and missing-telemetry rule;
- task-level estimator and equal/category weighting;
- primary/key-secondary or co-primary hierarchy;
- smallest worthwhile effect;
- one-sided versus two-sided test;
- alpha and multiplicity policy;
- power model, assumptions, seed, and at least 80% joint-power gate;
- exact analysis code/hash;
- no outcome-dependent task addition, endpoint switch, attempt extension,
  selective retry, or repeat-until-significant; and
- explicit exclusion of development and contaminated evidence from
  confirmation.

`tooling/taskcheck.py` remains the sole task-admission mechanism. None of these
statistical decisions justify another admission, enforcement, receipt, or
governance layer.

## 16. Three decision-ready options

These are alternatives for external review, not approved work.

### Option A — Preserve the 128-call target

- 16 **fresh** independent tasks, four per category;
- four attempts per arm: 128 scored calls;
- magnitude-sensitive task-level log-ratio endpoint;
- prospectively simulated power for the exact correctness and endpoint rules;
- launch only if conservative joint power is at least 80%.

This can be defensible if the real effect is large and reasonably consistent.
It is not justified by the old binary-correctness power calculation.

### Option B — Conservative balanced distribution-free design

- 36 fresh independent tasks, nine per category;
- four attempts per arm: 288 scored calls;
- exact two-sided task-direction sign test;
- 83.3% efficiency-only power if the MD truly wins 75% of tasks.

This is easy to explain and hard to game statistically. It still requires a
coherent correctness rule; the historical every-task guardrail destroys joint
power.

### Option C — Preserve the deferred 35-task design

- 35 fresh independent tasks;
- four attempts per arm: 280 scored calls;
- exact two-sided sign test, 24/35 favorable;
- 85.8% efficiency-only power at task-win probability 0.75.

This keeps the existing proposal but is unbalanced across four categories and
still has the flawed every-task correctness gate unless revised.

## 17. Auditor's provisional recommendation

Do not select the task count merely by copying 16 from the correctness plan or
35 from the deferred wall-time note.

First freeze, with external review:

1. the finite-set or task-population claim;
2. the smallest worthwhile reduction—likely 15% or 20%, but chosen for practical
   value;
3. a correctness margin or explicit strict guardrail;
4. failure treatment for both wall time and tokens;
5. wall time as primary with token proxy key-secondary, or a clearly stated
   co-primary rule;
6. a two-sided task-level test; and
7. the fresh, independent four-category sampling frame.

Then run one offline prospective power simulation of the frozen design. If a
conservative simulation clears 80% joint power at 16 tasks, the 128-call design
is defensible. If not, increase **independent tasks**, not post-result repeats,
to the prespecified powered count. If simplicity and distribution-free
robustness are more important than call cost, 36 balanced tasks is the clearest
current option.

The current evidence-bounded MD is not yet a confirmed candidate: it failed the
development correctness gate on Click. Whether to revise it before freezing is
a separate development decision. This audit authorizes neither revision nor a
new run.

## 18. Reproducibility and claim boundary

The exact binomial calculations in this packet use the standard binomial tail:

`P(X >= k) = sum(comb(n, i) × q^i × (1-q)^(n-i), i=k..n)`

Two-sided sign-test p-values use twice the `q = .5` upper tail, capped at one.
The log-ratio sample-size table uses the normal approximation shown in Section
13. The non-inferiority figures use an independent-attempt normal approximation
and are explicitly illustrative.

No historical run was altered or deleted. No task, control, candidate, runner,
or analysis implementation was changed. No unit test, preflight, benchmark, or
live model call was needed for this read-only statistical audit.
