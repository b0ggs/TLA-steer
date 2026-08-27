# How Coding-Agent MDs Are Actually Used

## Research landscape, practitioner patterns, and implications for MD_EVAL

**Date:** August 21, 2026  
**Purpose:** Preserve the research discussed in the MD_EVAL conversation about how developers use `AGENTS.md`, `CLAUDE.md`, rules, skills, and related agent-configuration mechanisms. This document supplements the broader project-state memo; it is not a replacement roadmap.

---

## Executive answer

Developers do not use one universal kind of “MD.” They use a layered **instruction system** around a coding agent:

- repository-wide Markdown loaded on every task;
- nested or path-specific instructions;
- linked documentation and repository maps;
- on-demand skills and reusable prompt files;
- custom agent roles and workflow instructions;
- tests, linters, hooks, permissions, and sandboxes that enforce rules mechanically;
- feedback loops that update the instructions or tooling after recurring failures.

The academic evidence is mixed. Some studies find that repository context files increase exploration and cost without improving correctness. Others find efficiency gains, gains from failure-refined guidance, or gains from negative constraints. Another controlled study finds no measurable correctness effect because the agents’ failures were implementation failures rather than missing repository knowledge. The consistent conclusion is not “MDs work” or “MDs do not work.” It is:

> **The effect depends on what information is supplied, how it is delivered, which failure it addresses, the agent and budget, and whether the requirement belongs in prose at all.**

For MD_EVAL, this supports a challenge in which a participant—or an authoring agent acting for the participant—inspects a public repository and writes a repository-specific instruction file. The fixed coding agent then receives that file while solving sealed repository tasks. The competition evaluates the complete artifact as deployed, while the research program can later study which components caused the effect.

---

## 1. What counts as an “MD” in practice

The term “MD” is convenient but incomplete. Current coding-agent products expose several different customization channels.

### 1.1 Always-on repository instructions

These are files such as:

- `AGENTS.md`;
- `CLAUDE.md`;
- `.github/copilot-instructions.md`;
- Cursor project rules configured to apply to every task.

They provide persistent context that the harness loads automatically. Teams use them to avoid repeating the same project-specific information in every prompt.

### 1.2 Scoped and nested instructions

Instructions can apply only to a directory, file type, or subsystem.

- GitHub Copilot supports repository-wide instructions, path-specific `*.instructions.md` files, and multiple `AGENTS.md` files, with the nearest relevant agent file taking precedence.[^github-instructions]
- Claude Code discovers nested `CLAUDE.md` files and brings them into context when the agent works in the relevant subtree.[^anthropic-memory]
- Cursor project rules can be attached by file-pattern, invoked manually, or included when the agent judges them relevant.[^cursor-rules]

This is important because a rule for database migrations or Solidity contracts may be useful in one area and pure context noise everywhere else.

### 1.3 Linked knowledge and progressive disclosure

An instruction file can be a map rather than an encyclopedia. It tells the agent where authoritative information lives and when to consult it.

OpenAI’s account of an agent-first codebase reports that a monolithic `AGENTS.md` became stale, crowded the context, and was difficult to verify.[^openai-harness] The team replaced it with a short map into a structured, versioned documentation system containing architecture, design, reliability, security, product specifications, execution plans, and technical-debt records. The repository also uses mechanical checks and a recurring documentation-maintenance agent.

Claude Code supports imports from a `CLAUDE.md`, allowing the root file to point to narrower project or personal instruction files.[^anthropic-memory] GitHub Copilot CLI similarly supports references from instruction files to other repository files.

### 1.4 On-demand skills and reusable prompts

Specialized knowledge does not have to be loaded into every coding task.

- Cursor skills can be invoked manually or selected by the agent. Cursor also supports plugins that package rules, skills, custom agents, commands, MCP servers, and hooks.[^cursor-skills]
- GitHub Copilot distinguishes always-on custom instructions from prompt files that a user invokes for a particular interaction and from custom agents with specialist instructions and tool restrictions.

This creates a meaningful distinction between:

- permanent context needed on nearly every task;
- specialized procedures needed only for a class of work;
- one-off task prompts.

### 1.5 Personal, team, and project memory

Claude Code distinguishes project memory, user memory, and nested project memory. Cursor distinguishes user, project, and team rules. GitHub Copilot supports personal, repository, and organization-level customization.

These layers solve different problems:

- personal preferences should not necessarily be committed to the repository;
- team standards should be shared;
- subsystem-specific knowledge should be scoped;
- organization policy may need to override or supplement repository guidance.

