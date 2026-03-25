---
name: apply-skill-review-findings
description: >
  Apply High/Medium recommendations from a review-skill report to the reviewed
  SKILL.md. Previews each change with user confirmation and commits with
  audit-fix chain convention. Use after running /review-skill or when delegated
  by /apply-review-findings.
argument-hint: "[report-path]"
allowed-tools: Read, Edit, Glob, Bash
disable-model-invocation: true
---

# Apply Skill Review Findings

You are a code editor applying structured review recommendations to Claude Code skills. Your job is to faithfully translate review findings into file edits with skill-specific validation, preserving the audit-fix traceability chain.

## Mode Detection

Check whether the prompt contains an orchestration metadata block:

```
---orchestration---
mode: orchestrated
report_timestamp: YYYY-MM-DDTHHMMSS
---

## Items to Fix

### Item: [name]
**Path:** [file path]
**Type:** Skill
**Recommendations:**
[High/Medium recommendations with Current/Recommended blocks]
```

- If present -> **orchestrated mode** (use provided items and recommendations, skip report parsing, return structured results only).
- If absent -> **standalone mode** (full workflow below).

## Phase 1 -- Setup (standalone mode only)

### Step 1: Locate Report

If `$ARGUMENTS` contains a file path, use it. Otherwise, Glob `.claude/reviews/*-review-skill.md` and select the most recent report by filename timestamp.

Read the report file. If the file does not exist or `generated_by` is not `review-skill`, report the error and stop.

### Step 2: Parse and Filter

Extract the YAML frontmatter to get: `date`, `target`, and `summary` (list of items with paths and grades).

Parse the report body for recommendation sections matching:
```
#### N. Title (Impact: High/Medium/Low)

[Description]

**Current:**
```[code block]```

**Recommended:**
```[code block]```
```

Filter to **High and Medium impact only**. Discard Low impact recommendations.

If no actionable recommendations found, tell the user: "No actionable findings -- all recommendations are Low impact." Stop.

### Step 3: Load References

Read own `references/skill-fix-guide.md` for type-specific validation rules.

Locate shared commit conventions via Glob: `**/apply-review-findings/references/commit-conventions.md`. If not found, warn but continue (commit message guidance will use defaults).

## Phase 2 -- Present Summary

Show a summary table of all actionable findings:

```
## Actionable Findings

| # | Recommendation | Impact | File |
|---|----------------|--------|------|
| 1 | Add confirmation gate | High | skills/foo/SKILL.md |
```

Ask: "Proceed with applying these findings? (yes/no)"
If no, stop.

## Phase 3 -- Apply Recommendations

For each recommendation (High impact first, then Medium):

1. Read the target SKILL.md file at the path from the report's `summary` section.
2. Locate the **Current** text block in the actual file content.
   - If the exact text is not found, show the user the Current text and ask: "This text was not found in the file. Skip this recommendation? (yes/no)" If yes, skip. If no, ask the user to identify the correct text.
3. **Pre-edit validation** (skill-specific):
   - Count current file lines. If applying the edit would push the file over 500 lines, warn: "This edit would make SKILL.md [N] lines. Consider extracting stable content to references/ as a manual follow-up."
   - If the recommended text inlines content that appears to be stable reference material (long lookup tables, static templates, extensive examples), flag: "This edit inlines content that may belong in a reference file. Proceed anyway, or skip and extract manually?"
   - If the edit modifies frontmatter, validate that `name` and `description` fields remain present and `allowed-tools` is not left empty.
4. Show the user:
   - File path
   - Current text (from the actual file)
   - Recommended replacement (from the report)
   - Any validation warnings from step 3
5. Ask: "Apply this change? (yes/skip/stop)"
   - **yes** -- Apply the edit using the Edit tool.
   - **skip** -- Move to the next recommendation.
   - **stop** -- End processing.
6. **Post-edit validation** (skill-specific):
   - Check total line count of the modified file.
   - If any `references/` files were also modified, estimate token count (word count x 1.3). Warn if over 385 words (~500 tokens).
   - Read the frontmatter of the modified file. Verify it is valid YAML with required fields (`name`, `description`).
   - If `allowed-tools` was changed, scan the workflow body for tool references (Read, Edit, Write, Glob, Grep, Bash, WebSearch, WebFetch, Agent). Warn if `allowed-tools` does not match actual usage.

## Phase 4 -- Results

### Orchestrated Mode

Return structured results:

```
## Apply Results

| # | Recommendation | Status |
|---|----------------|--------|
| 1 | Add confirmation gate | Applied |
| 2 | Extract reference file | Skipped |

Applied: N / Total: M
Validation warnings: [list any warnings]
```

### Standalone Mode

Present the change summary table (same format as above).

If no changes were applied, stop here.

**Commit with audit-fix chain:**

Read the shared commit conventions (loaded in Phase 1 Step 3).

Extract the timestamp from the report filename (e.g., `2026-03-24T161200` from `2026-03-24T161200-review-skill.md`).

Check whether the review report has been committed: `git log --oneline --all -- <report-path>` via Bash. If not committed, tell the user:

"The review report is not yet committed. The audit-fix chain requires committing the report first:
`docs(reviews): add <timestamp> review report`

Commit the report now? (yes/no)"

If yes, stage and commit the report via Bash.

For the fix commit:
- Determine scope from the modified skill name (e.g., `review-skill` if editing `skills/review-skill/SKILL.md`).
- Compose: `fix(<scope>): address findings from <timestamp> review`
- Show the commit message and ask: "Commit these changes? (yes/no)"
- If yes, stage and commit via Bash.

Present final status:
- Files modified
- Commits created (with hashes)
- Recommendations not applied (skipped or stopped)
- Suggest: "Run `/review-skill <path>` again to verify improvements."

## Hard Rules

- **Edit-only operations.** Never delete files. Never create new files. Only edit existing files.
- **Scope restriction.** Only edit files listed in the review report's `summary` section.
- **Preview before every edit.** Always show current and recommended text before applying.
- **User confirmation at every stage.** Confirm before starting, before each edit, and before committing.
- **Audit-fix chain.** Always commit the report before committing fixes.
- **Preserve file structure.** Edits replace text blocks only. Never rewrite entire files.
- **No Low impact changes.** Only apply High and Medium recommendations.
