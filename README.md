# Advertising Campaign Copilot

An offline, reviewable prototype that turns a structured campaign brief and synthetic performance data into a campaign plan, metric audit, creative-claim gate, and bounded optimization recommendations.

**中文介绍：** 面向中小企业广告投放规划与复盘的 AI 应用原型。它将广告需求、创意、预算和模拟投放数据整理成可审核的计划与优化建议；所有调整均需人工批准，不连接真实广告账户，不产生真实投放或业绩。

## Why this project exists

Many small teams need a transparent workflow before they need a fully autonomous advertising system. This repository demonstrates how an AI product can preserve evidence, business constraints, approval ownership, and safe execution boundaries.

The business scenario is an internal AI-application exploration for Changsha Shiju Trading Co., Ltd. All names, campaign inputs, performance values, and outputs in the repository are synthetic.

## What v0.1 demonstrates

- structured campaign briefs and explicit KPI targets;
- per-cell budget envelopes and one-variable experiment guidance;
- CTR, CVR, CPA, and ROAS calculations with source identifiers;
- a basic creative-claim release gate;
- bounded recommendations: scale candidate, hold and test, or pause and review;
- mandatory human approval and zero platform writes;
- deterministic tests and a static public demo.

## Quick start

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m campaign_copilot.cli data/sample_campaign.json \
  --json-output examples/campaign_review.json \
  --markdown-output examples/campaign_review.md
```

The package has no runtime dependencies and requires Python 3.10 or later.

## Workflow

```text
Campaign brief
  -> schema and relationship validation
  -> creative claim review
  -> synthetic metric calculation
  -> bounded recommendation draft
  -> human approval required
  -> no platform write
```

## Repository map

- `src/campaign_copilot/`: validation, review rules, reporting, and CLI
- `data/sample_campaign.json`: synthetic input package
- `examples/`: reproducible JSON and Markdown outputs
- `docs/PRD.md`: product intent and acceptance criteria
- `docs/ARCHITECTURE.md`: components, data flow, and boundaries
- `docs/OPTIMIZATION_LOGIC.md`: metric and decision rules
- `docs/SECURITY.md`: safety, privacy, and credential policy
- `docs/MAINTENANCE_PLAN.md`: ten planned maintenance rounds
- `site/`: static demonstration published through GitHub Pages

## Honest boundaries

This is a portfolio prototype, not a production ad-buying system. It does not call an LLM, estimate causal uplift, guarantee performance, connect to an ad platform, modify budgets, publish creatives, or store customer data. The deterministic engine is intentionally narrow so its decisions can be inspected and tested. See [the architecture](docs/ARCHITECTURE.md) and [maintenance plan](docs/MAINTENANCE_PLAN.md) for the planned path.

## License

MIT. See [LICENSE](LICENSE).
