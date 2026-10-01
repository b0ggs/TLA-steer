from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from tla_steer import execution, pipeline, verifier
from tla_steer.contract import ContractError, validate_guard_update_source
from tla_steer.oracle import ACTION_SYMBOLS, CONSTANTS, INITIAL

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = (ROOT / "tests/fixtures/candidates/golden.py").read_text()


def replace_tick(body: str, extra: str = "") -> str:
    tree = ast.parse(GOLDEN)
    tick = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "tick")
    return extra + GOLDEN.replace(ast.get_source_segment(GOLDEN, tick), body)


class GuardedCheckerTests(unittest.TestCase):
    def test_golden_and_benign_copy_method_conform(self):
        validate_guard_update_source(GOLDEN, complete=True)
        validate_guard_update_source(GOLDEN.replace("dict(state)", "state.copy()"), complete=True)
        validate_guard_update_source(GOLDEN.replace('successor["lightA"] = "yellow"', 'successor.update({"lightA": "yellow"})'), complete=True)

    def test_persistent_state_annotations_defaults_and_alias_mutations_rejected(self):
        cases = {
            "module_counter": replace_tick("def tick(state):\n    global calls\n    calls += 1\n    return None", "calls = 0\n"),
            "function_attribute": replace_tick("def tick(state):\n    tick.calls += 1\n    return None"),
            "input_alias": replace_tick("def tick(state):\n    alias = state\n    alias['clock'] = False\n    return None"),
            "method_alias": replace_tick("def tick(state):\n    alias = state\n    alias.update({'clock': False})\n    return None"),
            "mutable_default": replace_tick("def tick(state, history=[]):\n    return None"),
            "annotation": replace_tick("def tick(state: dict()):\n    return None"),
            "reflection": replace_tick("def tick(state):\n    return state.__class__(state)"),
            "module_alias": replace_tick("def tick(state):\n    alias = INITIAL\n    alias['clock'] = 1\n    return None"),
            "rebound_copy": replace_tick("def tick(state):\n    successor = dict(state)\n    successor = state\n    successor['clock'] = 1\n    return successor"),
            "branch_alias": replace_tick("def tick(state):\n    successor = dict(state)\n    if state['clock'] == 0:\n        successor = state\n    successor['clock'] = 1\n    return successor"),
        }
        for label, source in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                with self.assertRaises(ContractError):
                    validate_guard_update_source(source, complete=True)
                path = Path(temporary) / "candidate.py"
                path.write_text(source)
                with mock.patch("tla_steer.execution.run_observations") as launch:
                    result = verifier.verify_candidate(path)
                    launch.assert_not_called()
                self.assertEqual(result["outcome"], verifier.INVALID_CANDIDATE)
                self.assertIn("guard_update_contract", result["contract_failures"][0])
                self.assertEqual(result["containment_mode"], "not_run")

    def test_delayed_history_is_rejected_even_when_first_two_calls_are_correct(self):
        original = next(ast.get_source_segment(GOLDEN, node) for node in ast.parse(GOLDEN).body
                        if isinstance(node, ast.FunctionDef) and node.name == "tick")
        delayed = original.replace('    if state["timerA"]',
            '    global calls\n    calls += 1\n    if calls > 7056:\n        return None\n    if state["timerA"]', 1)
        source = replace_tick(delayed, "calls = 0\n")
        with self.assertRaisesRegex(ContractError, "extra module state"):
            validate_guard_update_source(source, complete=True)
        # The same single-fragment validator rejects the stateful Follower form.
        from tla_steer.contract import validate_guard_update_function
        with self.assertRaisesRegex(ContractError, "Global"):
            validate_guard_update_function(ast.parse(delayed).body[0])

    def observations(self, source, runner, request):
        # These exact hand-authored regression bytes are reviewed test fixtures.
        # Production exposes no arbitrary-source local override.
        digest = hashlib.sha256(source.encode()).hexdigest()
        with mock.patch("tla_steer.execution._reviewed_hashes", return_value=frozenset({digest})):
            return execution.run_observations(source, runner, request, timeout_seconds=2)

    def test_final_and_partial_observers_detect_value_equal_type_mutation(self):
        for replacement in ("False", "0.0"):
            with self.subTest(replacement=replacement):
                source = replace_tick(f"def tick(state):\n    state['clock'] = {replacement}\n    return None")
                state = dict(INITIAL)
                final = self.observations(source, verifier._CANDIDATE_RUNNER,
                    {"constants": CONSTANTS, "action_symbols": ACTION_SYMBOLS, "states": [state]})
                self.assertEqual(json.loads(final.stdout)["failure"]["kind"], "input_mutation")
                partial = self.observations(source, pipeline._PROBE_RUNNER, {"symbol": "tick", "states": [state]})
                self.assertTrue(json.loads(partial.stdout)["rows"][0]["input_mutated"])

    def test_final_and_partial_snapshot_mutable_result_before_next_call(self):
        source = replace_tick("def tick(state):\n    shared['clock'] = (shared['clock'] + 1) % 8\n    return shared", "shared = " + repr(INITIAL) + "\n")
        final = self.observations(source, verifier._CANDIDATE_RUNNER,
            {"constants": CONSTANTS, "action_symbols": ACTION_SYMBOLS, "states": [INITIAL]})
        self.assertEqual(json.loads(final.stdout)["failure"]["kind"], "nondeterminism")
        partial = self.observations(source, pipeline._PROBE_RUNNER, {"symbol": "tick", "states": [INITIAL]})
        self.assertFalse(json.loads(partial.stdout)["rows"][0]["deterministic"])
        self.assertEqual(json.loads(partial.stdout)["rows"][0]["first"]["clock"], 1)


