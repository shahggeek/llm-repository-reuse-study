import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/summarize_pilot_b.py"
SPEC = importlib.util.spec_from_file_location("summarize_pilot_b", MODULE_PATH)
summary = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(summary)


class PilotBFunctionalSummaryTests(unittest.TestCase):
    def test_frozen_reference_exclusions_are_checkpoint_scoped(self):
        self.assertEqual({2, 3}, summary.REFERENCE_INELIGIBLE["loadDocuments"])
        self.assertEqual({5}, summary.REFERENCE_INELIGIBLE["nodeArrayMerge"])
        self.assertNotIn("diff", summary.REFERENCE_INELIGIBLE)

    def test_add_checkpoint_validates_and_counts_same_turn_result(self):
        counts = summary.empty_counts()
        summary.add_checkpoint(
            counts,
            {
                "turn": 2,
                "cumulatively_correct": False,
                "tests": [
                    {"test_turn": 1, "status": "pass"},
                    {"test_turn": 2, "status": "fail"},
                ],
            },
        )
        self.assertEqual(1, counts["passed_checks"])
        self.assertEqual(1, counts["failed_checks"])
        self.assertEqual(1, counts["same_turn_failed"])

    def test_count_delta_uses_after_minus_before(self):
        before = summary.empty_counts()
        after = summary.empty_counts()
        before["passed_checks"] = 4
        after["passed_checks"] = 7
        before["trajectories_with_correct_checkpoint"] = 1
        after["trajectories_with_correct_checkpoint"] = 2
        delta = summary.count_delta(after, before)
        self.assertEqual(3, delta["passed_checks"])
        self.assertEqual(1, delta["trajectories_with_correct_checkpoint"])

    def test_frozen_created_at_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "summary.json"
            path.write_text(json.dumps({"created_at": "2026-01-02T03:04:05+00:00"}))
            self.assertEqual(
                "2026-01-02T03:04:05+00:00", summary.frozen_created_at(path)
            )


if __name__ == "__main__":
    unittest.main()
