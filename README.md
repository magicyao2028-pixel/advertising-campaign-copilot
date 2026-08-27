# Advertising Campaign Copilot

An offline, reviewable prototype that turns a structured campaign brief and synthetic multi-period performance data into a campaign plan, metric audit, trend check, evidence-linked creative-claim gate, and bounded optimization recommendations.

**中文介绍：** 面向中小企业广告投放规划与复盘的 AI 应用原型。它将广告需求、创意、预算和模拟投放数据整理成可审核的计划与优化建议；创意声明会按类别检查证据并显示政策依据，高风险或缺少依据的声明会阻断建议发布。所有调整均需人工批准，不连接真实广告账户，不产生真实投放或业绩。

## Why this project exists

Many small teams need a transparent workflow before they need a fully autonomous advertising system. This repository demonstrates how an AI product can preserve evidence, business constraints, approval ownership, and safe execution boundaries.

The business scenario is an internal AI-application exploration for Changsha Shiju Trading Co., Ltd. All names, campaign inputs, performance values, and outputs in the repository are synthetic.

## What v0.6 demonstrates

- structured campaign briefs and explicit KPI targets;
- per-cell budget envelopes and one-variable experiment guidance;
- CTR, CVR, CPA, and ROAS calculations with source identifiers;
- adjacent-period comparisons plus explicit missing, non-adjacent, and incompatible-data warnings;
- a structured creative-claim taxonomy with declared substantiation records;
- dated Google and FTC policy references plus an explicit non-certification boundary;
- fail-safe blocking for unsupported objective claims and high-risk guarantee, safety, or health categories;
- exact evidence binding for every releasable claim, headline, and message so edited or unregistered copy fails closed;
- bounded recommendations: scale candidate, hold and test, or pause and review;
- objective-specific policies with visible factors, weights, thresholds and scores;
- explicit prototype minimum-sample checks for impressions, clicks and conversions; low-information cells cannot qualify for scaling;
- explicit outcome semantics so lead policies cannot silently score purchase events;
- mandatory human approval and zero platform writes;
- governed replay of accepted creative feedback against an isolated campaign copy;
- prioritizes recommendations in a human-review experiment queue without changing budgets or launching experiments;
- exclusion of pending feedback plus an eight-claim evidence index and clean offline trial;
- deterministic tests and a static public demo.

## Quick start

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m campaign_copilot.cli data/sample_campaign.json \
  --json-output examples/campaign_review.json \
  --markdown-output examples/campaign_review.md
campaign-feedback-replay
campaign-trial
```

The package has no runtime dependencies and requires Python 3.10 or later.

The minimum-sample gate is deliberately modest and explicit: 1,000 impressions, 50 clicks and 10 conversions. It is a screening assumption for this portfolio prototype, not a statistical-power, significance or causal-inference claim.

## Workflow

```text
Campaign brief
  -> schema and relationship validation
  -> objective/outcome policy selection
  -> evidence-linked creative claim review
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
- `docs/CREATIVE_CLAIM_POLICY.md`: claim taxonomy, substantiation, and public policy references
- `docs/SECURITY.md`: safety, privacy, and credential policy
- `docs/TRIAL_GUIDE.md`: a 15–20 minute reviewer trial and recovery path
- `docs/MAINTENANCE_PLAN.md`: ten planned maintenance rounds
- `site/`: static demonstration published through GitHub Pages

## Honest boundaries

This is a portfolio prototype, not a production ad-buying system or compliance certification. It does not call an LLM, estimate causal uplift, forecast performance, guarantee results, connect to an ad platform, modify budgets, publish creatives, or store customer data. Policy links were checked on the recorded date and must be refreshed for a real release. Feedback records are synthetic regression evidence, not advertiser, platform, or maintainer feedback. Its claim decisions, period changes, and objective scores are deterministic review aids, not legal advice or proof of causal performance. See [the creative claim policy](docs/CREATIVE_CLAIM_POLICY.md), [objective policies](docs/OBJECTIVE_POLICIES.md), [architecture](docs/ARCHITECTURE.md), [trial guide](docs/TRIAL_GUIDE.md) and [maintenance plan](docs/MAINTENANCE_PLAN.md).

## License

MIT. See [LICENSE](LICENSE).
