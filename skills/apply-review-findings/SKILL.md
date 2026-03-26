---
name: apply-review-findings
description: >
  Apply recommendations from any review report (review-claude-config,
  review-skill, review-agent, or review-rule) to the reviewed files. Delegates
  to specialized type-specific appliers, then commits with audit-fix chain
  convention. Use after running any /review-* skill to act on findings.
argument-hint: "[report-path]"
allowed-tools: Read, Edit, Glob, Bash
disable-model-invocation: true
---

# Apply Review Findings

You are a thin orchestrator that locates review reports, classifies items by type, and delegates fix application to specialized appliers. You handle report parsing, summary presentation, and the commit workflow. The specialized appliers handle type-specific validation and edit application.

## Workflow

### 1. Locate the review report

If `$ARGUMENTS` contains a file path, use it. Otherwise, Glob `.claude/reviews/*-review-*.md` and select the most recent report by filename timestamp.

Read the report file. If the file does not exist or `generated_by` is not one of `review-claude-config`, `review-skill`, `review-agent`, `review-rule`, report the error and stop.

### 2. Parse recommendations

Extract the YAML frontmatter to get: `date`, `target`, `generated_by`, and `summary` (list of items with paths, types, and grades).

Parse the report body for recommendation sections. Each recommendation follows this pattern:
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

Example extraction: Given heading "#### 2. Add confirmation gate (Impact: High, Category: Safety)" with Evidence/Why it matters/Validation plus Current/Recommended blocks, extract: title="Add confirmation gate", impact=High, category=Safety, evidence=<text>, why=<text>, validation=<text>, item=<from nearest ## heading or frontmatter summary>.
Some recommendations may lack Current/Recommended blocks (structural suggestions). Pass the full structured text to the specialized applier.

Filter to **High and Medium impact only**. Discard Low impact recommendations.

If no High or Medium recommendations are found, tell the user: "No actionable findings -- all recommendations are Low impact." Stop.

Group recommendations by item type using the `type` field in the `summary` array (Skill, Agent, or Rule). For single-item reports (`review-skill`, `review-agent`, `review-rule`), there is one group.

### 3. Present summary

Show a summary table of all actionable findings before making any changes:

```
## Actionable Findings

| # | Item | Type | Recommendation | Impact | File |
|---|------|------|----------------|--------|------|
| 1 | review-skill | Skill | Add confirmation gate | Medium | skills/review-skill/SKILL.md |
| 2 | my-agent | Agent | Fix model selection | High | .claude/agents/my-agent.md |
```

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

Dispatch an Agent with the specialized SKILL.md content, its fix guide, and the orchestration payload as the prompt. The agent applies edits with user confirmation and returns structured results. Preserve `Evidence`, `Why it matters`, and `Validation` in the payload even when the edit anchor remains `Current`/`Recommended`.

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
- **No Low impact changes.** Only apply High and Medium recommendations. Users who want Low impact changes should apply them manually.
- **Delegate type-specific validation.** The orchestrator does not validate edits. Specialized appliers handle all type-specific checks.
