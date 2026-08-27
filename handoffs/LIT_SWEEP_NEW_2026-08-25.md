# Literature Sweep — New Items Not in the Prior Landscape Doc

**Date:** August 25, 2026
**Scope:** arXiv + general web, 2025–2026, emphasis on March–August 2026.
**Baseline excluded:** the seven studies already catalogued in `how-coding-agent-mds-are-used-research-landscape.md` §5 (Agent READMEs 2511.12884; Evaluating AGENTS.md 2602.11988; Efficiency 2601.20404; Probe-and-Refine 2606.20512; Do Context Files Help 2607.27250; Guardrails Beat Guidance 2604.11088; Configuration Smells 2606.15828), plus the vendor docs and the OpenAI harness-engineering post.

**Count:** 22 new items. 8 rated **high** relevance to MDs_EVAL, 9 **medium**, 5 **adjacent/context**.

Relevance ratings are mine, defined as: **high** = changes how we should design or score the challenge; **medium** = supplies method, metric, or corroborating evidence; **adjacent** = useful framing or background only.

---

## Theme 1 — Effectiveness of instruction/context files on real outcomes

### 1.1 Toward Instructions-as-Code: Understanding the Impact of Instruction Files on Agentic Pull Requests — **HIGH**

Ali Arabat, Mohammed Sayagh. arXiv:2606.13449, submitted June 11, 2026. Accepted at MSR 2026 (23rd International Conference on Mining Software Repositories).
https://arxiv.org/abs/2606.13449

Mines 15,549 agentic pull requests across 148 projects and compares each project against itself before and after an instruction file was introduced, on merge rate, code-change size/complexity, and merge effort. This is the largest natural-experiment-style test of instruction files on *merged* outcomes rather than benchmark pass rates.

**Key numbers:** 27.7% of projects raised merge rate by ≥20% after adding an instruction file; 26.35% of projects saw merge rate *decrease*. Similar bidirectional split for code-change and merge-effort metrics. Projects in the improved group had substantially longer files with more sections and sub-sections.

**Relevance:** The first strong evidence that the same intervention helps roughly as often as it hurts across real repositories, which is exactly the variance an MD competition is meant to resolve; also the only new datapoint suggesting *longer, more structured* files correlate with success, cutting against the "minimal file" reading of the prior doc.

### 1.2 SlopCodeBench: Benchmarking How Coding Agents Degrade Over Long-Horizon Iterative Tasks — **HIGH**

Gabriel Orlanski, Devjeet Roy, Alexander Yun, Changho Shin, Alex Gu, Albert Ge, Dyah Adila, Nicholas Roberts, Frederic Sala, Aws Albarghouthi. arXiv:2603.24755, submitted March 25, 2026 (v2 May 7, 2026).
https://arxiv.org/abs/2603.24755

36 problems with 196 checkpoints where agents must repeatedly extend their *own* prior solution, measuring structural erosion and redundancy accumulation rather than one-shot pass/fail. Includes an explicit arm testing whether quality guidance in the prompt changes degradation.

**Key numbers:** best agent solved only 14.8% of checkpoints, none end-to-end. Structural erosion increased in 77% of trajectories, redundant code in 75.5%. Agent code was 2.3x more verbose and had 2.0x more structural erosion than human open-source Python. **Explicit quality guidance cut initial verbosity and erosion by up to one-third but did not change the degradation rate.**

**Relevance:** A rare clean measurement that guidance changes the *level* of a quality metric without changing its *slope* — a candidate scoring dimension for MDs_EVAL beyond pass/fail, and a warning that single-shot tasks will miss the effect entirely.

### 1.3 Codified Context: Infrastructure for AI Agents in a Complex Codebase — **MEDIUM**

Aristidis Vasilopoulos. arXiv:2602.20478, submitted February 24, 2026.
https://arxiv.org/abs/2602.20478

Longitudinal single-project engineering report from building a 108,000-line C# distributed system with a three-layer context infrastructure: a "hot-memory constitution" (conventions, retrieval hooks, orchestration protocols), 19 specialized domain-expert subagents, and a "cold-memory" knowledge base of 34 on-demand specification documents. Reports infrastructure growth and interaction metrics over 283 development sessions plus four observational case studies.

