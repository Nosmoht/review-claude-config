---
name: apply-agent-review-findings
description: >
  Apply recommendations from a review-agent report to the reviewed agent file.
  Processes High/Medium findings first, then optionally offers Low findings
  for A-grade convergence. Previews each change with user confirmation and
  commits with audit-fix chain convention. Use after running /review-agent
  or when delegated by /apply-review-findings.
argument-hint: "[report-path]"
allowed-tools: Read, Edit, Glob, Bash
disable-model-invocation: true
---

# Apply Agent Review Findings

You are a code editor applying structured review recommendations to Claude Code agents. Your job is to faithfully translate review findings into file edits with agent-specific validation, preserving the audit-fix traceability chain.

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
**Type:** Agent
**Recommendations:**
[High/Medium recommendations with Current/Recommended blocks]
```

- If present -> **orchestrated mode** (use provided items, skip report parsing, return structured results only).
- If absent -> **standalone mode** (full workflow below).

## Phase 1 -- Setup (standalone mode only)

### Step 1: Locate Report

If `$ARGUMENTS` contains a file path, use it. Otherwise, Glob `.claude/reviews/*-review-agent.md` and select the most recent report by filename timestamp.

Read the report file. If the file does not exist or `generated_by` is not `review-agent`, report the error and stop.

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

Filter into two groups: **High/Medium** recommendations and **Low** recommendations.

If no High/Medium recommendations exist, skip to **Step 2a: Low Impact Offer**.

### Step 2a: Low Impact Offer

If no High/Medium recommendations exist, tell the user:

"No High or Medium findings. N Low impact recommendations remain. These are minor improvements that can help reach an A-grade. Address them? (yes/no)"

If no, stop. If yes, promote the Low recommendations into the actionable set and continue to Phase 2.

### Step 3: Load References

Read own `references/agent-fix-guide.md` for type-specific validation rules.

Locate shared commit conventions via Glob: `**/apply-review-findings/references/commit-conventions.md`. If not found, warn but continue.

## Phase 2 -- Present Summary

Show a summary table of all actionable findings:

```
## Actionable Findings

| # | Recommendation | Impact | File |
|---|----------------|--------|------|
| 1 | Add example blocks | High | .claude/agents/foo.md |
```

Ask: "Proceed with applying these findings? (yes/no)"
If no, stop.

## Phase 3 -- Apply Recommendations

For each recommendation (High impact first, then Medium):

1. Read the target agent file. Determine the path from:
   - The report's `summary` frontmatter field (if it contains file paths), or
   - The `**Path:**` line in the report body.
   If no valid path is found, ask the user to provide the agent file path.
2. Locate the **Current** text block in the actual file content.
   - If not found, show the user the Current text and ask: "This text was not found in the file. Skip this recommendation? (yes/no)" If yes, skip. If no, ask the user to identify the correct text.
3. **Pre-edit validation** (agent-specific):
   - If the recommended text references or creates external files (e.g., `references/`, includes, imports), block: "Agents are single-file. This edit would violate the single-file constraint. Skip this recommendation."
   - If the edit modifies the `model` frontmatter field, validate against complexity guidelines: haiku for simple routing/checks, sonnet for analysis/review (default), opus for complex multi-step reasoning. Warn if mismatch.
   - If the edit modifies the `description` field, check that the new description still contains natural trigger keywords relevant to the agent's purpose. Warn if keywords appear too broad or too narrow.
   - If the edit modifies the `tools` array, scan the agent body for tool references. Warn if tools are added that aren't referenced in the body.
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
6. **Post-edit validation** (agent-specific):
   - Verify the file is self-contained (no references to external files that don't exist).
   - If `description` was modified, verify it still contains specific trigger keywords (not generic terms like "help with tasks").
   - If `<example>` blocks were modified, verify they cover at least the primary use case described in the agent's goal.
   - If `tools` was modified, verify the array matches tools actually used in the body.

## Phase 4 -- Results

### Orchestrated Mode

Return structured results:

```
## Apply Results

| # | Recommendation | Status |
|---|----------------|--------|
| 1 | Add example blocks | Applied |
| 2 | Fix model selection | Skipped |

Applied: N / Total: M
Validation warnings: [list any warnings]
```

### Standalone Mode

Present the change summary table (same format as above).

If no changes were applied, stop here.

**Low Impact Pass (standalone mode only):**

If Low impact recommendations were set aside in Step 2 and at least one High/Medium change was applied, ask:

"N Low impact findings remain. Address them to reach A-grade? (yes/no)"

If yes, loop back to Phase 3 with the Low recommendations. Process through the same preview/confirm/validate pipeline. Append results to the change summary table.

If no, note: "N Low impact findings were not applied."

In orchestrated mode, do not prompt — process whatever recommendations the orchestrator sends.

**Commit with audit-fix chain:**

Read the shared commit conventions (loaded in Phase 1 Step 3).

Extract the timestamp from the report filename.

Check whether the review report has been committed: `git log --oneline --all -- <report-path>` via Bash. If not committed:

"The review report is not yet committed. The audit-fix chain requires committing the report first:
`docs(reviews): add <timestamp> review report`

Commit the report now? (yes/no)"

If yes, stage and commit via Bash.

For the fix commit:
- Determine scope from the agent name.
- Compose: `fix(<scope>): address findings from <timestamp> review`
- Show the commit message and ask: "Commit these changes? (yes/no)"
- If yes, stage and commit via Bash.

Present final status:
- Files modified
- Commits created (with hashes)
- Recommendations not applied (with skip reason for each)
- For validation-blocked recommendations: suggest manual resolution approach
Then end your response with this menu (substitute `<path>` with the target agent path):

---
**What's next?**
1. Verify improvements → `/review-agent <path>`
2. Apply findings from another report
3. Done

_Type a number to continue._

---

When the user responds: **1** → invoke `/review-agent` with the agent path. **2** → ask for the report path, then invoke `/apply-agent-review-findings`. **3** → acknowledge and stop.

## Hard Rules

- **Edit-only operations.** Never delete files. Never create new files. Only edit existing files.
- **Single-file constraint.** Agents are single-file. Never create reference directories or external files for agents.
- **Scope restriction.** Only edit files listed in the review report's `summary` section.
- **Preview before every edit.** Always show current and recommended text before applying.
- **Preserve review context.** Always carry `Evidence`, `Why it matters`, and `Validation` through previews even though `Current`/`Recommended` remain the edit anchors.
- **User confirmation at every stage.** Confirm before starting, before each edit, and before committing.
- **Audit-fix chain.** Always commit the report before committing fixes.
- **Preserve file structure.** Edits replace text blocks only. Never rewrite entire files.
- **High/Medium first.** Always process High and Medium recommendations before Low. Low impact recommendations are only offered after High/Medium are resolved, or when no High/Medium exist.
