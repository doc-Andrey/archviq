from __future__ import annotations

import io
import unittest

from site_questionnaire import architecture_gap, load_architecture_instrument, parse_cognitive_csv, score_architecture_responses


class SiteQuestionnaireTests(unittest.TestCase):
    def test_neutral_answers_score_fifty(self):
        instrument = load_architecture_instrument()
        responses = {
            item["id"]: 3
            for scale in instrument["scales"].values()
            for item in scale["items"]
        }
        scores = score_architecture_responses(responses)
        self.assertEqual(set(scores), set(instrument["scales"]))
        self.assertTrue(all(value == 50.0 for value in scores.values()))

    def test_gap_is_signed_questionnaire_minus_engine(self):
        engine = {axis: 40 for axis in ("resource", "switching", "lock", "novelty", "control", "processing_cost")}
        questionnaire = {
            "resource_expression": 55,
            "switching_expression": 55,
            "lock_expression": 55,
            "novelty_expression": 55,
            "control_expression": 55,
            "processing_cost_expression": 55,
        }
        self.assertEqual(architecture_gap(engine, questionnaire)["resource"]["signed_gap"], 15.0)

    def test_cognitive_export_parser(self):
        csv_data = io.StringIO(
            "SRT_median_rt,SRT_sd_rt,CHOICE_accuracy,NBACK_accuracy,SIMON_accuracy,COMPLEX_ACC_accuracy\n"
            "280,44,0.96,0.82,0.91,0.88\n"
        )
        result = parse_cognitive_csv(csv_data)
        self.assertEqual(result["status"], "RAW_TASK_METRICS_NOT_NORMED")
        self.assertEqual(result["metrics"]["SRT_median_rt"], 280.0)


if __name__ == "__main__":
    unittest.main()
