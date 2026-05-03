---
name: review-analytics
description: >
  Parses accumulated review reports, computes grade trajectories, and detects
  regressions. Use to 'track review results', 'show quality trends', or
  'analyze review history'. Do NOT use for freshness or integrity — use
  /check-repo-health.
argument-hint: "[folder] [--validation]"
allowed-tools: Read, Glob
---

# Review Analytics

You are a quality analyst tracking skill grades over time. Your job is to surface trends, regressions, and improvements from the review report archive.

## Workflow

### 1. Discover review reports

If `$ARGUMENTS` contains the standalone token `--validation`, set `validation_mode = true` and remove that token from the argument string. Use the remaining argument text as the target folder.

If no target folder remains, use the current working directory.

**Resolve report directory:** Load `repo-identification.md` via Glob `**/review-claude-config/references/repo-identification.md` to compute `<repo-slug>` (= `sanitize(basename(target_dir))` — lowercase, alphanumeric + hyphens only). The report directory is `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`.

Glob `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/*-review-*.md` to find all review reports. Sort by filename (timestamps sort lexicographically).

When no target is specified (CWD mode), also support cross-repo analysis: Glob `${HOME}/.claude/plugins/data/claude-config/reports/**/*-review-*.md` to discover reports across all repos.

If no reports are found, tell the user: "No review reports found in `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`." Stop.

### 2. Parse report frontmatter

Locate the canonical review contract via Glob: `**/review-claude-config/references/review-report-contract.md`.
- Prefer `skills/review-claude-config/references/review-report-contract.md` when present.
- Otherwise use the sibling `.claude/skills/review-claude-config/references/review-report-contract.md` copy.

Read that file for the forward-looking frontmatter and identity contract. Use `skills/review-claude-config/references/report-schema.md` for analytics-specific compatibility notes and producer partition rules.

For each report, read the YAML frontmatter and extract:
- `date` — report date
- `generated_by` — report producer (`review-claude-config`, `review-skill`, `review-agent`, `review-rule`)
- `items_reviewed` — count
- `summary` — array of items with: `name`, `type`, `path`, `overall`, `score`, `clarity`, `completeness`, `prompt_engineering`, `context_engineering`, `goal_alignment`, `safety`, `metadata`

Skip any report whose `generated_by` is not one of the supported review producers above.

