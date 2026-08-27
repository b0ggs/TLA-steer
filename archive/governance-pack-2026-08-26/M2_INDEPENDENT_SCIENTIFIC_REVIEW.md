# Independent Scientific Review: CODER Beneficial-Sensitivity Milestone 2

Reviewer basis: read-only inspection of the packet at commit `014c6b4`. All 121 payload files verified against `MANIFEST.sha256` (121 OK, 0 failures). No files were modified. No model experiments were run. The only executions performed were JSON parsing and static reading of the frozen artifacts. Conclusions about checker behavior come from reading the checkers, the frozen oracle variants, and the captured subject diffs, which together determine the outcomes without new runs.

---

## A. Executive verdict

The evaluator did not fail for the reason the design anticipated. It did not fail because the tasks were too easy for the model, although fourteen of them are. It failed because the measurement instrument is unsound.

At least six of the twenty frozen checkers enforce requirements that their public contracts never state. Every task that floored did so on a hidden requirement, not on a stated one. Every task that did not carry a hidden requirement saturated. The result is a pool that is bimodal by construction: near-deterministic success where the contract is complete, near-deterministic failure where it is not. There is no intermediate difficulty band for the calibration to find, so the selection gate could not pass, and the campaign terminated exactly as this structure predicts.

This defeats the Milestone 2 construct twice over. First, the "requirement coverage" failures the pool actually contains are failures to satisfy requirements the solver was never given. No instruction file can fix that. Second, on the fourteen sound tasks, the wrapper plus the explicit bullet-list contract format already delivers complete coverage of the stated requirements at a rate of 1.0. The helpful control has nothing left to add.

The qualification process could not catch this because it validated the checkers against reference solutions written with knowledge of the checkers. It proved internal consistency of a closed loop. It never tested the one property the experiment depended on: that an implementation faithful to the contract alone passes the checker. One instance of exactly this defect was flagged by the pre-freeze validator on feature-05 and was not actually fixed; the frozen checker bytes are identical to the flagged ones.

The v0.4.1 rerun was procedurally clean and substantively predetermined. The 116 mechanically intact v0.4 attempts already implied selection failure with near-certainty. Repeating 120 calls unchanged bought confirmatory-grade documentation of a known outcome.

Verdict: `SENSITIVITY_NOT_DEMONSTRATED` is the correct terminal label, but the correct diagnosis is instrument invalidity, not task difficulty, model saturation alone, or treatment weakness. The next step must repair checker-contract fidelity and the difficulty construct before any statistics are revisited. The statistics are mostly fine. The thing being measured is not.

---

## B. What went wrong

### B.1 Reconstruction of the design (question 1)

Causal question. For a fixed model (`gpt-5.6-sol`, effort high), fixed Codex runtime, fixed wrapper, and this frozen twenty-task diagnostic population: does replacing a zero-byte `CODER.md` with a specific helpful requirement-coverage file change the probability of complete task resolution?

Treatment. The entire project-level instruction file, compared as whole frozen bytes: `N` (empty), `H` (do-not-implement), `P` (250-word coverage-and-verify guidance).

Estimand. The finite selected-set macro-average of within-task differences in resolution probability, `theta = mean_t(p[P,t] - p[N,t])`, conditioned on the null-selected sixteen tasks.

Experimental unit. The task. Repeated attempts are nested replicates, correctly not treated as independent units.

Outcome. Binary complete resolution: all functional requirements and the regression constraint pass under the hidden checker.

Selection. Six no-MD attempts per candidate; eligible at one to five successes; four eligible tasks required per stratum; rank by distance from three.

Allowed claim. A conjunctive pass of integrity, A/A, harmful, and helpful gates permits only a sensitivity statement about this instrument under these frozen conditions. The claim boundary in the protocol is unusually disciplined and I have no complaint with it as written.

Mismatch. There is one central mismatch among the product goal, the manipulation check, and the actual design. The product wants to detect effects of arbitrary instruction files on downstream success. The manipulation check narrows this to one construct, complete coverage of explicit requirements, which is legitimate. But the actual task design then defeats that construct in both directions. The contracts present three requirements as a short labeled bullet list, delivered by a wrapper that orders the solver to read the contract completely. That format is itself a coverage aid. It leaves the helpful file nothing to teach on the sound tasks. And where tasks are hard, they are hard because the checker demands something the contract does not say, which is precisely the failure mode a coverage instruction cannot influence. The design measures contract completeness of the task author, not requirement coverage of the solver.

### B.2 The mechanism, task by task

The calibration evidence is decisive because it is nearly noiseless. Across 240 attempts in two campaigns, nineteen of twenty tasks produced identical pass counts both times. Only integration-01 moved, from 1/6 to 2/6. Durations averaged about 85 seconds against a 300-second budget with zero timeouts. This is not a stochastic system near a threshold. It is a near-deterministic system with the outcome fixed by the task artifact.

