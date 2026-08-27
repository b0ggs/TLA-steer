# Literature Verification — Section 5 of `how-coding-agent-mds-are-used-research-landscape.md`

**Date:** 2026-08-25
**Verifier:** independent citation audit (web search + arXiv abstract/full-text retrieval)
**Target file:** `/Users/wade/Documents/MDs_EVAL/how-coding-agent-mds-are-used-research-landscape.md`
**Scope:** the seven studies in the Section 5 table, their supporting claims in Sections 2/3, and the References/footnotes block.

---

## Summary table

| # | Study (as cited in doc) | arXiv ID | Exists? | Classification |
|---|---|---|---|---|
| 1 | Agent READMEs | 2511.12884 | Yes | **VERIFIED-ACCURATE** (minor version caveat) |
| 2 | Evaluating `AGENTS.md` | 2602.11988 | Yes | **VERIFIED-ACCURATE** |
| 3 | Impact on Efficiency | 2601.20404 | Yes | **VERIFIED-ACCURATE** |
| 4 | Probe-and-Refine | 2606.20512 | Yes | **VERIFIED-ACCURATE** |
| 5 | Do Context Files Help? | 2607.27250 | Yes | **VERIFIED-ACCURATE** |
| 6 | Guardrails Beat Guidance | 2604.11088 | Yes | **VERIFIED-ACCURATE** (title is v1 title; retitled in v2) |
| 7 | Configuration Smells | 2606.15828 | Yes | **VERIFIED-ACCURATE** |

**Result: 7/7 real papers. 7/7 accurately summarized. 0 fabrications. 0 material misrepresentations.**

---

## 1. Agent READMEs

**Doc's claim (Sections 2 and 5):** Mined 2,303 context files from 1,925 repositories. Implementation details 69.9%, architecture 67.7%, build/run commands 62.3%. "Security and performance appeared in only 14.5% of files each." Files behave like evolving configuration, maintained by frequent small additions; described as "READMEs for agents."

**Real citation:**
- **Title:** Agent READMEs: An Empirical Study of Context Files for Agentic Coding
- **Authors:** Worawalan Chatlatanagulchai, Hao Li, Yutaro Kashiwa, Brittany Reid, Kundjanasith Thonglek, Pattara Leelaprute, Arnon Rungsawang, Bundit Manaskasemsak, Bram Adams, Ahmed E. Hassan, Hajimu Iida
- **arXiv:** 2511.12884 — https://arxiv.org/abs/2511.12884
- **Dates:** v1 17 Nov 2025; v2 9 Aug 2026

**What I found:** The v1 abstract matches the doc **verbatim on every number**: "build and run commands (62.3%), implementation details (69.9%), and architecture (67.7%) … security (14.5%) and performance (14.5%)." Corpus size 2,303 files / 1,925 repositories confirmed. The "not static documentation but complex, difficult-to-read artifacts that evolve like configuration code, maintained through frequent, small additions" framing is confirmed verbatim, as is the "READMEs for agents" phrase and the 16-instruction-type content analysis.

**Discrepancy (non-material):** The paper was revised on 9 Aug 2026. The **v2** abstract reports a partly different content taxonomy: test procedures 75.9%, implementation details 70.8%, architecture 68.1%, security 14.8%, performance 14.5%. Notably v2 adds a *test procedures* category at 75.9% — the single most common instruction type — which the doc does not mention, and it nudges security to 14.8% (so "14.5% each" is no longer exactly right).

The doc is dated 21 Aug 2026, twelve days after the v2 revision, so it is quoting a superseded version. This is a currency issue, not an accuracy issue: every number the doc states was correct as published in v1.

**Classification: VERIFIED-ACCURATE** — recommend refreshing to v2 figures and adding the test-procedures finding.

---

## 2. Evaluating `AGENTS.md`

**Doc's claim (Section 5):** Multiple agents and LLMs on SWE-bench and repositories with developer-committed files. "Context files tended to reduce success and raised cost by more than 20%; they increased exploration and were followed." Implication drawn: minimal non-standard requirements may be the useful core.

**Real citation:**
- **Title:** Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?
- **Authors:** Thibaud Gloaguen, Niels Mündler, Mark Müller, Veselin Raychev, Martin Vechev (ETH Zurich SRI Lab)
- **arXiv:** 2602.11988 — https://arxiv.org/abs/2602.11988
- **Date:** 12 Feb 2026. Also presented at the ICLR 2026 Workshop on Memory for LLM-Based Agentic Systems.

