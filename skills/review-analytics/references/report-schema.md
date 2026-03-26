---
name: report-schema
description: Expected YAML frontmatter fields and grade values from review-claude-config reports
---

## Frontmatter Fields

```yaml
---
generated_by: review-claude-config       # Identifies report type
schema_version: 1                        # Schema version for compatibility
date: YYYY-MM-DD                         # Report date
target: /absolute/path                   # Reviewed directory
baseline_version: YYYY-MM-DD            # Engineering baseline version used
items_reviewed: N                        # Count of items
summary:                                 # Array of reviewed items
  - name: item-name                      # Display label for the item
    type: Skill                          # Skill, Agent, or Rule
    path: relative/path/to/SKILL.md      # Canonical tracking key within a report series
    overall: B                           # A-F composite grade
    score: 85.0                          # Weighted numeric score (0-100)
    clarity: B                           # Per-dimension grades (A-F)
    completeness: A
    prompt_engineering: B                # null for Rules
    context_engineering: B               # null for Rules
    goal_alignment: B
    safety: A                            # null for Rules
    metadata: B                          # null for Rules
---
```

Tracking guidance:
- Use `type + path` as the primary portfolio identity across multiple reports.
- Treat `name` as a display label only.
- If a path disappears and a new path appears, report a rename/move candidate instead of silently merging by name.

## Grade Values

| Grade | Score | Meaning |
|-------|-------|---------|
| A | 95 | Excellent — minor or no issues |
| B | 85 | Good — small improvements possible |
| C | 75 | Adequate — notable gaps |
| D | 65 | Below standard — significant issues |
| F | 50 | Failing — fundamental problems |

## Score Thresholds

| Range | Grade |
|-------|-------|
| ≥ 90 | A |
| ≥ 80 | B |
| ≥ 70 | C |
| ≥ 60 | D |
| < 60 | F |
