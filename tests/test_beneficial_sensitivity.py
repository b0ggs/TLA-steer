from __future__ import annotations

import hashlib
import itertools
import json
import os
import shutil
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from mdseval import beneficial_sensitivity as m2


HERE = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get("M2_TEST_ROOT", HERE))
CONFIG = ROOT / "experiments/coder-beneficial-sensitivity-m2.json"
COMMIT = "a" * 40


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(m2.canonical(value))


def commit_probe(root: Path, commit: str, paths: list[str]) -> dict[str, object]:
    return {"head": commit, "clean": True,
            "frozen_hashes": {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in paths}}


class FakeChecker:
    def __init__(self, root: Path):
        self.root = root
        self.calls = 0

    def __call__(self, checker: Path, task_id: str, workspace: Path, timeout: int) -> dict[str, object]:
        self.calls += 1
        state = ("pristine", "correct-a", "correct-b", "mutant-a", "mutant-b")[((self.calls - 1) % 15) // 3]
        task = json.loads((self.root / "evals/m2/coder-beneficial-sensitivity" / task_id / "task.json").read_text())
        requirement_ids = [x["id"] for x in task["requirements"]]
        regression_ids = [x["id"] for x in task["regressions"]]
        failed = set()
        if state == "pristine":
            failed = {requirement_ids[0]}
        elif state.startswith("mutant"):
            matrix = task["requirement_to_negative_case_matrix"]
            failed = {rid for rid, mutants in matrix.items() if state in mutants}
        resolved = not failed and state.startswith("correct")
        payload = {"schema": m2.CHECK_SCHEMA, "task_id": task_id, "environment": {"passed": True},
                   "requirements": {rid: {"passed": rid not in failed, "detail": "synthetic"} for rid in requirement_ids},
                   "regressions": {rid: {"passed": True, "detail": "synthetic"} for rid in regression_ids},
                   "integrity": {"passed": True}, "resolved": resolved}
        return {"valid": True, "resolved": resolved, "mechanical": True, "payload": payload}


class FakeAttempts:
    def __init__(self, mode: str = "pass"):
        self.mode = mode
        self.calls = 0

    def __call__(self, design: dict, slot: dict, semantic: str, index: int) -> dict:
        self.calls += 1
        stage = slot["stage"]
        invalid = self.mode == "invalid-smoke" and stage == "calibration"
        resolved = not invalid and ((stage == "calibration" and slot["round"] <= 3)
                    or (stage == "controls" and semantic in {"N1", "N2"}) or (stage == "helpful" and semantic == "P"))
        row = {**slot, "launch_index": index, "requested_model": "gpt-5.6-sol", "observed_model": None if invalid else "gpt-5.6-sol",
               "requested_reasoning_effort": "high", "observed_reasoning_effort": None if invalid else "high", "identity_status": "not_reported", "judge_calls": 0,
               "objective_resolved": resolved, "checker_valid": not invalid, "mechanical_integrity": not invalid,
               "requirements_passed": 3 if resolved else 0, "requirements_total": 3, "status": "ACTIVE",
               "infrastructure_invalid": invalid, "final_message_hex": m2.EXPECTED_FINAL.hex() if stage == "smoke" else "",
               "tree_unchanged": True, "capture_complete": True, "raw": {"source": "deterministic-fake"}}
        return row


def initialize_case(base: Path, *, instance: str = "case", checker: FakeChecker | None = None) -> tuple[Path, FakeChecker]:
    checker = checker or FakeChecker(ROOT)
    passed = base / "PASS.json"; write_json(passed, {"schema":"mdseval.coder-beneficial-sensitivity-m2-commission-pass-v1","status":"PASS","verified_commit":COMMIT,"runtime":{"fake":True}})
    qualified=base/"qualification"; m2.qualify(CONFIG,qualified,authoritative=True,commissioning_pass=passed,verified_commit=COMMIT,checker=checker,process=commit_probe)
    m2.initialize(design_path=CONFIG, instance=instance, verified_commit=COMMIT, qualification_receipt=qualified/"qualification-receipt.json", runs_root=base / "runs", process=commit_probe, entropy=lambda n:b"x"*n)
    return base / "runs", checker


def authorize(base: Path, runs: Path, stage: str, instance: str = "case") -> Path:
    path = base / f"auth-{stage}.json"
    live=runs/instance/"live"; manifest=json.loads((live/"initial-manifest.json").read_text()); design=json.loads(CONFIG.read_text())
    write_json(path, {"schema":"mdseval.coder-beneficial-sensitivity-m2-campaign-authorization-v1","experiment":design["experiment"],"instance":instance,"verified_commit":manifest["verified_commit"],"authorized":True,"manifest_sha256":m2.sha256_file(live/"initial-manifest.json"),"config_sha256":manifest["config_sha256"],"runtime_identity_sha256":manifest["runtime_identity_sha256"],"mapping_hashes":manifest["mapping_hashes"],"ordered_stages":list(m2.STAGES),"mechanical_gates":["selection","power","controls"],"fallback_by_stage":design["calls"]["fallback_by_stage"],"absolute_cap":313})
    return path


def qualification_freeze(path: Path) -> Path:
    write_json(path, {"schema": "mdseval.coder-beneficial-sensitivity-m2-4-freeze-v1", "experiment": "coder-beneficial-sensitivity-m2-timeout-v1",
                      "status": "PASS", "authoritative": False})
    return path


def disposable_root(base: Path) -> Path:
    root = base / "repo"
    for source in ("controls/coder", "evals/m2/coder-beneficial-sensitivity", "evals/qualification/coder-beneficial-sensitivity-m2"):
        shutil.copytree(ROOT / source, root / source)
    for source in ("experiments/coder-beneficial-sensitivity-m2-1-access.json", "experiments/coder-beneficial-sensitivity-m2-4-2-closure.json",
                   "experiments/coder-beneficial-sensitivity-m2-3-task-reliability-authorship.json",
                   "src/mdseval/beneficial_sensitivity.py", "src/mdseval/wrapper.py", "tests/test_beneficial_sensitivity.py",
                   "experiments/coder-beneficial-sensitivity-m2-exclusions.json", "README.md", "experiments/coder-beneficial-sensitivity-m2.json"):
        target = root / source
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / source, target)
    return root


class FrozenDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design = json.loads(CONFIG.read_text())

    def test_config_is_canonical_one_line_and_authority_runtime_are_frozen(self):
        raw = CONFIG.read_bytes()
        self.assertEqual(raw, m2.canonical(json.loads(raw)))
        self.assertEqual(len(raw.splitlines()), 1)
        self.assertEqual(self.design["protocol"]["version"], "0.4")
        self.assertEqual((self.design["schema"], self.design["experiment"]), (m2.SCHEMA, "coder-beneficial-sensitivity-m2-timeout-v1"))
        self.assertEqual((self.design["runtime"]["model"], self.design["runtime"]["reasoning_effort"]), ("gpt-5.6-sol", "high"))
        self.assertEqual((self.design["calls"]["base_cap"], self.design["calls"]["absolute_cap"]), (296, 313))

    def test_strict_paths_config_and_no_override_seam(self):
        for value in ("/a", "../a", "a/../b", "", "."):
            with self.subTest(value=value), self.assertRaises(ValueError): m2._safe(value, "x")
        config = m2.runner_config(self.design)
        self.assertEqual((config.model, config.reasoning_effort, config.max_parallel_runs), ("gpt-5.6-sol", "high", 1))
        clone = json.loads(json.dumps(self.design)); clone["runtime"]["model"] = "not-sol"
        with patch.object(m2, "_root", return_value=ROOT), patch.object(Path, "read_text", return_value=json.dumps(clone)):
            with self.assertRaisesRegex(ValueError, "runtime"): m2.load_design(Path("x"))

    def test_cli_has_initialize_and_no_output_or_runtime_options(self):
        source = Path(m2.__file__).read_text()
        self.assertIn('"commission","initialize","run-stage","replay"', source)
        self.assertNotIn("--model", source)
        self.assertNotIn("--runs-root", source)

    def test_exact_timeout_protocol_artifacts_qualification_and_owner_payload(self):
        self.assertEqual(set(self.design["protocol"]), {"version", "protocol_sha256", "implementation_plan_sha256", "measurement_base_commit"})
        self.assertEqual(set(self.design["artifacts"]), {"access", "helpful", "helpful_authorship", "harmful", "null", "master", "task_authorship",
            "task_reliability_authorship", "oracle", "wrapper", "evaluator", "tests", "exclusions"})
        self.assertTrue(all(set(value) == {"path", "sha256"} for value in self.design["artifacts"].values()))
        self.assertEqual(self.design["qualification"]["internal_timeout_seconds"], 10)
        owner = json.loads((ROOT / self.design["artifacts"]["task_reliability_authorship"]["path"]).read_text())
        stripped = sorted(f"644 {value} {key.removeprefix('return/')}\n".encode() for key, value in owner["output_hashes"].items())
        prefixed = sorted(f"644 {value} {key}\n".encode() for key, value in owner["output_hashes"].items())
        self.assertEqual(hashlib.sha256(b"".join(stripped)).hexdigest(), "a9bcb692d71290ed7b5bddf5bf65a80a022bfb9e491c03ca9ef59480c001e355")
        self.assertEqual(hashlib.sha256(b"".join(prefixed)).hexdigest(), "e3c8ad8f8cdc8bae3f0b2befcba140a2191a2b386cc77a89b554167d6ee9e156")

    def test_commission_fake_pass_identity_and_terminal_probe(self):
        self.assertEqual(m2.EXPECTED_FINAL, b"IMPLEMENTED\nSMOKE_READY")
        self.assertEqual([m2._service_identity(x)["status"] for x in ([], [{"type":"turn.started","service":{"model":"gpt-5.6-sol","reasoning_effort":"high"}}], [{"type":"response.completed","model":"other"}], [{"type":"tool","model":"other"}])], ["not_reported","reported_match","reported_mismatch","not_reported"])
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); root=disposable_root(base); diagnostics=base/"diagnostics"
            for command in (["git","init"],["git","add","."],["git","-c","user.name=Test","-c","user.email=test@example.com","commit","-m","baseline"]): m2.subprocess.run(command,cwd=root,check=True,capture_output=True)
            start=m2.subprocess.run(["git","rev-parse","HEAD"],cwd=root,check=True,capture_output=True,text=True).stdout.strip(); (root/"README.md").write_text("commissioned\n")
            for command in (["git","add","README.md"],["git","-c","user.name=Test","-c","user.email=test@example.com","commit","-m","implementation"]): m2.subprocess.run(command,cwd=root,check=True,capture_output=True)
            runtime={"fixture":"runtime"}; auth=base/"auth.json"; write_json(auth,{"schema":"mdseval.coder-beneficial-sensitivity-m2-commission-authorization-v1","experiment":"coder-beneficial-sensitivity-m2-timeout-v1","authorized":True,"starting_commit":start,"engineering_paths":list(m2.ENGINEERING_PATHS),"churn_cap":350,"max_probes":3,"max_repairs":2,"diagnostic_root":str(diagnostics.resolve()),"runtime_identity_sha256":m2.digest(runtime)})
            Run=m2.make_dataclass("Run",[(x,object) for x in ("status","exit_code","duration_seconds","timed_out","interrupted")])
            class Runner:
                def __init__(self,_config): pass
                def run(self,_prepared,output,_timeout,_redactor): (output/"events.jsonl").write_text('{"type":"turn.started","model":"gpt-5.6-sol","reasoning_effort":"high"}\n'); (output/"stderr.txt").write_text(""); (output/"final.txt").write_bytes(m2.EXPECTED_FINAL); return Run("COMPLETED",0,1,False,False)
            got=m2.commission(design_path=root/"experiments/coder-beneficial-sensitivity-m2.json",starting_commit=start,diagnostic_root=diagnostics,authorization_receipt=auth,runner_factory=Runner,runtime_probe=lambda *_:runtime)
            self.assertEqual((got["status"],got["identity"]["status"],len(list(diagnostics.glob("*/probe-1/PASS.json")))),("PASS","reported_match",1))
            with self.assertRaisesRegex(RuntimeError,"terminal"): m2.commission(design_path=root/"experiments/coder-beneficial-sensitivity-m2.json",starting_commit=start,diagnostic_root=diagnostics,authorization_receipt=auth,runner_factory=Runner,runtime_probe=lambda *_:runtime)


class ScheduleAndStatisticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design = json.loads(CONFIG.read_text()); cls.master = m2.build_master_schedules(cls.design)

    def test_schedules_are_opaque_balanced_consecutive_and_deterministic(self):
        self.assertEqual(self.master, m2.build_master_schedules(self.design))
        for stage, expected, fallback in (("calibration", 120, 6), ("controls", 60, 3), ("helpful", 160, 8)):
            value = self.master[stage]
            self.assertEqual(len(value["base"]), expected)
            self.assertTrue(all(len(x) == fallback for x in value["fallback_by_task"].values()))
            self.assertEqual(len(value["block_sentinels"]), 20)
        text = json.dumps(self.master)
        for semantic in ('"N1"', '"N2"', '"H"', '"N"', '"P"'): self.assertNotIn(semantic, text)
        for index in range(0, 160, 2):
            a, b = self.master["helpful"]["base"][index:index + 2]
            self.assertEqual((a["task_id"], a["round"]), (b["task_id"], b["round"]))

    def test_filter_selection_resume_and_exact_caps(self):
        counts = {task: 3 for task in m2.TASKS}; selection = m2.select_tasks(counts)
        self.assertEqual(len(selection["selected_ids"]), 16)
        filtered = m2.filter_schedule(self.master, selection["selected_ids"], "controls")
        self.assertEqual(len(filtered["slots"]), 48)
        control = self.master["controls"]["base"]
        self.assertFalse(m2.validate_resume("controls", control, 1)); self.assertTrue(m2.validate_resume("controls", control, 3))
        self.assertEqual(120 + 48 + 128, 296); self.assertEqual(296 + 6 + 3 + 8, 313)
        counts.update({task: 0 for task in m2.TASKS if task.startswith("bug-")})
        self.assertEqual(m2.select_tasks(counts)["status"], "SENSITIVITY_NOT_DEMONSTRATED")

    def test_sign_test_matches_bruteforce_and_directional_gates(self):
        values = [Fraction(1, 4)] * 6 + [Fraction()] * 10
        observed = abs(sum(values)); nonzero = [x for x in values if x]
        brute = Fraction(sum(abs(sum((v if bit else -v for bit, v in zip(bits, nonzero)), Fraction())) >= observed
                             for bits in itertools.product((0, 1), repeat=len(nonzero))), 2 ** len(nonzero))
        got = m2.exact_sign_test(values)
        self.assertEqual(Fraction(got["p_value"]["numerator"], got["p_value"]["denominator"]), brute)
        selected = list(m2.TASKS[:4] + m2.TASKS[5:9] + m2.TASKS[10:14] + m2.TASKS[15:19]); outcomes = {}
        for task in selected:
            outcomes[task, "N1"] = [True]; outcomes[task, "N2"] = [True]; outcomes[task, "H"] = [False]
            outcomes[task, "P"] = [True] * 4; outcomes[task, "N"] = [False] * 4
        self.assertFalse(m2.compare(outcomes, selected, "N1", "N2", bootstrap_iterations=100)["a_wins"])
        self.assertTrue(m2.compare(outcomes, selected, "N1", "H", bootstrap_iterations=100)["a_wins"])
        helpful = m2.compare(outcomes, selected, "P", "N", bootstrap_iterations=100)
        self.assertTrue(helpful["a_wins"]); self.assertEqual((helpful["bootstrap"]["lower_index"], helpful["bootstrap"]["upper_index"]), (2, 97))

    def test_invalidity_table_and_power_draw_contract(self):
        result = SimpleNamespace(timed_out=False, interrupted=False, exit_code=1)
        self.assertEqual(m2.classify_attempt(result, SimpleNamespace(events=()), "SERVICE_PRE_USABLE", ["SERVICE_PRE_USABLE"]), "INFRASTRUCTURE_INVALID")
        self.assertEqual(m2.classify_attempt(result, SimpleNamespace(events=({},)), "SERVICE_PRE_USABLE", ["SERVICE_PRE_USABLE"]), "Y0")
        power = m2.post_calibration_power({t: 3 for t in m2.TASKS}, list(m2.TASKS[:4] + m2.TASKS[5:9] + m2.TASKS[10:14] + m2.TASKS[15:19]), self.design, iterations=500)
        self.assertEqual(power["selected_ids"], sorted(power["selected_ids"])); self.assertTrue(all(x["value"] == .5 for x in power["rates"]))


