from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


OBJECTIVES = {"conversions", "revenue", "leads"}
OUTCOME_TYPES = {"purchase", "conversion", "qualified_lead"}
CHANNELS = {"search", "short_video", "social_feed", "marketplace"}
CLAIM_CATEGORIES = {
    "descriptive",
    "objective_product_claim",
    "performance_guarantee",
    "absolute_safety",
    "health_outcome",
}
CLAIM_EVIDENCE_TYPES = {"product_substantiation"}
PERIOD_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


@dataclass(frozen=True)
class ClaimEvidence:
    evidence_id: str
    title: str
    evidence_type: str
    reference: str

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "ClaimEvidence":
        item = cls(
            evidence_id=str(value.get("evidence_id", "")).strip(),
            title=str(value.get("title", "")).strip(),
            evidence_type=str(value.get("evidence_type", "")).strip(),
            reference=str(value.get("reference", "")).strip(),
        )
        if not all((item.evidence_id, item.title, item.evidence_type, item.reference)):
            raise ValueError("claim evidence fields must not be blank")
        if item.evidence_type not in CLAIM_EVIDENCE_TYPES:
            raise ValueError(f"evidence_type must be one of: {', '.join(sorted(CLAIM_EVIDENCE_TYPES))}")
        return item


@dataclass(frozen=True)
class CreativeClaim:
    claim_id: str
    text: str
    category: str
    evidence_ids: tuple[str, ...]

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "CreativeClaim":
        item = cls(
            claim_id=str(value.get("claim_id", "")).strip(),
            text=str(value.get("text", "")).strip(),
            category=str(value.get("category", "")).strip(),
            evidence_ids=_strings(value.get("evidence_ids", []), "evidence_ids", allow_empty=True),
        )
        if not item.claim_id or not item.text:
            raise ValueError("claim_id and claim text must not be blank")
        if item.category not in CLAIM_CATEGORIES:
            raise ValueError(f"claim category must be one of: {', '.join(sorted(CLAIM_CATEGORIES))}")
        return item


@dataclass(frozen=True)
class Creative:
    creative_id: str
    headline: str
    message: str
    claims: tuple[CreativeClaim, ...]

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "Creative":
        claims_payload = value.get("claims", [])
        if not isinstance(claims_payload, list):
            raise ValueError("creative claims must be a list")
        item = cls(
            creative_id=str(value.get("creative_id", "")).strip(),
            headline=str(value.get("headline", "")).strip(),
            message=str(value.get("message", "")).strip(),
            claims=tuple(CreativeClaim.from_mapping(entry) for entry in claims_payload),
        )
        if not all((item.creative_id, item.headline, item.message)):
            raise ValueError("creative_id, headline and message must not be blank")
        return item


@dataclass(frozen=True)
class PerformanceCell:
    cell_id: str
    period: str
    channel: str
    creative_id: str
    source_id: str
    spend: float
    impressions: int
    clicks: int
    conversions: int
    revenue: float

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "PerformanceCell":
        item = cls(
            cell_id=str(value.get("cell_id", "")).strip(),
            period=str(value.get("period", "")).strip(),
            channel=str(value.get("channel", "")).strip(),
            creative_id=str(value.get("creative_id", "")).strip(),
            source_id=str(value.get("source_id", "")).strip(),
            spend=float(value.get("spend", 0)),
            impressions=int(value.get("impressions", 0)),
            clicks=int(value.get("clicks", 0)),
            conversions=int(value.get("conversions", 0)),
            revenue=float(value.get("revenue", 0)),
        )
        if not all((item.cell_id, item.period, item.channel, item.creative_id, item.source_id)):
            raise ValueError("performance identity and period fields must not be blank")
        validate_period(item.period, "performance period")
        if item.channel not in CHANNELS:
            raise ValueError(f"channel must be one of: {', '.join(sorted(CHANNELS))}")
        if min(item.spend, item.impressions, item.clicks, item.conversions, item.revenue) < 0:
            raise ValueError("performance values must not be negative")
        if item.clicks > item.impressions or item.conversions > item.clicks:
            raise ValueError("performance funnel counts must be monotonic")
        return item


