# MDs_EVAL Project Roadmap

**Status:** Proposed high-level roadmap for user approval

**Date:** August 10, 2026

**Scope:** The scientific and product stages required to turn MDs_EVAL into a
working evaluator for complete role-instruction Markdown files

## Status and authority

This document defines the project direction, major stages, and exit gates. It is
not an implementation plan and does not authorize code changes, task creation,
live model calls, commits, pushes, candidate generation, or publication claims.

Every future implementation plan must identify the single roadmap stage it
serves and remain within that stage. Existing frozen experiments and their raw
evidence remain historical facts; this roadmap does not rewrite them. The file
`MD_EVAL_EXPERIMENT_REDESIGN_REQUIREMENTS.md` is useful advisory input but is not
adopted wholesale and is not a competing implementation authority.

Only one implementation authority may be active at a time. Before new work
begins, the existing `coder-outcome-evaluator-v2-implementation-plan.md` must be
explicitly amended or superseded while remaining preserved as the authority for
its historical frozen experiment. A new plan may not silently coexist as a
second active V2 authority.

## 1. Product mission

MDs_EVAL should answer:

> For a fixed model, harness, tools, resource limits, and declared role-specific
> workload, does replacing one exact, hash-locked, complete role-instruction MD
> with another—including a zero-instruction comparison condition—change the
> agent's downstream task success?

The first role is CODER. Later roles may include AUDITOR, RESEARCHER, and
ORCHESTRATOR, but each role requires its own task population, outcomes, controls,
and claim boundary.

The product must evaluate completed work, not resemblance to a preferred author,
style, workflow, or vocabulary. A Karpathy-inspired file is one possible
treatment; it wins only if it produces better coding outcomes under the declared
conditions.

The product is not initially:

- an autonomous instruction optimizer;
- a universal MD leaderboard;
- a dashboard or hosted service;
- a multi-agent topology optimizer;
- evidence that one file is best across models, roles, or workloads; or
- a mechanism for forcing a winner when the evidence is weak.

## 2. What the evaluator compares

The experimental treatment is the entire immutable MD file. The comparison may
be champion versus candidate, candidate versus candidate, or an MD versus a
defined null such as a zero-byte project-level role file.

“Zero instructions” never means that the agent receives literally no
instructions. Shared platform instructions, harness instructions, tools,
permissions, task prompts, and delivery mechanics remain fixed. Every report
must state what was shared and what changed.

For an operational whole-file comparison, all effects of the file—including
wording, length, priming, and interactions among instructions—belong to the
treatment. Claims about one instruction family or semantic mechanism require a
separate ablation or matched-control experiment.

The reusable product therefore consists of four scientific objects:

1. A role-specific task population and outcome definition.
2. A qualified, immutable task pack and measurement procedure.
3. Two immutable treatment MDs under one fixed runtime configuration.
4. A preserved comparison record with uncertainty, controls, costs, and raw
   evidence.

## 3. Current evidence and its boundary

The current engine has already demonstrated important plumbing:

- frozen treatment and task hashes;
- isolated sessions and workspaces;
- executable task-oracle qualification;
- raw trajectories, patches, checks, usage, and workspace evidence;
- deterministic offline replay;
- an A/A symmetry diagnostic;
- a generic harmful-instruction control; and
- task-level objective outcome reporting.

The completed champion-versus-zero-byte CODER run passed all existing controls,
while both real arms resolved all 16 attempts. Its result was `INCONCLUSIVE` with
a complete binary-outcome ceiling. This establishes neither equivalence nor
general uselessness of `CODER.md`.

The harmful control proves that instructions can cause a gross negative effect
through this channel. It does not prove that the current task pack can detect a
useful or modest instruction effect. The frozen eight-task pack is now
development and diagnostic evidence; it is not a fresh confirmation set.

## 4. Governing scientific principles

All later stages must preserve these principles.

### Downstream outcomes first

For CODER, the primary outcome is full requested task resolution: required
behavior works, relevant regressions pass, explicit user-facing constraints are
met, and protected experimental inputs remain intact.

