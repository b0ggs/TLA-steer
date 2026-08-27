# Cost/time probe result

> **CORRECTNESS REGRESSION RISK: YES.** At least one task/arm resolved fewer than 3/3 valid finalized attempts.

- `full-starlette-websocket-denial` / `probe`: 2/3 resolved.
- `full-click-stream-lifecycle` / `null`: 2/3 resolved.
- `full-click-stream-lifecycle` / `probe`: 2/3 resolved.

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
| `full-boltons-wraps-forwarding` | Primary token cost | -34,169 | 61,712 | no |
| `full-boltons-wraps-forwarding` | Wall time | -128.184 | 417.064 | no |
| `full-boltons-wraps-forwarding` | Trajectory length | -10 | 21 | no |
| `full-flask-automatic-options` | Primary token cost | +8,952 | 16,692 | no |
| `full-flask-automatic-options` | Wall time | -21.749 | 3.186 | yes |
| `full-flask-automatic-options` | Trajectory length | +1 | 5 | no |
| `full-starlette-websocket-denial` | Primary token cost | -4,620 | 55,923 | no |
| `full-starlette-websocket-denial` | Wall time | -66.394 | 521.700 | no |
| `full-starlette-websocket-denial` | Trajectory length | -14 | 5 | yes |
| `full-click-stream-lifecycle` | Primary token cost | +18,428 | 79,734 | no |
| `full-click-stream-lifecycle` | Wall time | -83.504 | 211.249 | no |
| `full-click-stream-lifecycle` | Trajectory length | -12 | 14 | no |

## Attempt evidence

### `full-boltons-wraps-forwarding`

| Arm | Primary token attempts | Wall-time attempts (s) | Trajectory attempts | Correctness | Usage |
|---|---|---|---|---:|---:|
| `null` | 82,258, 97,928, 143,970 (median 97,928; n=3) | 371.391, 437.019, 788.455 (median 437.019; n=3) | 24, 45, 38 (median 38; n=3) | 3/3 | 3/3 |
| `probe` | 65,921, 61,595, 63,759 (median 63,759; n=3) | 290.125, 310.631, 308.835 (median 308.835; n=3) | 24, 28, 30 (median 28; n=3) | 3/3 | 3/3 |

- `null` attempt 1: usable; token=82,258; wall=371.391; trajectory=24; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`boltons/funcutils.py`, `tests/test_funcutils_fb.py`, `tests/test_funcutils_fb_py3.py`; tools=command_execution×11 → file_change×2 → command_execution×2 → file_change → command_execution → file_change → command_execution → file_change → command_execution×4.
- `null` attempt 2: usable; token=97,928; wall=437.019; trajectory=45; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`boltons/funcutils.py`, `tests/test_funcutils_fb.py`, `tests/test_funcutils_fb_py3.py`; tools=command_execution×16 → file_change → command_execution → file_change → command_execution×6 → file_change → command_execution×3 → file_change → command_execution → file_change → command_execution → file_change → command_execution×7 → file_change → command_execution×3.
- `null` attempt 3: usable; token=143,970; wall=788.455; trajectory=38; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`boltons/funcutils.py`, `tests/test_funcutils_fb.py`, `tests/test_funcutils_fb_py3.py`; tools=command_execution×19 → file_change → command_execution → file_change → command_execution×6 → file_change → command_execution×2 → file_change → command_execution×4 → file_change → command_execution.
- `probe` attempt 1: usable; token=65,921; wall=290.125; trajectory=24; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`boltons/funcutils.py`, `tests/test_funcutils_fb.py`, `tests/test_funcutils_fb_py3.py`; tools=command_execution×14 → file_change → command_execution → file_change×2 → command_execution×3 → file_change → command_execution×2.
- `probe` attempt 2: usable; token=61,595; wall=310.631; trajectory=28; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`boltons/funcutils.py`, `tests/test_funcutils_fb.py`, `tests/test_funcutils_fb_py3.py`; tools=command_execution×15 → file_change → command_execution → file_change×2 → command_execution×3 → file_change×2 → command_execution×4.
- `probe` attempt 3: usable; token=63,759; wall=308.835; trajectory=30; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`boltons/funcutils.py`, `tests/test_funcutils_fb.py`, `tests/test_funcutils_fb_py3.py`; tools=command_execution×15 → file_change → command_execution×6 → file_change → command_execution×3 → file_change → command_execution×3.

### `full-flask-automatic-options`

| Arm | Primary token attempts | Wall-time attempts (s) | Trajectory attempts | Correctness | Usage |
|---|---|---|---|---:|---:|
| `null` | 54,532, 39,831, 37,840 (median 39,831; n=3) | 122.246, 121.284, 119.060 (median 121.284; n=3) | 11, 15, 16 (median 15; n=3) | 3/3 | 3/3 |
| `probe` | 35,194, 48,783, 51,696 (median 48,783; n=3) | 90.234, 99.536, 112.661 (median 99.536; n=3) | 12, 16, 19 (median 16; n=3) | 3/3 | 3/3 |

