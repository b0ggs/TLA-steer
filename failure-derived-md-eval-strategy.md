# Failure-Derived MD Evaluation

## A same-day pilot, infrastructure assessment, and roadmap fit

**Date:** August 21, 2026  
**Recommendation:** Run a one-task, two-arm proof-of-mechanism now. Treat it as a test of whether the new task-acquisition strategy works, not as a confirmatory result about MD files in general.

## Executive decision

The proposed idea is to stop trying to manufacture instruction sensitivity by making synthetic requirements less salient. Instead, begin with an **observed coding-agent failure**, identify the first meaningful divergence from a successful path, and reconstruct that incident as a controlled MD_EVAL task. Then test whether a **minimal, mechanism-matched repository instruction** prevents the same failure.

This is a good direction for three reasons:

1. It directly addresses the current ceiling problem. The existing task factory has repeatedly produced valid tasks that the bare model solves every time. Failure-derived acquisition begins with evidence that the agent can actually fail under the relevant conditions.
2. It creates a causal hypothesis. The treatment is not “a better MD” in the abstract. It is one instruction intended to change one diagnosed behavior, such as running the correct integration suite, avoiding a generated file, or consulting the repository’s actual source of truth.
3. It preserves nearly all of the expensive infrastructure already built: task admission, public/reference/blind trees, objective checking, omission probes, frozen manifests, paired execution, evidence capture, and comparison.

This is **not a major redesign** for the next experiment. The immediate change is primarily in how tasks are sourced and documented. A larger redesign would occur only later if the project expands from static MD files to persistent workflows, skills, retrieval, hooks, or full harness orchestration.

A complete end-to-end **developmental pilot** can reasonably be assembled and run in approximately **four to six hours** if the original failure snapshot, trace, and known repair are available. That pilot can determine whether the mechanism is promising. It cannot support a general claim about MD effectiveness from one task.

---

## 1. The idea

### 1.1 Start with a failure, not a task recipe

For each candidate incident:

1. Recover the repository state and task prompt from immediately before the failed run.
2. Preserve the failed trajectory or enough evidence to know what happened.
3. Identify the **first divergence** from a successful trajectory.
4. Classify that divergence.
5. Decide whether a static repository instruction could plausibly prevent it.
6. Reconstruct the incident in the existing MD_EVAL task format.
7. Compare a null arm with one concise, targeted instruction.

The causal chain being tested is:

```text
instruction available
        ↓
instruction used
        ↓
target behavior changes
        ↓
original failure is prevented
        ↓
final task outcome improves, or equal correctness costs less
```

This is stronger than observing only whether the final checker passed. If the targeted instruction caused the agent to run the missing integration test but the implementation still failed, the experiment has learned that the instruction fixed a verification failure but exposed an implementation failure. If the instruction was read but behavior did not change, that is a different result again.

### 1.2 Not every observed failure belongs in an MD study

The selection rule should be strict:

| Observed failure | Static MD candidate? | Reason |
|---|---:|---|
| Agent never found a project-specific test command | Yes | Repository guidance can expose operational knowledge. |
| Agent edited a generated artifact rather than its source | Yes, initially | A concise rule may help; a mechanical guard may ultimately be better. |
| Agent used the wrong package or entry point in a monorepo | Yes | This may be a localization or repository-map failure. |
| Agent declared completion without required integration verification | Maybe | Could be a static instruction, but may belong to a workflow or harness treatment. |
| Agent read and correctly explained the requirement, then wrote incorrect code | Usually no | This is more likely an implementation-capability failure. |
| Checker required behavior that was not publicly specified or inferable | No | This is an invalid evaluation task, not an agent failure. |
| Agent violated a safety boundary that should be impossible to cross | Separate study | Prefer sandboxing, permissions, hooks, or executable policy. |

The governing question is therefore not “Can an MD fix this?” It is:

> **What failed, and what is the least costly reliable intervention that could have prevented it?**

For this immediate project, admit only the subset where the hypothesized intervention is a static repository instruction. Other failures can be retained in a broader failure ledger for later harness or guardrail studies.

---

## 2. Why this is a strong research direction