Process observations such as commands run, files inspected, patch size, tool
calls, tokens, and time may explain an effect or measure efficiency. They do not
rescue failed task resolution. Subjective properties such as elegance,
clarification quality, or unnecessary complexity require a frozen rubric,
blinded evaluation, and reliability evidence before they can support a claim.

### Candidate-independent measurement

Task authors and validators must not inspect candidate MDs or candidate results.
Treatment authors must not inspect hidden tasks, checks, reference solutions,
mutants, calibration trajectories, or confirmation outcomes.

A public role-level construct taxonomy may guide independent work. Exact task
and treatment artifacts must then be authored separately and frozen before they
are mapped for interpretation. Missing coverage is reported as out of scope; it
does not trigger post-result rewriting.

### Calibration is not comparison evidence

No-MD calibration may screen task validity and diagnostic difficulty. Those
observations are selection evidence only. After the task set is selected and
frozen, the scored comparison must collect fresh, contemporaneous, randomized or
interleaved observations for every real arm.

This prevents regression-to-the-mean, selection, time, and model-service drift
from becoming treatment effects.

### Diagnostic sensitivity and practical value are different

A diagnostic sensitivity set may deliberately concentrate on tasks in the fixed
agent's informative difficulty range. It asks whether the instrument can detect
an instruction effect under conditions where one is observable.

A representative evaluation set must instead follow a declared sampling frame
for the intended workload. It retains naturally easy and hard tasks and natural
user instructions. It asks how much practical value the MD provides across that
workload.

Neither result substitutes for the other.

### Independent tasks drive inference

Repeated attempts estimate stochastic one-attempt reliability. They remain
nested within tasks and are not additional independent tasks. Related tasks may
also be clustered within repositories or task families.

Before a confirmatory comparison, the protocol must declare the estimand,
smallest worthwhile effect, sampling unit, clustering, repeats, randomization,
analysis, uncertainty interval, false-positive threshold, power target,
invalid-run policy, and multiplicity policy.

Non-significance is not equivalence. `EQUIVALENT` is permitted only when a
justified equivalence margin, adequate independent task count, and prospective
equivalence procedure have been approved. Otherwise the honest result is
`INCONCLUSIVE`.

### Evidence is immutable

Raw evidence is never deleted or rewritten to improve a result. Treatments,
tasks, checks, wrapper, analysis, retry rules, and resource limits are frozen
before scored calls. Anyone exposed to a hidden confirmation set is contaminated
for independently authoring or validating its replacement.

## 5. Project milestones

| Milestone | What it must demonstrate | What it must not claim |
| --- | --- | --- |
| 0. Preserve current evidence | Existing outcomes and limitations are reproducible | That current MDs are equivalent |
| 1. Freeze the scientific contract | The role, workload, estimand, outcomes, controls, and analysis are unambiguous | That the evaluator is already sensitive |
| 2. Demonstrate beneficial sensitivity | The same instrument handles null, harmful, and helpful directions correctly | Real-world value or a best complete MD |
| 3. Deliver the reusable CODER product | Any frozen manually supplied CODER candidate can be compared reproducibly | Universal generality |
| 4. Evaluate representative CODER candidates | Candidate effects and costs are estimated on the intended coding workload | Fresh confirmation after repeated selection |
| 5. Confirm and promote a CODER champion | A frozen finalist survives one untouched, adequately powered confirmation | Cross-model or cross-role superiority |
| 6. Extend individual roles | Each new role has validated role-specific outcomes and task packs | One universal MD score |
| 7. Evaluate bundles and topologies | Instruction-bundle and coordination effects are isolated in sequence | Causal attribution when MDs and topology change together |

Milestone 2 is the next demonstrable MVP. Milestone 3 is the reusable CODER
product MVP. Milestone 5 is the first scientifically defensible CODER selection
claim. Later milestones are optional expansion, not unfinished CODER MVP work.

## 6. Milestone 0 — preserve and classify current evidence

### Purpose

Prevent earlier work from being lost or silently promoted beyond what it shows.

### Required outcome

- Preserve the frozen source, treatments, tasks, raw calls, reports, and replay.
- Record that the current real comparison saturated at a ceiling.
- Classify the current task pack as exposed development/diagnostic evidence.
- Preserve the exact definition of the zero-byte treatment and shared context.

