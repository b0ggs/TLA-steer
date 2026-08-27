# Three-auditor review of PLAN_OF_RECORD_2026-08-26.md rev 1

Preserved verbatim from the audit session's report as relayed by Wade,
2026-08-26. Auditors: Euclid (raw runs and statistical claims), Epicurus
(git history and provenance), Gauss (governing documents and addendum
executability). Line references are to plan REV 1, which this report
caused to be superseded by rev 2; rev 1 is recoverable from this file's
findings and from git history once committed.

Verdict: No. Even after approval, a fresh session would hit the plan's
mandatory Step 1 STOP.

## (a) Factual errors

1. "Every admitted task is at ceiling" is false. The ledger contains 23
   distinct admitted task IDs, but only 15 have dev-v2 dispositions; the
   29 dispositions comprise 26 ceiling, two wrong-failure-mode, and one
   invalid. The sealed Real Boltons disposition is 2/3, q=0.888889, not
   ceiling. The findings record also explicitly says not every
   checker-sound task was ceiling, while the final clean handoff limits
   its conclusion to four tasks and rejects a population claim.
   Evidence: plan:14, tasks/ledger.jsonl,
   runs/dev-v2/phase3-real-null-sealed-v1/real-boltons-indexed-slice/null/disposition.json,
   PROCESS_FINDINGS_2026-08-19.md:21, HANDOFF.md:42-44 in
   handoffs/full-handoff-2026-08-25.tar.
2. The existing champion's correctness effect is not "settled." The only
   direct bare-versus-MD comparison used the 3,059-byte SignalNest
   treatment, not the 6,948-byte champion; no dev-v2 request references
   the champion path or hash. Evidence: plan:12,
   COST_AND_WEBSEARCH_ANALYSIS_2026-08-24.md:28,
   controls/pilot/pilot-signalnest-pager.md, targets/coder/champion.md.
3. "~84 sealed attempts, all campaigns" is false. The nine campaigns
   contain 89 launches, 88 event streams, and 87 finalized results.
   Container-bound campaigns account for 53 launches, 52 event streams,
   and 51 results; excluding the evidence-invalid authentication batch
   leaves 48 usable sealed results. The apparent 84 is 48 usable sealed
   plus 36 usable unsealed results. Evidence: runs/dev-v2,
   PROCESS_FINDINGS_2026-08-19.md:523, plan:73.
4. D1 misstates what the August 21 document prohibited. That document
   retained failure-derived task curation and parked only the
   generalized/automated failure factory; it did not broadly prohibit
   failure-derived or governance-failure experimentation. Evidence:
   plan:60, md-eval-project-state-and-way-forward.md:45, :298, :531.
5. D2 records the opposite of the cited Wade addendum. The addendum drops
   the generic champion entirely and specifies bare versus one
   repo-specific MD per repository; the plan reinstates the generic
   champion and defers repo-specific MDs while claiming the corrections
   were incorporated. Evidence: plan:62, plan:79,
   PLAN_REDTEAM_2026-08-26.md:287.
6. Three attempts per arm contradicts the recorded sample-size decision.
   Wade's addendum requires a variance/power-derived, preregistered n;
   the preceding committed handoff proposed five or six attempts per arm
   and explicitly left power review open. Evidence: plan:121,
   PLAN_REDTEAM_2026-08-26.md:303, HANDOFF.md:52-56 in
   handoffs/full-handoff-2026-08-25.tar.
7. D5 conflicts with the last independently preserved direction. The
   August 21 record selects one repository, one MD, and several sealed
   tasks as the next prototype; the same bytes are preserved in the
   committed handoff archive. Evidence: plan:67,
   md-eval-project-state-and-way-forward.md:41, :419, :550, the archive.
8. The "red-team + three-auditor review" pointer is wrong. The cited file
   contains one adversarial reviewer and Wade's addendum. The
   repository's actual three-auditor artifact concerns the unrelated
   Section 12 pre-build audit. Evidence: plan:77,
   PLAN_REDTEAM_2026-08-26.md:1, SECTION_12_PREBUILD_AUDIT_2026-08-22.md:5.
9. .mdseval-codex-home is not the promised session-transcript store. Its
   state_5.sqlite has zero threads and logs_2.sqlite has zero logs; it
   has no sessions directory and contains the real evaluator
   authentication profile. The prior committed handoff explicitly
   excluded that home and its credentials. Evidence: plan:90,
   .mdseval-codex-home, HANDOFF.md:75 in the archive.
