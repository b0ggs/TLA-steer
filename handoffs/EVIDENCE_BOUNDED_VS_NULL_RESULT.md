# Cost/time probe result

> **CORRECTNESS REGRESSION RISK: YES.** At least one task/arm resolved fewer than 3/3 valid finalized attempts.

- `full-starlette-websocket-denial` / `null`: 2/3 resolved.
- `full-starlette-websocket-denial` / `evidence-bounded`: 1/3 resolved.
- `full-click-stream-lifecycle` / `evidence-bounded`: 2/3 resolved.

## Overall outcome

| Arm | Resolved | Primary-token total | Wall-time total (s) |
|---|---:|---:|---:|
| `null` | 11/12 | 1,038,007 (n=12) | 3,364.107 (n=12) |
| `evidence-bounded` | 9/12 | 815,950 (n=12) | 2,728.005 (n=12) |

**Quality gate failed:** the candidate resolved fewer attempts than null, so lower aggregate resource totals cannot be treated as an efficiency improvement.

Totals are descriptive sums over metric-usable attempts and can be confounded by failed attempts ending earlier.

## Metric classifications

| Metric | Classification | Measurable tasks | Direction |
|---|---|---:|---|
| Primary token cost | **NO DIRECTIONAL SIGNAL** | 4 | — |
| Wall time | **NO DIRECTIONAL SIGNAL** | 4 | — |
| Trajectory length | **NO DIRECTIONAL SIGNAL** | 4 | — |

Positive differences mean the probe arm was higher than null. Classifications are independent descriptive triage, not significance tests or causal claims. No dollar price or time-to-first-action is inferred.

## Per-task comparisons

| Task | Metric | Probe − null median | Null range | Qualifies |
|---|---|---:|---:|---|
| `full-boltons-wraps-forwarding` | Primary token cost | +18,837 | 21,285 | no |
| `full-boltons-wraps-forwarding` | Wall time | -35.291 | 98.000 | no |
| `full-boltons-wraps-forwarding` | Trajectory length | +8 | 8 | no |
| `full-flask-automatic-options` | Primary token cost | +6,446 | 21,756 | no |
| `full-flask-automatic-options` | Wall time | -18.007 | 8.953 | yes |
| `full-flask-automatic-options` | Trajectory length | -7 | 2 | yes |
| `full-starlette-websocket-denial` | Primary token cost | +2,799 | 81,412 | no |
| `full-starlette-websocket-denial` | Wall time | +22.466 | 299.541 | no |
| `full-starlette-websocket-denial` | Trajectory length | -15 | 15 | no |
| `full-click-stream-lifecycle` | Primary token cost | -48,709 | 20,838 | yes |
| `full-click-stream-lifecycle` | Wall time | -86.686 | 40.445 | yes |
| `full-click-stream-lifecycle` | Trajectory length | -12 | 5 | yes |

## Attempt evidence

### `full-boltons-wraps-forwarding`

| Arm | Primary token attempts | Wall-time attempts (s) | Trajectory attempts | Correctness | Usage |
|---|---|---|---|---:|---:|
| `null` | 70,394, 76,589, 91,679 (median 76,589; n=3) | 285.741, 338.876, 383.741 (median 338.876; n=3) | 15, 16, 23 (median 16; n=3) | 3/3 | 3/3 |
| `evidence-bounded` | 125,927, 61,557, 95,426 (median 95,426; n=3) | 326.705, 303.585, 302.114 (median 303.585; n=3) | 24, 23, 26 (median 24; n=3) | 3/3 | 3/3 |

