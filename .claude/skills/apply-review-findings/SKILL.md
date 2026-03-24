---
name: apply-review-findings
description: >
  Apply recommendations from a review-claude-config report to the reviewed
  files. Parses High and Medium impact findings, previews each change, and
  commits with audit-fix chain convention linking fixes back to the review
  timestamp. Use after running /review-claude-config to act on findings.
argument-hint: "[report-path]"
allowed-tools: Read, Edit, Glob, Bash
disable-model-invocation: true
---

# Apply Review Findings

You are a code editor applying structured review recommendations. Your job is to faithfully translate review findings into file edits, preserving the audit-fix traceability chain.

## Workflow

### 1. Locate the review report

If `$ARGUMENTS` contains a file path, use it. Otherwise, Glob `.claude/reviews/*-review-claude-config.md` and select the most recent report by filename timestamp.

Read the report file. If the file does not exist or is not a review-claude-config report (check `generated_by` in frontmatter), report the error and stop.

### 2. Parse recommendations

Extract the YAML frontmatter to get: `date`, `target`, and `summary` (list of items with paths and grades).

Parse the report body for recommendation sections. Each recommendation follows this pattern:
```
#### N. Title (Impact: High/Medium/Low)

[Description]

**Current:**
```[code block]```

**Recommended:**
```[code block]```
```

Filter to **High and Medium impact only**. Discard Low impact recommendations.

If no High or Medium recommendations are found, tell the user: "No actionable findings — all recommendations are Low impact." Stop.

### 3. Present summary

Show a summary table of all actionable findings before making any changes:

```
## Actionable Findings

| # | Item | Recommendation | Impact | File |
|---|------|----------------|--------|------|
| 1 | review-claude-config | Add confirmation gate | Medium | .claude/skills/review-claude-config/SKILL.md |
```

Ask: "Proceed with applying these findings? (yes/no)"
If no, stop.

### 4. Apply recommendations one by one

For each recommendation (High impact first, then Medium):

1. Read the target file at the path from the report's `summary` section.
2. Locate the **Current** text block in the actual file content.
   - If the exact text is not found, the file may have changed since the review. Show the user the Current text from the report and ask: "This text was not found in the file. Skip this recommendation? (yes/no)" If yes, skip. If no, ask the user to identify the correct text to replace.
3. Show the user:
   - File path
   - Current text (from the actual file)
   - Recommended replacement (from the report)
4. Ask: "Apply this change? (yes/skip/stop)"
   - **yes** — Apply the edit using the Edit tool.
   - **skip** — Move to the next recommendation.
   - **stop** — End processing. Present summary of changes made so far.

### 5. Present change summary

After processing all recommendations (or after user says "stop"), present:

```
## Changes Applied

| # | Item | Recommendation | Status |
|---|------|----------------|--------|
| 1 | review-claude-config | Add confirmation gate | Applied |
| 2 | refresh-baseline | Token verification | Skipped |

Applied: N / Total: M
```

If no changes were applied, stop here.

### 6. Commit with audit-fix chain

Read `references/commit-conventions.md` for the commit format.

Extract the timestamp from the report filename (e.g., `2026-03-24T161200` from `2026-03-24T161200-review-claude-config.md`).

Check whether the review report itself has been committed. Run `git log --oneline --all -- <report-path>` via Bash. If the report is not yet committed, tell the user:

"The review report is not yet committed. The audit-fix chain convention requires committing the report first:
`docs(reviews): add <timestamp> review report`

Commit the report now? (yes/no)"

If yes, stage and commit the report via Bash.

Then, for the fix commit:
- Determine scope from the modified files. If all edits are within one skill directory, use that skill's name (e.g., `review-skill`). If multiple skills were edited, use comma-separated scopes.
- Compose the commit message: `fix(<scope>): address findings from <timestamp> review`
- Show the commit message and ask: "Commit these changes? (yes/no)"
- If yes, stage the modified files and commit via Bash.
- If no, tell the user the changes are applied but uncommitted.

### 7. Report

Present the final status:
- Files modified
- Commits created (with hashes)
- Recommendations not applied (skipped or stopped)
- Suggest: "Run `/review-claude-config` again to verify improvements."

## Hard Rules

- **Edit-only operations.** Never delete files. Never create new files. Only edit existing files.
- **Scope restriction.** Only edit files listed in the review report's `summary` section. Never edit files outside the report's scope.
- **Preview before every edit.** Always show the current and recommended text before applying.
- **User confirmation at every stage.** Confirm before starting, before each edit, and before committing.
- **Audit-fix chain.** Always commit the report before committing fixes. Use the report timestamp in the fix commit message.
- **Preserve file structure.** Edits replace text blocks only. Never rewrite entire files.
- **No Low impact changes.** Only apply High and Medium recommendations. Users who want Low impact changes should apply them manually.
