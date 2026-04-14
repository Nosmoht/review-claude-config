---
name: review-report-contract
description: Canonical review/report contract for all producers and consumers
last_refreshed: 2026-04-03
---

# Review Report Contract

The only normative source for the review/report contract (used by `review-*`, `apply-*-review-findings`, `review-analytics`, `check-repo-health`). Producer-specific behavior and legacy-consumer tolerance stay in individual skills.

## Certificate Shape

Order: `Goal` → `Certificate` → `Strengths` → `[Diagnostics]` → `Recommendations`. Calibration sections may appear between `Certificate` and `Strengths`. Diagnostic sections (e.g., `### Reliability Diagnostics`) may appear between `Strengths` and `Recommendations`.

## Recommendation Block

Heading: `#### N. [Title] (Impact: [High/Medium/Low][, Category: ...][, ID: {finding_id}])`

Required: `Evidence`, `Why it matters`, `Validation`. Optional: `Current`, `Recommended`, `finding_id`.

"Dispatchable" = includes both `Current` and `Recommended` anchors (≡ ESLint `meta.fixable`). "Manual-only" = valid finding without anchors.

## Finding Identity (optional)

`finding_id`: `{checklist_item}:{path}:{dimension}/v1` (e.g. `WS-2:skills/foo/SKILL.md:Clarity/v1`). Non-checklist: `ADHOC:{path}:{dim}:{slug}/v1`. Derived from verdict, not LLM text. Consumers match on `finding_id` when present; fall back to heading parse when absent.

## Report Frontmatter

```yaml
---
generated_by: review-*  # review-skill, review-agent, review-rule, review-mcp-server, review-settings, review-claude-config
schema_version: 1
date: YYYY-MM-DD
target: /absolute/path
baseline_version: YYYY-MM-DD
items_reviewed: N
summary:
  - name: item-name
    type: Skill|Agent|Rule|MCP|Settings
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

Single-item and batch reports share the same schemas. `schema_version` stays `1` unless breaking change.

## Dimensions

Full reports: `clarity`, `completeness`, `prompt_engineering`, `context_engineering`, `goal_alignment`, `safety`, `metadata`. Rules/MCP/Settings: non-applicable → `null`.
