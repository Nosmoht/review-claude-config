---
name: apply-review-findings
description: >
  Applies findings from a /review-claude-config batch report to all reviewed
  files. Use after /review-claude-config on a folder. Do NOT use for
  single-item reports — use the type-specific /apply-*-review-findings skills.
argument-hint: "[report-path]"
allowed-tools: Agent, Read, Edit, Glob, Bash
disable-model-invocation: true
---

# Apply Review Findings

You are a thin orchestrator that locates review reports, classifies items by type, and delegates fix application to specialized appliers. You handle report parsing, summary presentation, and the commit workflow. The specialized appliers handle type-specific validation and edit application.

## Workflow

### 1. Locate the review report

If `$ARGUMENTS` contains a file path, use it. Otherwise, Glob `.claude/reviews/*-review-*.md` and select the most recent report by filename timestamp.

Read the report file. If the file does not exist or `generated_by` is not one of `review-claude-config`, `review-skill`, `review-agent`, `review-rule`, report the error and stop.

### 2. Parse recommendations

Locate the canonical review contract via Glob: `**/review-claude-config/references/review-report-contract.md`.
- Prefer `skills/review-claude-config/references/review-report-contract.md` when present.
- Otherwise use the sibling `.claude/skills/review-claude-config/references/review-report-contract.md` copy.

Read that file as the forward-looking parse contract. Extract the YAML frontmatter fields defined there: `date`, `target`, `generated_by`, and `summary` (list of items with paths, types, and grades).

Parse the report body using consumer compatibility rules:
- modern recommendation headings may use `####`
- historical recommendation headings may use `###`
- heading: `#### N. Title (Impact: High/Medium/Low[, Category: ...])`
- forward-looking fields: `Evidence`, `Why it matters`, `Validation`
- historical reports may omit one or more of those fields
- optional fields: `Current`, `Recommended`

Example extraction: Given heading "#### 2. Add confirmation gate (Impact: High, Category: Safety)" with Evidence/Why it matters/Validation plus Current/Recommended blocks, extract: title="Add confirmation gate", impact=High, category=Safety, evidence=<text>, why=<text>, validation=<text>, item=<from nearest item heading or frontmatter summary>.

After parsing, classify each recommendation:
- **Dispatchable**: contains both `Current` and `Recommended`, so a specialized applier can attempt an edit
- **Manual-only**: valid review finding, but lacks one or both rewrite anchors

Split dispatchable recommendations into two groups: **High/Medium** and **Low**.

If no dispatchable High or Medium recommendations are found:
- if dispatchable Low recommendations exist, skip to **Step 2a: Low Impact Offer**
- otherwise show any manual-only findings and stop

### 2a. Low Impact Offer

If manual-only findings are present, show them before offering the Low-impact pass. Keep them visible even when dispatchable Low findings exist.

If dispatchable Low recommendations exist, tell the user:

"No High or Medium findings. N Low impact recommendations remain. These are minor improvements that can help reach an A-grade. Address them? (yes/no)"

If no, stop after preserving the manual-only findings as follow-up items. If yes, promote the Low recommendations into the actionable set and continue to Step 3.

Group dispatchable recommendations by item type using the `type` field in the `summary` array (Skill, Agent, or Rule). For single-item reports (`review-skill`, `review-agent`, `review-rule`), there is one group.

If no dispatchable recommendations exist at all, show any manual-only findings and stop.

### 3. Present summary

Show a summary table of all dispatchable findings before making any changes:

```
## Actionable Findings

| # | Item | Type | Recommendation | Impact | File |
|---|------|------|----------------|--------|------|
| 1 | review-skill | Skill | Add confirmation gate | Medium | skills/review-skill/SKILL.md |
| 2 | my-agent | Agent | Fix model selection | High | .claude/agents/my-agent.md |
```

Then show a manual-only summary when applicable:

```
## Manual Follow-Up

| # | Item | Type | Recommendation | Impact | Reason |
|---|------|------|----------------|--------|--------|
| 1 | review-skill | Skill | Clarify workflow policy | Medium | Missing Current/Recommended anchors |
```

If there are no dispatchable findings and at least one manual-only finding, stop after showing the manual follow-up section.

Ask: "Proceed with applying these findings? (yes/no)"
If no, stop.

### 4. Discover specialized appliers

Locate specialized applier skills via Glob:
- `**/apply-skill-review-findings/SKILL.md`
- `**/apply-agent-review-findings/SKILL.md`
- `**/apply-rule-review-findings/SKILL.md`

