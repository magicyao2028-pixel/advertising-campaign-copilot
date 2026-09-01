from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any


_STATUSES = {"accepted", "deferred", "rejected"}
_ACTIONS = {"pause_and_review", "hold_and_test", "candidate_scale"}


def summarize_experiment_review_history(
    review_export: dict[str, Any], history: list[dict[str, Any]]
) -> dict[str, Any]:
    """Summarize bounded human review feedback without applying any decision."""
    campaign_id = str(review_export.get("campaign_id", "")).strip()
    items = review_export.get("items")
    if not campaign_id or not isinstance(items, list) or not items:
        raise ValueError("Review export must contain a campaign and items")
    if review_export.get("approval_applied") is not False:
        raise ValueError("Review export must keep approvals unapplied")
    if review_export.get("platform_writes_executed") != 0 or review_export.get("external_actions_executed") != 0:
        raise ValueError("Review export must remain non-executing")
    if not isinstance(history, list) or not history:
        raise ValueError("Review history must contain entries")

    export_cells = {str(item.get("cell_id", "")).strip(): item for item in items if isinstance(item, dict)}
    if not export_cells or any(not cell_id for cell_id in export_cells):
        raise ValueError("Review export items must have cell IDs")
    seen_ids: set[str] = set()
    parsed_dates: list[date] = []
    statuses: Counter[str] = Counter()
    actions: Counter[str] = Counter()
    for entry in history:
        if not isinstance(entry, dict):
            raise ValueError("Every review-history entry must be an object")
        required = {"review_id", "campaign_id", "cell_id", "reviewed_on", "action", "status", "note", "approval_applied"}
        if required.difference(entry):
            raise ValueError("Review-history entry is incomplete")
        review_id = str(entry["review_id"]).strip()
        if not review_id or review_id in seen_ids:
            raise ValueError("Review-history IDs must be unique")
        seen_ids.add(review_id)
        if str(entry["campaign_id"]).strip() != campaign_id:
            raise ValueError("Review-history campaign does not match export")
        cell_id = str(entry["cell_id"]).strip()
        if cell_id not in export_cells:
            raise ValueError("Review-history cell does not exist in export")
        try:
            reviewed_on = date.fromisoformat(str(entry["reviewed_on"]))
        except ValueError as exc:
            raise ValueError("Review-history date must be ISO format") from exc
        if parsed_dates and reviewed_on < parsed_dates[-1]:
            raise ValueError("Review-history dates must be chronological")
        parsed_dates.append(reviewed_on)
        action = str(entry["action"]).strip()
        if action not in _ACTIONS or action != export_cells[cell_id].get("action"):
            raise ValueError("Review-history action does not match export")
        status = str(entry["status"]).strip()
        if status not in _STATUSES or not str(entry["note"]).strip():
            raise ValueError("Review-history status or note is invalid")
        if entry["approval_applied"] is not False:
            raise ValueError("Review-history entries cannot apply approvals")
        statuses[status] += 1
        actions[action] += 1

    return {
        "schema_version": "1.0",
        "entry_count": len(history),
        "status_counts": dict(sorted(statuses.items())),
        "action_counts": dict(sorted(actions.items())),
        "latest_reviewed_on": parsed_dates[-1].isoformat(),
        "approval_applied": False,
        "platform_writes_executed": 0,
        "external_actions_executed": 0,
        "boundary": "Review history records synthetic human-review outcomes for learning; it does not change budgets, launch experiments or publish creatives.",
    }