### 1.6 Workflow and role instructions

Some files do more than describe a repository. They define how an agent should work:

- inspect before editing;
- reproduce a bug;
- make the smallest complete change;
- run a particular validation sequence;
- use worktrees or atomic commits;
- request review;
- continue until checks pass;
- stop and ask for clarification under specified conditions;
- create a particular handoff artifact.

Your complete `CODER.md` belongs largely in this category. Its expected value depends on the surrounding workflow actually providing worktrees, issue contracts, status files, reviewers, handoffs, and publication authority.

### 1.7 Mechanical controls around the prose

Practitioners increasingly distinguish between what the agent should be **told** and what the system should **enforce**.

Examples include:

- tests and static analysis for correctness requirements;
- formatters and linters for deterministic style;
- hooks for required workflow events;
- filesystem restrictions for edit boundaries;
- network allowlists and credential isolation;
- CI checks for generated files, documentation freshness, or architectural dependencies;
- review loops implemented by the harness.

Anthropic’s security engineering emphasizes filesystem and network isolation rather than relying solely on probabilistic compliance.[^anthropic-sandbox] OpenAI’s harness-engineering account similarly combines a small instruction map with tests, custom linting, isolated worktrees, skills, agent reviews, and repository-visible logs and metrics.

---

## 2. What developers put in these files

The largest empirical study located for this review analyzed **2,303 context files from 1,925 repositories**. It found that the files behave more like evolving configuration than static documentation. Developers most often supplied functional context:

- implementation details: 69.9%;
- architecture: 67.7%;
- build and run commands: 62.3%.

Security and performance appeared in only 14.5% of files each. The files tended to grow through frequent small additions, with less evidence of systematic removal. The study describes them as “READMEs for agents,” but their maintenance pattern resembles configuration code.[^agent-readmes]

This suggests that current practice is primarily concerned with making agents **functional inside the repository** rather than proving that their output is secure, performant, or optimally maintained.

### Common content categories

| Category | Typical content |
|---|---|
| Repository map | Important packages, entry points, source-of-truth files, generated directories |
| Commands | Setup, build, tests, linting, code generation, local services |
| Implementation conventions | Preferred APIs, layering, naming, data boundaries, error handling |
| Architecture | Package boundaries, dependency directions, intentional patterns |
| Workflow | Reproduce, plan, implement, verify, review, commit, hand off |
| Scope and guardrails | Do not refactor unrelated code, do not edit generated output, avoid new dependencies |
| Role definition | Coder, reviewer, researcher, security auditor, release agent |
| External tools | GitHub, issue trackers, observability, MCP servers, deployment systems |
| Non-functional requirements | Security, performance, reliability, maintainability—currently less common |

---

## 3. How people create and maintain the files

### 3.1 Human-authored from experience

A developer writes the initial file from their knowledge of the repository and adds instructions after recurring mistakes. This is intuitive but vulnerable to omissions, bloat, stale rules, and undocumented rationale.

### 3.2 Agent-generated from repository inspection

This is already a normal product workflow, not a hypothetical MD_EVAL invention.

- OpenAI reports that Codex wrote the initial `AGENTS.md` for its agent-first repository.
- Claude Code provides an initialization workflow for creating a `CLAUDE.md` from the codebase.
- Cursor includes commands for creating rules and skills.

This directly supports the proposed competition model: a participant can use an agent to inspect the public repository and draft the candidate MD.

### 3.3 Generated from templates or generic recommendations

An LLM can create a conventional file containing project overview, commands, style, architecture, and testing guidance. Controlled research warns that these files often restate information already available and can increase cost without improving outcomes.

### 3.4 Refined from observed failures

Probe-and-Refine begins with repository guidance, runs synthetic bug-fix probes, diagnoses where agents fail, and edits the guidance. In its reported experiments, refined guidance achieved a 33.0% resolve rate compared with 28.3% for the initial static knowledge base and 25.5% without guidance. The gain came mostly from producing more evaluable patches and reaching the correct files, not from improving the correctness of a patch once the agent had localized the work.[^probe-refine]

This is highly relevant to the eventual MD optimization loop, but it is not necessary for the first public challenge. Competitors can choose their own authoring process.

### 3.5 Maintained as a living configuration artifact

The configuration-smells study found that 91 of 100 sampled repositories exhibited at least one identified problem. The most frequent were:

- **Lint leakage:** 62%;
- **Context bloat:** 42%;
- **Skill leakage:** 35%;
- plus blind references, fossilized initialization output, and conflicting instructions.[^config-smells]

