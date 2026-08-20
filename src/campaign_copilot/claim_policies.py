from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .models import ClaimEvidence, Creative


@dataclass(frozen=True)
class PolicyReference:
    policy_id: str
    title: str
    publisher: str
    url: str
    checked_on: str

    def to_dict(self) -> dict[str, str]:
        return {
            "policy_id": self.policy_id,
            "title": self.title,
            "publisher": self.publisher,
            "url": self.url,
            "checked_on": self.checked_on,
        }


POLICY_REFERENCES = {
    "GOOGLE-UNRELIABLE-CLAIMS": PolicyReference(
        "GOOGLE-UNRELIABLE-CLAIMS",
        "Unreliable claims - Advertising Policies Help",
        "Google",
        "https://support.google.com/adspolicy/answer/15936857?hl=en",
        "2026-08-16",
    ),
    "FTC-AD-SUBSTANTIATION": PolicyReference(
        "FTC-AD-SUBSTANTIATION",
        "Advertising FAQ's: A Guide for Small Business",
        "U.S. Federal Trade Commission",
        "https://www.ftc.gov/business-guidance/resources/advertising-faqs-guide-small-business",
        "2026-08-16",
    ),
    "FTC-HEALTH-CLAIMS": PolicyReference(
        "FTC-HEALTH-CLAIMS",
        "Health Products Compliance Guidance",
        "U.S. Federal Trade Commission",
        "https://www.ftc.gov/business-guidance/resources/health-products-compliance-guidance",
        "2026-08-16",
    ),
}


CATEGORY_POLICY = {
    "descriptive": ("allow", ()),
    "objective_product_claim": ("require_substantiation", ("FTC-AD-SUBSTANTIATION",)),
    "performance_guarantee": ("block", ("GOOGLE-UNRELIABLE-CLAIMS", "FTC-AD-SUBSTANTIATION")),
    "absolute_safety": ("block", ("GOOGLE-UNRELIABLE-CLAIMS", "FTC-AD-SUBSTANTIATION")),
    "health_outcome": ("block", ("FTC-HEALTH-CLAIMS",)),
}

