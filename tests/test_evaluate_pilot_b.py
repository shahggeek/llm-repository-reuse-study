import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
MODULE_PATH = SCRIPTS / "evaluate_pilot_b.py"
SPEC = importlib.util.spec_from_file_location("evaluate_pilot_b_tested", MODULE_PATH)
evaluate_pilot_b = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(evaluate_pilot_b)


class PilotBEvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.config = evaluate_pilot_b.pilot_b.read_json(evaluate_pilot_b.CONFIG_PATH)
        self.task = self.config["tasks"][0]

    def complete_record(self, condition):
        record = evaluate_pilot_b.run_pilot_b.initial_record(
            self.config, self.task, condition
        )
        record["completed_at"] = "2026-09-24T00:00:00+00:00"
        record["turns"] = [{}, {}, {}]
        return record

    def test_validate_record_accepts_matching_guardrail_record(self):
        record = self.complete_record("engineering-guardrails")
        evaluate_pilot_b.validate_record(
            record, self.config, self.task, "engineering-guardrails"
        )

    def test_validate_record_rejects_wrong_retrieval_digest(self):
        record = self.complete_record("engineering-guardrails-retrieval")
        record["retrieval_packet_sha256"] = "0" * 64
        with self.assertRaises(evaluate_pilot_b.PilotBEvaluationError):
            evaluate_pilot_b.validate_record(
                record,
                self.config,
                self.task,
                "engineering-guardrails-retrieval",
            )


if __name__ == "__main__":
    unittest.main()
