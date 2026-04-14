# review-analytics

Parse accumulated review reports, compute grade trajectories per item and dimension, and detect regressions. Pure read-only analytics over the review history, using the shared review report contract as the schema authority.

## Overview

| Property | Value |
|----------|-------|
| **Name** | review-analytics |
| **Location** | `skills/review-analytics/SKILL.md` |
| **Type** | Maintenance (Analytics) |
| **Allowed Tools** | Read, Glob |
| **Argument Hint** | `[folder] [--validation]` |
| **Mode** | Standalone only |
| **Research Behavior** | None (no web research) |

## Purpose

The skill answers three questions about a portfolio's quality evolution over time:

1. **Trajectory** -- Is each reviewed item improving, stable, or regressing across review cycles?
2. **Dimension trends** -- Which scoring dimensions are strengthening or weakening across the portfolio?
3. **Alerts** -- Are there regressions, disappearances, or systemic issues that need attention?

It operates exclusively on the structured YAML frontmatter defined by `review-claude-config/references/review-report-contract.md` for review reports already written to `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/`. The skill never modifies any file.

### Step 1: Discover review reports

Glob for `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/*-review-*.md` where `<target>` is the folder argument (defaults to the current project root). Sort results by filename -- because filenames are ISO-timestamped (`YYYY-MM-DDTHHMMSS-...`), lexicographic order equals chronological order. Then keep only reports whose `generated_by` is one of `review-claude-config`, `review-skill`, `review-agent`, or `review-rule`.

If `--validation` is present, first filter to supported, parseable reports, then keep only the 10 most recent of that filtered set and switch to the bounded validation summary described below.

Apply the report-count checks after this filtering/capping step as well:
- 0 supported, parseable reports -> stop
- 1 supported, parseable report -> single-report summary path

| Condition | Behavior |
|-----------|----------|
| No reports found | Output a message and stop |
| Exactly 1 matching report | Continue to parsing; single-report handling happens only after supported/parseable filtering |
| 2+ reports | Continue to full workflow |

### Step 2: Parse report frontmatter

Locate the canonical review contract first. Use `references/report-schema.md` only for analytics-specific compatibility notes. For each discovered report, extract:

| Field | Description |
|-------|-------------|
| `date` | Report timestamp |
| `items_reviewed` | Count of items in the report |
| `summary` | Array of item entries |

Each entry in the `summary` array contains:

| Field | Description |
|-------|-------------|
| `name` | Display label for the item |
| `type` | Item type (skill, agent, rule) |
| `path` | Canonical artifact key from the report summary |
| `overall` | Overall letter grade (A-F) |
| `score` | Numeric weighted score |
| 7 dimension grades | One grade per dimension (Clarity, Completeness, etc.) |

Malformed reports (missing required fields, unparseable YAML) are skipped with a warning message listing the filename and the reason for skipping. Processing continues with the remaining valid reports.

### Step 3: Build time series

Group items by artifact identity `type + path`, but partition time series by `generated_by + type + path`. This prevents batch and standalone reviews of the same file from being merged into one misleading series.

Handle lifecycle events:

| Event | Detection | Label |
|-------|-----------|-------|
| **New item** | Path appears for the first time in a report | "New" |
| **Removed item** | Path present in older report(s), absent in the latest report | "Removed" |
| **Rename/move candidate** | A path disappears and a new path appears for the same producer and type in the same report transition | Flagged for review |

### Step 4: Compute trajectories

**Per-item overall trajectory** -- Compare the earliest and latest data points for each item:

| Trajectory | Condition |
|------------|-----------|
| Improving | Latest grade > earliest grade, OR numeric score increased by >=5 |
| Stable | Grade unchanged and score variation < 5 across all data points |
| Regressing | Latest grade < previous grade, OR numeric score decreased by >=5 |

Grade comparison order: A > B > C > D > F.

Examples:
- B(82) -> B(86) -> B(81) = **Stable** (grade unchanged, score range < 5)
- B(82) -> A(90) -> B(85) = **Regressing** (latest grade B < previous grade A)

**Per-dimension trends** -- For each of the 7 dimensions, compute the average grade across only the items where that dimension is non-null in the latest report and compare against the average in the earliest report. Rule-only null dimensions are excluded from averages, lowest-item selection, and systemic-regression alerts.

### Step 5: Present analysis

If `--validation` is present, skip the wide trajectory matrix and the full heatmap. Present only a bounded validation summary with:
- analyzed report count
- analyzed series count
- latest regressions
- new items
- removed items

Validation mode is for release/CI checks only. It does not change series partitioning, artifact identity rules, or producer-scoped rename/move semantics.

Output three views in sequence. Keep artifact identity and analytics series identity distinct:
- artifact identity: `type + path`
- analytics series identity: `generated_by + type + path`

**View 1: Grade Trajectories**

```
### Grade Trajectories

| Producer | Item Path | Display Name | [Timestamp 1] | [Timestamp 2] | ... | Trend |
|----------|-----------|--------------|----------------|----------------|-----|-------|
| review-skill | path/to/skill | My Skill | B (82) | B (86) | ... | Stable |
```

One column per report timestamp. Each cell shows `Grade (Score)`. The Trend column shows Improving, Stable, or Regressing. Do not merge batch and standalone producers into one raw trajectory.

**View 2: Dimension Heatmap**

```
### Dimension Heatmap

| Dimension | Avg Grade (Latest) | Lowest Item | Trend vs First |
|-----------|--------------------|-------------|----------------|
| Clarity | A | path/to/weakest | Improving |
```

One row per dimension. Shows the average grade across items where that dimension is non-null in the latest report, identifies the item with the lowest grade in that dimension, and compares against the earliest report's average.

**View 3: Alerts**

```
### Alerts

**Regressions:** [list of items with Regressing trajectory]
**New Items:** [list of items first seen in the latest report]
**Removed Items:** [list of items absent from the latest report]
**Rename/Move Candidates:** [list of suspected renames with old and new paths]
**Systemic Issues:** [dimensions declining across multiple items]
```

Each section is omitted if empty. If all sections are empty, output "No alerts."

### Step 6: Summary

Output a single summary line:

```
Portfolio quality: [Improving|Stable|Declining] -- N items, M reports, X regressions.
```

The overall portfolio status is determined by:

| Status | Condition |
|--------|-----------|
| Improving | More items improving than regressing, no systemic dimension declines |
| Stable | No regressions, no systemic declines |
| Declining | Any regressions or systemic dimension declines present |

The "What's next?" menu appears only when regressions are detected:

1. Run full review -- `/review-claude-config`
2. Done

If no regressions exist, the summary is presented without a menu.

## Hard Rules

- **Read-only.** Never modify any file. This is a pure analytics skill.
- **Handle malformed reports gracefully.** Skip with a warning; never abort the entire analysis because of one bad report.
- **Present all data before conclusions.** The three views come before the summary line.
- **Timestamp sorting is lexicographic.** Rely on the ISO-formatted filenames for chronological ordering.
- **Track by path first, partition by producer.** The canonical artifact identity is `type + path`. The analytics series identity is `generated_by + type + path`. The `name` field is a display label only.
- **Grade comparison order.** A > B > C > D > F. No plus/minus modifiers.

## Reference Files

| File | Purpose |
|------|---------|
| `references/report-schema.md` (own) | Analytics-specific compatibility notes for review reports |

## Interactions

| Direction | Target | Notes |
|-----------|--------|-------|
| Called by | User directly | Standalone invocation |
| Called by | `/review-claude-config` menu | Suggested as a follow-up option |
| May suggest | `/review-claude-config` | Via menu when regressions are detected |
| Shares references with | None | -- |
