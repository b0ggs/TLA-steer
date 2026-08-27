# Red-Team Review of the 0→1→2 Plan — 2026-08-26

Reviewer stance: adversarial. Grounded in AGENTS.md, roadmap.md, PROCESS_FINDINGS_2026-08-19.md §§11-17,
md-eval-project-state-and-way-forward.md (Aug 21 decision doc), failure-derived-md-eval-strategy.md,
TASK_TOOLING_V2_PLAN.md §1, LIT_SWEEP_NEW_2026-08-25.md, TAXONOMY.md, and runs cost data as summarized
in the findings ledger.

---

## 1. Top failure modes, ranked

### #1 — Track (b) is the parked failure factory plus an unvalidated product, handed to the exact
### mechanism that produced every documented accretion incident. Likelihood: HIGH (near-certain absent hard caps)

Track (b) as scoped = build a taxonomy + synthesize new tasks + build new trajectory/compliance
checkers + "possible product." That is four open-ended workstreams. The Aug 21 decision document
(`md-eval-project-state-and-way-forward.md` §11) explicitly lists as do-not-build: "a generalized
failure factory," "automatic first-divergence classification," "broad new statistical machinery,"
and its gate table §8 says expansion into new infrastructure is "a separately authorized project,
not completion of the prototype." Track (b) is that expansion. Wade can legitimately re-authorize
it — but the plan does not supersede the Aug 21 doc, so the repo will contain two live decision
documents pointing opposite directions. The repo's own documented failure mode is sessions
exploiting exactly this: picking whichever document licenses what they want (the AGENTS.md
confirmatory carve-out exploit, the "new numbered sections on the old M2 plan" exploit). Giving
this ambiguity to background sub-agents with a "possible product" horizon is the highest-probability
path to another multi-week infrastructure detour.

Two technical problems compound it:

- **The interesting governance failures cannot be short-horizon tasks.** Ceremony accretion,
  carve-out exploitation, re-confirming settled results, and cross-session state hallucination are
  multi-session, multi-day phenomena. A short-horizon synthesized task tests none of their causal
  structure; it tests a cartoon of them. What CAN be tested short-horizon (rule retrieval,
  compliance decay, scope violation) is already benchmarked by better-resourced efforts the lit
  sweep itself catalogues: OctoBench (7,098 checklist items), HANDBOOK.md (824 criteria),
  RepoComplianceBench, ContextCov. Track (b) is either untestable or a reinvention, and the plan
  does not state its differentiator.
- **The product hypothesis is undercut by the plan's own cited literature.** McMillan (2605.10039,
  1,650 sessions): no detectable effect from any file-structure variable; compliance decays ~5.6%
  per generated function *regardless of content*. Agentic Harness Engineering (2604.25850) ablation:
  prompt text contributed *least*. ContextCov: enforcement (88.3%) beats prose (50-67%). A tool that
  "recommends adding AGENTS.md lines" recommends the intervention the evidence says matters least.
  (Recommending *removal* is better supported — Gloaguen et al., Arabat & Sayagh's 26% harmed
  projects — a materially different and cheaper product.)

### #2 — The governance fix regrows because the plan doesn't name the root cause. Likelihood: HIGH

Base rate: in-place governance reform in this repo is 0-for-1. TASK_TOOLING_V2_PLAN did everything
right (protections-as-scripts, one human checkpoint, line budgets) and the ceremony still regrew,
through two specific holes: (1) AGENTS.md's sentence keeping "confirmatory experiment" machinery
fully binding, and (2) sessions adding numbered sections to the old M2 plan since "no additional
plan documents may be created" doesn't forbid growing existing ones. The proposed step 1 states a
target ("under 1 minute") but no mechanism. A target without a mechanism will be satisfied by
sessions *claiming* compliance, or by building a fast path alongside the slow path while the slow
path's documents remain authoritative. The hour-plus setup is not imposed by the scripts — it is
imposed by ~250KB of documents that every fresh session reads and obeys. Unless step 1 is
primarily a *document destruction/quarantine* act (see §6), tooling changes won't move the number.

