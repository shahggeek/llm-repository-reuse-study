import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/structural_metrics.py"
SPEC = importlib.util.spec_from_file_location("structural_metrics", MODULE_PATH)
metrics = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(metrics)

HAS_PARSER = (
    importlib.util.find_spec("tree_sitter") is not None
    and importlib.util.find_spec("tree_sitter_java") is not None
    and importlib.util.find_spec("lizard") is not None
)


class StructuralMetricPureTests(unittest.TestCase):
    def test_comment_stripping_preserves_comment_markers_inside_strings(self):
        code = 'String url = "https://example.test"; // comment\n/* block */ return url;'
        stripped = metrics.strip_java_comments(code)
        self.assertIn('"https://example.test"', stripped)
        self.assertNotIn("comment", stripped)
        self.assertNotIn("block", stripped)
        self.assertEqual(2, metrics.source_line_count(code))

    def test_overhead_records_zero_reference(self):
        generated = {name: 2 for name in metrics.METRIC_NAMES}
        reference = {name: 1 for name in metrics.METRIC_NAMES}
        reference["throw_count"] = 0
        result = metrics.overhead(generated, reference)
        self.assertEqual(1, result["cyclomatic_complexity"]["absolute"])
        self.assertTrue(result["throw_count"]["reference_zero"])

    def test_percentile_uses_linear_interpolation(self):
        self.assertEqual(1.0, metrics.percentile([0.0, 2.0], 0.5))

    def test_clustered_bootstrap_is_deterministic(self):
        rows = [
            {
                "task_slug": "a",
                "overhead": {"physical_lines": {"absolute": 1}},
            },
            {
                "task_slug": "b",
                "overhead": {"physical_lines": {"absolute": -1}},
            },
        ]
        first = metrics.clustered_bootstrap(rows, "physical_lines", iterations=100)
        second = metrics.clustered_bootstrap(rows, "physical_lines", iterations=100)
        self.assertEqual(first, second)
        self.assertEqual(2, first["clusters"])


@unittest.skipUnless(HAS_PARSER, "Tree-sitter dependencies are installed by structural-check")
class StructuralMetricParserTests(unittest.TestCase):
    def test_hand_checked_control_flow_fixture(self):
        code = """public int example(int x, java.util.List<String> values) {
    int total = 0;
    if (x > 0 && values != null) {
        for (String value : values) {
            total += value.length();
        }
    } else {
        total = -1;
    }
    return total;
}"""
        result = metrics.extract_metrics(code)
        self.assertEqual(2, result["parameter_count"])
        self.assertEqual(4, result["cyclomatic_complexity"])
        self.assertEqual(4, result["parser_diagnostics"]["lizard_cyclomatic_complexity"])
        self.assertEqual(2, result["max_control_nesting"])
        self.assertEqual(2, result["branch_count"])
        self.assertEqual(1, result["method_invocation_count"])
        self.assertEqual(["length"], result["method_call_targets"])
        self.assertEqual(0, result["parser_diagnostics"]["error_nodes"])

    def test_all_selected_pairs_parse_and_selection_is_frozen(self):
        if not metrics.ORIGINAL_RECORD_DIR.is_dir():
            self.skipTest("ignored local Pilot A records are unavailable")
        pairs, _ = metrics.selected_pairs()
        self.assertEqual(24, len(pairs))
        self.assertEqual(16, sum(pair["strict_explicit_signature_subgroup"] for pair in pairs))
        for pair in pairs:
            metrics.extract_metrics(pair["generated_code"])
            metrics.extract_metrics(pair["reference_code"])


if __name__ == "__main__":
    unittest.main()