**Key numbers:** 108 KLOC, 19 subagents, 34 cold-memory docs, 283 sessions.

**Relevance:** Concrete, quantified instance of the hot/cold split the prior doc theorizes about in §4 — useful as a reference architecture for what a competitive MD submission might look like if multi-file submissions are ever allowed.

### 1.4 Cheap Code, Costly Judgment: A Case Study on Governable Agentic Software Engineering — **MEDIUM**

James C. Davis, Paschal C. Amusuo, Tanmay Singla, Berk Çakar, Kirsten A. Davis. arXiv:2607.01087, submitted July 1, 2026 (v2 July 4).
https://arxiv.org/abs/2607.01087

A 12-week autoethnographic case study producing 420 KLOC of production code plus 1.16 MLOC of tests, lints, docs and tooling, documented in 88 contemporaneous field notes. Develops a middle-range theory of "governance conversion": recurring structural failures surface governance needs, which human judgment converts into durable mechanisms (tests, lints, instructions).

**Key numbers:** 12 weeks, 420 KLOC production, 1.16 MLOC support material, 88 field notes.

**Relevance:** Independent qualitative support for the failure-derived-guidance loop the project is pursuing, and for the prose-vs-mechanism allocation table in §4 of the prior doc.

### 1.5 Adoption and Impact of Command-Line AI Coding Agents (Microsoft rollout) — **ADJACENT**

Emerson Murphy-Hill, Jenna Butler, Alexandra Savelieva. arXiv:2607.01418, submitted July 1, 2026.
https://arxiv.org/abs/2607.01418

Observational study of tens of thousands of Microsoft engineers during the early-2026 Claude Code / Copilot CLI rollout. Adoption spread through peer social networks; retention tracked prior coding activity rather than demographics.

**Key numbers:** adopters merged ~24% more PRs than counterfactual, sustained across a four-month window.

**Relevance:** Baseline for the size of a *tool-level* effect, which usefully bounds how large an *instruction-file-level* effect could plausibly be.

---

## Theme 2 — Instruction-following and context-file compliance

### 2.1 Instruction Adherence in Coding Agent Configuration Files: A Factorial Study of Four File-Structure Variables — **HIGH**

Damon McMillan. arXiv:2605.10039, submitted May 11, 2026.
https://arxiv.org/abs/2605.10039

Fully crossed factorial experiment manipulating four structural properties of the configuration file (including file size and internal conflict) and measuring compliance with a single trivial, unambiguous target annotation across 1,650 Claude Code CLI sessions on two TypeScript codebases. Registered-style analysis with multiple-testing correction and Bayes factors.

**Key numbers:** 1,650 sessions, 16,050 function-level observations. **No detectable contrast** from any of the four structural variables or three two-way interactions after correction; Bayes factors 0.05–0.10 favouring the null for file size and internal conflict. But compliance decays *within* a session: OR = 0.944, about **5.6% lower odds of compliance per additional function generated**. Models: Sonnet 4.6 primarily, Opus 4.6 / 4.7 as comparison.

**Relevance:** The single most directly useful new result. It says file *formatting* variables are probably noise (do not score them), and that compliance is a function of position in the trajectory — meaning task length and ordering are confounds MDs_EVAL must control or randomize.

### 2.2 ContextCov: Deriving and Enforcing Executable Constraints from Agent Instruction Files — **HIGH**

Reshabh K Sharma. arXiv:2603.00822, submitted February 28, 2026 (v2 May 4, 2026).
https://arxiv.org/abs/2603.00822

Extracts natural-language constraints from AGENTS.md-style files and synthesizes enforcement checks in three families — static AST queries for code patterns, runtime shell shims that intercept prohibited commands, and architectural validators — then feeds violations back to the agent for self-correction before commit. Evaluated by extraction at corpus scale and by compliance on SWE-bench Lite.

