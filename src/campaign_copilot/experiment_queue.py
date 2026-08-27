from __future__ import annotations

from typing import Any


_PRIORITY = {"pause_and_review": 0, "hold_and_test": 1, "candidate_scale": 2}
_NEXT_ACTION = {
    "pause_and_review": "escalate_to_campaign_owner",
    "hold_and_test": "collect_minimum_sample_before_scale_decision",
    "candidate_scale": "obtain_human_approval_and_monitor_one_variable",
}


def build_experiment_queue(review: dict[str, Any]) -> dict[str, Any]:
    """Convert bounded recommendations into a reviewable, non-executing work queue."""
    recommendations = review.get("optimization_recommendations")
    if not isinstance(recommendations, list) or not recommendations:
        raise ValueError("Campaign review must contain optimization recommendations")
    items: list[dict[str, Any]] = []
    for recommendation in recommendations:
        if not isinstance(recommendation, dict):
            raise ValueError("Every recommendation must be an object")
        action = str(recommendation.get("action", "")).strip()
        if action not in _NEXT_ACTION:
            raise ValueError(f"Unsupported recommendation action: {action}")
        items.append(
            {
                "cell_id": recommendation.get("cell_id"),
                "priority": "critical" if _PRIORITY[action] == 0 else "high" if _PRIORITY[action] == 1 else "normal",
                "action": action,
                "next_action": _NEXT_ACTION[action],
                "evidence_ids": list(recommendation.get("evidence_ids", [])),
                "requires_human_approval": True,
                "executed": False,
            }
        )
    items.sort(key=lambda item: (_PRIORITY[item["action"]], str(item["cell_id"])))
    return {
        "schema_version": "1.0",
        "queue_type": "campaign experiment review queue",
        "campaign_id": review.get("campaign_id"),
        "items": items,
        "platform_writes_executed": 0,
        "external_actions_executed": 0,
        "human_approval_required": True,
        "boundary": "This queue prioritizes review work only; it does not change budgets, launch experiments or publish creatives.",
    }
