# Original two-arm user test guide

This is the finite TwoLights prototype. The implementation handoff is the
reviewed code, offline checks and this runbook. A successful live comparison
still requires validation on your host and account. Model errors, particle
collapse or steering costing more are valid results; an evaluator failure or
missing usage is not a successful end-to-end validation.

## 1. Pull the reviewed revision

Use the exact 40-character commit and checkout command in the final draft PR.
Its branch is `dot/two-arm-completion`, based on PR #2 commit
`32af88241a5762e87a3ea9b1745a0b2b3c0cd8bf` and therefore including PR #1.
PR #3 is optional and is not part of this handoff.

For a fresh checkout:

```sh
git clone --branch dot/two-arm-completion https://github.com/b0ggs/TLA-steer.git
cd TLA-steer
git rev-parse HEAD
git status --short
```

Confirm that HEAD equals the tested commit printed in the final PR and that
the checkout is clean. The exact detached-checkout command there pins it even
if the branch later advances. Do not merge the draft PRs just to test them.

## 2. Offline checks

Use Linux, Bash, Git and Python 3.12 or newer for the full focused suite;
the execution tests exercise Linux system-runtime paths. No Python package
installation is required; run from the repository root with `PYTHONPATH=src`.

```sh
mkdir -p validation
set -o pipefail
PYTHONPATH=src python3 -m unittest tests.test_oracle tests.test_verifier tests.test_smc tests.test_worker_fake tests.test_execution tests.test_capture -v 2>&1 | tee validation/focused-tests.txt
```

These tests use reviewed fixtures and synthetic provider events, including
the existing two-arm N=8/C=4 test with 66 normal-path calls, weighted selection,
artifact freezing and offline report replay. The two new regressions check
action-first partial scoring and reasoning JSONL events. They also retain
final INITIAL requirements and malformed-usage/forbidden-tool rejection.

