import argparse, hashlib, json, os, re, secrets, shutil, subprocess, sys, tempfile, time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "scripts/contain/contamination-spec.json"
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
from mdseval.processutils import ProcessOutcome, run_process_group
from tooling import taskcheck

DOCKER = [os.environ.get("MDSEVAL_DOCKER", "/Applications/Docker.app/Contents/Resources/bin/docker"), "--config", os.environ.get("MDSEVAL_DOCKER_CONFIG", "/private/tmp/mdseval-public-docker-config"), "--host", os.environ.get("MDSEVAL_DOCKER_HOST", "unix:///Users/wade/.docker/run/docker.sock")]
PINS = Path(os.environ.get("MDSEVAL_INTERPRETERS", "/private/tmp/mdseval-interpreters-sealed"))
SECURITY = ("--cap-drop", "ALL", "--security-opt", "no-new-privileges=true", "--security-opt", "seccomp=unconfined", "--pids-limit", "256")
FIXED_ENV = ("HOME=/agent-home", "CODEX_HOME=/agent-home", "PYTHONHOME=/python", "PYTHONPATH=/sealed-deps", "PYTHONDONTWRITEBYTECODE=1", "PYTHONNOUSERSITE=1", "LANG=C.UTF-8", "PATH=/usr/lib/codex/bin:/usr/lib/codex/codex-path:/python/bin:/usr/bin:/bin")
PROXY_ENV = ("HTTPS_PROXY=http://model-proxy:8888", "HTTP_PROXY=http://model-proxy:8888")

def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
def spec_ids() -> list[str]:
    return sorted(json.loads(SPEC.read_text(encoding="utf-8")))
def _docker(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run([*DOCKER, *args], capture_output=True, text=True, check=False)
    if check and result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip())
    return result
def image_id(image: str) -> str:
    value = _docker("image", "inspect", "--format", "{{.Id}}", image).stdout.strip()
    if value != image or len(value) != 71 or not value.startswith("sha256:"):
        raise RuntimeError("runtime image is not the approved content-addressed digest")
    return value
def security_args(image: str, pin: str) -> list[str]:
    return ["internal-model-proxy", *SECURITY, "--user", f"{os.getuid()}:{os.getgid()}", "--workdir", "/workspace", *FIXED_ENV, *PROXY_ENV, "/workspace:rw", f"interpreter:{pin}:/python:ro", "fresh-agent-home:/agent-home:rw", image]

def security_sha256(image: str, pin: str) -> str:
    return sha(canonical(security_args(image, pin)).encode())
@contextmanager
def _home(codex_home: Path):
    auth = Path(codex_home) / "auth.json"
    if auth.is_symlink() or not auth.is_file() or not auth.stat().st_size:
        raise RuntimeError("sealed agent home source lacks safe auth.json")
    with tempfile.TemporaryDirectory(prefix="mdseval-agent-home-") as name:
        root = Path(name)
        shutil.copyfile(auth, root / "auth.json")
        os.chmod(root / "auth.json", 0o600)
        (root / "sessions").mkdir()
        entries = {path.relative_to(root).as_posix() for path in root.rglob("*")}
        if entries != {"auth.json", "sessions"} or any(path.is_symlink() for path in root.rglob("*")):
            raise RuntimeError("unsafe sealed agent home")
        yield root

def _args(image: str, pin: str, workspace: Path, home: Path, network: str) -> list[str]:
    python = (PINS / pin).resolve()
    workspace = workspace.resolve()
    home = home.resolve()
    if not all(path.is_dir() and not path.is_symlink() for path in (python, workspace, home)):
        raise RuntimeError("unsafe container bind source")
    args = [*DOCKER, "run", "--rm", "-i", "--network", network, *SECURITY, "--user", f"{os.getuid()}:{os.getgid()}", "--workdir", "/workspace"]
    for value in (*FIXED_ENV, *(() if network == "none" else PROXY_ENV)):
        args.extend(("-e", value))
    return [*args, "--mount", f"type=bind,src={workspace},dst=/workspace", "--mount", f"type=bind,src={python},dst=/python,readonly", "--mount", f"type=bind,src={home},dst=/agent-home", image]

def _run(image: str, pin: str, workspace: Path, codex_home: Path, network: str, command: list[str], *, stdin: str | None = None, timeout: int = 60) -> tuple[ProcessOutcome, list[str]]:
    with _home(codex_home) as home:
        args = [*_args(image, pin, workspace, home, network), *command]
        result = run_process_group(args, cwd=workspace, input_text=stdin, timeout=timeout, environment=os.environ.copy())
        return result, args

