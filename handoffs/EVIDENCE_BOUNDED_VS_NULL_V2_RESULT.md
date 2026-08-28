# Cost/time probe result

> **CORRECTNESS REGRESSION RISK: YES.** At least one task/arm resolved fewer than 3/3 valid finalized attempts.

- `full-click-stream-lifecycle` / `evidence-bounded`: 1/3 resolved.

## Overall outcome

| Arm | Resolved | Primary-token total | Wall-time total (s) |
|---|---:|---:|---:|
| `null` | 12/12 | 1,088,214 (n=12) | 4,249.436 (n=12) |
| `evidence-bounded` | 10/12 | 709,917 (n=12) | 2,787.407 (n=12) |

**Quality gate failed:** the candidate resolved fewer attempts than null, so lower aggregate resource totals cannot be treated as an efficiency improvement.

Totals are descriptive sums over metric-usable attempts and can be confounded by failed attempts ending earlier.

## Metric classifications

| Metric | Classification | Measurable tasks | Direction |
|---|---|---:|---|
| Primary token cost | **NO DIRECTIONAL SIGNAL** | 4 | — |
| Wall time | **NO DIRECTIONAL SIGNAL** | 4 | — |
| Trajectory length | **DIRECTIONAL SIGNAL** | 4 | probe lower than null |

Positive differences mean the probe arm was higher than null. Classifications are independent descriptive triage, not significance tests or causal claims. No dollar price or time-to-first-action is inferred.

## Per-task comparisons

| Task | Metric | Probe − null median | Null range | Qualifies |
|---|---|---:|---:|---|
| `full-boltons-wraps-forwarding` | Primary token cost | +8,758 | 27,846 | no |
| `full-boltons-wraps-forwarding` | Wall time | -100.602 | 143.626 | no |
| `full-boltons-wraps-forwarding` | Trajectory length | +2 | 7 | no |
| `full-flask-automatic-options` | Primary token cost | -20,488 | 20,082 | yes |
| `full-flask-automatic-options` | Wall time | -55.066 | 56.407 | no |
| `full-flask-automatic-options` | Trajectory length | -11 | 5 | yes |
| `full-starlette-websocket-denial` | Primary token cost | -38,041 | 93,312 | no |
| `full-starlette-websocket-denial` | Wall time | -301.567 | 123.120 | yes |
| `full-starlette-websocket-denial` | Trajectory length | -16 | 15 | yes |
| `full-click-stream-lifecycle` | Primary token cost | -29,831 | 38,954 | no |
| `full-click-stream-lifecycle` | Wall time | -15.980 | 76.465 | no |
| `full-click-stream-lifecycle` | Trajectory length | -8 | 4 | yes |

## Attempt evidence

### `full-boltons-wraps-forwarding`

| Arm | Primary token attempts | Wall-time attempts (s) | Trajectory attempts | Correctness | Usage |
|---|---|---|---|---:|---:|
| `null` | 68,250, 96,096, 71,843 (median 71,843; n=3) | 449.282, 334.376, 305.656 (median 334.376; n=3) | 17, 24, 18 (median 18; n=3) | 3/3 | 3/3 |
| `evidence-bounded` | 80,601, 46,220, 88,750 (median 80,601; n=3) | 233.774, 242.228, 211.687 (median 233.774; n=3) | 21, 20, 20 (median 20; n=3) | 3/3 | 3/3 |

