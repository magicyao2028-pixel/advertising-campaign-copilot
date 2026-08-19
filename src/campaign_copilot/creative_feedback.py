from __future__ import annotations

import copy
import json
from datetime import date
from pathlib import Path
from typing import Any

from .copilot import CampaignCopilot
from .models import CampaignBrief


SOURCE_TYPES = {"real", "synthetic"}
CLASSIFICATIONS = {"defect", "requirement", "usability", "performance", "safety", "documentation"}
DISPOSITIONS = {"accepted_for_replay", "pending", "rejected"}


def load_feedback(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Creative feedback must contain an object")
    records = payload.get("records")
    if not str(payload.get("batch_id", "")).strip() or not isinstance(records, list) or not records:
        raise ValueError("Creative feedback requires batch_id and records")
    seen: set[str] = set()
    for record in records:
        feedback_id = str(record.get("feedback_id", "")).strip() if isinstance(record, dict) else ""
        if not feedback_id or feedback_id in seen:
            raise ValueError("Feedback IDs must be present and unique")
        seen.add(feedback_id)
        required = {"source_type", "recorded_on", "classification", "disposition", "reviewer_alias", "rationale"}
        if required.difference(record) or any(not str(record[key]).strip() for key in required):
            raise ValueError("Feedback metadata is incomplete")
        date.fromisoformat(str(record["recorded_on"]))
        if record["source_type"] not in SOURCE_TYPES or record["classification"] not in CLASSIFICATIONS or record["disposition"] not in DISPOSITIONS:
            raise ValueError("Feedback source, classification or disposition is unsupported")
        if record["disposition"] == "accepted_for_replay":
            replay = record.get("replay")
            expected = record.get("expected")
            if not isinstance(replay, dict) or not isinstance(expected, dict):
                raise ValueError("Accepted feedback requires replay and expected objects")
            replay_required = {"creative_id", "claim_id", "text", "category", "evidence_ids"}
            if replay_required.difference(replay) or not isinstance(replay["evidence_ids"], list):
                raise ValueError("Accepted feedback replay is incomplete")
            if any(not isinstance(replay[key], str) or not replay[key].strip() for key in {"creative_id", "claim_id", "text", "category"}):
                raise ValueError("Accepted feedback replay values must be non-empty strings")
            if any(not isinstance(evidence_id, str) or not evidence_id.strip() for evidence_id in replay["evidence_ids"]):
                raise ValueError("Accepted feedback evidence IDs must be non-empty strings")
            if set(expected) != {"status", "release_blocked", "matched_rule_id"} or not isinstance(expected["release_blocked"], bool):
                raise ValueError("Accepted feedback expected result is invalid")
            if not isinstance(expected["status"], str) or not expected["status"].strip():
                raise ValueError("Accepted feedback expected status must be a non-empty string")
            if expected["matched_rule_id"] is not None and not isinstance(expected["matched_rule_id"], str):
                raise ValueError("Accepted feedback expected rule must be a string or null")
    return payload


def replay_creative_feedback(campaign_path: Path, feedback_path: Path) -> dict[str, Any]:
    base_payload = json.loads(campaign_path.read_text(encoding="utf-8"))
    if not isinstance(base_payload, dict):
        raise ValueError("Campaign file must contain an object")
    feedback = load_feedback(feedback_path)
    replayed, excluded = [], []
    for record in feedback["records"]:
        if record["disposition"] != "accepted_for_replay":
            excluded.append({
                "feedback_id": record["feedback_id"], "disposition": record["disposition"],
                "reason": "Only accepted_for_replay feedback can enter deterministic review.",
            })
            continue
        candidate = copy.deepcopy(base_payload)
        replay = record["replay"]
        creative = next((item for item in candidate.get("creatives", []) if item.get("creative_id") == replay["creative_id"]), None)
        if creative is None:
            raise ValueError(f"Unknown feedback creative_id: {replay['creative_id']}")
        claim = next((item for item in creative.get("claims", []) if item.get("claim_id") == replay["claim_id"]), None)
        if claim is None:
            raise ValueError(f"Unknown feedback claim_id: {replay['claim_id']}")
        claim.update({"text": replay["text"], "category": replay["category"], "evidence_ids": replay["evidence_ids"]})
        result = CampaignCopilot().review(CampaignBrief.from_mapping(candidate))
        violation = next((item for item in result["creative_review"]["violations"] if item.get("claim_id") == replay["claim_id"]), None)
        actual = {
            "status": result["status"],
            "release_blocked": result["creative_review"]["release_blocked"],
            "matched_rule_id": violation.get("matched_rule_id") if violation else None,
            "platform_write_executed": result["governance"]["platform_write_executed"],
            "optimization_recommendations": len(result["optimization_recommendations"]),
        }
        expected = record["expected"]
        checks = {
            "status": actual["status"] == expected["status"],
            "release_blocked": actual["release_blocked"] == expected["release_blocked"],
            "matched_rule_id": actual["matched_rule_id"] == expected["matched_rule_id"],
            "no_platform_write": actual["platform_write_executed"] is False,
            "blocked_release_has_no_optimization": not actual["release_blocked"] or actual["optimization_recommendations"] == 0,
        }
        replayed.append({
            "feedback_id": record["feedback_id"], "source_type": record["source_type"],
            "classification": record["classification"], "reviewer_alias": record["reviewer_alias"],
            "checks": checks, "actual": actual, "passed": all(checks.values()),
        })
    return {
        "replay_version": "0.5", "batch_id": feedback["batch_id"], "source_data": "synthetic",
        "summary": {"total_feedback": len(feedback["records"]), "replayed": len(replayed), "passed": sum(item["passed"] for item in replayed), "failed": sum(not item["passed"] for item in replayed), "excluded": len(excluded)},
        "replayed": replayed, "excluded": excluded,
        "governance": [
            "Feedback is separate review evidence and never changes the bundled campaign automatically.",
            "Only accepted_for_replay records execute; all platform writes and blocked optimization outputs remain disabled.",
            "The public fixture is synthetic and does not represent advertiser or platform feedback."
        ],
    }


def write_feedback_report(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = [
        "# Creative Feedback Replay", "", f"- Result: **{report['summary']['passed']}/{report['summary']['replayed']} cases passed**",
        "- Source: synthetic public fixture", "", "| Feedback | Classification | Status | Rule | Result |", "| --- | --- | --- | --- | --- |",
    ]
    for item in report["replayed"]:
        rows.append(f"| {item['feedback_id']} | {item['classification']} | {item['actual']['status']} | {item['actual']['matched_rule_id'] or 'none'} | {'PASS' if item['passed'] else 'FAIL'} |")
    rows.extend(["", "## Governance", "", *[f"- {item}" for item in report["governance"]]])
    markdown_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
