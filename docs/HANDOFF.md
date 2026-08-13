# Handoff

## Current state

- Release: v0.3.0
- Maintenance rounds completed: 2/10
- M2: objective-specific policies, explicit outcome semantics, and inspectable weighted scores
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

## M2 evidence

- revenue uses ROAS plus a CPA guardrail under `OBJ-REV-001`;
- conversions use CPA plus a recorded-conversion gate under `OBJ-CONV-001`;
- leads require `qualified_lead` outcome semantics under `OBJ-LEAD-001`;
- each recommendation exposes factor weights, observed values, thresholds, pass/fail states, and total score;
- all existing period warnings, claim gates, human approval, and zero-write boundaries remain active.

## Next authorized maintenance round

M3: expand the creative-claim taxonomy with policy evidence. Preserve objective policies, period comparability, approval, and execution boundaries. Do not add forecasting, persistence, or a live connector in M3.

## Completion gate for M3

- claim categories and policy references are explicit and tested;
- unsupported or high-risk claims fail safely;
- examples and the static site show why a claim was blocked;
- old and new tests pass;
- maintenance count advances to 3/10 only after publication is verified.
