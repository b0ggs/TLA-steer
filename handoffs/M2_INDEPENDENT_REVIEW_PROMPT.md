You are an independent senior research-methods reviewer with expertise in
randomized experiments, statistical power, psychometrics/benchmark design, and
LLM coding-agent evaluation.

This is a READ-ONLY scientific review. Do not edit files, write code, propose
implementation architecture, or run new model experiments. First determine
whether the scientific design is sound and what evidence would justify the
next experiment.

Project goal:
For a fixed model, runtime, agent configuration, and role-specific task
population, determine whether changing only a complete project instruction MD
causes better downstream task performance and at what measured cost. The
eventual product should compare arbitrary CODER.md files, but Milestone 2 is
only a manipulation check: can the evaluator correctly handle identical and
harmful controls and detect a deliberately useful instruction effect?

Important chronology:
1. An earlier eight-task evaluator produced 1.0 pass@1 for both compared
   conditions, including a CODER.md-versus-no-MD comparison.
2. The project was redesigned around no-MD-first calibration, independent task
   and treatment authorship, objective checkers, a harmful control, and a
   helpful requirement-coverage control.
3. Twenty new tasks were created: five each in bug, feature, integration, and
   refactor/data strata. Six no-MD attempts were planned per task. A task was
   eligible at 1–5 successes, and four eligible tasks were required per
   stratum.
4. The v0.4 campaign completed 120 calls but was declared INVALID because four
   attempt event logs had evidence-capture defects. Nevertheless, 116 attempts
   were mechanically intact. Its task pattern was 14 tasks at 6/6, five at
   0/6, and integration-01 at 1/6.
5. The capture defect was repaired without changing tasks, treatment, wrapper,
   model, or statistics. The authoritative v0.4.1 campaign repeated all 120
   no-MD calls. It had no infrastructure or evidence failures but again found
   14 tasks at 6/6, five at 0/6, and integration-01 at 2/6. It stopped before
   controls because the bug stratum had zero eligible tasks.
6. v0.4 is excluded from confirmatory estimates, but assess separately whether
   its outcomes should have prevented launching an unchanged v0.4.1 campaign.

Do not accept the project team’s diagnosis automatically. Inspect the protocol,
wrapper, treatments, every task contract, starting fixture, checker, oracle,
and both campaigns’ trajectories.

Answer these questions:

1. Reconstruct the causal question, treatment, estimand, experimental unit,
   outcome, selection procedure, and allowed claim. Identify any mismatch
   among the product goal, Milestone 2 manipulation check, and actual design.

2. Explain why the two redesign attempts produced ceiling/floor outcomes.
   Distinguish and rank these hypotheses using evidence:
   - intrinsic task difficulty;
   - tiny/synthetic task structure;
   - frontier-model saturation;
   - checker or prompt/checker mismatch;
   - shared-wrapper contamination;
   - treatment/task misalignment;
   - treatment weakness;
   - binary-outcome coarseness;
   - inadequate candidate-pool size;
   - sampling and selection rules;
   - model-service variation;
   - other causes you identify.

3. Produce a task-by-task table containing:
   - null success count in both campaigns;
   - actual coding complexity;
   - consistent failure signature;
   - whether the checker faithfully implements the public contract;
   - whether failure is plausibly caused by incomplete requirement coverage;
   - whether the helpful treatment could reasonably change that failure;
   - disposition: retain for development, revise, replace, or independently
     re-review.

4. Examine the wrapper and helpful control together. Does the wrapper or the
   explicit bullet-list task format already supply the checklist/coverage
   behavior attributed to the helpful MD? Is a +0.30 absolute effect plausible
   for this treatment on these tasks? Would merely making the tasks harder
   address this, or would it test coding competence rather than instruction
   adherence?

5. Audit the statistical design:
   - five candidate tasks per stratum while selecting four;
   - six calibration attempts and the 1–5 eligibility band;
   - the feasibility calculation assuming null rate 0.5;
   - null-conditioned task selection and regression to the mean;
   - sixteen tasks with four attempts per helpful arm;
   - task-level exact sign-flip test;
   - +0.20 observed-effect gate and +0.30 planning alternative;
   - A/A and harmful gates;
   - independence, exchangeability, temporal drift, multiplicity, and external
     validity.
   Separate genuine errors from defensible local choices.

6. Assess the validation process. Which properties were established by the
   deterministic correct/mutant qualification, and which essential properties
   were never established? Explain why prior audits failed to catch the
   present problem.

7. Decide whether repeating v0.4.1 unchanged was scientifically defensible
   after the v0.4 trajectories existed. Distinguish exclusion from confirmatory
   inference from legitimate use as contaminated development evidence.

8. Recommend one next scientific move—not a menu and not implementation.
   It must minimize another expensive dead-end while preserving experimental
   honesty. State:
   - what may be learned from the current tasks;
   - what is now contaminated;
   - whether Milestone 2 should retain this construct;
   - whether tasks should be different, harder, more numerous, or differently
     measured;
   - whether a development pool followed by fresh structurally matched
     confirmation tasks is required;
   - whether an established coding benchmark can help and its contamination or
     representativeness limitations;
   - whether changing to a weaker model would validate only that model rather
     than the intended frontier-model evaluator;
   - the smallest pre-authoritative empirical check that would falsify the new
     assumptions before a full campaign.

9. Identify what evidence must exist before any new authoritative call is
   permitted. Include explicit stop/go criteria.

10. Use current primary literature where available. Verify the citations in the
    supplied protocol rather than assuming their summaries are accurate.
    Distinguish published guidance from local judgment. Provide direct links
    and clearly label inferences.

Required output:
A. Executive verdict
B. What went wrong
C. What should have been knowable before v0.4
D. What v0.4 revealed and why v0.4.1 should or should not have run
E. Task-by-task assessment
F. Statistical assessment
G. Single recommended next scientific step
H. Preconditions before implementation or additional live calls
I. Literature-supported claims and limitations

Be adversarial but constructive. Do not recommend “harder tasks” without
specifying the causal mechanism by which difficulty would create sensitivity
to the MD rather than merely reduce general coding success.
