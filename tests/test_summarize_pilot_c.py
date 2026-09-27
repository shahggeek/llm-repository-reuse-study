import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import summarize_pilot_c


class PilotCSummaryTests(unittest.TestCase):
    def test_failure_classes_are_distinct(self):
        self.assertEqual(
            "compilation",
            summarize_pilot_c.failure_class(
                {"cumulatively_correct": False, "tests": [{"detail": "COMPILATION ERROR"}]}
            ),
        )
        self.assertEqual(
            "repository-style-gate",
            summarize_pilot_c.failure_class(
                {"cumulatively_correct": False, "tests": [{"detail": "Unused import [UnusedImports]"}]}
            ),
        )
        self.assertEqual(
            "behavioral-contract",
            summarize_pilot_c.failure_class(
                {"cumulatively_correct": False, "tests": [{"detail": "java.lang.AssertionError"}]}
            ),
        )

    def test_symbol_coverage_counts_only_declared_candidates(self):
        code = "objectToMap(source); mapToClass(values, clazz);"
        symbols = ["objectToMap(Object)", "mapToClass(Map<String, Object>, Class<T>)"]
        self.assertEqual(2, summarize_pilot_c.symbol_coverage(code, symbols))


if __name__ == "__main__":
    unittest.main()
