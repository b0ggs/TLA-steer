import argparse, errno, hashlib, json, os, re, secrets, shutil, subprocess, sys, tempfile, time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "scripts/contain/contamination-spec.json"
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
from mdseval.capture import parse_event_stream
from mdseval.processutils import ProcessOutcome, _stop_group, run_process_group
from tooling import taskcheck

DOCKER = [os.environ.get("MDSEVAL_DOCKER", "/Applications/Docker.app/Contents/Resources/bin/docker"), "--config", os.environ.get("MDSEVAL_DOCKER_CONFIG", "/private/tmp/mdseval-public-docker-config"), "--host", os.environ.get("MDSEVAL_DOCKER_HOST", "unix:///Users/wade/.docker/run/docker.sock")]
PINS = Path(os.environ.get("MDSEVAL_INTERPRETERS", "/private/tmp/mdseval-interpreters-sealed"))
SECURITY = ("--cap-drop", "ALL", "--security-opt", "no-new-privileges=true", "--security-opt", "seccomp=unconfined", "--pids-limit", "256")
FIXED_ENV = ("HOME=/agent-home", "CODEX_HOME=/agent-home", "PYTHONHOME=/python", "PYTHONPATH=/sealed-deps", "PYTHONDONTWRITEBYTECODE=1", "PYTHONNOUSERSITE=1", "LANG=C.UTF-8", "PATH=/usr/lib/codex/bin:/usr/lib/codex/codex-path:/python/bin:/usr/bin:/bin")
PROXY_ENV = ("HTTPS_PROXY=http://model-proxy:8888", "HTTP_PROXY=http://model-proxy:8888")
WEB_SEARCH_DISABLED_CONFIG = 'web_search="disabled"'
WEB_SEARCH_DISABLED_EVIDENCE = {"mode": "disabled", "origin_type": "sessionFlags", "session_layer_modes": ["disabled"]}
FAST_SEAL_SCHEMA = "fast-preflight-v1"
FAST_MOUNTS = {"/agent-home": "rw", "/python": "ro", "/workspace": "rw"}
FAST_SANDBOX = {"mode": "workspace-write", "network_access": False}
CONTAINER_KEYSETS = {frozenset({"image_digests", "spec_sha256", "interpreter_pins"}),
                     frozenset({"image_digests", "spec_sha256", "interpreter_pins", "web_search"})}