### 2.1 It responds to the actual evidence from MD_EVAL

The current project has already established that hiding, dispersing, or weakly pointing to legitimate requirements does not reliably create a useful difficulty band for the tested frontier model. The most recent low-salience cohort still produced 15 successful null-arm attempts out of 15. Continuing to make explicit requirements easier to overlook is therefore unlikely to solve the scientific problem.

Failure-derived acquisition changes the selection variable. Instead of asking an authoring agent to imagine what a coding model might miss, it starts from an incident in which a model demonstrably missed something, followed the wrong process, or failed to complete the work.

This does **not** guarantee instruction sensitivity. The failure may still prove to be model capability, bad evaluation, or a problem that needs enforcement rather than prose. But it gives the experiment a real mechanism to investigate.

### 2.2 It is better aligned with the emerging empirical literature

Recent context-file studies do not support the simplistic proposition that adding an `AGENTS.md` generally helps. One 2026 study found no significant success improvement overall, while context files increased exploration and inference cost; its authors recommended that human-written files contain only minimal requirements not already available elsewhere.[^1] This argues against testing a large undifferentiated CODER.md first.

The closest direct precedent for the proposed direction is *Probe-and-Refine Tuning of Repository Guidance for Coding Agents*. It iteratively used bug-fix probes to diagnose and refine repository guidance. Its refined guidance achieved a 33.0% mean resolve rate, compared with 28.3% for its initial static knowledge base and 25.5% without guidance. The improvement primarily increased the number of evaluable patches and helped agents reach the correct files; it did not materially improve precision once a patch existed.[^2] That is not proof that this exact MD_EVAL design will work, but it is strong evidence that **guidance derived from diagnosed failures can behave differently from generic guidance**.

A large empirical study of 2,303 agent context files found that practitioners most often use them for test procedures, implementation details, and architecture.[^3] These are precisely the kinds of mechanism-specific failures that a failure-derived task corpus would expose and test.

A separate paired study found that `AGENTS.md` was associated with lower median runtime and output-token use while completion behavior remained comparable.[^4] This supports retaining cost and efficiency as meaningful outcomes even when pass rates tie.

### 2.3 It follows the successful benchmark precedent of real software failures

SWE-bench established the value of constructing repository-level coding tasks from real GitHub issues and their corresponding pull requests, rather than relying only on synthetic programming exercises.[^5] Failure-derived MD_EVAL applies the same basic realism principle to a narrower causal question: not merely “Can the agent fix the issue?” but “Can a specified instruction prevent a known failure mode while the task and agent remain fixed?”

Real-task provenance does not remove the need for strong evaluation. UTBoost found that some SWE-bench tests were insufficient and identified hundreds of patches that had been incorrectly accepted.[^6] This strengthens the case for preserving MD_EVAL’s reference solution, blind solution, omission probes, regression checks, determinism tests, and frozen manifest instead of replacing them with raw PR tests.

### 2.4 It matches how advanced practitioners describe improving agent environments

OpenAI’s published harness-engineering account describes a feedback loop in which agent failures are treated as evidence of missing capabilities, tools, guardrails, or documentation. It also reports that one large monolithic `AGENTS.md` failed, leading the team to use a short map, structured repository knowledge, progressive disclosure, and mechanical enforcement for hard constraints.[^7]

That supports two principles of the proposed experiment:

- Diagnose the failure before choosing the treatment.
- Test the smallest relevant instruction first, then decide whether it belongs in prose, documentation, a skill, or executable enforcement.

### 2.5 It creates interpretable negative results

The current ceiling results say little about why an MD did not help. Failure-derived tasks can produce more informative outcomes:

- **Treatment changes nothing:** the diagnosed failure was probably not instruction-addressable, the instruction was ineffective, or the agent already knew the fact.
- **Target behavior changes but task still fails:** the instruction addressed one mechanism but implementation ability remained limiting.
- **Task improves:** evidence for the targeted instruction on that failure family.
- **Correctness ties but cost falls:** evidence for efficiency value.
- **Treatment harms performance:** evidence that the instruction adds distraction, conflict, or unnecessary process.

