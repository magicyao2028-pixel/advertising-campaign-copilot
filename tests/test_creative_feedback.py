import copy
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from campaign_copilot.creative_feedback import load_feedback, replay_creative_feedback, write_feedback_report


ROOT = Path(__file__).parents[1]
CAMPAIGN = ROOT / "data/sample_campaign.json"
FEEDBACK = ROOT / "data/creative_feedback.json"


class CreativeFeedbackTests(unittest.TestCase):
    def test_replays_accepted_feedback_and_excludes_pending(self):
        report = replay_creative_feedback(CAMPAIGN, FEEDBACK)
        self.assertEqual(report["summary"], {"total_feedback": 3, "replayed": 2, "passed": 2, "failed": 0, "excluded": 1})
        self.assertEqual(report["excluded"][0]["feedback_id"], "FB-AUTOPUBLISH-003")

    def test_guarantee_and_missing_substantiation_both_block(self):
        report = replay_creative_feedback(CAMPAIGN, FEEDBACK)
        guarantee, substantiation = report["replayed"]
        self.assertEqual(guarantee["actual"]["matched_rule_id"], "CLAIM-PERFORMANCE-GUARANTEE")
        self.assertIsNone(substantiation["actual"]["matched_rule_id"])
        self.assertTrue(all(item["actual"]["release_blocked"] for item in report["replayed"]))
        self.assertTrue(all(item["actual"]["optimization_recommendations"] == 0 for item in report["replayed"]))

    def test_rejects_duplicate_ids_and_unknown_target(self):
        payload = json.loads(FEEDBACK.read_text(encoding="utf-8"))
        payload["records"].append(copy.deepcopy(payload["records"][0]))
        with TemporaryDirectory() as directory:
            path = Path(directory) / "feedback.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "present and unique"):
                load_feedback(path)

        payload = json.loads(FEEDBACK.read_text(encoding="utf-8"))
        payload["records"][0]["replay"]["claim_id"] = "UNKNOWN"
        with TemporaryDirectory() as directory:
            path = Path(directory) / "feedback.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unknown feedback claim_id"):
                replay_creative_feedback(CAMPAIGN, path)

    def test_report_is_reproducible(self):
        report = replay_creative_feedback(CAMPAIGN, FEEDBACK)
        with TemporaryDirectory() as directory:
            json_path, md_path = Path(directory) / "report.json", Path(directory) / "report.md"
            write_feedback_report(report, json_path, md_path)
            first = (json_path.read_bytes(), md_path.read_bytes())
            write_feedback_report(report, json_path, md_path)
            self.assertEqual(first, (json_path.read_bytes(), md_path.read_bytes()))

    def test_rejects_malformed_batch_and_replay_values(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "feedback.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must contain an object"):
                load_feedback(path)

        payload = json.loads(FEEDBACK.read_text(encoding="utf-8"))
        payload["records"][0]["replay"]["text"] = {"unsafe": True}
        with TemporaryDirectory() as directory:
            path = Path(directory) / "feedback.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non-empty strings"):
                load_feedback(path)


if __name__ == "__main__":
    unittest.main()