### Exit gate

An independent reader can reproduce the current report and understand its claim
boundary without relying on conversation history.

### Current status

Substantially complete through the verified handoff archive. No additional live
run is required for this milestone.

## 7. Milestone 1 — freeze the CODER scientific contract

### Purpose

Define what “better coding” means before creating more tasks or treatments.

### Required outcome

- Declare the intended coding workload and its sampling frame.
- Define the exact whole-file treatment contrast, including the null condition.
- Define objective task resolution and any hard regression constraints.
- Separate primary, efficiency, and exploratory process outcomes.
- Define diagnostic, representative, development, validation, and confirmation
  evidence and how each may be used.
- Define the statistical unit, paired estimand, clustering, uncertainty,
  smallest worthwhile effect, power target, and verdict meanings.
- Define the information boundaries among task author, task validator, treatment
  author, solver, and analyst.
- Produce a targeted literature table distinguishing published evidence,
  preprints, local design choices, and unresolved questions.

### Exit gate

One concise protocol passes one statistical review and one construct/scope
review, receives at most one bounded revision, and leaves no decision that could
change after outcomes are observed.

### Not part of this milestone

No production code, task solutions, candidate MD, or live comparison is created.

## 8. Milestone 2 — demonstrate beneficial measurement sensitivity

### Purpose

Prove that MDs_EVAL can detect a beneficial instruction effect, not merely gross
harm or no difference.

### Required outcome

- Freeze a broad, role-relevant construct before artifact creation.
- Independently create a narrow helpful instruction control and a larger
  candidate-independent task pool in that broad domain.
- Qualify every checker using pristine state, multiple correct implementations,
  multiple plausible incorrect implementations, integrity checks, and
  repeatability checks.
- Use separate no-MD calibration attempts to identify a predeclared diagnostic
  difficulty band; do not reuse them as scored baseline observations.
- Freeze the diagnostic set, treatments, wrapper, model, budgets, analysis, and
  stop conditions.
- Collect fresh interleaved observations for A/A, harmful, and helpful-versus-null
  comparisons through the same pipeline.
- Preserve all evidence and replay the result offline.

The helpful treatment is a manipulation check, not a proposed champion. It
validates sensitivity only within its declared construct and task distribution.
If a research claim concerns helpful semantic content rather than the operational
effect of the complete file, a separately justified length/format-matched
irrelevant or shuffled control may be required.

### Exit gate

- A/A does not create a false winner under the predeclared rule.
- The harmful control loses in the expected direction.
- The helpful control wins in the expected direction with the predeclared effect
  and uncertainty requirements.
- Oracle, integrity, balance, and evidence gates pass.

A failed gate stops the milestone. Evidence is preserved and the failure is
diagnosed; tasks or controls are not tuned and rerun until they pass under the
same nominal experiment.

### Allowed claim

> Under the frozen diagnostic conditions, the A/A comparison produced no false
> winner, and MDs_EVAL detected harmful and beneficial instruction contrasts in
> their predeclared directions.

This is the demonstrable evaluator MVP.

## 9. Milestone 3 — deliver the reusable CODER product

### Purpose

Turn the qualified scientific procedure into a repeatable operator workflow for
manually supplied complete CODER files.

### Required capability

- Accept two arbitrary immutable CODER treatments, including champion and null.
- Record candidate identity, content hash, lineage, and comparison history.
- Bind a comparison to a compatible task-pack qualification record.
- Separate one-time or periodic instrument qualification from fresh candidate
  comparisons without silently weakening controls.
- Run balanced, fresh, paired observations under identical conditions.
- Preserve raw evidence and reproduce reports without model calls.
- Produce a concise human report showing task outcomes, uncertainty, controls,
  failures, tokens, tool calls, duration, and exact claim boundary.
- Keep promotion human-controlled.

### Exit gate

From a clean checkout, an operator can supply a new frozen CODER file and receive
a reproducible `A_BETTER`, `B_BETTER`, `INCONCLUSIVE`, or `INVALID` result without
editing evaluator source or overwriting history.

