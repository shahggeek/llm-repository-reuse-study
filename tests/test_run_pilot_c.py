import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_pilot_c


class PilotCRunnerTests(unittest.TestCase):
    def setUp(self):
        self.config = run_pilot_c.pilot_c.read_json(run_pilot_c.CONFIG_PATH)

    def test_packets_load_with_exact_prompt_source(self):
        for task in self.config["tasks"]:
            packet = run_pilot_c.load_packet(self.config, task)
            self.assertEqual(task["turns"], len(packet["turn_datas"]))

    def test_retrieval_prompt_is_guardrail_prompt_plus_packet(self):
        for task in self.config["tasks"]:
            packet = run_pilot_c.load_packet(self.config, task)
            turn = packet["turn_datas"][0]
            guardrail = run_pilot_c.render_prompt(
                self.config, task, packet, "engineering-guardrails", turn, ""
            )
            retrieval = run_pilot_c.render_prompt(
                self.config,
                task,
                packet,
                "engineering-guardrails-retrieval",
                turn,
                "",
            )
            self.assertTrue(retrieval.startswith(guardrail))
            self.assertIn(task["target_signature"], guardrail)
            self.assertNotIn("Repository evidence packet (read-only)", guardrail)
            self.assertIn("Repository evidence packet (read-only)", retrieval)

    def test_v3_record_has_explicit_repetition(self):
        task = self.config["tasks"][0]
        record = run_pilot_c.initial_record(
            self.config, task, "engineering-guardrails-retrieval", 2
        )
        self.assertEqual(3, record["schema_version"])
        self.assertEqual(2, record["repetition"])
        self.assertTrue(record["run_id"].endswith("-r02"))
        self.assertEqual(task["retrieval_sha256"], record["retrieval_packet_sha256"])

    def test_preflight_counts_all_repeated_trajectories(self):
        with tempfile.TemporaryDirectory() as directory:
            report = run_pilot_c.preflight(self.config, Path(directory))
            self.assertFalse(report["model_contacted"])
            self.assertEqual(2, report["summary"]["repositories"])
            self.assertEqual(12, report["summary"]["new_trajectories"])
            self.assertEqual(24, report["summary"]["prompt_skeletons"])


if __name__ == "__main__":
    unittest.main()