For the repository-wide record:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v 2>&1 | tee validation/full-tests.txt
```

The known baseline has seven errors in `test_scout.ScoutPhaseBTests` caused by
missing historical evidence and seven skips. The final PR records the exact
test results. Do not treat additional failures as this known baseline.
No test command is intended to launch a live model.

## 3. Credential-free Linux prerequisites

The current launcher requires **compatible Linux**, an ordinary non-root user,
`/usr/bin/python3` (3.12+), `/usr/bin/bwrap`, `/usr/bin/prlimit`, the Debian/Ubuntu-style
system Python stdlib under `/usr/lib`, and working unprivileged namespaces.
The host probe also uses `dpkg-query` for package-version records. It does not run
generated candidates directly on macOS. A Linux VM/server may be suitable,
but no VM setup or host configuration is included or validated by this guide.

With those prerequisites already available, run:

```sh
test "$(id -u)" -ne 0
PYTHONPATH=src timeout 15s python3 -c 'from tla_steer.execution import preflight; print(preflight())' 2>&1 | tee validation/isolation-preflight.txt
PYTHONPATH=src timeout 180s python3 tooling/validate_isolation.py 2>&1 | tee validation/isolation-probes.txt
```

Both commands must succeed before login or generated-code execution.
The second uses controlled, reviewed probes through the real boundary:
golden partial/final grading, private-file/environment/descriptor isolation,
network denial, resource/output bounds and descendant cleanup. It does not
use the local fixture exception or make model calls. A pass is evidence for
that recorded host, not a general sandbox certification; CPU limits are
inspected rather than independently stress-enforced.

Stop if a prerequisite fails. Do not disable security controls, use a privileged
fallback or bypass the execution guard. The latest hosted Linux attempt failed
with [RTM_NEWADDR EPERM](https://github.com/b0ggs/TLA-steer/actions/runs/36803529525);
the exact host policy cause is unconfirmed. Later probes were not run there.

## 4. Credential-free Codex CLI compatibility

An installed Codex CLI must support the worker's frozen flags/configuration,
including `--strict-config`, `--ephemeral`, `--json`,
`--ignore-user-config`, `--ignore-rules` and `--output-schema`.
The existing doctor passed with `codex-cli 0.159.0-alpha.7` in the implementation
workspace on 2026-10-01, using an empty profile and no credentials or model calls.
That establishes local parsing only. Record and check your actual installed version.

Reuse the foundation's existing doctor with an **empty temporary profile**:

```sh
tla_probe_home="$(mktemp -d)"
CODEX_HOME="$tla_probe_home" MDSEVAL_CODEX_HOME="$tla_probe_home" PYTHONPATH=src timeout 90s python3 -m mdseval doctor --experiment experiments/coder-v1.json 2>&1 | tee validation/codex-doctor.txt
CODEX_HOME="$tla_probe_home" timeout 10s codex exec --help > validation/codex-exec-help.txt
python3 -c 'from pathlib import Path; assert "--output-schema" in Path("validation/codex-exec-help.txt").read_text(), "Codex --output-schema is required"'
```

Do not add `--live-smoke` to the doctor command. It checks executable/version,
required flags and local parsing of frozen capability settings through an
absent local socket; it does not send a model request. Require exit 0,
`model_call_made: false`, `required_flags_compatible: true`,
`required_config_compatible: true`, and
`config_compatibility_status: VERIFIED_LOCAL_PARSE_ONLY`.

Despite the doctor's legacy `LIVE_RUNNER_AVAILABLE` label, this establishes
local CLI parsing only. It does not establish effective sandbox enforcement,
account model access, reasoning-effort support or real usage capture. Those
remain smoke-test checks. If it fails, preserve the output and stop; do not
remove shutdown settings or change model names to make it pass.

## 5. User-owned OAuth and one smoke

Only after both host and CLI checks pass, use your own dedicated Codex OAuth
profile outside this repository. Do not paste or commit tokens or auth files.
For a new dedicated profile, run the login yourself on the Linux host:

```sh
export TLA_STEER_CODEX_HOME="$HOME/.tla-steer-codex"
mkdir -p "$TLA_STEER_CODEX_HOME"
CODEX_HOME="$TLA_STEER_CODEX_HOME" codex login
```

The dedicated profile must not contain personal instruction files. If you
already have one, set `TLA_STEER_CODEX_HOME` to that directory instead.
Login and the following model calls are user-run steps; they have not been
performed or validated as part of this implementation.

Run one two-arm smoke:

```sh
PYTHONPATH=src python3 -m tla_steer smoke --config configs/prototype.json 2>&1 | tee validation/smoke.txt
```

The smoke uses N=2/C=2: normally 18 calls, at most 19 with one Planner schema
repair. Each call has a 300-second timeout. These are call limits, not a token,
dollar or subscription-credit cap. The configured models are
`gpt-5.6-sol/xhigh` for direct/Planner and `gpt-5.6-luna/low` for Followers.
Their current account availability and real JSONL usage are unverified.

Before the intended comparison, inspect the report's run status, errors,
accounting completeness and recorded requested/returned model identifiers.
If the provider does not return a model identifier, retain that limitation;
do not claim it was independently verified. A model mismatch, authentication
failure, unsupported setting, missing usage or evaluator error requires
diagnosis rather than treating the smoke as validated. A well-recorded wrong
candidate or particle collapse is a legitimate model outcome.

## 6. One intended comparison and replay

After the smoke validates the integration, run the original two-arm comparison:

```sh
PYTHONPATH=src python3 -m tla_steer compare --config configs/prototype.json 2>&1 | tee validation/compare.txt
```

This uses N=8/C=4 and eight semantic steps: normally 66 calls, at most 67 with
one Planner schema repair, with no Follower retries. Collapse may use fewer
calls. The run prints its ID and stores evidence under `runs/<run-id>`.
Both official selections, including documented absent artifacts for failed
arms, are frozen before grading.

Use the printed run ID for replay:

```sh
PYTHONPATH=src python3 -m tla_steer report runs/<run-id>
PYTHONPATH=src python3 -m tla_steer report runs/<run-id> --json > validation/replayed-report.json
```

Replay reads the saved evidence and frozen rate card. It makes no model calls
and does not execute candidate code. Do not pass a replacement rate card when
checking reproducibility. API-price-equivalent estimates are not actual OAuth
charges; incomplete accounting or unknown usage must remain unknown.

Preserve the complete run directory, commit ID, CLI doctor/version output and
host-probe results for review. Check that direct and DisCIPL outcomes, all
attempted/failed calls, selection hashes, errors and usage remain visible.
A CLI exit of 0 alone does not prove a complete comparison; inspect the report.
An `EVALUATOR_ERROR` or `pipeline_error` is not successful validation.

Then stop. The original plan permits at most one concrete prompt/parser
correction and a fresh run if needed, preserving the first attempt. Do not
repair generated artifacts or repeat runs until a model wins. If allowance
or latency prevents N=8, report the actual smaller configuration honestly.
TLC, more specifications, mandatory third-arm controls, statistical repeats,
a native Mac adapter and further CI expansion are outside this finish line.