**Key numbers:** 723 open-source repositories yielded >46,000 executable checks at 99.997% syntax validity. SWE-bench Lite constraint compliance **88.3% vs 67.0% and 50.3%** for baselines, at **3.4x lower feedback cost**, with functional correctness preserved.

**Relevance:** This is the operationalization of the prior doc's "what should be told vs. made mechanically impossible" question, with numbers attached — and it gives MDs_EVAL a ready method for automatically scoring *whether a submitted MD's own rules were obeyed*, independent of task pass/fail.

### 2.3 OctoBench: Benchmarking Scaffold-Aware Instruction Following in Repository-Grounded Agentic Coding — **HIGH**

Deming Ding, Shichun Liu, Enhui Yang, Jiahang Lin, Ziying Chen, Shihan Dou, Honglin Guo, Weiyu Cheng, Pengyu Zhao, Chengjun Xiao, Qunhong Zeng, Qi Zhang, Xuanjing Huang, Qidi Xu, Tao Gui. arXiv:2601.10343, submitted January 15, 2026 (v2 January 16).
https://arxiv.org/abs/2601.10343

Benchmarks whether agents follow *scaffold-specified* constraints while solving repository-grounded tasks, with heterogeneous constraints that persist across interactions. Ships an automated observation-and-scoring toolkit that captures full trajectories and runs fine-grained checks, deliberately separating "solved the task" from "obeyed the rules."

**Key numbers:** 34 environments, 217 tasks, three scaffold types, 7,098 objective checklist items, 8 models evaluated. Finds a systematic gap between task-solving ability and scaffold-aware compliance.

**Relevance:** The closest existing thing to an MD-compliance benchmark; its two-axis scoring (solve × comply) is a template MDs_EVAL could adopt directly, and its checklist-item design shows how to make compliance objectively gradable.

### 2.4 HANDBOOK.md: A Benchmark for Long-Context Agentic Instruction Following — **HIGH**

Liudas Panavas, Sebastian Minus, Bradley Monton, Derek Ray, Suhaas Garre, Sushant Mehta, Edwin Chen. arXiv:2607.25398, submitted July 28, 2026 (v3 August 3, 2026).
https://arxiv.org/abs/2607.25398

65 agentic tasks in self-contained mock company environments (email, chat, calendar, issue tracking, commerce over MCP) governed by expert-written handbooks of 20–124 pages across finance, medical billing, insurance, logistics and HR. Each task perturbs the base handbook's rules and thresholds to defeat memorization. Fully deterministic grading of both required and prohibited actions.

**Key numbers:** 65 tasks over 10 fictional companies, 824 programmatic criteria, 30 configurations of 20 models from 11 providers (July 2026 leaderboard). **Strongest model passes 36.2% of trials under strict grading; most frontier models below 25%.** Dominant failure mode: a plausible-but-unauthorized in-environment request overrides the standing written policy.

**Relevance:** Not coding-specific, but it is the strongest available evidence that standing written instructions are *weakly* followed by frontier models even when unambiguous — a ceiling constraint on how much any MD can be expected to do, and a strong argument for including prohibited-action checks in MDs_EVAL scoring.

### 2.5 A First Look at Coding Agents' Compliance with AI Contribution Rules in Open-Source Communities — **MEDIUM**

Wenhao Yang, Runzhi He, Minghui Zhou. arXiv:2607.26819, submitted July 29, 2026.
https://arxiv.org/abs/2607.26819

Builds RepoComplianceBench from real OSS AI-contribution policies (bans, mandatory disclosure, verification gates, human-escalation requirements) and tests whether four frontier models comply, under conditions with and without reminder prompts, quoted rules, and verifier feedback.

**Key numbers:** 106 issues from 49 repositories; 4 frontier models. Agents **almost never proactively retrieved** the contribution rules. Agents **never refused to contribute** in AI-banned repositories under any tested condition. Disclosure and verification compliance improved substantially with reminders, quoted rules, or verifier feedback.

**Relevance:** Isolates the first link in the prior doc's causal chain — instruction *available* vs. instruction *retrieved* — and shows retrieval is the failing step for repository-resident rules, which argues for testing MD delivery (always-on vs. discovered) as an explicit condition.