class ExecutionBoundaryTests(unittest.TestCase):
    def test_unreviewed_source_requires_real_preflight_and_cannot_fallback(self):
        source = GOLDEN + "\n# changed, unreviewed bytes\n"
        with mock.patch("tla_steer.execution.preflight", side_effect=execution.ContainmentUnavailable("blocked")) as preflight, \
             mock.patch("tla_steer.execution._collect") as collect:
            with self.assertRaisesRegex(execution.ContainmentUnavailable, "blocked"):
                execution.run_observations(source, "pass", {}, timeout_seconds=1)
            preflight.assert_called_once()
            collect.assert_not_called()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "candidate.py"
            path.write_text(source)
            with mock.patch("tla_steer.execution.preflight", side_effect=execution.ContainmentUnavailable("blocked")):
                result = verifier.verify_candidate(path)
            self.assertEqual(result["outcome"], verifier.EVALUATOR_ERROR)
            self.assertIn("containment_unavailable", result["contract_failures"][0])

    def test_failed_real_preflight_blocks_provider_and_credentials(self):
        config_path = ROOT / "configs/prototype.json"
        config = json.loads(config_path.read_text())
        with mock.patch("tla_steer.execution.preflight", side_effect=execution.ContainmentUnavailable("namespace unavailable")) as preflight, \
             mock.patch("tla_steer.pipeline.run_worker") as provider, \
             mock.patch("tla_steer.pipeline._codex_home") as credentials:
            with self.assertRaisesRegex(execution.ContainmentUnavailable, "namespace unavailable"):
                pipeline.run_comparison(config, config_path, ROOT, 2, 2, True)
            preflight.assert_called_once()
            provider.assert_not_called()
            credentials.assert_not_called()

    def test_partial_and_final_share_launcher_without_private_expected_values(self):
        from tla_steer.worker import ReviewedFixtureWorker
        from tla_steer.contract import controller_from_json, Proposal, PROPOSAL_SCHEMA_VERSION
        from tla_steer.smc import Particle
        fixture = ReviewedFixtureWorker(ROOT)
        controller = controller_from_json(json.dumps(fixture.controller))
        initial, step = controller.steps[:2]
        fragments = (Proposal(PROPOSAL_SCHEMA_VERSION, initial.id, fixture.initial),
                     Proposal(PROPOSAL_SCHEMA_VERSION, step.id, fixture.fragments['golden.py']['tick']))
        particle = Particle('p00-0000', None, (), 1, fragments, 0, (), 'alive')
        actual = execution.run_observations
        with mock.patch("tla_steer.execution.run_observations", wraps=actual) as launch:
            self.assertEqual(pipeline._score_action(particle, step).value, 1)
            self.assertEqual(verifier.verify_candidate(ROOT / 'tests/fixtures/candidates/golden.py')['outcome'], verifier.EXACT)
        self.assertEqual(launch.call_count, 2)
        for call in launch.call_args_list:
            request = call.args[2]
            self.assertNotIn('expected', json.dumps(request))
            self.assertNotIn('source', request)
            self.assertIn('states', request)

    def test_mount_plan_excludes_private_paths_and_requires_namespaces(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            command = execution._linux_command(root, root/'runner.py', 3)
        self.assertIn('--unshare-all', command)
        self.assertIn('--unshare-user', command)
        self.assertIn('--clearenv', command)
        self.assertIn('--disable-userns', command)
        self.assertNotIn('--share-net', command)
        self.assertNotIn('--not-a-security-boundary', command)
        bindings = [command[index+1:index+3] for index, value in enumerate(command) if value == '--ro-bind']
        self.assertNotIn(['/', '/'], bindings)
        self.assertFalse(any('/home' in source or '/workspace' in source for source, _ in bindings))
        self.assertNotIn(str(ROOT), command)
        for name in ('--as=', '--cpu=', '--fsize=', '--nofile=', '--core='):
            self.assertTrue(any(value.startswith(name) for value in command))
        self.assertFalse(any(value.startswith('--nproc=') for value in command))
        self.assertEqual(command[command.index('-c')+1], execution._namespace_bootstrap('/work/runner.py'))

    def test_namespace_bootstrap_sets_hard_process_limit_before_runner(self):
        with tempfile.TemporaryDirectory() as temporary:
            runner = Path(temporary) / 'runner.py'
            runner.write_text("import json, resource, sys\nprint(json.dumps([resource.getrlimit(resource.RLIMIT_NPROC), sys.argv[1]]))\n")
            result = subprocess.run([sys.executable, '-I', '-S', '-c',
                                     execution._namespace_bootstrap(str(runner)), 'candidate.py'],
                                    capture_output=True, text=True, check=True, timeout=5)
        self.assertEqual(json.loads(result.stdout), [[32, 32], 'candidate.py'])

    def test_reviewed_fixture_wall_timeout_and_output_are_bounded(self):
        # The runner scripts are trusted, deliberately adversarial test probes;
        # candidate bytes remain the exact pinned golden fixture.
        timeout = execution.run_observations(GOLDEN, 'while True: pass', {}, timeout_seconds=.1)
        self.assertTrue(timeout.timed_out)
        self.assertEqual(timeout.mode, 'reviewed_fixture_local')
        flood = execution.run_observations(GOLDEN, "import os\nwhile True: os.write(1, b'x'*65536)", {}, timeout_seconds=2)
        self.assertTrue(flood.output_exceeded)
        self.assertEqual(len(flood.stdout.encode()), execution.MAX_OUTPUT_BYTES)
        self.assertNotEqual(flood.returncode, 0)

    def test_known_fixture_bytes_have_no_generic_local_override(self):
        self.assertTrue(execution.is_reviewed_source(GOLDEN))
        self.assertFalse(execution.is_reviewed_source(GOLDEN + '\n'))
        self.assertFalse(execution.is_reviewed_source('print("not approved")'))
        with mock.patch('tla_steer.execution.preflight', side_effect=AssertionError('fixture requested sandbox')):
            result = execution.run_observations(GOLDEN, 'print("fixture")', {}, timeout_seconds=1)
        self.assertEqual(result.stdout.strip(), 'fixture')
        self.assertEqual(result.mode, 'reviewed_fixture_local')

    def test_transient_partial_boundary_failure_aborts_before_later_provider_steps(self):
        from tla_steer.worker import ReviewedFixtureWorker
        actual_worker = ReviewedFixtureWorker.__call__
        requests = []
        def worker(fixture, request):
            requests.append(request)
            return actual_worker(fixture, request)
        actual_launch = execution.run_observations
        failures = []
        def launch(source, runner, request, **kwargs):
            if runner == pipeline._PROBE_RUNNER and not failures:
                failures.append(True)
                raise execution.ContainmentUnavailable('transient injected boundary failure')
            return actual_launch(source, runner, request, **kwargs)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'repository'
            import shutil
            for name in ('configs', 'prompts', 'schemas', 'tests/fixtures/candidates'):
                shutil.copytree(ROOT / name, root / name)
            for name in ('TwoLights.tla', 'TwoLights.cfg'):
                shutil.copyfile(ROOT / name, root / name)
            config_path = root / 'configs/prototype.json'
            config = json.loads(config_path.read_text())
            with mock.patch.object(ReviewedFixtureWorker, '__call__', worker), \
                 mock.patch('tla_steer.execution.run_observations', side_effect=launch), \
                 mock.patch('tla_steer.pipeline.verify_candidate') as grade:
                with self.assertRaisesRegex(pipeline.PipelineError, 'transient injected boundary failure'):
                    pipeline.run_comparison(config, config_path, root, 2, 2, True, offline_screen=True)
                grade.assert_not_called()
            run_dir, = (root / 'runs/offline-cost-screen-r2').iterdir()
            summary = json.loads((run_dir / 'summary.json').read_text())
            manifest = json.loads((run_dir / 'manifest.json').read_text())
            self.assertEqual(summary['run_status'], 'pipeline_error')
            self.assertFalse(manifest['selection_complete'])
            self.assertIn('transient injected boundary failure', json.dumps(summary['errors']))
            self.assertTrue(summary['accounting']['complete'])
            self.assertEqual(summary['totals']['attempted_calls'], len(requests))
            self.assertLessEqual(len(requests), 7)
            self.assertGreaterEqual(len(requests), 6)
            self.assertFalse(any('-a_green_to_yellow-' in request.call_id for request in requests))
            for request in requests:
                self.assertTrue((request.spool_dir / 'result.json').is_file())
            self.assertTrue(all(arm['verification'] is None for arm in summary['arms'].values()))

    def test_final_boundary_failure_is_run_error_not_a_model_outcome(self):
        import shutil
        actual = execution.run_observations
        def launch(source, runner, request, **kwargs):
            if runner == verifier._CANDIDATE_RUNNER:
                raise execution.ContainmentUnavailable('final boundary unavailable')
            return actual(source, runner, request, **kwargs)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'repository'
            for name in ('configs', 'prompts', 'schemas', 'tests/fixtures/candidates'):
                shutil.copytree(ROOT / name, root / name)
            for name in ('TwoLights.tla', 'TwoLights.cfg'):
                shutil.copyfile(ROOT / name, root / name)
            config_path = root / 'configs/prototype.json'
            config = json.loads(config_path.read_text())
            with mock.patch('tla_steer.execution.run_observations', side_effect=launch):
                with self.assertRaisesRegex(pipeline.PipelineError, 'verifier infrastructure failure'):
                    pipeline.run_comparison(config, config_path, root, 2, 2, True, offline_screen=True)
            run_dir, = (root / 'runs/offline-cost-screen-r2').iterdir()
            summary = json.loads((run_dir / 'summary.json').read_text())
            self.assertEqual(summary['run_status'], 'pipeline_error')
            self.assertEqual(summary['arms']['direct']['verification']['outcome'], 'EVALUATOR_ERROR')
            self.assertIsNone(summary['arms']['cheap_alone']['verification'])
            self.assertIsNone(summary['arms']['discipl']['verification'])
            self.assertTrue(summary['accounting']['complete'])
            self.assertEqual(summary['totals']['attempted_calls'], 19)
            self.assertIn('final boundary unavailable', json.dumps(summary['errors']))
