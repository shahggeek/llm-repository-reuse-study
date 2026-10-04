import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import pilot_c


class PilotCConfigTests(unittest.TestCase):
    def setUp(self):
        self.config = pilot_c.read_json(pilot_c.DEFAULT_CONFIG)

    def test_frozen_config_and_dataset_are_valid(self):
        if not (ROOT / ".cache" / "SR-Eval").is_dir():
            self.skipTest("requires the separately obtained pinned SR-Eval checkout")
        self.assertEqual([], pilot_c.validate_config(self.config, check_dataset=True))

    def test_rejects_jvector_or_single_repository_design(self):
        changed = copy.deepcopy(self.config)
        changed["tasks"][1]["repo"] = "jvector"
        errors = pilot_c.validate_config(changed)
        self.assertTrue(any("two distinct non-JVector" in error for error in errors))

    def test_rejects_retrieval_packet_hash_change(self):
        changed = copy.deepcopy(self.config)
        changed["tasks"][0]["retrieval_sha256"] = "0" * 64
        errors = pilot_c.validate_config(changed)
        self.assertTrue(any("retrieval packet SHA-256 mismatch" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
