# MD_EVAL: What We Are Building, Where We Are, and the Roadmap-Aligned Way Forward

**Date:** August 21, 2026  
**Status:** Decision document  
**Purpose:** Consolidate the project evidence, the attached roadmap, the earlier failure-derived memo, and the subsequent discussion into one stable account. Where this document conflicts with the earlier memo, this document supersedes it.

---

## Executive summary

The product vision is a challenge site where people compete to produce the best repository instruction file, such as `CODER.md` or `AGENTS.md`.

The intended workflow is:

```text
PUBLIC AUTHORING PHASE
Public repository + public documentation
                ↓
Participant, usually assisted by an agent, studies the repository
                ↓
Participant submits one candidate MD for that repository

SEALED EVALUATION PHASE
Candidate MD + the same strong coding model + hidden tasks from that repository
                ↓
Objective checkers + repeated paired runs + preserved evidence
                ↓
Correctness, regression, and cost score
                ↓
Leaderboard

FUTURE AUTORESEARCH PHASE
An automated system studies the repository, proposes an MD, evaluates it,
learns from the result, and proposes another MD
```

**Yes: an agent inspecting the repository and helping write the MD is central to the product vision.** The challenge is the human- or agent-assisted precursor to the automated MD optimization loop in the final roadmap stage.

The project is not primarily stuck because the evaluator is missing. Most of the trusted evaluation machinery already exists. It is stuck because the current task corpus does not distinguish instruction files when used with the strong target model. Nearly every checker-sound small task has been solved perfectly without an MD. Hiding or dispersing stated requirements did not fix that.

The stable way forward is therefore:

1. **Keep the strong target model.** Do not switch to a weaker model merely to create failures.
2. **Keep the existing evaluator.** Do not redesign the statistics, evidence, tamper protection, or checker system.
3. **Define the Stage 1 challenge as one submitted MD evaluated across several sealed tasks from the same public repository.** This is the missing product-level specification.
4. **Build one small repository-level challenge pack manually before building any generalized factory.** The current runner can already apply one MD across multiple tasks.
5. **Do not build a failure factory now.** Failure-derived tasks remain a useful task-curation technique, but automated failure mining is a later task-acquisition project.
6. **Use a hard timebox.** Build the local challenge shell and attempt a small real repository pack. If the task source still yields only ceilings, stop and make the roadmap’s explicit task-source decision. Do not quietly begin another multi-week infrastructure project.

This keeps the project on the sequence in the attached roadmap: **statistics → open-source challenges → paid pilots → subscriptions → autoresearch**.[^roadmap]

---

## 1. What the product actually is

### 1.1 The competition unit

The clearest Stage 1 competition unit is:

> **One public repository, one submitted MD, one fixed strong coding agent, and one sealed pack of repository tasks.**

A participant receives the public repository and any public authoring materials. The participant may write the MD manually, ask an agent to inspect the repository and draft it, run their own experiments on public development tasks, or combine these approaches. The site initially needs only the final submitted MD, not the participant’s authoring system.

The submitted MD is then inserted into fresh copies of the repository for hidden coding tasks. The same model, harness, reasoning setting, permissions, and run policy are used for every submission. The tasks and private checkers remain sealed.

The authoring snapshot must not expose the hidden fixes. Hidden tasks should be unpublished, privately constructed, or drawn from repository states whose solutions are not visible in the public authoring history. Public development tasks and sealed holdout tasks must be separated.

This design tests whether the MD captures reusable repository knowledge and working procedures that help across multiple tasks, rather than whether it contains a hint for one known issue.

### 1.2 The two agents must not be confused

There are two distinct agent roles:

| Role | What it sees | What it produces |
|---|---|---|
| **MD-authoring agent** | The public repository, documentation, public development tasks, and perhaps prior public results | A candidate `CODER.md` or `AGENTS.md` |
| **Subject coding agent** | A hidden task, its repository snapshot, and the candidate MD | A code change that is objectively checked |

The current MD_EVAL infrastructure evaluates the **subject coding agent**. It does not yet host or standardize the **MD-authoring agent**. That is acceptable for Stage 1: participants can use their own tools and submit the resulting file.

Stage 4 later automates the authoring role:

```text
inspect repository → propose MD → evaluate on development pack → revise MD
```

The hidden holdout pack remains sealed so the optimizer cannot simply memorize task answers.

