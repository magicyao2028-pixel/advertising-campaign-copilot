from __future__ import annotations

from typing import Any


_CHECKLISTS = {
    "pause_and_review": ("blocked", "campaign owner confirms pause rationale and safety review"),
    "hold_and_test": ("pending", "minimum sample thresholds are met and one controlled variable is selected"),
    "candidate_scale": ("pending", "human approval is recorded and one-variable monitoring is scheduled"),
}


def build_experiment_review_export(review: dict[str, Any], queue: dict[str, Any]) -> dict[str, Any]:
    """Expose bounded experiment-review checklists without changing campaign state."""
    if queue.get("campaign_id") != review.get("campaign_id"):
        raise ValueError("Experiment queue does not match campaign review")
    if queue.get("platform_writes_executed") != 0 or queue.get("external_actions_executed") != 0:
        raise ValueError("Experiment queue must remain non-executing")
    items: list[dict[str, Any]] = []
    for item in queue.get("items", []):
        action = item.get("action")
        checklist = _CHECKLISTS.get(action)
        if checklist is None:
            raise ValueError("Unsupported experiment action")
        status, completion_criteria = checklist
        items.append(
            {
                "cell_id": item.get("cell_id"),
                "priority": item.get("priority"),
                "action": action,
                "status": status,
                "completion_criteria": completion_criteria,
                "evidence_ids": sorted(set(item.get("evidence_ids", []))),
                "requires_human_approval": True,
                "executed": False,
            }
        )
    items.sort(key=lambda row: (row["priority"] != "critical", str(row["cell_id"])))
    return {
        "schema_version": "1.0",
        "export_version": "0.7",
        "campaign_id": review.get("campaign_id"),
        "items": items,
        "item_count": len(items),
        "platform_writes_executed": 0,
        "external_actions_executed": 0,
        "approval_applied": False,
        "boundary": "This export makes experiment-review completion criteria visible; it does not change budgets, launch experiments or publish creatives.",
    }
