import json
import tempfile
import unittest
from pathlib import Path

from analysis_modules.ai_work_analysis import analyze as analyze_ai
from analysis_modules.burnout_analysis import analyze as analyze_burnout
from analysis_modules.architecture_gap_analysis import analyze as analyze_gap
from analysis_modules.common import load_json
from analysis_modules.compatibility_analysis import analyze as analyze_pair
from analysis_modules.score_questionnaires import score_instrument_row
from analysis_modules.validate_domain_dimensionality import dimensionality_report, make_synthetic_records, run_batch


ROOT = Path(__file__).resolve().parents[1]


class AnalysisModuleTests(unittest.TestCase):
    def setUp(self):
        self.registry = load_json(ROOT / "config" / "validation_registry_unvalidated.json")

    def test_research_modules_run_with_closed_gate(self):
        person = load_json(ROOT / "examples" / "person_example.json")
        pair = load_json(ROOT / "examples" / "pair_example.json")
        self.assertEqual(analyze_burnout(person, self.registry)["mode"], "RESEARCH_ONLY")
        self.assertEqual(analyze_ai(person, self.registry)["mode"], "RESEARCH_ONLY")
        result = analyze_pair(pair, self.registry)
        self.assertEqual(result["mode"], "RESEARCH_ONLY")
        self.assertIsNone(result["global_compatibility_percent"])
        self.assertIn("decision_role_coordination", result["domains"])
        self.assertAlmostEqual(result["role_processing_evidence"]["nested_auc"], 0.9256198347107437)
        burnout = analyze_burnout(person, self.registry)
        self.assertFalse(burnout["experimental_decision_load"]["included_in_integrated_index"])
        ai = analyze_ai(person, self.registry)
        self.assertIn("agency_retention", ai["work_modes"])
        self.assertIn("passive_acceptance_risk", ai["work_modes"])
        gap = analyze_gap(person, self.registry)
        self.assertEqual(gap["mode"], "RESEARCH_ONLY")
        self.assertIsNone(gap["global_tension_percent"])
        self.assertEqual(set(gap["axis_comparison"]), {"resource", "switching", "lock", "novelty", "control", "processing_cost"})

    def test_client_mode_is_blocked(self):
        person = load_json(ROOT / "examples" / "person_example.json")
        with self.assertRaises(RuntimeError):
            analyze_burnout(person, self.registry, research_mode=False)

    def test_reverse_scoring(self):
        blueprint = load_json(ROOT / "config" / "thematic_questionnaires.json")
        instrument = blueprint["instruments"]["burnout_questionnaire"]
        row = {"CLIENT_ID": "X"}
        for scale in instrument["scales"].values():
            for item in scale["items"]:
                row[item["id"]] = 1 if not item.get("reverse") else 5
        scored = score_instrument_row(row, instrument)
        self.assertEqual(scored["exhaustion"], 0.0)
        self.assertTrue(scored["QUESTIONNAIRE_VALID"])

    def test_incomplete_scale_is_not_scored(self):
        blueprint = load_json(ROOT / "config" / "thematic_questionnaires.json")
        instrument = blueprint["instruments"]["architecture_questionnaire"]
        scored = score_instrument_row({"CLIENT_ID": "X", "ARCH_RES_01": 5}, instrument)
        self.assertTrue(str(scored["resource_expression"]) == "nan")
        self.assertFalse(scored["QUESTIONNAIRE_VALID"])

    def test_revised_output_formulas_have_no_structural_collapse(self):
        for module in ("compatibility", "burnout", "ai_work", "architecture_gap"):
            records = make_synthetic_records(module, 1500, seed=43)
            frame = run_batch(module, records, self.registry)
            report = dimensionality_report(frame, "synthetic", repetitions=100, seed=43)
            self.assertEqual(report["status"], "STRUCTURALLY_DISTINCT")
            self.assertFalse(report["warning_pairs"])


if __name__ == "__main__":
    unittest.main()
