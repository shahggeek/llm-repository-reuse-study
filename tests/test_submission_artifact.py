import csv
import io
import json
import unittest

from scripts import build_submission_artifact as artifact


class SubmissionArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = artifact.collect_entries()
        cls.by_path = {entry.path: entry.content for entry in cls.entries}

    def test_private_paths_and_internal_notes_are_excluded(self):
        self.assertNotIn("docs/resume-handoff.md", self.by_path)
        self.assertNotIn("docs/saner-industrial-ethics-inquiry-email.md", self.by_path)
        self.assertNotIn("paper/mock-review-2026-10-03.md", self.by_path)
        self.assertNotIn("paper/saner-readiness-audit.md", self.by_path)
        self.assertFalse(any(path.startswith("paper/") for path in self.by_path))
        self.assertFalse(any(path.startswith("outputs/") for path in self.by_path))
        private_root = "Reviewers" + "Work/"
        self.assertFalse(any(path.startswith(private_root) for path in self.by_path))
        self.assertFalse(any(path.startswith("work/infrastructure-failures/") for path in self.by_path))
        self.assertFalse(any(path.startswith("work/pilot-c-precontact-failures/") for path in self.by_path))

    def test_practitioner_response_release_removes_private_sources(self):
        content = self.by_path[
            "results/pilot/industry-expert-review-responses.csv"
        ].decode("utf-8")
        rows = list(csv.DictReader(io.StringIO(content)))
        self.assertEqual(len(rows), 24)
        self.assertNotIn("source_path", rows[0])
        self.assertNotIn("source_sha256", rows[0])
        self.assertEqual({row["reviewer_code"] for row in rows}, {"EXP-01", "EXP-02", "EXP-03", "EXP-04"})

    def test_practitioner_intake_release_removes_paths_and_hashes(self):
        content = self.by_path[
            "results/pilot/industry-expert-review-intake-frozen.json"
        ]
        data = json.loads(content)
        self.assertEqual(len(data["responses"]), 4)
        for response in data["responses"]:
            self.assertEqual(set(response), {"reviewer_code", "included"})

    def test_expected_evidence_counts(self):
        if not any(
            path.startswith("data/generated-trajectories/") and path.endswith("/record.json")
            for path in self.by_path
        ):
            self.skipTest("requires the complete local or packaged evidence tree")
        counts = artifact.experiment_counts(self.entries)
        artifact.validate_counts(counts)

    def test_secret_and_machine_path_scan(self):
        artifact.reject_private_or_secret_content(self.entries)

    def test_provider_identifiers_are_pseudonymized(self):
        records = [
            json.loads(content)
            for path, content in self.by_path.items()
            if path.startswith("data/generated-trajectories/")
            and path.endswith("/record.json")
        ]
        if not records:
            self.skipTest("requires the complete local or packaged evidence tree")
        self.assertTrue(
            all(record["session_id"].startswith("session-") for record in records)
        )


if __name__ == "__main__":
    unittest.main()
