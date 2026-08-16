from __future__ import annotations

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

PHRASE_CATEGORY = {
    "guaranteed results": "performance_guarantee",
    "no exceptions": "performance_guarantee",
    "100% risk-free": "absolute_safety",
    "instant cure": "health_outcome",
}


def review_creative_claims(
    creatives: tuple[Creative, ...],
    evidence: tuple[ClaimEvidence, ...],
) -> dict[str, Any]:
    evidence_by_id = {item.evidence_id: item for item in evidence}
    decisions: list[dict[str, Any]] = []
    referenced_policy_ids: set[str] = set()

    for creative in creatives:
        for claim in creative.claims:
            action, policy_ids = CATEGORY_POLICY[claim.category]
            referenced_policy_ids.update(policy_ids)
            substantiation = [
                evidence_by_id[evidence_id]
                for evidence_id in claim.evidence_ids
                if evidence_by_id[evidence_id].evidence_type == "product_substantiation"
            ]
            blocked = action == "block" or (action == "require_substantiation" and not substantiation)
            reason = _reason(action, bool(substantiation))
            decisions.append({
                "creative_id": creative.creative_id,
                "claim_id": claim.claim_id,
                "claim": claim.text,
                "category": claim.category,
                "decision": "blocked" if blocked else "allowed_for_human_review",
                "reason": reason,
                "policy_ids": list(policy_ids),
                "substantiation_ids": [item.evidence_id for item in substantiation],
            })

        text = f"{creative.headline} {creative.message}".casefold()
        declared_text = " ".join(claim.text.casefold() for claim in creative.claims)
        for phrase, category in sorted(PHRASE_CATEGORY.items()):
            if phrase in text and phrase not in declared_text:
                _, policy_ids = CATEGORY_POLICY[category]
                referenced_policy_ids.update(policy_ids)
                decisions.append({
                    "creative_id": creative.creative_id,
                    "claim_id": None,
                    "claim": phrase,
                    "category": category,
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


def _reason(action: str, substantiated: bool) -> str:
    if action == "block":
        return "This high-risk claim category is blocked by the prototype policy."
    if action == "require_substantiation" and not substantiated:
        return "Objective product claims require a declared substantiation record before release."
    if action == "require_substantiation":
        return "Declared substantiation is present; a human must still verify scope and applicability."
    return "Descriptive claim; human policy review remains required."
