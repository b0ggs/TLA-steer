# Evidence-bounded exploratory result

## Result

On these 24 runs, `evidence-bounded-v1.md` was materially more efficient than
the previous MD overall, with equal observed correctness. This is a descriptive
result on four development tasks, not a significance or generalization claim.

- Correctness: **11/12 resolved in each arm**. Each arm missed Starlette `R1`
  on attempt 2; every other attempt resolved mechanically.
- Total primary token cost: **691,682 vs 959,049**, a **27.9% reduction**.
- Total subject wall time: **2,457.8s vs 3,580.6s**, a **31.4% reduction**.
- Total trajectory length: **227 vs 300**, a **24.3% reduction**.
- Pooled medians: primary tokens **-33.4%**, wall time **-25.7%**, and
  trajectory length unchanged at 18.5.
- Resolved-only medians: primary tokens **-33.4%**, wall time **-26.8%**, and
  trajectory length **-5.6%**. The efficiency result therefore does not depend
  on counting the two failed attempts as cheap wins.

Negative percentages below favor evidence-bounded.

| Task | Previous correctness | New correctness | Primary tokens | Wall time | Trajectory |
|---|---:|---:|---:|---:|---:|
| Boltons | 3/3 | 3/3 | +6.8% | +2.1% | +70.6% |
| Flask | 3/3 | 3/3 | -9.5% | -6.6% | -16.7% |
| Starlette | 2/3 | 2/3 | -52.5% | -61.0% | -56.5% |
| Click | 3/3 | 3/3 | -38.9% | -0.3% | -15.8% |

The new MD had lower task medians on 3/4 tasks for every efficiency metric.
The result is not uniform: Boltons favored the previous MD, while Starlette
accounts for the largest wall-time gain. On mechanically resolved Starlette
attempts only, the new MD used 63.6% fewer primary tokens, 70.3% less wall
time, and 64.9% fewer trajectory items.

## Evidence and boundary

- Batch verification: `python3 scripts/run_batch.py verify
  evidence-bounded-probe-v1` exited 0.
- Calls: 24 nominal and launched; no replacement, timeout, invalid attempt, or
  missing usage record.
- Primary token cost is `input_tokens - cached_input_tokens + output_tokens`.
- Trajectory length counts distinct completed command or file-change item IDs.
- The candidate was derived from traces involving these tasks. These runs show
  that it performed better here; they do not establish how it will perform on
  unseen tasks or that the MD caused the difference.

The machine-readable summary is
[`analysis.json`](../runs/dev-v2/evidence-bounded-probe-v1/analysis.json).