class QualificationTests(unittest.TestCase):
    def test_checker_demands_canonical_complete_mechanical_payload(self):
        source = ('import json\np={"schema":"mdseval.coder-beneficial-sensitivity-m2-check-v1","task_id":"t",'
                  '"environment":{"passed":True},"requirements":{"R1":{"passed":False}},'
                  '"regressions":{"G1":{"passed":True}},"integrity":{"passed":True},"resolved":True}\nprint(json.dumps(p))\n')
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); checker = root / "check.py"; checker.write_text(source)
            self.assertFalse(m2._checker(checker, "t", root)["valid"])

    @unittest.skip("v0.3 initializer history")
    def test_public_initialize_accepts_relative_paths_in_clean_repo(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); root = disposable_root(base); runs = base / "runs"; checker = FakeChecker(root)
            for command in (["git", "init"], ["git", "add", "."], ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "fixture"]): m2.subprocess.run(command, cwd=root, check=True, capture_output=True)
            commit = m2.subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
            freeze = base / "freeze.json"; write_json(freeze, {"schema": "mdseval.coder-beneficial-sensitivity-m2-freeze-authorization-v1", "experiment": "coder-beneficial-sensitivity-m2-timeout-v1", "instance": "case", "verified_commit": commit, "authorized": True})
            cwd = Path.cwd(); os.chdir(root)
            try: m2.initialize(design_path=Path("experiments/coder-beneficial-sensitivity-m2.json"), instance="case", verified_commit=commit, freeze_authorization=freeze, closure_record=m2.M2_4_2_CLOSURE, runs_root=runs, checker=checker)
            finally: os.chdir(cwd)
            live = runs / "case/live"; self.assertEqual((checker.calls, (live / "final-freeze-receipt.json").is_file(), (live / "post-freeze-alignment-receipt.json").is_file()), (300, True, True))
            receipt = json.loads((live / "qualification-receipt.json").read_text()); self.assertEqual((receipt["task_count"], receipt["execution_count"]), (20, 300))
            manifest = json.loads((live / "initial-manifest.json").read_text()); self.assertEqual(set(manifest["mapping_hashes"]), set(m2.STAGES)); self.assertNotIn('"mapping"', json.dumps(manifest))

    @unittest.skip("v0.3 closure history")
    def test_initialize_rejects_every_closure_except_exact_m2_4_2_record(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); closure = base / "closure.json"; freeze = base / "freeze.json"; exact = json.loads((ROOT / m2.M2_4_2_CLOSURE).read_text())
            write_json(freeze, {"schema": "mdseval.coder-beneficial-sensitivity-m2-freeze-authorization-v1", "experiment": "coder-beneficial-sensitivity-m2-timeout-v1", "instance": "case", "verified_commit": COMMIT, "authorized": True})
            def reject(path):
                with self.assertRaisesRegex(RuntimeError, "exact M2.4.2 closure"):
                    m2.initialize(design_path=CONFIG, instance="case", verified_commit=COMMIT, freeze_authorization=freeze, closure_record=path, runs_root=base / "runs", checker=FakeChecker(ROOT), process=commit_probe)
            variants = (exact, {**exact, "status": "FAIL"}, {**exact, "authoritative": True}, {**exact, "experiment": "wrong"}, {"schema": exact["schema"], "status": "PASS"})
            for variant in variants:
                with self.subTest(variant=variant): write_json(closure, variant); reject(closure)
            reject(ROOT / "experiments/coder-beneficial-sensitivity-m2-4-closure.json")


