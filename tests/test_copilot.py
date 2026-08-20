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
        self.assertEqual(action["objective_policy_id"], "OBJ-REV-001")
        self.assertEqual(action["policy_score"]["score"], 100)

    def test_revenue_policy_uses_roas_and_cpa(self):
        payload = sample_payload()
        payload["target_roas"] = 99
        result = CampaignCopilot().review(CampaignBrief.from_mapping(payload))
        action = next(item for item in result["optimization_recommendations"] if item["cell_id"] == "CELL-SEARCH-A")
        self.assertEqual(result["objective_policy"]["policy_id"], "OBJ-REV-001")
        self.assertEqual(action["policy_score"]["score"], 40)
        self.assertEqual(action["action"], "hold_and_test")

    def test_conversion_policy_does_not_treat_roas_as_scale_factor(self):
        payload = sample_payload()
        payload.update({"objective": "conversions", "outcome_type": "conversion", "target_roas": 99})
        result = CampaignCopilot().review(CampaignBrief.from_mapping(payload))
        action = next(item for item in result["optimization_recommendations"] if item["cell_id"] == "CELL-SEARCH-A")
        self.assertEqual(result["objective_policy"]["policy_id"], "OBJ-CONV-001")
        self.assertEqual(action["policy_score"]["score"], 100)
        self.assertEqual(action["action"], "candidate_scale")

    def test_lead_policy_requires_qualified_lead_semantics(self):
        payload = sample_payload()
        payload.update({"objective": "leads", "outcome_type": "qualified_lead", "target_roas": 99})
        result = CampaignCopilot().review(CampaignBrief.from_mapping(payload))
        action = next(item for item in result["optimization_recommendations"] if item["cell_id"] == "CELL-SEARCH-A")
        self.assertEqual(result["objective_policy"]["policy_id"], "OBJ-LEAD-001")
        self.assertEqual(action["action"], "candidate_scale")

    def test_rejects_objective_outcome_semantic_mismatch(self):
        payload = sample_payload()
        payload["objective"] = "leads"
        with self.assertRaisesRegex(ValueError, "requires outcome_type qualified_lead"):
            CampaignBrief.from_mapping(payload)

    def test_objective_policy_decision_is_deterministic(self):
        campaign = load_campaign(SAMPLE)
        first = CampaignCopilot().review(campaign)
        second = CampaignCopilot().review(campaign)
        self.assertEqual(first["objective_policy"], second["objective_policy"])
        self.assertEqual(first["optimization_recommendations"], second["optimization_recommendations"])

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

    def test_structured_performance_guarantee_has_policy_evidence(self):
        payload = sample_payload()
        payload["creatives"][0]["claims"][0].update({
            "category": "performance_guarantee",
            "text": "Guaranteed results for every campaign.",
            "evidence_ids": [],
        })
        result = CampaignCopilot().review(CampaignBrief.from_mapping(payload))
        violation = result["creative_review"]["violations"][0]
        self.assertEqual(violation["category"], "performance_guarantee")
        self.assertIn("GOOGLE-UNRELIABLE-CLAIMS", violation["policy_ids"])
        self.assertTrue(result["creative_review"]["policy_references"])

    def test_high_risk_phrase_overrides_misdeclared_descriptive_category(self):
        payload = sample_payload()
        payload["creatives"][0]["claims"][0].update({
            "category": "descriptive",
            "text": "We guarantee results for every campaign.",
            "evidence_ids": [],
        })
        result = CampaignCopilot().review(CampaignBrief.from_mapping(payload))
        violation = result["creative_review"]["violations"][0]
        self.assertEqual(violation["declared_category"], "descriptive")
        self.assertEqual(violation["category"], "performance_guarantee")
        self.assertTrue(violation["category_override_applied"])
        self.assertEqual(violation["matched_rule_id"], "CLAIM-PERFORMANCE-GUARANTEE")
        self.assertEqual(result["optimization_recommendations"], [])

    def test_reverse_order_guarantee_pattern_is_blocked(self):
        payload = sample_payload()
        payload["creatives"][0]["claims"][0].update({
            "category": "descriptive",
            "text": "Successful outcomes are fully guaranteed.",
            "evidence_ids": [],
        })
        result = CampaignCopilot().review(CampaignBrief.from_mapping(payload))
        self.assertTrue(result["creative_review"]["release_blocked"])
        self.assertEqual(result["creative_review"]["violations"][0]["category"], "performance_guarantee")

    def test_long_guarantee_grammar_cannot_bypass_category_override(self):
        variants = (
            "We guarantee you will see dramatically better results.",
            "We guarantee every single customer will get results.",
        )
        for text in variants:
            with self.subTest(text=text):
                payload = sample_payload()
                payload["creatives"][0]["claims"][0].update({
                    "category": "descriptive",
                    "text": text,
                    "evidence_ids": [],
                })
                result = CampaignCopilot().review(CampaignBrief.from_mapping(payload))
                violation = result["creative_review"]["violations"][0]
                self.assertTrue(result["creative_review"]["release_blocked"])
                self.assertEqual(violation["matched_rule_id"], "CLAIM-PERFORMANCE-GUARANTEE")
                self.assertEqual(result["optimization_recommendations"], [])

    def test_performance_promise_variants_cannot_bypass_category_override(self):
        variants = (
            "We promise sales will double.",
            "We assure every advertiser of improved results.",
            "Revenue will double after this campaign.",
            "Higher conversion results are promised.",
            "We commit to doubling your sales.",
            "Your sales are certain to double.",
            "You will get twice as many sales.",
            "We ensure that your revenue doubles.",
            "Double your revenue, no matter what.",
            "Revenue doubles every time.",
            "Sales always double.",
            "Your returns are sure to rise.",
            "Qualified leads are certain to double.",
            "Leads will double.",
            "Website traffic will double.",
            "Clicks will triple.",
            "CTR will increase.",
            "CVR is certain to improve.",
            "CPA will fall by half.",
            "CPC always falls.",
            "Reach will double.",
            "Impressions will triple.",
            "Engagement is sure to rise.",
            "ROAS cannot fail to improve.",
            "Revenue is bound to rise.",
            "Sales are destined to grow.",
            "CPA will decrease.",
            "CTR will climb.",
            "Clicks will soar.",
            "Traffic will surge.",
            "Profit will jump.",
            "Conversions will be higher.",
            "We ensure higher sales.",
            "We commit to higher revenue.",
            "Sales are certain to surge.",
            "Revenue is set to double.",
            "ROAS is destined to climb.",
            "Leads must double.",
            "Sales are going to double.",
            "Traffic cannot decrease.",
        )
        for text in variants:
            with self.subTest(text=text):
                payload = sample_payload()
                payload["creatives"][0]["claims"][0].update({
                    "category": "descriptive", "text": text, "evidence_ids": [],
                })
                result = CampaignCopilot().review(CampaignBrief.from_mapping(payload))
                violation = result["creative_review"]["violations"][0]
                self.assertTrue(result["creative_review"]["release_blocked"])
                self.assertEqual(violation["matched_rule_id"], "CLAIM-PERFORMANCE-GUARANTEE")
                self.assertEqual(result["optimization_recommendations"], [])

    def test_ordinary_descriptive_claim_does_not_trigger_performance_structure(self):
        variants = (
            "The gift box contains three tea tins for regional customers.",
            "We are committed to customer support.",
            "Customers always see the listed package contents.",
        )
        for text in variants:
            with self.subTest(text=text):
                payload = sample_payload()
                payload["claim_evidence"][0]["supported_texts"].append(text)
                payload["creatives"][0]["claims"][0].update({
                    "category": "descriptive", "text": text, "evidence_ids": ["SPEC-SYNTH-001"],
                })
                result = CampaignCopilot().review(CampaignBrief.from_mapping(payload))
                decision = result["creative_review"]["decisions"][0]
                self.assertEqual(decision["decision"], "allowed_for_human_review")
                self.assertIsNone(decision["matched_rule_id"])

    def test_descriptive_text_binding_is_exact_and_fails_closed_after_edit(self):
        payload = sample_payload()
        claim = payload["creatives"][1]["claims"][0]
        self.assertEqual(claim["evidence_ids"], ["SPEC-SYNTH-001"])
        allowed = CampaignCopilot().review(CampaignBrief.from_mapping(payload))
        allowed_claim = next(
            item for item in allowed["creative_review"]["decisions"]
            if item["claim_id"] == claim["claim_id"]
        )
        self.assertEqual(allowed_claim["decision"], "allowed_for_human_review")

        claim["text"] = "The concept focuses on packaging and guaranteed CAC reduction."
        blocked = CampaignCopilot().review(CampaignBrief.from_mapping(payload))
        blocked_claim = next(
            item for item in blocked["creative_review"]["violations"]
            if item["claim_id"] == claim["claim_id"]
        )
        self.assertEqual(blocked_claim["decision"], "blocked")
        self.assertEqual(blocked["optimization_recommendations"], [])

    def test_unregistered_headline_or_message_fails_closed(self):
        for field, text in (
            ("headline", "CAC will fall."),
            ("message", "Brand awareness will double."),
        ):
            with self.subTest(field=field):
                payload = sample_payload()
                payload["creatives"][0][field] = text
                result = CampaignCopilot().review(CampaignBrief.from_mapping(payload))
                violation = next(
                    item for item in result["creative_review"]["violations"]
                    if item["claim_id"] is None and item["claim"] == text
                )
                self.assertTrue(result["creative_review"]["release_blocked"])
                self.assertEqual(result["optimization_recommendations"], [])
                self.assertIn(violation["matched_rule_id"], {
                    "CLAIM-PERFORMANCE-METRIC-FAILSAFE",
                    "CLAIM-PERFORMANCE-GUARANTEE",
                    "CLAIM-UNREGISTERED-CREATIVE-SURFACE",
                })

    def test_unregistered_performance_vocabulary_fails_closed_across_surfaces(self):
        variants = (
            "CAC will fall.",
            "LTV will double.",
            "AOV will rise.",
            "Brand awareness will double.",
            "Customer base will triple.",
            "Churn will halve.",
            "Bounce rate will drop.",
            "Store visits will double.",
            "App activations will triple.",
            "Purchase frequency will rise.",
            "Pipeline value will double.",
        )
        for text in variants:
            for surface in ("claim", "headline", "message"):
                with self.subTest(text=text, surface=surface):
                    payload = sample_payload()
                    if surface == "claim":
                        payload["creatives"][0]["claims"][0].update({
                            "category": "descriptive", "text": text, "evidence_ids": [],
                        })
                    else:
                        payload["creatives"][0][surface] = text
                    result = CampaignCopilot().review(CampaignBrief.from_mapping(payload))
                    self.assertTrue(result["creative_review"]["release_blocked"])
                    self.assertEqual(result["optimization_recommendations"], [])

    def test_performance_metric_descriptions_fail_safe_even_in_governance_context(self):
        variants = (
            "The report shows revenue. Human reviewers always approve budget changes.",
            "Customers can order twice per month.",
            "We promise revenue reports are delivered every Monday.",
            "We pledge transparent reporting of campaign performance.",
            "We promise results are reviewed by a person.",
            "Revenue will increase or decrease depending on evidence.",
            "Clicks will increase in the simulation if input changes.",
            "Sales will increase only if a human approves the change.",
        )
        for text in variants:
            with self.subTest(text=text):
                payload = sample_payload()
                payload["creatives"][0]["claims"][0].update({
                    "category": "descriptive", "text": text, "evidence_ids": [],
                })
                result = CampaignCopilot().review(CampaignBrief.from_mapping(payload))
                decision = result["creative_review"]["violations"][0]
                self.assertTrue(result["creative_review"]["release_blocked"])
                self.assertIn(decision["matched_rule_id"], {
                    "CLAIM-PERFORMANCE-GUARANTEE", "CLAIM-PERFORMANCE-METRIC-FAILSAFE",
                })
                self.assertEqual(result["optimization_recommendations"], [])

    def test_supported_metric_claims_fail_safe_when_open_ended_language_changes(self):
        variants = (
            "Revenue will surpass the baseline.",
            "Sales will beat last month.",
            "CPA will go down.",
            "Traffic will go up.",
            "Profit will be greater.",
            "Orders are certain to multiply.",
            "Sales are certain to explode.",
            "Engagement will peak.",
            "Clicks cannot go down.",
            "We ensure more conversions.",
            "Revenue will overtake the baseline.",
        )
        for text in variants:
            with self.subTest(text=text):
                payload = sample_payload()
                payload["creatives"][0]["claims"][0].update({
                    "category": "descriptive", "text": text, "evidence_ids": [],
                })
                result = CampaignCopilot().review(CampaignBrief.from_mapping(payload))
                violation = result["creative_review"]["violations"][0]
                self.assertTrue(result["creative_review"]["release_blocked"])
                self.assertIn(violation["matched_rule_id"], {
                    "CLAIM-PERFORMANCE-GUARANTEE", "CLAIM-PERFORMANCE-METRIC-FAILSAFE",
                })
                self.assertEqual(result["optimization_recommendations"], [])

    def test_objective_claim_requires_declared_substantiation(self):
        payload = sample_payload()
        payload["creatives"][0]["claims"][0]["evidence_ids"] = []
        result = CampaignCopilot().review(CampaignBrief.from_mapping(payload))
        violation = result["creative_review"]["violations"][0]
        self.assertEqual(violation["category"], "objective_product_claim")
        self.assertIn("require a declared substantiation", violation["reason"])

    def test_substantiated_objective_claim_reaches_human_review(self):
        result = CampaignCopilot().review(load_campaign(SAMPLE))
        decision = next(
            item for item in result["creative_review"]["decisions"]
            if item["claim_id"] == "CLAIM-001"
        )
        self.assertEqual(decision["decision"], "allowed_for_human_review")
        self.assertEqual(decision["substantiation_ids"], ["SPEC-SYNTH-001"])

    def test_rejects_unknown_claim_evidence_reference(self):
        payload = sample_payload()
        payload["creatives"][0]["claims"][0]["evidence_ids"] = ["UNKNOWN"]
        with self.assertRaisesRegex(ValueError, "declared claim_evidence"):
            CampaignBrief.from_mapping(payload)

    def test_health_claim_is_blocked_even_with_product_substantiation(self):
        payload = sample_payload()
        payload["creatives"][0]["claims"][0]["category"] = "health_outcome"
        result = CampaignCopilot().review(CampaignBrief.from_mapping(payload))
        violation = result["creative_review"]["violations"][0]
        self.assertEqual(violation["decision"], "blocked")
        self.assertEqual(violation["policy_ids"], ["FTC-HEALTH-CLAIMS"])

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

    def test_rejects_non_finite_and_boolean_numeric_inputs(self):
        for field in ("total_budget", "target_roas", "target_cpa", "max_reallocation_pct"):
            for invalid in ("NaN", "Infinity", "-Infinity", True):
                with self.subTest(field=field, value=invalid):
                    payload = sample_payload()
                    payload[field] = invalid
                    with self.assertRaisesRegex(ValueError, "finite number"):
                        CampaignBrief.from_mapping(payload)

        for field in ("spend", "revenue"):
            for invalid in ("NaN", "Infinity", "-Infinity", True):
                with self.subTest(field=field, value=invalid):
                    payload = sample_payload()
                    payload["performance"][0][field] = invalid
                    with self.assertRaisesRegex(ValueError, "finite number"):
                        CampaignBrief.from_mapping(payload)

    def test_rejects_boolean_fractional_and_non_finite_funnel_counts(self):
        for invalid in (True, 3.5, "NaN", "Infinity"):
            with self.subTest(value=invalid):
                payload = sample_payload()
                payload["performance"][0]["clicks"] = invalid
                with self.assertRaisesRegex(ValueError, "finite number|non-negative integer"):
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
        self.assertIn("OBJ-REV-001", markdown)
        self.assertIn("Policy score 100/100", markdown)
        self.assertIn("FTC-AD-SUBSTANTIATION", markdown)
        self.assertIn("SPEC-SYNTH-001", markdown)


if __name__ == "__main__":
    unittest.main()