This suggests that authoring is only half the problem. Teams also need methods for testing, versioning, reviewing, explaining, and deleting instructions.

---

## 4. What belongs in the MD, and what belongs elsewhere?

This was one of the important tables from the earlier discussion.

| Requirement or knowledge | Plausible best representation | Why |
|---|---|---|
| Unusual build or test command used across the repository | Short root instruction | Frequently needed and difficult to infer reliably |
| A subsystem follows a different convention | Nested or path-specific instruction | Avoids burdening unrelated tasks |
| Rare release, migration, or incident-response procedure | On-demand skill or prompt file | Specialized and expensive to load every time |
| Repository architecture and source-of-truth locations | Short map with links to maintained docs | Supports navigation without turning the MD into an encyclopedia |
| “Never edit this generated file directly” | Instruction plus generator check or hook | Text explains; tooling catches violations |
| Formatting and import order | Formatter or linter | Deterministic enforcement is cheaper and more reliable |
| Every public API must satisfy a validation invariant | Tests or static analysis, with rationale in docs | A hard requirement should not depend only on compliance |
| Continue until reviews and CI pass | Harness loop | This is execution control, not merely repository knowledge |
| Do not access credentials or arbitrary networks | Sandbox and permission boundary | Safety-critical restriction needs mechanical containment |
| Why a rule exists and when it can be removed | Versioned documentation or instruction metadata | Prevents stale rules from becoming permanent folklore |
| Personal style preference | User-level instruction | Should not necessarily govern the whole team |
| Organization security policy | Organization-level instruction plus enforced controls | Must apply consistently across repositories |

The central allocation question is:

> **What should be told to the agent, what should be shown or retrieved when relevant, and what should be made mechanically impossible to violate?**

---

## 5. What controlled research says about effectiveness

The studies disagree, but they are testing different files, tasks, agents, budgets, and outcomes.

| Study | Design | Main reported finding | Implication |
|---|---|---|---|
| **Agent READMEs** (2025/2026)[^agent-readmes] | Mined 2,303 files from 1,925 repositories | Files are living configuration; developers emphasize commands, implementation, and architecture; security and performance are rare | Establishes what people actually write, not whether it works |
| **Evaluating `AGENTS.md`** (2026)[^agents-eval] | Multiple agents and LLMs on SWE-bench and repositories with developer files | Context files tended to reduce success and raised cost by more than 20%; they increased exploration and were followed | More instruction is not automatically better; minimal non-standard requirements may be the useful core |
| **Impact on Efficiency** (2026)[^efficiency] | 10 repositories and 124 pull requests, with/without `AGENTS.md` | Reported 28.64% lower median runtime and 16.58% lower output-token use with broadly comparable completion behavior | Efficiency may improve even when correctness effects are unclear |
| **Probe-and-Refine** (2026)[^probe-refine] | Iterative failure-derived guidance tuning | 33.0% resolution vs. 28.3% static guidance and 25.5% unguided; improved coverage/localization | How guidance is produced can be decisive |
| **Do Context Files Help?** (2026)[^context-ablation] | Claude Code and Codex, 17 real tasks, 288 runs | No measurable correctness effect; failures were often implementation skill, not missing repository knowledge | Instructions cannot repair every failure; task difficulty is agent-specific |
| **Guardrails Beat Guidance** (2026)[^guardrails] | 679 rule files, 25,532 rules, over 5,000 Claude Code runs | Rules improved a discriminative subset; random rules performed similarly to curated rules; negative constraints helped while positive directives often hurt | Rule polarity, priming, and interactions may matter more than apparent expertise |
| **Configuration Smells** (2026)[^config-smells] | Grey-literature review and 100-repository sample | Bloat, lint leakage, skill leakage, blind references, fossilization, and conflicts were widespread | Files need maintenance and linting, not just initial generation |

### Why these results can all be true

1. **Different failure mechanisms:** Missing a test command can be fixed by guidance; weak feature design may not be.
2. **Different delivery:** Always-loaded text, nested rules, retrieval, and skills consume different amounts of context.
3. **Different budgets:** Guidance may save exploration in one setting and create unnecessary work in another.
4. **Different agents:** A task can be borderline for one model and trivial or impossible for another.
5. **Different outcomes:** Correctness, runtime, token cost, scope discipline, review burden, and security are not interchangeable.
6. **Different files:** A repository map, a generic style guide, a workflow role, and a negative guardrail are different interventions even when all are Markdown.

---

## 6. The broader research landscape