### 2.6 How Coding Agents Fail Their Users: A Large-Scale Analysis of Developer-Agent Misalignment in 20,574 Real-World Sessions — **MEDIUM**

Ningzhi Tang, Chaoran Chen, Gelei Xu, Yiyu Shi, Yu Huang, Collin McMillan, Tao Dong, Toby Jia-Jun Li. arXiv:2605.29442, submitted May 28, 2026.
https://arxiv.org/abs/2605.29442

Observational study of 20,574 real coding-agent sessions from 1,639 repositories across IDE and CLI workflows. Operationalizes misalignment as breakdowns visible through developer pushback and annotates each episode by form, cause, cost, and resolution, yielding seven recurring failure forms — including how agents read projects, follow rules, and bound their actions.

**Key numbers:** 20,574 sessions, 1,639 repositories, 7 failure forms. 90.50% of episodes impose effort/trust cost rather than irreversible damage; 91.49% of visible resolutions still require explicit user correction. Over time overall misalignment rates decline but **constraint violations and inaccurate self-reporting grow as a share**.

**Relevance:** Supplies an empirically grounded failure taxonomy for the "instruction content × failure mechanism" study in the prior doc's §7, and identifies rule-following and scope-bounding as the failure classes that are *not* improving on their own.

---

## Theme 3 — Efficiency, waste, and trajectory metrics as evaluation outcomes

### 3.1 Prompt-Induced Waste in Coding Agents: Reasoning, Effort, Harness Design, and End-to-End Cost — **HIGH**

Sarel Weinberger, Amir Hozez. arXiv:2608.01347, submitted August 2, 2026 (v5, August 24, 2026). *Preregistered.*
https://arxiv.org/abs/2608.01347

Preregistered controlled study — hypotheses and metric definitions frozen in a public repository before benchmark results were inspected — of how prompt wording, reasoning effort, and harness configuration change agent trajectories at fixed task definition. Defines efficiency as **cost per successful task induced by the trajectory**, treating token and cache counts as measurements rather than optimization targets.

**Key findings:** prompt wording alone changes reasoning and verification behaviour without changing the task; extra inference effort helps hard tasks but adds cost without proportional benefit elsewhere; efficiency gains are mediated by harness configuration, so harness must be held fixed or reported.

**Relevance:** The freshest and most methodologically careful item found (three weeks old). Its cost-per-success metric and preregistration pattern are directly adoptable for the MDs_EVAL leaderboard's cost column, and its harness-mediation finding justifies MDs_EVAL's fixed-harness design choice.

### 3.2 AI Agents Do Not Fail Alone: The Context Fails First — **HIGH**

Fouad Bousetouane. arXiv:2607.14275, submitted July 15, 2026.
https://arxiv.org/abs/2607.14275

Holds frontier LLM agents constant and varies only the operating context, scoring context quality on seven dimensions — role clarity, guardrail coverage, instruction consistency, tool schema quality, grounding sufficiency, injection hardening, token efficiency — via a multi-juror consensus rubric in an open-source harness (ProofAgent-Harness). Context scores are computed independently of behavioural metrics to keep validation non-circular.

**Key findings:** each context dimension predicts a specific behavioural outcome — grounding sufficiency → hallucination resistance; guardrail coverage → manipulation resistance; instruction consistency → instruction following; tool-schema quality → tool-use performance. Concludes context quality works as an auditable *preflight* signal.

**Relevance:** This is effectively a proposed rubric for scoring an instruction file *before* running it. If it replicates, MDs_EVAL could publish a static-score-vs-outcome correlation, which is a genuine research contribution and a fast feedback signal for competitors.

### 3.3 RigorBench: Benchmarking Engineering Process Discipline in Autonomous AI Coding Agents — **MEDIUM**

Meher Bhaskar Madiraju, Meher Sai Preetam Madiraju. arXiv:2606.22678, submitted June 21, 2026 (v2 June 29).
https://arxiv.org/abs/2606.22678

