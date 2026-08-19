# Reviewer Trial Guide

## Purpose

This 15–20 minute offline trial reviews one synthetic campaign, replays two accepted synthetic creative-feedback cases and proves that high-risk or unsupported claims stop optimization output and platform writes.

## Clean start

```bash
python -m venv .venv
python -m pip install -e .
campaign-trial
```

Expected result: the baseline campaign reaches human review; both feedback cases are blocked; the pending auto-publish suggestion remains excluded; no platform write is executed.

## Failure and recovery

If a feedback replay fails, inspect the feedback ID, target claim and matched policy rule. Do not relabel a high-risk claim, add fabricated substantiation or enable publishing merely to pass the fixture.

## Real-pilot boundary

A real pilot requires current platform and jurisdiction policy review, verified product substantiation, authenticated campaign owners, approved budgets, live-data quality checks and explicit approval before any ad or budget change.