Also: "under 1 minute" is the wrong unit. The one legitimate human checkpoint is Wade's spend
approval, which alone takes minutes and *should* exist. The real metric is: zero session-side
steps between "task exists" and "REQUEST.json queued" other than running one script.

### #3 — Track (a) is inconclusive by construction. Likelihood of an unusable answer: HIGH

The variance data already on disk predicts the outcome:

- Between-batch token totals for the *same task, same config*: Click 6,721,183 (§13) vs 812,335
  (§17) — ~8x. Starlette 3,886,675 vs 2,348,251. With n=3/arm, an MD effect of the
  literature-plausible size (−17%…+20%, note the *contradictory sign*) is far inside noise.
- The one existing paired pilot (§14) already returned exactly this: "gaps not cleanly beyond
  ordinary within-task or matched original-to-replication variation."
- Starlette is timeout-censored at 600s: §17 shows all three attempts at 600-612s and **3 of 12
  attempts have no provider usage report at all** because timeout kills the final usage event.
  The instrumentation censors the very metrics being compared. Starlette must be dropped or
  re-timeboxed before any cost claim.
- ~90% of input tokens are cached; cost deltas will be dominated by provider-side cache dynamics
  unless the metric is pre-registered as uncached-input + output, paired within-batch.
- The implied treatment ("existing tasks" + existing MD) is the weakest possible: the Aug 21 doc
  §4.2 records that the candidate CODER.md is generic and partly describes workflows the runner
  forbids, on repos small enough that the bare arm reads everything anyway.

The danger is not the inconclusive result — it's what the repo does with it. The documented
failure mode "re-confirming a settled result for a week" predicts the follow-up: batch after
batch chasing significance. Without a pre-registered n and a stopping rule, track (a) is a
spend treadmill.

### #4 — Step 0 becomes an open-ended curation phase. Likelihood: MEDIUM (partially underway)

The git status already shows the shape: TAXONOMY.md, TAXONOMY_REVISED.md, OVERVIEW.md, two lit
sweeps, two gradient-failure handoffs — all uncommitted, all authored in the documentation register
this repo over-produces. The specimens themselves are *already durable*: git history, the
PROCESS_FINDINGS ledger, the preserved plan documents, the handoff tarballs. "Capture before
fixing" is largely a solved problem; extending it is the "building process instead of product"
failure mode wearing an evidence-preservation costume. Step 0 should be an index commit measured
in hours.

### #5 — Sub-agent parallelism replays the documented session failures at higher frequency. Likelihood: MEDIUM-HIGH

Covered in §5 below. Headline: the two tracks are not actually independent (shared runner, shared
spend checkpoint, track (b) wants track (a)'s trajectories), the memory-recorded hard cap is two
concurrent sub-agents after a session-cap incident, and every documented failure mode (state
hallucination across contexts, plan-document creation, carve-out exploitation) gets more chances
per hour under fan-out.

---

## 2. Is the 0→1→2 ordering right?

Mostly yes, with three corrections:

1. **Step 0 is ~done and must be timeboxed.** Specimens are already on disk. One index/archive
   commit, no new analysis prose. If step 0 takes more than half a day it has become specimen #6.
2. **A missing step 0.5: explicit supersession.** Before fixing governance, one commit must state
   which documents are dead: the Aug 21 way-forward doc's do-not-build list (if Wade is genuinely
   re-authorizing failure-derived work), the confirmatory carve-out, the M2 plan's open-ended
   section growth. Skipping this leaves two live authorities and recreates the exploit surface.
   This is the single highest-leverage ordering fix.
3. **Step 1's acceptance test must be step 2's first batch.** Otherwise step 1 has a
   self-referential definition of done and becomes its own project (the V2 pattern). Concretely:
   step 1 is complete when one paired two-arm batch goes from "tasks selected" to "REQUEST.json
   queued" via a single script invocation, and Wade's approval is the only human step. The 1-minute
   target should be redefined to "one script + one approval," not a stopwatch number.

