import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
MODULE_PATH = ROOT / "scripts/finalize_pilot_b_reuse.py"
SPEC = importlib.util.spec_from_file_location("finalize_pilot_b_reuse", MODULE_PATH)
finalize = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(finalize)


class FinalizePilotBReuseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adjudication = finalize.build_adjudication()
        cls.review = finalize.build_adjudicated_review()
        cls.summary = finalize.build_final_summary(cls.review, cls.adjudication)

    def test_adjudication_preserves_two_decisions(self):
        self.assertEqual(2, len(self.adjudication["decisions"]))
        self.assertEqual(20, len(self.adjudication["final_classifications"]))
        self.assertEqual(20, self.adjudication["summary"]["reuse_class_counts"]["R1"] + self.adjudication["summary"]["reuse_class_counts"]["R2"] + self.adjudication["summary"]["reuse_class_counts"]["R3"])

    def test_only_primary_new_label_change_is_guardrails_node_turn_one(self):
        changed = [row for row in self.review["records"] if row.get("adjudication_id")]
        self.assertEqual(1, len(changed))
        self.assertEqual(("nodeArrayMerge", 1, "R3", "C1"), (changed[0]["task_slug"], changed[0]["turn"], changed[0]["reuse_class"], changed[0]["context_class"]))

    def test_final_guardrails_and_retrieval_counts(self):
        guard = self.summary["conditions"]["engineering-guardrails"]
        retrieval = self.summary["conditions"]["engineering-guardrails-retrieval"]
        self.assertEqual({"R0": 0, "R1": 5, "R2": 3, "R3": 1}, guard["reuse_class_counts"])
        self.assertEqual(4, guard["missed_reuse"]["checkpoints"])
        self.assertEqual({"R0": 0, "R1": 14, "R2": 0, "R3": 0}, retrieval["reuse_class_counts"])

    def test_paired_and_lineage_results(self):
        paired = self.summary["paired_comparisons"]["retrieval_vs_guardrails"]
        self.assertEqual({"R1->R1": 5, "R2->R1": 3, "R3->R1": 1}, paired["reuse_transitions"])
        lineage = self.summary["lineage_analysis"]
        self.assertEqual(4, lineage["clean_paired_lineages"])
        self.assertEqual(1, lineage["improved_lineages"])
        self.assertEqual(3, lineage["unchanged_appropriate_lineages"])


if __name__ == "__main__":
    unittest.main()
