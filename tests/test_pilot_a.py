import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/pilot_a.py"
SPEC = importlib.util.spec_from_file_location("pilot_a", MODULE_PATH)
pilot_a = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(pilot_a)


class PilotAGenerationTests(unittest.TestCase):
    def test_extract_java_requires_one_nonempty_block(self):
        self.assertEqual("int x = 1;", pilot_a.extract_java("```java\nint x = 1;\n```"))
        with self.assertRaises(pilot_a.GenerationError):
            pilot_a.extract_java("no code block")
        with self.assertRaises(pilot_a.GenerationError):
            pilot_a.extract_java("```java\na();\n```\n```java\nb();\n```")

    def test_render_prompt_replaces_frozen_placeholders(self):
        rendered = pilot_a.render_prompt(
            "{{CONTEXT}}|{{PREVIOUS_CODE}}|{{INSTRUCTION}}",
            context="context",
            code="code",
            instruction="instruction",
        )
        self.assertEqual("context|code|instruction", rendered)

    def test_event_metadata_is_found_recursively(self):
        events = [
            {"type": "thread.started", "thread_id": "thread-123"},
            {"type": "turn.completed", "payload": {"usage": {"input_tokens": 12}}},
        ]
        self.assertEqual("thread-123", pilot_a.event_session_id(events))
        self.assertEqual({"input_tokens": 12}, pilot_a.event_usage(events))

    def test_frozen_protocol_hashes_only_prompt_files(self):
        protocol = pilot_a.read_json(pilot_a.PROTOCOL_PATH)
        hashes = pilot_a.prompt_hashes(protocol)
        self.assertEqual(4, len(hashes))
        self.assertTrue(all(len(digest) == 64 for digest in hashes.values()))

    def test_required_codex_version_comes_from_frozen_protocol(self):
        protocol = pilot_a.read_json(pilot_a.PROTOCOL_PATH)
        self.assertEqual("0.153.0", pilot_a.required_codex_version(protocol))

    def test_amendment_run_spec_is_isolated_from_original_batch(self):
        protocol = pilot_a.read_json(pilot_a.PROTOCOL_PATH)
        amendment = pilot_a.read_json(pilot_a.AMENDMENT_PATH)
        spec = pilot_a.run_spec(protocol, amendment)
        self.assertEqual(amendment["batch_id"], spec["batch_id"])
        self.assertEqual(pilot_a.AMENDMENT_PACKET_DIR, spec["packet_dir"])
        self.assertEqual(pilot_a.AMENDMENT_OUTPUT_ROOT, spec["output_root"])
        self.assertEqual(["rerank", "addInOrder"], [task["slug"] for task in spec["tasks"]])


if __name__ == "__main__":
    unittest.main()