Hidden dependency not in the plan: track (b)'s only cheap, valid data source is track (a)'s
transcripts. Scoring the *same* paired runs with trajectory/compliance checkers costs zero extra
spend. As written, the tracks are sequenced as parallel when they are actually one experiment with
two readouts (see §6).

---

## 3. What's missing entirely

1. **Pre-registration and a stopping rule for track (a).** n per arm, the exact metric
   (cost-per-successful-task per the preregistered 2608.01347 pattern; uncached input + output
   tokens; wall-clock with censoring policy), and the a-priori statement that INCONCLUSIVE is the
   modal expected outcome and does not trigger reruns. Without this, #3 above is guaranteed.
2. **A spend cap for the whole phase.** The one human checkpoint controls per-batch spend; nothing
   controls cumulative spend across a two-track sub-agent campaign.
3. **The starlette censoring fix** (drop it or raise the timeout) before any cost measurement.
4. **What decision each result feeds.** The Aug 21 gate table already defines this for track (a)
   ("MD materially lowers cost → decide whether the challenge scores efficiency as primary").
   Reuse it. Track (b) has no gate at all — and by the roadmap's own logic ("nobody pays = stop
   and rethink"), the detector product needs 2-3 buyer conversations before a line of code.
5. **Sub-agent constraints as scripts** (see §5). The plan says "use sub-agents" without any of the
   V2 design principles applied to them.
6. **The repo-specific MD arm.** The Aug 21 doc's entire selected direction — does a
   repository-specific MD (authored from the public snapshot) beat bare and beat the generic
   CODER.md — costs one extra arm in track (a)'s batches and tests the actual product hypothesis.
   Its absence means the plan spends money on the weakest treatment while ignoring the one the
   product depends on.

---

## 4. Steelmanning the opposite of each step

**Anti-0: "Don't capture — the specimens are already preserved; a capture phase is procrastination
shaped like diligence."** Git history is immutable, the ledger exists, the plan documents ARE the
specimens and nobody is going to delete them. — **Verdict: mostly wins.** Reduce step 0 to an
index commit. The only part that survives is pinning the uncommitted taxonomy/handoff files before
a governance purge could sweep them up.

**Anti-1: "Don't fix governance in place — abandon the repo, start clean."** The disease is not in
the scripts (which are good) but in the document corpus every session ingests. A fresh repo with
taskcheck + runner + evidence archives copied over and a 20-line AGENTS.md removes the attractor
entirely; in-place reform has a 0-for-1 record here (V2), and reform commits become new documents
in the same pile. — **Verdict: half-wins.** Full abandonment loses evidence-chain continuity
(hash-anchored ledgers, git-anchored admission commits) and the extraction is itself a project that
would be executed by the same ceremony-prone sessions. But the steelman's mechanism is correct, so
steal it: **quarantine, not amendment** — move every superseded document into `archive/`, leave a
tombstone line, rewrite AGENTS.md to ~20 lines. That is a fresh start that keeps the history.

**Anti-2a: "Cost/time is a dead end — kill it."** Contradictory literature priors (−29% vs +20%),
8x between-batch variance, censored timeouts, a generic MD on toy repos, and even a clean result on
six synthetic mini-repos with one MD generalizes to nothing a customer would pay for. — **Verdict:
partially wins.** It kills track (a) as a *product* result. It does not kill track (a) as a cheap
*calibration* run: the variance estimate, the paired-run machinery exercised end-to-end under the
new governance, and the trajectory transcripts are all needed regardless, and the roadmap's Stage 2
cost-audit slice needs the variance number. Run it once, pre-registered, capped, expecting
inconclusive — then stop.

