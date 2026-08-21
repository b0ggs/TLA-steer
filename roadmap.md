# Roadmap — Aug 7, 2026

**Stats → Open source + challenges → Paid pilots → Subscriptions → Autoresearch**

| # | Stage | Time | Build | Gate to next stage |
|---|---|---|---|---|
| 0 | **Statistics** | 2–3 wks | Repeated paired runs, A/A calibration, "inconclusive" output. Stop SF2. Run private PD pilot (20 games, one afternoon). | A/A intervals calibrated. PD result known. |
| 1 | **Open source + MD challenges** | ~1 mo | Release engine + public packs. Keep PR-to-task mining closed. Challenges: coder.md / agent.md on Kimi (label corpus by model). PD challenge only if pilot hit, MD division only, turn-based, sealed scoring. Champion video = marketing. | Participation ≥ N (set N before launch). Corpus growing. |
| 2 | **Paid pilots (Harness Eval)** | ~1 qtr | Private packs from customer repos. Compare harnesses. Include cheap Cost Audit slice: substitution tests. 10 buyer interviews, incl. "loop before trust?" | 3–5 pilots paid at real price. **Nobody pays = stop and rethink.** |
| 3 | **Subscriptions (Regression)** | 2–4 qtr window | Frozen packs in customer CI, rerun on every change, alerts via stats engine. | Pilots converting to subscriptions. |
| 4 | **Autoresearch (the company)** | — | MD loop first (trained on challenge corpus), then harness loop. Moat = owned objectives + trust, not the loop. | — |

**Cut / parked**

| Item | Status | Why |
|---|---|---|
| Attribution (#3) standalone | Cut | Unproven demand. Build later inside Cost Audit |
| Full Cost Audit (#7) | Parked | Needs attribution. Substitution slice ships in Stage 2 |
| SF2 | Parked | Revisit as paused-frame MD division, only if PD draws a crowd |
| Autoresearch Harness now | Parked | Racing funded teams before owning the objective layer |

**Tripwire:** NeoSigma or Kayba lands a repo-work customer → Stage 4 accelerates, ready or not.

---

## Tooling coverage note — Aug 20, 2026

Where the eval tooling (built + planned) carries each stage, and what each stage
still needs beyond it. "Built" = task format, admission checker (taskcheck),
freeze/tamper ledger, evidence capture, stats primitives, null-arm calibration.
"Planned" = task factory (`make` = agent-driven task generation from recipes,
`blindsolve` = automated isolated solver with provenance, spread check = no
master-list-of-requirements verification) + measurement bridge (two-arm driver
on the new task format, comparison + verdict writer, un-hardcode subject model
and MD filename).

| Stage | Covered by built + planned | Still needs (beyond tooling) |
|---|---|---|
| 0 Statistics | A/A calibration, paired runs, inconclusive verdicts → bridge | PD pilot: game domain = new runner + scorer, nothing reusable from coding stack |
| 1 Open source + challenges | Public packs from factory; sealed scoring = freeze/verify ledger; corpus labeling = calibration runs | Challenge ops (submission intake, identity, hosting, champion video); PR-to-task mining (closed piece — real-PR input mode for factory, harder than synthetic recipes, unplanned) |
| 2 Paid pilots | Private packs = factory pointed at customer repos; cost-audit slice = per-run token/time telemetry already captured | Agent adapters beyond Codex (Claude Code etc. — one small adapter each, none written); factory hardening for large/messy real repos |
| 3 Subscriptions | Frozen-pack verify + rerun already built | CI packaging (Actions integration, alerting) — modest glue |
| 4 Autoresearch | Trusted-eval layer (the anti-reward-hacking substrate the loop optimizes against) = taskcheck + ledger; owned objective = validated task corpus | The optimizer loop itself (propose MD → eval → iterate) — correctly parked |

Key implication: the tooling is not a coder.md side quest — it is the "owned
objectives + trust" moat layer named in Stage 4. Factory + bridge clears Stage 1
(minus challenge ops) and most of Stage 2.

First real new-build decision (business call, not a tooling gap): PR-to-task
mining vs. game challenges — whichever the Stage 1 launch actually leans on.
