# MD Eval

MD Eval is a small, local, harness-independent evaluator for comparing two
versions of one agent instruction file against the same coding tasks. This MVP
evaluates the locked `CODER.md` target with a single-agent `codex exec` subject
runtime. It is not an instruction optimizer, OpenClaw integration, hosted
service, or security boundary for hostile instruction files.

The champion intentionally retains its source metadata line, `GPT-5.5 @ xhigh
reasoning`, while the experiment runtime is pinned separately to
`gpt-5.6-sol` with `high` reasoning. Reports preserve that mismatch as baseline
metadata rather than mutating the source baseline.

## Offline setup and acceptance

Python 3.12 is recommended; the implementation is standard-library-only. It
also runs directly from a clean source checkout without installation:

```bash
python -m unittest discover -s tests -v
python -m mdseval validate --experiment experiments/coder-v1.json
python -m mdseval demo --experiment experiments/coder-v1.json
```

On systems where Python is installed only as `python3`, substitute `python3`
literally. An editable install is optional:

```bash
python -m pip install -e .
mdseval validate --experiment experiments/coder-v1.json
```

The fake demo creates a complete ignored directory under `runs/`, including
raw per-run evidence and JSON/Markdown reports. It always reports `NOT_RUN` and
makes no claim about `CODER.md` quality.

## CODER outcomes V2 commands

The V2 oracle qualification is deterministic and makes no model calls. A
provisional qualification runs all eight tasks against pristine state, two
correct implementations, and two semantic mutants three times each (120 checker
executions), but does not issue a live-use receipt:

```bash
PYTHONPATH=src python3 -m mdseval.outcome_mvp \
  --experiment experiments/coder-outcomes-v2-mvp.json \
  qualify runs/coder-outcomes-v2-provisional
```

After separate commit authorization, run the authoritative form from that clean
exact commit with an isolated Codex home logged in through ChatGPT. It performs
local Git, isolated-runner, CLI-compatibility, and `codex login status` checks;
it still makes no model call. A passing run creates the commit- and hash-bound
receipt exactly once:

```bash
export MDSEVAL_CODEX_HOME="$HOME/.codex-mdseval"
PYTHONPATH=src python3 -m mdseval.outcome_mvp \
  --experiment experiments/coder-outcomes-v2-mvp.json \
  qualify runs/coder-outcomes-v2-qualification --authoritative
```

Only after a separate explicit LIVE authorization may the receipt-gated command
below be used. The manifest fixes ChatGPT OAuth, a 10,800-second aggregate wall
ceiling, a 300-second per-call cap, and a 60-call absolute cap:

```bash
PYTHONPATH=src python3 -m mdseval.outcome_mvp \
  --experiment experiments/coder-outcomes-v2-mvp.json \
  run runs/coder-outcomes-v2-live \
  runs/coder-outcomes-v2-qualification/qualification-receipt.json
```

Replay regenerates reports from preserved evidence without authentication,
network access, or model calls:

```bash
PYTHONPATH=src python3 -m mdseval.outcome_mvp \
  --experiment experiments/coder-outcomes-v2-mvp.json \
  replay runs/coder-outcomes-v2-live/raw-evidence.json \
  runs/coder-outcomes-v2-replay
```

## CODER beneficial-sensitivity M2 commands

Run the complete offline gate in this order. Provisional output belongs in a
temporary directory outside the repository:

```bash
python3 -m unittest discover -s tests -v
M2_OFFLINE_DIR="$(mktemp -d)"
PYTHONPATH=src python3 -m mdseval.beneficial_sensitivity validate \
  --experiment experiments/coder-beneficial-sensitivity-m2.json
PYTHONPATH=src python3 -m mdseval.beneficial_sensitivity qualify \
  --experiment experiments/coder-beneficial-sensitivity-m2.json \
  --output "$M2_OFFLINE_DIR/qualification"
PYTHONPATH=src python3 -m mdseval.beneficial_sensitivity verify-power \
  --experiment experiments/coder-beneficial-sensitivity-m2.json
PYTHONPATH=src python3 -m mdseval.beneficial_sensitivity simulate \
  --experiment experiments/coder-beneficial-sensitivity-m2.json \
  --output "$M2_OFFLINE_DIR/simulation"
git diff --check
git status --short
```

Each live stage requires its own explicit authorization receipt and must run in
order. There is no output or runtime override:

```bash
PYTHONPATH=src python3 -m mdseval.beneficial_sensitivity run-stage \
  --experiment experiments/coder-beneficial-sensitivity-m2.json \
  --instance <instance-id> --stage smoke \
  --authorization-receipt <smoke-authorization.json>
PYTHONPATH=src python3 -m mdseval.beneficial_sensitivity run-stage \
  --experiment experiments/coder-beneficial-sensitivity-m2.json \
  --instance <instance-id> --stage calibration \
  --authorization-receipt <calibration-authorization.json>
PYTHONPATH=src python3 -m mdseval.beneficial_sensitivity run-stage \
  --experiment experiments/coder-beneficial-sensitivity-m2.json \
  --instance <instance-id> --stage controls \
  --authorization-receipt <controls-authorization.json>
PYTHONPATH=src python3 -m mdseval.beneficial_sensitivity run-stage \
  --experiment experiments/coder-beneficial-sensitivity-m2.json \
  --instance <instance-id> --stage helpful \
  --authorization-receipt <helpful-authorization.json>
```