### 1.3 What the site would show

A minimal challenge page needs:

- the public repository or frozen authoring snapshot;
- the target model and harness settings;
- the MD filename and size or format rules;
- public development examples, if any;
- an upload box for the candidate MD;
- a sealed evaluation queue;
- a leaderboard showing task completion, regressions, cost, and uncertainty;
- downloadable evidence or a reproducibility record where disclosure is safe.

The site does **not** initially need:

- an automated MD generator;
- a failure-mining platform;
- arbitrary GitHub repository ingestion;
- a persistent multi-agent coding organization;
- automatic PR creation and merging;
- the final autoresearch loop.

Those are later capabilities.

---

## 2. How this interpretation fits the roadmap

The attached roadmap explicitly defines the sequence:

1. Statistics
2. Open source and MD challenges
3. Paid harness-evaluation pilots
4. Regression subscriptions
5. Autoresearch

It also says that Stage 1 releases the engine and public packs, while Stage 4 begins with an MD loop trained on the challenge corpus. The roadmap identifies the validated task corpus and trust layer—not merely the optimization loop—as the eventual moat.[^roadmap]

The roadmap does **not** explicitly define whether the Stage 1 entrant submits:

- one generic MD used across unrelated miniature repositories;
- one repository-specific MD;
- or an automated MD-generation program.

The user’s clarified product vision resolves that ambiguity:

> **Stage 1 should begin with repository-specific static MD submissions. Participants may use agents to inspect the repository and write them. Stage 4 later automates that process.**

The roadmap names Kimi for the original challenge. The current decision is not to substitute a weaker model merely to make the tasks fail. The challenge should use the strong target model the project actually wants to evaluate and label every result by model and harness. If that changes the named model in Stage 1, the roadmap should be amended explicitly rather than quietly changing the scientific question.

That is a clarification of the roadmap, not a replacement for it.

### Roadmap mapping

| Roadmap stage | Repository-MD challenge interpretation |
|---|---|
| **0. Statistics** | Prove paired execution, A/A calibration, valid `INCONCLUSIVE` output, evidence integrity, and objective checking. |
| **1. Open source + challenges** | Publish one or more repository packs. Entrants inspect a public repo and submit an MD. Evaluate all submissions on sealed tasks with one fixed model. |
| **2. Paid pilots** | Build private packs from a customer’s repository and compare the customer’s current instructions or harness with alternatives. |
| **3. Subscriptions** | Re-run frozen repository packs when the model, harness, MD, or repository changes. Alert on regressions and cost changes. |
| **4. Autoresearch** | Automate repository inspection, MD proposal, evaluation, and iteration against the owned objective corpus. |

---

## 3. What has already been built

The August 21 handoff describes a substantial working evaluation system.[^handoff]

### 3.1 Trusted task format

Each task contains:

- `public/`: what the subject model sees;
- `reference/`: a known-correct solution;
- `blind/`: an independently produced solution made from the public task alone;
- `check.py`: the private objective checker;
- `requirements.json`: the scored requirements and omission probes;
- `manifest.json`: hashes and admission evidence binding the task bytes.

### 3.2 Admission and integrity

`taskcheck.py` verifies that:

- the untouched project fails;
- the reference and blind solutions pass;
- the checker is deterministic;
- individual omissions can be detected;
- requirements are legitimately stated or inferable under the task rules;
- `CODER.md` content does not leak into grading;
- task files are frozen and bound to a tamper-evident ledger.

### 3.3 Task and run pipeline

The archive includes:

- `taskgen.py` for recipe-driven candidate generation;
- `blindsolve.py` for isolated independent solving and provenance;
- `run_batch.py` for one- or two-arm runs with equal task bytes, alternating order, approvals, evidence capture, and replacement-call limits;
- `compare.py` for evidence verification and paired comparison.

The runner already accepts multiple tasks and applies the same arm MD to every task. This means a repository-level challenge pack does **not** require a new evaluator. At most it requires pack metadata, submission packaging, and tasks that genuinely belong to one repository distribution.

### 3.4 What is not yet a product

Despite the tooling, the project does not yet provide:

- a simple submission-to-score user experience;
- a hosted challenge site;
- a leaderboard;
- a repository-level public pack with sealed, discriminating hidden tasks;
- a stable definition of what entrants are optimizing;
- an automated MD-writing or autoresearch loop.

So the accurate state is:

