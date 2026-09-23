import importlib.util
import csv
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/calculate_reuse_agreement.py"
SPEC = importlib.util.spec_from_file_location("calculate_reuse_agreement", MODULE_PATH)
agreement = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(agreement)


class ReuseAgreementTests(unittest.TestCase):
    def test_perfect_weighted_kappa(self):
        labels = ["R0", "R1", "R2", "R3"]
        self.assertEqual(1.0, agreement.weighted_kappa(labels, labels, agreement.REUSE_LABELS))

    def test_weighted_kappa_penalizes_larger_disagreement(self):
        first = ["R0", "R0", "R3", "R3"]
        adjacent = ["R1", "R1", "R2", "R2"]
        opposite = ["R3", "R3", "R0", "R0"]
        self.assertGreater(
            agreement.weighted_kappa(first, adjacent, agreement.REUSE_LABELS),
            agreement.weighted_kappa(first, opposite, agreement.REUSE_LABELS),
        )

    def test_exact_agreement(self):
        result = agreement.exact_agreement(["R0", "R1"], ["R0", "R2"])
        self.assertEqual({"matches": 1, "n": 2, "rate": 0.5}, result)

    def test_complete_blinded_response_set_is_accepted(self):
        key = agreement.read_json(agreement.KEY_PATH)
        fieldnames = [
            "case_id",
            "variant",
            "reuse_class",
            "context_class",
            "candidate_symbol",
            "evidence",
            "maintenance_consequence",
            "confidence",
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "responses.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                for case in key["cases"]:
                    for variant in ("A", "B"):
                        writer.writerow(
                            {
                                "case_id": case["case_id"],
                                "variant": variant,
                                "reuse_class": "R0",
                                "context_class": "C0",
                                "candidate_symbol": "",
                                "evidence": "Synthetic test evidence",
                                "maintenance_consequence": "None",
                                "confidence": "High",
                            }
                        )
            responses = agreement.load_responses(path, key)
            result = agreement.calculate(responses)
        self.assertEqual(20, len(responses))
        self.assertEqual(10, result["sample_size"])


if __name__ == "__main__":
    unittest.main()
