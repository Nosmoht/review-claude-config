---
name: apply-skill-review-findings
description: >
  Applies findings from a /review-skill report to the reviewed SKILL.md. Use
  after /review-skill on a single skill or when delegated by
  /apply-review-findings. Do NOT use for agent or rule reports.
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

**Resolve report directory:** Load `repo-identification.md` via Glob `**/review-claude-config/references/repo-identification.md` to compute `<repo-slug>` (= `sanitize(basename(CWD))` — lowercase, alphanumeric + hyphens only). The report directory is `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/`.

If `$ARGUMENTS` contains a file path, use it. Otherwise, Glob `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/*-review-skill.md` and select the most recent report by filename timestamp.

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

Confirm via AskUserQuestion (header: "Low-impact findings only"):
- Option 1 label: "Address N low-impact findings" — description: `"Process Low recommendations to reach A-grade"`
- Option 2 label: "Skip" (Recommended) — description: `"Stop — preserve manual-only findings as follow-up items"`

On "Skip": stop after preserving the manual-only findings as follow-up items. On "Address N low-impact findings": promote the Low recommendations into the actionable set and continue to Phase 2.

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

Confirm via AskUserQuestion (header: "Apply findings"):
- Option 1 label: "Apply N findings" (Recommended) — description: `"Process High/Medium recommendations with preview for each"`
- Option 2 label: "Cancel" — description: `"Stop without making changes"`

On "Cancel": stop.

## Phase 3 -- Apply Recommendations

Example flow: Read `skills/review-skill/SKILL.md` -> search for Current text -> found at line 45 -> pre-edit: 128 lines (under 500) -> show preview -> user says "yes" -> Edit applied -> post-edit: frontmatter valid, 128 lines OK.

For each recommendation (High impact first, then Medium):

1. Read the target SKILL.md file at the path from the report's `summary` section.
2. Locate the **Current** text block in the actual file content.
   - If the exact text is not found, show the user the Current text and confirm via AskUserQuestion (header: "Text not found"):
     - Option 1 label: "Skip this recommendation" (Recommended) — description: `"Move to the next recommendation"`
     - Option 2 label: "Identify correct text" — description: `"Describe where the text is so the edit can be applied"`
     On "Skip this recommendation": skip. On "Identify correct text": ask the user to identify the correct text.
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
5. Confirm via AskUserQuestion (header: "Apply: <recommendation title>"):
   - Option 1 label: "Apply this change" (Recommended) — description: `"Edit the file with the recommended replacement"`
   - Option 2 label: "Skip" — description: `"Move to the next recommendation"`
   - Option 3 label: "Stop" — description: `"End processing, keep changes applied so far"`
   On "Apply this change": apply the edit using the Edit tool. On "Skip": move to next. On "Stop": end processing.
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

If Low impact recommendations were set aside in Step 2 and at least one High/Medium change was applied, confirm via AskUserQuestion (header: "Low-impact findings"):
- Option 1 label: "Address N low-impact findings" — description: `"Process remaining Low recommendations to reach A-grade"`
- Option 2 label: "Skip" (Recommended) — description: `"Leave low-impact findings for later"`

On "Address N low-impact findings": loop back to Phase 3 with the Low recommendations. Process through the same preview/confirm/validate pipeline. Append results to the change summary table. On "Skip": note: "N Low impact findings were not applied."

In orchestrated mode, do not prompt — process whatever recommendations the orchestrator sends.
The orchestrator must send only dispatchable recommendations with both `Current` and `Recommended`.

**Regression check (after all edits applied):**

For each modified file, verify that applied changes did not:
1. Remove or weaken existing stop conditions, confirmation gates, or error handling.
2. Add tools to `allowed-tools` not referenced in the workflow body.
3. Remove output format specifications or validation criteria.
4. Push total file line count over 500 lines.

If any regression is detected, confirm via AskUserQuestion (header: "Potential regression detected"):
- Option 1 label: "Review before committing" (Recommended) — description: `"Inspect [file]: [description] before proceeding"`
- Option 2 label: "Proceed anyway" — description: `"Continue to the commit step"`

**Commit with audit-fix chain:**

Read the shared commit conventions (loaded in Phase 1 Step 3).

Extract the timestamp from the report filename (e.g., `2026-03-24T161200` from `2026-03-24T161200-review-skill.md`).

Check whether the review report has been committed: `git log --oneline --all -- <report-path>` via Bash. If the command fails (not a git repo, or other error), warn the user and skip the commit workflow -- edits are already applied. If not committed, tell the user:

Tell the user: "The review report is not yet committed. The audit-fix chain requires committing the report first: `docs(reviews): add <timestamp> review report`"

Confirm via AskUserQuestion (header: "Commit report"):
- Option 1 label: "Commit the report now" (Recommended) — description: `"Stage and commit the review report with docs(reviews): add <timestamp> review report"`
- Option 2 label: "Skip" — description: `"Continue without committing the report"`

On "Commit the report now": stage and commit the report via Bash.

For the fix commit:
- Determine scope from the modified skill name (e.g., `review-skill` if editing `skills/review-skill/SKILL.md`).
- Compose: `fix(<scope>): address findings from <timestamp> review`
- Show the commit message and confirm via AskUserQuestion (header: "Commit changes"):
  - Option 1 label: "Commit these changes" (Recommended) — description: `"Stage and commit: fix(<scope>): address findings from <timestamp> review"`
  - Option 2 label: "Skip" — description: `"Leave changes uncommitted"`
- On "Commit these changes": stage and commit via Bash.

Present final status:
- Files modified
- Commits created (with hashes)
- Recommendations not applied (skipped or stopped)
Then end your response with this menu (substitute `<path>` with the target skill path, `<report-path>` with any other report path if needed):

Present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Verify improvements" (Recommended) — description: `"Run /review-skill <path> to detect cross-dimension regressions"`
- Option 2 label: "Apply findings from another report" — description: `"Provide a report path to apply"`
- Option 3 label: "Done" — description: `"End the workflow"`

On "Verify improvements": invoke `/review-skill` with the skill path. On "Apply findings from another report": ask for the report path, then invoke `/apply-skill-review-findings`. On "Done": acknowledge and stop.

## Hard Rules

- **Edit-only operations.** Never delete files. Never create new files. Only edit existing files.
- **Scope restriction.** Only edit files listed in the review report's `summary` section.
- **Preview before every edit.** Always show current and recommended text before applying.
- **Preserve review context.** Always carry `Evidence`, `Why it matters`, and `Validation` through previews even though `Current`/`Recommended` remain the edit anchors.
- **User confirmation at every stage.** Confirm before starting, before each edit, and before committing.
- **Audit-fix chain.** Always commit the report before committing fixes.
- **Preserve file structure.** Edits replace text blocks only. Never rewrite entire files.
- **High/Medium first.** Always process High and Medium recommendations before Low. Low impact recommendations are only offered after High/Medium are resolved, or when no High/Medium exist.