> **The trusted evaluation engine is largely built. The challenge product and a useful objective corpus are not.**

---

## 4. What the experiments have actually shown

The project has spent substantial effort trying to create synthetic tasks that are valid but difficult enough for the strong target model.

The internal record reports:[^process]

- In the M2 campaign, 14 checker-sound tasks were solved in every repeated attempt. Six other tasks produced apparent floors because of hidden requirements and were invalid.
- In `scout-v1`, four sound tasks were solved 3/3; two apparent failures were invalid scope-routing cases.
- Sound rolling tasks such as the badge tool and `durafmt` were solved 3/3.
- Removing prominent requirement signposting from `durafmt` still produced 3/3 success.
- Five independently admitted low-salience tasks produced 15/15 successful no-MD attempts.
- One historical sound task, `scout-c-integration-01`, resolved only 1/3 attempts because the model missed a stated test twice. It showed that legitimate partial failure can occur, but it did not establish a repeatable difficulty band.

The archive’s defensible conclusion is:

> For the tested strong model and repositories of this size, making already stated requirements less prominent has not produced a useful benchmark cohort. Continuing to hide, spread, or softly point to stated requirements is a dead end unless task scale or structure changes substantially.[^handoff]

### 4.1 What this means

It does **not** mean that MD files cannot help coding agents.

It means that the current tasks leave almost no completion headroom:

```text
No-MD completion ≈ 100%
Maximum possible MD completion = 100%
Observable accuracy improvement ≈ 0
```

An MD may still change:

- exploration;
- files inspected;
- test behavior;
- runtime;
- tokens;
- cost;
- regression risk.

But the existing task corpus cannot establish a large beneficial completion effect for this model.

### 4.2 Why the current setup is especially insensitive

Several features work against observing a useful MD effect:

1. **The repositories are small.** The subject agent can often read most of the project during one run.
2. **The legitimate requirements are explicit.** Once found, many are straightforward local changes.
3. **The wrapper already directs the agent to read the task contract and project documentation.** This gives the null arm some of the behavior a coverage-oriented MD would request.
4. **The candidate CODER.md is largely generic.** It does not necessarily encode knowledge specific to each miniature repository.
5. **Parts of the full CODER.md describe workflows the runner forbids.** Worktrees, commits, pull requests, and persistent handoffs cannot improve an evaluation that disables them.
6. **Adding hidden checker requirements is invalid, not difficult.** The project correctly rejected those apparent floors.

The repository-specific competition changes the fourth point: the MD author can deeply inspect one public repository and encode reusable knowledge that is amortized across several hidden tasks.

---

## 5. What the research literature says

External evidence is mixed, which is exactly why a controlled benchmark is useful.

A 2026 controlled study found that repository context files often reduced success and increased inference cost because they added unnecessary requirements, even though agents generally followed them and explored more broadly. The authors recommended keeping human-written files minimal.[^agents-eval]

A different 2026 study used bug-fix probes to iteratively refine repository guidance. Its refined guidance achieved a 33.0% mean resolution rate, compared with 28.3% for its initial static knowledge base and 25.5% with no guidance. The main gain came from helping agents reach evaluable patches and the correct files, not from improving the quality of a patch after localization.[^probe-refine]

SWE-bench demonstrated that real GitHub issues and pull requests can provide challenging repository-level evaluation tasks, although importing and validating those tasks is materially harder than generating miniature synthetic repositories.[^swebench]

OpenAI’s practitioner account of harness engineering describes having Codex write the repository’s initial `AGENTS.md`, replacing an overgrown monolithic file with a short map into structured repository knowledge, and continuously feeding observed failures back into documentation, tooling, and mechanically enforced constraints.[^openai-harness]

These sources support four conclusions:

1. An MD should not be assumed to help merely because it exists.
2. How guidance is created matters.
3. Repository-specific knowledge and navigation are plausible intervention mechanisms.
4. Hard requirements may belong in tests, linters, permissions, or harnesses rather than prose.

They do **not** establish that the complete current CODER.md will improve the current synthetic task pack.

---

## 6. Ideas discussed in this thread and their current status

The conversation explored several possible directions. They should not all become workstreams.

