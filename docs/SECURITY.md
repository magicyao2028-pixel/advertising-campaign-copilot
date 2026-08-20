# Security and Data Policy

## Current posture

- The application runs offline and has no runtime dependencies.
- The repository contains only synthetic campaign and performance data.
- No API token, advertising credential, customer identifier, or payment data is required.
- No platform write, creative publication, or budget mutation is implemented.
- Objective/outcome mismatches are rejected before a recommendation is drafted.
- Policy scores are review evidence only and never authorize an external action.
- Feedback fixtures are synthetic and cannot be presented as advertiser, platform, or maintainer adoption.
- Only explicitly accepted feedback is replayed; replay runs against an isolated copy and never mutates the bundled campaign.
- Trial and feedback commands write local reports only and preserve zero platform writes.
- The content-binding fail-safe deliberately blocks every unregistered or edited headline, message and descriptive claim, including harmless edits; this is a documented safety tradeoff, not a semantic compliance classifier.

## Safe-use rules

1. Do not replace the sample with confidential exports in a public clone.
2. Keep secrets in an ignored environment file if future adapters require them.
3. Default every future connector to read-only or dry-run.
4. Require authenticated human approval for any proposed external mutation.
5. Log the decision, evidence version, approver, and connector response.

## Reporting a vulnerability

Open a private GitHub security advisory if available. Do not include real credentials or customer data in a public issue.

## Not yet production-ready

The prototype has no authentication, authorization, encrypted persistence, rate limiting, dependency scanning, incident response, or privacy-retention controls. These omissions are explicit and block production use.