_TARGETED_SMOKE_SCRIPT = r'''
import hashlib, inspect, json, os, pathlib, platform, pydoc, re, shutil, socket, stat, sys, time, tokenize

def need(value, message):
    if not value:
        raise RuntimeError(message)

def digest(value):
    if isinstance(value, str):
        value = value.encode()
    return hashlib.sha256(value).hexdigest()

def normalized(value):
    return "".join(character for character in value if not character.isspace())

def unescape(value):
    return re.sub(r"\\([0-7]{3})", lambda match: chr(int(match.group(1), 8)), value)

def mounts():
    found = {}
    with open("/proc/self/mountinfo", encoding="utf-8") as stream:
        for line in stream:
            left, right = line.rstrip("\n").split(" - ", 1)
            fields = left.split()
            need(len(fields) >= 6 and len(right.split()) >= 3, "malformed mount table")
            target = unescape(fields[4])
            found.setdefault(target, []).append(set(fields[5].split(",")))
    expected = {"/workspace": "rw", "/python": "ro", "/agent-home": "rw"}
    for target, mode in expected.items():
        need(len(found.get(target, [])) == 1 and mode in found[target][0],
             "unexpected mount: " + target)
    marker = pathlib.Path("/workspace/.mdseval-runtime-smoke")
    marker.write_text("workspace-write", encoding="utf-8")
    need(marker.read_text(encoding="utf-8") == "workspace-write", "workspace is not writable")
    marker.unlink()
    return expected

def identity(image, pin):
    executable = os.path.realpath(sys.executable)
    resolution = shutil.which("python3")
    need(platform.python_version() == pin, "interpreter pin mismatch")
    need(executable.startswith("/python/") and resolution is not None
         and os.path.realpath(resolution) == executable, "interpreter path mismatch")
    return {"canonical_executable": executable, "version": sys.version,
            "executable_sha256": digest(pathlib.Path(executable).read_bytes()),
            "image_digest": image, "path_resolution": resolution}

def auth():
    home = pathlib.Path("/agent-home")
    source = home / "auth.json"
    sessions = home / "sessions"
    source_mode = os.lstat(source).st_mode
    need(stat.S_ISREG(source_mode) and not stat.S_ISLNK(source_mode)
         and source.stat().st_size > 0, "unsafe isolated auth")
    need(sessions.is_dir() and not sessions.is_symlink(), "unsafe isolated sessions")
    need({path.name for path in home.iterdir()} == {"auth.json", "sessions"},
         "unsafe isolated auth topology")
    return "isolated-readable"

def python_source(path):
    with tokenize.open(path) as stream:
        return stream.read()

def sources(target):
    if target.startswith("filesystem:"):
        relative = target.split(":", 1)[1]
        result = []
        for entry in sys.path:
            base = os.path.abspath(entry or os.getcwd())
            candidate = os.path.normpath(os.path.join(base, relative))
            if not os.path.isfile(candidate) or os.path.islink(candidate):
                continue
            result.append((candidate, python_source(candidate)))
        return sorted(set(result))
    try:
        value = pydoc.locate(target)
        if value is None:
            return []
        source = inspect.getsource(value)
        origin = inspect.getsourcefile(value) or inspect.getfile(value)
        return [(origin, source)]
    except Exception:
        return []

def targets(spec):
    rows = []
    for task_id in sorted(spec):
        item = spec[task_id]
        signatures = [(digest(value), normalized(value))
                      for value in item["fix_signature_strings"]]
        for target in item["answer_bearing_modules"]:
            located = sources(target)
            source_hashes = sorted(digest(normalized(source)) for _, source in located)
            matches = sorted(signature_hash for signature_hash, signature in signatures
                             if any(signature in normalized(source) for _, source in located))
            need(not matches, "fix signature present in targeted source: " + target)
            rows.append({"task_id": task_id, "target": target,
                         "source_available": bool(located),
                         "source_sha256": source_hashes,
                         "checked_signature_sha256": sorted(value[0] for value in signatures)})
    return rows

def bare_connect(host, port):
    last = None
    for _ in range(30):
        try:
            connection = socket.create_connection((host, port), timeout=1)
            connection.close()
            return True
        except OSError as exc:
            last = exc
            time.sleep(0.1)
    raise RuntimeError("isolated proxy is unreachable: " + type(last).__name__)

def main():
    payload = json.load(sys.stdin)
    rows = targets(payload["tasks"])
    result = {"status": "PASS", "identity": identity(payload["image"], payload["pin"]),
              "mounts": mounts(), "auth": auth(), "bare_connect": bare_connect(
                  payload["proxy_host"], payload["proxy_port"]),
              "target_checks": rows}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))

try:
    main()
except Exception as exc:
    print(json.dumps({"status": "FAIL", "error": type(exc).__name__ + ": " + str(exc)},
                     sort_keys=True, separators=(",", ":")))
    raise SystemExit(2)
'''