| Idea | What it was trying to solve | Current status |
|---|---|---|
| **Continue hiding or dispersing requirements** | Create legitimate partial failures | **Rejected.** Recent low-salience tasks still saturated. |
| **Use a weaker model** | Create a wider difficulty band | **Rejected for this product.** The goal is to evaluate the strong target model, not manufacture failure by downgrading it. |
| **Impose a tight artificial work budget** | Turn saved exploration into completion differences | **Not the current plan.** It changes the product question and should not be adopted merely to force failures. Cost remains a legitimate outcome under normal fixed settings. |
| **Test only a tiny piece of project-specific information** | Isolate a causal mechanism | **Useful research method, not the whole product.** |
| **Test the complete CODER.md in its full intended workflow** | Evaluate worktrees, loops, commits, handoffs, and review | **Later harness track.** The current runner does not implement that environment. |
| **Build a failure ledger and failure-derived tasks** | Start from observed model failures instead of imagined ones | **Useful task-curation method.** |
| **Build an automated failure factory now** | Scale failure-derived task supply | **Parked.** This would become a major new task-acquisition platform before the challenge exists. |
| **Build a repository-specific MD challenge** | Let people or agents inspect a repo, submit an MD, and compete on hidden tasks | **Selected direction.** This connects the current evaluator to the roadmap and later MD optimization loop. |

### 6.1 What was valuable in the failure-derived memo

The earlier memo correctly argued that an observed failure provides better evidence than an author’s guess about what a model might miss. It also correctly separated:

- discovery or localization failures that instructions may address;
- implementation-capability failures that instructions probably cannot address;
- checker defects that invalidate the task;
- hard constraints that should be enforced mechanically.

That remains useful.

### 6.2 What the earlier memo did not solve

It did not solve task supply. A manually recovered incident can support a mechanism pilot, but it does not automatically yield the many independent hidden tasks required for a challenge or scientific claim.

Building source adapters, null scouting, automatic failure classification, environment reconstruction, and PR-to-task conversion would be a substantial new workstream. The attached roadmap already labels PR-to-task mining as harder, unplanned Stage 1 work and the first real new-build business decision.[^roadmap]

Therefore:

> **Failure-derived evaluation is one possible hidden-task acquisition method. It is not the challenge architecture, and it is not a prerequisite for the first prototype.**

---

## 7. The chosen architecture

### 7.1 Stage 1: static repository-specific MD challenge

For each challenge repository:

```text
repo-pack/
  authoring-snapshot/       # public
  public-development/       # optional public tasks and results
  task-01/                  # sealed during competition
  task-02/
  task-03/
  ...
  pack.json                 # model, harness, scoring, MD rules
```

Each hidden task can retain the current MD_EVAL task structure:

```text
task-01/
  public/
  reference/
  blind/
  check.py
  requirements.json
  manifest.json
```

The same submitted MD is injected into every task in the pack. The current batch runner already supports this execution pattern.

### 7.2 Stage 4: automated MD authoring

The later optimizer becomes:

```text
public repository
        ↓
analysis agent
        ↓
candidate MD
        ↓
current trusted evaluator on development tasks
        ↓
result and evidence
        ↓
next candidate MD
```

The final candidate is evaluated once on a sealed holdout. This is the automated version of what Stage 1 competitors do manually or with their own agents.

### 7.3 Separate future harness division

A complete CODER role file may govern:

- worktrees;
- commits;
- long-running loops;
- workpads and persistent state;
- pull requests;
- agent review;
- handoffs and authorization.

Testing those mechanisms requires a matching persistent workflow. That can become a later harness-evaluation division, especially in Stage 2. It should not be silently mixed into the first static-MD challenge.

---

## 8. The immediate way forward without another multi-week detour

There are two different deliverables. They should be timeboxed separately.

### Deliverable A: local challenge shell

**Goal:** demonstrate the actual product interaction locally.

```text
public repo pack + submitted MD
              ↓
existing batch runner
              ↓
comparison and evidence
              ↓
leaderboard-style result row
```

This requires modest glue:

- a `pack.json` or equivalent grouping file;
- a command that accepts an MD submission and runs it across the pack;
- a result summarizer suitable for a leaderboard row;
- baseline entries for no MD and the current champion MD.

The underlying runner, checker, evidence, and comparison system remain unchanged.

### Deliverable B: one discriminating repository pack

**Goal:** create the smallest pack that can test the competition concept with the strong target model.

Start with one repository and manually curate or import a small number of tasks. Do not build generalized mining.

