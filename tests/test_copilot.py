import json
import unittest
from pathlib import Path

from campaign_copilot import CampaignBrief, CampaignCopilot, load_campaign, render_markdown


ROOT = Path(__file__).parents[1]
SAMPLE = ROOT / "data" / "sample_campaign.json"


def sample_payload() -> dict:
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


class CampaignCopilotTests(unittest.TestCase):
    def test_builds_reviewable_campaign_plan(self):
        result = CampaignCopilot().review(load_campaign(SAMPLE))
        self.assertEqual(result["status"], "ready_for_human_review")
        self.assertEqual(len(result["performance_review"]), 3)
        self.assertTrue(result["governance"]["human_approval_required"])
        self.assertFalse(result["governance"]["platform_write_executed"])

    def test_budget_envelopes_sum_to_total(self):
        result = CampaignCopilot().review(load_campaign(SAMPLE))
        allocated = sum(item["planned_budget"] for item in result["planning"]["budget_envelopes"])
        self.assertEqual(allocated, result["planning"]["total_budget"])

    def test_calculates_performance_metrics(self):
        result = CampaignCopilot().review(load_campaign(SAMPLE))
        cell = next(item for item in result["performance_review"] if item["cell_id"] == "CELL-SEARCH-A")
        self.assertEqual(cell["ctr"], 0.035)
        self.assertEqual(cell["cpa"], 90.0)
        self.assertEqual(cell["roas"], 3.33)

    def test_scale_recommendation_is_bounded_and_not_executed(self):
        result = CampaignCopilot().review(load_campaign(SAMPLE))
        action = next(
            item for item in result["optimization_recommendations"]
            if item["cell_id"] == "CELL-SEARCH-A"
        )
        self.assertEqual(action["action"], "candidate_scale")
        self.assertLessEqual(action["recommended_budget_change_pct"], 20)
        self.assertTrue(action["requires_human_approval"])
        self.assertFalse(action["executed"])

    def test_zero_conversion_cell_requires_pause_review(self):
        result = CampaignCopilot().review(load_campaign(SAMPLE))
        action = next(
            item for item in result["optimization_recommendations"]
            if item["cell_id"] == "CELL-SOCIAL-C"
        )
        self.assertEqual(action["action"], "pause_and_review")
        self.assertEqual(action["evidence_ids"], ["PERF-2026-003"])

    def test_prohibited_claim_blocks_optimization_release(self):
        payload = sample_payload()
        payload["creatives"][0]["headline"] = "Guaranteed results for every buyer"
        result = CampaignCopilot().review(CampaignBrief.from_mapping(payload))
        self.assertEqual(result["status"], "blocked_claim_review")
        self.assertTrue(result["creative_review"]["release_blocked"])
        self.assertEqual(result["optimization_recommendations"], [])

    def test_zero_traffic_cell_is_safe(self):
        payload = sample_payload()
        payload["performance"][0].update({
            "spend": 0, "impressions": 0, "clicks": 0, "conversions": 0, "revenue": 0
        })
        result = CampaignCopilot().review(CampaignBrief.from_mapping(payload))
        cell = next(item for item in result["performance_review"] if item["cell_id"] == "CELL-SEARCH-A")
        self.assertEqual(cell["ctr"], 0)
        self.assertIsNone(cell["cpa"])
        self.assertEqual(cell["roas"], 0)

    def test_zero_conversion_high_roas_cell_does_not_scale(self):
        payload = sample_payload()
        payload["performance"][0].update({
            "spend": 1000, "conversions": 0, "revenue": 5000
        })
        result = CampaignCopilot().review(CampaignBrief.from_mapping(payload))
        action = next(
            item for item in result["optimization_recommendations"]
            if item["cell_id"] == "CELL-SEARCH-A"
        )
        self.assertEqual(action["action"], "hold_and_test")

    def test_rejects_observed_spend_above_budget(self):
        payload = sample_payload()
        payload["performance"][0]["spend"] = 40000
        with self.assertRaisesRegex(ValueError, "exceed total_budget"):
            CampaignBrief.from_mapping(payload)

    def test_rejects_invalid_funnel_counts(self):
        payload = sample_payload()
        payload["performance"][0]["clicks"] = 130000
        with self.assertRaisesRegex(ValueError, "monotonic"):
            CampaignBrief.from_mapping(payload)

    def test_reallocation_ceiling_cannot_exceed_twenty_percent(self):
        payload = sample_payload()
        payload["max_reallocation_pct"] = 25
        with self.assertRaisesRegex(ValueError, "no more than 20"):
            CampaignBrief.from_mapping(payload)

    def test_markdown_contains_metric_sources_and_governance(self):
        markdown = render_markdown(CampaignCopilot().review(load_campaign(SAMPLE)))
        self.assertIn("[PERF-2026-001]", markdown)
        self.assertIn("Platform write executed: no", markdown)
        self.assertIn("All inputs and performance values are synthetic", markdown)


if __name__ == "__main__":
    unittest.main()
