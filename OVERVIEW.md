# MD Eval

MD Eval tests whether repository instructions such as `CODER.md` or
`AGENTS.md` improve a coding agent's task completion. It runs the same model on
the same coding tasks under different instruction conditions, scores observable
results, and preserves the evidence behind each comparison.

It answers two questions:

1. Does the current instruction file produce a higher task-success rate than an
   empty control file?
2. Does a proposed replacement produce a higher success rate than the current
   file without causing regressions?

MD Eval evaluates instruction files. It does not optimize them yet. Future
iterations will add hill climbing.

Task development and confirmatory experiments use separate workflows.
Development results are exploratory and are labeled accordingly.
A larger raw pass count is not enough. The comparator reports a winner only
when enough tasks show a difference, the exact significance test passes, and
the mean difference clears the effect-size threshold.

## System at a glance

```text
+------------------------------------------------------------+
| 1. BUILD                                                   |
| Public task + checker + reference + blind solution         |
+------------------------------------------------------------+
                               |
                               v
+------------------------------------------------------------+
| 2. VALIDATE                                                |
| taskcheck.py checks the task and records its hashes        |
+------------------------------------------------------------+
                               |
                               v
+------------------------------------------------------------+
| 3. APPROVE                                                 |
| REQUEST.json must match the hash in APPROVED.json          |
+------------------------------------------------------------+
                               |
                               v
+------------------------------------------------------------+
| 4. RUN                                                     |
| run_batch.py creates a fresh workspace per attempt         |
+------------------------------------------------------------+
                               |
                               v
+------------------------------------------------------------+
| 5. SCORE AND VERIFY                                        |
| check.py scores. Ledgers make changes detectable           |
+------------------------------------------------------------+
                               |
                               v
+------------------------------------------------------------+
| 6. TEST AND DECIDE                                         |
| compare.py runs an exact two-sided sign test               |
| Significance and an effect threshold are both required     |
| A_BETTER | B_BETTER | INCONCLUSIVE | INVALID               |
+------------------------------------------------------------+
```

## How the confirmatory experiment establishes significance

After a no-MD calibration screens out tasks the bare model always solves, MD
Eval compares the MD against no MD on 16 independently sourced tasks, with four
fresh runs per condition on each task. The MD is considered beneficial only if
it improves task success by at least 20 percentage points and the exact paired
test yields `p <= 0.05` (`n = 16` tasks, 128 scored runs).

So far, every clean task cohort has hit the bare-model ceiling. No cohort has
qualified for the paired significance test.

## How each stage works

1. **Build a task.** A task pairs the public repository and acceptance criteria
   with an external checker, a known-correct reference, and a blind solution
   made from a copy of the public task. The blind solver and its input are
   recorded. `tooling/taskgen.py` and `tooling/blindsolve.py` can help, but
   `tooling/taskcheck.py` must validate the result.

2. **Validate the task.** `taskcheck.py` checks that the untouched task fails
   while its existing behavior still works, both known solutions pass, scoring
   is repeatable, and a dummy instruction file does not affect the checker. It
   also validates per-requirement omission probes. Admission records file
   hashes in a manifest and ledger. The task remains repairable until its first
   recorded exposure. After that it is immutable, and any repair gets a new ID.

3. **Approve a batch.** `scripts/run_batch.py queue` writes a `REQUEST.json`
   that binds the task and instruction-file hashes, runner settings, order seed,
   and call limit. Live calls cannot start until an `APPROVED.json` names the
   exact request hash.

4. **Run one or two conditions.** Calibration batches test one condition.
   Comparison batches test two. The runner tries to collect three usable
   attempts per task and condition. Each starts in a fresh workspace with the
   named instruction file injected. Comparisons hold the task, model, and
   settings constant and alternate execution order. Evidence includes the event
   stream, final response, patch, timing, reported token use, and checker result.
   A new attempt cannot overwrite earlier evidence.

5. **Score and verify.** The external `check.py` reports requirements,
   regressions, and an overall pass. It runs twice against the finished tree.
   Disagreement invalidates the attempt. `run_batch.py verify` checks hashes,
   manifests, per-task summaries, and the evidence ledger. Correctness is
   mechanical. No LLM judge can override a failed check.

6. **Compare conditions.** `tooling/compare.py` reads the per-task
   `disposition.json` summaries and never re-scores an attempt. For each task it
   compares the number of passing attempts in conditions A and B, then applies
   the statistical decision rule above.

The ledgers detect accidental drift and provide an audit trail. They are not an
unforgeable security boundary. Task admissions are also recorded in Git.

## Current status

Host-based comparisons work today. Docker-backed single-condition runs also
work, but `tooling/compare.py` cannot yet process the additional metadata from a
Docker-backed paired batch. Its reports cannot, on their own, justify keeping
or replacing an instruction file. That decision requires the confirmatory
machinery described in [README.md](README.md).

Recent development runs show that most tested tasks are too easy for this
model. Most batches in `runs/dev-v2/` are single-condition calibrations. In
`maximum-difficulty-search-disabled-v2`, a sealed, search-disabled control
batch, all 12 `gpt-5.6-sol` workspaces across four full-repository tasks passed
their checks, including three where the model process later reached its time
limit. The only direct control-versus-instruction pilot was unsealed and covered
one task. Both conditions passed all three attempts. Its token and runtime
differences did not stand apart from variation among repeated control runs.
Because that pilot had one tied task and no non-tied tasks, it could not reach
the minimum effective sample. It provides no statistical evidence of a
difference between the conditions.

These local results do not show that instruction files never help. They show
that these recent cohorts left little room to measure a correctness gain. A
credible comparison needs tasks with repeatable failures that a good instruction
file could plausibly prevent.

## Repository map

- `tasks/`: task packages, admission manifests, and exposure records
- `controls/`: instruction files used as development conditions
- `tooling/`: task generation, blind solving, admission, and comparison
- `scripts/run_batch.py`: batch queueing, execution, and verification
- `scripts/contain/`: optional sealed Docker execution
- `runs/dev-v2/`: preserved development requests, attempts, and ledgers
- `src/mdseval/`: shared runtime and evidence code, plus the retained
  confirmatory evaluator
- `experiments/`, `evals/`: confirmatory definitions and qualification material
- `tests/`: offline tests with no live model calls

For task formats and commands, see [tooling/README.md](tooling/README.md). The
historical task-development plan is archived at
[TASK_TOOLING_V2_PLAN.md](archive/governance-pack-2026-08-26/TASK_TOOLING_V2_PLAN.md).