A prototype pack can begin with three tasks. A credible alpha pack will need more, but the first question is whether a repository-specific MD can create any useful separation at all.

Candidate task sources, in priority order:

1. already preserved, checker-sound tasks from one repository or project history;
2. manually reconstructed real issues with a known correct repair;
3. existing benchmark tasks that can be imported without creating a new environment platform;
4. carefully designed tasks in a medium repository where the required knowledge is legitimate and reusable across tasks;
5. observed failures, when a recoverable incident is available.

The treatment should be a repository-specific MD written after inspecting the public authoring snapshot. The baseline remains an empty MD. The strong model and normal run settings remain fixed.

### Hard timebox and gate

The next development cycle should have a strict boundary:

1. Build the local submission-to-report shell.
2. Attempt to assemble a three-task repository pack without building reusable mining infrastructure.
3. Run null scouting with the strong target model.
4. Repeat only legitimate failures to determine whether they are stable enough for development.
5. Test one repository-specific candidate MD across the same tasks.

Then stop and decide.

| Result | Decision |
|---|---|
| At least part of the pack produces legitimate, repeatable headroom and the repo MD changes behavior or outcome | Expand this pack and prepare an alpha challenge. |
| Tasks remain ceilings, but MD materially lowers cost without regressions | Decide explicitly whether the challenge will score efficiency as a primary dimension. |
| All tasks remain ceilings and cost differences are negligible | The task source is unsuitable. Make the roadmap’s PR-to-task/import decision. |
| Task construction repeatedly produces invalid hidden requirements or brittle checkers | Stop the source method. Do not hide more requirements. |
| The work begins expanding into automatic mining, arbitrary dependency reconstruction, or a new harness | Stop. That is a separately authorized project, not completion of the prototype. |

The software shell can be built quickly. **The existence of discriminating tasks cannot be promised on a schedule.** That is the uncertainty the timeboxed pack attempt must resolve.

---

## 9. Scalability

### 9.1 Why the challenge architecture scales

A repository-specific challenge amortizes repository understanding:

- the participant or authoring agent studies the repository once;
- the resulting MD is tested across many fresh hidden tasks;
- the subject agent starts fresh on each task but receives the reusable repository map and procedures;
- one hidden pack supports many submissions;
- one trusted evaluator supports many repositories.

The expensive asset becomes the validated hidden task corpus. That is consistent with the roadmap’s claim that the moat is **owned objectives plus trust**, not merely the loop.[^roadmap]

### 9.2 What does not need to scale immediately

The first challenge does not require automatic task creation. Many successful benchmarks begin with carefully curated tasks. Manual curation is acceptable for the first pack because the objective is to validate demand and the competition format.

### 9.3 How task acquisition can scale later

The roadmap already contains natural sources:

- **Stage 1:** closed PR-to-task mining or imported public benchmark tasks;
- **Stage 2:** customer issues, rejected agent patches, review comments, and CI failures;
- **Stage 3:** every newly observed customer regression becomes a candidate frozen task;
- **Stage 4:** the growing challenge and customer corpus becomes the objective layer for MD optimization.

Failure-derived mining can become one of these acquisition pipelines later. It should be judged by admitted-task yield and human effort, not assumed to scale in advance. Selecting development tasks because the null arm failed is acceptable for finding a challenge difficulty band, but it cannot by itself estimate the average effect of MDs on arbitrary repository work. Any general scientific claim would require prospectively selected held-out tasks.

### 9.4 The real scaling risk

The primary scaling risk is not running submissions. The current runner already batches arms and tasks.

The risk is producing many tasks that are simultaneously:

- realistic;
- checker-sound;
- reproducible;
- not leaked;
- difficult enough for the target model;
- and plausibly affected by repository guidance.

That is precisely why the first pack should be manually curated and timeboxed before any factory is built.

---

## 10. What should be added to the roadmap

The roadmap needs one clarifying sentence, not a new stage:

> **Stage 1 challenge unit: entrants inspect a public repository and submit one repository-specific `coder.md`/`agent.md`; the fixed strong subject model is evaluated on a sealed multi-task pack from that repository. Entrants may use their own agents to author the MD, and submissions are judged as artifacts rather than by the tools used to create them.**

It should also record:

> **Automated failure mining is parked as a possible closed task-acquisition method. It is not required for the first challenge.**

And:

