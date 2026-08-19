import copy
import inspect
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import badge_cli
from badge_manifest import BadgeManifestError, build_manifest


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "badge_policy.json"
ATTENDEES_PATH = ROOT / "fixtures" / "attendees.json"
EMPTY_PATH = ROOT / "fixtures" / "empty-attendees.json"
MALFORMED_PATH = ROOT / "fixtures" / "malformed-attendees.json"
MISSING_PATH = ROOT / "fixtures" / "missing-attendees.json"

ATTENDEE_KEYS = {"id", "name", "role", "active", "late_shift"}
ENTRY_KEYS = {"badge_id", "display", "areas", "late_shift"}


def load_json(path):
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def valid_attendee(**changes):
    attendee = {
        "id": "V-200",
        "name": "Kai Reed",
        "role": "runner",
        "active": True,
        "late_shift": False,
    }
    attendee.update(changes)
    return attendee


class BadgeManifestPublicTests(unittest.TestCase):
    def test_r1_api_and_preservation(self):
        self.assertEqual(BadgeManifestError.__bases__, (ValueError,))

        parameters = list(inspect.signature(build_manifest).parameters.values())
        self.assertEqual([parameter.name for parameter in parameters], ["attendees", "policy"])
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
                for parameter in parameters
            )
        )
        self.assertTrue(
            all(parameter.default is inspect.Parameter.empty for parameter in parameters)
        )

        attendees = []
        policy = load_json(POLICY_PATH)
        attendees_before = copy.deepcopy(attendees)
        policy_before = copy.deepcopy(policy)

        self.assertEqual(build_manifest(attendees, policy), [])
        self.assertEqual(attendees, attendees_before)
        self.assertEqual(policy, policy_before)

    def test_r2_public_negative_attendees(self):
        policy = load_json(POLICY_PATH)

        extra_key = valid_attendee()
        extra_key["note"] = "desk"

        wrong_bool = valid_attendee(active=1)
        duplicate_id = [valid_attendee(), valid_attendee(name="Jo Bell")]
        unknown_role = [valid_attendee(role="usher")]

        negatives = [
            "not-a-list",
            [extra_key],
            [wrong_bool],
            duplicate_id,
            unknown_role,
        ]

        for attendees in negatives:
            with self.subTest(attendees=attendees):
                with self.assertRaises(BadgeManifestError):
                    build_manifest(attendees, policy)

    def test_r3_public_negative_policies(self):
        extra_key = load_json(POLICY_PATH)
        extra_key["version"] = 1

        wrong_common = load_json(POLICY_PATH)
        wrong_common["common_area"] = 7

        empty_roles = load_json(POLICY_PATH)
        empty_roles["role_area"] = {}

        wrong_role_area = load_json(POLICY_PATH)
        wrong_role_area["role_area"] = {"checkin": 9}

        for policy in [extra_key, wrong_common, empty_roles, wrong_role_area]:
            with self.subTest(policy=policy):
                with self.assertRaises(BadgeManifestError):
                    build_manifest([], policy)

    def test_r4_active_selection(self):
        attendees = load_json(ATTENDEES_PATH)
        policy = load_json(POLICY_PATH)

        result = build_manifest(attendees, policy)

        self.assertEqual(
            {entry["badge_id"] for entry in result},
            {"V-099", "V-101", "V-104"},
        )

    def test_r5_area_grants(self):
        policy = load_json(POLICY_PATH)
        attendee = {
            "id": "V-500",
            "name": "Noah Green",
            "role": "runner",
            "active": True,
            "late_shift": True,
        }

        result = build_manifest([attendee], policy)

        self.assertEqual(
            result[0]["areas"],
            ["lobby", "supply-room", "staff-exit"],
        )

    def test_r6_shape_display_and_order(self):
        policy = load_json(POLICY_PATH)
        attendees = [
            {
                "id": "V-9",
                "name": "Zed Wu",
                "role": "runner",
                "active": True,
                "late_shift": False,
            },
            {
                "id": "V-2",
                "name": "Ana Fox",
                "role": "checkin",
                "active": True,
                "late_shift": True,
            },
        ]

        result = build_manifest(attendees, policy)

        self.assertIs(type(result), list)
        self.assertTrue(all(type(entry) is dict for entry in result))
        self.assertTrue(all(set(entry) == ENTRY_KEYS for entry in result))
        self.assertEqual(
            [
                (entry["badge_id"], entry["display"], entry["late_shift"])
                for entry in result
            ],
            [
                ("V-2", "Ana Fox [checkin]", True),
                ("V-9", "Zed Wu [runner]", False),
            ],
        )

    def test_r7_cli_success_isolated(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "badge_cli.py"),
                str(EMPTY_PATH),
                str(POLICY_PATH),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, "[]\n")
        self.assertEqual(completed.stderr, "")

        serialization_value = [
            {
                "zeta": "café",
                "alpha": "雪",
                "nested": {"b": 2, "a": 1},
            }
        ]
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch(
            "badge_cli.build_manifest",
            return_value=serialization_value,
        ):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                status = badge_cli.main([str(EMPTY_PATH), str(POLICY_PATH)])

        self.assertEqual(status, 0)
        self.assertEqual(
            stdout.getvalue(),
            '[{"alpha":"\\u96ea","nested":{"a":1,"b":2},"zeta":"caf\\u00e9"}]\n',
        )
        self.assertEqual(stderr.getvalue(), "")

    def test_r8_cli_failures_isolated(self):
        probes = [
            [],
            [str(MISSING_PATH), str(POLICY_PATH)],
            [str(MALFORMED_PATH), str(POLICY_PATH)],
        ]

        for argv in probes:
            with self.subTest(argv=argv):
                stdout = io.StringIO()
                stderr = io.StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    status = badge_cli.main(argv)
                self.assertEqual(status, 2)
                self.assertEqual(stdout.getvalue(), "")
                self.assertNotEqual(stderr.getvalue(), "")

        with tempfile.NamedTemporaryFile() as source:
            source.write(b"\xff")
            source.flush()
            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                status = badge_cli.main([source.name, str(POLICY_PATH)])
            self.assertEqual(status, 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertNotEqual(stderr.getvalue(), "")

        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch(
            "badge_cli.build_manifest",
            side_effect=BadgeManifestError("forced application failure"),
        ):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                status = badge_cli.main([str(EMPTY_PATH), str(POLICY_PATH)])

        self.assertEqual(status, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertNotEqual(stderr.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
