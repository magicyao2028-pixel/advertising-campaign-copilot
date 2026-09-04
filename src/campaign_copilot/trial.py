from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from .copilot import CampaignCopilot
from .creative_feedback import replay_creative_feedback
from .experiment_queue import build_experiment_queue
from .review_export import build_experiment_review_export
from .review_history import summarize_experiment_review_history
from .reviewer_feedback_replay import replay_reviewer_feedback
from .models import CampaignBrief, load_campaign


COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return payload


def validate_evidence_index(root: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    claims = payload.get("claims")
    if not isinstance(claims, list) or not claims:
        raise ValueError("Evidence index must contain claims")
    root = root.resolve()
    seen: set[str] = set()
    checks = []
    for claim in claims:
        claim_id = str(claim.get("claim_id", "")).strip() if isinstance(claim, dict) else ""
        artifacts = claim.get("artifacts") if isinstance(claim, dict) else None
        if not claim_id or claim_id in seen or not str(claim.get("statement", "")).strip() or not isinstance(artifacts, list) or not artifacts:
            raise ValueError("Evidence claims must be unique and complete")
        seen.add(claim_id)
        paths = []
        for artifact in artifacts:
            relative = str(artifact.get("path", "")) if isinstance(artifact, dict) else ""
            target = (root / relative).resolve()
            if not isinstance(artifact, dict) or not str(artifact.get("kind", "")).strip() or not relative or not target.is_relative_to(root) or not target.is_file():
                raise ValueError(f"Missing, unsafe or untyped evidence path: {relative}")
            paths.append(relative)
        checks.append({"claim_id": claim_id, "artifact_paths": paths, "passed": True})
    return checks


def validate_external_intake(payload: dict[str, Any]) -> list[dict[str, Any]]:
    date.fromisoformat(str(payload.get("reviewed_on", "")))
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("External intake must contain candidates")
    checks = []
    for item in candidates:
        required = {"repository", "version", "commit", "license", "decision", "code_adopted", "reason"}
        if not isinstance(item, dict) or required.difference(item):
            raise ValueError("External candidate metadata is incomplete")
        if not str(item["repository"]).startswith("https://github.com/") or not COMMIT_PATTERN.fullmatch(str(item["commit"])):
            raise ValueError("External repository or full commit SHA is invalid")
        if item["decision"] not in {"adopted", "rejected"} or not isinstance(item["code_adopted"], bool) or (item["decision"] == "adopted") != item["code_adopted"]:
            raise ValueError("External decision is invalid or inconsistent")
        checks.append({"repository": item["repository"], "decision": item["decision"], "passed": True})
    return checks


def validate_feedback(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    required = {"feedback_id", "source_type", "recorded_on", "classification", "decision", "summary", "acceptance_test", "implementation", "release_result"}
    if required.difference(payload) or any(not str(payload[key]).strip() for key in required):
        raise ValueError("Feedback record is incomplete")
    date.fromisoformat(str(payload["recorded_on"]))
    if payload["source_type"] not in {"real", "synthetic"} or payload["classification"] not in {"defect", "requirement", "usability", "performance", "safety", "documentation"}:
        raise ValueError("Feedback source_type or classification is unsupported")
    if payload["decision"] != "accepted":
        raise ValueError("Trial feedback case must be accepted")
    for key in ("acceptance_test", "implementation"):
        target = (root.resolve() / str(payload[key])).resolve()
        if not target.is_relative_to(root.resolve()) or not target.is_file():
            raise ValueError(f"Feedback {key} path is missing or unsafe")
    return {"feedback_id": payload["feedback_id"], "source_type": payload["source_type"], "passed": True}


def run_trial(root: Path) -> dict[str, Any]:
    root = root.resolve()
    baseline = CampaignCopilot().review(load_campaign(root / "data/sample_campaign.json"))
    queue = build_experiment_queue(baseline)
    review_export = build_experiment_review_export(baseline, queue)
    review_history_payload = json.loads((root / "data/review_history.json").read_text(encoding="utf-8"))
    review_history = summarize_experiment_review_history(review_export, review_history_payload)
    reviewer_feedback_replay = replay_reviewer_feedback(
        json.loads((root / "data/reviewer_feedback.json").read_text(encoding="utf-8")),
        review_history_payload,
    )
    low_information_payload = json.loads((root / "data/sample_campaign.json").read_text(encoding="utf-8"))
    low_information_payload["performance"][0].update({"spend": 100, "impressions": 100, "clicks": 50, "conversions": 10, "revenue": 300})
    low_information = CampaignCopilot().review(CampaignBrief.from_mapping(low_information_payload))
    low_information_scale_blocked = (
        low_information["optimization_recommendations"][0]["action"] == "hold_and_test"
        and not low_information["optimization_recommendations"][0]["sample_quality"]["passed"]
    )
    replay = replay_creative_feedback(root / "data/sample_campaign.json", root / "data/creative_feedback.json")
    evidence = validate_evidence_index(root, load_json_object(root / "evidence/evidence_index.json"))
    external = validate_external_intake(load_json_object(root / "evidence/external_intake.json"))
    feedback = validate_feedback(root, load_json_object(root / "evidence/feedback_case.json"))
    replay_safe = all(item["actual"]["release_blocked"] and item["actual"]["optimization_recommendations"] == 0 and item["actual"]["platform_write_executed"] is False for item in replay["replayed"])
    core_passed = baseline["status"] == "ready_for_human_review" and baseline["governance"]["platform_write_executed"] is False and replay["summary"]["passed"] == 2 and replay_safe and low_information_scale_blocked and queue["platform_writes_executed"] == 0 and queue["items"] and review_export["item_count"] == len(queue["items"]) and review_export["approval_applied"] is False and review_history["entry_count"] == 3 and review_history["platform_writes_executed"] == 0 and review_history["approval_applied"] is False and reviewer_feedback_replay["replayed_count"] == 1 and reviewer_feedback_replay["excluded_count"] == 1 and reviewer_feedback_replay["approval_applied"] is False
    return {
        "schema_version": "1.0", "trial_id": "TRIAL-CAMPAIGN-001", "source_data": "synthetic",
        "overall_passed": core_passed and feedback["passed"] and all(item["passed"] for item in evidence + external),
        "core_flow": {"passed": core_passed, "baseline_status": baseline["status"], "feedback_cases_passed": replay["summary"]["passed"], "pending_feedback_excluded": replay["summary"]["excluded"], "blocked_cases_emitted_optimization": False, "low_information_scale_blocked": low_information_scale_blocked, "platform_writes_executed": 0},
        "feedback_regression": feedback, "reviewer_feedback_replay": reviewer_feedback_replay, "external_intake": external, "experiment_queue": queue, "experiment_review_export": review_export, "review_history": review_history, "evidence_index": evidence,
        "boundaries": load_json_object(root / "evidence/evidence_index.json")["boundaries"],
    }


def write_trial_report(root: Path, json_path: Path, markdown_path: Path) -> dict[str, Any]:
    report = run_trial(root)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text("\n".join([
        "# Campaign Copilot Trial Readiness", "", "> Synthetic offline verification; no ad, budget or platform write is executed.", "",
        f"- Overall: **{'PASS' if report['overall_passed'] else 'FAIL'}**", f"- Baseline: `{report['core_flow']['baseline_status']}`",
        f"- Feedback cases blocked as expected: {report['core_flow']['feedback_cases_passed']}/2", f"- Pending feedback excluded: {report['core_flow']['pending_feedback_excluded']}", f"- Reviewer feedback replay: {report['reviewer_feedback_replay']['replayed_count']} accepted, {report['reviewer_feedback_replay']['excluded_count']} excluded", f"- Low-information scale blocked: {'yes' if report['core_flow']['low_information_scale_blocked'] else 'no'}", f"- Experiment queue items: {len(report['experiment_queue']['items'])}", f"- Review export approvals applied: {report['experiment_review_export']['approval_applied']}", f"- Review-history entries summarized: {report['review_history']['entry_count']}", "",
        "## Pilot boundary", "", *[f"- {item}" for item in report["boundaries"]], "",
    ]), encoding="utf-8")
    return report
