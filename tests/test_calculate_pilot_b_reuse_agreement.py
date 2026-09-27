import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/calculate_pilot_b_reuse_agreement.py"
SPEC = importlib.util.spec_from_file_location("calculate_pilot_b_reuse_agreement", MODULE_PATH)
agreement = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(agreement)


class PilotBReuseAgreementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = agreement.calculate()

    def test_complete_response_set(self):
        self.assertEqual(20, self.result["implementation_count"])
        self.assertEqual(10, self.result["paired_case_count"])

    def test_pre_adjudication_agreement_is_preserved(self):
        self.assertEqual(19, self.result["reuse"]["exact_agreement"]["matches"])
        self.assertAlmostEqual(0.9029126213592233, self.result["reuse"]["linear_weighted_cohens_kappa"])
        self.assertEqual(20, self.result["binary_missed_reuse"]["exact_agreement"]["matches"])
        self.assertEqual(19, self.result["context_availability"]["exact_agreement"]["matches"])
        self.assertAlmostEqual(0.9534883720930233, self.result["context_availability"]["linear_weighted_cohens_kappa"])

    def test_only_two_disagreements(self):
        identities = {(row["case_id"], row["variant"]) for row in self.result["disagreements"]}
        self.assertEqual({("PB-RV-106", "B"), ("PB-RV-110", "B")}, identities)


if __name__ == "__main__":
    unittest.main()