_POLICY_CHILD_SCRIPT = r'''
import errno, hashlib, json, os, pathlib, re, shutil, socket, sys

def need(value, message):
    if not value:
        raise RuntimeError(message)

def digest_argv(values):
    return hashlib.sha256(b"\0".join(os.fsencode(value) for value in values) + b"\0").hexdigest()

def identity(image):
    executable = os.path.realpath(sys.executable)
    return {"canonical_executable": executable, "version": sys.version,
            "executable_sha256": hashlib.sha256(pathlib.Path(executable).read_bytes()).hexdigest(),
            "image_digest": image, "path_resolution": shutil.which("python3")}

def policy_shape(argv):
    starts = [index for index, value in enumerate(argv) if value == "--sandbox-policy-cwd"]
    ends = [index for index, value in enumerate(argv) if value == "--apply-seccomp-then-exec"]
    need(len(starts) == len(ends) == 1 and starts[0] < ends[0], "non-unique policy bounds")
    policy = argv[starts[0]:ends[0] + 1]
    need(sum(os.path.basename(value) == "bwrap" for value in argv) == 1,
         "non-unique bwrap")
    need(sum("codex-linux-sandbox" in os.path.basename(value) for value in argv) == 1,
         "non-unique sandbox helper")
    need("--use-legacy-landlock" not in argv, "legacy Landlock")
    for flag in ("--sandbox-policy-cwd", "--command-cwd"):
        need(policy.count(flag) == 1 and policy[policy.index(flag) + 1] == "/workspace", flag)
    need(policy.count("--permission-profile") == 1, "missing permission profile")
    profile = json.loads(policy[policy.index("--permission-profile") + 1])
    flat = "".join(character for character in json.dumps(profile, sort_keys=True)
                   if not character.isspace()).lower().replace("-", "").replace("_", "")
    need('"type":"managed"' in flat and '"path":"/workspace"' in flat
         and '"access":"write"' in flat and '"network":"restricted"' in flat,
         "profile is not network-free workspace-write")
    return policy, profile

def main():
    status = pathlib.Path("/proc/self/status").read_text(encoding="utf-8")
    parent_pid = int(re.search(r"^PPid:\s*(\d+)$", status, re.M).group(1))
    raw = pathlib.Path("/proc/%d/cmdline" % parent_pid).read_bytes()
    parent = [os.fsdecode(value) for value in raw.rstrip(b"\0").split(b"\0")]
    policy, profile = policy_shape(parent)
    row = {"identity": identity(sys.argv[3]), "permission_profile": profile,
           "policy_sha256": digest_argv(policy), "socket_target": [sys.argv[1], int(sys.argv[2])]}
    try:
        connection = socket.create_connection((sys.argv[1], int(sys.argv[2])), timeout=5)
        connection.close()
        row.update({"status": "FAIL", "denial": None, "exit_status": 0})
        code = 2
    except PermissionError as exc:
        explicit = exc.errno == errno.EPERM
        row.update({"status": "DENIED" if explicit else "FAIL",
                    "denial": "PermissionError: " + str(exc), "exit_status": exc.errno})
        code = 0 if explicit else 2
    except Exception as exc:
        row.update({"status": "FAIL", "denial": type(exc).__name__ + ": " + str(exc),
                    "exit_status": getattr(exc, "errno", 2)})
        code = 2
    print(json.dumps(row, sort_keys=True, separators=(",", ":")))
    return code

try:
    raise SystemExit(main())
except Exception as exc:
    print(json.dumps({"status": "FAIL", "error": type(exc).__name__ + ": " + str(exc)},
                     sort_keys=True, separators=(",", ":")))
    raise SystemExit(2)
'''

def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def _remaining(deadline: float | None, check: str) -> float | None:
    if deadline is None:
        return None
    if isinstance(deadline, bool) or not isinstance(deadline, (int, float)):
        raise ValueError("preflight deadline must be an absolute monotonic time")
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError(f"global preflight deadline expired during {check}")
    return remaining

def spec_ids() -> list[str]:
    return sorted(json.loads(SPEC.read_text(encoding="utf-8")))

def _docker(*args: str, check: bool = True,
            deadline: float | None = None) -> subprocess.CompletedProcess[str]:
    timeout = _remaining(deadline, "docker " + " ".join(args))
    try:
        result = subprocess.run([*DOCKER, *args], capture_output=True, text=True,
                                check=False, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError("global preflight deadline expired during docker "
                           + " ".join(args)) from exc
    _remaining(deadline, "docker " + " ".join(args))
    if check and result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip())
    return result

def image_id(image: str, *, deadline: float | None = None) -> str:
    value = _docker("image", "inspect", "--format", "{{.Id}}", image,
                    deadline=deadline).stdout.strip()
    if value != image or len(value) != 71 or not value.startswith("sha256:"):
        raise RuntimeError("runtime image is not the approved content-addressed digest")
    return value
def security_args(image: str, pin: str) -> list[str]:
    return ["internal-model-proxy", *SECURITY, "--user", f"{os.getuid()}:{os.getgid()}", "--workdir", "/workspace", *FIXED_ENV, *PROXY_ENV, "/workspace:rw", f"interpreter:{pin}:/python:ro", "fresh-agent-home:/agent-home:rw", image]

def security_sha256(image: str, pin: str) -> str:
    return sha(canonical(security_args(image, pin)).encode())

def _pin_path(pin: str, *, deadline: float | None = None) -> Path:
    _remaining(deadline, "interpreter pin")
    if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", pin) is None:
        raise RuntimeError("unsafe interpreter pin")
    source = PINS / pin
    if (PINS.is_symlink() or not PINS.is_dir() or source.is_symlink()
            or not source.is_dir() or source.resolve() != PINS.resolve() / pin):
        raise RuntimeError("unsafe interpreter pin source")
    _remaining(deadline, "interpreter pin")
    return source.resolve()