**What I found:** All four sub-claims check out, each against the paper's own wording.

- *Reduce success.* The paper's own abstract language is "context files tend to **reduce** task success rates compared to providing no repository context," with body text giving "the average resolution rate is reduced by 0.5% and 2% on average on SWE-bench Lite and AGENTbench, respectively." A later abstract revision softens this to "does not generally improve task success rates." The doc's "tended to reduce" therefore tracks the paper's phrasing exactly. The effect is small and applies to LLM-generated files; developer-provided files did better than LLM-generated ones and beat no-context for all agents except Claude Code.
- *Cost >20%.* Confirmed: "a cost increase of 20% and 23% on average," driven by 2.45 and 3.92 additional steps.
- *Increased exploration.* Confirmed: "they search more files (grep), read more files, and write more files," and run more tests. Reasoning tokens up 22% (GPT-5.2) and 14% (GPT-5.1 mini).
- *Were followed.* Confirmed: "instructions in the context files are well followed by coding agents," while repository overviews specifically are "not helpful."

The doc's implication — "minimal non-standard requirements may be the useful core" — is a fair restatement of the paper's own conclusion that context files "are useful for specifying non-standard coding practices" and that "developer-written context files should describe only minimal requirements."

Design description is accurate: two settings (SWE-bench tasks with LLM-generated files; a new AGENTbench collection of 138 real-world Python tasks from niche repositories with developer-committed files), across four agents and multiple LLMs.

**Classification: VERIFIED-ACCURATE.** Optional nuance the doc omits: the reduction is small in absolute terms, and developer-committed files fared better than LLM-generated ones — a distinction directly relevant to MD_EVAL, since competition submissions are agent-authored.

---

## 3. Impact on Efficiency

**Doc's claim (Section 5):** 10 repositories, 124 pull requests, with/without `AGENTS.md`. "Reported 28.64% lower median runtime and 16.58% lower output-token use with broadly comparable completion behavior."

**Real citation:**
- **Title:** On the Impact of AGENTS.md Files on the Efficiency of AI Coding Agents
- **Authors:** Jai Lal Lulla, Seyedmoein Mohsenimofidi, Matthias Galster, Jie M. Zhang, Sebastian Baltes, Christoph Treude
- **arXiv:** 2601.20404 — https://arxiv.org/abs/2601.20404
- **Date:** January 2026

**What I found:** Exact match on every figure. 10 repositories, 124 pull requests, wall-clock runtime and token usage measured. Presence of `AGENTS.md` associated with 28.64% lower median runtime and 16.58% lower output-token consumption, "while maintaining comparable task completion behavior." The paper's mechanism hypothesis — less exploratory navigation, fewer planning iterations, fewer repeated model requests — is consistent with the doc's framing.

**Note, not a discrepancy:** this is an observational association across PRs, not a randomized within-task A/B. The doc's own hedging ("Reported…", "Efficiency may improve even when correctness effects are unclear") is appropriately cautious. Worth flagging that this finding sits in tension with study #2, which found context files *increase* steps and cost — a tension the doc acknowledges in its "Why these results can all be true" subsection.

**Classification: VERIFIED-ACCURATE.**

---

## 4. Probe-and-Refine

**Doc's claim (Sections 3.4 and 5):** Iterative failure-derived guidance tuning. "33.0% resolve rate compared with 28.3% for the initial static knowledge base and 25.5% without guidance. The gain came mostly from producing more evaluable patches and reaching the correct files, not from improving the correctness of a patch once the agent had localized the work."

**Real citation:**
- **Title:** Probe-and-Refine Tuning of Repository Guidance for Coding Agents
- **Authors:** Asa Shepard, Jeannie Albrecht
- **arXiv:** 2606.20512 — https://arxiv.org/abs/2606.20512
- **Date:** 18 June 2026

**What I found:** Exact match. "33.0% mean resolve rate vs. 28.3% for the static knowledge base used to initialize it and 25.5% for an unguided baseline (p < 0.001 for both probe-and-refine contrasts)" on SWE-bench Verified.

The mechanism claim is also exact and is arguably the doc's best-supported sentence: "Refined guidance produces evaluable patches for 14.5 percentage points more instances while per-patch precision remains statistically constant (~59%, p = 0.119)." That is precisely "more evaluable patches and reaching the correct files, not improving correctness once localized."

