import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/screen_reuse_candidates.py"
SPEC = importlib.util.spec_from_file_location("screen_reuse_candidates", MODULE_PATH)
screen = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(screen)


class ReuseCandidateScreenTests(unittest.TestCase):
    def test_name_occurrences_match_whole_identifiers(self):
        self.assertEqual(2, screen.name_occurrences("growArrays(); growArrays", "growArrays"))
        self.assertEqual(0, screen.name_occurrences("regrowArrays", "growArrays"))
        self.assertEqual(1, screen.callable_occurrences("call growArrays()", "growArrays"))
        self.assertEqual(0, screen.callable_occurrences("scale the pivot row", "scale"))

    def test_explicit_reference_only_call_has_highest_priority(self):
        if not screen.PACKET_DIR.is_dir():
            self.skipTest("requires the archived Pilot A task packets")
        record = {
            "task_slug": "addInOrder",
            "repository": "jvector",
            "turn": 2,
            "run_id": "test",
            "prompt_context_classification": "explicit-consistent",
            "strict_explicit_signature_subgroup": True,
            "generated": {"method_call_targets": []},
            "reference": {"method_call_targets": ["growArrays"]},
        }
        result = screen.screen_record(record)
        self.assertEqual("explicit-review", result["screen_priority"])
        self.assertEqual("instruction-explicit", result["call_evidence"][0]["visibility"])

    def test_frozen_selection_has_24_records(self):
        if not screen.METRICS_PATH.is_file() or not screen.PACKET_DIR.is_dir():
            self.skipTest("ignored local Pilot A inputs are unavailable")
        records, summary = screen.build_outputs()
        self.assertEqual(24, len(records))
        self.assertEqual(10, summary["scope"]["trajectories"])

    def test_manual_pilot_summary_matches_labels(self):
        path = screen.ROOT / "results/pilot/pilot-a-reuse-rubric-pilot.json"
        data = screen.read_json(path)
        labels = [row["reuse_class"] for row in data["classifications"]]
        self.assertEqual(data["sample_size"], len(labels))
        for label, expected in data["summary"]["reuse_class_counts"].items():
            self.assertEqual(expected, labels.count(label))
        missed = sum(label in {"R2", "R3"} for label in labels)
        self.assertEqual(data["summary"]["candidate_missed_reuse_events"], missed)


if __name__ == "__main__":
    unittest.main()
