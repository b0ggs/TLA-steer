# Process-failure experiment designs

Status: zero-spend design input for Wade. No experiment was run, and this note
reports no instruction effect. The designs reuse preserved repository snapshots,
run captures, and existing acceptance commands; they add no task, checker,
taxonomy, platform, or enforcement mechanism.

## Evidence basis

- `handoffs/PROCESS_FINDINGS_2026-08-19.md` records the observed development
  bottleneck: repeated reviews and blind solves, narrative receipts, terminal
  stops, and hours of candidate consumption despite mechanically fast production.
- The Section 12 git sequence makes planning, review, implementation, and result
  bytes separately inspectable. In particular, commits `e5a0e5c`, `6a6f0de`,
  `505c7d4`, and `45ada03` record a 92-line plan addition, a 58-insertion/19-deletion
  revision, a 36-line audit-closure document, and a 144-line mechanical
  implementation. The later result is preserved at
  `runs/dev-v2/pilot-signalnest-pager-v1/`.
- The Section 13 sequence provides a second specimen: commits `fc73eab`,
  `90ebf50`, `03485ac`, and `b4eb836` record plan/review growth before the
  implementation at `db25419`. This history shows that plan text and product
  changes can be counted independently; it does not establish that either was
  unnecessary.
- Existing attempt evidence already contains the needed raw material. For
  example,
  `runs/dev-v2/maximum-difficulty-search-disabled-v2/full-boltons-wraps-forwarding/null/attempt-1/capture.json`
  records tracked and untracked changed paths and bytes, while `checker.json`
  and `result.json` record mechanical completion. Git preserves the equivalent
  before/after bytes for repository-level work.

## Mechanically computable outcomes

Each historical specimen would have a baseline commit, a literal set `P` of
requested product paths, and one or more already-existing acceptance commands
recorded before arm assignment. The instruction file itself would sit outside
the measured worktree. Given baseline bytes `B(path)` and final bytes `F(path)`,
with an absent file represented by zero bytes:

1. **Off-task touched bytes.** For every regular file outside `P` whose bytes
   changed, sum `len(B(path)) + len(F(path))`. This counts edits, additions, and
   deletions, including untracked outputs, without deciding what kind of mistake
   a file represents. Lower is less off-task footprint.
2. **Unrequested Markdown growth.** Across every `*.md` path outside `P`, sum
   `max(0, len(F(path)) - len(B(path)))`. This directly captures added
   instruction/plan-like text while avoiding a semantic document classifier.
3. **Requested-product completion.** Report `1` only when every requested output
   path exists and every pre-recorded acceptance command exits zero; otherwise
   report `0`, alongside the individual exit codes. No qualitative judgment
   changes this outcome.

The three values remain separate. In particular, completion does not cancel an
off-task footprint, and a small diff does not compensate for failed completion.

## Short controlled designs

### 1. Bounded implementation replay

Two or three implementation slices would be copied from clean historical parent
commits, using only the problem text and acceptance commands preserved at those
commits. The Section 13 sealed-runtime slice ending at `db25419` is one available
source. Each slice would receive either a zero-byte instruction file or one short
general scope-and-stop instruction, with the model, runtime, work order, starting
bytes, and attempt count held fixed and arm order randomized. The three outcomes
above would be calculated per attempt and compared as paired descriptive values.

### 2. Optional-review pressure

The same clean implementation slices would receive the same short, optional
review paragraph drawn from the preserved Section 12 or Section 13 review record.
Both arms would see identical review text and the same explicit product paths;
only the instruction file would differ. This isolates whether the instruction
changes requested-product completion or turns advisory review material into extra
repository and Markdown bytes.

### 3. Already-complete stop condition

A snapshot immediately after a preserved implementation and its passing existing
acceptance commands would receive the corresponding historical work order phrased
as a request to finish and verify it. Since completion is true at baseline, a
no-change result remains mechanically valid. The paired arms would show whether
the instruction changes unnecessary touched bytes or Markdown growth while
preserving the passing completion result.

These are candidate designs, not a queued phase. Git and run evidence support the
measurements and specimen selection; only a future controlled comparison could
support a claim about instruction-file effects.
