import tempfile
import unittest
from pathlib import Path

from scripts import reconstruct_prompts


ROOT = Path(__file__).resolve().parents[1]


class ReconstructPromptsTests(unittest.TestCase):
    def test_all_prompt_hashes_match_pinned_benchmark(self):
        sr_eval = ROOT / ".cache/SR-Eval"
        if not sr_eval.is_dir():
            self.skipTest("requires the separately obtained pinned SR-Eval checkout")
        with tempfile.TemporaryDirectory() as directory:
            count = reconstruct_prompts.reconstruct(
                sr_eval, Path(directory), verify_only=False
            )
            self.assertEqual(147, count)
            self.assertEqual(
                147, len(list(Path(directory).glob("*/*/turn-*.prompt.txt")))
            )


if __name__ == "__main__":
    unittest.main()