- `null` attempt 1: usable; token=54,532; wall=122.246; trajectory=11; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/flask/sansio/app.py`, `tests/test_basic.py`, `tests/test_views.py`; tools=command_execution×6 → file_change → command_execution×4.
- `null` attempt 2: usable; token=39,831; wall=121.284; trajectory=15; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/flask/sansio/app.py`, `tests/test_basic.py`, `tests/test_views.py`; tools=command_execution×9 → file_change → command_execution×5.
- `null` attempt 3: usable; token=37,840; wall=119.060; trajectory=16; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/flask/sansio/app.py`, `tests/test_basic.py`, `tests/test_views.py`; tools=command_execution×9 → file_change → command_execution×4 → file_change → command_execution.
- `probe` attempt 1: usable; token=35,194; wall=90.234; trajectory=12; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/flask/sansio/app.py`, `tests/test_basic.py`, `tests/test_views.py`; tools=command_execution×5 → file_change → command_execution×6.
- `probe` attempt 2: usable; token=48,783; wall=99.536; trajectory=16; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/flask/sansio/app.py`, `tests/test_basic.py`, `tests/test_views.py`; tools=command_execution×6 → file_change → command_execution×9.
- `probe` attempt 3: usable; token=51,696; wall=112.661; trajectory=19; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/flask/sansio/app.py`, `tests/test_basic.py`, `tests/test_views.py`; tools=command_execution×13 → file_change → command_execution×5.

### `full-starlette-websocket-denial`

| Arm | Primary token attempts | Wall-time attempts (s) | Trajectory attempts | Correctness | Usage |
|---|---|---|---|---:|---:|
| `null` | 82,208, 79,401, 135,324 (median 82,208; n=3) | 232.612, 312.357, 754.312 (median 312.357; n=3) | 32, 31, 36 (median 32; n=3) | 3/3 | 3/3 |
| `probe` | 77,588, 106,671, 52,954 (median 77,588; n=3) | 245.963, 637.429, 203.281 (median 245.963; n=3) | 18, 38, 17 (median 18; n=3) | 2/3 | 3/3 |

- `null` attempt 1: usable; token=82,208; wall=232.612; trajectory=32; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`starlette/responses.py`, `tests/test_websockets.py`; tools=command_execution×14 → file_change → command_execution×14 → file_change → command_execution×2.
- `null` attempt 2: usable; token=79,401; wall=312.357; trajectory=31; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`starlette/responses.py`, `tests/test_websockets.py`; tools=command_execution×13 → file_change×2 → command_execution×12 → file_change → command_execution×3.
- `null` attempt 3: usable; token=135,324; wall=754.312; trajectory=36; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`starlette/responses.py`, `tests/test_responses.py`, `tests/test_websockets.py`; tools=command_execution×6 → file_change → command_execution×18 → file_change → command_execution×10.
- `probe` attempt 1: usable; token=77,588; wall=245.963; trajectory=18; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`starlette/responses.py`, `tests/test_websockets.py`; tools=command_execution×6 → file_change → command_execution → file_change → command_execution×3 → file_change → command_execution → file_change → command_execution×3.
- `probe` attempt 2: usable; token=106,671; wall=637.429; trajectory=38; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`starlette/responses.py`, `tests/test_websockets.py`; tools=command_execution×15 → file_change → command_execution → file_change → command_execution×9 → file_change×4 → command_execution → file_change → command_execution → file_change → command_execution×3.
- `probe` attempt 3: usable; token=52,954; wall=203.281; trajectory=17; resolved=False; checks=R1=fail, R2=pass, G1=pass; paths=`starlette/responses.py`, `tests/test_websockets.py`; tools=command_execution×6 → file_change → command_execution×10.

### `full-click-stream-lifecycle`

| Arm | Primary token attempts | Wall-time attempts (s) | Trajectory attempts | Correctness | Usage |
|---|---|---|---|---:|---:|
| `null` | 71,822, 151,556, 79,696 (median 79,696; n=3) | 401.601, 527.505, 316.257 (median 401.601; n=3) | 38, 29, 43 (median 38; n=3) | 2/3 | 3/3 |
| `probe` | 98,124, 53,175, 131,688 (median 98,124; n=3) | 318.097, 231.071, 443.008 (median 318.097; n=3) | 21, 26, 29 (median 26; n=3) | 2/3 | 3/3 |

- `null` attempt 1: usable; token=71,822; wall=401.601; trajectory=38; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/click/testing.py`, `tests/test_testing.py`; tools=command_execution×21 → file_change → command_execution×5 → file_change×2 → command_execution×4 → file_change → command_execution×4.
- `null` attempt 2: usable; token=151,556; wall=527.505; trajectory=29; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/click/testing.py`, `tests/test_testing.py`; tools=command_execution×14 → file_change → command_execution×11 → file_change → command_execution×2.
- `null` attempt 3: usable; token=79,696; wall=316.257; trajectory=43; resolved=False; checks=R1=fail, R2=pass, G1=pass; paths=`src/click/testing.py`, `tests/test_testing.py`; tools=command_execution×23 → file_change → command_execution×19.
- `probe` attempt 1: usable; token=98,124; wall=318.097; trajectory=21; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/click/testing.py`, `tests/test_testing_logging.py`; tools=command_execution×9 → file_change → command_execution×5 → file_change → command_execution×5.
- `probe` attempt 2: usable; token=53,175; wall=231.071; trajectory=26; resolved=False; checks=R1=fail, R2=pass, G1=pass; paths=`src/click/testing.py`, `tests/test_testing.py`; tools=command_execution×19 → file_change×2 → command_execution×5.
- `probe` attempt 3: usable; token=131,688; wall=443.008; trajectory=29; resolved=True; checks=R1=pass, R2=pass, G1=pass; paths=`src/click/testing.py`, `tests/test_testing.py`; tools=command_execution×10 → file_change → command_execution×15 → file_change → command_execution×2.
