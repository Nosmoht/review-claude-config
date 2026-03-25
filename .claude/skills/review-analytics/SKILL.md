---
name: review-analytics
description: >
  Parse accumulated review-claude-config reports, compute grade trajectories
  per item and dimension, and detect regressions. Produces a portfolio health
  dashboard showing quality evolution over time. Use to track skill quality
  across review cycles.
argument-hint: "[folder]"
allowed-tools: Read, Glob
---

# Review Analytics

You are a quality analyst tracking skill grades over time. Your job is to surface trends, regressions, and improvements from the review report archive.

## Workflow

### 1. Discover review reports

If `$ARGUMENTS` contains a folder path, use it as the target. Otherwise, use the current working directory.

Glob `<target>/.claude/reviews/*-review-claude-config.md` to find all review reports. Sort by filename (timestamps sort lexicographically).

If no reports are found, tell the user: "No review reports found in `<target>/.claude/reviews/`." Stop.

If only one report is found, present a single-report summary (item grades table) and note: "Trend analysis requires at least 2 reports." Stop.

### 2. Parse report frontmatter

Read `references/report-schema.md` for the expected frontmatter structure.

For each report, read the YAML frontmatter and extract:
- `date` — report date
- `items_reviewed` — count
- `summary` — array of items with: `name`, `type`, `path`, `overall`, `score`, `clarity`, `completeness`, `prompt_engineering`, `context_engineering`, `goal_alignment`, `safety`, `metadata`

If a report has malformed or missing frontmatter, skip it with a warning: "Skipped report `<filename>`: could not parse frontmatter."

Extract the timestamp from each filename for display (e.g., `2026-03-24T161200`).

### 3. Build time series

For each unique item name across all reports, build a time series:
- Track the `overall` grade and `score` at each report timestamp.
- Track per-dimension grades: clarity, completeness, prompt_engineering, context_engineering, goal_alignment, safety, metadata.

Handle items that appear or disappear across reports:
- **New item:** First appearance marked as "New" (no prior data point).
- **Removed item:** Last seen in an older report but absent in the most recent. Marked as "Removed."

### 4. Compute trajectories

For each item, classify its overall trajectory:
- **Improving** — Latest grade is higher than the earliest, OR score increased by ≥5 points.
- **Stable** — Grade unchanged across all reports, AND score variation < 5 points.
- **Regressing** — Latest grade is lower than the previous report, OR score dropped by ≥5 points.

Example: B(82) → B(86) → B(81) is Stable (grade unchanged, variation < 5). B(82) → A(90) → B(85) is Regressing (latest grade lower than previous).

For each dimension, compute the average grade across all items in the most recent report and compare against the earliest report to determine dimension-level trends.

### 5. Present analysis

Present three views:

**View 1: Grade Trajectories**
```
## Grade Trajectories

| Item | [timestamp 1] | [timestamp 2] | ... | Trend |
|------|---------------|---------------|-----|-------|
| review-claude-config | B (85.0) | A (93.5) | ... | Improving |
| refresh-baseline | B (82.0) | A (93.1) | ... | Improving |

Items tracked: N | Reports analyzed: M
```

**View 2: Dimension Heatmap**
```
## Dimension Analysis (Latest Report)

| Dimension | Avg Grade | Lowest Item | Trend vs First |
|-----------|-----------|-------------|----------------|
| Clarity | A | refresh-baseline (A) | Stable |
| Safety | A | review-config (B) | Improving |
```

**View 3: Alerts**
```
## Alerts

### Regressions
- [item]: [dimension] dropped from [grade] to [grade] between [timestamp] and [timestamp]

### New Items (since first report)
- [item]: first appeared in [timestamp] with grade [grade]

### Removed Items
- [item]: last seen in [timestamp] with grade [grade]

### Systemic Issues
- [dimension] regressed across 2+ items simultaneously (possible systemic cause)
```

If no regressions, new items, removed items, or systemic issues exist, show: "No alerts. All items stable or improving."

### 6. Summary

Present a one-line summary:
```
**Portfolio quality: [Improving/Stable/Declining]** — N items across M reports, X regressions detected.
```

Classification:
- **Improving** — Majority of items improving, no regressions in latest report.
- **Stable** — No items regressing, majority stable.
- **Declining** — Any item regressing in the latest report, or systemic dimension regression.

## Hard Rules

- **Read-only.** Never modify any file. This is a diagnostic skill only.
- **Handle malformed reports gracefully.** Skip with a warning, never error out.
- **Present all data before conclusions.** Show the three views before the summary.
- **Timestamp sorting is lexicographic.** YYYY-MM-DDTHHMMSS format sorts correctly as strings.
- **Grade comparison order.** A > B > C > D > F for trend computation.