The five floor tasks, plus the single intermediate task, each fail on an unstated requirement. In every case the frozen "correct" oracle variant encodes the hidden knowledge, which proves the checker cannot be passed without it.

**bug-03 (0/6, 0/6, zero of three requirements every attempt).** The contract says "Collect repeated keys into lists" and, in its regression line, "Continue decoding a simple single key-value pair." The pristine fixture returns scalars. The natural reading is: lists for repeats, scalars otherwise. The checker requires `parse_qs` semantics: every value is a list, including the regression case, which demands `{"a":["b"]}` for input `a=b`. The frozen correct oracle uses `setdefault(key, []).append(...)` for all keys. The contract's own regression sentence actively steers the solver toward the behavior the checker rejects.

**feature-05 (0/6, one of three requirements every attempt).** The contract asks for "a dash separator row" and cells joined with `' | '`. The checker requires the separator row joined with `-+-` and requires trailing-space padding on the final column. The captured subject solutions build a perfectly reasonable table with `' | '` in the separator row and fail R1 and R2 byte-exactly. The pre-freeze validator flagged exactly this: "Checker requires an exact dash separator row that the contract never requests or defines." The frozen checker hash is identical to the flagged one. The remediation changed the contract file, but the frozen contract still does not define the separator format, so the blocker was never actually resolved.