Scores process discipline rather than outcome correctness alone, across five pillars — Planning Fidelity, Verification Coverage, Recovery Efficiency, Abstention Quality, Atomic Transition Integrity — aggregated into a "RigorScore." Compares structured harnesses (which cite AGENTS.md as the configuration standard) against baseline assistants.

**Key numbers:** 30 tasks in five categories; structured discipline improved process quality scores by **41%** and downstream correctness by **17%**.

**Relevance:** Provides five named, defensible process metrics — Abstention Quality and Atomic Transition Integrity in particular map onto the "scope discipline" outcome MDs_EVAL wants; caveat: small task set (30) and self-defined composite score, so treat the 41%/17% as indicative only.

### 3.4 AgentLens: Production-Assessed Trajectory Reviews for Coding Agent Evaluation — **MEDIUM**

Andrey Podivilov, Vadim Lomshakov, Sergey Savin, Matvei Startsev, Roman Pozharskiy, Maksim Parshin, Sergey Nikolenko. arXiv:2607.06624, submitted July 7, 2026 (v2 July 14).
https://arxiv.org/abs/2607.06624

Open-source benchmark that scores the *whole trajectory* — instruction following, tool use, self-verification, error recovery, and communication — pairing formal verification where an objective check exists with LLM-written trajectory reviews and side-by-side comparisons, so each run yields a readable explanation of its score. Used in production for nightly regression detection on the authors' own agent.

**Relevance:** A working template for the "optional blinded quality review among mechanically passing patches" line item already in the prior doc's leaderboard plan, plus evidence that hybrid formal + LLM-review scoring survives production use.

### 3.5 Improving the Efficiency of LLM Agent Systems through Trajectory Reduction (AgentDiet) — **ADJACENT**

arXiv:2509.23586 (2025, revised into 2026).
https://arxiv.org/abs/2509.23586

Shows useless, redundant, and expired information is pervasive in agent trajectories and removes it during execution.

**Key numbers:** input tokens down 39.9%–59.7%, total cost down 21.1%–35.9%, performance unchanged, on two LLMs and two benchmarks.

**Relevance:** Establishes that a large fraction of agent context is measurably waste — the mechanism by which a good MD could plausibly reduce cost without changing correctness, matching the Lulla et al. efficiency result already in the prior doc.

---

## Theme 4 — Automatically optimized / failure-derived agent guidance

### 4.1 Agentic Harness Engineering: Observability-Driven Automatic Evolution of Coding-Agent Harnesses — **HIGH**

Jiahang Lin, Shichun Liu, Chengjun Pan, Lizhi Lin, Shihan Dou, Zhiheng Xi, Xuanjing Huang, Hang Yan, Zhenhua Han, Tao Gui, Yu-Gang Jiang. arXiv:2604.25850, submitted April 28, 2026 (v4 May 18, 2026).
https://arxiv.org/abs/2604.25850

Automatically evolves a coding agent's harness using three observability pillars: component observability (every editable harness component gets a file-level representation, so the action space is explicit and revertible), experience observability (millions of raw trajectory tokens distilled into a layered drill-down evidence corpus), and decision observability (every edit is paired with a self-declared prediction that is later verified).

**Key numbers:** Terminal-Bench 2 pass@1 **69.7% → 77.0%** over ten iterations, beating Codex-CLI (71.9%) and the ACE and TF-GRPO baselines. On SWE-bench-verified, top aggregate success with **12% fewer tokens** than baseline. Cross-family transfer of **+5.1 to +10.1 points** on Terminal-Bench 2. Ablation credits tools, middleware and long-term memory more than the system prompt.

**Relevance:** The strongest new result on automated optimization of agent configuration, and a direct blueprint for the Stage 4 MD-authoring loop — note especially the ablation finding that *prompt text* contributed least, which is a caution for a text-only MD competition.

### 4.2 Meta Context Engineering via Agentic Skill Evolution — **MEDIUM**

Haoran Ye, Xuning He, Vincent Arak, Haonan Dong, Guojie Song. arXiv:2601.21557, submitted January 29, 2026 (v2 February 11, 2026).
https://arxiv.org/abs/2601.21557