- `null` attempt 1: usable; token=68,250; wall=449.282; trajectory=17; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`boltons/funcutils.py`, `tests/test_funcutils_fb.py`, `tests/test_funcutils_fb_py3.py`; tools=command_execution×7 → file_change → command_execution×2 → file_change → command_execution×3 → file_change → command_execution×2.
- `null` attempt 2: usable; token=96,096; wall=334.376; trajectory=24; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`boltons/funcutils.py`, `tests/test_funcutils_fb.py`, `tests/test_funcutils_fb_py3.py`; tools=command_execution×9 → file_change → command_execution → file_change → command_execution → file_change → command_execution×4 → file_change×2 → command_execution×4.
- `null` attempt 3: usable; token=71,843; wall=305.656; trajectory=18; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`boltons/funcutils.py`, `tests/test_funcutils_fb.py`, `tests/test_funcutils_fb_py3.py`; tools=command_execution×7 → file_change → command_execution×2 → file_change → command_execution×5 → file_change → command_execution.
- `evidence-bounded` attempt 1: usable; token=80,601; wall=233.774; trajectory=21; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`boltons/funcutils.py`, `tests/test_funcutils_fb.py`, `tests/test_funcutils_fb_py3.py`; tools=command_execution×14 → file_change → command_execution → file_change → command_execution×4.
- `evidence-bounded` attempt 2: usable; token=46,220; wall=242.228; trajectory=20; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`boltons/funcutils.py`, `tests/test_funcutils_fb.py`, `tests/test_funcutils_fb_py3.py`; tools=command_execution×10 → file_change → command_execution×2 → file_change → command_execution×3 → file_change → command_execution×2.
- `evidence-bounded` attempt 3: usable; token=88,750; wall=211.687; trajectory=20; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`boltons/funcutils.py`, `tests/test_funcutils_fb.py`, `tests/test_funcutils_fb_py3.py`; tools=command_execution×12 → file_change×2 → command_execution → file_change → command_execution×4.

### `full-flask-automatic-options`

| Arm | Primary token attempts | Wall-time attempts (s) | Trajectory attempts | Correctness | Usage |
|---|---|---|---|---:|---:|
| `null` | 64,119, 56,260, 44,037 (median 56,260; n=3) | 127.777, 184.184, 170.383 (median 170.383; n=3) | 19, 24, 21 (median 21; n=3) | 3/3 | 3/3 |
| `evidence-bounded` | 35,772, 30,015, 51,150 (median 35,772; n=3) | 109.888, 115.317, 116.200 (median 115.317; n=3) | 10, 10, 11 (median 10; n=3) | 3/3 | 3/3 |

- `null` attempt 1: usable; token=64,119; wall=127.777; trajectory=19; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/flask/sansio/app.py`, `tests/test_basic.py`, `tests/test_views.py`; tools=command_execution×6 → file_change → command_execution×12.
- `null` attempt 2: usable; token=56,260; wall=184.184; trajectory=24; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/flask/sansio/app.py`, `tests/test_basic.py`, `tests/test_views.py`; tools=command_execution×13 → file_change → command_execution×7 → file_change → command_execution×2.
- `null` attempt 3: usable; token=44,037; wall=170.383; trajectory=21; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/flask/sansio/app.py`, `tests/test_basic.py`, `tests/test_views.py`; tools=command_execution×6 → file_change → command_execution → file_change → command_execution×9 → file_change → command_execution×2.
- `evidence-bounded` attempt 1: usable; token=35,772; wall=109.888; trajectory=10; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/flask/sansio/app.py`, `tests/test_basic.py`, `tests/test_views.py`; tools=command_execution×5 → file_change → command_execution×4.
- `evidence-bounded` attempt 2: usable; token=30,015; wall=115.317; trajectory=10; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/flask/sansio/app.py`, `tests/test_basic.py`, `tests/test_views.py`; tools=command_execution×4 → file_change → command_execution×5.
- `evidence-bounded` attempt 3: usable; token=51,150; wall=116.200; trajectory=11; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/flask/sansio/app.py`, `tests/test_basic.py`, `tests/test_views.py`; tools=command_execution×6 → file_change → command_execution×4.

### `full-starlette-websocket-denial`

| Arm | Primary token attempts | Wall-time attempts (s) | Trajectory attempts | Correctness | Usage |
|---|---|---|---|---:|---:|
| `null` | 194,166, 111,354, 100,854 (median 111,354; n=3) | 655.116, 531.996, 606.671 (median 606.671; n=3) | 34, 49, 38 (median 38; n=3) | 3/3 | 3/3 |
| `evidence-bounded` | 74,015, 55,287, 73,313 (median 73,313; n=3) | 305.104, 303.435, 352.588 (median 305.104; n=3) | 15, 22, 35 (median 22; n=3) | 3/3 | 3/3 |

