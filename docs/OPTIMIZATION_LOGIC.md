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
3. A cell becomes `candidate_scale` only when CPA exists, CPA is no higher than target, and ROAS is no lower than target.
4. Every other cell becomes `hold_and_test`.

## Budget guardrail

A scale candidate receives a suggested increase equal to the smaller of 15% and the campaign's declared maximum reallocation. Input validation prevents that maximum from exceeding 20%.

The suggestion is informational. It does not calculate where the funding comes from and it never changes a live budget.

## Evidence and approval

Each recommendation cites the performance cell's `source_id`, declares `requires_human_approval: true`, and declares `executed: false`.

## Important limitations

The rules do not check sample sufficiency, seasonality, attribution windows, marginal return, channel policy, inventory, incrementality, or statistical confidence. Those are planned maintenance topics, not hidden capabilities.
