from __future__ import annotations

from datetime import date, timedelta
from typing import Any


_REVIEW_STATUSES = {"accepted", "deferred", "rejected"}
_OPEN_STATUSES = {"deferred"}
_ACTIONS = {"pause_and_review", "hold_and_test", "candidate_scale"}


def reconcile_campaign_review_feedback(
    review_export: dict[str, Any],
    review_history: list[dict[str, Any]],
    feedback_replay: dict[str, Any],
    *,
    as_of_date: str,
    stale_after_days: int = 30,
) -> dict[str, Any]:
    """Reconcile accepted feedback and surface stale reviews without campaign writes."""
    if isinstance(stale_after_days, bool) or not isinstance(stale_after_days, int) or stale_after_days < 1:
        raise ValueError("stale_after_days must be a positive integer")
    try:
        as_of = date.fromisoformat(as_of_date)
    except (TypeError, ValueError) as exc:
        raise ValueError("as_of_date must be ISO format") from exc

    campaign_id = str(review_export.get("campaign_id", "")).strip() if isinstance(review_export, dict) else ""
    export_items = review_export.get("items") if isinstance(review_export, dict) else None
    if not campaign_id or not isinstance(export_items, list) or not export_items:
        raise ValueError("review export must contain a campaign and items")
    if (
        review_export.get("approval_applied") is not False
        or review_export.get("platform_writes_executed") != 0
        or review_export.get("external_actions_executed") != 0
    ):
        raise ValueError("review export must remain non-executing")

    export_cells: dict[str, str] = {}
    for item in export_items:
        cell_id = str(item.get("cell_id", "")).strip() if isinstance(item, dict) else ""
        action = str(item.get("action", "")).strip() if isinstance(item, dict) else ""
        if not cell_id or cell_id in export_cells or action not in _ACTIONS:
            raise ValueError("review export cells must be unique and actionable")
        export_cells[cell_id] = action

    if not isinstance(review_history, list) or not review_history:
        raise ValueError("review history must contain entries")
    reviews: dict[str, dict[str, Any]] = {}
    for entry in review_history:
        if not isinstance(entry, dict):
            raise ValueError("review-history entries must be objects")
        review_id = str(entry.get("review_id", "")).strip()
        cell_id = str(entry.get("cell_id", "")).strip()
        action = str(entry.get("action", "")).strip()
        status = str(entry.get("status", "")).strip()
        if not review_id or review_id in reviews:
            raise ValueError("review-history IDs must be unique")
        if str(entry.get("campaign_id", "")).strip() != campaign_id:
            raise ValueError("review-history campaign must match the current export")
        if cell_id not in export_cells or export_cells[cell_id] != action:
            raise ValueError("review-history cell and action must match the current export")
        if status not in _REVIEW_STATUSES or entry.get("approval_applied") is not False:
            raise ValueError("review-history status must be valid and approval must remain unapplied")
        try:
            reviewed_on = date.fromisoformat(str(entry.get("reviewed_on", "")))
        except ValueError as exc:
            raise ValueError("review-history date must be ISO format") from exc
        if reviewed_on > as_of:
            raise ValueError("review history cannot be future-dated")
        reviews[review_id] = {
            "review_id": review_id,
            "cell_id": cell_id,
            "action": action,
            "review_status": status,
            "reviewed_on": reviewed_on,
        }

    if not isinstance(feedback_replay, dict):
        raise ValueError("feedback replay must be an object")
    replayed = feedback_replay.get("replayed")
    excluded = feedback_replay.get("excluded")
    if not isinstance(replayed, list) or not isinstance(excluded, list):
        raise ValueError("feedback replay must expose replayed and excluded records")
    if (
        feedback_replay.get("approval_applied") is not False
        or feedback_replay.get("campaign_state_changed") is not False
        or feedback_replay.get("platform_writes_executed") != 0
    ):
        raise ValueError("feedback replay must remain non-executing")
    if feedback_replay.get("record_count") != len(replayed) + len(excluded):
        raise ValueError("feedback replay counts must reconcile")

    seen_feedback: set[str] = set()
    reconciled: list[dict[str, Any]] = []
    for collection, expected_statuses in ((replayed, {"accepted"}), (excluded, {"pending", "rejected"})):
        for record in collection:
            feedback_id = str(record.get("feedback_id", "")).strip() if isinstance(record, dict) else ""
            review_id = str(record.get("review_id", "")).strip() if isinstance(record, dict) else ""
            status = str(record.get("status", "")).strip() if isinstance(record, dict) else ""
            if not feedback_id or feedback_id in seen_feedback:
                raise ValueError("feedback replay IDs must be unique")
            seen_feedback.add(feedback_id)
            if review_id not in reviews or status not in expected_statuses or record.get("passed") is not True:
                raise ValueError("feedback replay records must retain validated status and current review references")
            if status == "accepted":
                current = reviews[review_id]
                reconciled.append({
                    "feedback_id": feedback_id,
                    "review_id": review_id,
                    "cell_id": current["cell_id"],
                    "action": current["action"],
                    "review_status": current["review_status"],
                    "closure_state": "open" if current["review_status"] in _OPEN_STATUSES else "closed",
                })

    cutoff = as_of - timedelta(days=stale_after_days)
    stale_reviews = [
        {
            "review_id": item["review_id"],
            "cell_id": item["cell_id"],
            "action": item["action"],
            "review_status": item["review_status"],
            "age_days": (as_of - item["reviewed_on"]).days,
        }
        for item in reviews.values()
        if item["review_status"] in _OPEN_STATUSES and item["reviewed_on"] <= cutoff
    ]
    stale_reviews.sort(key=lambda item: (-item["age_days"], item["review_id"]))
    reconciled.sort(key=lambda item: (item["review_id"], item["feedback_id"]))
    return {
        "schema_version": "1.0",
        "as_of_date": as_of.isoformat(),
        "stale_after_days": stale_after_days,
        "reconciled_count": len(reconciled),
        "stale_review_count": len(stale_reviews),
        "reconciled_feedback": reconciled,
        "stale_reviews": stale_reviews,
        "approval_applied": False,
        "campaign_state_changed": False,
        "budget_changes_executed": 0,
        "platform_writes_executed": 0,
        "external_actions_executed": 0,
        "boundary": "Reconciliation exposes accepted feedback and stale deferred reviews for human follow-up; it does not approve, launch, publish or change budget.",
    }


__all__ = ["reconcile_campaign_review_feedback"]
