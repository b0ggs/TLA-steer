# PROPOSAL: Task Factory v2 (not an active plan; supersedes nothing until adopted)

Goal: produce 120 validated omission-sensitive tasks in days, not months, keeping the
gates that caught real defects and deleting the ceremony that caused every stall.

## What today proved
- The defect-catching gates are cheap and automatable: a contract-only blind solve
  accepted by the frozen checker, plus per-requirement omission mutants.
- Authoring + blind validation of one task ≈ 20–30 min of agent time, fully parallel.
- Every stall in the current system came from serialization and bookkeeping:
  single gatekeeper, one mutable candidate at a time, role-rotation rows, repeated
  re-hashing, artifacts held in chat context (Candidate 4 was lost to compaction).

## Pipeline (per task; run N lanes in parallel, N = 8–10)
1. AUTHOR   — agent gets only the frozen recipe spec + checker-pathology checklist.
              Writes public/, check.py, reference/, NOTES.md to disk immediately.
2. SELF-TEST— script (no agent): checker vs public (must fail all R), vs reference
              (must resolve), auto-generate omission mutants (revert one deliverable
              each from reference), verify each mutant fails exactly its own R.
3. BLIND    — separate agent sees ONLY public/. Solves. Script runs frozen checker
              against the blind solution. Reject task on any failure not traceable
              to public text. (This is the gate that killed rolling candidates 1–2.)
4. FREEZE   — one hashing script emits a single manifest.json per task (all file
              SHA-256s, requirement map, mutant results, blind-solve verdict).
              Git commit per BATCH of tasks, not per candidate.
5. CALIBRATE— live null attempts in 3-call lots per task, batched across tasks.
              Label promising / ceiling / floor. Denominators preserved; no retries;
              frozen bytes after exposure. (Unchanged from current rules — this part
              was never the problem.)

## Kept from the current system (the parts that worked)
- Author/solver information isolation (enforced by prompt scoping, not packets).
- Frozen-at-exposure bytes; no post-exposure edits; preserved raw evidence.
- Objective checkers, stdlib-only, outside the workspace; canonical JSON output.
- The promising-band definition and labels.

## Deleted (with the failure each caused)
- Single gatekeeper / one-mutable-candidate rule        → serialization stalls
- Role-rotation rows and per-role authorization records → triple blind solves
- Per-candidate chat approvals                          → hour-long waits on the user
- Conversation-held artifacts                           → Candidate 4 lost to compaction
- Narrative receipts and repeated re-hashing            → 30+ min admission per task
- Terminal stops for pre-exposure issues                → the dead week of Aug 10–13
  (pre-exposure failures are repaired and retried, per AGENTS.md's own rule)

## Throughput estimate
- Offline: 10 lanes × ~25 min/task → ~20–30 validated tasks/day. 120 tasks ≈ 4–6 days.
- Live: 120 × 3 = 360 calibration calls (comparable to the 258 already spent).
- Expected attrition: build ~180 to keep 120 (blind-gate rejects + wrong-band labels).

## Gate before scaling
Do NOT start the 120 until the current campaign's Candidates 5/6 return live labels.
- If either is promising: recipe confirmed; scale with this factory.
- If both ceiling: raise omission pressure (less tag salience, more files/requirements)
  on 3–5 factory tasks and re-test with 9–15 live calls before committing to 120.

## Contamination note
Factory authors are agents scoped to the recipe spec only (no campaign outcomes),
which satisfies the development/confirmatory boundary better than human-mediated
packets did. The confirmatory experiment (bare vs coder.md comparison) keeps the
existing evidence machinery — that machinery was sound; only task production moves
to the factory.
