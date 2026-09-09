# Handoff

## Current state

- Release: v1.0.0
- Maintenance rounds completed: 10/10
- M4: governed creative-feedback replay, regression evidence, reviewer trial, and seven-claim evidence index
- M5: explicit minimum-sample checks for impressions, clicks and conversions; low-information cells are held for testing even when policy factors would otherwise qualify them for scale; eight-claim evidence index and trial regression.
- M6: deterministic priority-ordered experiment review queue for pause, hold-and-test and candidate-scale outcomes; the queue is advisory and performs no platform write.
- M7: bounded experiment-review export with action completion criteria; approvals remain unapplied and the export performs no platform write.
- M8: chronological, cell-linked synthetic review-history summary; reviewer outcomes remain advisory and perform no platform write.
- M9: accepted-only synthetic reviewer-feedback replay references current review events, excludes pending/rejected records and keeps approvals, campaign state and platform writes disabled.
- M10: accepted feedback is reconciled to current campaign reviews and stale deferred reviews are surfaced at an explicit analysis date; approvals, budget changes, campaign state and platform writes remain disabled.
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
python -m campaign_copilot.creative_feedback_cli
python -m campaign_copilot.trial_cli
```

## M4 evidence

- two accepted synthetic feedback records replay deterministically and remain blocked as expected;
- a pending auto-publish suggestion is visible but excluded from execution;
- replay uses an isolated campaign copy and never alters the source fixture;
- the trial validates external screening, feedback provenance, seven claims, and zero platform writes;
- synthetic labels are explicit and no adoption or commercial result is claimed.

## Preserved M3 evidence

- revenue uses ROAS plus a CPA guardrail under `OBJ-REV-001`;
- conversions use CPA plus a recorded-conversion gate under `OBJ-CONV-001`;
- leads require `qualified_lead` outcome semantics under `OBJ-LEAD-001`;
- each recommendation exposes factor weights, observed values, thresholds, pass/fail states, and total score;
- all existing period warnings, claim gates, human approval, and zero-write boundaries remain active.
- objective product claims require declared substantiation IDs;
- performance guarantees, absolute-safety claims and health outcomes are blocked with inspectable policy references;
- undeclared high-risk phrases are still caught by a narrow fallback scanner;
- policy references record publisher, URL and checked date, while explicitly avoiding a compliance guarantee.

## Maintenance status

The planned ten-round maintenance sequence is complete. Any later model, connector, persistence or live-data work requires a new evidence-backed contract and must preserve claim policies, provenance, period comparability, minimum-sample, approval and execution boundaries.

## Completion record

- each exported checklist has explicit completion criteria and is tested;
- low-information cells remain unable to qualify for scaling;
- old and new tests pass and the maintenance count advances only after publication is verified.
- review history is chronological, references exported cells, and records no applied approval or platform write.
- accepted feedback reconciles only to current review IDs and matching cell/action state;
- one stale deferred synthetic review is visible without changing budget, approval, campaign state or platform state;
- 78 offline tests and the deterministic M10 trial pass.
