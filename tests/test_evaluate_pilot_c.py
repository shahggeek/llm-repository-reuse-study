import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import evaluate_pilot_c


class PilotCEvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.config = evaluate_pilot_c.pilot_c.read_json(evaluate_pilot_c.CONFIG_PATH)
        self.task = self.config["tasks"][0]

    def complete_record(self, condition, repetition):
        record = evaluate_pilot_c.run_pilot_c.initial_record(
            self.config, self.task, condition, repetition
        )
        record["completed_at"] = "2026-09-27T00:00:00+00:00"
        record["turns"] = [{}, {}]
        return record

    def test_validate_record_accepts_matching_repetition(self):
        record = self.complete_record("engineering-guardrails", 2)
        evaluate_pilot_c.validate_record(
            record, self.config, self.task, "engineering-guardrails", 2
        )

    def test_validate_record_rejects_wrong_repetition(self):
        record = self.complete_record("engineering-guardrails-retrieval", 2)
        with self.assertRaises(evaluate_pilot_c.PilotCEvaluationError):
            evaluate_pilot_c.validate_record(
                record,
                self.config,
                self.task,
                "engineering-guardrails-retrieval",
                1,
            )


if __name__ == "__main__":
    unittest.main()
