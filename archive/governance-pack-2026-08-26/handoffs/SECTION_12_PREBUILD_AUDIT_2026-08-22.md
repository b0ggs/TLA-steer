# Section 12 pre-build audit report — 2026-08-22

## Scope and outcome

The single permitted pre-build audit round was completed by three auditors on
2026-08-22. The round returned NO-GO on the original Section 12 draft. This file
records that completed round; it does not perform or authorize another audit.

## Findings and required dispositions

1. A bundled friction decoy could not identify which operational fact failed.
   Require two private decoys, one for wrong-layer editing and one for wrong
   verification, and machine-reject each independently at admission.
2. Admission must remain mechanical. Validate `mechanism.json` structurally and
   enforce the two decoy results in `taskcheck`; do not add semantic review.
3. A null result is uninterpretable if the treatment omits either operational
   fact. Check every declared `required_md_substrings` before queuing the batch;
   permit one fresh blinded re-author after `TREATMENT_UNFAITHFUL`, then stop on
   a second failure.
4. Outcome labels must be mechanical. Derive `ran_real`, `wrong_layer`, and
   `stumble` only from checker booleans, captured commands, capture diff, and
   durations, with the precedence fixed in Section 12.5.
5. Resolve the conflict with Section 11 by superseding its synthetic-cohort ban
   only for this fictional pilot, closing its historical-issue lane, and treating
   Phase 3 as a motivating hypothesis rather than causal evidence.
6. Increase the `tooling/taskcheck.py` cap to 700 lines and grant a separate
   outcome-coding helper of at most 150 lines under `scripts/import/`.
7. Select one balanced alternating arm order from the recorded
   `task_order_seed`, and commit that seed in `REQUEST.json` before launch.

## Closure

All seven dispositions were incorporated in plan commit
`6a6f0dea4d27971998f7ca63e02117238c405088` before pilot activation. Section
12's audit round is therefore closed. No further document audit precedes the
implementation.