**integration-01 (1/6 then 2/6, the pool's only intermediate task).** The contract says "write exactly one JSON object containing its numeric total." It does not name the key and it does not require compact serialization. The checker's R1 requires the exact bytes `{"total":6}\n`. The captured failing attempts use `json.dump` with default separators and produce `{"total": 6}`, correct by any plain reading, failed byte-exactly. The frozen oracle hard-codes `separators=(",",":")`. The pool's sole intermediate task is intermediate only because the model sometimes happens to emit compact JSON. This is formatting lottery, not a difficulty band.

**integration-05 (0/6, two of three requirements every attempt).** The checker's verify test writes the manifest file inside the target directory, then requires verification to succeed. Success is only possible if the solution silently excludes the manifest file being verified from the directory scan. The contract never says this. The frozen oracle carries an explicit `exclude` parameter for exactly this file. A correct exact-match implementation, which is what the contract requests, must fail R3.

**refactor-data-01 and refactor-data-02 (0/6 each, all three requirements passing every attempt).** Both contracts ask for "independent" or "copied" record dictionaries. Both checkers mutate a nested list inside a returned record and require the input to be unaffected, which requires a deep copy. The captured subject solutions use `dict(record)`, a faithful reading of "copied dictionaries," pass all functional requirements, and fail the hidden G1 every time. The frozen oracles use `copy.deepcopy`. The identical trap appears in two tasks in the same stratum, which makes their failures dependent and violates the protocol's own prohibition on shared structure that couples outcomes. It also single-handedly floored two of the five refactor-data candidates, and the redaction defect that invalidated v0.4 occurred on this same task family.

The remaining fourteen tasks are small, single-file, standard-library exercises whose reference solutions run roughly eight to twenty-five lines. The frontier model resolves them at 84 of 84 attempts across both campaigns, at full three-of-three requirement coverage every time.

### B.3 Ranking the candidate explanations (question 2)

Ranked by evidential support, strongest first.

1. **Checker and prompt/checker mismatch. Primary cause of the floors, and of the selection failure.** Direct artifact evidence in six tasks as shown above. Without these defects, the floor tasks would very likely be additional ceiling tasks, which changes the diagnosis but not the verdict.

2. **Frontier-model saturation on this task class. Primary cause of the ceilings.** Fourteen of fourteen sound tasks at 6/6 twice, median 85 seconds, no timeouts. The earlier eight-task V2 experiment showed the same complete ceiling. This is real and was predictable.

3. **Tiny synthetic task structure. Enabling condition for both.** Three-bullet contracts on 3-6 line fixtures cannot host graded partial completion. Everything either fits in one clean pass or fails on a byte. The structure removes the middle.

4. **Treatment/task misalignment. Independent defeater of the helpful gate even if selection had passed.** The wrapper commands "Read CODER.md and .issue-contract.md completely before acting" and each contract is an explicit numbered-style requirement list plus a labeled regression line. The coverage behavior `P` teaches is already supplied by the task format. Requirement coverage under `N` is 320 of 360 in v0.4.1, and the forty misses are concentrated in the mismatch tasks. There is no coverage deficit for `P` to repair.

5. **Binary outcome coarseness. Real but secondary.** The requirement-level secondary outcome exists and is more informative. The binary gate would still have failed here for the reasons above.

6. **Inadequate candidate pool size. Real but secondary.** Five candidates per stratum with four required leaves margin for a single dead task per stratum. Two dead bug tasks were never survivable. But with sound checkers this pool likely saturates rather than fails selection, so pool size is not the binding constraint.

7. **Sampling and selection rules.** The 1-5 band and the feasibility number are internally correct. The failure is the Binomial(6, 0.5) input assumption, addressed in Section F, not the rule mechanics.

8. **Intrinsic task difficulty.** Rejected as an explanation of the floors. The floor tasks are not intrinsically harder. The model solved their stated content while failing their unstated content.

9. **Shared-wrapper contamination.** The wrapper is clean of construct teaching in the harmful sense, but it does contribute to item 4 by mandating complete contract reading. No evidence of arm leakage.

10. **Treatment weakness.** Untested, because the helpful wave never ran, but the treatment is well-formed for its construct. Its problem is item 4, not its wording.

11. **Model-service variation.** No evidence. Identity was `not_reported` throughout, as disclosed. Between-campaign agreement was nearly perfect, which argues against meaningful service drift over the interval.

12. **Other: the correction loop.** The blocker remediation changed contracts or checkers for four tasks with no independent post-correction fidelity review, and the fix for the one flagged fidelity defect did not resolve it. This is a process cause layered on cause 1.

### B.4 Wrapper and helpful control together (question 4)

Yes, the wrapper plus the contract format already supplies most of the checklist behavior attributed to `P`. The wrapper requires complete reading of the contract before acting. The contract is a short enumerated list of three requirements and one labeled regression constraint. A checklist instruction adds value when requirements are numerous, dispersed, buried in prose, or when a salient primary change overshadows secondary deliverables. None of that is present. The null-arm requirement coverage of 320/360, with every miss attributable to unstated checker demands, shows the model already enumerates and completes everything it is told about.

Is +0.30 absolute plausible for this treatment on these tasks? No. On the sound tasks the null rate is 1.0 and no positive effect is arithmetically possible. On the mismatch tasks the missing requirement is invisible to the solver, so a coverage instruction cannot recover it, except by accident where the hidden demand correlates with generic thoroughness. Current evidence agrees: Zhang et al. find that beneficial persistent rules are almost exclusively negative constraints while positive process directives do not help capable agents, and Khatri finds context files never converted a near-miss to a pass because failures were implementation skill, not missing guidance. A +0.30 effect from a positive coverage directive on three-bullet tasks contradicts both the pool's own data and the external evidence.

Would harder tasks fix this? Not by themselves, and the review prompt is right to demand the mechanism. Raising algorithmic difficulty lowers null success by increasing implementation failure, which tests coding competence. `P` says nothing about coding competence, so the treatment effect on such tasks is still near zero and the experiment fails at a lower baseline instead of a higher one. Difficulty helps only if it is *omission difficulty*: many explicit, individually easy, spatially dispersed requirements where the dominant null failure mode is forgetting one, and where the checker verifies each stated item and nothing unstated. That is the only difficulty axis with a causal path from the treatment's content to the outcome.

### B.5 Why validation missed it (question 6)

The deterministic qualification established real properties: pristine fails, two author-supplied correct variants pass, two mutants fail with per-requirement negative coverage, results are stable across three executions, checks live outside the workspace. All 300 executions in the authoritative v0.4.1 qualification behaved as designed.

It never established the property the experiment rested on: **checker soundness with respect to the public contract**. Formally, that any implementation satisfying a reasonable reading of the contract is accepted. The correct variants were authored inside the same information set as the checkers, so they encode the hidden demands (`deepcopy`, compact separators and the key name `total`, the `-+-` separator row, the manifest self-exclusion, all-values-as-lists). A closed loop of author-written checker plus author-written solution can only certify that the author agrees with themselves.

The one process step that could catch this, independent validator inspection, did catch one instance (feature-05) and partially caught the class (it read prompts against checkers). It missed five others, which is unsurprising for by-eye review of byte-level oracles, and its one confirmed catch was then remediated without re-validation: the checker hash for feature-05 is unchanged from the flagged version, and the corrected contract still does not specify the format the checker enforces. The correction packet gave the author full task trees only for the four blocked tasks, and no second independent review of contract-checker fit occurred after correction. So prior audits failed for a structural reason, not a diligence reason: no stage in the pipeline ever executed the frozen checkers against artifacts produced from the contract alone.

---

## C. What should have been knowable before v0.4

Three things were knowable from evidence already in hand, and a fourth from the literature the protocol itself cites.

First, the ceiling was predicted by the project's own prior data. The V2 experiment ran the same model class on eight similar tiny synthetic Python tasks and saturated completely: 1.000 versus 1.000 in both comparisons. The roadmap records this. Twenty new tasks of the same species, same session budget, same standard-library scope, authored to "three to five explicit checkable requirements," had no empirical reason to land near 0.5. The feasibility calculation nevertheless assumed Binomial(6, 0.5) per task. That assumption was not a neutral default. It contradicted the only observed data point and was never tested by even a two-task pilot.

Second, checker soundness was a known problem class with a known fix. The protocol cites SWE-bench, whose inherited-test grading is criticized precisely for rejecting valid alternatives and accepting incomplete ones, and it cites DeepSWE, whose central design feature is a hand-written verifier that accepts any implementation providing the requested functionality. Qualification item 2 ("accept two materially different correct implementations") gestures at this but leaves authorship of the correct variants inside the checker's information set. The stronger requirement, independent contract-only solutions, costs nothing at runtime and was available.

Third, the pre-freeze validator explicitly surfaced the fatal defect class. Blocker: a checker enforcing an exact format the contract never defines. A design that takes that blocker seriously asks the obvious next question, whether the other sixteen "passed" tasks harbor the same class, and verifies the fix by rerunning the fidelity check. Neither happened.

Fourth, five candidates per stratum against a four-per-stratum requirement, under a selection band that any near-deterministic task fails, gives essentially no redundancy. This is visible from the design arithmetic alone.

---

## D. What v0.4 revealed, and whether v0.4.1 should have run (question 7)

What v0.4 revealed. Its 116 mechanically intact attempts showed 14 tasks at 6/6, five at 0/6, and integration-01 at 1/6, with per-attempt requirement counts that localize every floor to a fixed subset of checks. The bug stratum sat at 6,6,6,6,0. Under the frozen eligibility rule, four of five bug tasks needed to land in the 1-5 band. Given outcome patterns that consistent, the probability of a different selection verdict on rerun was negligible. The evidence-capture defect itself was narrow: a redactor truncated four event-log lines containing the literal `key="id"` on refactor-data-01, corrupting evidence records without touching outcomes.

The exclusion decision was correct. `INVALID` evidence must not enter confirmatory estimates, and the team never laundered it. That discipline is to their credit.

But exclusion from inference is not the same as inadmissibility for resource decisions, and here the team conflated the two. The protocol's own framework already names the correct category: contaminated development evidence. Development evidence is exactly what one uses to decide whether launching an expensive campaign is futile. The v0.4 pattern made `SENSITIVITY_NOT_DEMONSTRATED` at the selection gate a near-certain outcome of v0.4.1, and the repaired component, evidence capture, had no plausible causal path to different task outcomes. The remediation plan even required demonstrating the redactor defect on synthetic input before implementation, which shows the team understood how to validate a fix without 120 live calls. A commissioning-grade probe plus offline replay of the sanitizer would have validated the capture repair at a tiny fraction of the cost.

There is one honest defense: the protocol's rigid one-campaign lifecycle contains no futility rule, and running the fixed machinery end-to-end produced a clean, fully valid negative record that now anchors this review. That has some value. But the team's own commissioning rules state that "unchanged reruns are forbidden" for probes, precisely because repeating an unchanged procedure after a known failure signature is uninformative. The same logic applies at campaign scale. My assessment: v0.4.1 was scientifically defensible only as machinery validation, was not defensible as an attempt to reach a different scientific outcome, and the correct fix is a predeclared futility clause in the next protocol version, so that this judgment never again has to be made ad hoc.

---

## E. Task-by-task assessment (question 3)

Complexity is judged from the fixture, contract scope, and the frozen oracle solutions (roughly 8-25 lines for library tasks, 30-80 lines for CLI tasks). "Coverage-caused?" asks whether the observed null failures plausibly stem from incomplete coverage of *stated* requirements. "P could change it?" asks whether the helpful treatment could plausibly change the observed failure mode.

| Task | Null v0.4 / v0.4.1 | Actual complexity | Consistent failure signature | Checker faithful to contract? | Coverage-caused? | P could change it? | Disposition |
|---|---|---|---|---|---|---|---|
| bug-01 | 6/6 / 6/6 | Small (duration parse/format) | None (ceiling) | Yes, as far as exercised | n/a | No (ceiling) | Retain for development only |
| bug-02 | 6/6 / 6/6 | Small (interval merge) | None | Yes, as far as exercised | n/a | No | Retain for development only |
| bug-03 | 0/6 / 0/6 | Small (query decode) | 0/3 requirements every attempt | **No.** Checker imposes all-values-as-lists; contract's regression line implies scalar singles | No; the demanded semantics are unstated | No | Replace, and independently re-review contract vs checker |
| bug-04 | 6/6 / 6/6 | Small (inventory ops) | None | Yes, as far as exercised | n/a | No | Retain for development only |
| bug-05 | 6/6 / 6/6 | Small (median of iterable) | None | Yes, as far as exercised | n/a | No | Retain for development only |
| feature-01 | 6/6 / 6/6 | Small (lazy chunking) | None | Yes, as far as exercised | n/a | No | Retain for development only |
| feature-02 | 6/6 / 6/6 | Small (escaped deep lookup) | None | Yes; prior blocker was mutant coverage only, fixed | n/a | No | Retain for development only |
| feature-03 | 6/6 / 6/6 | Small (sliding-window limiter) | None | Yes, as far as exercised | n/a | No | Retain for development only |
| feature-04 | 6/6 / 6/6 | Small (recursive masking) | None | Yes, as far as exercised | n/a | No | Retain for development only |
| feature-05 | 0/6 / 0/6 | Small (text table render) | Fails R1/R2 on exact `-+-` separator row and trailing padding; passes R3 | **No.** Validator flagged this pre-freeze; checker bytes unchanged; contract still silent on format | No; format is unstated | No | Revise contract to fully specify format or relax checker; independent re-review mandatory |
| integration-01 | 1/6 / 2/6 | Small CLI (JSON sum) | Fails R1 byte-exact `{"total":6}` unless model happens to emit compact JSON; key name `total` also unstated | **No.** R1 enforces serialization bytes and a key name the contract omits | No | No; occasional passes are formatting luck | Revise: state key and format, or compare parsed JSON; independent re-review |
| integration-02 | 6/6 / 6/6 | Small CLI (unique lines) | None | Yes, as far as exercised | n/a | No | Retain for development only |
| integration-03 | 6/6 / 6/6 | Small CLI (env templating) | None | Yes, as far as exercised | n/a | No | Retain for development only |
| integration-04 | 6/6 / 6/6 | Small CLI (deep JSON merge) | None | Yes post-correction (blocker was missing error-case coverage; checker was changed) | n/a | No | Retain for development only |
| integration-05 | 0/6 / 0/6 | Medium-small CLI (checksum manifest) | Fails R3: verify test writes the manifest inside the scanned directory and demands success, requiring silent self-exclusion | **No.** Oracle hard-codes an `exclude` for the manifest file; contract never mentions it | No | No | Revise checker (write manifest outside the tree, or state the exclusion); independent re-review |
| refactor-data-01 | 0/6 / 0/6 | Small (stable dedupe) | 3/3 requirements pass, G1 deep-copy regression fails every attempt | **No.** "Independent dictionaries" read naturally as shallow copy; checker demands deepcopy | No | No | Revise contract wording or checker; note shared trap with -02 |
| refactor-data-02 | 0/6 / 0/6 | Small (UTC grouping) | 3/3 requirements pass, G1 deep-copy regression fails every attempt | **No.** Same hidden deepcopy demand; dependent failure with -01 | No | No | Revise; the duplicate trap violates the pool's independence requirement |
| refactor-data-03 | 6/6 / 6/6 | Small (cycle-safe flatten) | None | Yes, as far as exercised | n/a | No | Retain for development only |
| refactor-data-04 | 6/6 / 6/6 | Small (config overlay) | None | Yes, as far as exercised | n/a | No | Retain for development only |
| refactor-data-05 | 6/6 / 6/6 | Small (schema row coercion) | None | Yes; prior blocker was cosmetic oracle diversity | n/a | No | Retain for development only |

Two caveats on the "Yes" rows. "Faithful as far as exercised" means no contradiction between contract and checker was observed at a 6/6 ceiling; a ceiling exercises only one solution path, so latent mismatches in the fourteen sound tasks cannot be excluded, only unobserved. And every task in this table, including the sound ones, is now outcome-exposed development material. None may serve in a future confirmatory set.

---

## F. Statistical assessment (question 5)

**Five candidates per stratum, selecting four.** Genuine design error in robustness, defensible in intent. One structurally dead task per stratum is fatal. Given that the same author wrote all twenty tasks and authoring defects correlate within an author, the effective redundancy was lower than it looked. Reasonable practice for a screen-then-select design is at least two spare candidates per required slot.

**Six calibration attempts and the 1-5 band.** Defensible local choice, correctly reasoned. The band widening prevents chance discard of genuinely centered tasks, and the ranking still prefers the center. I verified the arithmetic: with per-task eligibility 62/64 under Binomial(6, 0.5), the probability that all four strata yield four eligible tasks is 0.9638 as stated. The mechanics are fine.

**The feasibility calculation assuming null rate 0.5.** Genuine error, and the load-bearing one. The 0.9638 number is conditional on an assumption with zero empirical support that contradicted the project's only prior observation (complete saturation on the same task species). The realized per-task rates were approximately {1.0 x 14, 0.0 x 5, 0.25 x 1}, under which the feasibility probability is effectively zero. A feasibility calculation whose input is a guess is a hypothesis, and the protocol treated it as a planning fact. The missing step was a cheap pilot to estimate the rate distribution before freezing twenty tasks.

**Null-conditioned selection and regression to the mean.** Handled correctly. Calibration attempts are excluded from scored estimates, fresh interleaved observations are collected for every arm, and the protocol names RTM explicitly. The plug-in Laplace-smoothed rates in the post-calibration power check still carry six-attempt noise, which the protocol also discloses. Defensible.

**Sixteen tasks, four attempts per helpful arm.** Defensible for the declared +0.30 planning alternative. The Monte Carlo grid (power 0.85-0.94 across null rates) is plausible on its face for that effect size and I found no internal inconsistency in its specification. Note one interaction the protocol acknowledges but the design ignored in practice: had selection somehow passed with fallback tasks near the band edges, the smoothed null rates of 7/8 would cap the attainable per-task effect at 1/8, and the frozen +0.30-capped power gate would itself have stopped the run. Selection failure and power failure were two doors to the same wall.

**Task-level exact sign-flip test.** Correct and correctly caveated. The protocol is unusually careful to state that exchangeability, not the weak null, is what the test targets, and that unequal arm sizes would invalidate it, which is the right reason to keep `N2` out of the harmful comparison. One qualification: the exact test assumes independent task effects, and the duplicated deep-copy trap shows the pool can violate that assumption through shared authoring patterns. In a sound pool this is a minor risk; here it is a documented one.

**+0.20 observed-effect gate and +0.30 planning alternative.** Defensible and honestly framed. The protocol explicitly says the gate does not establish `theta >= 0.20` and that a lower-bound claim would need a different test. The granularity note (13/64 minimum passing estimate) is correct.

**A/A and harmful gates.** Defensible. The A/A rule with one attempt per arm can produce a false winner only through an extreme split and is applied bidirectionally. The harmful gate's arithmetic checks out: two-sided sign test with n nonzero pairs passes at n >= 6, hence the minimum detectable harmful effect of 6/16 = 0.375, and the stated pass probabilities (0.190, 0.593, 0.895 at null rates 0.25, 0.375, 0.5 when H always fails) match binomial tail calculations. The disclosed honest-false-stop risk at low baselines is real; at the baselines this pool actually produces, near 1.0, the harmful gate would have been the one gate likely to pass.

**Independence, exchangeability, temporal drift, multiplicity, external validity.** Mostly defensible on paper. Serial execution with paired within-task randomization is the right mitigation for drift in the helpful wave. Conjunctive gates avoid multiplicity inflation. External validity is explicitly disclaimed. The two genuine weaknesses: task-effect dependence through a single author's repeated patterns, and the unverifiable model-service identity (`not_reported` on all 240 attempts), which the protocol discloses but which limits every claim to "the configured runtime as served."

Summary. The statistical machinery is largely sound and its self-disclosure is above the field's standard. The genuine errors are concentrated upstream of the statistics: an unfounded feasibility input, insufficient pool redundancy, and a qualification suite that never tested the assumption every downstream number depended on.

---

## G. Single recommended next scientific step (question 8)

**Run one bounded development-phase instrument-validation study, on a redesigned omission-sensitive task specification, gated by two falsification checks that must pass before any protocol v0.5 is written or any confirmatory pool is authored.**

Concretely, as one move: specify the revised task class (below), build a development pool of roughly ten to twelve tasks under it, and subject that pool to (a) an offline contract-only soundness check and (b) a small preregistered no-MD live pilot. The study's deliverable is a validated task-generation specification plus measured null behavior, not a verdict about any treatment. Only if both checks pass does anyone draft the next authoritative protocol.

The task class change is the substance. Tasks must be difficult on the omission axis, not the algorithm axis: eight to twelve explicit, individually easy requirements per task, dispersed across a multi-file repository rather than listed in one tidy block; one salient primary change plus several non-salient secondary deliverables (the doc line, the config entry, the added test, the changelog, the boundary case in a second module) that a hurried solver plausibly skips; checkers that verify each stated requirement behaviorally and verify nothing unstated; and a graded requirement-coverage fraction recorded alongside the binary gate, with the null coverage fraction, not the binary rate, as the calibration dial. This is the only difficulty design with a causal mechanism running from the helpful file's content to the outcome: the file targets omission, so the tasks must make omission the dominant null failure mode.

Answers to the required sub-questions.

*What may be learned from the current tasks.* Three things, all development-grade. The fourteen sound tasks calibrate a saturation frontier: this model, in 300 seconds, solves three-bullet standard-library tasks at essentially 1.0, so nothing of that shape belongs in any future pool. The six defective tasks are a catalogue of checker-authoring pathologies (byte-exact serialization, unstated key names, hidden deep-copy semantics, self-referential test fixtures, undefined output formats) that should be written into the checker-authoring guidance and the validator's checklist. And the near-zero between-campaign variance tells you six calibration attempts are more than enough for tasks of this determinism; attempt budget should shift toward more tasks.

*What is now contaminated.* All twenty tasks, their contracts, checkers, fixtures, oracles, and both campaigns' outcomes are exposed development evidence. Anyone who has read this packet, including this reviewer, the project team, and any model instance shown it, is contaminated for authoring or validating a future confirmatory task set. The helpful control `P` and its authorship record remain uncontaminated by outcomes and may be reused frozen. The wrapper likewise, though its "read completely" line deserves reconsideration given Section B.4.

*Should Milestone 2 retain this construct.* Yes, with a corrected operationalization. Complete requirement coverage remains a defensible, checkable, role-relevant construct, and the external evidence (Shepard and Albrecht's coverage-driven gains, Zhang's finding that effects appear only on discriminative task subsets) suggests instruction effects on coverage are detectable when the task structure permits omission. What must not be retained is the equation of "multi-requirement" with "three bullets in one list."

*Different, harder, more numerous, or differently measured.* Different in structure as specified above. Harder only on the omission axis. More numerous in candidates per stratum, at least six or seven per four required, funded by the demonstrated surplus in the attempt budget. Differently measured: requirement-level coverage fraction as the calibrated and reported dial, binary resolution retained as the confirmatory gate.

*Development pool then fresh confirmation tasks.* Yes, required. The development pool validates the specification and burns its own generalizability in doing so. The confirmatory pool must be freshly authored to the frozen specification by parties with no exposure to this packet or the development outcomes, then pass the same contract-only soundness gate before freeze. Per the packet's own instruction, this review must not be treated as authorship of that set, and I have deliberately not drafted example confirmation tasks.

*Can an established benchmark help.* As a calibration side-channel, yes; as the M2 instrument, no. SWE-bench-family tasks can bracket the model's difficulty frontier and supply the "discriminative subset" method Zhang et al. used, but they carry training-contamination risk for exactly this model class, their inherited tests have the same soundness pathology this pool just demonstrated, and their construct is issue resolution, not multi-requirement coverage. DeepSWE is closer in verifier philosophy and originality, but its long-horizon scope does not fit a 300-second single-session runtime, and importing it would change the population the product claims to serve. Use benchmarks to sanity-check difficulty estimates, not to replace the role-specific pool.

*Would a weaker model rescue the design.* No. Downshifting the model manufactures intermediate rates by lowering competence, which validates the evaluator only for that model. Khatri's finding that borderline difficulty is strongly agent-specific (rho = 0.75 between agents, and that is between two frontier agents) means a weak-model calibration would not transfer. The product's stated target is the frontier-model evaluator, so the difficulty must come from the tasks.

*Smallest pre-authoritative empirical check.* Two checks, in order, both cheap, both falsifying. First, zero model calls: for every development task, two independent parties (or independently sandboxed non-subject sessions) who see only the public contract each write a solution; the frozen checker must accept both. Any rejection falsifies checker soundness and blocks the task. This check, applied to the current pool, would have failed six of twenty tasks before a single live call. Second, about 24-30 subject calls: three no-MD attempts on eight to ten development tasks, with a preregistered pass band, for example mean per-requirement null coverage between 0.55 and 0.90 and at least half the tasks strictly inside 0/3 and 3/3 on the binary outcome. Missing the band falsifies the difficulty assumption at one fifth of a campaign's cost.

---

## H. Preconditions before implementation or additional live calls (question 9)

No new authoritative subject call should be permitted until every item below holds. These are stop/go criteria, not aspirations.

1. **Contract-only soundness gate (GO requires 100%).** Every candidate task's frozen checker accepts at least two solutions authored from the public contract alone, by parties attested to have had no access to the checker, oracles, mutants, or each other. Any rejection is a STOP for that task; two rejections traceable to the same authoring pattern are a STOP for the pool pending a specification fix.
2. **Post-correction re-validation rule.** Any task revised after a validator blocker returns to independent fidelity review, and the reviewer confirms the specific blocker no longer reproduces against the frozen bytes. An unchanged checker hash on a checker-side blocker is an automatic STOP. This rule would have caught feature-05.
3. **Independence audit.** No two tasks in the pool share a hidden-check pattern, regression template, or trap structure. The duplicated deep-copy regression is the reference violation.
4. **Empirically grounded feasibility input.** The selection-feasibility and power calculations must use null-rate estimates from the development pilot, with sensitivity shown across the pilot's uncertainty, not an assumed homogeneous rate. A feasibility probability computed from an untested rate assumption is a STOP.
5. **Pilot difficulty band met.** The preregistered no-MD micro-pilot lands inside its declared coverage and intermediacy band (Section G). Outside the band is a STOP and a specification revision, not a task-level patch-and-retry.
6. **Pool redundancy floor.** At least six qualified candidates per stratum for every four to be selected, with the feasibility calculation rerun on pilot-informed rates showing at least a 0.9 probability of full selection.
7. **Futility clause in the protocol.** The new protocol version predeclares that development-grade evidence implying near-certain gate failure (with a stated threshold) blocks campaign launch under an unchanged design, closing the gap that produced v0.4.1.
8. **Contamination boundary enforced.** Confirmatory task authors and validators attest non-exposure to this packet, this review, and both M2 campaigns. This reviewer's outputs may inform the specification and the checklists, never the confirmatory task content.
9. **Everything currently required by protocol v0.4's integrity machinery** (hash freezing, blinded mappings, append-only evidence, offline replay) carries forward unchanged. That machinery worked. It is the one part of this experiment that needs no repair.

GO is the conjunction of 1 through 9. Any single failure is NO-GO for authoritative calls, without exception for sunk cost.

---

## I. Literature-supported claims and limitations (question 10)

I verified every citation in the protocol's Section 15 table against current sources. All twelve resolve to real works, and the protocol's one-line summaries are faithful to them. Verification notes and direct links follow, with published work distinguished from preprints and from my own inferences.

**Published, verified.**
- Chen et al., HumanEval: https://arxiv.org/abs/2107.03374. Functional-correctness grading and repeated sampling. Correctly used.
- Jimenez et al., SWE-bench: https://arxiv.org/abs/2310.06770. Repository-level resolution. Correctly used; note that the field's later critique of its inherited tests is directly relevant to this project's failure.
- Cawley and Talbot, JMLR 2010: https://www.jmlr.org/papers/v11/cawley10a.html. Selection bias from tuning on evaluation data. Correctly motivates the calibration/confirmation split.
- Dwork et al., Science 2015: https://doi.org/10.1126/science.aaa9375. Adaptive holdout reuse. Correctly motivates the contamination rules.
- Lakens 2017: https://doi.org/10.1177/1948550617697177. Non-significance is not equivalence. Correctly applied in the A/A framing.
- Card et al., EMNLP 2020: https://aclanthology.org/2020.emnlp-main.745/. Prospective power in NLP. Correctly applied in spirit; the failure here was the power input, not the power method.

**2026 preprints, verified as real, summaries checked (not peer reviewed).**
- Bjarnason, Silva, Monperrus, "On Randomness in Agentic Evals": https://arxiv.org/abs/2602.07150. 60,000 trajectories showing single-run pass@1 is unreliable. Supports the repeated-attempt design. Ironically, this pool exhibited almost no run-to-run randomness, which is itself diagnostic of degenerate tasks.
- Gloaguen et al., "Evaluating AGENTS.md": https://arxiv.org/abs/2602.11988. Context files do not generally improve success and add over 20% inference cost. Supports the protocol's null-first skepticism and the cost-tracking secondary outcomes.
- Zhang et al., "Guardrails Beat Guidance": https://arxiv.org/abs/2604.11088. Random rules matched expert rules (+13.8pp) on a *discriminative subset* of SWE-bench Verified; beneficial rules were negative constraints, harmful ones positive directives. Two direct lessons: effects are measurable only on discriminative task subsets, which this pool lacked; and a positive process directive like the coverage MD is the rule type least likely to help a capable agent.
- Shepard and Albrecht, "Probe-and-Refine Tuning": https://arxiv.org/abs/2606.20512. Refined repository guidance lifted resolve rate 28.3% to 33.0%, with gains from coverage (reaching the right files), not per-patch precision. This is the best current evidence that instruction effects on coverage exist and are detectable, at effect sizes of roughly +0.05, an order of magnitude below this protocol's +0.30 planning alternative.
- Khatri, "Do Context Files Help Coding Agents?": https://arxiv.org/abs/2607.27250. Context strategy did not move correctness (bounded to 10-15pp by equivalence testing); failures were implementation skill, not missing guidance; the real AGENTS.md never converted a near-miss; borderline difficulty is agent-specific (rho = 0.75). Directly supports Sections B.4 and G.
- DeepSWE: https://arxiv.org/abs/2607.07946. Original tasks with hand-written verifiers that accept any implementation providing the requested functionality, and an order-of-magnitude lower judge-disagreement rate than inherited tests. This is the published articulation of exactly the checker-soundness property M2's qualification never tested.

**Inferences that are mine, not the literature's.** The diagnosis that six specific checkers contradict their contracts is my direct reading of the frozen artifacts, confirmed by the frozen oracles and captured subject diffs; no citation asserts it. The claim that omission-structured difficulty is the only mechanism linking this treatment to the outcome is an inference from the treatment's content plus Zhang and Khatri, not a demonstrated result. The estimate that a +0.30 effect is implausible extrapolates from external effect sizes measured on different populations; it is a strong prior, not a measurement. And the recommendation architecture in Section G is local design judgment, consistent with but not required by any cited source.

**Limitations of this review.** I could not inspect the four defective v0.4 event logs, the concealed mapping plaintexts, or per-attempt qualification directories, which the packet intentionally excludes; nothing in my conclusions depends on them. Checker faithfulness for the fourteen ceiling tasks is confirmed only along the single solution path a ceiling exercises. Model-service identity was `not_reported` throughout, so, as the protocol itself states, every behavioral claim attaches to the configured runtime as served. Finally, having read every outcome in this packet, I am contaminated for confirmatory task authorship, and this document should be handled under the packet's own rule: development guidance, never independent authorship of what comes next.
