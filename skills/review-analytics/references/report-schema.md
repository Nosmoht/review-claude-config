---
name: report-schema
description: Analytics compatibility notes for the canonical review report contract
---

## Canonical Source

The canonical review/report schema is defined in:

- `skills/review-claude-config/references/review-report-contract.md`

This file is not an independent schema authority. It exists only to document analytics-specific expectations for consumers of that contract.

## Analytics Expectations

- `review-analytics` reads the frontmatter fields from the canonical contract.
- `type + path` identifies the reviewed artifact.
- `generated_by + type + path` identifies the analytics series so batch and standalone reviews are not merged blindly.
- `name` is display-only.
- If a path disappears and a new path appears, analytics should flag a rename/move candidate instead of silently merging by name.
- Legacy reports may use older heading depth or recommendation shapes. Analytics compatibility is limited to what can be derived from frontmatter plus supported historical layouts.

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
