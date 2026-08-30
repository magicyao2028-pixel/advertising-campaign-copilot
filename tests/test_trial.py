import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from campaign_copilot.trial import load_json_object, run_trial, validate_external_intake, validate_feedback, write_trial_report
from campaign_copilot.experiment_queue import build_experiment_queue
from campaign_copilot.review_export import build_experiment_review_export


ROOT = Path(__file__).parents[1]


class TrialTests(unittest.TestCase):
    def test_complete_trial_passes_without_platform_write(self):
        report = run_trial(ROOT)
        self.assertTrue(report["overall_passed"])
        self.assertEqual(report["core_flow"]["feedback_cases_passed"], 2)
        self.assertEqual(report["core_flow"]["platform_writes_executed"], 0)
        self.assertEqual(report["experiment_review_export"]["item_count"], len(report["experiment_queue"]["items"]))
        self.assertFalse(report["experiment_review_export"]["approval_applied"])

    def test_external_intake_requires_full_sha(self):
        payload = load_json_object(ROOT / "evidence/external_intake.json")
        payload["candidates"][0]["commit"] = "short"
        with self.assertRaisesRegex(ValueError, "full commit SHA"):
            validate_external_intake(payload)

    def test_feedback_must_be_accepted(self):
        payload = load_json_object(ROOT / "evidence/feedback_case.json")
        payload["decision"] = "pending"
        with self.assertRaisesRegex(ValueError, "accepted"):
            validate_feedback(ROOT, payload)

    def test_trial_report_is_reproducible(self):
        with TemporaryDirectory() as directory:
            json_path, md_path = Path(directory) / "trial.json", Path(directory) / "trial.md"
            first = write_trial_report(ROOT, json_path, md_path)
            first_bytes = (json_path.read_bytes(), md_path.read_bytes())
            second = write_trial_report(ROOT, json_path, md_path)
            self.assertEqual(first, second)
            self.assertEqual(first_bytes, (json_path.read_bytes(), md_path.read_bytes()))
            self.assertTrue(json.loads(json_path.read_text())["overall_passed"])

    def test_experiment_queue_requires_human_approval_and_no_writes(self):
        review = run_trial(ROOT)
        queue = build_experiment_queue({
            "campaign_id": "QUEUE-TEST",
            "optimization_recommendations": [
                {"cell_id": "C-2", "action": "candidate_scale", "evidence_ids": ["S-2"]},
                {"cell_id": "C-1", "action": "pause_and_review", "evidence_ids": ["S-1"]},
            ],
        })
        self.assertEqual(queue["items"][0]["priority"], "critical")
        self.assertTrue(queue["human_approval_required"])
        self.assertEqual(queue["platform_writes_executed"], 0)
        self.assertTrue(review["experiment_queue"]["items"])

    def test_review_export_preserves_queue_boundary(self):
        review = {"campaign_id": "QUEUE-TEST", "optimization_recommendations": [{"cell_id": "C-1", "action": "hold_and_test", "evidence_ids": ["S-1"]}]}
        queue = build_experiment_queue(review)
        export = build_experiment_review_export(review, queue)
        self.assertEqual(export["item_count"], 1)
        self.assertEqual(export["items"][0]["status"], "pending")
        self.assertFalse(export["approval_applied"])
        self.assertEqual(export["platform_writes_executed"], 0)


if __name__ == "__main__":
    unittest.main()
