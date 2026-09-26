import hashlib
import json
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KEY_PATH = ROOT / "results/pilot/pilot-b-reuse-blind-key.json"
MANIFEST_PATH = ROOT / "results/pilot/pilot-b-reuse-review-package.json"


class PilotBReuseBlindKeyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.key = json.loads(KEY_PATH.read_text(encoding="utf-8"))
        self.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_selection_is_complete_balanced_and_unique(self) -> None:
        cases = self.key["cases"]
        self.assertEqual(10, len(cases))
        self.assertEqual(10, len({case["case_id"] for case in cases}))
        self.assertEqual(9, sum(case["comparison"] == "guardrails-vs-retrieval" for case in cases))
        self.assertEqual(1, sum(case["comparison"] == "baseline-vs-retrieval" for case in cases))
        self.assertEqual(5, sum(case["variant_a"]["condition"] == "engineering-guardrails-retrieval" for case in cases))
        self.assertEqual(5, sum(case["variant_b"]["condition"] == "engineering-guardrails-retrieval" for case in cases))

    def test_every_selected_checkpoint_is_cumulatively_correct(self) -> None:
        for case in self.key["cases"]:
            for variant in ("variant_a", "variant_b"):
                mapping = case[variant]
                run_id = mapping["run_id"]
                roots = (
                    ROOT / "data/generated-trajectories/pilot-b",
                    ROOT / "data/generated-trajectories/pilot-a-amendment",
                    ROOT / "data/generated-trajectories/pilot-a",
                )
                record_path = next((base / run_id / "record.json" for base in roots if (base / run_id / "record.json").exists()), None)
                self.assertIsNotNone(record_path, f"Missing record for {run_id}")
                record = json.loads(record_path.read_text(encoding="utf-8"))
                self.assertEqual(mapping["condition"], record.get("condition", "baseline"))
                turn = next(row for row in record["turns"] if int(row["turn"]) == int(case["turn"]))
                self.assertTrue(turn["cumulatively_correct"], f"{case['case_id']} {variant}")

    def test_workbook_is_frozen_and_does_not_expose_condition_identifiers(self) -> None:
        workbook = ROOT / self.manifest["workbook"]
        digest = hashlib.sha256(workbook.read_bytes()).hexdigest()
        self.assertEqual(self.manifest["workbook_sha256"], digest)
        with zipfile.ZipFile(workbook) as archive:
            xml = b"\n".join(
                archive.read(name)
                for name in archive.namelist()
                if name.endswith(".xml") or name.endswith(".rels")
            )
        for concealed in (
            b"engineering-guardrails",
            b"pilot-b-20260924T233242Z",
            b"pilot-a-amendment-20260923T012647Z",
            b"baseline-vs-retrieval",
        ):
            self.assertNotIn(concealed, xml)


if __name__ == "__main__":
    unittest.main()
