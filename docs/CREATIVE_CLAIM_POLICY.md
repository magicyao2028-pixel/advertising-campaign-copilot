# Creative Claim Policy

## Purpose

v0.4 converts the earlier phrase list into an inspectable claim register. Each structured claim has a category, evidence links and a deterministic release decision. The result is a screening package for a human reviewer, not a platform-policy certification.

The v0.5 fail-safe is intentionally conservative and content-bound. Every headline, message and releasable claim must exactly match normalized text listed by a declared evidence record. Leading and trailing whitespace is removed during input normalization; every other text change invalidates the binding and blocks release until a human updates the evidence package. Metric and phrase rules remain useful explanations for known high-risk language, but release safety no longer depends on an open-ended synonym or metric dictionary. Reporting, simulation or conditional text can still be over-blocked. A human reviewer must update the reviewed-text registry instead of weakening the release gate.

## Taxonomy

| Category | Prototype decision | Evidence rule |
| --- | --- | --- |
| `descriptive` | allow only when content-bound | exact text in a referenced `product_substantiation` record |
| `objective_product_claim` | allow only with declared substantiation | exact text in a referenced `product_substantiation` record |
| `performance_guarantee` | block | cannot be released by adding a local attachment |
| `absolute_safety` | block | cannot be released by adding a local attachment |
| `health_outcome` | block | outside this prototype's safe release scope |

The free-text fallback uses versioned concept-pattern rules for performance guarantees, absolute-safety language, and instant health outcomes. Any `guarantee` word-family match is fail-safe blocked regardless of distance from an outcome phrase or the declared category. Separately, an unregistered headline or message receives `CLAIM-UNREGISTERED-CREATIVE-SURFACE`; an unbound structured description also blocks. The patterns explain familiar cases, while exact content binding closes the unknown-vocabulary path. This remains a review workflow, not a semantic or legal classifier.

## Public policy references

- `GOOGLE-UNRELIABLE-CLAIMS`: [Google Ads - Unreliable claims](https://support.google.com/adspolicy/answer/15936857?hl=en), checked 2026-08-16.
- `FTC-AD-SUBSTANTIATION`: [FTC Advertising FAQ's: A Guide for Small Business](https://www.ftc.gov/business-guidance/resources/advertising-faqs-guide-small-business), checked 2026-08-16.
- `FTC-HEALTH-CLAIMS`: [FTC Health Products Compliance Guidance](https://www.ftc.gov/business-guidance/resources/health-products-compliance-guidance), checked 2026-08-16.

References explain why the prototype asks for substantiation or blocks high-risk categories. They do not prove compliance in a particular country, platform, product category or campaign date. A real release must refresh current platform rules and obtain qualified legal or policy review where appropriate.

## Safe failure behavior

- Any blocked claim prevents all optimization recommendations from being released.
- Known high-risk phrases override a falsely declared `descriptive` category and record the override.
- A descriptive or objective product claim whose exact text is absent from its referenced evidence is blocked.
- Any headline or message absent from the normalized reviewed-text registry is blocked, including harmless wording or punctuation edits, until re-reviewed.
- Unknown evidence IDs fail input validation.
- Human approval remains required after a claim passes the screening rules.
- No ad, budget or creative is published by the program.
