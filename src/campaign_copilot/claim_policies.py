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
            r"\bguarante(?:e|es|ed|eing)\b|\bno\s+exceptions?\b",
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
    r"\b(?:sales?|revenue|results?|returns?|performance|conversions?|profit|roi|roas|orders?|"
    r"leads?|traffic|clicks?|ctr|cvr|cpa|cpc|reach|impressions?|engagement|growth|uplift|"
    r"acquisition|retention|installs?|downloads?|subscribers?|signups?|bookings?|footfall|market\s+share)\b",
    re.IGNORECASE,
)
PERFORMANCE_PROMISE = re.compile(
    r"\b(?:promis(?:e|es|ed|ing)|assur(?:e|es|ed|ing)|pledge(?:s|d|ing)?)\b",
    re.IGNORECASE,
)
PERFORMANCE_COMMITMENT = re.compile(
    r"\b(?:commit(?:s|ted|ting)?|ensur(?:e|es|ed|ing))\b",
    re.IGNORECASE,
)
PERFORMANCE_CERTAINTY = re.compile(
    r"\b(?:certain(?:ly)?|sure(?:ly)?|always|inevitabl(?:e|y)|definitel(?:y)|bound|destined|"
    r"set\s+to|going\s+to|must|cannot|every\s+time|no\s+matter\s+what|cannot\s+fail)\b",
    re.IGNORECASE,
)
PERFORMANCE_MODAL = re.compile(r"\b(?:will|shall)\b", re.IGNORECASE)
PERFORMANCE_CHANGE = re.compile(
    r"\b(?:double[ds]?|doubling|triple[ds]?|tripling|twice|2x|3x|increase[ds]?|increasing|"
    r"grow(?:s|ing|n)?|improve[ds]?|improving|rise[sn]?|rising|fall(?:s|ing)?|drop(?:s|ped|ping)?|"
    r"decreas(?:e|es|ed|ing)|climb(?:s|ed|ing)?|soar(?:s|ed|ing)?|surg(?:e|es|ed|ing)|jump(?:s|ed|ing)?|"
    r"boost(?:s|ed|ing)?|skyrocket(?:s|ed|ing)?|lift(?:s|ed|ing)?|reduc(?:e|es|ed|ing)|cut(?:s|ting)?|"
    r"halv(?:e|es|ed|ing)|higher|lower|better|worse|outperform(?:s|ed|ing)?|exceed(?:s|ed|ing)?|half)\b",
    re.IGNORECASE,
)
PERFORMANCE_IMPERATIVE = re.compile(
    r"\b(?:double|triple|2x|3x|increase|improve|grow|boost|lift|raise|cut|halve|reduce)\s+(?:your\s+)?(?:sales?|revenue|results?|returns?|conversions?|profit|orders?|leads?|traffic|clicks?|ctr|cvr|cpa|cpc|reach|impressions?|engagement)\b|"
    r"\b(?:twice|three\s+times)\s+as\s+many\s+(?:sales?|orders?|leads?|clicks?|conversions?)\b",
    re.IGNORECASE,
)
PERFORMANCE_GOVERNANCE_CONTEXT = re.compile(
    r"\b(?:reports?|reporting|reported|reviews?|reviewed|reviewing|simulation|scenario|historical|"
    r"baseline|input|evidence|human|approval|approves?|approved)\b",
    re.IGNORECASE,
)
PERFORMANCE_CONDITIONAL = re.compile(
    r"\b(?:if|when|unless|depending\s+on|subject\s+to|may|might|could|only\s+if)\b",
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
            if not matched and claim.category == "descriptive" and PERFORMANCE_OUTCOME.search(claim.text):
                matched = {
                    "rule_id": "CLAIM-PERFORMANCE-METRIC-FAILSAFE",
                    "category": "performance_guarantee",
                    "matched_text": claim.text,
                }
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

        text = f"{creative.headline}. {creative.message}"
        fallback_matches = _find_high_risk_matches(text)
        if PERFORMANCE_OUTCOME.search(text) and not any(
            item["category"] == "performance_guarantee" for item in fallback_matches
        ):
            fallback_matches.append({
                "rule_id": "CLAIM-PERFORMANCE-METRIC-FAILSAFE",
                "category": "performance_guarantee",
                "matched_text": text,
            })
        for matched in fallback_matches:
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
    if direct:
        return {
            "rule_id": "CLAIM-PERFORMANCE-GUARANTEE",
            "category": "performance_guarantee",
            "matched_text": direct.group(0),
        }
    for sentence in (part.strip() for part in re.split(r"[.!?;\n]+", text) if part.strip()):
        if not PERFORMANCE_OUTCOME.search(sentence):
            continue
        change = PERFORMANCE_CHANGE.search(sentence)
        governance = PERFORMANCE_GOVERNANCE_CONTEXT.search(sentence)
        conditional = PERFORMANCE_CONDITIONAL.search(sentence)
        if governance and (not change or conditional):
            continue
        structural = (
            (PERFORMANCE_PROMISE.search(sentence) and (change or not governance))
            or PERFORMANCE_IMPERATIVE.search(sentence)
            or (change and (
                PERFORMANCE_COMMITMENT.search(sentence)
                or PERFORMANCE_CERTAINTY.search(sentence)
                or PERFORMANCE_MODAL.search(sentence)
            ))
        )
        if structural:
            return {
                "rule_id": "CLAIM-PERFORMANCE-GUARANTEE",
                "category": "performance_guarantee",
                "matched_text": sentence,
            }
    return None


def _reason(action: str, substantiated: bool) -> str:
    if action == "block":
        return "This high-risk claim category is blocked by the prototype policy."
    if action == "require_substantiation" and not substantiated:
        return "Objective product claims require a declared substantiation record before release."
    if action == "require_substantiation":
        return "Declared substantiation is present; a human must still verify scope and applicability."
    return "Descriptive claim; human policy review remains required."