Read each found SKILL.md and its type-specific fix guide from `references/`.

If a specialized applier is not found for a type present in the report, warn: "No specialized applier found for type [Type]. Skipping [N] recommendations." Continue with other types.

### 5. Dispatch to specialized appliers

Extract the report timestamp from the filename (e.g., `2026-03-24T161200` from `2026-03-24T161200-review-skill.md`).

For each type group (process sequentially -- edits require user confirmation):

Construct the orchestration payload:

```
---orchestration---
mode: orchestrated
report_timestamp: YYYY-MM-DDTHHMMSS
---

## Items to Fix

### Item: [name]
**Path:** [file path]
**Type:** [Skill|Agent|Rule]
**Recommendations:**

#### 1. [Title] (Impact: [High/Medium])
**Evidence:** [text]

**Why it matters:** [text]

**Validation:** [text]

**Current:**
```[code block]```

**Recommended:**
```[code block]```
```

Dispatch an Agent with the specialized SKILL.md content, its fix guide, and the orchestration payload as the prompt. Only dispatch recommendations already classified as dispatchable. Preserve `Evidence`, `Why it matters`, and `Validation` in the payload even though the edit anchors remain `Current`/`Recommended`.

Collect results from each specialized applier.

### 6. Aggregate and present change summary

Combine results from all specialized appliers:

```
## Changes Applied

| # | Item | Type | Recommendation | Status |
|---|------|------|----------------|--------|
| 1 | review-skill | Skill | Add confirmation gate | Applied |
| 2 | my-agent | Agent | Fix model selection | Skipped |

Applied: N / Total: M
```

If no changes were applied, stop here.

### 6a. Low Impact Pass

If Low impact recommendations were set aside in Step 2 and at least one High/Medium change was applied, ask:

"N Low impact findings remain. Address them to reach A-grade? (yes/no)"

If yes, re-enter Step 5 with the Low recommendations. Use the same orchestration payload format but with `(Impact: Low)` on each recommendation heading. Collect results and append to the change summary table.

If no, note in the final report: "N Low impact findings were not applied."

### 7. Commit with audit-fix chain

Read `references/commit-conventions.md` for the commit format.

Check whether the review report itself has been committed. Run `git log --oneline --all -- <report-path>` via Bash. If the report is not yet committed, tell the user:

"The review report is not yet committed. The audit-fix chain convention requires committing the report first:
`docs(reviews): add <timestamp> review report`

Commit the report now? (yes/no)"

If yes, stage and commit the report via Bash.

Then, for the fix commit:
- Determine scope from the modified files. If all edits are within one skill/agent/rule, use that item's name. If multiple items were edited, use comma-separated scopes.
- Compose the commit message: `fix(<scope>): address findings from <timestamp> review`
- Show the commit message and ask: "Commit these changes? (yes/no)"
- If yes, stage the modified files and commit via Bash. If the commit fails (non-zero exit), show the error and tell the user: "Commit failed. Changes are applied but uncommitted. Resolve the issue and commit manually."
- If no, tell the user the changes are applied but uncommitted.

### 8. Report

Present the final status:
- Files modified
- Commits created (with hashes)
- Recommendations not applied (skipped or stopped)
- Manual-only findings not dispatched
Then end your response with this menu. Determine the verify command from `generated_by`: if `review-skill` → `/review-skill <path>`, if `review-agent` → `/review-agent <path>`, if `review-rule` → `/review-rule <path>`, if `review-claude-config` → `/review-claude-config <target>`.

---
**What's next?**
1. Verify improvements → `<verify-command>`
2. Review a specific item
3. Done

_Type a number to continue._

---

When the user responds: **1** → invoke the verify command. **2** → ask which item, then invoke the matching `/review-*` command. **3** → acknowledge and stop.

## Hard Rules

- **Edit-only operations.** Never delete files. Never create new files. Only edit existing files.
- **Scope restriction.** Only edit files listed in the review report's `summary` section. Never edit files outside the report's scope.
- **Preview before every edit.** Always show the current and recommended text before applying.
- **User confirmation at every stage.** Confirm before starting, before each edit, and before committing.
- **Audit-fix chain.** Always commit the report before committing fixes. Use the report timestamp in the fix commit message.
- **Preserve file structure.** Edits replace text blocks only. Never rewrite entire files.
- **High/Medium first.** Always process High and Medium recommendations before Low. Low impact recommendations are only offered after High/Medium are resolved, or when no High/Medium exist.
- **Delegate type-specific validation.** The orchestrator does not validate edits. Specialized appliers handle all type-specific checks.