- `null` attempt 1: usable; token=70,394; wall=285.741; trajectory=15; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`boltons/funcutils.py`, `tests/test_funcutils_fb.py`, `tests/test_funcutils_fb_py3.py`; tools=command_execution×8 → file_change → command_execution×2 → file_change×2 → command_execution×2.
- `null` attempt 2: usable; token=76,589; wall=338.876; trajectory=16; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`boltons/funcutils.py`, `tests/test_funcutils_fb.py`, `tests/test_funcutils_fb_py3.py`; tools=command_execution×6 → file_change×4 → command_execution → file_change×2 → command_execution×2 → file_change.
- `null` attempt 3: usable; token=91,679; wall=383.741; trajectory=23; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`boltons/funcutils.py`, `tests/test_funcutils_fb.py`, `tests/test_funcutils_fb_py3.py`; tools=command_execution×12 → file_change → command_execution → file_change → command_execution×3 → file_change×2 → command_execution×3.
- `evidence-bounded` attempt 1: usable; token=125,927; wall=326.705; trajectory=24; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`boltons/funcutils.py`, `tests/test_funcutils_fb.py`, `tests/test_funcutils_fb_py3.py`; tools=command_execution×13 → file_change → command_execution×4 → file_change → command_execution → file_change×2 → command_execution×2.
- `evidence-bounded` attempt 2: usable; token=61,557; wall=303.585; trajectory=23; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`boltons/funcutils.py`, `tests/test_funcutils_fb.py`, `tests/test_funcutils_fb_py3.py`; tools=command_execution×15 → file_change → command_execution×5 → file_change → command_execution.
- `evidence-bounded` attempt 3: usable; token=95,426; wall=302.114; trajectory=26; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`boltons/funcutils.py`, `tests/test_funcutils_fb.py`, `tests/test_funcutils_fb_py3.py`; tools=command_execution×15 → file_change → command_execution → file_change → command_execution → file_change×3 → command_execution×2 → file_change → command_execution.

### `full-flask-automatic-options`

| Arm | Primary token attempts | Wall-time attempts (s) | Trajectory attempts | Correctness | Usage |
|---|---|---|---|---:|---:|
| `null` | 69,262, 47,506, 51,161 (median 51,161; n=3) | 131.253, 135.314, 126.361 (median 131.253; n=3) | 20, 19, 18 (median 19; n=3) | 3/3 | 3/3 |
| `evidence-bounded` | 57,607, 58,220, 35,209 (median 57,607; n=3) | 113.246, 103.762, 115.945 (median 113.246; n=3) | 12, 11, 21 (median 12; n=3) | 3/3 | 3/3 |

- `null` attempt 1: usable; token=69,262; wall=131.253; trajectory=20; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/flask/sansio/app.py`, `tests/test_basic.py`, `tests/test_views.py`; tools=command_execution×12 → file_change → command_execution×7.
- `null` attempt 2: usable; token=47,506; wall=135.314; trajectory=19; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/flask/sansio/app.py`, `tests/test_basic.py`, `tests/test_views.py`; tools=command_execution×12 → file_change → command_execution×2 → file_change → command_execution×3.
- `null` attempt 3: usable; token=51,161; wall=126.361; trajectory=18; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/flask/sansio/app.py`, `tests/test_basic.py`, `tests/test_views.py`; tools=command_execution×13 → file_change → command_execution×4.
- `evidence-bounded` attempt 1: usable; token=57,607; wall=113.246; trajectory=12; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/flask/sansio/app.py`, `tests/test_basic.py`, `tests/test_views.py`; tools=command_execution×7 → file_change → command_execution×4.
- `evidence-bounded` attempt 2: usable; token=58,220; wall=103.762; trajectory=11; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/flask/sansio/app.py`, `tests/test_basic.py`, `tests/test_views.py`; tools=command_execution×6 → file_change → command_execution×4.
- `evidence-bounded` attempt 3: usable; token=35,209; wall=115.945; trajectory=21; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/flask/sansio/app.py`, `tests/test_basic.py`, `tests/test_views.py`; tools=command_execution×10 → file_change → command_execution×10.

### `full-starlette-websocket-denial`

| Arm | Primary token attempts | Wall-time attempts (s) | Trajectory attempts | Correctness | Usage |
|---|---|---|---|---:|---:|
| `null` | 66,875, 64,734, 146,146 (median 66,875; n=3) | 198.473, 229.993, 498.015 (median 229.993; n=3) | 27, 14, 29 (median 27; n=3) | 2/3 | 3/3 |
| `evidence-bounded` | 55,287, 69,674, 77,778 (median 69,674; n=3) | 252.459, 333.080, 154.250 (median 252.459; n=3) | 14, 11, 12 (median 12; n=3) | 1/3 | 3/3 |

