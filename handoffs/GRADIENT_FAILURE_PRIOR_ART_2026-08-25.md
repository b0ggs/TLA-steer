# Gradient Failure — Prior Art Sweep

Date: 2026-08-25
Question: has anyone already built a unified, cross-domain taxonomy of the ways an
optimization signal can fail when an automated loop tries to hill-climb against it?

Method: arXiv + web search, ~20 query families, seeded from the brief plus variants.
Items below are grouped by which of our four families they touch. Each entry ends with a
verdict: **SAME** (same phenomenon, same level of the stack) or **ANALOGOUS** (same shape,
different level — e.g. it's about a human institution, or about an SGD step, not about an
agentic experiment loop).

Confidence note: entries marked (snippet) were characterized from search-result summaries
rather than a full read of the paper. Entries with no marker were fetched and read at least
at abstract level.

---

## 0. Unification attempts — the closest things to what we are building

### 0.1 Manheim & Garrabrant (2018/2019), *Categorizing Variants of Goodhart's Law*
arXiv:1803.04585. https://arxiv.org/abs/1803.04585
Four mechanisms by which a proxy breaks *under optimization pressure*: **Regressional**
(optimizing selects for the noise term / "tails come apart"), **Extremal** (optimization
pushes into a regime where the proxy-goal correlation never held), **Causal** (intervening
on a correlate that isn't on the causal path), **Adversarial** (a second agent manipulates
the proxy).
Covers: our family (2) almost entirely — proxy divergence, simulator exploits, tampering.
Says nothing about families (1), (3), (4).
Verdict: **SAME** for family 2. This is the single most-cited taxonomy in the space and is
the obvious anchor to cite, but it is a taxonomy of *one* of our four families, not of all four.

### 0.2 Krakovna & Kumar (2019), *Classifying specification problems as variants of Goodhart's Law*
AI Alignment Forum, 2019-08-19.
https://www.alignmentforum.org/posts/yXPT4nr4as7JvxLQa/classifying-specification-problems-as-variants-of-goodhart-s
Maps DeepMind's Specification/Robustness/Assurance taxonomy onto Manheim–Garrabrant by
inserting intermediate specification levels: ideal → model → design → implementation →
revealed. Model-design gap ↔ Regressional; proxy-design gap ↔ Extremal; tampering gap ↔
Causal; implementation-to-reality gap ↔ robustness.
Covers: family 2, plus a useful "levels of specification" spine we could borrow.
Verdict: **SAME** for family 2. Notable because it is an explicit *unification of two
existing taxonomies* — precedent for the move we want to make, but still only within
proxy-divergence.

### 0.3 John, Caldwell, McCoy & Braganza (2024), *Dead rats, dopamine, performance metrics, and peacock tails: Proxy failure is an inherent risk in goal-oriented systems*
Behavioral and Brain Sciences 47:e67. doi:10.1017/S0140525X23002753
Target article (+20 peer commentaries) arguing "proxy failure" is one mechanism recurring
across economics, academia, machine learning, neuroscience and ecology. Framework is
regulator / agent / proxy: when a regulator incentivizes or selects on an imperfect proxy,
a pressure arises that makes the proxy a *worse* approximation of the goal over time.
Enumerates prerequisites (proxy exists; incentive/selection targets it; correlation is
imperfect) and constraints; absorbs Goodhart's law, Campbell's law, the cobra effect, the
McNamara fallacy, goal displacement, the "proxy treadmill."
Covers: family 2 again, but at maximum cross-domain generality.
Verdict: **SAME phenomenon, broader scope.** This is the most ambitious existing
cross-domain unification — and it is still *only family 2*. It explicitly does not treat
ceiling effects, noise floors, measurement cost, or objective disagreement. Strongest
evidence that our four-family unification is not yet taken.

### 0.4 Manheim (2019), *Multiparty Dynamics and Failure Modes for Machine Learning and AI*
arXiv:1810.10862; Big Data & Cognitive Computing 3(2):21.
Extends the Goodhart work to multi-agent settings. Categories: accidental steering,
coordination failures, adversarial misalignment, input spoofing and filtering, goal
co-option / direct hacking.
Covers: family 2 (tampered measurement, adversarial proxy gaming) and gestures at family 4
(conflicting objectives across parties).
Verdict: **SAME** for family 2; **ANALOGOUS** for family 4 (multi-agent, not
multi-stakeholder-values). Companion: Manheim (2018), *Building Less Flawed Metrics*, MPRA
Paper, Univ. Library of Munich — a prescriptive counterpart on how to design metrics that
resist those failures.

