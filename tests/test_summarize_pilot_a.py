import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/summarize_pilot_a.py"
SPEC = importlib.util.spec_from_file_location("summarize_pilot_a", MODULE_PATH)
summary = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(summary)


class PilotAAdjustedSummaryTests(unittest.TestCase):
    def test_frozen_exclusions_are_checkpoint_scoped(self):
        self.assertEqual((False, "reference-ineligible"), summary.is_eligible("loadDocuments", 2))
        self.assertEqual((False, "prompt-confounded"), summary.is_eligible("set", 1))
        self.assertEqual((True, None), summary.is_eligible("set", 2))

    def test_context_sensitivity_exclusions_come_from_audit(self):
        audit = summary.read_json(summary.AUDIT_PATH)
        self.assertEqual(
            {"rerank": {1, 2, 3, 4}}, summary.context_sensitivity_exclusions(audit)
        )
        manifest = summary.read_json(summary.MANIFEST_PATH)
        amendment = summary.read_json(summary.AMENDMENT_PATH)
        metadata = {
            task["slug"]: task
            for task in manifest["tasks"]
            if task["slug"] not in {"copyToTarget", "mergeBeans"}
        }
        metadata.update({task["slug"]: task for task in summary.amendment_tasks(amendment)})
        strict = summary.strict_signature_exclusions(audit, metadata)
        self.assertEqual(
            {"invert", "writeInline", "calculatePhaseTimeGradient", "rerank"},
            set(strict),
        )
        self.assertEqual(17, sum(len(turns) for turns in strict.values()))

    def test_add_checkpoint_counts_same_turn_outcome(self):
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

    def test_artifact_digest_is_sha256(self):
        digest = summary.artifact_digest(summary.PROTOCOL_PATH)
        self.assertEqual("experiment/config/protocol.json", digest["path"])
        self.assertEqual(64, len(digest["sha256"]))
        self.assertGreater(digest["bytes"], 0)


if __name__ == "__main__":
    unittest.main()
