# Architecture

## System context

The prototype is a local decision-support workflow. A human supplies a synthetic JSON brief; the application produces a report for human review. There is no external model, database, ad platform, or write-capable connector.

```text
JSON brief
  -> CampaignBrief validation
  -> objective policy selection and scoring
  -> structured claim taxonomy + exact-text evidence binding + policy-reference gate
  -> metric engine
  -> adjacent-period comparability check
  -> recommendation rules
  -> JSON + Markdown reports
  -> human decision
```

## Components

| Component | Responsibility |
| --- | --- |
| `models.py` | Parse types and validate identities, relationships, budget, and funnel counts |
| `objective_policies.py` | Bind objectives to outcome semantics, weighted factors, and scale thresholds |
| `claim_policies.py` | Apply category decisions, require exact-text evidence binding, and expose dated public policy references |
| `copilot.py` | Review claims, calculate metrics and period changes, draft bounded recommendations, emit trace |
| `report.py` | Render a decision-readable Markdown report with evidence IDs |
| `cli.py` | Provide a reproducible local entry point and write output artifacts |

## Agent boundary

The word *copilot* describes a reviewable application workflow. v0.5 uses deterministic rules rather than an autonomous or LLM-based agent. The trace makes the workflow stages visible, while the governance object makes the execution boundary machine-readable.

## Data boundary

- inputs are local and synthetic;
- no network request is performed by the application;
- no credentials are required;
- outputs contain recommendations, not commands;
- `platform_write_executed` is always `false` in v0.5;
- headlines, messages and releasable claims must exactly match normalized text in a declared evidence record; leading/trailing whitespace is ignored, while other edits require a new human-reviewed binding;
- policy URLs are provenance for reviewer inspection, not a claim that the offline application continuously monitors platform rules;
- only adjacent monthly observations with unchanged channel and creative are compared;
- missing or incompatible observations remain visible as warnings instead of being silently interpolated.

## Production gaps

Before a controlled pilot, the product would need identity and role controls, encrypted persistence, audit retention, policy versioning, robust claim review, statistical experiment checks, monitoring, retry/idempotency design, and a connector that remains dry-run by default.
