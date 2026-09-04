import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/evaluate_pilot_a.py"
SPEC = importlib.util.spec_from_file_location("evaluate_pilot_a", MODULE_PATH)
evaluate = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(evaluate)


class PilotAEvaluationTests(unittest.TestCase):
    def test_run_record_path_is_deterministic(self):
        protocol = {"pilot_a": {"batch_id": "batch"}}
        task = {"slug": "sample"}
        self.assertEqual(
            "batch-sample-01/record.json",
            str(evaluate.run_record_path(protocol, task)).split("pilot-a/")[-1],
        )

    def test_validate_record_rejects_incomplete_generation(self):
        protocol = {"benchmark": {"commit": "a" * 40}}
        task = {"slug": "sample", "hash_id": "b" * 24, "turns": 1}
        record = {
            "task_hash": "b" * 24,
            "benchmark_commit": "a" * 40,
            "completed_at": None,
            "turns": [{}],
        }
        with self.assertRaises(evaluate.EvaluationError):
            evaluate.validate_record(record, protocol, task)


if __name__ == "__main__":
    unittest.main()
