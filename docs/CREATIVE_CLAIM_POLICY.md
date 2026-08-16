# Creative Claim Policy

## Purpose

v0.4 converts the earlier phrase list into an inspectable claim register. Each structured claim has a category, evidence links and a deterministic release decision. The result is a screening package for a human reviewer, not a platform-policy certification.

## Taxonomy

| Category | Prototype decision | Evidence rule |
| --- | --- | --- |
| `descriptive` | allow for human review | no substantiation required by this narrow rule |
| `objective_product_claim` | allow only with declared substantiation | at least one `product_substantiation` record |
| `performance_guarantee` | block | cannot be released by adding a local attachment |
| `absolute_safety` | block | cannot be released by adding a local attachment |
| `health_outcome` | block | outside this prototype's safe release scope |

The free-text fallback still catches four known phrases when they appear outside the structured claim register. That fallback is deliberately narrow and is not a complete policy classifier.

## Public policy references

- `GOOGLE-UNRELIABLE-CLAIMS`: [Google Ads - Unreliable claims](https://support.google.com/adspolicy/answer/15936857?hl=en), checked 2026-08-16.
- `FTC-AD-SUBSTANTIATION`: [FTC Advertising FAQ's: A Guide for Small Business](https://www.ftc.gov/business-guidance/resources/advertising-faqs-guide-small-business), checked 2026-08-16.
- `FTC-HEALTH-CLAIMS`: [FTC Health Products Compliance Guidance](https://www.ftc.gov/business-guidance/resources/health-products-compliance-guidance), checked 2026-08-16.

References explain why the prototype asks for substantiation or blocks high-risk categories. They do not prove compliance in a particular country, platform, product category or campaign date. A real release must refresh current platform rules and obtain qualified legal or policy review where appropriate.

## Safe failure behavior

- Any blocked claim prevents all optimization recommendations from being released.
- Known high-risk phrases override a falsely declared `descriptive` category and record the override.
- An objective product claim with no declared substantiation is blocked.
- Unknown evidence IDs fail input validation.
- Human approval remains required after a claim passes the screening rules.
- No ad, budget or creative is published by the program.