@contextmanager
def _network(image: str):
    suffix = secrets.token_hex(6)
    network = f"mdseval-{suffix}"
    proxy = f"mdseval-proxy-{suffix}"
    _docker("network", "create", "--internal", network)
    try:
        _docker("run", "-d", "--rm", "--name", proxy, "--network", network, "--network-alias", "model-proxy",
                "--cap-drop", "ALL", "--security-opt", "no-new-privileges=true", "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=1m",
                "--user", "tinyproxy:tinyproxy", image, "/usr/bin/tinyproxy", "-d", "-c", "/etc/tinyproxy/mdseval.conf")
        _docker("network", "connect", "bridge", proxy)
        details = json.loads(_docker("inspect", proxy).stdout)[0]
        ip = details["NetworkSettings"]["Networks"][network]["IPAddress"]
        yield network, ip
    finally:
        _docker("stop", proxy, check=False)
        _docker("network", "rm", network, check=False)

def _json_line(value: str) -> dict[str, Any]:
    rows = [json.loads(line) for line in value.splitlines() if line.strip()]
    if not rows or not isinstance(rows[-1], dict):
        raise RuntimeError("missing JSON record")
    return rows[-1]
def _identity(image: str, pin: str, workspace: Path, codex_home: Path, network: str = "none") -> dict[str, Any]:
    command = ["/python/bin/python3", "/usr/lib/mdseval/probe.py", "identity", image]
    result, _ = _run(image, pin, workspace, codex_home, network, command)
    row = _json_line(result.stdout)
    if result.returncode or row.pop("check", None) != "identity" or row.pop("status", None) != "PASS":
        raise RuntimeError("interpreter identity failed")
    return row

def _policy(image: str, pin: str, workspace: Path, codex_home: Path, network: str, ip: str) -> dict[str, Any]:
    child = ["/python/bin/python3", "/usr/lib/mdseval/probe.py", "policy-child", ip, "8888", image]
    retry = "import socket,sys,time\nfor i in range(30):\n try:\n  socket.create_connection((sys.argv[1],int(sys.argv[2])),3).close()\n  break\n except OSError:\n  if i==29: raise\n  time.sleep(.1)"
    bare, bare_argv = _run(image, pin, workspace, codex_home, network,
                           ["/python/bin/python3", "-c", retry, ip, "8888"])
    messages = [
        {"method": "initialize", "id": 1, "params": {"clientInfo": {"name": "mdseval_policy_probe", "title": "MD Eval policy probe", "version": "1"}, "capabilities": {"experimentalApi": True}}},
        {"method": "initialized", "params": {}},
        {"method": "command/exec", "id": 2, "params": {"command": child, "cwd": "/workspace", "disableOutputCap": True, "timeoutMs": 10000}}]
    with _home(codex_home) as app_home:
        app_argv = [*_args(image, pin, workspace, app_home, network), "/usr/lib/codex/bin/codex",
                    "-c", 'sandbox_mode="workspace-write"', "-c",
                    "sandbox_workspace_write.network_access=false", "app-server"]
        process = subprocess.Popen(app_argv, cwd=workspace, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                   encoding="utf-8", env=os.environ.copy(), start_new_session=True)
        process.stdin.write("".join(canonical(row) + "\n" for row in messages))
        process.stdin.flush()
        time.sleep(8)
        stdout, stderr = process.communicate(timeout=20)
        app = ProcessOutcome(process.returncode, stdout, stderr, False, False)
    reply = next((row for row in map(json.loads, app.stdout.splitlines()) if row.get("id") == 2), None)
    if bare.returncode or app.returncode or not reply or "result" not in reply:
        raise RuntimeError("policy export failed: " + canonical({"bare": [bare.returncode, bare.stderr[-1000:]], "app": [app.returncode, app.stdout[-1000:], app.stderr[-1000:]], "reply": reply}))
    source = _json_line(reply["result"]["stdout"])
    profile = source.get("permission_profile")
    if not profile:
        raise RuntimeError("policy child failed: " + canonical(reply))
    state = canonical({"permissionProfile": profile, "codexLinuxSandboxExe": "/usr/lib/codex/bin/codex",
                       "sandboxCwd": "file:///workspace", "useLegacyLandlock": False})
    replay, replay_argv = _run(image, pin, workspace, codex_home, network,
                               ["/usr/lib/codex/bin/codex", "sandbox", "--sandbox-state-json",
                                state, "--", *child])
    replay_row = _json_line(replay.stdout)
    if replay.returncode or source.get("status") != "DENIED" or replay_row.get("status") != "DENIED" or source.get("policy_sha256") != replay_row.get("policy_sha256"):
        raise RuntimeError("resolved policy replay mismatch")
    return {"bare_connect": True, "socket_target": replay_row["socket_target"],
            "source_argv": source["parent_argv"], "replay_argv": replay_row["parent_argv"],
            "source_sha256": source["policy_sha256"], "replay_sha256": replay_row["policy_sha256"],
            "source_identity": source["identity"], "replay_identity": replay_row["identity"],
            "denial": replay_row["denial"], "exit_status": replay_row["exit_status"],
            "identity": source["identity"], "bare_argv": bare_argv,
            "export_container_argv": app_argv, "replay_container_argv": replay_argv,
            "process_returncode": replay.returncode}