Treat `type + path` as the artifact key and `repo + generated_by + type + path` as the series key (where `repo` is the `<repo-slug>` derived from the report's parent directory under `reports/`). Treat `name` as a display label only.

If a report has malformed or missing frontmatter, skip it with a warning: "Skipped report `<filename>`: could not parse frontmatter."

Extract the timestamp from each filename for display (e.g., `2026-03-24T161200`).

If `validation_mode = true`, after filtering unsupported or malformed reports, keep only the 10 most recent supported, parseable reports.

After filtering (and validation-mode capping, if active):
- If no supported, parseable reports remain, tell the user: "No supported review reports found in `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`." Stop.
- If exactly one supported, parseable report remains, present the single-report summary path and note: "Trend analysis requires at least 2 supported review reports." Stop.

### 3. Build time series

For each unique `generated_by + type + path` combination across all reports, build a time series:
- Track the `overall` grade and `score` at each report timestamp.
- Track per-dimension grades: clarity, completeness, prompt_engineering, context_engineering, goal_alignment, safety, metadata.

For Rule reports, `prompt_engineering`, `context_engineering`, `safety`, and `metadata` are `null`. Exclude `null` values from all dimension averages, lowest-item selection, and systemic-regression logic.

Handle items that appear or disappear across reports:
- **New item:** First appearance marked as "New" (no prior data point).
- **Removed item:** Last seen in an older report but absent in the most recent. Marked as "Removed."
- **Rename/move candidate:** A path disappears and a new path appears for the same producer and type in the next report. Flag it as a candidate instead of silently merging by `name`.

### 4. Compute trajectories

For each item, classify its overall trajectory:
- **Improving** — Latest grade is higher than the earliest, OR score increased by ≥5 points.
- **Stable** — Grade unchanged across all reports, AND score variation < 5 points.
- **Regressing** — Latest grade is lower than the previous report, OR score dropped by ≥5 points.

Example: B(82) → B(86) → B(81) is Stable (grade unchanged, variation < 5). B(82) → A(90) → B(85) is Regressing (latest grade lower than previous by ≥1 grade-step or ≥5 score points).

For each dimension, compute the average grade across only the items where that dimension is non-null in the most recent report and compare against the earliest report to determine dimension-level trends.

### 5. Present analysis

If `validation_mode = true`, present only:

```markdown
## Validation Summary

- Mode: validation
- Reports analyzed: M
- Series analyzed: N
- Latest regressions: X
- New items: Y
- Removed items: Z

### Regressions
- ...

### New Items
- ...

### Removed Items
- ...
```

In validation mode:
- do not render the full timestamp-wide trajectory matrix
- do not render the full dimension heatmap table
- keep producer partitioning and path-first identity exactly the same
- omit the follow-up menu

Otherwise present the normal three views below.

Present three views:

**View 1: Grade Trajectories**
```
## Grade Trajectories

| Producer | Item Path | Display Name | [timestamp 1] | [timestamp 2] | ... | Trend |
|----------|-----------|--------------|---------------|---------------|-----|-------|
| review-claude-config | skills/review-claude-config/SKILL.md | review-claude-config | B (85.0) | A (93.5) | ... | Improving |
| review-skill | .claude/skills/refresh-engineering-baseline/SKILL.md | refresh-engineering-baseline | B (82.0) | A (93.1) | ... | Improving |

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

### Rename/Move Candidates
- [old path] → [new path]: same type, path changed, review manually before treating as continuity

### Systemic Issues
- [dimension] regressed across 2+ items simultaneously (possible systemic cause)
```

If no regressions, new items, removed items, or systemic issues exist, show: "No alerts. All items stable or improving."

**View 4: Convergence Analysis**

For each artifact with 2+ reports, analyze finding-level stability:

1. Parse recommendation headings in report bodies for `finding_id` values (format: `{checklist_item}:{path}:{dimension}/v1`). If report bodies are not available (frontmatter-only), skip View 4 with note "Convergence analysis requires report bodies."

2. For the two most recent reports per artifact, classify each finding_id:
   - `recurring` — present in both reports
   - `new` — present only in latest
   - `fixed` — present only in previous

3. For each artifact with 3+ reports, compute max grade variance per dimension (difference between highest and lowest grade across all reports).

4. Convergence verdict per artifact:
   - **Converged** — latest two reports share all High/Medium finding_ids AND max grade variance ≤1 per dimension AND no dimension is null in latest where previous had a non-null grade
   - **Not converged** — any High/Medium finding_id differs OR dimension variance >1 OR null-dimension regression

```
## Convergence Analysis

| Artifact | Reports | Recurring | New | Fixed | Max Grade Var | Converged? |
|----------|---------|-----------|-----|-------|---------------|------------|

[If no artifact has 2+ reports: "Insufficient data for convergence analysis (requires 2+ reports per artifact)."]
```

### 6. Summary

Present a one-line summary:
```
**Portfolio quality: [Improving/Stable/Declining]** — N items across M reports, X regressions detected.
```

Classification:
- **Improving** — Majority of items improving, no regressions in latest report.
- **Stable** — No items regressing, majority stable.
- **Declining** — Any item regressing in the latest report, or systemic dimension regression.

If any regressions were detected (classification is "Declining"), present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Review regressing items" (Recommended) — description: `"Run /review-claude-config to re-evaluate and detect regressions"`
- Option 2 label: "Done" — description: `"End the workflow"`

On "Review regressing items": invoke `/review-claude-config`. On "Done": acknowledge and stop.

If no regressions (classification is "Improving" or "Stable"), skip the menu — just present the dashboard.

## Hard Rules

- **Read-only.** Never modify any file. This is a diagnostic skill only.
- **Handle malformed reports gracefully.** Skip with a warning, never error out.
- **Present all data before conclusions.** Show all four views before the summary.
- **Timestamp sorting is lexicographic.** YYYY-MM-DDTHHMMSS format sorts correctly as strings.
- **Track by path first, partition by producer.** `type + path` identifies the artifact; `generated_by + type + path` identifies the analytics series. `name` is only a label.
- **Grade comparison order.** A > B > C > D > F for trend computation.