- `null` attempt 1: usable; token=194,166; wall=655.116; trajectory=34; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`starlette/responses.py`, `tests/test_websockets.py`; tools=command_execution×7 → file_change×2 → command_execution×6 → file_change → command_execution×5 → file_change → command_execution×4 → file_change → command_execution×7.
- `null` attempt 2: usable; token=111,354; wall=531.996; trajectory=49; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`starlette/responses.py`, `tests/test_websockets.py`; tools=command_execution×16 → file_change×2 → command_execution×6 → file_change → command_execution×7 → file_change → command_execution×9 → file_change → command_execution×6.
- `null` attempt 3: usable; token=100,854; wall=606.671; trajectory=38; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`starlette/responses.py`, `tests/test_websockets.py`; tools=command_execution×8 → file_change → command_execution → file_change → command_execution×19 → file_change → command_execution×7.
- `evidence-bounded` attempt 1: usable; token=74,015; wall=305.104; trajectory=15; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`starlette/responses.py`, `tests/test_websockets.py`; tools=command_execution×8 → file_change → command_execution×3 → file_change → command_execution×2.
- `evidence-bounded` attempt 2: usable; token=55,287; wall=303.435; trajectory=22; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`starlette/responses.py`, `tests/test_websockets.py`; tools=command_execution×8 → file_change → command_execution×2 → file_change → command_execution×5 → file_change×2 → command_execution×3.
- `evidence-bounded` attempt 3: usable; token=73,313; wall=352.588; trajectory=35; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`starlette/responses.py`, `tests/test_websockets.py`; tools=command_execution×14 → file_change → command_execution×3 → file_change → command_execution×9 → file_change → command_execution×2 → file_change → command_execution×3.

### `full-click-stream-lifecycle`

| Arm | Primary token attempts | Wall-time attempts (s) | Trajectory attempts | Correctness | Usage |
|---|---|---|---|---:|---:|
| `null` | 116,909, 77,955, 86,371 (median 86,371; n=3) | 341.831, 265.366, 276.797 (median 276.797; n=3) | 30, 34, 31 (median 31; n=3) | 3/3 | 3/3 |
| `evidence-bounded` | 56,540, 55,897, 62,357 (median 56,540; n=3) | 260.816, 259.087, 277.281 (median 260.816; n=3) | 23, 13, 23 (median 23; n=3) | 1/3 | 3/3 |

- `null` attempt 1: usable; token=116,909; wall=341.831; trajectory=30; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/click/testing.py`, `tests/test_testing.py`; tools=command_execution×13 → file_change → command_execution×10 → file_change → command_execution×5.
- `null` attempt 2: usable; token=77,955; wall=265.366; trajectory=34; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/click/testing.py`, `tests/test_testing.py`; tools=command_execution×19 → file_change×2 → command_execution×13.
- `null` attempt 3: usable; token=86,371; wall=276.797; trajectory=31; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/click/testing.py`, `tests/test_testing.py`; tools=command_execution×19 → file_change → command_execution×11.
- `evidence-bounded` attempt 1: usable; token=56,540; wall=260.816; trajectory=23; resolved=False; checks=R1=fail, R2=pass, G1=pass; paths=`src/click/testing.py`, `tests/test_testing.py`; tools=command_execution×13 → file_change → command_execution → file_change → command_execution×3 → file_change → command_execution×3.
- `evidence-bounded` attempt 2: usable; token=55,897; wall=259.087; trajectory=13; resolved=False; checks=R1=fail, R2=pass, G1=pass; paths=`src/click/testing.py`, `tests/test_testing.py`; tools=command_execution×8 → file_change → command_execution×4.
- `evidence-bounded` attempt 3: usable; token=62,357; wall=277.281; trajectory=23; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/click/testing.py`, `tests/test_testing.py`; tools=command_execution×14 → file_change → command_execution×4 → file_change → command_execution×3.