Bi-level framework: a meta-level agent refines *context-engineering skills* via "agentic crossover" — a deliberative search over the history of skills, their executions, and their evaluations — while a base-level agent executes those skills and optimizes context as adaptable files and code from training rollouts.

**Key numbers:** 5.6%–53.8% relative improvement over existing agentic context-engineering methods, **mean 16.9%** across five domains, offline and online. Reports better transferability and lower training/resource cost.

**Relevance:** Demonstrates that the "MD-authoring agent" role can itself be optimized and that its output transfers across tasks — the mechanism MDs_EVAL would need for an automated submission generator.

### 4.3 GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning — **MEDIUM**

Lakshya A. Agrawal et al. arXiv:2507.19457; **accepted at ICLR 2026 (Oral)**.
https://arxiv.org/abs/2507.19457

Reflective, language-feedback-driven evolution of system prompts and demonstrations in compound LLM systems, formalized over modules with per-module prompts. Outperforms GRPO and MIPROv2 and learns faster per rollout. Widely adopted downstream (open-source implementation at github.com/gepa-ai/gepa).

**Relevance:** The default off-the-shelf optimizer a serious competitor would point at an MDs_EVAL practice pack; the project should assume submissions may be GEPA-optimized against the public tasks and design sealed-task separation accordingly.

### 4.4 Automating SKILL.md Generation for Computer-Using Agents via Interaction Trajectory Mining — **MEDIUM (negative result)**

Yuexing Hao, Xiaomin Li. arXiv:2606.20363, submitted June 18, 2026.
https://arxiv.org/abs/2606.20363

Three-stage pipeline that segments GUI trajectories, clusters segments into candidate skills, and trains a skill-aware policy. Explicitly framed by the authors as a diagnostic study.

**Key numbers:** 5 of 8 clusters reached ≥0.95 purity against reference labels (so the mined skills are readable), but downstream gains were marginal — GRPO accuracy 18.5% → 20.5% on one benchmark, near-zero on another, and *underperforming simpler baselines*. Authors conclude the boundary detector, orderless segment representation, and offline reward model are insufficient.

**Relevance:** A useful counterweight to Probe-and-Refine: mining guidance from trajectories produces human-readable artifacts that do not necessarily improve the policy. Readability of an MD is not evidence of its value.

---

## Theme 5 — Delivery mechanism: always-on file vs. skill vs. retrieval

### 5.1 Is Progressive Disclosure All You Need for Long-Context Agents? — **HIGH**

Yifeng He, Yinzhe Zhao, Jicheng Wang, Hao Chen. arXiv:2607.17598, submitted July 20, 2026.
https://arxiv.org/abs/2607.17598

First controlled comparison of raw-document navigation, several Agent-Skills-style progressive-disclosure pack designs, and a classical hybrid retriever, across three agent harnesses and three model families on InfiniteBench. Packs share one chunk set so the only varying factor is *how the agent reaches a passage*.

**Key findings:** on a single document the gain depends heavily on the harness — large when the agent navigates raw documents poorly, near zero when a strong harness already chunks and retrieves on its own. Across many documents, raw navigation collapses while one-level progressive disclosure degrades more slowly and wins. **A second routing level adds nothing and sometimes hurts: one level is enough.** Progressive disclosure is a context-management tool, not an intelligence enhancer.

**Relevance:** Directly answers part of the prior doc's §4 allocation question — the always-on-vs-linked-docs choice only matters once content exceeds what the harness can navigate, and nesting beyond one level of indirection is wasted. Predicts elaborate multi-level MD submissions will not beat a flat one for a strong agent.

### 5.2 Harness Engineering for Agentic AI Coding Tools: An Exploratory Study — **MEDIUM**

Matthias Galster, Seyedmoein Mohsenimofidi, Jai Lal Lulla, Muhammad Auwal Abubakar, Christoph Treude, Sebastian Baltes. arXiv:2602.14690, submitted February 16, 2026 (last revised June 30, 2026). *Also circulated as "Configuring Agentic AI Coding Tools: An Exploratory Study."*
https://arxiv.org/abs/2602.14690

