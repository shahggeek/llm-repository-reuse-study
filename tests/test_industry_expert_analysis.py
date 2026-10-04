import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "industry_review", ROOT / "scripts/analyze_industry_expert_reviews.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class IndustryExpertAnalysisTests(unittest.TestCase):
    def test_numeric_experience_is_binned(self):
        self.assertEqual(MODULE.experience_category(4), "1–5 years")
        self.assertEqual(MODULE.experience_category(9), "6–10 years")
        self.assertEqual(MODULE.experience_category(15), "11–15 years")
        self.assertEqual(MODULE.experience_category(19), "16+ years")

    def test_variant_mapping(self):
        self.assertEqual(MODULE.mapped_choice("A", "A", "B"), "retrieval")
        self.assertEqual(MODULE.mapped_choice("A", "B", "A"), "comparator")
        self.assertEqual(MODULE.mapped_choice("No material difference", "A", "B"),
                         "no-material-difference")

    def test_frozen_summary_matches_planned_descriptive_result(self):
        summary = json.loads(
            (ROOT / "results/pilot/industry-expert-review-summary.json").read_text()
        )
        self.assertEqual(summary["status"], "decoded-after-frozen-intake")
        self.assertEqual((summary["reviewers"], summary["cases"], summary["judgments"]),
                         (4, 6, 24))
        primary = summary["primary_contrasts"]
        self.assertEqual(primary["case_ids"], ["IE-RV-104", "IE-RV-105", "IE-RV-106"])
        self.assertEqual(primary["preferred_arm"], {"retrieval": 12})
        self.assertEqual(primary["retrieval_decision"], {"Approve": 12})
        self.assertEqual(primary["repository_fit_delta"]["positive"], 12)
        self.assertEqual(primary["repository_fit_delta"]["median"], 2.0)
        self.assertEqual(primary["maintainability_delta"]["positive"], 12)
        self.assertEqual(primary["maintainability_delta"]["median"], 2.0)

    def test_intake_was_frozen_before_decoding(self):
        intake = json.loads(
            (ROOT / "results/pilot/industry-expert-review-intake-frozen.json").read_text()
        )
        self.assertEqual(intake["status"], "frozen-before-treatment-decoding")
        self.assertEqual(intake["final_included_reviewers"], 4)
        self.assertTrue(all(item["included"] for item in intake["responses"]))


if __name__ == "__main__":
    unittest.main()
