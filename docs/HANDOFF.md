# Handoff

## Current state

- Release: v0.2.0
- Maintenance rounds completed: 1/10
- M1: multi-period performance history and transparent trend checks
- Runtime: offline Python 3.10+, no runtime dependencies
- Data: synthetic only
- External writes: none

## Reproduce

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m campaign_copilot.cli data/sample_campaign.json \
  --json-output examples/campaign_review.json \
  --markdown-output examples/campaign_review.md
```

## M1 evidence

- current observations are tied to a declared `reporting_period`;
- history must be earlier and cell-period/source identities are unique;
- only adjacent monthly records with unchanged dimensions are compared;
- no-prior, missing-latest, period-gap, and changed-dimension cases are explicit warnings;
- period changes cite both source observations and remain descriptive.

## Next authorized maintenance round

M2: make recommendation scoring depend on the declared campaign objective while preserving the current approval and execution boundaries. Do not add an LLM, forecasting, persistence, or a live connector in M2.

## Completion gate for M2

- objective-specific policies are explicit and tested;
- identical evidence produces deterministic decisions;
- unsupported objectives fail safely;
- examples and the static site show why a policy was selected;
- old and new tests pass;
- maintenance count advances to 2/10 only after publication is verified.