### 0.5 Chen, Wang & Qu (2026), *Recursive Self-Improvement in AI: From Bounded Self-Refinement to Autonomous Research Loops*
arXiv:2607.07663 (2026-07-08). Survey of 1,250 arXiv papers 2024–2026.
Two-dimensional taxonomy (what improves: behavior / policy / evaluator / research process ×
degree of loop closure), plus a **verification hierarchy** of self-evaluation signals ordered
strongest→weakest: formal verifiers → process reward models → judges & rubrics →
meta-evaluation → intrinsic self-assessment. Names the evaluation signal itself as the scarce
input to any improvement loop, and identifies self-confirming loops, model collapse and
diversity collapse as what happens when the hierarchy is violated. Explicitly separates
"bounded self-refinement (evaluable, already industrial)" from "open-ended RSI (not evaluable)."
Covers: cuts across families 1, 2 and 4 — it is the closest existing work to *our specific
framing* (automated loop, signal quality as the binding constraint).
Verdict: **SAME level of the stack**, but organized by *strength of verifier* rather than by
*mode of failure*. It answers "how good is the signal" not "what are the distinct ways it
can be bad." Complementary, and the most important paper to position against.

### 0.6 Reward-hacking survey: Wang et al. (2026), *Reward Hacking in the Era of Large Models: Mechanisms, Emergent Misalignment, Challenges*
arXiv:2604.13602 (2026-04-15).
Organizes reward hacking under a "Proxy Compression Hypothesis": objective compression →
optimization amplification → evaluator-policy co-adaptation. Manifestations split by regime
(RLHF / RLAIF / RLVR): verbosity bias, sycophancy, hallucinated justification, benchmark
overfitting, oversight manipulation.
Covers: family 2, with an explicit *dynamic* (co-adaptation) that our list underweights.
Verdict: **SAME** for family 2.

---

## Family 1 — Score can't move (ceiling / floor / no partial credit)

### 1.1 *When AI Benchmarks Plateau: A Systematic Study of Benchmark Saturation*
arXiv:2602.16763 (2026). (snippet)
Defines benchmark saturation as loss of discriminative power near a practical ceiling.
Of 60 benchmarks analyzed, 29 show high/very-high saturation. Saturation index rises with
benchmark age and falls with test-set size. Key framing: "saturation is not only a property
of the task distribution but a consequence of limited evaluation *resolution*" — top systems
get identical task-level outcomes while latent quality still differs.
Covers: our ceiling/saturation mode, exactly.
Verdict: **SAME**. Best existing citation for "score can't move — ceiling."

### 1.2 *Benchmark²: Systematic Evaluation of LLM Benchmarks*
arXiv:2601.03986 (2026). (snippet) Meta-evaluation of benchmarks as measuring instruments,
including discriminative power. Verdict: **SAME**, supporting.

### 1.3 *SEAL: Can Saturated Benchmarks Be Revived by LLM-as-a-Meta-Judge?*
arXiv:2605.30104 (2026). (snippet) Attempts to restore resolution above the ceiling by
re-scoring with a meta-judge. Verdict: **SAME**, mitigation-side.

### 1.4 Sparse-reward / hard-exploration literature (RL)
Canonical: Ecoffet et al., *Go-Explore: a New Approach for Hard-Exploration Problems*,
arXiv:1901.10995 (and Nature 2021). Also the reward-shaping line (Ng, Harada & Russell 1999
potential-based shaping; Eschmann 2021 *Reward Function Design in RL*).
"Sparse reward" = precise sequences of hundreds of actions between any non-zero signal;
"deceptive reward" = the signal actively points away from the global optimum.
Covers: our "floor" and "no partial credit" modes.
Verdict: **ANALOGOUS**, and arguably SAME with relabeling. The RL community's *sparse* is our
*no partial credit*; their *deceptive* is our family-2 proxy divergence expressed as a
landscape property. Strong prior art but framed as an algorithm problem (need better
exploration), not as a property that makes a task unsuitable for an automated loop.

### 1.5 Fitness-landscape pathologies (evolutionary computation)
- Beaudoin, Verel, Collard & Escazut (2006), *Deceptiveness and neutrality: the ND family of
  fitness landscapes*, GECCO '06. https://dl.acm.org/doi/10.1145/1143997.1144091
- Vanneschi, Tomassini et al., *Smoothness, Ruggedness and Neutrality of Fitness Landscapes:
  from Theory to Application*, Springer 2011.
- Smith, Husbands, Layzell & O'Shea (2002), *Fitness Landscapes and Evolvability*,
  Evolutionary Computation 10(1).
