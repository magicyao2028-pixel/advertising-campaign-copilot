# Handoff

## Current state

- Release: v0.1.0
- Maintenance rounds completed: 0/10
- Runtime: offline Python 3.10+, no dependencies
- Data: synthetic only
- External writes: none

## Reproduce

```bash
python -m unittest discover -s tests -v
python -m campaign_copilot.cli data/sample_campaign.json \
  --json-output examples/campaign_review.json \
  --markdown-output examples/campaign_review.md
```

## Next authorized maintenance round

M1: accept multiple dated observations per campaign cell, calculate transparent period-over-period changes, and warn when the latest period is missing or not comparable. Do not add forecasting, statistical significance, a database, or a live connector in M1.

## Completion gate for M1

- dated observations validate deterministically;
- comparable-period logic is documented;
- missing or incompatible periods produce explicit warnings;
- examples and the static site show the new trace;
- old and new tests pass;
- maintenance count advances to 1/10 only after publication is verified.
