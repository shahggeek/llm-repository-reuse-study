import json
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReuseFullReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review = json.loads(
            (ROOT / "data/processed/pilot-a-reuse-full-review.json").read_text(encoding="utf-8")
        )
        cls.summary = json.loads(
            (ROOT / "results/pilot/pilot-a-reuse-full-review-summary.json").read_text(encoding="utf-8")
        )

    def test_review_covers_each_eligible_checkpoint_once(self):
        candidates = json.loads(
            (ROOT / "data/processed/pilot-a-reuse-candidates.json").read_text(encoding="utf-8")
        )
        expected = {(row["task_slug"], row["turn"]) for row in candidates["records"]}
        actual = {(row["task_slug"], row["turn"]) for row in self.review["records"]}
        self.assertEqual(24, len(self.review["records"]))
        self.assertEqual(24, len(actual))
        self.assertEqual(expected, actual)

    def test_summary_matches_review_labels(self):
        records = self.review["records"]
        reuse = Counter(row["reuse_class"] for row in records)
        context = Counter(row["context_class"] for row in records)
        missed = [row for row in records if row["reuse_class"] in {"R2", "R3"}]
        self.assertEqual(dict(reuse), {k: v for k, v in self.summary["reuse_class_counts"].items() if v})
        self.assertEqual(dict(context), self.summary["context_class_counts"])
        self.assertEqual(len(missed), self.summary["missed_reuse"]["checkpoints"])
        self.assertEqual(0, sum(row["context_class"] == "C3" for row in missed))
        self.assertEqual(4, len({row["task_slug"] for row in missed}))

    def test_prompt_provenance_correction_does_not_change_reuse(self):
        correction = self.summary["prompt_provenance_correction"]
        self.assertEqual(("ensureCapacity", 2), (correction["task_slug"], correction["turn"]))
        self.assertEqual("C2", correction["prior_context_class"])
        self.assertEqual("C3", correction["corrected_context_class"])
        self.assertFalse(correction["reuse_class_changed"])
        self.assertFalse(correction["missed_reuse_changed"])

    def test_cross_pilot_consistency_correction_is_frozen(self):
        correction = self.summary["cross_pilot_consistency_correction"]
        self.assertEqual(("nodeArrayMerge", 1), (correction["task_slug"], correction["turn"]))
        self.assertEqual("R2", correction["prior_reuse_class"])
        self.assertEqual("R3", correction["corrected_reuse_class"])
        self.assertFalse(correction["binary_missed_reuse_changed"])
        self.assertEqual(
            {"R0": 0, "R1": 13, "R2": 7, "R3": 4},
            self.summary["reuse_class_counts"],
        )


if __name__ == "__main__":
    unittest.main()
