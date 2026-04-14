# apply-skill-review-findings

> Apply review-skill recommendations to the reviewed SKILL.md. Process dispatchable High/Medium findings first, optionally offer dispatchable Low findings, and keep anchorless findings visible as manual follow-up items.

**Command:** `/apply-skill-review-findings [report-path]`
**Location:** `skills/apply-skill-review-findings/SKILL.md`
**Type:** Fix/Apply
**Allowed Tools:** Read, Edit, Glob, Bash
**disable-model-invocation:** true
**Mode Support:** Standalone + Orchestrated

## Overview

The apply-skill-review-findings skill translates structured review recommendations into targeted file edits on SKILL.md files. It bridges the gap between review output (from `/review-skill`) and actual code changes by providing a guided, confirmation-gated editing workflow with skill-specific validation at every step.

The skill operates in two modes. In standalone mode, it locates and parses a review-skill report, separates dispatchable findings from manual-only follow-up items, and walks the user through each edit. In orchestrated mode, it receives pre-parsed recommendations from `/apply-review-findings` and returns structured results without the report-parsing or commit phases.

Every edit follows a strict cycle: read the target file, locate the text to change, run pre-edit validation, show a preview with full review context, wait for user confirmation, apply the edit, and run post-edit validation. This ensures no change is made without explicit approval and that each edit preserves file integrity.

Because the skill has `disable-model-invocation: true`, it runs without spawning sub-agents. It never creates or deletes files -- only edits existing ones within the scope declared in the review report.

## Process Steps

### Mode Detection

The skill checks whether the prompt contains an orchestration metadata block with `report_timestamp` and an "Items to Fix" section. If present, the skill enters orchestrated mode: it uses the provided items and recommendations directly, skips report parsing and the commit workflow, and returns structured results only. If absent, the skill runs the full standalone workflow described below.

### Phase 1 -- Setup (standalone mode only)

**Step 1: Locate report.** If `$ARGUMENTS` contains a file path, the skill uses it directly. Otherwise, it globs `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/*-review-skill.md` and selects the most recent report by filename timestamp. The skill reads the report file and verifies that `generated_by` in the frontmatter equals `review-skill`. If the file does not exist or validation fails, the skill reports the error and stops.

**Step 2: Parse and classify.** The skill locates the canonical review contract, extracts the YAML frontmatter to get `date`, `target`, and `summary`, and parses recommendation sections using consumer compatibility rules. Historical reports may use `###` headings or omit some modern fields, but only findings with both `Current` and `Recommended` are dispatchable to edits. Anchorless findings remain visible as manual-only follow-up items. Low findings are deferred, not discarded.

Dispatchable High and Medium impact recommendations are handled first. Dispatchable Low impact recommendations are deferred to an optional follow-up pass rather than discarded. If only Low dispatchable findings remain, any manual-only findings must still be shown before the Low-impact offer. If only manual-only findings remain, the skill reports them as manual follow-up and stops.

**Step 3: Load references.** The skill reads its own `references/skill-fix-guide.md` for skill-specific validation rules. It also locates the shared commit conventions file via Glob (`**/apply-review-findings/references/commit-conventions.md`). If the shared file is not found, the skill warns but continues -- commit message guidance will use defaults.

### Phase 2 -- Present Summary

The skill displays a summary table of all dispatchable findings:

```
## Actionable Findings

| # | Recommendation | Impact | File |
|---|----------------|--------|------|
| 1 | Add confirmation gate | High | skills/foo/SKILL.md |
| 2 | Extract reference file | Medium | skills/foo/SKILL.md |
```

If manual-only findings are present, it also shows a separate `## Manual Follow-Up` table with the reason `Missing Current/Recommended anchors`.

It then asks: "Proceed with applying these findings? (yes/no)". If the user declines, the skill stops.

### Phase 3 -- Apply Recommendations

The skill processes each recommendation in priority order (High impact first, then Medium). For each recommendation, it executes the following cycle:

**1. Read target file.** Read the target SKILL.md at the path from the report's `summary` section.

**2. Locate current text.** Search for the Current text block (from the report) in the actual file content. If the exact text is not found, the skill shows the user the Current text and asks: "This text was not found in the file. Skip this recommendation?" If the user chooses not to skip, they identify the correct text to replace.

