# Changelog

## 1.0.0 - 2026-09-04

- added accepted-only synthetic reviewer-feedback replay against experiment review history;
- excluded pending/rejected records and kept approvals, campaign state and platform writes disabled;
- added chronological/reference validation, regression tests and trial evidence.

## 0.8.0 - 2026-09-01

- added a chronological, cell-linked synthetic review-history summary;
- preserved unapplied approvals and zero platform writes while making reviewer feedback auditable;
- added deterministic validation and trial evidence for the review-history boundary.

## 0.7.0 - 2026-08-30

- added a deterministic experiment-review export with action-specific completion criteria;
- preserved human approval, minimum-sample and zero-platform-write boundaries;
- added trial and regression coverage without launching or mutating campaigns.

## 0.6.0 - 2026-08-27

- added a prioritized experiment-review queue derived from bounded recommendations;
- preserved explicit human approval, zero platform writes and no automatic experiment launch;
- added trial and regression evidence for queue ordering and safety boundaries.

## 0.6.0 - 2026-08-24

- Added explicit minimum-sample checks of 1,000 impressions, 50 clicks and 10 conversions to each performance cell.
- Prevented low-information cells from receiving `candidate_scale` even when objective-policy factors pass.
- Added sample-quality details and an honest non-statistical boundary to recommendations and trial reports.
- Added a low-information regression fixture, expanded the evidence index to eight claims, and retained human approval plus zero platform writes.

## 0.5.0 - 2026-08-20

- Added governed replay for accepted creative-feedback records while excluding pending and rejected records.
- Added regression cases proving that guarantees and missing substantiation still block optimization output.
- Added a reviewer trial, seven-claim evidence index, external intake record, and synthetic feedback provenance.
- Preserved human approval and zero platform writes throughout the feedback loop.

## 0.4.0 - 2026-08-16

- Added a structured five-category creative-claim register and deterministic review decisions.
- Required declared substantiation for objective product claims and validated evidence links.
- Blocked performance guarantees, absolute-safety claims, and health outcomes with inspectable policy IDs.
- Added dated Google and FTC public policy references while preserving an explicit non-certification boundary.
- Preserved objective semantics, bounded budget recommendations, human approval, and zero platform writes.
- Hardened the structured register so known high-risk phrases override a misdeclared low-risk category.
- Made the guarantee rule distance-independent so longer grammar cannot bypass a false low-risk declaration.

## 0.3.0 - 2026-08-13

- Added versioned policies for revenue, conversion, and qualified-lead objectives.
- Added explicit objective-to-outcome semantic validation.
- Added weighted, inspectable policy factors and deterministic scores to every recommendation.
- Preserved claim blocking, bounded budget changes, human approval, and zero platform writes.
- Expanded the test suite from 21 to 26 cases and updated reports and the public demo.

## 0.2.0 - 2026-08-10

- Added validated reporting periods and multi-period synthetic performance history.
- Added adjacent-period metric changes with two-source evidence links.
- Added explicit warnings for missing, non-adjacent, and incompatible observations.
- Updated reports, tests, documentation, example output, and the static demo.

## 0.1.0 - 2026-08-08

- Added structured synthetic campaign validation.
- Added creative-claim blocking, budget envelopes, and descriptive metrics.
- Added bounded, evidence-linked recommendations with human approval gates.
- Added offline CLI, tests, documentation, generated examples, and static demo.