Stop on any predeclared gate, integrity failure, unresolved validation blocker,
or call-cap condition. Replay only after an allowed terminal verdict:

```bash
PYTHONPATH=src python3 -m mdseval.beneficial_sensitivity replay \
  --experiment experiments/coder-beneficial-sensitivity-m2.json \
  --instance <instance-id>
```

There is no dollar-ceiling argument, oracle-passed assertion, or runtime
implementation-path allowlist. Each subject observation preserves raw capture,
the resulting workspace, protected-contract hashes, baseline/final tree hashes,
and an explicit reconstructable patch. Missing usage or tool events remain
nullable efficiency evidence and never alter the objective winner rule.

## Add and compare candidates

Keep `candidates/coder/karpathy-v1.md` unchanged. Add each manual candidate as an immutable, versioned `candidates/coder/<candidate-id>.md` file and add only its path to the flat `variants` mapping in `experiments/coder-v1.json`. `validate` lists registered candidates in sorted ID/path/SHA-256 order. Commit the candidate and mapping together; live work requires that clean, exact evaluator/experiment commit.

Run fresh A/A and bad-control gates for that state. Candidates registered together may share those exact-commit controls, but their results never pool. Compare one selected candidate at a time with `--variant-a champion --variant-b <candidate-id>` on development. Reports and evidence name its ID and hash; sealed holdout binds that exact candidate's completed development lineage. Review development and obtain explicit approval before holdout: `run --suite holdout` is rejected, so use only the sealed pair command.

Nothing automatically retries, advances stages, or starts another candidate. Preserve manual reruns as separate attempts; disclose quality-informed attempts as exploratory. There is no multiplicity correction across candidates, and `PROMOTE` remains a heuristic recommendation. Once holdouts inform tuning, later use is exploratory; a new confirmatory claim needs fresh undisclosed holdouts. Maximum calls are controls 72, development 48, holdout 12, and a complete one-candidate cycle 132.

Deferred: dashboard/UI; candidate add/discovery and batch/tournament commands; candidate-independent calibration reuse; retry/exploratory ledgers or verdicts; holdout-exposure ledgers/fresh-holdout machinery; multiplicity corrections; development-verdict gating; a global live-call canary; raw duplicate-key hardening; and generalized snapshot, locking, or runner refactors. Schema/report version 1, inputs, controls, statistics, and promotion gates remain unchanged.

## Live Codex setup

Use a dedicated Codex home. The evaluator never copies credentials from another
profile and never writes credential values into configuration or artifacts:

```bash
mkdir -p "$HOME/.codex-mdseval"
CODEX_HOME="$HOME/.codex-mdseval" codex login
export MDSEVAL_CODEX_HOME="$HOME/.codex-mdseval"
python -m mdseval doctor \
  --experiment experiments/coder-v1.json \
  --runner codex
```

The default doctor runs only executable/version/help checks and does not make a
model call. An explicit minimal authenticated call is available with
`--live-smoke`.

```bash
python -m mdseval doctor \
  --experiment experiments/coder-v1.json \
  --runner codex \
  --live-smoke
```

Run one live champion smoke pass:

```bash
python -m mdseval run \
  --experiment experiments/coder-v1.json \
  --variant champion \
  --suite smoke \
  --repeats 1
```

Run the live gates in order:

```bash
python -m mdseval calibrate \
  --experiment experiments/coder-v1.json \
  --suite dev \
  --repeats 2

python -m mdseval compare \
  --experiment experiments/coder-v1.json \
  --variant-a champion \
  --variant-b deliberately-bad \
  --suite dev \
  --repeats 1

python -m mdseval compare \
  --experiment experiments/coder-v1.json \
  --variant-a champion \
  --variant-b karpathy-v1 \
  --suite dev \
  --repeats 2

python -m mdseval compare \
  --experiment experiments/coder-v1.json \
  --variant-a champion \
  --variant-b karpathy-v1 \
  --suite holdout \
  --repeats 2 \
  --seal-candidate
```

The sealed holdout command refuses to start unless the latest completed development evidence matching the requested candidate ID and current hash has intact, fully matching report and manifest lineage.
Promotion is only a recommendation; the evaluator never rewrites the champion.
Live commands also require the evaluator repository to be intentionally
committed and clean so the recorded evaluator identity is stable.

## Evidence and isolation

Every subject run starts from a fresh Git repository containing only the case
fixture, the selected variant as `CODER.md`, the contract as
`.issue-contract.md`, and the fixed wrapper prompt. Hidden checks run after the
subject exits. Agent-command network access and subagents are disabled. The
qualitative judge receives a separately created blinded packet and never sees
variant names, instruction contents, or source evidence paths.

Raw artifacts include event JSONL, stderr, final response, complete baseline
diff evidence, untracked-file metadata/content, command order, hidden checks,
mechanical fields, usage, duration, and frozen manifests. Untracked content is
bounded to 65,536 bytes per file and 524,288 bytes per run. Only central Python
cache paths are excluded; source-controlled ignore files cannot hide artifacts.
Configured secret values and credential-shaped command assignments are redacted.

This practical isolation is for trusted, manually written candidates. It is not
secure against a deliberately hostile instruction file or prompt injection.
Before autonomous candidate generation, holdouts and evaluator code must move
behind a stronger process or container boundary.

The complete implementation authority is
[`docs/coder-single-file-mvp-spec.md`](docs/coder-single-file-mvp-spec.md).
