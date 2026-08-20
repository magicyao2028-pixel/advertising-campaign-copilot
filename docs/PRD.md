# Product Requirements Document

## Product statement

Advertising Campaign Copilot helps a small business team translate a campaign brief and observed performance into a traceable review package before a human makes any advertising decision.

## Target users

- an operations manager planning a campaign;
- a marketing lead reviewing creative and budget choices;
- a product or technology partner validating an AI-assisted workflow.

## Primary job to be done

When a team has a campaign objective, several creatives, and incomplete performance data, create one reviewable package that shows the plan, calculations, supporting source IDs, proposed action, and approval boundary.

## v0.5 scope

1. Validate a structured JSON campaign brief.
2. Divide the declared budget into experiment envelopes.
3. classify structured creative claims, require declared substantiation for objective product claims, and block high-risk categories with public policy references.
4. Calculate CTR, conversion rate, CPA, and ROAS.
5. Compare only compatible adjacent monthly observations and expose data gaps.
6. Draft bounded rule-based recommendations.
7. Render machine-readable JSON and human-readable Markdown.
8. Select a versioned policy from the declared objective.
9. Reject objective/outcome semantic mismatches.
10. Expose weighted factor evidence and deterministic policy scores.
11. Preserve policy IDs, substantiation IDs, reasons and the checked date in the claim-review output.
12. Bind every releasable claim, headline and message to exact normalized text in the declared review evidence; wording, punctuation or internal-spacing edits and unregistered copy fail closed.

## Acceptance criteria

- invalid relationships and funnel counts are rejected;
- every recommendation points to a performance source ID;
- a prohibited claim blocks recommendation release;
- suggested increases never exceed the declared ceiling or 20%;
- zero-conversion cells never qualify for scaling;
- current and historical periods validate deterministically;
- missing, non-adjacent, and changed-dimension comparisons are warnings rather than invented trends;
- all recommendations require human approval and remain unexecuted;
- revenue, conversion, and lead objectives select different explicit policies;
- lead scoring accepts only `qualified_lead` outcomes;
- every claim decision exposes its category, reason, evidence links and relevant public policy IDs;
- unsupported objective claims and all high-risk guarantee, absolute-safety and health-outcome categories block release;
- changing any reviewed creative's normalized text invalidates its evidence binding and blocks recommendation release;
- the sample can be rebuilt offline with no paid API.

## Out of scope

- real account authentication or platform connectors;
- automatic publishing, bidding, or budget changes;
- causal attribution, forecasting, or statistical significance claims;
- production identity, permissions, persistence, monitoring, and concurrency;
- real customer, creative, transaction, or campaign data.

## Success evidence

For v0.1, success means the example is reproducible, the rules are documented, the tests pass, and the static demo is publicly inspectable. It does not mean commercial or advertising performance has been achieved.