Taxonomizes eight configuration mechanisms spanning static context through executable and external integrations across Claude Code, Copilot, Cursor, Gemini and Codex, then measures their prevalence in 2,853 GitHub repositories.

**Key numbers:** 2,853 repositories, 8 mechanisms. Context files dominate and are frequently the *sole* mechanism in a repository; AGENTS.md functions as the interoperable cross-tool standard; Skills and Subagents are rare; configurations overwhelmingly rely on static instructions rather than executable scripts. Claude Code users employ the broadest mechanism range.

**Relevance:** Establishes the population baseline — evaluating a single static Markdown file is representative of what almost everyone actually deploys, which validates the MDs_EVAL submission format. (Note: shares an author, Lulla, with the efficiency paper already in the prior doc.)

### 5.3 Agent Skills for Large Language Models: Architecture, Acquisition, Security, and the Path Forward — **ADJACENT**

arXiv:2602.12430 (v4, 2026).
https://arxiv.org/abs/2602.12430

Survey of the Agent Skills abstraction — packaging, on-demand loading, acquisition, and security.

**Relevance:** Background for the skills-vs-instructions delivery axis; survey rather than evidence.

---

## Theme 6 — Benchmark and leaderboard design for agent configuration

### 6.1 Structural Quality Gaps in Practitioner AI Governance Prompts: An Empirical Study Using a Five-Principle Evaluation Framework — **MEDIUM**

Christo Zietsman. arXiv:2604.21090, submitted April 22, 2026.
https://arxiv.org/abs/2604.21090

Proposes a five-principle structural-completeness framework grounded in computability theory, proof theory, and Bayesian epistemology, and applies it to a corpus of 34 publicly available AGENTS.md governance files scraped from GitHub. Treats instruction files as executable specifications defining mandate, scope, and quality criteria.

**Key numbers:** 34 files; **37% of file-model pairs scored below the structural-completeness threshold**; the most frequently missing elements were data classification and assessment-rubric criteria. Identifies an "artefact classification gap" in the AGENTS.md convention itself.

**Relevance:** A second candidate static rubric for scoring a submitted MD before execution (compare 3.2); small corpus and heavy theoretical framing, so useful mainly as a source of rubric dimensions rather than as evidence.

### 6.2 Position: Coding Benchmarks Are Misaligned with Agentic Software Engineering — **MEDIUM**

Maria I. Gorinova, Macey Baker, Amy Heineike, Maksim Shaposhnikov, Rob Willoughby, Dru Knox. arXiv:2606.17799, submitted June 16, 2026 (v2 July 18).
https://arxiv.org/abs/2606.17799

Position paper arguing that current benchmarks collapse model, harness, and environment into one end-to-end score against a single reference solution, provide no component-level signal for iteration, and penalize functionally equivalent alternative solutions. Notes that individual non-model components can produce gains equivalent to a model-generation gap.

**Relevance:** Makes the explicit argument that MDs_EVAL is built on — that a configuration component deserves its own isolated evaluation — and is a citable framing for why an instruction-file leaderboard is a distinct contribution rather than a SWE-bench variant.

### 6.3 Beyond Static Leaderboards: Predictive Validity for the Evaluation of LLM Agents — **MEDIUM**

arXiv:2606.19704, June 2026.
https://arxiv.org/abs/2606.19704v1

Argues leaderboard rank should be validated by whether it predicts downstream deployment performance rather than treated as an end in itself.

**Relevance:** Directly bears on the MDs_EVAL claim that a winning MD generalizes to fresh sealed work; supplies the vocabulary (predictive validity) for the sealed-task rationale in §8 of the prior doc.

### 6.4 AgentAtlas: Beyond Outcome Leaderboards for LLM Agents — **MEDIUM**

arXiv:2605.20530, May 2026.
https://arxiv.org/abs/2605.20530

Proposes multi-dimensional agent profiling in place of single-number outcome leaderboards.