@contextmanager
def _home(codex_home: Path, *, deadline: float | None = None):
    _remaining(deadline, "isolated auth source")
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
        _remaining(deadline, "isolated auth source")
        yield root

def _args(image: str, pin: str, workspace: Path, home: Path, network: str) -> list[str]:
    python = _pin_path(pin)
    workspace = workspace.resolve()
    home = home.resolve()
    if not all(path.is_dir() and not path.is_symlink() for path in (python, workspace, home)):
        raise RuntimeError("unsafe container bind source")
    args = [*DOCKER, "run", "--rm", "-i", "--network", network, *SECURITY, "--user", f"{os.getuid()}:{os.getgid()}", "--workdir", "/workspace"]
    for value in (*FIXED_ENV, *(() if network == "none" else PROXY_ENV)):
        args.extend(("-e", value))
    return [*args, "--mount", f"type=bind,src={workspace},dst=/workspace", "--mount", f"type=bind,src={python},dst=/python,readonly", "--mount", f"type=bind,src={home},dst=/agent-home", image]

def _run(image: str, pin: str, workspace: Path, codex_home: Path, network: str,
         command: list[str], *, stdin: str | None = None, timeout: float = 60,
         deadline: float | None = None,
         linger_seconds: float = 0.0) -> tuple[ProcessOutcome, list[str]]:
    with _home(codex_home, deadline=deadline) as home:
        args = [*_args(image, pin, workspace, home, network), *command]
        remaining = _remaining(deadline, "sealed container process")
        if remaining is not None and remaining <= 1.1:
            raise TimeoutError("global preflight deadline expired before sealed process cleanup")
        process_timeout = min(timeout, remaining - 1.1) if remaining is not None else timeout
        if not linger_seconds:
            result = run_process_group(args, cwd=workspace, input_text=stdin,
                                       timeout=process_timeout, environment=os.environ.copy())
        else:
            if stdin is None or linger_seconds <= 0:
                raise ValueError("lingering sealed process requires nonempty stdin")
            process = subprocess.Popen(
                args, cwd=workspace, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, encoding="utf-8",
                env=os.environ.copy(), start_new_session=True)
            try:
                assert process.stdin is not None
                process.stdin.write(stdin)
                process.stdin.flush()
                time.sleep(min(linger_seconds, max(0.0, process_timeout - 1.0)))
                process.stdin.close()
                process.stdin = None
                stdout, stderr = process.communicate(timeout=max(0.1, process_timeout - linger_seconds))
                result = ProcessOutcome(process.returncode, stdout or "", stderr or "", False, False)
            except subprocess.TimeoutExpired as exc:
                _stop_group(process)
                process.communicate(timeout=1)
                raise TimeoutError("global preflight deadline expired during sealed container process") from exc
            except BaseException:
                _stop_group(process)
                process.communicate(timeout=1)
                raise
        _remaining(deadline, "sealed container process")
        if deadline is not None and result.timed_out:
            raise TimeoutError("global preflight deadline expired during sealed container process")
        return result, args

@contextmanager
def _network(image: str, *, deadline: float | None = None):
    suffix = secrets.token_hex(6)
    network = f"mdseval-{suffix}"
    proxy = f"mdseval-proxy-{suffix}"
    _docker("network", "create", "--internal", network, deadline=deadline)
    try:
        _docker("run", "-d", "--rm", "--name", proxy, "--network", network, "--network-alias", "model-proxy",
                "--cap-drop", "ALL", "--security-opt", "no-new-privileges=true", "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=1m",
                "--user", "tinyproxy:tinyproxy", image, "/usr/bin/tinyproxy", "-d", "-c", "/etc/tinyproxy/mdseval.conf",
                deadline=deadline)
        _docker("network", "connect", "bridge", proxy, deadline=deadline)
        details = json.loads(_docker("inspect", proxy, deadline=deadline).stdout)[0]
        ip = details["NetworkSettings"]["Networks"][network]["IPAddress"]
        yield network, ip
    finally:
        for arguments in (("stop", "--time", "1", proxy), ("network", "rm", network)):
            try:
                _docker(*arguments, check=False, deadline=deadline)
            except (OSError, RuntimeError, TimeoutError, subprocess.SubprocessError):
                pass

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