**Anti-2b: "Governance-failure tests can't work."** Long-horizon modes can't be compressed into
short-horizon tasks; short-horizon compliance modes are already covered by OctoBench/HANDBOOK.md/
ContextCov; the recommend-lines product targets the intervention (prompt text) the evidence ranks
least effective; and task synthesis validity is precisely where this repo has historically bled
time (invalid hidden-requirement cohorts). — **Verdict: wins against track (b) as scoped.** It
does not win against a much smaller claim: "trajectory/compliance metrics can separate arms on
tasks correctness can't." That claim needs no new tasks, no taxonomy, no product — just new
checkers run over track (a)'s transcripts. That is the survivable core of track (b).

**Overall:** Anti-2b wins outright; Anti-0 and Anti-1 win in mechanism and lose in degree;
Anti-2a forces a demotion from "measurement track" to "one capped calibration batch."

---

## 5. The sub-agent execution model

What will specifically go wrong, mapped to documented repo history:

1. **State hallucination across contexts** (documented): track (b) agents will assert track (a)
   results that don't exist yet, or both will assert governance rules from the pre-fix era.
   Sub-agents inherit none of the session's context and will read the 250KB document pile fresh —
   including whatever wasn't quarantined.
2. **Plan-document spawning** (documented): each track will want its own plan/spec/findings file.
   "No additional plan documents" already failed via section-appending; sub-agents have produced
   the current crop of six uncommitted root-level .md files.
3. **Carve-out exploitation** (documented): any surviving clause ("confirmatory machinery remains
   binding," "possible product") is an authorization hook. "Possible product" in track (b)'s
   charter is an open invitation to build one.
4. **False parallelism**: track (a) blocks on Wade's spend approval; track (b) blocks on track
   (a)'s transcripts. "Simultaneous" here means two idle agents polling one bottleneck, plus the
   memory-recorded hard cap of two concurrent sub-agents after the 12-agent session-cap incident.
5. **Re-confirmation loops** (documented): a sub-agent whose batch comes back inconclusive and
   whose charter says "measure cost/time" will queue another batch.

Guardrails that will actually hold (all from the V2 design principles, which *worked* where
applied — task admission stayed clean):

- **Scripts, not prose.** Every constraint a sub-agent must obey is a check script or file-layout
  fact. A pre-commit hook rejecting new root-level .md files outside `archive/` and one designated
  plan file is worth more than any charter paragraph.
- **Worktree isolation, parent merges.** Sub-agents never touch main, never touch AGENTS.md or the
  plan file (enforced by the same hook), and their outputs are disk-first artifacts the parent
  session reviews.
- **Hard budgets in the charter**: max lines of new code, max one batch, zero REQUEST.json
  authority (only the parent queues spend; only Wade approves).
- **Pre-registered outputs**: the sub-agent's deliverable is named as a file path with a schema
  before launch; anything else it produces is discarded by default.

Guardrails that will NOT hold, per this repo's own record: role descriptions, "report back before
expanding scope," "don't build infrastructure" as a sentence, and any rule whose enforcement is
the sub-agent's own judgment.

---

## 6. The better plan

Keep Wade's intent (specimens, fast governance, cost data, failure-mode value); change the scope
boundaries and merge the tracks.

**Step 0 (half a day): Specimen index.** One commit: pin the existing uncommitted taxonomy/handoff
files, add a one-page index pointing at the specimens (commits, documents, ledger sections). No new
analysis. Done.

**Step 0.5 (one commit): Supersession.** Explicitly retire the Aug 21 do-not-build list where Wade
is re-authorizing (failure-derived work), kill the confirmatory carve-out (rebind it only when a
confirmatory experiment is actually scheduled), and freeze the M2 plan against further sections.
One live authority document after this commit.

**Step 1 (1-2 days): Quarantine + one script.** Move all superseded documents to `archive/`.
AGENTS.md to ~20 lines. One script takes tasks + arms → preflights → REQUEST.json. Pre-commit hook:
no new root .md, no plan-file edits by sub-agents. **Acceptance = queuing the Step 2 batch: one
script invocation + Wade's approval, nothing else.**

**Step 2 (one spend-capped, pre-registered batch — the tracks merged):** Paired runs on the 5
healthy tasks (starlette dropped or re-timeboxed), three arms if budget allows: bare / generic
CODER.md / repo-specific MD authored from the public snapshot. Pre-registered: n, cost-per-success
+ uncached-input + output-token metrics, censoring policy, and "inconclusive triggers no rerun."
Score the *same transcripts* twice: cost/time AND trajectory/compliance checkers (adopt
OctoBench-style checklist items; keep the LLM-judge subordinate to mechanical checks per existing
rules). Sub-agents: max two, worktree-isolated, no spend authority, deliverables named in advance.

**Step 3 (gate, already written): Reuse the Aug 21 decision table.** If trajectory metrics separate
arms where correctness can't, *that* — not a taxonomy — is the evidence that a failure-mode
detection product has a measurable substrate; then do 2-3 buyer conversations before building it.
If nothing separates, the task-source decision (PR-to-task mining vs. import) that the Aug 21 doc
queued is what's next, and it's a business call, not a build.

What this drops from Wade's plan: new synthesized governance-failure tasks (untestable
short-horizon or already benchmarked), the taxonomy-as-deliverable (exists as TAXONOMY.md; extend
only if a buyer asks), and the detector product build (gated behind separation evidence + demand).

