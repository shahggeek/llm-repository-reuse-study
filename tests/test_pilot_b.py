import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/pilot_b.py"
SPEC = importlib.util.spec_from_file_location("pilot_b", MODULE_PATH)
pilot_b = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(pilot_b)


class PilotBProtocolTests(unittest.TestCase):
    def setUp(self):
        self.config = pilot_b.read_json(pilot_b.DEFAULT_CONFIG)

    def test_frozen_config_is_self_consistent(self):
        self.assertEqual([], pilot_b.validate_config(self.config))

    def test_six_tasks_and_three_conditions_are_fixed(self):
        self.assertEqual(set(pilot_b.EXPECTED_TASKS), {task["slug"] for task in self.config["tasks"]})
        self.assertEqual(
            pilot_b.EXPECTED_CONDITIONS,
            [condition["name"] for condition in self.config["conditions"]],
        )

    def test_only_two_conditions_require_new_generation(self):
        self.assertEqual(2, sum(condition["new_generation"] for condition in self.config["conditions"]))
        self.assertEqual(12, 6 * sum(condition["new_generation"] for condition in self.config["conditions"]))

    def test_every_task_has_literal_signature_and_hashed_packet(self):
        for task in self.config["tasks"]:
            self.assertIn(f"{task['function']}(", task["target_signature"])
            packet = ROOT / task["retrieval_packet"]
            self.assertTrue(packet.is_file())
            self.assertEqual(task["retrieval_sha256"], pilot_b.sha256(packet))


if __name__ == "__main__":
    unittest.main()
