# Objective Policies

The declared objective selects exactly one deterministic policy. A factor contributes its full weight only when its explicit condition passes; there is no hidden model score.

| Policy | Objective | Required outcome type | Weighted scale factors |
| --- | --- | --- | --- |
| `OBJ-REV-001` | Revenue | `purchase` | ROAS target 60; CPA guardrail 40 |
| `OBJ-CONV-001` | Conversions | `conversion` | CPA target 80; at least one recorded outcome 20 |
| `OBJ-LEAD-001` | Leads | `qualified_lead` | CPA target 80; at least one recorded outcome 20 |

A scale candidate must reach 100/100. Zero outcomes after the minimum review-spend threshold still produce `pause_and_review`, regardless of objective. All other cases produce `hold_and_test`.

The weights are illustrative product rules, not trained probabilities, forecasts, statistical confidence, or universally valid advertising standards. Changing them requires a versioned policy and new tests.
