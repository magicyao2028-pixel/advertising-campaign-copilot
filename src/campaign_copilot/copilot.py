from __future__ import annotations

from typing import Any

from .claim_policies import review_creative_claims
from .models import CampaignBrief, PerformanceCell, period_index
from .objective_policies import get_objective_policy, score_cell


class CampaignCopilot:
    """Builds a deterministic campaign review with bounded optimization advice."""

    def review(self, campaign: CampaignBrief) -> dict[str, Any]:
        creative_review = review_creative_claims(campaign.creatives, campaign.claim_evidence)
        violations = creative_review["violations"]
        envelopes = self._budget_envelopes(campaign)
        cells = [self._evaluate_cell(cell, campaign) for cell in campaign.performance]
        trend_review = self._trend_review(campaign)
        objective_policy = get_objective_policy(campaign.objective)
        status = "blocked_claim_review" if violations else "ready_for_human_review"
        recommendations = [] if violations else [
            self._recommendation(cell, campaign, objective_policy) for cell in cells
        ]
        return {
            "campaign_id": campaign.campaign_id,
            "status": status,
            "objective": campaign.objective,
            "outcome_type": campaign.outcome_type,
            "objective_policy": objective_policy.to_dict(),
            "planning": {
                "product": campaign.product,
                "audience": campaign.audience,
                "channels": list(campaign.channels),
                "currency": campaign.currency,
                "total_budget": campaign.total_budget,
                "budget_envelopes": envelopes,
                "experiment_rule": "Change one primary variable per cell before interpreting uplift.",
            },
            "creative_review": creative_review,
            "performance_review": cells,
            "trend_review": trend_review,
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
                {"step": "select_objective_policy", "status": objective_policy.policy_id},
                {
                    "step": "compare_periods",
                    "status": "warnings_present" if trend_review["warnings"] else "completed",
                },
                {"step": "draft_optimization", "status": "skipped" if violations else "completed"},
                {"step": "request_human_approval", "status": "required"},
            ],
            "limitations": [
                "All campaign and performance values are synthetic.",
                "Rules are illustrative and do not replace platform policy or statistical review.",
                "Period changes are descriptive and do not establish causality or forecast results.",
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
    def _evaluate_cell(cell: PerformanceCell, campaign: CampaignBrief) -> dict[str, Any]:
        ctr = cell.clicks / cell.impressions if cell.impressions else 0.0
        conversion_rate = cell.conversions / cell.clicks if cell.clicks else 0.0
        cpa = cell.spend / cell.conversions if cell.conversions else None
        roas = cell.revenue / cell.spend if cell.spend else 0.0
        return {
            "cell_id": cell.cell_id,
            "period": cell.period,
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

    def _trend_review(self, campaign: CampaignBrief) -> dict[str, Any]:
        current_by_id = {cell.cell_id: cell for cell in campaign.performance}
        history_by_id: dict[str, list[PerformanceCell]] = {}
        for cell in campaign.performance_history:
            history_by_id.setdefault(cell.cell_id, []).append(cell)
        for cells in history_by_id.values():
            cells.sort(key=lambda item: period_index(item.period))

        comparable: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        for cell_id in sorted(set(current_by_id) | set(history_by_id)):
            current = current_by_id.get(cell_id)
            history = history_by_id.get(cell_id, [])
            if current is None:
                warnings.append({
                    "cell_id": cell_id,
                    "code": "latest_period_missing",
                    "message": f"No observation exists for reporting period {campaign.reporting_period}.",
                    "latest_available_period": history[-1].period,
                    "evidence_ids": [history[-1].source_id],
                })
                continue
            if not history:
                warnings.append({
                    "cell_id": cell_id,
                    "code": "no_prior_period",
                    "message": "No earlier observation is available for comparison.",
                    "latest_available_period": current.period,
                    "evidence_ids": [current.source_id],
                })
                continue
            previous = history[-1]
            if current.channel != previous.channel or current.creative_id != previous.creative_id:
                warnings.append({
                    "cell_id": cell_id,
                    "code": "incompatible_dimensions",
                    "message": "Channel or creative changed, so the observations are not directly comparable.",
                    "latest_available_period": current.period,
                    "comparison_period": previous.period,
                    "evidence_ids": [previous.source_id, current.source_id],
                })
                continue
            if period_index(current.period) - period_index(previous.period) != 1:
                warnings.append({
                    "cell_id": cell_id,
                    "code": "non_adjacent_periods",
                    "message": "The latest available history is not the immediately preceding month.",
                    "latest_available_period": current.period,
                    "comparison_period": previous.period,
                    "evidence_ids": [previous.source_id, current.source_id],
                })
                continue
            current_metrics = self._evaluate_cell(current, campaign)
            previous_metrics = self._evaluate_cell(previous, campaign)
            comparable.append({
                "cell_id": cell_id,
                "current_period": current.period,
                "comparison_period": previous.period,
                "evidence_ids": [previous.source_id, current.source_id],
                "changes": {
                    "spend_pct": _percent_change(current.spend, previous.spend),
                    "ctr_percentage_points": round(
                        (current_metrics["ctr"] - previous_metrics["ctr"]) * 100, 2
                    ),
                    "conversion_rate_percentage_points": round(
                        (current_metrics["conversion_rate"] - previous_metrics["conversion_rate"]) * 100,
                        2,
                    ),
                    "cpa_pct": _percent_change(current_metrics["cpa"], previous_metrics["cpa"]),
                    "roas_pct": _percent_change(current_metrics["roas"], previous_metrics["roas"]),
                },
            })
        return {
            "reporting_period": campaign.reporting_period,
            "status": "warnings_present" if warnings else "comparable_history_available",
            "comparable": comparable,
            "warnings": warnings,
        }

    @staticmethod
    def _recommendation(cell: dict[str, Any], campaign: CampaignBrief, policy: Any) -> dict[str, Any]:
        minimum_review_spend = campaign.total_budget * 0.10
        policy_score = score_cell(cell, policy)
        if cell["conversions"] == 0 and cell["spend"] >= minimum_review_spend:
            action = "pause_and_review"
            reason = "No conversions after the minimum review-spend threshold."
            change = 0.0
        elif policy_score["score"] >= policy_score["scale_score"]:
            action = "candidate_scale"
            reason = f"All weighted factors in {policy.policy_id} meet the declared thresholds."
            change = min(15.0, campaign.max_reallocation_pct)
        else:
            action = "hold_and_test"
            reason = f"The cell does not meet every scale factor in {policy.policy_id}."
            change = 0.0
        return {
            "cell_id": cell["cell_id"],
            "action": action,
            "reason": reason,
            "objective": campaign.objective,
            "objective_policy_id": policy.policy_id,
            "policy_score": policy_score,
            "recommended_budget_change_pct": change,
            "evidence_ids": [cell["source_id"]],
            "requires_human_approval": True,
            "executed": False,
        }


def _percent_change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return round((current - previous) / previous * 100, 2)
