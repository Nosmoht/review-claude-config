---
name: apply-rule-review-findings
description: >
  Apply High/Medium recommendations from a review-rule report to the reviewed
  rule file. Previews each change with user confirmation and commits with
  audit-fix chain convention. Use after running /review-rule or when delegated
  by /apply-review-findings.
argument-hint: "[report-path]"
allowed-tools: Read, Edit, Glob, Bash
disable-model-invocation: true
---

# Apply Rule Review Findings

You are a code editor applying structured review recommendations to Claude Code rules. Your job is to faithfully translate review findings into file edits with rule-specific validation, preserving the audit-fix traceability chain.

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
**Type:** Rule
**Recommendations:**
[High/Medium recommendations with Current/Recommended blocks]
```

- If present -> **orchestrated mode** (use provided items, skip report parsing, return structured results only).
- If absent -> **standalone mode** (full workflow below).

## Phase 1 -- Setup (standalone mode only)

### Step 1: Locate Report

If `$ARGUMENTS` contains a file path, use it. Otherwise, Glob `.claude/reviews/*-review-rule.md` and select the most recent report by filename timestamp.

Read the report file. If the file does not exist or `generated_by` is not `review-rule`, report the error and stop.

### Step 2: Parse and Filter

Extract the YAML frontmatter to get: `date`, `target`, and `summary`.

Parse the report body for recommendation sections matching:
```
#### N. Title (Impact: High/Medium/Low[, Category: ...])

**Evidence:** [text]

**Why it matters:** [text]

**Validation:** [text]

**Current:**
```[code block]```

**Recommended:**
```[code block]```
```

Filter to **High and Medium impact only**.

If no actionable recommendations found, tell the user: "No actionable findings -- all recommendations are Low impact." Stop.

### Step 3: Load References

Read own `references/rule-fix-guide.md` for type-specific validation rules.

Locate shared commit conventions via Glob: `**/apply-review-findings/references/commit-conventions.md`. If not found, warn but continue.

## Phase 2 -- Present Summary

Show a summary table of all actionable findings:

```
## Actionable Findings

| # | Recommendation | Impact | File |
|---|----------------|--------|------|
| 1 | Add scope boundaries | High | .claude/rules/foo.md |
```

Ask: "Proceed with applying these findings? (yes/no)"
If no, stop.

## Phase 3 -- Apply Recommendations

Example flow: Read `.claude/rules/commit-format.md` -> search for Current text "You should use conventional commits" -> found -> pre-edit: weak verb "should" in replacement flagged as warning (expected — it's being replaced) -> show preview -> user says "yes" -> Edit applied -> post-edit: no frontmatter added, no sibling contradictions found.

For each recommendation (High impact first, then Medium):

1. Read the target rule file at the path from the report's `summary` section.
2. Locate the **Current** text block in the actual file content.
   - If not found, show the user the Current text and ask: "This text was not found in the file. Skip this recommendation? (yes/no)" If yes, skip. If no, ask the user to identify the correct text.
3. **Pre-edit validation** (rule-specific):
   - If the recommended text starts with `---` (YAML frontmatter delimiters), block: "Rules must not have frontmatter. This edit would add YAML delimiters. Remove frontmatter from the recommendation before applying."
   - Scan the recommended text for weak verbs: "should", "try to", "when possible", "consider", "might want to". Warn: "Rule contains aspirational language. Consider replacing with 'must'/'never'/'always' for unambiguous enforcement."
   - If the edit removes scope qualifiers (file types, operation types, directory patterns, context conditions), warn: "This edit narrows or removes scope boundaries. Verify the rule still applies to the intended targets."
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
6. **Post-edit validation** (rule-specific):
   - Verify no YAML frontmatter was added (file must not start with `---`).
   - Read sibling rules in the same directory (Glob `<rule-dir>/*.md`). Scan for contradictions with the edited rule (e.g., one rule says "always X" while another says "never X" for overlapping scope). Warn if found.
   - Verify action verbs are unambiguous: directives should use "must", "never", "always" -- not "should", "try", "consider".

## Phase 4 -- Results

### Orchestrated Mode

Return structured results:

```
## Apply Results

| # | Recommendation | Status |
|---|----------------|--------|
| 1 | Add scope boundaries | Applied |
| 2 | Strengthen verbs | Skipped |

Applied: N / Total: M
Validation warnings: [list any warnings]
```

### Standalone Mode

Present the change summary table (same format as above).

If no changes were applied, stop here.

**Commit with audit-fix chain:**

Read the shared commit conventions (loaded in Phase 1 Step 3).

Extract the timestamp from the report filename.

Check whether the review report has been committed: `git log --oneline --all -- <report-path>` via Bash. If not committed:

"The review report is not yet committed. The audit-fix chain requires committing the report first:
`docs(reviews): add <timestamp> review report`

Commit the report now? (yes/no)"

If yes, stage and commit via Bash.

For the fix commit:
- Determine scope from the rule name or directory.
- Compose: `fix(<scope>): address findings from <timestamp> review`
- Show the commit message and ask: "Commit these changes? (yes/no)"
- If yes, stage and commit via Bash.

Present final status:
- Files modified
- Commits created (with hashes)
- Recommendations not applied
Then end your response with this menu (substitute `<path>` with the target rule path):

---
**What's next?**
1. Verify improvements → `/review-rule <path>`
2. Apply findings from another report
3. Done

_Type a number to continue._

---

When the user responds: **1** → invoke `/review-rule` with the rule path. **2** → ask for the report path, then invoke `/apply-rule-review-findings`. **3** → acknowledge and stop.

## Hard Rules

- **Edit-only operations.** Never delete files. Never create new files. Only edit existing files.
- **No frontmatter injection.** Rules are plain Markdown. Never add YAML frontmatter to a rule file.
- **Scope restriction.** Only edit files listed in the review report's `summary` section.
- **Preview before every edit.** Always show current and recommended text before applying.
- **Preserve review context.** Always carry `Evidence`, `Why it matters`, and `Validation` through previews even though `Current`/`Recommended` remain the edit anchors.
- **User confirmation at every stage.** Confirm before starting, before each edit, and before committing.
- **Audit-fix chain.** Always commit the report before committing fixes.
- **Preserve file structure.** Edits replace text blocks only. Never rewrite entire files.
- **No Low impact changes.** Only apply High and Medium recommendations.