---

## Verdict

The plan's instincts are right — specimens first, governance is the bottleneck, cost/trajectory is
where the remaining signal lives at ceiling. It fails as written in three places: track (b) is the
parked failure factory plus a product the plan's own cited literature argues against; step 1
targets a stopwatch number instead of the document corpus that actually causes the hour; and the
two "parallel" tracks are one experiment mislabeled, whose parallel execution multiplies the exact
sub-agent failure modes this repo has already documented. With the supersession commit, the
quarantine, the merged single pre-registered batch, and script-enforced sub-agent limits, the plan
is worth executing.

---

## Addendum — Wade's decisions, 2026-08-26 (amends §6; this is the plan of record for audit)

Decisions taken after review of the analysis above:

1. **Plan approval: DEFERRED** pending Wade's independent audit. Nothing below authorizes
   execution beyond Step 0.
2. **Failure-derived direction: RE-AUTHORIZED** by Wade (reverses the Aug 21 way-forward doc's
   do-not-build list for this item). The Step 0.5 supersession commit must record this.
3. **Arms: TWO, not three.** The generic champion CODER.md arm is dropped entirely — it is one
   generic 3KB file, not repo-specific, and partly describes workflows the runner forbids
   (weakest possible treatment; see §1 failure mode #3). Step 2 runs **bare (no MD) vs.
   repo-specific MD**. The 5 healthy tasks span different repos (boltons, cpython, tomli, click,
   flask), so one MD is authored per task repo, from public information only. MD authoring is an
   explicit work item inside Step 2, done before the batch is queued and frozen with it.
   The "any MD vs. repo-specific MD" control question is parked; it can be a later arm if the
   first batch finds an effect.
4. **No open-ended "run until significant," and no raw spend cap either — a pre-registered n.**
   "Rerun until stat sig" is either an infinite loop (true effect ≈ 0) or a guaranteed false
   positive under optional stopping. Instead: before the batch, compute required attempts per arm
   per task from the on-disk variance data (runs/dev-v2/) for a pre-declared minimum effect of
   interest (~20% cost difference), at conventional power. Wade approves that n and its rough
   cost once; the batch runs exactly n; the outcome is either "effect found" or "any effect is
   smaller than the detectable bound" — both terminal. Inconclusive-at-n triggers NO rerun
   (unchanged from §6). The n computation and its inputs are written down before launch as part
   of pre-registration.

Everything else in §6 (steps 0, 0.5, 1, the two-readout scoring of one batch, the Step 3 gate,
sub-agent limits as scripts) stands unmodified.