def probe(task_id: str, image: str, pin: str, codex_home: Path) -> tuple[str, str, int]:
    image_id(image)
    with tempfile.TemporaryDirectory(prefix="mdseval-probe-") as name, \
         _network(image) as (network, ip), _home(codex_home) as home:
        workspace = Path(name)
        shutil.copyfile(SPEC, workspace / "contamination-spec.json")
        policy = _policy(image, pin, workspace, codex_home, network, ip)
        checker_identity = _identity(image, pin, workspace, codex_home)
        command = ["/python/bin/python3", "/usr/lib/mdseval/probe.py", "container", task_id,
                   image, "/workspace/contamination-spec.json", "/workspace/runtime.json"]
        args = [*_args(image, pin, workspace, home, network), *command]
        runtime = {"runtime_args": args, "runtime_security_args": security_args(image, pin),
                   "runtime_security_sha256": security_sha256(image, pin), "policy": policy,
                   "policy_sha256": policy["source_sha256"],
                   "identity": {"subject": policy["identity"], "checker": checker_identity}}
        (workspace / "runtime.json").write_text(canonical(runtime) + "\n", encoding="utf-8")
        result = run_process_group(args, cwd=workspace, input_text=None, timeout=180,
                                   environment=os.environ.copy())
        return result.stdout, result.stderr, result.returncode

def subject(command: list[str], workspace: Path, final_path: Path, stdin: str, timeout: int, codex_home: Path, image: str, pin: str, seal: dict[str, Any]) -> ProcessOutcome:
    image_id(image)
    if seal.get("runtime_security_sha256") != security_sha256(image, pin):
        raise RuntimeError("approved runtime security mismatch")
    rewritten = list(command)
    rewritten[0] = "/usr/lib/codex/bin/codex"
    rewritten[rewritten.index("--cd") + 1] = "/workspace"
    temporary = workspace / ".mdseval-final"
    rewritten[rewritten.index("--output-last-message") + 1] = "/workspace/.mdseval-final"
    with _network(image) as (network, ip):
        policy = _policy(image, pin, workspace, codex_home, network, ip)
        if policy["source_sha256"] != seal.get("policy_sha256") or policy["identity"] != seal.get("identity"):
            raise RuntimeError("subject policy or identity mismatch")
        result, _ = _run(image, pin, workspace, codex_home, network, rewritten,
                         stdin=stdin, timeout=timeout)
    if temporary.is_file() and not temporary.is_symlink():
        final_path.write_bytes(temporary.read_bytes())
    temporary.unlink(missing_ok=True)
    return result

