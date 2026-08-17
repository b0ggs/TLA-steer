# MD_EVAL Experiment Redesign Requirements

## Purpose

The goal of MD_EVAL is to create a scientifically credible way to answer:

> Does an instruction MD file cause an LLM agent to perform better than the same agent without that MD file?

The current system successfully runs controlled comparisons, but the experiment design needs improvement. The main problem was not the evaluator infrastructure; the problem was that the tasks, treatments, and measurement design did not create a situation where an MD file had a fair opportunity to demonstrate value.

This document describes what needs to change and why. It intentionally stays at a high level. The agent implementing these changes should inspect the existing codebase and choose the appropriate implementation.

---

# 1. Separate Task Creation From Task Evaluation

## Problem

A task creator who knows the MD being tested can accidentally create tasks that reward that MD or leak the expected behavior.

The task author must not create tasks specifically designed to make one treatment win.

## Requirement

Introduce a clear separation between:

1. **Task Designer**
2. **Task Validator**
3. **Agent Solver**

The Task Designer creates candidate tasks.

The Task Validator checks whether each task is valid, measurable, and useful for the experiment.

The Agent Solver is the LLM being evaluated.

The solver must never see:

- hidden tests or scoring logic
- reference solutions
- deliberately incorrect mutant solutions
- task-quality metadata
- why the task was selected
- which MD treatments are being compared
- prior calibration outcomes

The Task Designer and Task Validator should operate in separate sessions or contexts from the Solver. A task-generating LLM may be the same model family as the solver, but it must not share hidden context, task solutions, or evaluation history with solver runs.

## Why

The evaluation should measure whether an MD improves general agent behavior, not whether a benchmark was designed around that MD.

A model can generate tasks that the same model later fails. However, the model's claim that a task is difficult is not evidence. Difficulty must be established through fresh, blind solver runs.

---

# 2. Build a Mandatory Task Quality Rubric

## Problem

A task is not useful merely because the no-MD model fails it.

Some failures happen because:

- the task is impossible
- the instructions are internally inconsistent
- essential information is missing
- the hidden checker is wrong
- the checker recognizes only one implementation
- the task leaks the process behavior being tested
- the model made an unrelated coding mistake
- the task is too easy or too hard to measure a treatment effect

## Requirement

Every evaluation task must pass all of the following gates before it can enter a frozen comparison set.

A task that fails any required gate must be revised or rejected. These gates should not be averaged into one quality score because strength in one area cannot compensate for a fatal flaw in another.

## Gate 1: Validity

The task must have a coherent, attainable correct outcome.

Evidence should include:

- the starting repository or workspace fails the intended acceptance check
- a reference implementation passes
- at least one independently produced alternative correct implementation passes

## Gate 2: Checker Discrimination

The checker must measure the intended behavior rather than one exact patch.

Evidence should include:

- multiple correct implementations pass
- multiple deliberately incorrect implementations fail
- incorrect implementations fail for the intended reason
- the checker does not depend on formatting, naming, or patch shape unless those are explicit requirements

## Gate 3: No Policy Leakage

The task prompt may state product requirements and necessary context, but it must not tell the solver the exact process behavior that the MD is intended to provide.

For review, every task-prompt sentence should be classifiable as one of:

- **Requirement**
- **Context**
- **Process Policy**

A task testing an MD behavior must not contain a Process Policy sentence that duplicates that behavior.

For example, a task intended to test whether the MD causes the agent to verify the real user-facing entry point should not explicitly instruct both treatments to run that entry point.

## Gate 4: MD Relevance

Each task must declare:

- the behavior being tested
- why an instruction MD could plausibly affect that behavior
- the expected failure signature when the behavior is absent
- the observable evidence used to score the behavior

A task should not be admitted merely because the no-MD solver fails. The failure should be related to the targeted behavior rather than a random implementation error.

## Gate 5: Informative Difficulty

The task must provide room for treatment differences.

Tasks that the no-MD condition always solves or never solves provide little or no power for a diagnostic comparison.

Difficulty must be measured through repeated no-MD solver runs, not estimated by the task designer.

For an initial diagnostic suite, tasks solved by the no-MD condition in roughly 20% to 80% of fresh attempts are generally more informative than tasks at a complete ceiling or floor. The final threshold should be declared before candidate treatments are evaluated.

## Gate 6: Candidate-Blind Selection

Task inclusion must not depend on whether a candidate MD wins.