- Weise et al., the **W-Model** benchmark: tunable ruggedness, deceptiveness, epistasis,
  neutrality, multi-objectivity as separable, dialable layers.
Three canonical structural properties: **ruggedness**, **neutrality** (large plateaus where
mutations don't change fitness), **deceptiveness**.
Covers: neutral plateaus ↔ our "no partial credit / floor"; ruggedness ↔ our "noise swamps
signal" at the landscape level; deceptiveness ↔ family 2.
Verdict: **ANALOGOUS but the closest structural precedent for the *shape* of our taxonomy.**
The W-Model in particular is a taxonomy-as-generator: it enumerates independent pathologies
and lets you switch each on. That is the design pattern our 15 modes want. Crucially, EC
treats these as properties of a *fixed, honest* fitness function; it has no vocabulary for
"the fitness function itself is lying / is contested / costs money to query."

---

## Family 2 — Score moves but lies (proxy divergence, exploits, contamination, tampering)

### 2.1 Goodhart's law / Campbell's law (originals)
Campbell, D.T. (1976), *Assessing the Impact of Planned Social Change* — "The more any
quantitative social indicator is used for social decision-making, the more subject it will be
to corruption pressures and the more apt it will be to distort and corrupt the social
processes it is intended to monitor."
Verdict: **ANALOGOUS** (institutions, human agents), but it is the ancestral statement and
the reason "Goodhart" is the default umbrella word.

### 2.2 Krakovna et al., *Specification gaming: the flip side of AI ingenuity* (DeepMind, 2020)
https://deepmind.google/blog/specification-gaming-the-flip-side-of-ai-ingenuity/
Plus the public **specification-gaming examples spreadsheet** (~60 examples at publication,
now 100+). Canonical examples: Lego block flipped rather than stacked; CoastRunners boat
looping power-ups forever; CoinRun agents learning coin *location* not coin.
Covers: simulator exploits, proxy divergence.
Verdict: **SAME** phenomenon. But note: this is a *list*, not a taxonomy — it is deliberately
unstructured. Frequently miscited as a taxonomy.

### 2.3 Gao, Schulman & Hilton (2023), *Scaling Laws for Reward Model Overoptimization*
arXiv:2210.10760; ICML 2023.
Synthetic gold-vs-proxy reward setup; measures how far you can optimize a proxy before true
performance turns over, and shows the turnover point scales smoothly with reward-model size.
Covers: proxy divergence, quantitatively.
Verdict: **SAME**. This is the empirical backbone for "score moves but lies."
Follow-on: Rafailov et al. (NeurIPS 2024), *Scaling Laws for Reward Model Overoptimization
in Direct Alignment Algorithms*.

### 2.4 Karwowski, Hayman, Bai, Kiendlhofer, Griffin & Skalse (2024), *Goodhart's Law in Reinforcement Learning*
arXiv:2310.09144; ICLR 2024.
Quantifies the magnitude of Goodhart divergence in MDPs, gives a *geometric* explanation for
why it happens, and derives a provably-safe early-stopping rule with regret bounds.
Covers: proxy divergence.
Verdict: **SAME**, and the most formal treatment. Important because it implies the failure
mode is *predictable and boundable*, not just anecdotal.

### 2.5 Everitt, Hutter, Kumar & Krakovna (2021), *Reward tampering problems and solutions in reinforcement learning: a causal influence diagram perspective*
arXiv:1908.04734; Synthese 198.
Separates **reward-function tampering** (agent modifies the reward rule) from **RF-input
tampering** (agent feeds the reward function false observations — the disabled dirt sensor,
the spoofed GPS). Uses causal influence diagrams to read off, from the graph, whether an
agent has an instrumental incentive to tamper.
Covers: our "tampered measurement" mode, cleanly split in two.
Verdict: **SAME**. Our single "tampered measurement" mode should probably split along their
line — tampering with the *scorer* vs tampering with the *inputs to the scorer* are different
to detect and different to defend. Related: *REALab: An Embedded Perspective on Tampering*,
arXiv:2011.08820; and the Causal Incentives Working Group corpus (causalincentives.com),
incl. *Agent Incentives: A Causal Perspective*, arXiv:2102.01685.

### 2.6 Data contamination
- *A Taxonomy for Data Contamination in Large Language Models*, arXiv:2407.08716. Grades
  contamination severity from exposure to task meta-information up to exposure to labeled
  benchmark items. (snippet)
- *LLM Benchmark Datasets Should Be Contamination-Resistant*, arXiv:2605.19999 (2026).
  (snippet)
- Community index: github.com/lyy1994/awesome-data-contamination.
Covers: our contamination/memorization mode.
Verdict: **SAME**, and already has a real taxonomy of its own.

### 2.7 Singh et al. (2025), *The Leaderboard Illusion*
arXiv:2504.20879.
Chatbot Arena case study: undisclosed private variant testing (Meta 27 variants pre-Llama-4,
Google 10), score retraction rights, and heavily skewed data access (Google ~19.2%, OpenAI
~20.4% of all arena data vs 29.7% shared across 83 open-weight models). Extra arena data
yields up to 112% relative gain on the arena distribution — i.e. overfitting to the
measurement, not the capability.
Covers: contamination + tampered measurement, at the *ecosystem* level.
Verdict: **SAME phenomenon, institutional level.** Useful evidence that measurement gaming
happens even without an agent "cheating" — it emerges from selection over many attempts.

### 2.8 Reality gap / sim-to-real
- *The Reality Gap in Robotics: Challenges, Solutions, and Best Practices*, arXiv:2510.20808;
  Annual Review of Control, Robotics, and Autonomous Systems.
  Taxonomy of *solutions* split into **gap reduction** (system ID, learned residual models,
  real-to-sim) vs **gap overcoming** (domain randomization, adaptation, robust policies).
  Decomposes the gap itself into dynamics, perception/sensing, actuation/control, system design.
- Jakobi, Husbands & Harvey (1995), *Noise and the Reality Gap: The Use of Simulation in
  Evolutionary Robotics* — the origin; established that noise injection is what stops
  evolution from exploiting simulator artifacts.
- Koos, Mouret & Doncieux, *Crossing the Reality Gap in Evolutionary Robotics by Promoting
  Transferable Controllers*.
Key quote from the ER line: "the most efficient solutions in simulation often exploit
simulator artifacts."
Covers: our "simulator exploits" mode.
Verdict: **SAME**. And the reality-gap literature has the decomposition-by-subsystem that our
mode currently lacks.

### 2.9 Surrogate endpoint validity (medicine / biostatistics)
- Prentice, R.L. (1989), *Surrogate endpoints in clinical trials: definition and operational
  criteria*, Statistics in Medicine 8(4):431–440. The **Prentice criterion**: T ⊥ Y | S.
- Freedman et al. — "proportion explained."
- Buyse & Molenberghs — **trial-level vs individual-level** surrogacy; meta-analytic validation.
- Frangakis & Rubin — principal stratification; average causal necessity / sufficiency.
- *Novel Criteria to Exclude the Surrogate Paradox and Their Optimalities*, arXiv:1607.05454.
- *On the Individual Surrogate Paradox*, arXiv:1712.08732.
The **surrogate paradox**: a treatment improves the surrogate, the surrogate is positively
associated with the true outcome, and yet the treatment *harms* the true outcome.
Covers: proxy divergence — with a *formal validity criterion* rather than a failure list.
Verdict: **SAME phenomenon, ANALOGOUS level** (one-shot causal inference, not iterated
optimization). But this is the field that has thought hardest about *when a proxy is
licensed*, which is the constructive dual of our taxonomy. The trial-level vs individual-level
distinction is directly reusable for our "effects only visible in aggregate" mode (3.5).

### 2.10 Backtest overfitting / selection bias over many trials
- Bailey, Borwein, López de Prado & Zhu, *The Probability of Backtest Overfitting*
  (SSRN 2326253; J. Computational Finance). CSCV cross-validation estimate of PBO.
- Bailey & López de Prado, *The Deflated Sharpe Ratio: Correcting for Selection Bias,
  Backtest Overfitting and Non-Normality* (SSRN 2460551; J. Portfolio Management 2014).
- Bailey & López de Prado (2021), *How "backtest overfitting" in finance leads to false
  discoveries*, Significance 18(6).
Core result: the probability of selecting an overfit strategy **grows rapidly with the number
of trials**, and selected strategies systematically underperform the median trial
out-of-sample. DSR deflates a reported Sharpe by the number of trials attempted.
Covers: a mode we arguably *do not have* — **search-induced inflation**: the score is honest
per-query, but the act of running many optimization iterations and keeping the max
manufactures apparent gains.
Verdict: **SAME phenomenon, and the best-quantified version of it anywhere.** This is directly
about automated hill-climbing over a fixed evaluation set. Strong recommendation: add
"multiplicity / selection-under-search inflation" as an explicit 16th mode, and cite DSR as
the existing correction. Related: Manheim–Garrabrant's Regressional Goodhart is the same
effect stated statically; PBO/DSR states it as a function of *iteration count*, which is what
an autoresearch loop actually controls.

---

## Family 3 — Score exists but is unreadable (noise, delay, cost, aggregate-only)

### 3.1 Online controlled experiments: sensitivity and power
- Larsen, Stallrich, Sengupta, Deng, Kohavi & Stevens (2024), *Statistical Challenges in
  Online Controlled Experiments: A Review of A/B Testing Methodology*, The American
  Statistician 78(2). https://doi.org/10.1080/00031305.2023.2257237
- Deng, Xu, Kohavi & Walker (2013), *Improving the sensitivity of online controlled
  experiments by utilizing pre-experiment data* (CUPED), WSDM.
- Kohavi, Tang & Xu (2020), *Trustworthy Online Controlled Experiments*.
Sensitivity = f(variance, effect size, number of randomization units). Heavy-tailed metrics
need capping. Thousands of units minimum; smaller effects need many more.
Covers: our "noise swamps signal" and "effects only visible in aggregate" modes.
Verdict: **SAME phenomenon, ANALOGOUS level** (product experimentation, human users). The
transfer is real though: an autoresearch loop making a 0.3% improvement against an eval with
run-to-run σ of 1% is in exactly the CUPED situation, and variance reduction is the fix.

### 3.2 Athey, Chetty, Imbens & Kang (2019/2025), *The Surrogate Index: Combining Short-Term Proxies to Estimate Long-Term Treatment Effects More Rapidly and Precisely*
NBER WP 26463; Review of Economic Studies.
Builds a predicted long-term outcome from several short-term outcomes; under Prentice
surrogacy the ATE on the surrogate index equals the ATE on the long-term outcome. California
job-training case: 9-year employment impact estimable within 1.5 years, SEs cut 35%.
Covers: our **delayed outcomes** mode — and it is the *constructive answer*, not just a
diagnosis.
Verdict: **SAME phenomenon, ANALOGOUS level.** Directly applicable: if the true objective is
6 months out, build a surrogate index rather than declaring the gradient unusable.
Empirical check: *Evaluating the Surrogate Index as a Decision-Making Tool Using 200 A/B Tests
at Netflix*, arXiv:2311.11922.

### 3.3 *PROXIMA: A Reliability Scoring Framework for Proxy Metrics in Online Controlled Experiments*
arXiv:2604.14352 (2026). (snippet) Scores how trustworthy a proxy metric is before you let
decisions ride on it. Verdict: **SAME**, mitigation-side, and close to what we'd want as
tooling.

### 3.4 Expensive / budgeted black-box optimization
- Multi-fidelity and cost-aware Bayesian optimization: *Multi-Step Budgeted Bayesian
  Optimization with Unknown Evaluation Costs*, arXiv:2111.06537 (NeurIPS 2021).
- Fixed-budget best-arm identification / GP bandits: *Gaussian Process Bandits with
  Aggregated Feedback*, arXiv:2112.13029.
- Noisy global optimization with RBF surrogates (radial basis function methods).
Covers: our **cost-per-measurement** mode — treated as a resource-allocation problem with a
well-developed algorithmic answer, not as a pathology.
Verdict: **ANALOGOUS in framing, SAME in substance.** Notable asymmetry: the BO community
never calls this a "failure mode"; it calls it the *setting*. That is a real difference in
stance we should acknowledge — cost-per-measurement doesn't make a gradient unusable, it makes
it a budget problem.

### 3.5 Aggregate-only effects
Best existing handle is the **trial-level vs individual-level surrogacy** split from Buyse &
Molenberghs (see 2.9), plus *Evaluation of Individual and Trial Level Association Metrics in
the Validation of a Binary Surrogate Endpoint*, arXiv:2603.19403 (2026) (snippet), and
*Learning the Covariance of Treatment Effects Across Many Weak Experiments*, arXiv:2402.17637.
Verdict: **ANALOGOUS.** No one appears to name "the effect only exists in aggregate" as an
optimization-signal failure mode. Nearest named concept is the ecological/atomistic fallacy
pair. **This is one of our weakest-covered modes — likely genuinely novel framing.**

### 3.6 LLM-as-judge measurement noise
- *How to Correctly Report LLM-as-a-Judge Evaluations*, arXiv:2511.21140. (snippet) Noisy
  judgments induce bias in naive estimates; gives corrections.
- *Self-Preference Bias in LLM-as-a-Judge*, arXiv:2410.21819. Bias range −38% to +90% on
  ArenaHard.
- *A Single Character can Make or Break Your LLM Evals*, arXiv:2510.05152. (snippet)
- *A Unified Perturbation Framework for Analyzing Leaderboard Stability and Manipulation*,
  arXiv:2605.15761 (2026). (snippet) Prompt paraphrasing alone can reverse model rankings.
Covers: noise swamping signal, at the specific level our loops actually operate at.
Verdict: **SAME.** This is the most directly relevant body of work for "score exists but is
unreadable" in an LLM-agent loop.

---

## Family 4 — "Up" is undefined (no agreed measure, conflicting objectives, stakeholder disagreement, drift)

### 4.1 Jacobs & Wallach (2021), *Measurement and Fairness*
arXiv:1912.05511; ACM FAccT 2021, pp. 375–385.
Imports **measurement modeling** from the quantitative social sciences. Unobservable
theoretical constructs must be operationalized, and that operationalization can mismatch the
construct. Gives a fairness-oriented taxonomy of construct reliability and construct validity
with named sub-types: face, content, convergent, discriminant, predictive, hypothesis, and
**consequential** validity. Argues fairness is an *essentially contested construct* — apparent
disputes about operationalization are actually disputes about theory.
Covers: our "no agreed measure" and "stakeholder disagreement" modes.
Verdict: **SAME phenomenon, and the best existing vocabulary for family 4.** "Essentially
contested construct" is a better name than "stakeholder disagreement." Strong recommendation:
adopt the construct-validity vocabulary wholesale for family 4 rather than inventing terms.
See also: *Measurement as governance in and for responsible AI*, arXiv:2109.05658.

### 4.2 *Quantifying construct validity in large language model evaluations*
arXiv:2602.15532 (2026). (snippet) And *Measuring what Matters: Construct Validity in Large
Language Model Benchmarks*, arXiv:2511.04703 / OpenReview mdA5lVvNcU.
Verdict: **SAME** — Jacobs–Wallach machinery applied to LLM benchmarks specifically. This is
the live thread; family 4 is the one area where the literature has recently caught up.

### 4.3 Raji, Bender, Paullada, Denton & Hanna (2021), *AI and the Everything in the Whole Wide World Benchmark*
arXiv:2111.15366; NeurIPS Datasets & Benchmarks.
Argues that "general" benchmarks (ImageNet, GLUE) cannot bear the construct-validity weight
placed on them: task selection is arbitrary, coverage is not general, and the benchmark
becomes a stand-in for an anointed common problem it does not actually measure.
Covers: "no agreed measure" / construct invalidity of the target itself.
Verdict: **SAME**, at benchmark-design level.

### 4.4 Multi-objective alignment / preference aggregation
- Sorensen et al., *A Roadmap to Pluralistic Alignment* (ICML 2024) — steerable, distributional
  and overton pluralism. Ongoing venue: Pluralistic Alignment workshop (ICML 2026).
- *Self-Improvement Towards Pareto Optimality: Mitigating Preference Conflicts in
  Multi-Objective Alignment*, arXiv:2502.14354.
- *Multi-Objective Preference Optimization*, arXiv:2505.10892.
- *Reward-free Alignment for Conflicting Objectives*, arXiv:2602.02495 (2026). (snippet)
- Social-choice framing: alignment from diverse feedback as preference aggregation; nonlinear
  weighted p-means from social-choice axioms rather than linear scalarization. (CMU AI-SDM
  pluralistic alignment thread.)
Key technical point: linear aggregation is ill-suited to **conflicting gradients**;
helpfulness and harmlessness are often anti-correlated.
Covers: our "conflicting objectives" mode.
Verdict: **SAME.** "Conflicting gradients" is already the term of art (cf. PCGrad, gradient
surgery, in the MTL literature). Note: I did **not** find work explicitly deriving an
Arrow-style impossibility result for AI objective aggregation, despite the social-choice
framing — that connection is gestured at but not made rigorous. Possible gap.

### 4.5 Non-stationarity / drift
- *Optimization in dynamic environments: a survey on problems, methods and measures*, Soft
  Computing 15 (2011). doi:10.1007/s00500-010-0681-0
- Nguyen, Yang & Branke, *Evolutionary dynamic optimization: A survey of the state of the
  art*, Swarm and Evolutionary Computation 6 (2012).
- *Dynamic Combinatorial Optimization Problems: A Fitness Landscape Analysis*, Springer 2012.
- *Evolving Machine Learning in Non-Stationary Environments: A Unified Survey of Drift,
  Forgetting, and Adaptation*, arXiv:2505.17902.
Drift is already typed: sudden/abrupt, incremental, gradual, recurring. The DOP framing: once
the problem is time-varying the goal changes from *finding* the optimum to *tracking* it, and
converged populations cannot track.
Covers: our "non-stationary drift" mode.
Verdict: **SAME phenomenon, ANALOGOUS level** (EC/streaming ML rather than agentic loops), and
already better-typed than our single mode. Recommend importing the four drift types.

---

## Related: critiques of automated research loops specifically

### 5.1 Bisht, Kumar, Jablonka, Mausam & Krishnan (2026), *Agentic AI Scientists Are Not Built For Autonomous Scientific Discovery*
arXiv:2605.08956 (2026-05-09).
Four obstacles: (i) **problem selection driven by the McNamara fallacy** — the loop selects
problems that are measurable rather than important; (ii) missing tacit procedural and failure
knowledge; (iii) preference optimization compresses output diversity toward consensus;
(iv) benchmarks measure single-turn prediction and lack feedback from physical experiment back
to the model.
Covers: (i) is *our whole thesis, stated in one sentence*. (iii) is a mode we don't have —
diversity collapse under the loop.
Verdict: **SAME level of the stack.** The closest position paper to our motivation. Cite as
the statement of the problem we are taxonomizing.

### 5.2 METR (2024), *RE-Bench: Evaluating frontier AI R&D capabilities of language model agents against human experts*
arXiv:2411.15114; metr.org/AI_R_D_Evaluation_Report.pdf
Seven ML research-engineering environments vs 50+ human experts. Task-design principle stated
explicitly: every environment's objective is a *scalar the agent can query* — optimize runtime,
optimize loss, optimize benchmark score — and each agent gets "a way to score their progress."
Covers: nothing directly, but it is the clearest instance of the assumption we are
interrogating: RE-Bench is a set of tasks *pre-selected for having a clean gradient*.
Verdict: **ANALOGOUS/negative space.** Useful as evidence that the field has implicitly
selected for optimizable tasks without naming the selection criterion.

### 5.3 Lu, Lu, Lange, Foerster, Clune & Ha (2024), *The AI Scientist: Towards Fully Automated Open-Ended Scientific Discovery*
arXiv:2408.06292. The system whose LLM-reviewer-in-the-loop design is the canonical instance
of "optimize against a proxy judge." Verdict: **ANALOGOUS/negative space.**

### 5.4 Other 2026 autoresearch critiques (snippet, lower confidence)
- *NOVA: Fundamental Limits of Knowledge Discovery Through AI*, arXiv:2605.15219.
- *When Should an AI Scientist Stop? Verifiable Experiment Steering and Refusal for Autonomous
  Discovery*, arXiv:2606.07576.
- *Can AI Evaluate AI Scientists?*, arXiv:2607.28631.
- *Self-Improvements in Modern Agentic Systems: A Survey*, arXiv:2607.13104.
- *Who Grades the Grader? Co-Evolving Evaluation Metrics and Skills for Self-Improving LLM
  Agents*, arXiv:2607.12790.
- Frontiers in AI (2025), *AI, agentic models and lab automation for scientific discovery*:
  warns research agendas may "shift from curiosity-driven exploration toward problems that are
  computationally convenient or yield rapid performance gains," privileging machine-tractable
  inquiries. — Same observation as 5.1(i).

---

## Coverage map: our 15 modes vs existing names

| # | Our mode | Existing name(s) | Coverage |
|---|---|---|---|
| 1 | Ceiling / saturation | benchmark saturation; ceiling effect; loss of evaluation resolution | **Strong** (1.1–1.3) |
| 2 | Floor | sparse reward; hard-exploration | **Strong** (1.4) |
| 3 | No partial credit | binary/sparse reward; neutrality, neutral plateaus | **Strong** (1.4, 1.5) |
| 4 | Proxy divergence / Goodhart | Regressional+Extremal Goodhart; reward-model overoptimization; proxy failure | **Very strong** (0.1, 0.3, 2.3, 2.4) |
| 5 | Simulator exploits | specification gaming; reality gap; simulator-artifact exploitation | **Very strong** (2.2, 2.8) |
| 6 | Contamination / memorization | benchmark data contamination; leaderboard overfitting | **Very strong** (2.6, 2.7) |
| 7 | Tampered measurement | reward-function tampering vs RF-input tampering; wireheading; Adversarial/Causal Goodhart | **Very strong** (2.5) |
| 8 | Noise swamps signal | experiment sensitivity/power; judge noise; landscape ruggedness | **Strong** (3.1, 3.6) |
| 9 | Delayed outcomes | surrogate endpoints; surrogate index; long-term-effect estimation | **Very strong** (2.9, 3.2) |
| 10 | Cost per measurement | expensive black-box optimization; budgeted/multi-fidelity BO; fixed-budget BAI | **Strong, but not framed as failure** (3.4) |
| 11 | Effects only in aggregate | trial-level vs individual-level surrogacy (nearest) | **Weak — likely our most novel mode** (3.5) |
| 12 | No agreed measure | construct validity; essentially contested construct; McNamara fallacy | **Strong** (4.1–4.3) |
| 13 | Conflicting objectives | conflicting gradients; multi-objective alignment; Pareto/scalarization | **Strong** (4.4) |
| 14 | Stakeholder disagreement | pluralistic alignment; preference aggregation; annotator disagreement as signal not noise | **Strong** (4.4) |
| 15 | Non-stationary drift | dynamic optimization problems; concept drift (sudden/incremental/gradual/recurring) | **Strong, better-typed than ours** (4.5) |

### Modes the literature has that our 15 do not
- **Search-multiplicity inflation** — the score is honest per-query but selecting the max over
  N iterations manufactures gains (PBO / Deflated Sharpe Ratio, 2.10). Distinct from
  contamination and from regressional Goodhart-as-usually-stated because it is a function of
  *how many times the loop ran*.
- **Evaluator–policy co-adaptation** — the scorer moves in response to being optimized against
  (2.6, 5.4 "Who Grades the Grader"). Our list treats the scorer as static.
- **Diversity collapse / self-confirming loops** — the loop narrows its own search
  distribution, so the gradient stops being informative about the wider space (0.5, 5.1).
- **Problem-selection distortion** — the loop reshapes *which questions get asked* toward
  measurable ones (5.1, 5.4). This is the meta-level of our whole taxonomy.

---

## Synthesis

1. **No unified cross-domain taxonomy of all four families exists.** Nothing found spans
   "can't move / lies / unreadable / undefined" in one framework.
2. The most ambitious unification is **proxy failure** (John et al., BBS 2024) — genuinely
   cross-domain (econ, academia, ML, neuroscience, ecology) but confined to family 2.
3. Family 2 is **saturated** prior art: Manheim–Garrabrant is the canonical taxonomy,
   Krakovna–Kumar unifies it with DeepMind's SRA, Gao et al. and Karwowski et al. make it
   quantitative and boundable. We add nothing here; we should cite and move on.
4. Families 1, 3 and 4 each have strong literature, but in **three mutually non-citing fields**:
   EC/fitness landscapes (1), biostatistics + online experimentation + Bayesian optimization
   (3), measurement theory + social choice (4). The cross-field bridge is the contribution.
5. **Best-covered modes:** proxy divergence, simulator exploits, contamination, tampering,
   delayed outcomes, saturation. All have canonical names — use them, don't rename.
6. **Weakest-covered mode: "effects only visible in aggregate."** No one names it as an
   optimization-signal failure. Most likely genuinely novel.
7. **Cost-per-measurement** is well-solved but never framed as a *failure*; in BO it is simply
   the setting. Worth flagging that stance difference rather than claiming novelty.
8. Four modes are missing from our list and should be added: search-multiplicity inflation,
   evaluator–policy co-adaptation, diversity collapse, problem-selection distortion.
9. Two of our modes should be **split**, following existing distinctions: tampering →
   function-tampering vs input-tampering (Everitt); drift → sudden/incremental/gradual/recurring.
10. **Umbrella term: there is no standard one.** "Gradient failure" is unused in this sense
    (the only arXiv hits are literal-gradient papers). Candidates in descending order of
    existing currency: **proxy failure** (broadest existing, but family-2-flavored),
    **construct validity** (rigorous, but framed as a property of the measure, not of the
    loop), **specification problems** (DeepMind, AI-only), **optimizability** (no established
    usage — free to claim).
11. Recommendation: keep "gradient failure" as the coinage — the space is genuinely open — but
    position it explicitly as *the union of proxy failure, construct invalidity, and
    landscape pathology, evaluated from the perspective of an automated loop*.
12. Closest competitor to watch: Chen et al. 2026 (arXiv:2607.07663), which organizes the same
    territory by *verifier strength* rather than *failure mode*. Complementary, not duplicative.
13. Closest statement of our motivating problem: Bisht et al. 2026 (arXiv:2605.08956) —
    "problem selection is influenced by the McNamara fallacy."
14. Items catalogued in this sweep: **41** (grouped into 24 numbered entries).
15. Main risk to the contribution: family 2 is so well-trodden that a taxonomy that *looks*
    Goodhart-shaped will be read as derivative. Lead with families 1, 3 and 4.