def checker(task: Path, source: Path, image: str, pin: str, codex_home: Path, expected: dict[str, Any] | None = None) -> tuple[dict[str, Any], bool, float, dict[str, Any]]:
    image_id(image)
    with tempfile.TemporaryDirectory(prefix="mdseval-score-") as name:
        root = Path(name)
        shutil.copy2(task / "check.py", root / "check.py")
        shutil.copytree(task / "private", root / "private")
        shutil.copytree(source, root / "source", ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
        identity = _identity(image, pin, root, codex_home)
        if expected is not None and identity != expected:
            raise RuntimeError("checker identity mismatch")
        started = time.monotonic()
        runs = [_run(image, pin, root, codex_home, "none",
                     ["/python/bin/python3", "/workspace/check.py", "/workspace/source"])[0]
                for _ in range(2)]
        duration = time.monotonic() - started
        evidence = {"identity": identity, "image_digest": image, "interpreter_pin": pin,
                    "runs": [{"returncode": run.returncode, "stdout": run.stdout,
                              "stderr": run.stderr, "timed_out": run.timed_out,
                              "interrupted": run.interrupted} for run in runs]}
        if any(run.returncode or run.timed_out or run.interrupted for run in runs):
            raise RuntimeError("container checker failed")
        deterministic = all((run.returncode, run.stdout, run.stderr) ==
                            (runs[0].returncode, runs[0].stdout, runs[0].stderr) for run in runs[1:])
        return taskcheck._parse_result(runs[0].stdout), deterministic, duration, evidence

def environment(task: Path, image: str, pin: str, codex_home: Path) -> dict[str, Any]:
    image_id(image)
    with tempfile.TemporaryDirectory(prefix="mdseval-verify-") as name:
        root = Path(name)
        tasks = root / "tasks"
        shutil.copytree(task.parent, tasks, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        command = ["/python/bin/python3", "/usr/lib/mdseval/taskcheck.py", "verify",
                   f"/workspace/tasks/{task.name}", "--md-filename", "CODER.md"]
        verify, _ = _run(image, pin, root, codex_home, "none", command, timeout=180)
    verify_row = _json_line(verify.stdout)
    manifest = verify_row.get("manifest_sha256")
    manifest_good = isinstance(manifest, str) and re.fullmatch(r"[0-9a-f]{64}", manifest) is not None
    verify_good = (not verify.returncode and not verify.stderr and verify.stdout == canonical(verify_row) + "\n" and set(verify_row) == {"task_id", "verified", "manifest_sha256"} and verify_row["task_id"] == task.name and verify_row["verified"] is True and manifest_good)
    public = checker(task, task / "public", image, pin, codex_home)
    reference = checker(task, task / "reference", image, pin, codex_home)
    identities = public[3]["identity"] == reference[3]["identity"]
    ok = (verify_good and not public[0]["resolved"] and all(public[0]["regressions"].values())
          and public[1] and reference[0]["resolved"] and reference[1] and identities)
    return {"task_id": task.name, "status": "ALL_GREEN" if ok else "EXCLUDED",
            "image_digest": image, "interpreter_pin": pin, "spec_sha256": sha(SPEC.read_bytes()),
            "spec_task_ids": spec_ids(), "task_manifest_sha256": manifest if manifest_good else None,
            "runtime_security_sha256": security_sha256(image, pin),
            "identity": public[3]["identity"],
            "taskcheck": {"returncode": verify.returncode, "stdout": verify.stdout, "stderr": verify.stderr},
            "public": {"result": public[0], "deterministic": public[1],
                       "duration_seconds": public[2], **public[3]},
            "reference": {"result": reference[0], "deterministic": reference[1],
                          "duration_seconds": reference[2], **reference[3]}}

def host_env(task_id: str, output: Path) -> dict[str, str]:
    path = output.resolve()
    task = (ROOT / "tasks" / task_id).resolve()
    good = (path.name == task_id + ".jsonl" and path.parent.name == "host"
            and path.parent.parent.name == "preflight" and task.is_dir() and not task.is_symlink())
    if not good:
        raise RuntimeError("host evidence or task root is not canonical")
    roots = {"task": str(task), "evidence": str(path.parents[2])}
    return {**os.environ, "MDSEVAL_WORKSPACE": str(task / "public"),
            "MDSEVAL_PROBE_EXCLUSIONS": canonical(roots)}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("probe", "environment", "host"))
    parser.add_argument("task_id")
    parser.add_argument("image")
    parser.add_argument("pin")
    parser.add_argument("auth_home", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    stderr = arguments.output.with_suffix(arguments.output.suffix + ".stderr")
    if arguments.output.exists() or stderr.exists():
        raise RuntimeError("preflight evidence path already exists")
    try:
        if arguments.mode == "probe":
            value = probe(arguments.task_id, arguments.image, arguments.pin, arguments.auth_home)
        elif arguments.mode == "environment":
            record = environment(ROOT / "tasks" / arguments.task_id, arguments.image,
                                 arguments.pin, arguments.auth_home)
            value = canonical(record) + "\n", "", 0
        else:
            command = [sys.executable, str(ROOT / "scripts/contain/probe.py"), "host",
                       arguments.task_id, arguments.image, str(SPEC)]
            host = subprocess.run(command, capture_output=True, text=True,
                                  env=host_env(arguments.task_id, arguments.output))
            value = host.stdout, host.stderr, host.returncode
    except Exception as exc:
        status = ("EXCLUDED" if arguments.mode == "environment" else "BUILD_REJECTED" if arguments.mode == "probe" else "CONTROL_FAILED")
        record = {"task_id": arguments.task_id, "status": status,
                  "image_digest": arguments.image, "interpreter_pin": arguments.pin,
                  "spec_sha256": sha(SPEC.read_bytes()), "spec_task_ids": spec_ids(),
                  "task_manifest_sha256": None,
                  "error": f"{type(exc).__name__}: {exc}"}
        if arguments.mode != "environment":
            record.update({"check": "summary", "failure_count": 1, "contamination_count": 0})
        value = canonical(record) + "\n", record["error"] + "\n", 2
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(value[0], encoding="utf-8")
    stderr.write_text(value[1], encoding="utf-8")
    return value[2]

if __name__ == "__main__":
    raise SystemExit(main())