Tasks should be selected using task validation and no-MD calibration only. Candidate MD outcomes must not be used to decide which tasks remain in the benchmark.

## Gate 7: Frozen Inputs

Before treatment comparison begins, freeze and identify by hash:

- task prompt
- starting workspace
- hidden checker
- reference solution
- task metadata
- shared wrapper
- model and runtime configuration
- treatment MD files

---

# 3. Run the No-MD Condition First

## Problem

The previous comparison began before establishing whether the task pack had enough headroom to measure improvement. Both the MD and no-MD treatments then solved all scored tasks, creating a ceiling effect.

## Requirement

The experiment workflow must be ordered as follows:

1. Create a larger pool of candidate tasks.
2. Validate each task and checker.
3. Run the baseline/no-MD condition on every candidate task using fresh solver sessions.
4. Estimate baseline success and identify failure signatures.
5. Remove or separate tasks that are too easy, too hard, invalid, or unrelated to the targeted MD behavior.
6. Determine whether enough informative tasks remain to support the planned comparison.
7. Freeze the selected task set.
8. Only then run candidate MD treatments.

## Why

No-MD calibration is essential for statistical power.

A task where both treatments are almost certain to succeed cannot demonstrate improvement. A task where both are almost certain to fail is similarly uninformative.

The baseline calibration stage is therefore not optional setup. It determines whether the main experiment is capable of answering its question.

## Important Restriction

Do not run candidate MDs during task selection.

Otherwise, tasks may be retained because they favor a candidate or rejected because they expose a weakness, creating benchmark overfitting.

---

# 4. Distinguish Two Task Sets

## Problem

Selecting only medium-difficulty tasks improves diagnostic sensitivity but may no longer represent the natural task distribution an agent encounters.

## Requirement

MD_EVAL should distinguish between:

### Diagnostic Sensitivity Set

A calibrated set designed to reveal whether an MD can change behavior under informative conditions.

This set may exclude complete ceiling and floor tasks.

### Representative Evaluation Set

A set sampled to reflect the intended real-world use of the evaluated agent, including easier and harder tasks where appropriate.

## Why

The diagnostic set answers:

> Can this evaluator detect whether the MD changes behavior?

The representative set answers:

> What is the practical value of the MD across the intended workload?

These are related but different questions and should not be silently combined.

---

# 5. Create a Neutral Experimental Treatment MD

## Problem

The existing treatment MD is based on a particular system, workflow philosophy, and set of operating assumptions.

It may contain:

- project-specific conventions
- personal workflow preferences
- handoff or status-file rules
- behaviors the current task environment cannot exercise
- instructions unrelated to the outcomes being scored

That makes it difficult to answer the more basic experimental question:

> Can a well-designed instruction MD improve agent performance at all?

## Requirement

Create a new treatment MD specifically for the MD_EVAL experiment.

This treatment should:

- be independent of the user's existing agent system
- be model- and harness-neutral where possible
- focus on broadly useful coding-agent behavior
- include only instructions that can be exercised and measured by the task set
- avoid unnecessary ceremony and project-specific artifacts
- avoid wording copied from individual hidden tasks
- remain concise enough that its cost can be evaluated honestly

Potential behavior areas include:

- confirm all requirements before declaring completion
- avoid unnecessary or unrelated changes
- inspect available repository evidence before guessing
- ask a focused question only when required information is genuinely unavailable
- verify important behavior using an appropriate execution path
- complete every requested deliverable
- prefer the smallest sufficient change over unnecessary architecture

These examples are behavioral domains, not required final wording.

---

# 6. Create the Treatment MD Blindly

## Problem

A treatment author who sees the hidden tasks, tests, failure signatures, or calibration results can optimize the MD for the benchmark.

That would test benchmark memorization or prompt overfitting rather than general usefulness.

## Requirement

The person or LLM creating the neutral treatment MD must not see:

- evaluation task prompts
- task repositories or fixtures
- hidden tests
- reference solutions
- mutant solutions
- task categories tied to specific cases
- no-MD calibration outcomes
- solver trajectories
- candidate comparison results

The treatment author should receive only:

- the general objective of improving coding-agent reliability
- the broad allowed scope of the MD
- the environment's real capabilities and restrictions
- a length or token budget
- general writing requirements such as clarity and non-contradiction

## Treatment Author Independence

The treatment MD should be created in a separate session or context from task creation and validation.