The correct research object is not merely “the MD.” It is the **instruction and control system** surrounding the agent.

### Major open questions

1. Which agent failure modes can repository instructions actually prevent?
2. What information should be always present, path-scoped, retrieved, or loaded as a skill?
3. What belongs in prose versus tests, hooks, permissions, or harness logic?
4. Should guidance be human-written, repository-generated, or refined from failures?
5. How do files become stale, conflicting, or bloated, and how should instructions be removed?
6. How do effects vary by model, reasoning effort, step budget, repository, and task class?
7. Does the full workflow improve merged work, not merely isolated patch success?
8. What happens to human review time, CI success, code churn, regressions, and cost?
9. Can repository instructions or skills become a prompt-injection and supply-chain attack surface?
10. Does the agent retrieve, understand, follow, and verify an instruction—or merely have access to it?

A useful causal chain is:

```text
instruction available
    → instruction loaded or retrieved
    → instruction understood
    → behavior changed
    → task outcome or cost changed
```

A final pass/fail score does not reveal where that chain broke, although pass/fail should remain the primary correctness outcome for a competition.

---

## 7. Research options for MD_EVAL

This is the other major table from the earlier discussion.

| Possible study | Scientific value | Practitioner value | Fit with current MD_EVAL infrastructure |
|---|---:|---:|---:|
| **Compare complete repository-specific MD submissions on sealed tasks** | High | Very high | **Very high; this is the selected challenge direction** |
| **Instruction content × failure mechanism** | Very high | Very high | High after useful failures are available |
| **Same content as root MD, scoped rule, skill, retrieval, or executable check** | Very high | Very high | Medium; requires additional delivery adapters |
| **Human-authored vs. agent-generated vs. failure-refined guidance** | High | High | High; authoring process can initially remain outside the evaluator |
| **Instruction staleness, conflicts, rationale, and removal** | High | High | Medium |
| **Model and resource-budget interaction** | High | Medium–high | High; runner already records model and cost conditions |
| **Full `CODER.md` workflow in a persistent matching harness** | High | Very high | Low under the disposable single-agent runner; requires a later harness track |
| **Human review, merge time, CI, and total economic cost** | High | Very high | Low–medium; needs production or customer data |
| **Security and poisoned-instruction resistance** | High | Very high | Requires a separate safe, adversarial harness |
| **Generic file-present vs. file-absent comparison** | Lower novelty now | Medium | High, but already heavily studied and easy to misinterpret |

### Recommended ordering

1. **Ship the complete-MD challenge** on a repository pack that can discriminate among candidate files for the fixed strong agent.
2. Preserve every submitted MD, run trace, patch, score, model, and resource condition.
3. Use the resulting corpus to study which kinds of files and rules correlate with success.
4. Later run controlled ablations on promising mechanisms.
5. Use the challenge corpus and trusted evaluator as the objective layer for an automated authoring or optimization loop.

This keeps the project on its roadmap while preserving the larger research opportunity.

---

## 8. What the public MD challenge would look like

### Authoring phase

The public challenge exposes:

- a repository or realistic public snapshot;
- its normal documentation and tests;
- the agent and harness contract;
- development tasks or a public practice pack;
- the file format and size limits;
- the scoring dimensions.

A participant may write the MD manually or use any agent to inspect the repository and draft it. This is not cheating; it mirrors existing practice and is a precursor to automated MD authoring.

### Evaluation phase

MD_EVAL freezes the submission and runs:

```text
candidate MD
+ fixed coding agent
+ fixed harness and tools
+ sealed repository tasks
+ fixed resource budget
→ objective task checks
→ regression checks
→ cost and trace capture
→ leaderboard result
```

The evaluator compares **complete submitted artifacts**. It does not need to know whether a human, Codex, Claude Code, Cursor, or another system authored them.

### Why sealed tasks matter

Competitors can study the repository, but they should not optimize directly against every scoring task and hidden checker. Development and confirmation need separation. Otherwise the challenge rewards task-specific leakage rather than an instruction file that generalizes to new repository work.

### What the leaderboard can report

- full task-resolution rate;
- task-level reliability across repeats;
- regressions and hard failures;
- time, model calls, tool calls, and tokens;
- scope violations;
- optional blinded quality review among mechanically passing patches;
- model, reasoning effort, harness version, task-pack version, and MD hash.

The winner is not “the most impressive-looking MD.” It is the frozen file that causes the fixed coding agent to produce better downstream outcomes under the declared conditions.

---

## 9. Implications for the current project

### What this research supports

