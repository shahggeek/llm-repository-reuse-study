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
        self.assertFalse(any(path.startswith("work/") for path in self.by_path))

    def test_scoped_license_and_attribution_files_are_included(self):
        for path in (
            "CITATION.cff",
            "LICENSE",
            "LICENSE_SCOPE.md",
            "NOTICE",
            "THIRD_PARTY_LICENSES.md",
        ):
            self.assertIn(path, self.by_path)

    def test_public_makefile_exposes_only_public_commands(self):
        content = self.by_path["Makefile"].decode("utf-8")
        self.assertIn("evidence-check:", content)
        self.assertIn("reconstruct-prompts:", content)
        for private_target in (
            "paper-pdf",
            "industry-review",
            "submission-artifact",
            "reuse-pilot-b-extract",
        ):
            self.assertNotIn(private_target, content)
        self.assertNotIn("artifacts/PUBLIC_MAKEFILE", self.by_path)

    def test_public_gitignore_protects_reconstructed_and_local_material(self):
        content = self.by_path[".gitignore"].decode("utf-8")
        self.assertIn("reconstructed-prompts/", content)
        self.assertIn(".cache/", content)
        self.assertNotIn("data/generated-trajectories/**", content)
        self.assertNotIn("artifacts/PUBLIC_GITIGNORE", self.by_path)

    def test_public_ci_requires_complete_evidence_inventory(self):
        content = self.by_path[".github/workflows/verify.yml"].decode("utf-8")
        self.assertIn("make evidence-check", content)
        self.assertNotIn("artifacts/PUBLIC_VERIFY_WORKFLOW.yml", self.by_path)

    def test_public_readme_discloses_filtered_history(self):
        content = self.by_path["README.md"].decode("utf-8")
        self.assertIn("Public history provenance", content)
        self.assertIn("commit hashes necessarily differ", content)

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

    def test_benchmark_authored_prompt_text_is_omitted_but_hash_bound(self):
        records = [
            json.loads(content)
            for path, content in self.by_path.items()
            if path.startswith("data/generated-trajectories/")
            and path.endswith("/record.json")
        ]
        if not records:
            self.skipTest("requires the complete local or packaged evidence tree")
        omission = artifact.BENCHMARK_TEXT_OMISSION
        for record in records:
            self.assertFalse(
                record["public_prompt_policy"]["benchmark_authored_text_included"]
            )
            for turn in record["turns"]:
                self.assertEqual(omission, turn["instruction"])
                self.assertEqual(omission, turn["prompt"])
                self.assertEqual(64, len(turn["instruction_source_sha256"]))
                self.assertEqual(64, len(turn["rendered_prompt_sha256"]))

        prompt_files = [
            content.decode("utf-8")
            for path, content in self.by_path.items()
            if path.startswith("data/generated-trajectories/")
            and path.endswith(".prompt.txt")
        ]
        self.assertEqual(147, len(prompt_files))
        self.assertTrue(
            all("Benchmark-derived prompt omitted" in content for content in prompt_files)
        )


if __name__ == "__main__":
    unittest.main()
