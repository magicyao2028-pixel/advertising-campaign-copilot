# Product Requirements Document

## Product statement

Advertising Campaign Copilot helps a small business team translate a campaign brief and observed performance into a traceable review package before a human makes any advertising decision.

## Target users

- an operations manager planning a campaign;
- a marketing lead reviewing creative and budget choices;
- a product or technology partner validating an AI-assisted workflow.

## Primary job to be done

When a team has a campaign objective, several creatives, and incomplete performance data, create one reviewable package that shows the plan, calculations, supporting source IDs, proposed action, and approval boundary.

## v0.1 scope

1. Validate a structured JSON campaign brief.
2. Divide the declared budget into experiment envelopes.
3. flag a small set of prohibited creative claims.
4. Calculate CTR, conversion rate, CPA, and ROAS.
5. Draft bounded rule-based recommendations.
6. Render machine-readable JSON and human-readable Markdown.

## Acceptance criteria

- invalid relationships and funnel counts are rejected;
- every recommendation points to a performance source ID;
- a prohibited claim blocks recommendation release;
- suggested increases never exceed the declared ceiling or 20%;
- zero-conversion cells never qualify for scaling;
- all recommendations require human approval and remain unexecuted;
- the sample can be rebuilt offline with no paid API.

## Out of scope

- real account authentication or platform connectors;
- automatic publishing, bidding, or budget changes;
- causal attribution, forecasting, or statistical significance claims;
- production identity, permissions, persistence, monitoring, and concurrency;
- real customer, creative, transaction, or campaign data.

## Success evidence

For v0.1, success means the example is reproducible, the rules are documented, the tests pass, and the static demo is publicly inspectable. It does not mean commercial or advertising performance has been achieved.
