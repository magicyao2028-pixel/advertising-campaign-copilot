from __future__ import annotations

from typing import Any

from .models import CampaignBrief, Creative, PerformanceCell


PROHIBITED_PHRASES = {
    "guaranteed results",
    "100% risk-free",
    "instant cure",
    "no exceptions",
}


class CampaignCopilot:
    """Builds a deterministic campaign review with bounded optimization advice."""

    def review(self, campaign: CampaignBrief) -> dict[str, Any]:
        violations = self._creative_violations(campaign.creatives)
        envelopes = self._budget_envelopes(campaign)
        cells = [self._evaluate_cell(cell, campaign) for cell in campaign.performance]
        status = "blocked_claim_review" if violations else "ready_for_human_review"
        recommendations = [] if violations else [self._recommendation(cell, campaign) for cell in cells]
        return {
            "campaign_id": campaign.campaign_id,
            "status": status,
            "objective": campaign.objective,
            "planning": {
                "product": campaign.product,
                "audience": campaign.audience,
                "channels": list(campaign.channels),
                "currency": campaign.currency,
                "total_budget": campaign.total_budget,
                "budget_envelopes": envelopes,
                "experiment_rule": "Change one primary variable per cell before interpreting uplift.",
            },
            "creative_review": {
                "release_blocked": bool(violations),
                "violations": violations,
            },
            "performance_review": cells,
            "optimization_recommendations": recommendations,
            "constraints": list(campaign.constraints),
            "governance": {
                "human_owner": campaign.human_owner,
                "human_approval_required": True,
                "platform_write_executed": False,
                "max_reallocation_pct": campaign.max_reallocation_pct,
            },
            "trace": [
                {"step": "validate_brief", "status": "completed"},
                {"step": "review_creative_claims", "status": "blocked" if violations else "completed"},
                {"step": "calculate_performance", "status": "completed"},
                {"step": "draft_optimization", "status": "skipped" if violations else "completed"},
                {"step": "request_human_approval", "status": "required"},
            ],
            "limitations": [
                "All campaign and performance values are synthetic.",
                "Rules are illustrative and do not replace platform policy or statistical review.",
                "No ad-platform connection, budget change or creative publication is implemented.",
            ],
        }

    @staticmethod
    def _budget_envelopes(campaign: CampaignBrief) -> list[dict[str, Any]]:
        count = len(campaign.performance)
        cents = round(campaign.total_budget * 100)
        base, remainder = divmod(cents, count)
        return [
            {
                "cell_id": cell.cell_id,
                "channel": cell.channel,
                "planned_budget": (base + (1 if index < remainder else 0)) / 100,
            }
            for index, cell in enumerate(campaign.performance)
        ]

    @staticmethod
    def _creative_violations(creatives: tuple[Creative, ...]) -> list[dict[str, str]]:
        violations = []
        for creative in creatives:
            text = f"{creative.headline} {creative.message}".casefold()
            for phrase in sorted(PROHIBITED_PHRASES):
                if phrase in text:
                    violations.append({"creative_id": creative.creative_id, "phrase": phrase})
        return violations

    @staticmethod
    def _evaluate_cell(cell: PerformanceCell, campaign: CampaignBrief) -> dict[str, Any]:
        ctr = cell.clicks / cell.impressions if cell.impressions else 0.0
        conversion_rate = cell.conversions / cell.clicks if cell.clicks else 0.0
        cpa = cell.spend / cell.conversions if cell.conversions else None
        roas = cell.revenue / cell.spend if cell.spend else 0.0
        return {
            "cell_id": cell.cell_id,
            "channel": cell.channel,
            "creative_id": cell.creative_id,
            "source_id": cell.source_id,
            "spend": cell.spend,
            "impressions": cell.impressions,
            "clicks": cell.clicks,
            "conversions": cell.conversions,
            "revenue": cell.revenue,
            "ctr": round(ctr, 4),
            "conversion_rate": round(conversion_rate, 4),
            "cpa": round(cpa, 2) if cpa is not None else None,
            "roas": round(roas, 2),
            "target_cpa": campaign.target_cpa,
            "target_roas": campaign.target_roas,
        }

    @staticmethod
    def _recommendation(cell: dict[str, Any], campaign: CampaignBrief) -> dict[str, Any]:
        minimum_review_spend = campaign.total_budget * 0.10
        if cell["conversions"] == 0 and cell["spend"] >= minimum_review_spend:
            action = "pause_and_review"
            reason = "No conversions after the minimum review-spend threshold."
            change = 0.0
        elif (
            cell["cpa"] is not None
            and cell["roas"] >= campaign.target_roas
            and cell["cpa"] <= campaign.target_cpa
        ):
            action = "candidate_scale"
            reason = "ROAS and CPA both meet the declared targets."
            change = min(15.0, campaign.max_reallocation_pct)
        else:
            action = "hold_and_test"
            reason = "The cell does not yet meet both optimization targets."
            change = 0.0
        return {
            "cell_id": cell["cell_id"],
            "action": action,
            "reason": reason,
            "recommended_budget_change_pct": change,
            "evidence_ids": [cell["source_id"]],
            "requires_human_approval": True,
            "executed": False,
        }
