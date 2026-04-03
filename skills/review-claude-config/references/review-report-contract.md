---
name: review-report-contract
description: Canonical review/report contract for all producers and consumers
---

# Review Report Contract

The only normative source for the review/report contract (used by `review-*`, `apply-*-review-findings`, `review-analytics`, `check-repo-health`). Producer-specific behavior and legacy-consumer tolerance stay in individual skills.

## Certificate Shape

Order: `Goal` → `Certificate` → `Strengths` → `Recommendations`. Calibration sections may appear between `Certificate` and `Strengths`.

## Recommendation Block

Heading: `#### N. [Title] (Impact: [High/Medium/Low][, Category: ...])`

Required: `Evidence`, `Why it matters`, `Validation`. Optional: `Current`, `Recommended`.

"Dispatchable" = includes both `Current` and `Recommended` anchors (≡ ESLint `meta.fixable`). "Manual-only" = valid finding without anchors.

## Report Frontmatter

```yaml
---
generated_by: review-skill|review-agent|review-rule|review-claude-config
schema_version: 1
date: YYYY-MM-DD
target: /absolute/path
baseline_version: YYYY-MM-DD
items_reviewed: N
summary:
  - name: item-name
    type: Skill|Agent|Rule
    path: relative/path/to/file
    overall: B
    score: 85.0
    clarity: B
    completeness: A
    prompt_engineering: B
    context_engineering: B
    goal_alignment: B
    safety: A
    metadata: B
---
```

## Identity and Tracking

`type + path` is the canonical identity; `name` is display-only. A disappearing path + new path is a rename/move candidate, not a silent merge by name.

## Producer Compatibility

Single-item and batch reports share the same schemas. `generated_by` is producer-specific; `schema_version` stays `1` unless a real breaking change is introduced.

## Dimensions

Full reports: `clarity`, `completeness`, `prompt_engineering`, `context_engineering`, `goal_alignment`, `safety`, `metadata`. Rules: non-applicable → `null`.
