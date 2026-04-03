---
name: apply-skill-review-findings
description: >
  Apply recommendations from a review-skill report to the reviewed SKILL.md.
  Processes High/Medium findings first, then optionally offers Low findings
  for A-grade convergence. Previews each change with user confirmation and
  commits with audit-fix chain convention. Use after running /review-skill
  or when delegated by /apply-review-findings.
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

Locate the canonical review contract via Glob: `**/review-claude-config/references/review-report-contract.md`.
- Prefer `skills/review-claude-config/references/review-report-contract.md` when present.
- Otherwise use the sibling `.claude/skills/review-claude-config/references/review-report-contract.md` copy.

Read that file as the forward-looking report contract. Extract the YAML frontmatter to get: `date`, `target`, and `summary` (list of items with paths and grades).

Parse the report body using consumer compatibility rules:
- modern headings may use `####`
- historical headings may use `###`
- historical reports may omit `Evidence`, `Why it matters`, or `Validation`
- only recommendations with both `Current` and `Recommended` are dispatchable for edits

Classify recommendations:
- **Dispatchable**: includes `Current` and `Recommended`
- **Manual-only**: lacks one or both rewrite anchors

Filter dispatchable recommendations into two groups: **High/Medium** recommendations and **Low** recommendations.

If no High/Medium dispatchable recommendations exist:
- if dispatchable Low recommendations exist, skip to **Step 2a: Low Impact Offer**
- otherwise present any manual-only findings as manual follow-up items and stop

### Step 2a: Low Impact Offer

If manual-only findings are present, show them before offering the Low-impact pass. Keep them visible even when dispatchable Low findings exist.

If dispatchable Low recommendations exist, tell the user:

"No High or Medium findings. N Low impact recommendations remain. These are minor improvements that can help reach an A-grade. Address them? (yes/no)"

If no, stop after preserving the manual-only findings as follow-up items. If yes, promote the Low recommendations into the actionable set and continue to Phase 2.

If there are no dispatchable recommendations but manual-only findings exist, present them as manual follow-up items and stop. Do not attempt file edits without rewrite anchors.

### Step 3: Load References

Read own `references/skill-fix-guide.md` for type-specific validation rules.

Locate shared commit conventions via Glob: `**/apply-review-findings/references/commit-conventions.md`. If not found, warn but continue (commit message guidance will use defaults).

## Phase 2 -- Present Summary

Show a summary table of all dispatchable findings:

```
## Actionable Findings

| # | Recommendation | Impact | File |
|---|----------------|--------|------|
| 1 | Add confirmation gate | High | skills/foo/SKILL.md |
```

If manual-only findings are present, also show:

```
## Manual Follow-Up

| # | Recommendation | Impact | Reason |
|---|----------------|--------|--------|
| 1 | Clarify rubric language | Medium | Missing Current/Recommended anchors |
```

Ask: "Proceed with applying these findings? (yes/no)"
If no, stop.

## Phase 3 -- Apply Recommendations

Example flow: Read `skills/review-skill/SKILL.md` -> search for Current text -> found at line 45 -> pre-edit: 128 lines (under 500) -> show preview -> user says "yes" -> Edit applied -> post-edit: frontmatter valid, 128 lines OK.

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
   - Evidence / Why it matters / Validation (from the report)
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

If any manual-only findings were not dispatchable, list them separately as manual follow-up items.

If no changes were applied, stop here.

**Low Impact Pass (standalone mode only):**

If Low impact recommendations were set aside in Step 2 and at least one High/Medium change was applied, ask:

"N Low impact findings remain. Address them to reach A-grade? (yes/no)"

If yes, loop back to Phase 3 with the Low recommendations. Process through the same preview/confirm/validate pipeline. Append results to the change summary table.

If no, note: "N Low impact findings were not applied."

In orchestrated mode, do not prompt — process whatever recommendations the orchestrator sends.
The orchestrator must send only dispatchable recommendations with both `Current` and `Recommended`.

**Commit with audit-fix chain:**

Read the shared commit conventions (loaded in Phase 1 Step 3).

Extract the timestamp from the report filename (e.g., `2026-03-24T161200` from `2026-03-24T161200-review-skill.md`).

Check whether the review report has been committed: `git log --oneline --all -- <report-path>` via Bash. If the command fails (not a git repo, or other error), warn the user and skip the commit workflow -- edits are already applied. If not committed, tell the user:

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
Then end your response with this menu (substitute `<path>` with the target skill path, `<report-path>` with any other report path if needed):

---
**What's next?**
1. Verify improvements → `/review-skill <path>`
2. Apply findings from another report
3. Done

_Type a number to continue._

---

When the user responds: **1** → invoke `/review-skill` with the skill path. **2** → ask for the report path, then invoke `/apply-skill-review-findings`. **3** → acknowledge and stop.

## Hard Rules

- **Edit-only operations.** Never delete files. Never create new files. Only edit existing files.
- **Scope restriction.** Only edit files listed in the review report's `summary` section.
- **Preview before every edit.** Always show current and recommended text before applying.
- **Preserve review context.** Always carry `Evidence`, `Why it matters`, and `Validation` through previews even though `Current`/`Recommended` remain the edit anchors.
- **User confirmation at every stage.** Confirm before starting, before each edit, and before committing.
- **Audit-fix chain.** Always commit the report before committing fixes.
- **Preserve file structure.** Edits replace text blocks only. Never rewrite entire files.
- **High/Medium first.** Always process High and Medium recommendations before Low. Low impact recommendations are only offered after High/Medium are resolved, or when no High/Medium exist.