@dataclass(frozen=True)
class CampaignBrief:
    campaign_id: str
    reporting_period: str
    objective: str
    outcome_type: str
    product: str
    audience: str
    currency: str
    total_budget: float
    target_roas: float
    target_cpa: float
    max_reallocation_pct: float
    human_owner: str
    channels: tuple[str, ...]
    constraints: tuple[str, ...]
    creatives: tuple[Creative, ...]
    performance: tuple[PerformanceCell, ...]
    performance_history: tuple[PerformanceCell, ...]
    claim_evidence: tuple[ClaimEvidence, ...]

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "CampaignBrief":
        creatives_payload = value.get("creatives")
        performance_payload = value.get("performance")
        history_payload = value.get("performance_history", [])
        claim_evidence_payload = value.get("claim_evidence", [])
        if not isinstance(creatives_payload, list) or not creatives_payload:
            raise ValueError("creatives must be a non-empty list")
        if not isinstance(performance_payload, list) or not performance_payload:
            raise ValueError("performance must be a non-empty list")
        if not isinstance(history_payload, list):
            raise ValueError("performance_history must be a list")
        if not isinstance(claim_evidence_payload, list):
            raise ValueError("claim_evidence must be a list")
        channels = _strings(value.get("channels"), "channels")
        if not set(channels).issubset(CHANNELS):
            raise ValueError(f"channels must be selected from: {', '.join(sorted(CHANNELS))}")
        item = cls(
            campaign_id=str(value.get("campaign_id", "")).strip(),
            reporting_period=str(value.get("reporting_period", "")).strip(),
            objective=str(value.get("objective", "")).strip(),
            outcome_type=str(value.get("outcome_type", "")).strip(),
            product=str(value.get("product", "")).strip(),
            audience=str(value.get("audience", "")).strip(),
            currency=str(value.get("currency", "")).strip().upper(),
            total_budget=float(value.get("total_budget", 0)),
            target_roas=float(value.get("target_roas", 0)),
            target_cpa=float(value.get("target_cpa", 0)),
            max_reallocation_pct=float(value.get("max_reallocation_pct", 0)),
            human_owner=str(value.get("human_owner", "")).strip(),
            channels=channels,
            constraints=_strings(value.get("constraints", []), "constraints", allow_empty=True),
            creatives=tuple(Creative.from_mapping(entry) for entry in creatives_payload),
            performance=tuple(PerformanceCell.from_mapping(entry) for entry in performance_payload),
            performance_history=tuple(PerformanceCell.from_mapping(entry) for entry in history_payload),
            claim_evidence=tuple(ClaimEvidence.from_mapping(entry) for entry in claim_evidence_payload),
        )
        if not all((item.campaign_id, item.product, item.audience, item.currency, item.human_owner)):
            raise ValueError("campaign identity and owner fields must not be blank")
        validate_period(item.reporting_period, "reporting_period")
        if item.objective not in OBJECTIVES:
            raise ValueError(f"objective must be one of: {', '.join(sorted(OBJECTIVES))}")
        if item.outcome_type not in OUTCOME_TYPES:
            raise ValueError(f"outcome_type must be one of: {', '.join(sorted(OUTCOME_TYPES))}")
        expected_outcome = {"revenue": "purchase", "conversions": "conversion", "leads": "qualified_lead"}[item.objective]
        if item.outcome_type != expected_outcome:
            raise ValueError(
                f"objective {item.objective} requires outcome_type {expected_outcome}; "
                f"received {item.outcome_type}"
            )
        if min(item.total_budget, item.target_roas, item.target_cpa) <= 0:
            raise ValueError("budget, target_roas and target_cpa must be positive")
        if not 0 < item.max_reallocation_pct <= 20:
            raise ValueError("max_reallocation_pct must be above 0 and no more than 20")
        _validate_relationships(item)
        return item


def load_campaign(path: Path) -> CampaignBrief:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid campaign JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Campaign file must contain a JSON object")
    return CampaignBrief.from_mapping(payload)


def period_index(period: str) -> int:
    year, month = (int(part) for part in period.split("-"))
    return year * 12 + month


def validate_period(period: str, field: str) -> None:
    if not PERIOD_PATTERN.fullmatch(period):
        raise ValueError(f"{field} must use YYYY-MM")


def _strings(value: Any, field: str, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field} must be a list of strings")
    cleaned = tuple(item.strip() for item in value if item.strip())
    if not cleaned and not allow_empty:
        raise ValueError(f"{field} must not be empty")
    return cleaned


def _validate_relationships(item: CampaignBrief) -> None:
    creative_ids = [creative.creative_id for creative in item.creatives]
    claims = [claim for creative in item.creatives for claim in creative.claims]
    claim_ids = [claim.claim_id for claim in claims]
    claim_evidence_ids = [evidence.evidence_id for evidence in item.claim_evidence]
    current_cell_ids = [cell.cell_id for cell in item.performance]
    observations = item.performance + item.performance_history
    source_ids = [cell.source_id for cell in observations]
    observation_keys = [(cell.cell_id, cell.period) for cell in observations]
    if len(creative_ids) != len(set(creative_ids)):
        raise ValueError("creative_id values must be unique")
    if len(claim_ids) != len(set(claim_ids)):
        raise ValueError("claim_id values must be unique")
    if len(claim_evidence_ids) != len(set(claim_evidence_ids)):
        raise ValueError("claim evidence_id values must be unique")
    if any(not set(claim.evidence_ids).issubset(claim_evidence_ids) for claim in claims):
        raise ValueError("every claim evidence_id must reference declared claim_evidence")
    if len(current_cell_ids) != len(set(current_cell_ids)):
        raise ValueError("current performance cell_id values must be unique")
    if any(cell.period != item.reporting_period for cell in item.performance):
        raise ValueError("current performance periods must match reporting_period")
    if any(period_index(cell.period) >= period_index(item.reporting_period) for cell in item.performance_history):
        raise ValueError("performance_history periods must be earlier than reporting_period")
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("source_id values must be unique")
    if len(observation_keys) != len(set(observation_keys)):
        raise ValueError("cell_id and period combinations must be unique")
    if any(cell.creative_id not in creative_ids for cell in observations):
        raise ValueError("every performance observation must reference a declared creative")
    if any(cell.channel not in item.channels for cell in observations):
        raise ValueError("every performance channel must be declared in channels")
    if sum(cell.spend for cell in item.performance) > item.total_budget:
        raise ValueError("observed spend must not exceed total_budget")