This is much more useful for both research and customer decisions than a single average “MD score.”

---

## 3. Does the existing infrastructure work?

### 3.1 What remains unchanged

| Existing component | Use in the new experiment | Redesign required? |
|---|---|---:|
| `public/` task tree | Pre-failure repository state and neutral task contract | No |
| `reference/` | Known-correct repair | No |
| `blind/` | Independent solution from public evidence only | No |
| `check.py` | Functional requirements and regressions | No |
| `requirements.json` | Requirement keys, target paths, omission probes, and public statements | No |
| `taskcheck.py` | Admission, arm neutrality, determinism, provenance, and integrity | No |
| Frozen manifest and ledger | Bind the admitted task before exposure | No |
| `run_batch.py` | Null versus targeted instruction, three attempts per arm | No |
| Evidence capture | Preserve attempts, durations, final trees, and runner settings | No |
| `compare.py` | Paired task-level comparison once a cohort exists | No |

The expensive and trustworthy part of the project remains the same.

### 3.2 What changes for the pilot

#### A. Bypass synthetic generation

For the first pilot, do not use `taskgen.py` to invent a new problem. Manually reconstruct one observed failure directly into the existing task layout.

This is a new **input path**, not a new evaluation architecture.

#### B. Add one provenance file

Add a private, task-root file such as `failure-source.json`:

```json
{
  "source_type": "observed_agent_failure",
  "source_incident": "internal-id-or-commit",
  "subject_model": "gpt-5.6-sol",
  "first_divergence": "verification.integration_suite_not_run",
  "observed_failure": "The agent completed the unit tests but never ran the required integration command.",
  "known_resolution": "The correct repair and integration suite pass.",
  "instruction_hypothesis": "A concise repository rule naming the integration command will increase its execution and prevent premature completion.",
  "mechanism_observation": "Whether the command appears in the preserved event trace.",
  "eligible_for_static_md": true
}
```

For the same-day pilot, this file does not require a schema change. The current admission tool hashes all task-root files other than the generated manifest, so the auxiliary metadata can be integrity-bound immediately. Semantic validation can be added later if the approach survives the pilot.

#### C. Add manual mechanism review

The objective checker should continue to decide correctness. Separately, review the trace for the preregistered mechanism observation, such as:

- Was the required command executed?
- Was the correct source-of-truth document opened?
- Was the generated file avoided?
- Was the correct package entered before editing?

Do not automate this before the pilot. A short human-coded diagnostic note is enough to determine whether the research direction is viable.

### 3.3 What should not be built now

Do not build any of the following for the first test:

- generalized PR mining;
- automatic failure classification;
- a multi-arm instruction-delivery framework;
- skills or retrieval;
- persistent worktrees and long-running orchestration;
- an MD optimizer;
- automated first-divergence judging.

Those would turn a small task-acquisition change into a major platform redesign before the central mechanism has been demonstrated.

---

## 4. How to run a complete pilot in hours

### 4.1 What “complete” means

A same-day pilot can be complete in the engineering sense:

- one valid task;
- a known-correct reference;
- an independent blind solution;
- a passing admission check;
- null and targeted instruction arms;
- three attempts per arm;
- verified evidence;
- objective scoring;
- trace-level mechanism assessment;
- a written continue/stop decision.

It will **not** be a confirmatory benchmark. The current comparison tool requires at least six non-tied task-level differences before it can issue a directional verdict. One task should therefore produce `INCONCLUSIVE` in the formal comparison, even if the developmental signal is interesting. That is correct behavior.

### 4.2 Fastest candidate

The best documented existing candidate is `scout-c-integration-01`, provided its task bytes and traces can be recovered. The project record says it was checker-sound, resolved only one of three attempts, and missed one stated test twice. It is the closest existing example of a legitimate non-ceiling task.

It should be used only if the targeted instruction can be expressed as a stable repository rule rather than a task-specific answer. For example:

> For changes affecting `<component>`, run `<integration command>` before declaring completion; the unit suite alone is insufficient.

If the original task assets are unavailable, choose another preserved incident with all four of these properties:

1. pre-failure repository state exists;
2. failed trace exists;
3. correct repair exists;
4. the intervention can be written as a legitimate repository-wide instruction.

### 4.3 Same-day sequence

| Elapsed time | Work | Output |
|---:|---|---|
| 0:00–0:30 | Select incident and write the failure hypothesis before looking at new outcomes | `failure-source.json` draft and eligibility decision |
| 0:30–1:30 | Copy the pre-failure state into `public/`; write a neutral `.issue-contract.md`; copy or recreate the correct repair in `reference/` | Public and reference trees |
| 1:30–2:30 | Adapt the checker and requirements; produce an independent blind solution; run admission | Admitted frozen task |
| 2:30–2:45 | Create the empty null file and one minimal targeted instruction file | Two treatment arms |
| 2:45–3:30 | Queue, approve, run, and verify six attempts | Three null and three treatment results |
| 3:30–4:30 | Run comparison, inspect the preregistered trace behavior, and write the disposition | Continue, revise, or stop decision |
| 4:30–6:00 | Contingency for checker repair, one infrastructure replacement, or task packaging issues | Completed pilot without expanding scope |

The current representative `fac-07` attempt took approximately 146.7 seconds. At that observed rate, six subject calls equal about 14.7 minutes of model execution. At the configured 300-second timeout, six calls have a 30-minute timeout ceiling before any infrastructure replacement. Task reconstruction and checker validation—not live execution—are therefore the main schedule risk.

### 4.4 Minimal arm design

```text
Arm A — null
    Empty CODER.md

Arm B — targeted
    One concise repository-wide rule addressing the diagnosed failure
```

Do not use the full CODER.md in the first pilot. If the minimal instruction produces the predicted mechanism change, the next comparison can test:

1. null;
2. minimal targeted instruction;
3. full current CODER.md.

That reveals whether the full file preserves the useful instruction, dilutes it, or adds harmful process and context.

### 4.5 Pilot outcomes and decision gate

Use final correctness as the primary outcome, but make the same-day continuation decision from both correctness and the preregistered mechanism.

**Continue to a small cohort when:**

- the targeted arm changes the predicted behavior in at least two of three attempts; and
- it produces at least one task-level correctness improvement, prevents a known failure, or shows a substantial efficiency improvement without a regression.

**Revise the instruction when:**

- the instruction is read but interpreted ambiguously;
- the desired behavior changes inconsistently; or
- the instruction duplicates information already strongly supplied by the wrapper or issue contract.

**Stop this failure family when:**

- both arms behave identically;
- the targeted behavior changes but the failure remains purely implementation-related;
- the treatment leaks the solution rather than providing stable repository knowledge; or
- the rule should clearly be enforced mechanically instead of tested as prose.

This is a development gate, not a significance test.

---

## 5. Is it scalable?

Yes, if scaling is staged.

### Level 0: One manual proof-of-mechanism

- One observed failure.
- One targeted instruction.
- Existing evaluator unchanged.
- Manual trace diagnosis.

**Purpose:** determine whether failure-derived acquisition can produce an instruction-sensitive task at all.

### Level 1: A small mechanism cohort

- Six to twelve independent tasks.
- Two or three failure families.
- A consistent `failure-source.json` format.
- Prospective inclusion rules.
- Null calibration by model.

**Purpose:** estimate whether the effect repeats across tasks and repositories.

### Level 2: Semi-automated import

Add a thin `import-failure` or `import-pr` path that accepts:

- base commit;
- issue or task prompt;
- failed trace;
- repair commit or patch;
- test command;
- source metadata.

It should materialize a candidate task, but the existing admission process should remain the authority. This is the scalable version of the roadmap’s currently unplanned PR-to-task mining component.

### Level 3: Customer failure packs

For paid pilots, ingest incidents from a customer’s own repository:

- repeated agent failure;
- reviewer rejection;
- CI regression;
- wrong-layer edit;
- missed project-specific workflow;
- unnecessary cost or exploration.

Then compare the customer’s current harness or instructions against a proposed treatment on a frozen private pack.

### Level 4: Optimization corpus

