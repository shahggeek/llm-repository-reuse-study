import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/pilot.py"
SPEC = importlib.util.spec_from_file_location("pilot", MODULE_PATH)
pilot = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(pilot)


class PilotHarnessTests(unittest.TestCase):
    def test_frozen_manifest_has_expected_strata_and_pairs(self):
        manifest = pilot.read_json(pilot.DEFAULT_MANIFEST)
        self.assertEqual([], pilot.validate_manifest(manifest))
        tasks = pilot.manifest_tasks(manifest)
        self.assertEqual(12, sum(task["stratum"] == "primary" for task in tasks))
        self.assertEqual(6, sum(task["stratum"] == "control" for task in tasks))
        self.assertEqual(6, sum(task["pilot_b"] for task in tasks))

    def test_match_tasks_detects_metadata_mismatch(self):
        manifest = {
            "tasks": [
                {
                    "slug": "sample",
                    "hash_id": "a" * 24,
                    "repo": "expected",
                    "function": "f",
                    "turns": 2,
                    "stratum": "primary",
                    "pilot_b": False,
                    "rationale": "test",
                }
            ]
        }
        row = {
            "hash_id": "a" * 24,
            "total_turn": 2,
            "turn_datas": [
                {"solution": "s1", "test": "t1"},
                {"solution": "s2", "test": "t2"},
            ],
            "metadata": {"repo": "actual", "func_name": "f"},
        }
        _, errors = pilot.match_tasks(manifest, [row])
        self.assertTrue(any("repo expected" in error for error in errors))

    def test_read_jsonl_reports_bad_line(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.jsonl"
            path.write_text('{}\n{"broken"\n', encoding="utf-8")
            with self.assertRaises(pilot.PilotError):
                pilot.read_jsonl(path)

    def test_smoke_plan_is_cumulative(self):
        task = {"slug": "x", "turns": 3}
        row = {
            "metadata": {"repo": "r", "test_instruction": "mvn test"},
            "turn_datas": [
                {"solution": "s1", "test": "t1"},
                {"solution": "s2", "test": "t2"},
                {"solution": "s3", "test": "t3"},
            ],
        }
        plan = pilot.smoke_plan(task, row)
        self.assertEqual(6, len(plan))
        self.assertEqual((3, 3), (plan[-1]["checkpoint_turn"], plan[-1]["test_turn"]))

    def test_smoke_status_distinguishes_cross_turn_from_executability_failures(self):
        self.assertEqual("pass", pilot.smoke_status(0, 0))
        self.assertEqual("partial", pilot.smoke_status(2, 0))
        self.assertEqual("fail", pilot.smoke_status(2, 1))


if __name__ == "__main__":
    unittest.main()