@unittest.skipUnless(os.name == "posix", "M2.4 qualification requires POSIX process groups")
class ProcessSafetyTests(unittest.TestCase):
    def make_checker(self, root: Path, *, child: str = "", detail: str = "ok", stderr: str = "") -> Path:
        payload = {"schema": m2.CHECK_SCHEMA, "task_id": "t", "environment": {"passed": True, "checks": []},
                   "requirements": {"R1": {"passed": detail != "timeout", "detail": detail}},
                   "regressions": {"G1": {"passed": True, "detail": "ok"}}, "integrity": {"passed": True, "detail": "ok"},
                   "resolved": detail != "timeout"}
        source = "import json,os,subprocess,sys,time\n" + child + f"\np={payload!r}\n"
        source += f"sys.stderr.buffer.write({stderr.encode()!r})\nsys.stdout.buffer.write((json.dumps(p,sort_keys=True,separators=(',',':'))+'\\n').encode())\n"
        path = root / "check.py"
        path.write_text(source)
        return path

    def test_normal_completion_cleans_leaked_and_term_resistant_children(self):
        children = (("subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)", False),
                    ("r,w=os.pipe();subprocess.Popen([sys.executable,'-c',f'import os,signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);os.write({w},b\"ready\");time.sleep(30)'],pass_fds=(w,),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);os.close(w);os.read(r,5);os.close(r)", True))
        for child, killed in children:
            with self.subTest(killed=killed), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                got = m2._checker(self.make_checker(root, child=child), "t", root)
                self.assertTrue(got["valid"])
                self.assertTrue(got["raw"]["process_cleanup"]["term_sent"])
                self.assertEqual(got["raw"]["process_cleanup"]["kill_sent"], killed)
                self.assertTrue(got["raw"]["process_cleanup"]["direct_checker_waited"])
                self.assertTrue(got["raw"]["process_cleanup"]["no_live_process_group_members"])

    def test_outer_timeout_preserves_partial_binary_and_process_exception_cleans(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "partial.py"
            path.write_bytes(b"import sys,time\nsys.stdout.buffer.write(b'\\xff\\x00');sys.stdout.buffer.flush()\nsys.stderr.buffer.write(b'\\xfe');sys.stderr.buffer.flush()\ntime.sleep(30)\n")
            got = m2._checker(path, "t", root, timeout=.5)
            self.assertEqual(got["raw"]["disposition"], "outer-timeout")
            self.assertIn("ff00", got["raw"]["stdout_hex"])
            self.assertIn("fe", got["raw"]["stderr_hex"])
            self.assertTrue(got["infrastructure_invalid"])
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "sleep.py"
            path.write_text("import time\ntime.sleep(30)\n")
            original = m2.subprocess.Popen.communicate
            def explode(process, *args, **kwargs):
                if kwargs.get("timeout") == .5:
                    return original(process, *args, **kwargs)
                raise RuntimeError("post-launch")
            with patch.object(m2.subprocess.Popen, "communicate", new=explode):
                got = m2._checker(path, "t", root)
            self.assertEqual(got["raw"]["disposition"], "process-error")
            self.assertTrue(got["raw"]["process_cleanup"]["succeeded"])

    def test_stderr_and_internal_timeout_are_never_successes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assertFalse(m2._checker(self.make_checker(root, stderr="noise"), "t", root)["valid"])
            timed = m2._checker(self.make_checker(root, detail="timeout"), "t", root)
            self.assertTrue(timed["infrastructure_invalid"])
            self.assertFalse(timed["valid"])


class QualificationEvidenceTests(unittest.TestCase):
    def test_raw_root_creation_failure_publishes_zero_execution_terminal(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); freeze=qualification_freeze(base/"freeze.json"); original=Path.mkdir
            def mkdir(path,*args,**kwargs):
                if path.name=="raw": raise OSError("raw unavailable")
                return original(path,*args,**kwargs)
            with patch.object(Path,"mkdir",new=mkdir): result=m2.qualify(CONFIG,base/"return/qualification-evidence",final_freeze_receipt=freeze,checker=FakeChecker(ROOT))
            terminal=json.loads((base/"return/qualification-evidence/terminal.json").read_text()); self.assertEqual((result["status"],terminal["status"],result["execution_count"],terminal["execution_count"],terminal["execution_records"]),("FAIL","FAIL",0,0,[]))
    def test_workspace_delta_allows_only_new_cache_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "solution.py").write_text("x=1\n")
            before = m2._manifest(root)
            (root / "__pycache__").mkdir()
            (root / "__pycache__/solution.pyc").write_bytes(b"cache")
            self.assertTrue(m2._workspace_ok(before, m2._manifest(root)))
            (root / "extra.txt").write_text("x")
            self.assertFalse(m2._workspace_ok(before, m2._manifest(root)))
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "solution.py"
            target.write_text("x=1\n")
            before = m2._manifest(root)
            target.write_text("x=2\n")
            self.assertFalse(m2._workspace_ok(before, m2._manifest(root)))
            target.write_text("x=1\n")
            target.chmod(0o600)
            self.assertFalse(m2._workspace_ok(before, m2._manifest(root)))

    def test_timeout_detail_in_pristine_and_mutant_is_terminal_infrastructure_fail(self):
        class TimeoutChecker:
            def __init__(self, at: int): self.fake, self.at = FakeChecker(ROOT), at
            def __call__(self, *args):
                got = self.fake(*args)
                if self.fake.calls == self.at:
                    first = next(iter(got["payload"]["requirements"].values()))
                    first["detail"] = "timeout"
                return got
        for at in (1, 13):
            with self.subTest(execution=at), tempfile.TemporaryDirectory() as td:
                base = Path(td)
                result = m2.qualify(CONFIG, base / "return/qualification-evidence", final_freeze_receipt=qualification_freeze(base / "freeze.json"), checker=TimeoutChecker(at))
                self.assertEqual((result["status"], result["execution_count"]), ("FAIL", at))
                terminal = json.loads((base / "return/qualification-evidence/terminal.json").read_text())
                self.assertEqual((terminal["status"], terminal["execution_count"]), ("FAIL", at))

    def test_exception_publishes_raw_before_workspace_deletion_and_create_once_collides(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            def failing(*_args): raise RuntimeError("synthetic")
            result = m2.qualify(CONFIG, base / "return/qualification-evidence", final_freeze_receipt=qualification_freeze(base / "freeze.json"), checker=failing)
            raw = base / "return/qualification-evidence/raw/execution-0001.json"
            self.assertEqual((result["status"], result["execution_count"], raw.is_file()), ("FAIL", 1, True))
            self.assertFalse((base / "scratch/qualification/workspace-0001").exists())
            with self.assertRaises(FileExistsError): m2._publish(raw, {"collision": True})

    def test_disposable_source_mutation_is_recorded_and_stops(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = disposable_root(base)
            fake = FakeChecker(root)
            def mutate(checker, task_id, workspace, timeout):
                got = fake(checker, task_id, workspace, timeout)
                checker.write_text(checker.read_text() + "\n")
                return got
            result = m2.qualify(root / "experiments/coder-beneficial-sensitivity-m2.json", base / "return/qualification-evidence",
                                final_freeze_receipt=qualification_freeze(base / "freeze.json"), checker=mutate)
            self.assertEqual((result["status"], result["execution_count"]), ("FAIL", 1))
            record = json.loads((base / "return/qualification-evidence/raw/execution-0001.json").read_text())
            self.assertNotEqual(record["pre_state"]["governed"], record["post_state"]["governed"])


class PublicLifecycleTests(unittest.TestCase):
    def test_actual_initialize_four_stages_terminal_and_replay_without_live_runner(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); runs, checker = initialize_case(base); fake = FakeAttempts()
            def forbidden_runner(_config):
                raise AssertionError("live runner constructed")
            for stage in m2.STAGES:
                result = m2.run_stage(design_path=CONFIG, instance="case", stage=stage,
                    authorization_receipt=authorize(base, runs, stage), runs_root=runs, runner_factory=forbidden_runner,
                    attempt_executor=fake, power_iterations=1000, bootstrap_iterations=100)
            self.assertEqual(checker.calls, 300); self.assertEqual(fake.calls, 296)
            live = runs / "case/live"
            self.assertEqual(result["verdict"], "SENSITIVITY_DEMONSTRATED")
            self.assertTrue((live / "locked-evidence-manifest.json").is_file())
            self.assertEqual(len(list(live.glob("*-unblinding-receipt.json"))), 3)
            replayed = m2.replay(CONFIG, "case", runs_root=runs, bootstrap_iterations=100)
            self.assertEqual(replayed, result)
            self.assertEqual((runs / "case/replay/report.json").read_bytes(), (live / "reports/report.json").read_bytes())
    def test_selection_stop_is_terminal_reportable_and_blocks_controls(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); runs, _ = initialize_case(base); fake = FakeAttempts()
            def floor(design, slot, semantic, index):
                row = fake(design, slot, semantic, index)
                if slot["stage"] == "calibration" and slot["task_id"].startswith("bug-"): row["objective_resolved"] = False
                return row
            report = m2.run_stage(design_path=CONFIG, instance="case", stage="calibration", authorization_receipt=authorize(base, runs, "calibration"),
                                  runs_root=runs, attempt_executor=floor, power_iterations=20, bootstrap_iterations=20)
            self.assertEqual((report["verdict"], report["terminal_reason"]), ("SENSITIVITY_NOT_DEMONSTRATED", "selection"))
            with self.assertRaisesRegex(RuntimeError, "active initialized"):
                m2.run_stage(design_path=CONFIG, instance="case", stage="controls", authorization_receipt=base / "none", runs_root=runs, attempt_executor=fake)
            self.assertEqual(m2.replay(CONFIG, "case", runs_root=runs, bootstrap_iterations=20)["verdict"], "SENSITIVITY_NOT_DEMONSTRATED")
    @unittest.skip("v0.3 authoritative smoke history")
    def test_preusable_smoke_failures_are_fail_closed_and_never_retried(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); runs,_=initialize_case(base); auth=authorize(base,runs,"smoke"); live=runs/"case/live"
            with patch.dict(os.environ,{"MDSEVAL_CODEX_HOME":""}), patch("mdseval.runner.codex_cli.CodexCLI",side_effect=AssertionError("constructed")), patch.object(m2,"_live_attempt",side_effect=AssertionError("launched")):
                with self.assertRaisesRegex(RuntimeError,"^AUTHENTICATION_PRE_USABLE$"): m2.run_stage(design_path=CONFIG,instance="case",stage="smoke",authorization_receipt=auth,runs_root=runs)
            self.assertEqual((list(live.glob("smoke-*")),(live/"attempts").exists()),([],False))
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); runs,_=initialize_case(base); calls=[]
            def fail(*_args): calls.append(1); raise RuntimeError("LIVE_RUNNER_UNAVAILABLE: MDSEVAL_CODEX_HOME is not set")
            report=m2.run_stage(design_path=CONFIG,instance="case",stage="smoke",authorization_receipt=authorize(base,runs,"smoke"),runs_root=runs,runner_factory=lambda _:SimpleNamespace(run=fail),bootstrap_iterations=20)
            live=runs/"case/live"; row=json.loads((live/"smoke-attempts.json").read_text())[0]
            self.assertEqual((report["verdict"],calls,row["infrastructure_invalid"],row["error_code"],row["error"]),("INVALID",[1],True,"AUTHENTICATION_PRE_USABLE","LIVE_RUNNER_UNAVAILABLE: MDSEVAL_CODEX_HOME is not set"))
            self.assertTrue(all((live/name).is_file() for name in ("smoke-outcome-lock.json","smoke-receipt.json","locked-evidence-manifest.json")))
            self.assertFalse((live/"smoke-supersession.json").exists())
    @unittest.skip("v0.3 stage authorization history")
    def test_transition_authorization_smoke_bytes_and_duplicate_receipts_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); runs, _ = initialize_case(base); fake = FakeAttempts()
            with self.assertRaisesRegex(RuntimeError, "prerequisites"):
                m2.run_stage(design_path=CONFIG, instance="case", stage="calibration", authorization_receipt=authorize(base, runs, "calibration"), runs_root=runs, attempt_executor=fake)
            bad = FakeAttempts()
            def newline(design, slot, semantic, index):
                row = bad(design, slot, semantic, index); row["final_message_hex"] = b"IMPLEMENTED\nSMOKE_READY".hex(); return row
            with self.assertRaisesRegex(RuntimeError, "smoke raw bytes"):
                m2.run_stage(design_path=CONFIG, instance="case", stage="smoke", authorization_receipt=authorize(base, runs, "smoke"), runs_root=runs, attempt_executor=newline)
    @unittest.skip("v0.3 binding names")
    def test_initial_evidence_bindings_block_stage_and_replay(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); runs, _ = initialize_case(base); live = runs / "case/live"
            cases = (("qualification-receipt.json", False), ("final-freeze-receipt.json", True),
                     ("qualification/qualification-results.json", False))
            for relative, delete in cases:
                with self.subTest(relative=relative):
                    target = live / relative; original = target.read_bytes()
                    target.unlink() if delete else target.write_bytes(b"{}\n")
                    fake = FakeAttempts()
                    with self.assertRaisesRegex(ValueError, "initial evidence binding"):
                        m2.run_stage(design_path=CONFIG, instance="case", stage="smoke", authorization_receipt=authorize(base, runs, "smoke"),
                                     runs_root=runs, attempt_executor=fake, bootstrap_iterations=20)
                    self.assertEqual(fake.calls, 0)
                    target.write_bytes(original)
            fake = FakeAttempts("invalid-smoke")
            m2.run_stage(design_path=CONFIG, instance="case", stage="calibration", authorization_receipt=authorize(base, runs, "calibration"),
                         runs_root=runs, attempt_executor=fake, bootstrap_iterations=20)
            target = live / "final-freeze-receipt.json"; target.write_bytes(b"{}\n")
            locked = json.loads((live / "locked-evidence-manifest.json").read_text())
            with patch.object(m2, "governed_inventory", return_value=locked["files"]), self.assertRaisesRegex(ValueError, "initial evidence binding"):
                m2.replay(CONFIG, "case", runs_root=runs, bootstrap_iterations=20)
    def test_replay_detects_tamper_deletion_insertion_and_never_accepts_summary(self):
        design = json.loads(CONFIG.read_text())
        self.assertEqual(m2.analyze(design, {"schema": "mdseval.coder-beneficial-sensitivity-m2-evidence-v1", "attempts": []})["verdict"], "INVALID")
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); runs, _ = initialize_case(base); fake = FakeAttempts("invalid-smoke")
            m2.run_stage(design_path=CONFIG, instance="case", stage="calibration", authorization_receipt=authorize(base, runs, "calibration"),
                         runs_root=runs, attempt_executor=fake, bootstrap_iterations=20)
            live = runs / "case/live"
            inserted = live / "inserted"
            inserted.write_text("x")
            with self.assertRaisesRegex(ValueError, "changed"): m2.replay(CONFIG, "case", runs_root=runs, bootstrap_iterations=20)
            inserted.unlink()
            report = live / "reports/report.json"
            original = report.read_bytes()
            report.unlink()
            with self.assertRaisesRegex(ValueError, "missing|changed"): m2.replay(CONFIG, "case", runs_root=runs, bootstrap_iterations=20)
            report.write_bytes(original)
            report.write_bytes(m2.canonical({"supplied": "summary"}))
            with self.assertRaisesRegex(ValueError, "changed"):
                m2.replay(CONFIG, "case", runs_root=runs, bootstrap_iterations=20)

