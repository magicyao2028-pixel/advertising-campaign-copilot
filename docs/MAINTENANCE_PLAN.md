# Maintenance Plan

v0.1 is intentionally narrow. The following ten rounds provide visible room for disciplined growth rather than presenting a one-day prototype as a finished platform.

| Round | Planned increment | Status |
| --- | --- | --- |
| M1 | Add multi-period performance history and trend checks | Complete in v0.2 |
| M2 | Add objective-specific scoring and recommendation policies | Complete in v0.3 |
| M3 | Expand creative-claim taxonomy with policy evidence | Planned |
| M4 | Add minimum-sample and experiment-quality checks | Planned |
| M5 | Add an optional grounded model adapter with deterministic fallback | Planned |
| M6 | Add an API boundary, idempotency keys, and contract tests | Planned |
| M7 | Add persistence, audit retention, and role-based approval design | Planned |
| M8 | Add a read-only connector and explicit dry-run mutation package | Planned |
| M9 | Add concurrency controls, observability, and failure recovery | Planned |
| M10 | Prepare a controlled synthetic pilot and evaluation report | Planned |

**Current maintenance count: 2/10.**

Every round should preserve the current tests, add focused tests for the new risk, update the example, and document honest boundaries. A future model adapter must not turn ungrounded text into an executable instruction.