Once the corpus is sufficiently large and held out by repository, failure family, and model, it becomes the objective layer for the future MD optimization loop. The optimizer is then rewarded for preventing validated real failure modes, not for exploiting synthetic checker quirks.

### The main scaling bottleneck

The bottleneck will be trustworthy task construction, especially the checker. That is exactly where the current infrastructure is strongest. Real PR tests can be incomplete or overfit, so reference/blind agreement, omission probes, regression checks, determinism, and arm neutrality should remain mandatory.[^6]

---

## 6. Does it fit the roadmap?

It fits strongly and does not require reordering the roadmap.[^8]

### Stage 0 — Statistics

The current Stage 0 requires paired runs, A/A calibration, and legitimate `INCONCLUSIVE` results. Failure-derived task acquisition does not replace this. It supplies better candidate tasks for the statistical machinery.

The same-day pilot is a **pre-cohort mechanism probe**. Once a mechanism works, a multi-task cohort can pass through the existing Stage 0 process.

### Stage 1 — Open source and MD challenges

The roadmap calls for public task packs, sealed scoring, and a growing corpus labeled by model. Failure-derived tasks improve this stage because each task can also be labeled by failure mechanism:

- localization;
- repository knowledge;
- verification;
- workflow;
- generated-file governance;
- implementation capability;
- non-instruction-addressable.

This produces a more valuable public challenge than a collection labeled only ceiling or floor.

The roadmap says PR-to-task mining should remain closed. The recommended same-day manual import respects that. It prototypes the closed acquisition method without requiring a public miner.

### Stage 2 — Paid harness-evaluation pilots

This direction may fit Stage 2 better than the current synthetic factory. A buyer can provide actual incidents and ask:

> Can our current instruction file or harness prevent the failures we have already experienced, and at what cost?

The existing private-pack, paired-run, and cost-telemetry infrastructure already supports that product shape. Later, the treatment need not be limited to an MD; it could compare harness configurations once the product expands.

### Stage 3 — Regression subscriptions

A resolved customer incident becomes a frozen regression task. The subscription product can rerun the pack when any of the following changes:

- model;
- agent harness;
- repository instructions;
- repository structure;
- test workflow;
- permissions or tools.

That is a direct continuation from one-time failure diagnosis to ongoing regression monitoring.

### Stage 4 — Autoresearch

The roadmap identifies the moat as **owned objectives plus trust**, not the optimization loop itself. A validated corpus of real, mechanism-labeled failures is a stronger owned objective than a large set of synthetic tasks whose null arms saturate.

The future loop can propose instruction changes and evaluate them against held-out failures. The present recommendation therefore strengthens the objective layer while respecting the decision to keep the optimizer parked.

### The only roadmap amendment needed

Add a thin, explicit task-acquisition lane:

```text
Synthetic recipes
    → pipeline tests, controls, and known-winner validation

Failure-derived imports
    → beneficial-sensitivity research, public challenge packs, and customer packs
```

Synthetic tasks remain useful for testing infrastructure and detecting gross harm. They should no longer be expected to carry the full beneficial-sensitivity claim by themselves.

---

## 7. Risks and controls

| Risk | Control |
|---|---|
| Cherry-picking only failures that favor an instruction | Use failures for development, then freeze external held-out incidents before testing the final treatment. |
| Hindsight leakage from the known repair | Treatment must state a stable repository rule, not identify the exact patch, file, or answer for that task. |
| Incorrect failure diagnosis | Preregister the first-divergence hypothesis and the trace behavior before running treatment attempts. |
| Model-specific results | Label every task and result by model and harness; recalibrate when either changes. |
| One incident duplicated into many pseudo-independent tasks | Require independent incidents or repositories for confirmatory inference. Variants may be used only for development. |
| Weak or overfit checker | Preserve task admission, reference and blind solutions, regressions, omission probes, and determinism checks. |
| Static instruction tested against a workflow failure | Exclude it from the static-MD cohort or explicitly move it to a later workflow-treatment track. |
| Large MD obscures the causal component | Prove a minimal instruction first; compare the full CODER.md only afterward. |
| Pilot mistaken for proof | Require an independent multi-task cohort and prospective analysis before any general claim. |

