# Optimization Logic

## Metrics

- `CTR = clicks / impressions`
- `CVR = conversions / clicks`
- `CPA = spend / conversions`; undefined when conversions are zero
- `ROAS = revenue / spend`; reported as zero when spend is zero

Division-by-zero cases are handled explicitly. These descriptive metrics do not prove causality.

## Decision order

1. A prohibited creative phrase blocks the release of every optimization recommendation.
2. A cell with zero conversions after spending at least 10% of the total campaign budget becomes `pause_and_review`.
3. The declared objective selects one versioned policy and verifies its required outcome type.
4. A cell becomes `candidate_scale` only when every weighted factor in that policy passes and the score reaches 100.
5. Every other cell becomes `hold_and_test`.

See [Objective Policies](OBJECTIVE_POLICIES.md) for exact factors and weights.

## Budget guardrail

A scale candidate receives a suggested increase equal to the smaller of 15% and the campaign's declared maximum reallocation. Input validation prevents that maximum from exceeding 20%.

The suggestion is informational. It does not calculate where the funding comes from and it never changes a live budget.

## Period comparison

The campaign declares one `reporting_period` in `YYYY-MM` format. Current observations must match it, and history must be earlier. A trend is calculated only when the same cell has an observation in the immediately preceding month and both channel and creative ID are unchanged.

The review emits explicit warnings for:

- no prior observation;
- a missing observation in the reporting period;
- a latest comparison period that is not adjacent;
- a changed channel or creative dimension.

Comparable records report percentage-point changes for CTR and CVR, and percentage changes for spend, CPA, and ROAS. A percentage change is `null` when its earlier denominator is zero or unavailable. These calculations are descriptive and do not establish incrementality, statistical significance, or future performance.

## Evidence and approval

Each recommendation cites the performance cell's `source_id`, declares `requires_human_approval: true`, and declares `executed: false`.

## Important limitations

The rules do not check sample sufficiency, seasonality, attribution windows, marginal return, channel policy, inventory, incrementality, or statistical confidence. Those are planned maintenance topics, not hidden capabilities.