def _resolved_web_search(reply: dict[str, Any]) -> dict[str, Any]:
    result = reply.get("result") if isinstance(reply, dict) else None
    config = result.get("config") if isinstance(result, dict) else None
    origins = result.get("origins") if isinstance(result, dict) else None
    layers = result.get("layers") if isinstance(result, dict) else None
    origin = origins.get("web_search") if isinstance(origins, dict) else None
    name = origin.get("name") if isinstance(origin, dict) else None
    session_modes = [layer.get("config", {}).get("web_search") for layer in layers
                     if isinstance(layer, dict) and layer.get("name") == {"type": "sessionFlags"}
                     and isinstance(layer.get("config"), dict)] if isinstance(layers, list) else []
    evidence = {"mode": config.get("web_search") if isinstance(config, dict) else None,
                "origin_type": name.get("type") if isinstance(name, dict) else None,
                "session_layer_modes": session_modes}
    if evidence != WEB_SEARCH_DISABLED_EVIDENCE:
        raise RuntimeError("resolved web search is not disabled by the session flag")
    return evidence

def container_web_search_valid(value: dict[str, Any], required: bool) -> bool:
    return (("web_search" not in value or value["web_search"] == "disabled")
            and (not required or value.get("web_search") == "disabled"))

def bind_web_search_evidence(result: dict[str, Any], container: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    if container.get("web_search") != "disabled":
        return result
    evidence = policy.get("policy", {}).get("web_search")
    if evidence != WEB_SEARCH_DISABLED_EVIDENCE:
        raise RuntimeError("sealed preflight does not prove web search disabled")
    return {**result, "web_search": evidence}

def event_usage_and_web_search(path: Path) -> tuple[dict[str, int], bool]:
    parsed = parse_event_stream(path)
    seen = any(isinstance(item := event.get("item"), dict) and item.get("type") == "web_search"
               for event in parsed.events)
    return parsed.usage, seen

def _policy(image: str, pin: str, workspace: Path, codex_home: Path, network: str, ip: str) -> dict[str, Any]:
    child = ["/python/bin/python3", "/usr/lib/mdseval/probe.py", "policy-child", ip, "8888", image]
    retry = "import socket,sys,time\nfor i in range(30):\n try:\n  socket.create_connection((sys.argv[1],int(sys.argv[2])),3).close()\n  break\n except OSError:\n  if i==29: raise\n  time.sleep(.1)"
    bare, bare_argv = _run(image, pin, workspace, codex_home, network,
                           ["/python/bin/python3", "-c", retry, ip, "8888"])
    messages = [
        {"method": "initialize", "id": 1, "params": {"clientInfo": {"name": "mdseval_policy_probe", "title": "MD Eval policy probe", "version": "1"}, "capabilities": {"experimentalApi": True}}},
        {"method": "initialized", "params": {}},
        {"method": "config/read", "id": 2, "params": {"cwd": "/workspace", "includeLayers": True}},
        {"method": "command/exec", "id": 3, "params": {"command": child, "cwd": "/workspace", "disableOutputCap": True, "timeoutMs": 10000}}]
    with _home(codex_home) as app_home:
        app_argv = [*_args(image, pin, workspace, app_home, network), "/usr/lib/codex/bin/codex",
                    "--strict-config", "-c", WEB_SEARCH_DISABLED_CONFIG,
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
    rows = list(map(json.loads, app.stdout.splitlines()))
    config_replies = [row for row in rows if row.get("id") == 2]
    replies = [row for row in rows if row.get("id") == 3]
    if bare.returncode or app.returncode or len(config_replies) != 1 or len(replies) != 1 or "result" not in replies[0]:
        raise RuntimeError("policy export failed: " + canonical({"bare": [bare.returncode, bare.stderr[-1000:]], "app": [app.returncode, app.stdout[-1000:], app.stderr[-1000:]], "config_replies": config_replies, "replies": replies}))
    web_search = _resolved_web_search(config_replies[0])
    reply = replies[0]
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
            "process_returncode": replay.returncode, "web_search": web_search}

def _valid_smoke_item(value: Any) -> bool:
    target = r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*"
    filesystem = r"filesystem:(?!/)(?!\.\.(?:/|$))(?!.*?/\.\.(?:/|$))[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\.py"
    return (isinstance(value, dict)
            and set(value) == {"answer_bearing_modules", "fix_signature_strings", "interpreter_pin"}
            and isinstance(value["answer_bearing_modules"], list)
            and bool(value["answer_bearing_modules"])
            and len(value["answer_bearing_modules"]) == len(set(value["answer_bearing_modules"]))
            and all(isinstance(item, str) and re.fullmatch(target + "|" + filesystem, item)
                    for item in value["answer_bearing_modules"])
            and isinstance(value["fix_signature_strings"], list)
            and bool(value["fix_signature_strings"])
            and len(value["fix_signature_strings"]) == len(set(value["fix_signature_strings"]))
            and all(isinstance(item, str)
                    and len("".join(character for character in item
                                    if not character.isspace())) >= 20
                    for item in value["fix_signature_strings"])
            and isinstance(value["interpreter_pin"], str)
            and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value["interpreter_pin"]) is not None)

