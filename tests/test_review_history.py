import unittest

from campaign_copilot.review_history import summarize_experiment_review_history


class ReviewHistoryTests(unittest.TestCase):
    def setUp(self):
        self.export = {
            "campaign_id": "C-1",
            "items": [
                {"cell_id": "CELL-A", "action": "pause_and_review"},
                {"cell_id": "CELL-B", "action": "hold_and_test"},
            ],
            "approval_applied": False,
            "platform_writes_executed": 0,
            "external_actions_executed": 0,
        }
        self.history = [
            {"review_id": "R-1", "campaign_id": "C-1", "cell_id": "CELL-A", "reviewed_on": "2026-08-01", "action": "pause_and_review", "status": "accepted", "note": "ok", "approval_applied": False},
            {"review_id": "R-2", "campaign_id": "C-1", "cell_id": "CELL-B", "reviewed_on": "2026-08-02", "action": "hold_and_test", "status": "deferred", "note": "wait", "approval_applied": False},
        ]

    def test_summary_is_deterministic_and_non_executing(self):
        summary = summarize_experiment_review_history(self.export, self.history)
        self.assertEqual(summary["entry_count"], 2)
        self.assertEqual(summary["status_counts"], {"accepted": 1, "deferred": 1})
        self.assertFalse(summary["approval_applied"])
        self.assertEqual(summary["platform_writes_executed"], 0)

    def test_duplicate_review_id_is_rejected(self):
        duplicate = [*self.history, dict(self.history[0])]
        with self.assertRaisesRegex(ValueError, "unique"):
            summarize_experiment_review_history(self.export, duplicate)

    def test_unknown_cell_is_rejected(self):
        invalid = [dict(self.history[0], cell_id="CELL-X")]
        with self.assertRaisesRegex(ValueError, "does not exist"):
            summarize_experiment_review_history(self.export, invalid)

    def test_out_of_order_dates_are_rejected(self):
        invalid = [dict(self.history[0]), dict(self.history[1], reviewed_on="2026-07-01")]
        with self.assertRaisesRegex(ValueError, "chronological"):
            summarize_experiment_review_history(self.export, invalid)


if __name__ == "__main__":
    unittest.main()
