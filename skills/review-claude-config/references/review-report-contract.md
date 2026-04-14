---
name: review-report-contract
description: Canonical review/report contract for all producers and consumers
last_refreshed: 2026-04-03
---

# Review Report Contract

Normative source for the review/report contract (`review-*`, `apply-*-review-findings`, `review-analytics`, `check-repo-health`).

## Certificate Shape

Order: `Goal` → `Certificate` → `Strengths` → `[Diagnostics]` → `Recommendations`. Calibration/diagnostic sections may appear between `Certificate` and `Recommendations`.

## Recommendation Block

Heading: `#### N. [Title] (Impact: [High/Medium/Low][, Category: ...][, ID: {finding_id}])`

Required: `Evidence`, `Why it matters`, `Validation`. Optional: `Current`, `Recommended`, `finding_id`.

Dispatchable = both `Current` and `Recommended` present. Manual-only = valid finding without anchors.

## Finding Identity (optional)

`finding_id`: `{checklist_item}:{path}:{dimension}/v1`. Non-checklist: `ADHOC:{path}:{dim}:{slug}/v1`. Consumers match on `finding_id` when present; fall back to heading parse when absent.

## Report Frontmatter

```yaml
---
generated_by: review-*  # review-skill, review-agent, review-rule, review-mcp-server, review-settings, review-claude-config
schema_version: 1
date: YYYY-MM-DD
repo: <slug>                # basename(target_dir)
origin: <git-remote-url>    # Optional
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

`type + path` is the canonical artifact identity; `name` is display-only. A disappearing path + new path is a rename/move candidate, not a silent merge by name. Analytics series identity: `repo + generated_by + type + path`.

## Producer Compatibility

Single-item and batch reports share the same schemas. `schema_version` stays `1` unless breaking change.

## Dimensions

Full reports: `clarity`, `completeness`, `prompt_engineering`, `context_engineering`, `goal_alignment`, `safety`, `metadata`. Rules/MCP/Settings: non-applicable → `null`.