def _smoke_spec(task_ids: list[str], pin: str,
                deadline: float | None = None) -> tuple[dict[str, Any], str]:
    _remaining(deadline, "contamination specification")
    if (not isinstance(task_ids, list) or not task_ids
            or any(not isinstance(task_id, str) for task_id in task_ids)
            or len(task_ids) != len(set(task_ids))):
        raise RuntimeError("runtime smoke task IDs are invalid")
    raw = SPEC.read_bytes()
    try:
        full = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("contamination specification is malformed") from exc
    ids = sorted(task_ids)
    if (not isinstance(full, dict) or any(task_id not in full for task_id in ids)
            or any(not _valid_smoke_item(full[task_id]) for task_id in ids)):
        raise RuntimeError("runtime smoke tasks are absent or malformed in contamination specification")
    selected = {task_id: full[task_id] for task_id in ids}
    if any(value["interpreter_pin"] != pin for value in selected.values()):
        raise RuntimeError("runtime smoke interpreter pin differs from contamination specification")
    _remaining(deadline, "contamination specification")
    return selected, sha(raw)

def _targeted_smoke(image: str, pin: str, tasks: dict[str, Any], workspace: Path,
                    codex_home: Path, network: str, ip: str,
                    deadline: float) -> dict[str, Any]:
    payload = canonical({"image": image, "pin": pin, "proxy_host": ip,
                         "proxy_port": 8888, "tasks": tasks})
    command = ["/python/bin/python3", "-c", _TARGETED_SMOKE_SCRIPT]
    result, _ = _run(image, pin, workspace, codex_home, network, command,
                     stdin=payload, deadline=deadline)
    try:
        row = _json_line(result.stdout)
    except (UnicodeError, json.JSONDecodeError, RuntimeError, TypeError) as exc:
        raise RuntimeError("targeted sealed-runtime smoke returned malformed JSON") from exc
    if result.returncode or row.get("status") != "PASS":
        raise RuntimeError("targeted sealed-runtime smoke failed: "
                           + str(row.get("error", result.stderr[-500:])))
    if (set(row) != {"status", "identity", "mounts", "auth", "bare_connect", "target_checks"}
            or row["mounts"] != FAST_MOUNTS or row["auth"] != "isolated-readable"
            or row["bare_connect"] is not True or not isinstance(row["identity"], dict)
            or not isinstance(row["target_checks"], list)):
        raise RuntimeError("targeted sealed-runtime smoke proof is incomplete")
    expected = [(task_id, target,
                 sorted(sha(signature.encode())
                        for signature in tasks[task_id]["fix_signature_strings"]))
                for task_id in sorted(tasks)
                for target in tasks[task_id]["answer_bearing_modules"]]
    checks = row["target_checks"]
    if len(checks) != len(expected):
        raise RuntimeError("targeted contamination check coverage is incomplete")
    for check, (task_id, target, signatures) in zip(checks, expected):
        good = (isinstance(check, dict)
                and set(check) == {"task_id", "target", "source_available",
                                   "source_sha256", "checked_signature_sha256"}
                and check["task_id"] == task_id and check["target"] == target
                and isinstance(check["source_available"], bool)
                and isinstance(check["source_sha256"], list)
                and all(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
                        for value in check["source_sha256"])
                and check["checked_signature_sha256"] == signatures)
        if not good:
            raise RuntimeError("targeted contamination check proof is malformed")
    identity = row["identity"]
    identity_good = (set(identity) == {"canonical_executable", "version", "executable_sha256",
                                      "image_digest", "path_resolution"}
                     and identity["image_digest"] == image
                     and isinstance(identity["canonical_executable"], str)
                     and identity["canonical_executable"].startswith("/python/")
                     and isinstance(identity["path_resolution"], str)
                     and identity["path_resolution"].startswith("/python/")
                     and isinstance(identity["version"], str)
                     and identity["version"].startswith(pin)
                     and isinstance(identity["executable_sha256"], str)
                     and re.fullmatch(r"[0-9a-f]{64}", identity["executable_sha256"]) is not None)
    if not identity_good:
        raise RuntimeError("sealed interpreter identity proof is malformed")
    return row

