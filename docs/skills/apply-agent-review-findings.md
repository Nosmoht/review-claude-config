# apply-agent-review-findings

Apply High and Medium priority recommendations from a `review-agent` report to the reviewed agent file, then optionally offer dispatchable Low findings. Includes agent-specific validation for single-file constraint, model selection, description keywords, and tools array consistency.

## Overview

| Property | Value |
|----------|-------|
| **Name** | apply-agent-review-findings |
| **Location** | `skills/apply-agent-review-findings/SKILL.md` |
| **Type** | Fix/Apply |
| **Allowed Tools** | Read, Edit, Glob, Bash |
| **disable-model-invocation** | true |
| **Argument Hint** | `[report-path]` |
| **Mode** | Standalone + Orchestrated |
| **Research Behavior** | None (no web research) |

## Purpose

The skill reads a `review-agent` report, extracts dispatchable High and Medium priority findings, and applies the recommended fixes to the reviewed agent file. Dispatchable Low findings are deferred to an optional follow-up pass rather than discarded. Findings without both `Current` and `Recommended` anchors remain visible as manual follow-up items rather than being silently dropped.

Because agents are single-file primitives, the skill enforces constraints that differ from skill-level fixes: no external reference directories, no multi-file sprawl, and strict validation that the agent file remains self-contained after edits.

### Step 1: Load report and extract findings

If `$ARGUMENTS` provides a report path, use it directly. Otherwise, locate the most recent `review-agent` report in `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/` by timestamp.

Read the report and parse the findings list from the review body using consumer compatibility rules derived from the canonical review contract. Historical reports may vary in heading depth or omit some modern fields, but only findings with both `Current` and `Recommended` are dispatchable to edits; anchorless findings are manual-only. The edit target comes only from `summary.path`; body `**Path:**` text is not an alternate authority.

### Step 2: Filter by dispatchability and priority

Separate findings into dispatchable and manual-only groups. Build a work list of dispatchable High and Medium findings ordered by priority (High first). If no dispatchable High or Medium findings exist but dispatchable Low findings remain, show any manual-only findings first and then offer the Low-impact pass. If only manual-only findings remain, output a manual follow-up summary and exit.

### Step 3: Read the agent file

Extract the reviewed file path from the report frontmatter. Read the agent file to establish the current state before edits.

### Step 4: Pre-edit validation (agent-specific)

Run four agent-specific checks before applying any edits:

**Single-file constraint.** Scan each recommendation for references to external files (`references/`, `includes/`, creating new files). If any recommendation would require creating files outside the agent file, **block that finding** and report: "Agents are single-file. This recommendation cannot be applied." Continue with remaining findings.

**Model field validation.** If a finding changes the `model` field, validate the new value against task complexity:

| Model | Appropriate For |
|-------|-----------------|
| `haiku` | Simple routing, quick checks, classification |
| `sonnet` | Analysis, review, moderate reasoning (default) |
| `opus` | Complex multi-step reasoning, nuanced judgment |

Warn if the model seems mismatched for the agent's described purpose but do not block.

**Description keywords.** If a finding modifies the `description` field, check that the new text contains specific trigger keywords relevant to the agent's purpose. Warn if the description is too broad ("help with tasks") or too narrow (overly specific single phrase).

**Tools array consistency.** If a finding adds entries to the `tools` array, verify that the agent body references those tools. Warn on tools listed but never mentioned in the instructions.

### Step 5: Present actionable findings

Present a summary of all dispatchable High/Medium changes that can be applied:

```
## Actionable Findings

### Finding 1 (High): <title>
- Current: <relevant excerpt>
- Proposed: <new text>

### Finding 2 (Medium): <title>
- Current: <relevant excerpt>
- Proposed: <new text>

Blocked findings: <count, if any>
Warnings: <list, if any>

Proceed with applying these findings? (yes/no)
```

If manual-only findings are present, show them in a separate `## Manual Follow-Up` table with the reason `Missing Current/Recommended anchors`.

Wait for user confirmation before entering the per-finding edit loop.

### Step 6: Apply edits per finding

For each dispatchable recommendation, show:
- canonical target path from `summary.path`
- Evidence / Why it matters / Validation
- Current text from the actual file
- Recommended replacement
- any validation warnings

Then ask: `Apply this change? (yes/skip/stop)`.

Use the Edit tool only for findings the user approves. Apply changes in document order (top to bottom) to avoid offset drift.

No new files are created. All changes are edits to the single agent file.

### Step 7: Post-edit validation (agent-specific)

After all edits are applied, re-read the agent file and run four validation checks:

**Self-contained check.** Scan the edited file for references to non-existent external files. Agent files must be fully self-contained.

**Description trigger keywords.** Verify the description contains specific, relevant trigger keywords -- not generic phrases like "help with tasks" or "assist the user."

**Example block coverage.** Confirm that `<example>` blocks exist and cover the agent's primary use case. Warn if no examples are present or if examples only cover edge cases.

**Tools array consistency.** Compare the `tools` array against actual tool references in the body. Warn on mismatches in either direction (listed but unused, used but unlisted).

If any validation fails, report the issues and suggest manual corrections. Do not attempt automated repair of validation failures.

### Step 8: Commit with audit-fix chain

Follow the audit-fix chain convention:

1. The review report should already be committed (by the review skill). If not, note this.
2. Commit the agent file changes with: `fix(<scope>): address findings from <timestamp> review`

The timestamp in the commit message links the fix to the originating report. Determine `<scope>` from the agent name.

## Hard Rules

- **Edit-only.** Never create new files. Agents are single-file primitives.
- **Single-file constraint.** Never create reference directories, include files, or any external dependencies for agents.
- **Scope restriction.** Only modify the file identified in the review report.
- **Canonical target path.** Use `summary.path` as the sole canonical target identity for edits.
- **Preview before edit.** Always show a batch summary first, then preview each individual change and wait for confirmation.
- **Audit-fix chain.** Commit message must reference the review report timestamp.
- **High/Medium first.** Apply High and Medium findings first. Offer dispatchable Low findings afterward instead of discarding them.
- **disable-model-invocation: true.** This skill modifies files and requires explicit user confirmation.

## Reference Files

| File | Purpose |
|------|---------|
| `references/agent-fix-guide.md` (own) | Agent-specific validation rules and single-file constraints |
| `apply-review-findings/references/commit-conventions.md` (shared) | Commit message format for audit-fix chain |

## Interactions

| Direction | Target | Notes |
|-----------|--------|-------|
| Called by | `apply-review-findings` | Orchestrated mode, receives report path |
| Called by | User directly | Standalone invocation |
| Calls | Nothing | Terminal skill in the fix chain |