Method description confirmed: synthetic bug-fix probes used to iteratively improve repository guidance via single-shot LLM calls.

**Classification: VERIFIED-ACCURATE.** The doc adds the 14.5pp coverage detail in prose but not the table; both are faithful.

---

## 5. Do Context Files Help?

**Doc's claim (Section 5):** Claude Code and Codex, 17 real tasks, 288 runs. "No measurable correctness effect; failures were often implementation skill, not missing repository knowledge."

**Real citation:**
- **Title:** Do Context Files Help Coding Agents? A Two-Agent Ablation Study on Real Repositories
- **Author:** Prakhar Khatri
- **arXiv:** 2607.27250 — https://arxiv.org/abs/2607.27250
- **Date:** 28 July 2026

**What I found:** Exact match on design. "Two frontier agents (Claude Code and Codex), 17 real tasks from 3 repositories (15 shared + 2 Codex-only), and 288 evaluated runs with gold-test evaluation." Main finding confirmed: "Context strategy does not measurably move correctness on either agent (bounded to <=10-15pp via equivalence testing)."

The doc's "no measurable correctness effect" is precise, and the equivalence-testing bound is the right way to read it — this is a bounded null, not proof of no effect. The doc's second clause ("failures were often implementation skill, not missing repository knowledge") is the paper's interpretation of its failure analysis rather than a headline abstract claim, but it is consistent with the abstract and with the doc's own hedged framing.

Also worth noting the doc correctly captures the "task difficulty is agent-specific" point, which is reflected in the paper's asymmetric task set (2 Codex-only tasks).

**Classification: VERIFIED-ACCURATE.** Caveat for downstream use: this is a small, single-author study — 17 tasks across 3 repositories is a narrow base, and the doc leans on it for a fairly strong claim in the executive summary.

---

## 6. Guardrails Beat Guidance

**Doc's claim (Section 5):** 679 rule files, 25,532 rules, over 5,000 Claude Code runs. "Rules improved a discriminative subset; random rules performed similarly to curated rules; negative constraints helped while positive directives often hurt."

**Real citation:**
- **Title (v1, as cited by the doc):** Do Agent Rules Shape or Distort? Guardrails Beat Guidance in Coding Agents
- **Title (v2):** Guardrails Beat Guidance: A Large-Scale Study of Rules, Skills, and Persistent Configuration for Coding Agents
- **Authors:** Xing Zhang, Guanghui Wang, Yanwei Cui, Wei Qiu, Ziyuan Li, Bing Zhu, Peiyang He
- **arXiv:** 2604.11088 — https://arxiv.org/abs/2604.11088
- **Dates:** v1 13 Apr 2026; v2 28 May 2026

**What I found:** Every number matches. 679 rule files containing 25,532 rules scraped from GitHub; over 5,000 agent runs of Claude Code with Claude Opus 4.6 on SWE-bench Verified.

- *Improved a discriminative subset:* confirmed — +13.8pp on a discriminative subset of SWE-bench Verified.
- *Random ≈ curated:* confirmed and stronger than the doc states — "random, shuffled, mismatched-domain, and unconverted-format rule files all match curated rules," which the authors read as context priming rather than rule content driving the benefit.
- *Negative constraints help, positive directives hurt:* confirmed — "negative constraints shape behavior while positive directives distort it"; individually beneficial rules were constraints ("do not refactor unrelated code"), harmful ones were positive prescriptions ("follow code style").

**Title discrepancy (non-material):** The doc cites the **v1** title, which was correct at v1 and still resolves to the same arXiv ID. The paper was retitled at v2 on 28 May 2026, roughly three months before the doc was written. Same issue class as study #1: the doc appears to have been assembled from a snapshot of arXiv metadata that predates the mid-2026 revisions of two of its sources.

**Classification: VERIFIED-ACCURATE** — recommend updating the footnote to the v2 title.

**Relevance flag for MD_EVAL:** this is the most consequential result in the table for the competition design. If random rule files match curated ones, a leaderboard that scores complete MD submissions may be partly measuring context priming rather than instruction quality. A random-rules or shuffled-rules control arm would be cheap insurance and would make the challenge's results far more defensible.

---

## 7. Configuration Smells

**Doc's claim (Sections 3.5 and 5):** Grey-literature review plus 100-repository sample. "91 of 100 sampled repositories exhibited at least one identified problem." Lint leakage 62%, context bloat 42%, skill leakage 35%, plus blind references, fossilized initialization output, and conflicting instructions.