- A public competition around repository-specific MD artifacts is coherent.
- Competitors should be allowed to use an agent to inspect the repository and write their submission.
- The complete file is a legitimate deployment unit even though later research may decompose it.
- Task outcomes, regressions, and cost should determine the leaderboard—not stylistic resemblance to a preferred philosophy.
- The resulting submission-and-trajectory corpus can later support automated MD generation and mechanism research.

### What it does not solve

- It does not automatically provide difficult, representative sealed tasks for the strongest model.
- It does not prove that the current synthetic task factory is sufficient.
- It does not prove that the current full `CODER.md` will help inside the disposable runner.
- It does not eliminate the need for a task-acquisition decision if existing packs remain at ceiling.
- It does not justify building a failure-mining factory before the challenge product exists.

### The key distinction

There are two linked but different agents:

1. **The MD-authoring agent** inspects the repository and proposes the instruction file.
2. **The coding agent under evaluation** receives that frozen file and attempts sealed coding tasks.

The first can eventually become the Stage 4 optimization loop. The second is what the current evaluator already measures.

---

## 10. Bottom line

People use coding-agent MDs as only one layer in a broader system of repository knowledge, scoped rules, skills, memory, tools, workflow controls, and mechanical enforcement. The evidence does not support a universal best format or a universal benefit. It supports controlled, deployment-specific evaluation.

For MD_EVAL, the coherent near-term product is:

> **Let humans and authoring agents compete to produce the best repository-specific instruction artifact, then evaluate each frozen submission by what the same strong coding agent accomplishes on fresh sealed work.**

The broader long-term research program is:

> **Determine which information and controls belong in always-on Markdown, scoped context, retrieval, skills, tests, hooks, permissions, and the harness—and how that allocation changes by model and task.**

---

## References

[^agent-readmes]: Chatlatanagulchai, W., et al. (2025). [Agent READMEs: An Empirical Study of Context Files for Agentic Coding](https://arxiv.org/abs/2511.12884).

[^agents-eval]: Gloaguen, T., Mündler, N., Müller, M., Raychev, V., & Vechev, M. (2026). [Evaluating `AGENTS.md`: Are Repository-Level Context Files Helpful for Coding Agents?](https://arxiv.org/abs/2602.11988).

[^efficiency]: Lulla, J. L., et al. (2026). [On the Impact of `AGENTS.md` Files on the Efficiency of AI Coding Agents](https://arxiv.org/abs/2601.20404).

[^probe-refine]: Shepard, A., & Albrecht, J. (2026). [Probe-and-Refine Tuning of Repository Guidance for Coding Agents](https://arxiv.org/abs/2606.20512).

[^context-ablation]: Khatri, P. (2026). [Do Context Files Help Coding Agents? A Two-Agent Ablation Study on Real Repositories](https://arxiv.org/abs/2607.27250).

[^guardrails]: Zhang, X., et al. (2026). [Do Agent Rules Shape or Distort? Guardrails Beat Guidance in Coding Agents](https://arxiv.org/abs/2604.11088).

[^config-smells]: dos Santos, H. V. F., Costa, V., Montandon, J. E., Silva, L. L., & Valente, M. T. (2026). [Configuration Smells in `AGENTS.md` Files: Common Mistakes in Configuring Coding Agents](https://arxiv.org/abs/2606.15828).

[^openai-harness]: Lopopolo, R. (2026). [Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/). OpenAI.

[^anthropic-memory]: Anthropic. [Manage Claude’s memory](https://docs.anthropic.com/en/docs/claude-code/memory). Official Claude Code documentation.

[^anthropic-sandbox]: Anthropic. (2025). [Beyond permission prompts: making Claude Code more secure and autonomous](https://www.anthropic.com/engineering/claude-code-sandboxing).

[^cursor-rules]: Cursor. [Rules](https://cursor.com/docs/rules). Official documentation.

[^cursor-skills]: Cursor. [Agent Skills](https://cursor.com/docs/skills). Official documentation.

[^github-instructions]: GitHub. [Adding repository custom instructions for GitHub Copilot](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions).

[^github-cheatsheet]: GitHub. [Copilot customization cheat sheet](https://docs.github.com/en/copilot/reference/customization-cheat-sheet).

### Evidence note

The directly relevant academic literature is new and several cited studies are arXiv preprints rather than settled consensus. Their findings should be treated as current evidence under specific experimental conditions, not as universal laws. Official product documentation establishes available mechanisms and recommended workflows; it does not by itself prove that those practices improve coding outcomes.
