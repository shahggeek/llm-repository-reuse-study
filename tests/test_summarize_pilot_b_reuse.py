import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/summarize_pilot_b_reuse.py"
SPEC = importlib.util.spec_from_file_location("summarize_pilot_b_reuse", MODULE_PATH)
summary = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(summary)


class PilotBReuseSummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        trajectory_root = MODULE_PATH.parents[1] / "data" / "generated-trajectories" / "pilot-b"
        if not any(trajectory_root.glob("*/record.json")):
            raise unittest.SkipTest("requires the archived Pilot B trajectories")
        cls.result, cls.rows = summary.build_outputs()

    def test_review_covers_all_new_eligible_correct_checkpoints(self):
        self.assertEqual(23, len(self.rows))
        self.assertEqual(
            9,
            self.result["conditions"]["engineering-guardrails"]["checkpoints"],
        )
        self.assertEqual(
            14,
            self.result["conditions"]["engineering-guardrails-retrieval"][
                "checkpoints"
            ],
        )

    def test_retrieval_eliminates_reviewed_missed_reuse(self):
        guardrails = self.result["conditions"]["engineering-guardrails"]
        retrieval = self.result["conditions"]["engineering-guardrails-retrieval"]
        self.assertEqual(4, guardrails["missed_reuse"]["checkpoints"])
        self.assertEqual(0, retrieval["missed_reuse"]["checkpoints"])
        self.assertEqual(14, retrieval["reuse_class_counts"]["R1"])

    def test_shared_new_condition_transitions_are_paired(self):
        paired = self.result["paired_comparisons"]["retrieval_vs_guardrails"]
        self.assertEqual(9, paired["shared_functionally_correct_checkpoints"])
        self.assertEqual(
            {"R1->R1": 5, "R2->R1": 4}, paired["reuse_transitions"]
        )
        self.assertEqual(4, len(paired["missed_to_appropriate"]))
        self.assertEqual(5, len(paired["newly_functionally_correct_after"]))

    def test_baseline_to_retrieval_contains_add_in_order_improvement(self):
        paired = self.result["paired_comparisons"]["retrieval_vs_baseline"]
        self.assertEqual(
            {"R1->R1": 5, "R2->R1": 3, "R3->R1": 2},
            paired["reuse_transitions"],
        )


if __name__ == "__main__":
    unittest.main()
