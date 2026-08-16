# Handoff

## Current state

- Release: v0.4.0
- Maintenance rounds completed: 3/10
- M3: structured claim taxonomy, declared substantiation, public policy references, and fail-safe release blocking
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

## M3 evidence

- revenue uses ROAS plus a CPA guardrail under `OBJ-REV-001`;
- conversions use CPA plus a recorded-conversion gate under `OBJ-CONV-001`;
- leads require `qualified_lead` outcome semantics under `OBJ-LEAD-001`;
- each recommendation exposes factor weights, observed values, thresholds, pass/fail states, and total score;
- all existing period warnings, claim gates, human approval, and zero-write boundaries remain active.
- objective product claims require declared substantiation IDs;
- performance guarantees, absolute-safety claims and health outcomes are blocked with inspectable policy references;
- undeclared high-risk phrases are still caught by a narrow fallback scanner;
- policy references record publisher, URL and checked date, while explicitly avoiding a compliance guarantee.

## Next authorized maintenance round

M4: add minimum-sample and experiment-quality checks. Preserve claim policy references, objective policies, period comparability, approval, and execution boundaries.

## Completion gate for M4

- minimum-sample assumptions are explicit and tested;
- low-information cells cannot qualify for scaling;
- old and new tests pass and the maintenance count advances only after publication is verified.