def _fast_policy_messages(ip: str, image: str) -> list[dict[str, Any]]:
    child = ["/python/bin/python3", "-I", "-c", _POLICY_CHILD_SCRIPT, ip, "8888", image]
    return [
        {"method": "initialize", "id": 1,
         "params": {"clientInfo": {"name": "mdseval_fast_preflight",
                                    "title": "MD Eval fast preflight", "version": "1"},
                    "capabilities": {"experimentalApi": True}}},
        {"method": "initialized", "params": {}},
        {"method": "config/read", "id": 2,
         "params": {"cwd": "/workspace", "includeLayers": True}},
        {"method": "command/exec", "id": 3,
         "params": {"command": child, "cwd": "/workspace",
                    "disableOutputCap": True, "timeoutMs": 10000}},
    ]

def _fast_policy(image: str, pin: str, workspace: Path, codex_home: Path,
                 network: str, ip: str, deadline: float) -> dict[str, Any]:
    command = ["/usr/lib/codex/bin/codex", "--strict-config", "-c",
               WEB_SEARCH_DISABLED_CONFIG, "-c", 'sandbox_mode="workspace-write"',
               "-c", "sandbox_workspace_write.network_access=false", "app-server"]
    stdin = "".join(canonical(row) + "\n" for row in _fast_policy_messages(ip, image))
    result, _ = _run(image, pin, workspace, codex_home, network, command,
                     stdin=stdin, deadline=deadline, linger_seconds=5.0)
    try:
        rows = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    except (UnicodeError, json.JSONDecodeError, TypeError) as exc:
        raise RuntimeError("fast policy smoke returned malformed JSON") from exc
    config_replies = [row for row in rows if isinstance(row, dict) and row.get("id") == 2]
    command_replies = [row for row in rows if isinstance(row, dict) and row.get("id") == 3]
    if (result.returncode or len(config_replies) != 1 or len(command_replies) != 1
            or not isinstance(command_replies[0].get("result"), dict)):
        detail = {"returncode": result.returncode, "timed_out": result.timed_out,
                  "interrupted": result.interrupted,
                  "config_reply_count": len(config_replies),
                  "command_reply_count": len(command_replies),
                  "stdout_tail": result.stdout[-1000:], "stderr_tail": result.stderr[-1000:]}
        raise RuntimeError("fast policy smoke failed: " + canonical(detail))
    web_search = _resolved_web_search(config_replies[0])
    try:
        source = _json_line(command_replies[0]["result"]["stdout"])
    except (KeyError, TypeError, UnicodeError, json.JSONDecodeError, RuntimeError) as exc:
        raise RuntimeError("fast policy child returned malformed JSON") from exc
    denial = source.get("denial")
    good = (source.get("status") == "DENIED" and source.get("exit_status") == errno.EPERM
            and isinstance(denial, str) and "PermissionError" in denial
            and source.get("socket_target") == [ip, 8888]
            and isinstance(source.get("permission_profile"), dict)
            and isinstance(source.get("policy_sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", source["policy_sha256"]) is not None
            and isinstance(source.get("identity"), dict))
    if not good:
        raise RuntimeError("workspace-write network-denied policy proof failed")
    return {"identity": source["identity"], "policy_sha256": source["policy_sha256"],
            "web_search": web_search}

_FAST_SEAL_KEYS = {"seal_schema", "image_digest", "interpreter_pin", "task_ids",
                   "spec_sha256", "runtime_security_sha256", "policy_sha256", "identity",
                   "web_search", "mounts", "sandbox", "auth", "target_checks_sha256",
                   "seal_sha256"}

def _seal(core: dict[str, Any]) -> dict[str, Any]:
    return {**core, "seal_sha256": sha(canonical(core).encode())}

def _validate_fast_seal(seal: dict[str, Any], image: str, pin: str) -> bool:
    if seal.get("seal_schema") != FAST_SEAL_SCHEMA:
        return False
    if set(seal) != _FAST_SEAL_KEYS:
        raise RuntimeError("fast-preflight seal schema is invalid")
    core = {key: value for key, value in seal.items() if key != "seal_sha256"}
    tasks, spec_sha256 = _smoke_spec(seal.get("task_ids"), pin)
    identity = seal.get("identity")
    good = (seal.get("seal_sha256") == sha(canonical(core).encode())
            and seal.get("image_digest") == image
            and seal.get("interpreter_pin") == pin
            and seal.get("task_ids") == sorted(tasks)
            and seal.get("spec_sha256") == spec_sha256
            and seal.get("runtime_security_sha256") == security_sha256(image, pin)
            and isinstance(seal.get("policy_sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", seal["policy_sha256"]) is not None
            and isinstance(identity, dict) and identity.get("image_digest") == image
            and seal.get("web_search") == WEB_SEARCH_DISABLED_EVIDENCE
            and seal.get("mounts") == FAST_MOUNTS and seal.get("sandbox") == FAST_SANDBOX
            and seal.get("auth") == "isolated-readable"
            and isinstance(seal.get("target_checks_sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", seal["target_checks_sha256"]) is not None)
    if not good:
        raise RuntimeError("fast-preflight seal binding is invalid")
    return True

def fast_smoke(image: str, pin: str, task_ids: list[str], codex_home: Path,
               deadline: float) -> dict[str, Any]:
    """Return one deterministic in-memory runtime seal for an image/pin task group."""
    _remaining(deadline, "fast sealed-runtime smoke")
    tasks, spec_sha256 = _smoke_spec(task_ids, pin, deadline)
    _pin_path(pin, deadline=deadline)
    image_id(image, deadline=deadline)
    # Leave time under the caller's one global deadline for Docker cleanup.
    operation_deadline = deadline - 2.0
    _remaining(operation_deadline, "fast sealed-runtime smoke")
    with tempfile.TemporaryDirectory(prefix="mdseval-fast-smoke-") as name:
        workspace = Path(name)
        with _network(image, deadline=deadline) as (network, ip):
            inspection = _targeted_smoke(image, pin, tasks, workspace, codex_home,
                                         network, ip, operation_deadline)
            policy = _fast_policy(image, pin, workspace, codex_home, network, ip,
                                  operation_deadline)
    _remaining(deadline, "fast sealed-runtime smoke")
    if policy["identity"] != inspection["identity"]:
        raise RuntimeError("sandbox and targeted interpreter identities differ")
    checks_sha256 = sha(canonical(inspection["target_checks"]).encode())
    core = {"seal_schema": FAST_SEAL_SCHEMA, "image_digest": image,
            "interpreter_pin": pin, "task_ids": sorted(tasks),
            "spec_sha256": spec_sha256,
            "runtime_security_sha256": security_sha256(image, pin),
            "policy_sha256": policy["policy_sha256"], "identity": policy["identity"],
            "web_search": policy["web_search"], "mounts": dict(FAST_MOUNTS),
            "sandbox": dict(FAST_SANDBOX), "auth": inspection["auth"],
            "target_checks_sha256": checks_sha256}
    result = _seal(core)
    _validate_fast_seal(result, image, pin)
    _remaining(deadline, "fast sealed-runtime smoke")
    return result

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
    fast = _validate_fast_seal(seal, image, pin)
    if not fast:
        image_id(image)
    if command.count(WEB_SEARCH_DISABLED_CONFIG) != 1:
        raise RuntimeError("subject command does not disable web search exactly once")
    if seal.get("runtime_security_sha256") != security_sha256(image, pin):
        raise RuntimeError("approved runtime security mismatch")
    rewritten = list(command)
    rewritten[0] = "/usr/lib/codex/bin/codex"
    rewritten[rewritten.index("--cd") + 1] = "/workspace"
    temporary = workspace / ".mdseval-final"
    rewritten[rewritten.index("--output-last-message") + 1] = "/workspace/.mdseval-final"
    with _network(image) as (network, ip):
        if not fast:
            policy = _policy(image, pin, workspace, codex_home, network, ip)
            if (policy["source_sha256"] != seal.get("policy_sha256") or policy["identity"] != seal.get("identity")
                    or seal.get("web_search") is not None and policy["web_search"] != seal["web_search"]):
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