**3. Pre-edit validation.** Three skill-specific checks run before showing the preview:

| Check | Condition | Action |
|-------|-----------|--------|
| Line count | Edit would push file over 500 lines | Warn with suggestion to extract to references/ |
| Reference material | Recommended text inlines stable content (long tables, templates, examples) | Flag and ask whether to proceed or skip |
| Frontmatter | Edit modifies frontmatter | Verify `name` and `description` remain present, `allowed-tools` not empty |

**4. Show preview.** The skill presents all review context alongside the proposed change:

- File path being edited
- Evidence (from the report)
- Why it matters (from the report)
- Validation criteria (from the report)
- Current text (as found in the actual file)
- Recommended replacement (from the report)
- Any validation warnings from pre-edit checks

**5. Confirm edit.** The skill asks: "Apply this change? (yes/skip/stop)"

| Response | Behavior |
|----------|----------|
| **yes** | Apply the edit using the Edit tool |
| **skip** | Move to the next recommendation without changes |
| **stop** | End processing immediately and proceed to results |

**6. Post-edit validation.** After applying each edit, four checks run:

| Check | Threshold | Action |
|-------|-----------|--------|
| Total line count | 500 lines | Warn if file exceeds limit |
| Reference token estimate | 385 words (~500 tokens, using word count x 1.3) | Warn if any modified reference file exceeds budget |
| Frontmatter YAML | Required fields present | Verify `name`, `description` are valid |
| Allowed-tools match | Body tool references | Warn if `allowed-tools` does not match actual tool usage in workflow body |

### Phase 4 -- Results

**Orchestrated mode:** The skill returns a structured results table and stops:

```
## Apply Results

| # | Recommendation | Status |
|---|----------------|--------|
| 1 | Add confirmation gate | Applied |
| 2 | Extract reference file | Skipped |

Applied: N / Total: M
Validation warnings: [list any warnings]
```

**Standalone mode:** The skill presents the same results table, then enters the audit-fix chain commit workflow:

1. **Check report commit status.** Run `git log --oneline --all -- <report-path>` via Bash. If the report is not committed, offer to commit it first with the message `docs(reviews): add <timestamp> review report`.
2. **Compose fix commit.** Determine the scope from the modified skill name (e.g., `review-skill` if editing `skills/review-skill/SKILL.md`). Compose the message: `fix(<scope>): address findings from <timestamp> review`. Show the message and ask: "Commit these changes? (yes/no)".
3. **Present final status.** List files modified, commits created (with hashes), and recommendations not applied (skipped or stopped).

The "What's next?" menu follows the final status:

1. Verify improvements -- `/review-skill <path>`
2. Apply findings from another report
3. Done

## Hard Rules

1. **Edit-only operations.** Never delete files. Never create new files. Only edit existing files.
2. **Scope restriction.** Only edit files listed in the review report's `summary` section.
3. **Preview before every edit.** Always show current and recommended text before applying.
4. **Preserve review context.** Always carry Evidence, Why it matters, and Validation through previews even though Current/Recommended remain the edit anchors.
5. **User confirmation at every stage.** Confirm before starting, before each edit, and before committing.
6. **Audit-fix chain.** Always commit the report before committing fixes. The report timestamp links the two commits.
7. **Preserve file structure.** Edits replace text blocks only. Never rewrite entire files.
8. **High/Medium first.** Only apply High and Medium recommendations in the first pass. Offer dispatchable Low findings afterward instead of discarding them.

## Research Behavior

None. This skill performs no web research. It operates entirely on local files.

## Reference Files

| File | Purpose | Token Budget |
|------|---------|-------------|
| `references/skill-fix-guide.md` (own) | Skill-specific validation rules for pre/post-edit checks | <=500 |
| `apply-review-findings/references/commit-conventions.md` (shared) | Commit format conventions for audit-fix chain | <=500 |

## Interactions

| Direction | Target | Notes |
|-----------|--------|-------|
| Called by | `/apply-review-findings` | In orchestrated mode, receives pre-parsed recommendations |
| Called by | User directly | In standalone mode, full workflow with report parsing |
| Calls | Nothing | Does not invoke other skills |
| Shares references with | `/apply-review-findings` | Commit conventions file |
| May suggest | `/review-skill` | Via "What's next?" menu to verify improvements |
