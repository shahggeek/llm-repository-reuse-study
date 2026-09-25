import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
MODULE_PATH = SCRIPTS / "run_pilot_b.py"
SPEC = importlib.util.spec_from_file_location("run_pilot_b_tested", MODULE_PATH)
run_pilot_b = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(run_pilot_b)


class PilotBRunnerTests(unittest.TestCase):
    def setUp(self):
        self.config = run_pilot_b.pilot_b.read_json(run_pilot_b.CONFIG_PATH)

    def test_every_frozen_packet_loads_with_exact_prompt_source(self):
        for task in self.config["tasks"]:
            packet = run_pilot_b.load_packet(task)
            self.assertEqual(task["turns"], len(packet["turn_datas"]))

    def test_retrieval_prompt_is_guardrail_prompt_plus_frozen_packet(self):
        for task in self.config["tasks"]:
            packet = run_pilot_b.load_packet(task)
            turn = packet["turn_datas"][0]
            guardrail = run_pilot_b.render_prompt(
                self.config, task, packet, "engineering-guardrails", turn, ""
            )
            retrieval = run_pilot_b.render_prompt(
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

    def test_v2_record_separates_retrieval_provenance(self):
        task = self.config["tasks"][0]
        guardrail = run_pilot_b.initial_record(
            self.config, task, "engineering-guardrails"
        )
        retrieval = run_pilot_b.initial_record(
            self.config, task, "engineering-guardrails-retrieval"
        )
        self.assertEqual(2, guardrail["schema_version"])
        self.assertIsNone(guardrail["retrieval_packet_sha256"])
        self.assertEqual(task["retrieval_sha256"], retrieval["retrieval_packet_sha256"])
        self.assertEqual(task["prompt_source_sha256"], retrieval["prompt_source_sha256"])

    def test_preflight_renders_all_planned_prompt_skeletons_without_model_contact(self):
        with tempfile.TemporaryDirectory() as directory:
            report = run_pilot_b.preflight(self.config, Path(directory))
            self.assertFalse(report["model_contacted"])
            self.assertEqual(6, report["summary"]["tasks"])
            self.assertEqual(12, report["summary"]["new_trajectories"])
            self.assertEqual(46, report["summary"]["prompt_skeletons"])
            self.assertTrue((Path(directory) / "summary.json").is_file())


if __name__ == "__main__":
    unittest.main()
