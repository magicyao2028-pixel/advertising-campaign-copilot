from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ObjectivePolicy:
    policy_id: str
    objective: str
    required_outcome_type: str
    scale_score: int
    factor_weights: dict[str, int]
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "objective": self.objective,
            "required_outcome_type": self.required_outcome_type,
            "scale_score": self.scale_score,
            "factor_weights": dict(self.factor_weights),
            "explanation": self.explanation,
        }


OBJECTIVE_POLICIES = {
    "revenue": ObjectivePolicy(
        policy_id="OBJ-REV-001",
        objective="revenue",
        required_outcome_type="purchase",
        scale_score=100,
        factor_weights={"roas_target_met": 60, "cpa_guardrail_met": 40},
        explanation="Prioritize revenue efficiency while retaining a CPA guardrail.",
    ),
    "conversions": ObjectivePolicy(
        policy_id="OBJ-CONV-001",
        objective="conversions",
        required_outcome_type="conversion",
        scale_score=100,
        factor_weights={"cpa_target_met": 80, "recorded_outcome_present": 20},
        explanation="Prioritize conversion cost and require at least one recorded conversion.",
    ),
    "leads": ObjectivePolicy(
        policy_id="OBJ-LEAD-001",
        objective="leads",
        required_outcome_type="qualified_lead",
        scale_score=100,
        factor_weights={"cpa_target_met": 80, "recorded_outcome_present": 20},
        explanation="Treat only explicitly labelled qualified leads as lead outcomes.",
    ),
}


def get_objective_policy(objective: str) -> ObjectivePolicy:
    try:
        return OBJECTIVE_POLICIES[objective]
    except KeyError as exc:
        raise ValueError(f"unsupported objective policy: {objective}") from exc


def score_cell(cell: dict[str, Any], policy: ObjectivePolicy) -> dict[str, Any]:
    if policy.objective == "revenue":
        checks = {
            "roas_target_met": {
                "observed": cell["roas"], "operator": ">=", "threshold": cell["target_roas"],
                "passed": cell["roas"] >= cell["target_roas"],
            },
            "cpa_guardrail_met": {
                "observed": cell["cpa"], "operator": "<=", "threshold": cell["target_cpa"],
                "passed": cell["cpa"] is not None and cell["cpa"] <= cell["target_cpa"],
            },
        }
    else:
        checks = {
            "cpa_target_met": {
                "observed": cell["cpa"], "operator": "<=", "threshold": cell["target_cpa"],
                "passed": cell["cpa"] is not None and cell["cpa"] <= cell["target_cpa"],
            },
            "recorded_outcome_present": {
                "observed": cell["conversions"], "operator": ">", "threshold": 0,
                "passed": cell["conversions"] > 0,
            },
        }
    factors = []
    score = 0
    for factor, weight in policy.factor_weights.items():
        check = checks[factor]
        if check["passed"]:
            score += weight
        factors.append({"factor": factor, "weight": weight, **check})
    return {"score": score, "scale_score": policy.scale_score, "factors": factors}