The task designer should not revise hidden tasks after seeing how the treatment performs.

The treatment author should not revise the MD after seeing the frozen confirmation results.

## Why

The benchmark must test whether the MD generalizes to unseen tasks.

---

# 7. Validate the Treatment MD Before Testing Performance

## Problem

A neutral treatment MD can still be internally inconsistent, impossible to follow, too vague, or incompatible with the evaluation environment.

## Requirement

Before the treatment enters the scored comparison, validate it without exposing hidden tasks.

Review should confirm that:

- each instruction is understandable
- instructions do not contradict one another
- instructions are compatible with available tools and permissions
- instructions do not require prohibited actions
- each claimed behavior has at least one corresponding task family
- the MD does not restate shared wrapper instructions unnecessarily
- the MD does not contain task-specific answers
- the MD fits within the declared length budget

This validation should examine the treatment itself and public experiment specification, not hidden benchmark contents.

---

# 8. Improve Task-to-MD Alignment

## Problem

The previous experiment tested a broad workflow MD against small coding tasks while also prohibiting many behaviors described by the MD.

Many instructions therefore had no opportunity to influence the outcome.

## Requirement

Create a treatment-to-outcome map before running the experiment.

For every behavior claimed to be evaluated, identify:

- the corresponding MD instruction or instruction family
- the task family that exercises it
- the observable failure mode
- the scoring method

Examples:

| MD behavior | Task design | Observable outcome |
|---|---|---|
| Avoid expanding scope | Include tempting but unrelated cleanup opportunities | Unrelated files or regions changed |
| Verify before completion | Include a change that appears correct but fails through the real entry point | Appropriate verification evidence and final correctness |
| Resolve repository-answerable ambiguity | Place the needed answer in repository evidence | Evidence inspected and correct decision made |
| Ask when ambiguity is genuinely unresolved | Provide conflicting requirements with no authoritative answer | Focused clarification and no speculative edit |
| Complete all deliverables | Request several independently checkable outputs | Every deliverable completed |
| Prefer a small sufficient solution | Provide an easy path to unnecessary abstraction | Correctness with limited scope and complexity |

## Reporting Restriction

The final report must not claim that the entire MD was evaluated unless every major instruction family was exercised and measured.

It should instead state exactly which behaviors were tested and which were out of scope.

---

# 9. Keep the Shared Wrapper Minimal and Neutral

## Problem

The shared wrapper can accidentally duplicate the treatment, override it, or prohibit the behaviors the experiment claims to test.

## Requirement

The shared wrapper should contain only:

- unavoidable safety constraints
- delivery mechanics
- tool or environment facts
- required output protocol

It should not contain general coding policy that is part of the treatment comparison.

Every wrapper sentence should be classifiable as:

- **Safety**
- **Environment**
- **Delivery**
- **Output Protocol**

If a wrapper rule prevents a behavior, that behavior must be marked out of scope for the experiment.

## Why

The experiment should isolate the incremental effect of the treatment MD rather than quietly supplying the same instructions to both arms.

---

# 10. Add a Narrow Helpful Positive Control

## Problem

The previous experiment showed that a harmful instruction can reduce performance. That proves the instruction channel can cause gross harm, but it does not prove that MD_EVAL can detect a useful instruction.

## Requirement

Add a separate positive-control treatment containing one narrow, broadly applicable, non-obvious helpful rule.

Create a dedicated positive-control task subset where that rule should matter.

The positive-control author must not see the exact hidden tasks or tests. They may be told the broad behavioral domain being controlled, but not benchmark answers.

Example domain:

> Before declaring success, validate the actual user-facing execution path rather than relying only on internal unit tests.

The exact instruction and tasks should be designed independently.

## Why

A credible evaluator should demonstrate that it can detect:

- no difference through A/A testing
- harmful instructions through a negative control
- beneficial instructions through a positive control

The main candidate comparison should not proceed as confirmatory evidence if the evaluator cannot pass these sensitivity checks.

---

# 11. Measure More Than Final Correctness

## Problem

An MD may change behavior without changing binary task success. It may also preserve correctness while imposing substantial cost.

## Requirement

Define primary and secondary outcomes before running treatment comparisons.

## Primary Outcome

The primary outcome should remain a clearly defined task-level success measure, such as functional correctness plus required behavioral constraints.

## Secondary Outcomes

Where deterministically measurable, track:

- token usage
- latency
- tool calls
- failed commands
- files inspected
- files changed
- unrelated modifications
- verification commands executed
- completion of every deliverable
- clarification quality
- final disposition
- unnecessary complexity or patch footprint

## Scoring Rule

Do not create an after-the-fact combined score that makes a preferred treatment win.

Any combined score, gate, or tradeoff rule must be defined before the comparison.

Correctness and efficiency should remain separately visible even when a promotion rule considers both.

---

# 12. Plan Statistical Power Before the Main Comparison

## Problem

A larger number of model calls does not automatically create a well-powered experiment. Statistical information depends heavily on the number of independent tasks and the number of tasks where treatments produce different outcomes.

## Requirement

Use the no-MD calibration results to determine whether the planned experiment has enough informative tasks.

Before the main treatment comparison, declare:

- the smallest improvement worth detecting
- the acceptable false-positive threshold
- the desired statistical power
- the number of independent tasks
- the number of repeated solver attempts per task
- how repeated attempts will be summarized at the task level
- how inconclusive results will be handled

Do not choose the task count only because it seems larger than the previous experiment.

## Why

The no-MD calibration stage should inform whether the experiment can detect the effect size that matters.

If the available task pack cannot support that decision, the correct action is to create and qualify more tasks before spending on the candidate comparison.

---

# 13. Freeze Development, Validation, and Confirmation Stages

## Problem

Repeatedly editing the MD or task set after viewing results causes overfitting.

## Requirement

Separate experiment materials into:

### Development Set

Used to debug the evaluator, inspect failures, and improve general task-generation procedures.

### Validation Set

Used to select among candidate treatment MDs or refine the experiment before final confirmation.

### Confirmation Set

A fresh hidden set used once after the final treatment, wrapper, metrics, and analysis plan are frozen.

Once confirmation results are viewed, that set must not be reused to revise the treatment and claim a fresh result.

---

# 14. Preserve Experimental Honesty

Every experiment report should state:

- the exact question tested
- the model and agent configuration
- what no-MD means in that experiment
- what shared instructions both treatments received
- which MD behaviors were tested
- which behaviors were not tested
- how tasks were created and validated
- how no-MD calibration was performed
- whether the treatment author saw any benchmark information
- whether the task designer saw the treatment
- whether the task set was frozen before candidate runs
- the primary and secondary outcomes
- treatment costs as well as benefits
- any failed controls or invalidated runs

Allowed conclusions must include:

- the MD improved performance
- the MD reduced performance
- the MD preserved correctness while improving efficiency
- the MD preserved correctness but increased cost
- no meaningful difference was detected
- the experiment was inconclusive
- the experiment was invalid because a required control failed

"Inconclusive" is a valid scientific result.

---

# 15. Definition of Done for the Redesign

The redesign is complete when MD_EVAL can demonstrate all of the following:

1. Candidate tasks pass a documented validity and checker-quality rubric.
2. Task selection is performed without access to candidate MD outcomes.
3. The no-MD condition is run first to establish task difficulty and experimental power.
4. Ceiling and floor tasks are handled according to a predeclared policy.
5. The selected task set is frozen before treatment comparison.
6. The shared wrapper does not leak or override the behavior being tested.
7. A new neutral treatment MD is created without access to hidden tasks or tests.
8. The task designer does not create tasks around the wording of that treatment MD.
9. Every claimed MD behavior maps to a task family and deterministic outcome.
10. A/A testing correctly detects no difference.
11. A harmful control demonstrates sensitivity to harmful instructions.
12. A helpful positive control demonstrates sensitivity to beneficial instructions.
13. Correctness, behavior, and efficiency are reported separately.
14. The analysis can honestly return improvement, harm, equivalence under a declared margin, no detected difference, or inconclusive.
15. A fresh confirmation set is evaluated only after all choices are frozen.

---

# Final Goal

MD_EVAL should become a reliable instrument for answering:

> Given this model, agent configuration, task population, runtime, and instruction MD, does the MD provide measurable value compared with the same setup without it?

The core runner and evidence system may already provide much of the experimental infrastructure.

The main redesign priorities are:

1. task quality
2. no-MD-first calibration
3. statistical power
4. treatment independence
5. task-to-MD alignment
6. positive and negative sensitivity controls
7. honest reporting

The goal is not to make MD files appear effective.

The goal is to determine when they help, when they hurt, when they add cost without benefit, and when the available evidence cannot answer the question.
