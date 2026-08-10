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
        self.assertEqual(cell["period"], "2026-07")

    def test_calculates_adjacent_period_changes_with_sources(self):
        result = CampaignCopilot().review(load_campaign(SAMPLE))
        trend = next(
            item for item in result["trend_review"]["comparable"]
            if item["cell_id"] == "CELL-SEARCH-A"
        )
        self.assertEqual(trend["comparison_period"], "2026-06")
        self.assertEqual(trend["current_period"], "2026-07")
        self.assertEqual(trend["evidence_ids"], ["PERF-2026-004", "PERF-2026-001"])
        self.assertEqual(trend["changes"]["ctr_percentage_points"], 0.5)
        self.assertEqual(trend["changes"]["roas_pct"], 14.83)

    def test_warns_when_periods_are_not_adjacent(self):
        result = CampaignCopilot().review(load_campaign(SAMPLE))
        warning = next(
            item for item in result["trend_review"]["warnings"]
            if item["cell_id"] == "CELL-VIDEO-B"
        )
        self.assertEqual(warning["code"], "non_adjacent_periods")
        self.assertEqual(warning["comparison_period"], "2026-05")

    def test_warns_when_latest_period_is_missing(self):
        result = CampaignCopilot().review(load_campaign(SAMPLE))
        warning = next(
            item for item in result["trend_review"]["warnings"]
            if item["cell_id"] == "CELL-MARKETPLACE-D"
        )
        self.assertEqual(warning["code"], "latest_period_missing")
        self.assertEqual(warning["latest_available_period"], "2026-06")

    def test_warns_when_no_prior_period_exists(self):
        result = CampaignCopilot().review(load_campaign(SAMPLE))
        warning = next(
            item for item in result["trend_review"]["warnings"]
            if item["cell_id"] == "CELL-SOCIAL-C"
        )
        self.assertEqual(warning["code"], "no_prior_period")

    def test_warns_when_comparison_dimensions_changed(self):
        payload = sample_payload()
        payload["performance_history"][0]["creative_id"] = "CR-VIDEO-02"
        result = CampaignCopilot().review(CampaignBrief.from_mapping(payload))
        warning = next(
            item for item in result["trend_review"]["warnings"]
            if item["cell_id"] == "CELL-SEARCH-A"
        )
        self.assertEqual(warning["code"], "incompatible_dimensions")

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

    def test_rejects_invalid_reporting_period(self):
        payload = sample_payload()
        payload["reporting_period"] = "2026-13"
        with self.assertRaisesRegex(ValueError, "YYYY-MM"):
            CampaignBrief.from_mapping(payload)

    def test_rejects_current_observation_outside_reporting_period(self):
        payload = sample_payload()
        payload["performance"][0]["period"] = "2026-06"
        with self.assertRaisesRegex(ValueError, "match reporting_period"):
            CampaignBrief.from_mapping(payload)

    def test_rejects_history_at_or_after_reporting_period(self):
        payload = sample_payload()
        payload["performance_history"][0]["period"] = "2026-07"
        with self.assertRaisesRegex(ValueError, "earlier than reporting_period"):
            CampaignBrief.from_mapping(payload)

    def test_rejects_duplicate_cell_period_observation(self):
        payload = sample_payload()
        duplicate = dict(payload["performance_history"][0])
        duplicate["source_id"] = "PERF-2026-DUPLICATE"
        payload["performance_history"].append(duplicate)
        with self.assertRaisesRegex(ValueError, "cell_id and period"):
            CampaignBrief.from_mapping(payload)

    def test_markdown_contains_metric_sources_and_governance(self):
        markdown = render_markdown(CampaignCopilot().review(load_campaign(SAMPLE)))
        self.assertIn("[PERF-2026-001]", markdown)
        self.assertIn("Platform write executed: no", markdown)
        self.assertIn("All inputs and performance values are synthetic", markdown)
        self.assertIn("Comparable period changes", markdown)
        self.assertIn("latest_period_missing", markdown)


if __name__ == "__main__":
    unittest.main()