**Relevance:** Supports reporting MDs_EVAL results as a profile (resolution, reliability, regressions, cost, scope violations) rather than one score.

---

## Theme 7 — Adjacent: instruction files as an attack surface, and practitioner tooling

### 7.1 PhantomSkill: Malicious Code Injection in Agent Skill Ecosystems — **ADJACENT**

arXiv:2606.19191, June 2026. https://arxiv.org/abs/2606.19191

Malicious behaviour carried by executable skill *resources* rather than by textual instructions — a different threat model from classic prompt injection.

### 7.2 Agent Data Injection Attacks are Realistic Threats to AI Agents — **ADJACENT**

arXiv:2607.05120, July 2026. https://arxiv.org/abs/2607.05120

**Relevance of 7.1–7.2:** Both bear on open question 9 in the prior doc (instruction files as a supply-chain surface). If MDs_EVAL ever accepts third-party submissions that ship alongside executable content, this is the relevant threat literature.

### 7.3 Practitioner tooling — **ADJACENT**

- **AgentLint** (https://www.agentlint.app/) — commercial linter for the agent-harness layer, advertising 33 "evidence-backed" checks for AGENTS.md / CLAUDE.md. Vendor claims, unverified.
- **"Code quality in agentic software engineering," evidence-led report v1.24**, Peter Roelants, evidence through August 14, 2026 (https://gist.github.com/peterroelants/69029d4100a99e22dbb7df60a14c286b) — continuously updated practitioner literature review on maintainability, measurement, and verification in agentic SE. Useful as a cross-check on this sweep's coverage.
- **Self-improving CLAUDE.md** posts (Martin Alderson; addyosmani.com "Self-Improving Coding Agents"; jngiam) — the practitioner version of the Probe-and-Refine loop, all anecdotal, none controlled. Worth citing only as evidence that the practice exists in the wild.

---

## What's changed since the prior doc

The prior doc's central tension — does a repository instruction file help, hurt, or do nothing — has not been resolved, but the field has moved past asking it. Three shifts stand out. First, the outcome has moved off benchmark pass rate: Arabat & Sayagh (§1.1) tested 15,549 real agentic PRs and found merge rates rose ≥20% in 27.7% of projects and *fell* in 26.35%, which recasts the question from "does it work" to "why does the same intervention split roughly evenly." Second, the field has separated *solving* from *complying*: OctoBench, HANDBOOK.md, and RepoComplianceBench (§2.3–2.5) all now score rule adherence as its own axis, and the picture is bleak — the best model passes 36.2% of HANDBOOK.md trials, agents almost never retrieve repository rules on their own, and they never once honored an AI-contribution ban. That means the prior doc's causal chain now has measured breakpoints, and the break is early, at retrieval and adherence, not at comprehension. Third, two results directly constrain how MDs_EVAL should be designed: McMillan (§2.1) shows across 1,650 sessions that file *structure* variables produce no detectable effect while compliance decays ~5.6% per generated function, so trajectory position is a confound that must be controlled; and He et al. (§5.1) show that one level of progressive disclosure is enough and that a strong harness erases the benefit of clever context packaging entirely.

Two genuinely new capabilities appeared that the prior doc could not have covered. ContextCov (§2.2) converts prose instructions into executable checks and lifts constraint compliance from 50–67% to 88.3% — the first quantified answer to the prior doc's "tell vs. enforce" allocation table, and a ready-made way for MDs_EVAL to score whether a submission's own rules were kept. And Agentic Harness Engineering (§4.1) pushes Terminal-Bench 2 from 69.7% to 77.0% by automatically evolving agent configuration, but its ablation credits tools, middleware, and memory over the system prompt — the single most important caution for a text-only MD competition. Finally, the measurement vocabulary has matured: cost-per-successful-task (§3.1, preregistered, three weeks old), trajectory review (§3.4), process-discipline pillars (§3.3), and static context-quality rubrics that predict behaviour before a run (§3.2, §6.1). MDs_EVAL now has both the metrics and the framing arguments (§6.2, §6.3) it needs to position an instruction-file leaderboard as a distinct contribution rather than a SWE-bench variant.