class LifecycleIntegrityTests(unittest.TestCase):
    def test_live_checker_timeout_propagates_infrastructure_invalid_without_a_live_runner(self):
        Run = m2.make_dataclass("Run", [(x, object) for x in ("timed_out", "interrupted", "exit_code")])
        Events = m2.make_dataclass("Events", [("events", object), ("valid", object)])
        Capture = m2.make_dataclass("Capture", [(x, object) for x in ("status", "diff", "untracked")])
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            repo = base / "repo"
            shutil.copytree(ROOT / "evals/m2/coder-beneficial-sensitivity/bug-01/fixture", repo)
            prepared = SimpleNamespace(repo=repo, baseline_commit=COMMIT, cleanup=lambda: None)
            class Runner:
                def run(self, _prepared, output, _timeout, _redactor):
                    output.mkdir(parents=True)
                    (output / "final.txt").write_bytes(b"done")
                    return Run(False, False, 0)
            events = Events(({"model": "gpt-5.6-sol", "reasoning_effort": "high"},), True)
            capture = Capture("", "", [])
            timeout = {"valid": False, "resolved": None, "mechanical": False, "payload": {}, "infrastructure_invalid": True}
            slot = {"slot_id": "calibration:base:r1:bug-01:K0", "stage": "calibration", "round": 1,
                    "task_id": "bug-01", "opaque_arm_id": "K0", "fallback": False}
            with patch("mdseval.fixtures.prepare_fixture", return_value=prepared), patch("mdseval.fixtures.audit_final_subject_tree"), \
                 patch("mdseval.capture.parse_event_stream", return_value=events), patch("mdseval.capture.capture_git", return_value=capture), \
                 patch.object(m2, "_checker", return_value=timeout):
                row = m2._live_attempt(json.loads(CONFIG.read_text()), CONFIG, base / "live", slot, "N", Runner(), 1)
            self.assertTrue(row["infrastructure_invalid"])
            self.assertFalse(row["objective_resolved"])
            self.assertFalse(row["mechanical_integrity"])

    @unittest.skip("covered through v0.4 envelope replay")
    def test_noncanonical_record_and_dependency_cycle_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            live = Path(td)
            noncanonical = live / "bad.json"
            noncanonical.write_text("{}")
            with self.assertRaisesRegex(RuntimeError, "noncanonical"): m2._json(noncanonical)
            prerequisites = ("final-freeze-receipt.json", "post-freeze-alignment-receipt.json",
                             "qualification-receipt.json")
            for name in prerequisites:
                write_json(live / name, {"fixture": name})
            write_json(live / "qualification/qualification-results.json", {"fixture": "qualification-results"})
            manifest = {"schedules": {}, "schedule_sha256": m2.digest({}),
                        "prerequisite_sha256": {name: m2.sha256_file(live / name) for name in prerequisites},
                        "qualification_results_sha256": m2.sha256_file(live / "qualification/qualification-results.json")}
            write_json(live / "initial-manifest.json", manifest)
            manifest_hash = m2.sha256_file(live / "initial-manifest.json")
            write_json(live / "cycle-receipt.json", {"manifest_sha256": manifest_hash,
                       "prerequisite_sha256": {"cycle-receipt.json": "0" * 64}})
            with self.assertRaisesRegex(ValueError, "prerequisite"): m2._validate_dag(live, manifest_hash)

    def test_process_capability_and_workspace_deletion_failures_terminalize(self):
        for branch in ("capability", "deletion"):
            with self.subTest(branch=branch), tempfile.TemporaryDirectory() as td:
                base = Path(td)
                freeze = qualification_freeze(base / "freeze.json")
                context = patch.object(m2.os, "name", "non-posix") if branch == "capability" else patch.object(m2.shutil, "rmtree", side_effect=OSError("synthetic"))
                with context:
                    result = m2.qualify(CONFIG, base / "return/qualification-evidence", final_freeze_receipt=freeze, checker=FakeChecker(ROOT))
                self.assertEqual(result["status"], "FAIL")
                terminal = json.loads((base / "return/qualification-evidence/terminal.json").read_text())
                self.assertEqual(terminal["status"], "FAIL")
                self.assertEqual(terminal["execution_count"], 0 if branch == "capability" else 1)

    def test_post_checker_and_final_hash_exceptions_preserve_terminal_evidence(self):
        for branch,expected in (("post-checker",1),("final-hash",300)):
            with self.subTest(branch=branch), tempfile.TemporaryDirectory() as td:
                base=Path(td); seen={}; original_manifest,original_tree=m2._manifest,m2.tree_sha256
                def manifest(path):
                    value=original_manifest(path); key=str(path)
                    seen[key]=seen.get(key,0)+1
                    if branch=="post-checker" and path.name=="workspace-0002" and seen[key]==2: raise OSError("synthetic")
                    return value
                def tree(path):
                    key=str(path); seen[key]=seen.get(key,0)+1
                    if branch=="final-hash" and path.name=="bug-01" and seen[key]==2: raise OSError("synthetic")
                    return original_tree(path)
                with patch.object(m2,"_manifest",side_effect=manifest), patch.object(m2,"tree_sha256",side_effect=tree):
                    result=m2.qualify(CONFIG,base/"return/qualification-evidence",final_freeze_receipt=qualification_freeze(base/"freeze.json"),checker=FakeChecker(ROOT))
                terminal=json.loads((base/"return/qualification-evidence/terminal.json").read_text())
                self.assertEqual((result["status"],terminal["status"],terminal["execution_count"]),("FAIL","FAIL",expected))
                self.assertEqual(len(terminal["execution_records"]),expected)
                self.assertEqual(len(list((base/"return/qualification-evidence/raw").glob("execution-*.json"))),expected)

    def test_terminal_publication_failure_propagates_without_terminal_claim(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); original_manifest,original_publish=m2._manifest,m2._publish; calls=0
            def manifest(path):
                nonlocal calls
                if path.name=="workspace-0001":
                    calls+=1
                    if calls==2: raise OSError("matrix")
                return original_manifest(path)
            def publish(path,value):
                if path.name=="terminal.json": raise OSError("terminal unavailable")
                return original_publish(path,value)
            with patch.object(m2,"_manifest",side_effect=manifest), patch.object(m2,"_publish",side_effect=publish), self.assertRaisesRegex(OSError,"terminal unavailable"):
                m2.qualify(CONFIG,base/"return/qualification-evidence",final_freeze_receipt=qualification_freeze(base/"freeze.json"),checker=FakeChecker(ROOT))
            self.assertFalse((base/"return/qualification-evidence/terminal.json").exists())


class BudgetTests(unittest.TestCase):
    def test_returned_source_and_tests_stay_within_nonreallocatable_caps(self):
        self.assertLessEqual(len(Path(m2.__file__).read_text().splitlines()), 1000)
        self.assertLessEqual(len(Path(__file__).read_text().splitlines()), 650)


if __name__ == "__main__":
    unittest.main()