10. The referenced companion DEFERRED.md and "Deferred list" do not
    exist. A repository-wide search returns no such file. Evidence:
    plan:47, plan:154.
11. The Step 1 command is not a valid CLI invocation. The subcommand is
    queue; queue_request is only an internal Python function. The CLI
    exposes only queue, run, and verify. Evidence: plan:107,
    run_batch.py:579.
12. Price-weighted tokens are not computable from the named evidence. No
    price schedule or backend fingerprint is preserved; the repository's
    own cost analysis says the evidence supports token/time descriptions,
    not dollar costs. Evidence: plan:123,
    COST_AND_WEBSEARCH_ANALYSIS_2026-08-24.md:46, :529.

## (b) Internal contradictions

1. Step 1 violates I3. I3 permits only deletion, archiving, or shortening
   and forbids creating a new process or gate; Step 1 creates a
   pre-commit enforcement gate. Evidence: I3 (plan:34), Step 1 (plan:101).
2. Step 3 violates I5. I5 says only live-call spend waits on a human and
   nothing else does; Step 3 requires Wade's decision and blocks all
   further work pending it. Evidence: I5 (plan:41), Step 3 (plan:146).
3. Step 3 violates I7. I7 requires every step to have a time or size cap;
   Step 3 has neither. Evidence: I7 (plan:45), Step 3 (plan:146).
4. The authority-transfer sequence violates I4. Step 0.5 claims sole
   authority immediately, but the AGENTS rewrite is deferred to Step 1;
   current AGENTS.md still names TASK_TOOLING_V2_PLAN.md as sole
   authority, and that plan expressly requires an atomic AGENTS edit to
   avoid this exact split-authority window. Evidence: Step 0.5 (plan:94),
   Step 1 (plan:101), AGENTS.md:9, TASK_TOOLING_V2_PLAN.md:10.
5. The Step 2a arms violate I1's reuse-only/unmodified-runner rule. The
   runner and verifier accept arm files only below controls/, so
   targets/coder/champion.md is rejected; the runner also always writes
   an MD file, so literal "bare (no MD)" is unsupported. Remedying either
   requires a new control artifact or runner/tooling changes. Evidence:
   I1 (plan:28), arm specification (plan:121), run_batch.py:115,
   taskcheck.py:379, run_batch.py:245.
6. The required time-to-first metrics violate I1's no-instrumentation
   rule. Across 88 event streams and 4,032 JSON events, none has a
   timestamp field. The process layer buffers the entire subject stream
   with communicate(), and the runner writes it only after completion;
   time-to-first-edit/action cannot be reconstructed offline. Evidence:
   Step 2a (plan:123), Step 2b (plan:136), processutils.py:47,
   run_batch.py:312, runs/dev-v2.
7. Step 2b simultaneously prohibits and permits taxonomy expansion.
   Evidence: plan:141.

## (c) Recommendations

- Enumerate the exact Step 1 archive and tombstone paths.
- Name every sub-agent deliverable path before launch.
- Specify a verifiable Wade-authorship mechanism and the hook
  installation path.
- State whether Step 2a is sealed or host-run and identify the applicable
  combined preflight specification.
- Use capture.json and diff.patch as the edit-scope evidence sources.
- Pre-register a compliance rubric for conflicts between the champion and
  the subject wrapper.
- State that the optional 900-second timeout is batch-global and give
  both possible request sizes.
- Pre-register timeout, missing-usage, task-blocking, and aggregation
  policies.
- Name the batch ID, seed, evaluator profile, container configuration,
  and complete CLI invocation.
- Define when Step 2b's three-day clock begins relative to approval and
  batch completion.
- Designate either TAXONOMY.md or TAXONOMY_REVISED.md as canonical.
- Preserve the claimed Wade decisions and auditor outputs as independent
  artifacts before supersession.
- Exclude volatile .mdseval-codex-home/tmp paths from full-repository
  copy tests; the required suite currently ran 216 tests with 6 copy
  errors and 6 skips.

## Executability

No. Before approval, the document is explicitly a draft and authorizes
nothing beyond Step 0. After approval, the exact blockers are:

- The prescribed queue_request command does not exist.
- Correcting it to queue still rejects targets/coder/champion.md, so
  Step 1's only acceptance test mandates STOP.
- Literal no-MD execution and time-to-first metrics require runner
  instrumentation forbidden by I1.
- Price weights, the Deferred file, and the actual transcript-store paths
  are absent.
- Steps 0.5, 1, and 3 cannot simultaneously satisfy I3, I4, I5, and I7.

The repository was not modified by the audit.