- `null` attempt 1: usable; token=66,875; wall=198.473; trajectory=27; resolved=False; checks=R1=fail, R2=pass, G1=pass; paths=`starlette/responses.py`, `tests/test_websockets.py`; tools=command_execution×12 → file_change → command_execution×14.
- `null` attempt 2: usable; token=64,734; wall=229.993; trajectory=14; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`starlette/responses.py`, `tests/test_websockets.py`; tools=command_execution×6 → file_change → command_execution×3 → file_change → command_execution×3.
- `null` attempt 3: usable; token=146,146; wall=498.015; trajectory=29; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`starlette/responses.py`, `tests/test_websockets.py`; tools=command_execution×7 → file_change → command_execution×6 → file_change → command_execution×6 → file_change×2 → command_execution → file_change → command_execution×4.
- `evidence-bounded` attempt 1: usable; token=55,287; wall=252.459; trajectory=14; resolved=False; checks=R1=fail, R2=pass, G1=pass; paths=`starlette/responses.py`, `tests/test_websockets.py`; tools=command_execution×6 → file_change → command_execution×5 → file_change → command_execution.
- `evidence-bounded` attempt 2: usable; token=69,674; wall=333.080; trajectory=11; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`starlette/responses.py`, `tests/test_websockets.py`; tools=command_execution×5 → file_change → command_execution×3 → file_change → command_execution.
- `evidence-bounded` attempt 3: usable; token=77,778; wall=154.250; trajectory=12; resolved=False; checks=R1=fail, R2=pass, G1=pass; paths=`starlette/responses.py`, `tests/test_websockets.py`; tools=command_execution×7 → file_change → command_execution×4.

### `full-click-stream-lifecycle`

| Arm | Primary token attempts | Wall-time attempts (s) | Trajectory attempts | Correctness | Usage |
|---|---|---|---|---:|---:|
| `null` | 109,044, 114,735, 129,882 (median 114,735; n=3) | 331.005, 333.887, 371.450 (median 333.887; n=3) | 22, 27, 27 (median 27; n=3) | 3/3 | 3/3 |
| `evidence-bounded` | 66,828, 46,411, 66,026 (median 66,026; n=3) | 286.407, 247.201, 189.252 (median 247.201; n=3) | 15, 18, 15 (median 15; n=3) | 2/3 | 3/3 |

- `null` attempt 1: usable; token=109,044; wall=331.005; trajectory=22; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/click/testing.py`, `tests/test_testing.py`; tools=command_execution×13 → file_change → command_execution×5 → file_change → command_execution×2.
- `null` attempt 2: usable; token=114,735; wall=333.887; trajectory=27; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/click/testing.py`, `tests/test_stream_lifecycle.py`; tools=command_execution×10 → file_change → command_execution×11 → file_change → command_execution×4.
- `null` attempt 3: usable; token=129,882; wall=371.450; trajectory=27; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/click/testing.py`, `tests/test_testing.py`; tools=command_execution×14 → file_change → command_execution×2 → file_change → command_execution×9.
- `evidence-bounded` attempt 1: usable; token=66,828; wall=286.407; trajectory=15; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/click/testing.py`, `tests/test_testing.py`; tools=command_execution×10 → file_change → command_execution×2 → file_change → command_execution.
- `evidence-bounded` attempt 2: usable; token=46,411; wall=247.201; trajectory=18; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/click/testing.py`, `tests/test_testing.py`; tools=command_execution×13 → file_change → command_execution×4.
- `evidence-bounded` attempt 3: usable; token=66,026; wall=189.252; trajectory=15; resolved=False; checks=R1=fail, R2=pass, G1=pass; paths=`src/click/testing.py`, `tests/test_testing.py`; tools=command_execution×11 → file_change → command_execution×3.