---

## 8. Final recommendation

Proceed with a same-day failure-derived pilot.

The first experiment should be deliberately small:

1. Recover one checker-sound observed failure, preferably `scout-c-integration-01` if its original assets remain available.
2. Classify the first divergence and decide whether it is truly static-instruction-addressable.
3. Reconstruct it manually in the existing task format.
4. Add `failure-source.json` as integrity-bound private provenance.
5. Test an empty MD against one minimal targeted rule, three attempts per arm.
6. Score correctness with the existing checker and inspect one preregistered mechanism in the trace.
7. Continue only if the treatment causes the predicted behavior change.

This preserves the project’s core investment and stays on the roadmap. It changes the source of meaningful tasks, not the trusted evaluation layer.

The most important distinction is:

> A full proof-of-mechanism can be completed in hours. A credible general claim still requires a held-out cohort.

That is not a weakness. It is the fastest honest way to learn whether this direction deserves further investment.

---

## References

[^1]: Thibaud Gloaguen, Niels Mündler, Mark Müller, Veselin Raychev, and Martin Vechev, “[Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?](https://arxiv.org/abs/2602.11988),” arXiv:2602.11988, 2026. The study reports no significant overall completion benefit, increased exploration and cost, and recommends minimal human-written requirements.

[^2]: Asa Shepard and Jeannie Albrecht, “[Probe-and-Refine Tuning of Repository Guidance for Coding Agents](https://arxiv.org/abs/2606.20512),” arXiv:2606.20512, 2026. The reported comparison was 33.0% mean resolve rate for refined guidance, 28.3% for the initial static knowledge base, and 25.5% for no guidance; the main gain was coverage rather than per-patch precision.

[^3]: Worawalan Chatlatanagulchai et al., “[Agent READMEs: An Empirical Study of Context Files for Agentic Coding](https://arxiv.org/abs/2511.12884),” arXiv:2511.12884, revised August 2026. The authors analyzed 2,303 context files from 1,925 repositories and found that test procedures, implementation details, and architecture were among the most common instruction classes.

[^4]: Jai Lal Lulla et al., “[On the Impact of AGENTS.md Files on the Efficiency of AI Coding Agents](https://arxiv.org/abs/2601.20404),” arXiv:2601.20404, 2026. Across 10 repositories and 124 pull requests, the paper reports 28.64% lower median runtime and 16.58% lower output-token consumption with comparable completion behavior.

[^5]: Carlos E. Jimenez et al., “[SWE-bench: Can Language Models Resolve Real-World GitHub Issues?](https://arxiv.org/abs/2310.06770),” arXiv:2310.06770, 2023. SWE-bench constructed 2,294 repository-level tasks from real GitHub issues and corresponding pull requests.

[^6]: Boxi Yu, Yuxuan Zhu, Pinjia He, and Daniel Kang, “[UTBoost: Rigorous Evaluation of Coding Agents on SWE-Bench](https://arxiv.org/abs/2506.09289),” ACL 2025 / arXiv:2506.09289. The study found insufficient tests in some benchmark instances and identified hundreds of erroneous patches that had been accepted, illustrating why real-task provenance still requires strong independent checking.

[^7]: OpenAI, “[Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/),” 2026. This is a practitioner report rather than a controlled study. It describes treating failures as evidence of missing tools, guardrails, or documentation; replacing a monolithic `AGENTS.md` with a short map and structured knowledge; and enforcing hard constraints mechanically.

[^8]: Internal project document, *Roadmap — Aug 7, 2026*, especially the Stage 0–4 table and the August 20 tooling-coverage note. It defines the sequence “Statistics → Open source + challenges → Paid pilots → Subscriptions → Autoresearch,” identifies PR-to-task mining as an unplanned Stage 1 input mode, and describes the trusted task corpus as part of the Stage 4 moat.

## Evidence note

The 2026 context-file papers are recent and, except where otherwise noted, should be treated as preprints. They motivate the experiment and establish that results are mixed; they do not settle the question. The proposed pilot is designed to test a narrower mechanism with the project’s own controlled infrastructure.
