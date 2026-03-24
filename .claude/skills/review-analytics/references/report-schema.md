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
  - name: item-name                      # Kebab-case identifier
    type: Skill                          # Skill or Agent
    path: relative/path/to/SKILL.md      # Relative to target
    overall: B                           # A-F composite grade
    score: 85.0                          # Weighted numeric score (0-100)
    clarity: B                           # Per-dimension grades (A-F)
    completeness: A
    prompt_engineering: B
    context_engineering: B
    goal_alignment: B
    safety: A
    metadata: B
---
```

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