HIGH_RISK_RULES = (
    (
        "CLAIM-PERFORMANCE-GUARANTEE",
        "performance_guarantee",
        re.compile(
            r"\bguarante(?:e|es|ed|eing)\b|\bno\s+exceptions?\b|"
            r"\b(?:promis(?:e|es|ed|ing)|assur(?:e|es|ed|ing)|pledge(?:s|d|ing)?)\b"
            r"[^.!?\n]{0,160}\b(?:sales?|revenue|results?|returns?|performance|conversions?|profit|roi|roas|orders?|customers?)\b|"
            r"\b(?:sales?|revenue|results?|returns?|performance|conversions?|profit|roi|roas|orders?|customers?)\b"
            r"[^.!?\n]{0,160}\b(?:promis(?:e|es|ed|ing)|assur(?:e|es|ed|ing)|pledge(?:s|d|ing)?)\b|"
            r"\b(?:sales?|revenue|results?|returns?|performance|conversions?|profit|roi|roas|orders?)\b"
            r"[^.!?\n]{0,80}\b(?:will|shall)\s+(?:double|triple|increase|grow|improve|rise)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "CLAIM-ABSOLUTE-SAFETY",
        "absolute_safety",
        re.compile(
            r"\b(?:100\s*%|completely|totally)\s+(?:risk[- ]free|safe)\b|\bno\s+risk\b",
            re.IGNORECASE,
        ),
    ),
    (
        "CLAIM-INSTANT-HEALTH-OUTCOME",
        "health_outcome",
        re.compile(
            r"\b(?:instant|instantly|immediate|immediately)\w*\s+(?:cure|cures|cured|heal|heals|healed|relief)\b",
            re.IGNORECASE,
        ),
    ),
)

PERFORMANCE_OUTCOME = re.compile(
    r"\b(?:sales?|revenue|results?|returns?|performance|conversions?|profit|roi|roas|orders?|customers?)\b",
    re.IGNORECASE,
)
PERFORMANCE_CERTAINTY = re.compile(
    r"\b(?:promis(?:e|es|ed|ing)|assur(?:e|es|ed|ing)|pledge(?:s|d|ing)?|"
    r"commit(?:s|ted|ting)?|ensur(?:e|es|ed|ing)|certain(?:ly)?|sure(?:ly)?|"
    r"always|inevitabl(?:e|y)|definitel(?:y)|every\s+time|no\s+matter\s+what)\b",
    re.IGNORECASE,
)
PERFORMANCE_MULTIPLIER = re.compile(
    r"\b(?:double[ds]?|doubling|triple[ds]?|tripling|twice|2x|3x)\b",
    re.IGNORECASE,
)
PERFORMANCE_CERTAIN_GROWTH = re.compile(
    r"\b(?:will|shall)\b[^.!?\n]{0,80}\b(?:increase[ds]?|grow[sn]?|improve[ds]?|rise[sn]?|double[ds]?|triple[ds]?)\b",
    re.IGNORECASE,
)


def review_creative_claims(
    creatives: tuple[Creative, ...],
    evidence: tuple[ClaimEvidence, ...],
) -> dict[str, Any]:
    evidence_by_id = {item.evidence_id: item for item in evidence}
    decisions: list[dict[str, Any]] = []
    referenced_policy_ids: set[str] = set()

    for creative in creatives:
        structured_rule_ids: set[str] = set()
        for claim in creative.claims:
            matched = _match_high_risk_rule(claim.text)
            if matched:
                structured_rule_ids.add(matched["rule_id"])
            effective_category = matched["category"] if matched else claim.category
            action, policy_ids = CATEGORY_POLICY[effective_category]
            referenced_policy_ids.update(policy_ids)
            substantiation = [
                evidence_by_id[evidence_id]
                for evidence_id in claim.evidence_ids
                if evidence_by_id[evidence_id].evidence_type == "product_substantiation"
            ]
            blocked = action == "block" or (action == "require_substantiation" and not substantiation)
            reason = _reason(action, bool(substantiation))
            if effective_category != claim.category:
                reason = "A high-risk phrase overrides the declared category. " + reason
            decisions.append({
                "creative_id": creative.creative_id,
                "claim_id": claim.claim_id,
                "claim": claim.text,
                "declared_category": claim.category,
                "category": effective_category,
                "category_override_applied": effective_category != claim.category,
                "matched_rule_id": matched["rule_id"] if matched else None,
                "matched_text": matched["matched_text"] if matched else None,
                "decision": "blocked" if blocked else "allowed_for_human_review",
                "reason": reason,
                "policy_ids": list(policy_ids),
                "substantiation_ids": [item.evidence_id for item in substantiation],
            })

        text = f"{creative.headline} {creative.message}"
        for matched in _find_high_risk_matches(text):
            rule_id, category = matched["rule_id"], matched["category"]
            if rule_id not in structured_rule_ids:
                _, policy_ids = CATEGORY_POLICY[category]
                referenced_policy_ids.update(policy_ids)
                decisions.append({
                    "creative_id": creative.creative_id,
                    "claim_id": None,
                    "claim": matched["matched_text"],
                    "declared_category": None,
                    "category": category,
                    "category_override_applied": True,
                    "matched_rule_id": rule_id,
                    "matched_text": matched["matched_text"],
                    "decision": "blocked",
                    "reason": "A high-risk phrase was found outside the structured claim register.",
                    "policy_ids": list(policy_ids),
                    "substantiation_ids": [],
                })

    blocked = [item for item in decisions if item["decision"] == "blocked"]
    return {
        "release_blocked": bool(blocked),
        "decisions": decisions,
        "violations": blocked,
        "policy_references": [
            POLICY_REFERENCES[policy_id].to_dict()
            for policy_id in sorted(referenced_policy_ids)
        ],
        "policy_scope": "screening aid; current platform and jurisdiction review still required",
    }


def _match_high_risk_rule(text: str) -> dict[str, str] | None:
    matches = _find_high_risk_matches(text)
    return matches[0] if matches else None


def _find_high_risk_matches(text: str) -> list[dict[str, str]]:
    matches: list[dict[str, str]] = []
    performance = _match_performance_guarantee(text)
    if performance:
        matches.append(performance)
    for rule_id, category, pattern in HIGH_RISK_RULES:
        if rule_id == "CLAIM-PERFORMANCE-GUARANTEE":
            continue
        match = pattern.search(text)
        if match:
            matches.append({"rule_id": rule_id, "category": category, "matched_text": match.group(0)})
    return matches


def _match_performance_guarantee(text: str) -> dict[str, str] | None:
    direct_pattern = HIGH_RISK_RULES[0][2]
    direct = direct_pattern.search(text)
    has_outcome = PERFORMANCE_OUTCOME.search(text)
    structural = has_outcome and (
        PERFORMANCE_CERTAINTY.search(text)
        or PERFORMANCE_MULTIPLIER.search(text)
        or PERFORMANCE_CERTAIN_GROWTH.search(text)
    )
    if not direct and not structural:
        return None
    matched_text = direct.group(0) if direct else text.strip()
    return {
        "rule_id": "CLAIM-PERFORMANCE-GUARANTEE",
        "category": "performance_guarantee",
        "matched_text": matched_text,
    }


def _reason(action: str, substantiated: bool) -> str:
    if action == "block":
        return "This high-risk claim category is blocked by the prototype policy."
    if action == "require_substantiation" and not substantiated:
        return "Objective product claims require a declared substantiation record before release."
    if action == "require_substantiation":
        return "Declared substantiation is present; a human must still verify scope and applicability."
    return "Descriptive claim; human policy review remains required."