**Real citation:**
- **Title:** Configuration Smells in AGENTS.md Files: Common Mistakes in Configuring Coding Agents
- **Authors:** Helio Victor F. dos Santos, Vitor Costa, Joao Eduardo Montandon, Luciana Lourdes Silva, Marco Tulio Valente
- **arXiv:** 2606.15828 — https://arxiv.org/abs/2606.15828
- **Date:** 14 June 2026

**What I found:** Everything checks out, including the "91 of 100" figure that does **not** appear in the abstract — the doc's author went past the abstract to get it. Paper body: "We detected at least one smell in 91 agent configuration files. Thus, only nine files were smell-free."

Method confirmed: grey literature review plus repository mining to derive a six-smell catalog with automated detection heuristics, then prevalence measured on 100 popular open-source repositories containing an `AGENTS.md` or `CLAUDE.md`.

Full prevalence table (the doc names the bottom three smells but gives no percentages — these are the missing numbers):

| Smell | Prevalence |
|---|---|
| Lint Leakage | 62% |
| Context Bloat | 42% |
| Skill Leakage | 35% |
| Conflicting Instructions | 28% |
| Init Fossilization | 24% |
| Blind References | 16% |

The doc's ordering of the unquantified three ("blind references, fossilized initialization output, and conflicting instructions") is not the prevalence order, but the doc does not claim it is.

The paper additionally reports that several smells frequently co-occur — particularly Context Bloat, Skill Leakage, and Conflicting Instructions — which the doc does not mention and which reinforces its Section 3.5 argument that files need linting and maintenance, not just generation.

**Classification: VERIFIED-ACCURATE.**

---

## Cross-cutting observations

**Footnote hygiene.** All seven arXiv IDs resolve to the correct papers. First authors in the footnotes are correct in all seven cases (Chatlatanagulchai, Gloaguen, Lulla, Shepard, Khatri, Zhang, dos Santos). Years are correct. The five-author list for Configuration Smells and the five-author list for Evaluating `AGENTS.md` are both complete and correctly ordered.

**One systematic weakness: version drift.** Two of seven citations (Agent READMEs, Guardrails) reflect pre-revision versions of papers that were updated before the doc was written — one with changed numbers and a new headline finding, one with a changed title. Nothing stated is false, but the doc is quoting stale snapshots. If this file is going to be cited in project decisions or shown externally, refresh both.

**Numbers were not invented.** Every specific figure the audit was asked to check — 28.64%, 16.58%, 33.0/28.3/25.5%, >20% cost, 679/25,532/5,000+, 91/100, 2,303/1,925, 62/42/35%, 17 tasks/288 runs — matches the source exactly. Several match verbatim down to the decimal, and the 91/100 and 14.5pp figures required reading past the abstract. This is a doc whose author actually opened the papers.

**Where the doc editorializes rather than misreports.** The "Implication" column in the Section 5 table is the doc's own interpretation, clearly labeled as such, and is reasonable in every row. The Section 5 preamble ("The studies disagree, but they are testing different files, tasks, agents, budgets, and outcomes") and the Evidence Note at the end of the file both correctly warn that these are new arXiv preprints rather than settled consensus.

**Two substantive gaps worth closing, neither an accuracy failure:**
1. The Evaluating `AGENTS.md` result that *developer-committed* files outperformed *LLM-generated* ones is omitted, and it bears directly on a competition that expects agent-authored submissions.
2. The Guardrails random-rules result deserves more weight than the table gives it. It is the strongest available warning that MD leaderboard rankings could reflect priming rather than content.

---

## Overall verdict

**Section 5 is trustworthy.** All seven cited studies are real, correctly attributed, and correctly identified by arXiv ID. Every quoted statistic reproduces its source accurately, in several cases verbatim to the decimal place, and two of the checked figures were only obtainable from the papers' bodies rather than their abstracts. There are no fabricated citations, no invented numbers, and no findings reversed or inflated in the retelling.

The only corrections needed are two version-drift fixes — refresh Agent READMEs to the 9 Aug 2026 v2 figures (test procedures 75.9% is a notable omission) and update the Guardrails footnote to its v2 title. Both are cosmetic relative to the doc's arguments.

**Confidence: high.** Verification rests on arXiv abstract and full-text retrieval for all seven papers, with independent corroboration from ETH SRI Lab, ResearchGate, Hugging Face, alphaXiv, and NASA ADS listings.

**Score: 7/7 verified accurate.**
