import copy
import unittest

from campaign_copilot.review_reconciliation import reconcile_campaign_review_feedback


class ReviewReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.export = {
            "campaign_id": "C-1",
            "items": [
                {"cell_id": "CELL-1", "action": "pause_and_review"},
                {"cell_id": "CELL-2", "action": "hold_and_test"},
            ],
            "approval_applied": False,
            "platform_writes_executed": 0,
            "external_actions_executed": 0,
        }
        self.history = [
            {"review_id": "R-1", "campaign_id": "C-1", "cell_id": "CELL-1", "action": "pause_and_review", "status": "accepted", "reviewed_on": "2026-08-01", "approval_applied": False},
            {"review_id": "R-2", "campaign_id": "C-1", "cell_id": "CELL-2", "action": "hold_and_test", "status": "deferred", "reviewed_on": "2026-08-02", "approval_applied": False},
        ]
        self.replay = {
            "record_count": 2,
            "replayed": [{"feedback_id": "F-1", "review_id": "R-1", "status": "accepted", "passed": True}],
            "excluded": [{"feedback_id": "F-2", "review_id": "R-2", "status": "pending", "passed": True}],
            "approval_applied": False,
            "campaign_state_changed": False,
            "platform_writes_executed": 0,
        }

    def run_reconciliation(self, **kwargs):
        return reconcile_campaign_review_feedback(
            self.export, self.history, self.replay, as_of_date="2026-09-09", **kwargs
        )

    def test_reconciles_accepted_feedback_and_stale_deferred_review(self):
        result = self.run_reconciliation(stale_after_days=30)
        self.assertEqual(result["reconciled_count"], 1)
        self.assertEqual(result["stale_review_count"], 1)
        self.assertEqual(result["reconciled_feedback"][0]["cell_id"], "CELL-1")
        self.assertEqual(result["stale_reviews"][0]["review_id"], "R-2")
        self.assertEqual(result["platform_writes_executed"], 0)

    def test_recent_deferred_review_is_not_stale(self):
        self.history[1]["reviewed_on"] = "2026-09-01"
        self.assertEqual(self.run_reconciliation(stale_after_days=30)["stale_review_count"], 0)

    def test_rejects_writing_export_or_replay(self):
        self.export["approval_applied"] = True
        with self.assertRaisesRegex(ValueError, "non-executing"):
            self.run_reconciliation()
        self.export["approval_applied"] = False
        self.replay["campaign_state_changed"] = True
        with self.assertRaisesRegex(ValueError, "non-executing"):
            self.run_reconciliation()

    def test_rejects_duplicate_export_cells(self):
        self.export["items"].append(copy.deepcopy(self.export["items"][0]))
        with self.assertRaisesRegex(ValueError, "unique"):
            self.run_reconciliation()

    def test_rejects_duplicate_history_ids(self):
        self.history[1]["review_id"] = "R-1"
        with self.assertRaisesRegex(ValueError, "unique"):
            self.run_reconciliation()

    def test_rejects_future_history(self):
        self.history[0]["reviewed_on"] = "2026-09-10"
        with self.assertRaisesRegex(ValueError, "future-dated"):
            self.run_reconciliation()

    def test_rejects_unknown_replay_review(self):
        self.replay["replayed"][0]["review_id"] = "UNKNOWN"
        with self.assertRaisesRegex(ValueError, "current review"):
            self.run_reconciliation()

    def test_rejects_invalid_replay_partition(self):
        self.replay["excluded"][0]["status"] = "accepted"
        with self.assertRaisesRegex(ValueError, "validated status"):
            self.run_reconciliation()

    def test_rejects_duplicate_feedback_across_partitions(self):
        self.replay["excluded"][0]["feedback_id"] = "F-1"
        with self.assertRaisesRegex(ValueError, "unique"):
            self.run_reconciliation()

    def test_rejects_boolean_or_zero_stale_threshold(self):
        for threshold in (True, 0):
            with self.subTest(threshold=threshold):
                with self.assertRaisesRegex(ValueError, "positive integer"):
                    self.run_reconciliation(stale_after_days=threshold)


if __name__ == "__main__":
    unittest.main()