### Explicitly deferred

Dashboard, hosted service, autonomous candidate generation, leaderboard ranking
and presentation, tournament systems, and other roles.

### Future champion-ladder direction — recorded, not planned

The long-term CODER product should evolve into a versioned champion/challenger
ladder. Each changed MD becomes a new immutable candidate; one confirmed
champion remains in place until a challenger satisfies the approved promotion
gate, and all attempted candidates and outcomes remain in history. Champion
status is specific to the role, model/runtime, and qualified task-population
version.

This paragraph records product direction only. It does not choose a ranking
method, leaderboard schema, user interface, tournament format, requalification
policy, multiple-candidate statistical policy, or automated candidate source.
Those decisions require a separate roadmap-compatible product plan after
Milestone 5 has produced the first confirmed CODER champion. Milestones 3–5
should preserve the immutable identities, lineage, comparison history, and
promotion evidence that a future ladder will need without building the ladder
itself.

## 10. Milestone 4 — evaluate representative CODER candidates

### Purpose

Estimate practical MD value on the coding work the product is meant to support.

### Required outcome

- Establish a candidate-independent representative sampling frame.
- Include realistic repositories, task types, durations, languages, and natural
  prompts to the extent required by the declared deployment workload.
- Retain valid ceiling and floor tasks rather than filtering the workload into a
  diagnostic-only distribution.
- Use development evidence for small single-change variants and ablations.
- Track every attempted candidate and account for repeated selection or label
  results as exploratory.
- Keep task resolution primary and costs separate.

### Exit gate

One finalist is frozen based on transparent development/validation evidence, or
the project records that no candidate justified advancement.

The finalist result is not yet fresh confirmation.

## 11. Milestone 5 — confirm and promote a CODER champion

### Purpose

Make one defensible deployment decision without reusing selection evidence.

### Required outcome

- Create or independently secure a fresh confirmation task set after the
  finalist, runtime, outcomes, and analysis are frozen.
- Prevent the finalist author and selection process from seeing confirmation
  tasks or results in advance.
- Run the confirmation once under the approved invalidation policy.
- Report superiority, inferiority, equivalence only if prospectively supported,
  inconclusive evidence, or invalid comparison.
- Require a human promotion decision and preserve the previous champion and full
  lineage.

### Exit gate

The project either promotes a confirmed CODER champion with a narrowly scoped
claim or retains the existing champion because evidence was negative,
inconclusive, or invalid.

## 12. Milestone 6 — extend individual role evaluators

### Purpose

Reuse the qualified engine without pretending that coding metrics apply to every
role.

Each role begins again at its scientific contract and sensitivity demonstration.
Examples of possible primary constructs include:

- **AUDITOR:** consequential defects correctly identified, with false positives
  and missed defects reported separately.
- **RESEARCHER:** source-supported factual conclusions, coverage of the research
  question, and calibrated uncertainty.
- **ORCHESTRATOR:** completion of the parent goal through bounded delegation,
  correct integration, and absence of duplicated or abandoned required work.

These examples are starting constructs, not frozen rubrics. Each role must pass
its own null, harmful, helpful, oracle, and representativeness gates before real
candidate claims.

### Exit gate

Each supported role has an independently qualified task pack, primary outcome,
comparison protocol, and confirmed candidate history. There is no universal
cross-role score.

## 13. Milestone 7 — bundles and agent topologies

### Purpose

Study cooperation only after individual role files are stable enough to freeze.

Proceed in causal order:

1. Compare multi-file role bundles under one fixed topology, initially changing
   one file at a time.
2. Freeze the MD bundle before comparing topologies.
3. Compare a bounded menu such as solo, primary-plus-checker,
   specialist-plus-reviewer, and bounded swarm-plus-mediator.
4. Report results by task class and resource envelope rather than declaring one
   universal best topology.

MD content and topology must not change simultaneously in the first causal
comparisons.

### Exit gate

Bundle effects and topology effects have separate versioned treatments,
qualified tasks, fixed budgets, and preserved evidence.

## 14. Product and research completion criteria

The reusable CODER product is complete when:

- a new manually supplied CODER file can be frozen and compared without source
  edits;
- its task pack has passed oracle and directional-sensitivity qualification;
- the comparison uses fresh paired observations and an approved analysis;
- reports are understandable to an operator while retaining the detail needed
  for statistical review;
- all evidence and lineage are preserved; and
- the result can honestly be better, worse, inconclusive, or invalid.

A publishable CODER study additionally requires:

- a declared and defensible target workload;
- enough independent repositories/tasks for the planned effect and uncertainty;
- separation of development, selection, and fresh confirmation;
- reproducible code, task provenance, raw evidence, and analysis;
- explicit treatment of model/runtime version limits and contamination;
- comparison with the closest instruction-file literature; and
- claims restricted to the tested population and configuration.

Other roles, bundles, topologies, optimization, and a dashboard are future
products. Their absence does not make the CODER product incomplete.

## 15. Anti-scope-creep and anti-loop rules

- One roadmap milestone and one active implementation plan at a time.
- Every plan declares allowed outputs, frozen inputs, live-call limits, and stop
  conditions before work begins.
- Audits identify blockers; they do not automatically authorize extra features.
- Each stage receives at most one planned audit pass and one bounded revision
  unless the user explicitly approves a new cycle.
- A failed live gate is preserved and reported. It is not repeatedly rerun or
  tuned away.
- Calibration, development, validation, and confirmation evidence are never
  silently pooled.
- No dashboard, optimizer, new role, or topology work begins while the current
  milestone's measurement gate is unresolved.
- No leaderboard, ranking system, tournament, or champion-ladder UI is designed
  or implemented before the first confirmed CODER champion and a separately
  approved plan.
- No implementation grows merely to approximate a security boundary when a
  simpler, enforceable experimental separation satisfies the declared threat
  model.
- Existing working infrastructure is reused unless a demonstrated defect blocks
  the active milestone.
- “Unused budget” is not a reason to expand scope.

## 16. Immediate next decision

The next work should be Milestone 1: a concise CODER scientific protocol for the
beneficial-sensitivity experiment. It should resolve the target construct,
authorship boundaries, calibration-versus-comparison split, primary outcome,
positive-control interpretation, statistical design, call ceiling, and stop
conditions.

Only after that protocol is approved should the existing active V2 authority be
explicitly amended or superseded by one bounded Milestone 2 implementation plan.
No competing active plan may be introduced. No current MD should be optimized,
promoted, or rejected from the existing ceiling result.

## 17. Literature foundation

The roadmap is informed by several complementary research traditions:

- Functional coding success and repeated sampling:
  [HumanEval](https://arxiv.org/abs/2107.03374).
- Repository-level issue resolution:
  [SWE-bench](https://arxiv.org/abs/2310.06770).
- Original tasks and implementation-agnostic functional verifiers:
  [DeepSWE](https://arxiv.org/abs/2607.07946).
- Stochastic variation and repeated `pass@1` estimation:
  [Bjarnason, Silva, and Monperrus](https://arxiv.org/abs/2602.07150).
- Context-file null comparisons and possible instruction costs:
  [Gloaguen et al.](https://arxiv.org/abs/2602.11988).
- Controlled persistent-rule interventions:
  [Zhang et al.](https://arxiv.org/abs/2604.11088).
- Tuned repository guidance under fixed conditions:
  [Shepard and Albrecht](https://arxiv.org/abs/2606.20512).
- Agent-specific informative difficulty and null effects:
  [Khatri](https://arxiv.org/abs/2607.27250).
- Selection bias from repeated optimization against finite evaluation data:
  [Cawley and Talbot](https://www.jmlr.org/papers/v11/cawley10a.html).
- Adaptive holdout reuse:
  [Dwork et al.](https://doi.org/10.1126/science.aaa9375).
- Equivalence testing and smallest effects of interest:
  [Lakens](https://doi.org/10.1177/1948550617697177).

Several directly relevant 2026 works are recent preprints. They support design
choices and identify risks, but no single study supplies a universal MD rubric,
difficulty threshold, effect size, or sample count. Those remain prospective,
configuration-specific decisions for MDs_EVAL.
