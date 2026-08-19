import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from triageboard import route_ticket, route_tickets


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "corridor.json"


class PublicContractTests(unittest.TestCase):
    def setUp(self):
        self.bundle = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.policy = self.bundle["policy"]

    def test_r1_api_and_immutability(self):
        ticket = {
            "id": "X",
            "product": "mobile",
            "severity": "normal",
            "tags": [],
        }
        original_ticket = copy.deepcopy(ticket)
        original_policy = copy.deepcopy(self.policy)

        result = route_ticket(ticket, self.policy)

        self.assertIsInstance(result, dict)
        self.assertIsNot(result, ticket)
        self.assertEqual(ticket, original_ticket)
        self.assertEqual(self.policy, original_policy)

    def test_r2_ticket_validation(self):
        valid = {
            "id": "X",
            "product": "mobile",
            "severity": "normal",
            "tags": [],
        }
        invalid_tickets = [
            {
                "id": "X",
                "product": "mobile",
                "severity": "normal",
            },
            {**valid, "extra": True},
            {**valid, "id": " "},
            {**valid, "product": 7},
            {**valid, "tags": "vip"},
            {**valid, "tags": [1]},
            {**valid, "severity": "urgent"},
        ]

        for ticket in invalid_tickets:
            with self.subTest(ticket=ticket):
                with self.assertRaises(ValueError):
                    route_ticket(ticket, self.policy)

    def test_r3_normalization_and_one_alias_lookup(self):
        corridor_result = route_ticket(
            self.bundle["tickets"][0],
            self.policy,
        )
        self.assertEqual(corridor_result["id"], "T-20")
        self.assertEqual(corridor_result["product"], "mobile")

        chained_policy = copy.deepcopy(self.policy)
        chained_policy["aliases"]["phone"] = "ios"
        chained_ticket = {
            "id": " Alias-1 ",
            "product": " PHONE ",
            "severity": "normal",
            "tags": [],
        }
        chained_result = route_ticket(chained_ticket, chained_policy)
        self.assertEqual(chained_result["id"], "Alias-1")
        self.assertEqual(chained_result["product"], "ios")

    def test_r4_queue_selection(self):
        billing = route_ticket(self.bundle["tickets"][1], self.policy)
        mobile = route_ticket(self.bundle["tickets"][0], self.policy)
        fallback = route_ticket(self.bundle["tickets"][2], self.policy)

        self.assertEqual(billing["queue"], "accounts")
        self.assertEqual(mobile["queue"], "apps")
        self.assertEqual(fallback["queue"], "general")

    def test_r5_priority_and_escalation(self):
        vip = route_ticket(self.bundle["tickets"][0], self.policy)
        high = route_ticket(self.bundle["tickets"][1], self.policy)
        low = route_ticket(self.bundle["tickets"][2], self.policy)
        normal = route_ticket(
            {
                "id": "T-N",
                "product": "other",
                "severity": "normal",
                "tags": [],
            },
            self.policy,
        )

        self.assertEqual((vip["priority"], vip["escalated"]), (1, True))
        self.assertEqual((high["priority"], high["escalated"]), (1, True))
        self.assertEqual((low["priority"], low["escalated"]), (3, False))
        self.assertEqual(
            (normal["priority"], normal["escalated"]),
            (2, False),
        )

    def test_r6_projection_and_tags(self):
        result = route_ticket(
            {
                "id": " Card-7 ",
                "product": "other",
                "severity": "normal",
                "tags": [" Beta ", "VIP", "beta", " "],
            },
            self.policy,
        )

        self.assertEqual(
            set(result),
            {
                "id",
                "product",
                "queue",
                "priority",
                "escalated",
                "tags",
            },
        )
        self.assertEqual(result["id"], "Card-7")
        self.assertEqual(result["tags"], ["beta", "vip"])
        self.assertIsInstance(result["id"], str)
        self.assertIsInstance(result["product"], str)
        self.assertIsInstance(result["queue"], str)
        self.assertIs(type(result["priority"]), int)
        self.assertIs(type(result["escalated"]), bool)
        self.assertIsInstance(result["tags"], list)

    def test_r7_batch_order_and_immutability(self):
        tickets = [
            {
                "id": "B",
                "product": "other",
                "severity": "low",
                "tags": [],
            },
            {
                "id": "C",
                "product": "other",
                "severity": "normal",
                "tags": [],
            },
            {
                "id": "A",
                "product": "other",
                "severity": "normal",
                "tags": [],
            },
        ]
        original = copy.deepcopy(tickets)

        result = route_tickets(tickets, self.policy)

        self.assertEqual([row["id"] for row in result], ["A", "C", "B"])
        self.assertEqual(tickets, original)
        with self.assertRaises(ValueError):
            route_tickets(tuple(tickets), self.policy)

    def test_r8_cli(self):
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "triageboard",
                "fixtures/corridor.json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        expected_stdout = (
            json.dumps(
                self.bundle["expected"],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        )

        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, expected_stdout)
        self.assertEqual(completed.stderr, "")

        failed = subprocess.run(
            [
                sys.executable,
                "-m",
                "triageboard",
                "fixtures/does-not-exist.json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(failed.returncode, 2)
        self.assertEqual(failed.stdout, "")
        self.assertNotEqual(failed.stderr, "")


if __name__ == "__main__":
    unittest.main()