> **The full persistent CODER workflow is a later harness-evaluation track, not part of the first static-MD challenge unless the runner explicitly implements those mechanisms.**

These clarifications prevent the project from drifting between three different products:

1. a generic prompt benchmark;
2. a repository-specific MD challenge;
3. a full autonomous coding-harness benchmark.

The selected first product is number 2.

---

## 11. What not to build next

Until the repository challenge prototype produces evidence, do not build:

- a generalized failure factory;
- arbitrary GitHub PR ingestion;
- automatic first-divergence classification;
- a weaker-model challenge solely to create failures;
- artificial budget restrictions solely to create failures;
- a persistent multi-agent workflow;
- a hosted MD-generation service;
- the autoresearch optimizer;
- broad new statistical machinery;
- another synthetic low-salience task cohort of the same type.

These may become legitimate later projects. They are not the next prototype.

---

## 12. Current decision in one paragraph

MD_EVAL should become a repository-specific instruction-file challenge. A participant—or an agent working for the participant—studies a public repository and submits one MD. The existing strong coding model then receives that MD while solving several sealed tasks from the same repository. The current trusted evaluator is largely capable of running this comparison; the missing asset is a discriminating repository pack and the missing product layer is submission-to-leaderboard glue. The failure-derived idea remains useful as one way to curate future tasks, but building an automated failure factory now would move the project away from its immediate roadmap. The next work is one timeboxed local repository challenge, not another generalized infrastructure program.

---

## Sources and evidence boundaries

### Internal project sources

[^roadmap]: *Roadmap — Aug 7, 2026*, including the Stage 0–4 table and the August 20 tooling-coverage note. It establishes the sequence “Statistics → Open source + challenges → Paid pilots → Subscriptions → Autoresearch,” identifies PR-to-task mining as unplanned harder work, and describes the trusted corpus as part of the Stage 4 moat.

[^handoff]: *Outside review handoff — 21 August 2026* (`outside-handoff-2026-08-21/HANDOFF.md`). It defines the benchmark, inventories the built pipeline, and records the final 15/15 low-salience null result.

[^process]: *Process & Science Findings — 2026-08-19* (`handoffs/PROCESS_FINDINGS_2026-08-19.md`). It contains the complete live-result ledger, the historical `scout-c-integration-01` exception, task-validity failures, throughput findings, and the distinction between development calibration and confirmatory evidence.

The claims about what has been built and what the internal experiments found are derived from these project files. The recommendation to define the competition as a repository-specific MD challenge is a product-design decision made in this document; the original roadmap did not specify the challenge unit this precisely.

### External research and practitioner sources

[^agents-eval]: Thibaud Gloaguen, Niels Mündler, Mark Müller, Veselin Raychev, and Martin Vechev, [“Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?”](https://arxiv.org/abs/2602.11988), arXiv:2602.11988, 2026. The paper reports that context files often reduced success and increased inference cost, while encouraging broader exploration and instruction compliance.

[^probe-refine]: Asa Shepard and Jeannie Albrecht, [“Probe-and-Refine Tuning of Repository Guidance for Coding Agents”](https://arxiv.org/abs/2606.20512), arXiv:2606.20512, 2026. The paper reports 33.0% mean resolution for refined guidance, 28.3% for the initial static knowledge base, and 25.5% for no guidance; the main gain was increased coverage and evaluable patches.

[^swebench]: Carlos E. Jimenez et al., [“SWE-bench: Can Language Models Resolve Real-World GitHub Issues?”](https://arxiv.org/abs/2310.06770), arXiv:2310.06770, 2023. SWE-bench introduced 2,294 repository-level tasks drawn from real GitHub issues and corresponding pull requests.

[^openai-harness]: Ryan Lopopolo, [“Harness engineering: leveraging Codex in an agent-first world”](https://openai.com/index/harness-engineering/), OpenAI, February 11, 2026. This is a practitioner report rather than a controlled study. It describes Codex writing repository instructions, using a short `AGENTS.md` as a map, making repositories agent-legible, and feeding failures into documentation, tooling, and mechanical controls.

### Evidence note

The recent context-file papers are preprints and do not settle whether repository instruction files help in general. They support the need for controlled, repository-specific evaluation and warn against assuming that more instructions are automatically better. The internal task results establish the current ceiling problem but do not establish that a repository-specific challenge will solve it. The proposed timeboxed pack is the experiment needed to answer that next question.
