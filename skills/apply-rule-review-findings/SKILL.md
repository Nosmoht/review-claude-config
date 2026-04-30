---
name: apply-rule-review-findings
description: >
  Applies findings from a /review-rule report to the reviewed rule file
  (always-loaded directives, imperatives). Use after /review-rule on a
  single rule or when delegated by /apply-review-findings. Do NOT use for
  skill or agent reports.
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

**Resolve report directory:** Load `repo-identification.md` via Glob `**/review-claude-config/references/repo-identification.md` to compute `<repo-slug>` (= `sanitize(basename(CWD))` — lowercase, alphanumeric + hyphens only). The report directory is `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/`.

If `$ARGUMENTS` contains a file path, use it. Otherwise, Glob `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/*-review-rule.md` and select the most recent report by filename timestamp.

Read the report file. If the file does not exist or `generated_by` is not `review-rule`, report the error and stop.

### Step 2: Load Findings

> This step runs in standalone mode only. Orchestrated mode bypasses Step 2 entirely — recommendations come from the inline `## Items to Fix` Markdown block in the orchestration prompt (see Mode Detection above).

Locate the canonical review contract via Glob: `**/review-claude-config/references/review-report-contract.md`.
- Prefer `skills/review-claude-config/references/review-report-contract.md` when present.
- Otherwise use the sibling `.claude/skills/review-claude-config/references/review-report-contract.md` copy.

Read that file as the forward-looking report contract. Extract the YAML frontmatter to get: `date`, `target`, and `summary`.

#### Step 2.1: Sidecar discovery

Resolve the report path to absolute via `Bash("realpath <report-path>")`. Require it to end in `.md`; otherwise skip sidecar discovery and use the Markdown fallback (Step 2.3). Sidecar path = `<report-path>` with the trailing `.md` removed and `.findings.json` appended.

Try to Read the sidecar. Five outcomes:
- **File missing** → log `"no sidecar at <path> — using Markdown body"` (legitimate for `--single-perspective`, orchestrated mode, or pre-#81 legacy reports — `/review-rule` does not yet emit sidecars) and fall through to Step 2.3.
- **JSON parse fails** → log `"sidecar parse failed at <path> — falling back to Markdown"` and fall through to Step 2.3.
- **`generated_by` or `findings` keys missing/non-list** → log `"sidecar schema mismatch at <path> — falling back to Markdown"` and fall through to Step 2.3.
- **`findings: []`** → clean-review state. Surface "No findings — review was clean." and stop. Do NOT fall back to Markdown.
- **`findings: [...]` non-empty** → continue to Step 2.2.

#### Step 2.2: Map sidecar findings

The sidecar conforms to `skills/review-claude-config/references/schemas/findings-list.schema.json`. Map each finding to the local recommendation model:
- **title** — `checklist_item` + a short fragment from `evidence` (truncate to ~60 chars)
- **impact** — `severity` (`High`/`Medium`/`Low`)
- **file path** — finding `path`; fall back to `summary[0].path` (the canonical rule path) when `path` is missing
- **evidence** — finding `evidence`
- **why it matters** — finding `why` (when absent, surface the rubric-item reference; never blank)
- **validation** — finding `validation` (when absent, surface "Manual re-verification recommended"; never blank)
- **current** — finding `current`
- **recommended** — finding `recommended`

Continue to Step 2.4 (applyability gate).

#### Step 2.3: Markdown back-compat path

Parse the report body using consumer compatibility rules:
- modern headings may use `####`
- historical headings may use `###`
- historical reports may omit `Evidence`, `Why it matters`, or `Validation`
- recommendations carry `Current` and `Recommended` blocks when dispatchable

Apply the same defensive defaults as the sidecar path. Log a one-line note: "Loaded findings from Markdown body (sidecar absent — legacy report)."

#### Step 2.4: Applyability gate

For each mapped recommendation, verify it can drive a real Edit:
1. If `current` or `recommended` is empty → mark **Manual-only** (reason: "Missing rewrite anchors").
2. Read the target rule file.
3. If `current` does NOT appear as a literal substring of the file content → mark **Manual-only**. Distinguish reasons: synthesized-evidence shape (`current` starts with `line ` and contains `; match=` / `; trigger=` / `; missing=`) → "Synthesized evidence summary, not a literal source quote (binary item)"; otherwise → "Anchor text not found (whitespace, encoding, or quoting drift?)".
4. Otherwise → mark **Dispatchable**.

Filter Dispatchable into **High/Medium** and **Low** groups.

> Reports produced after issue #72 ship only the **deterministic subset** at H+M severity (items in `BINARY_ITEM_IDS` or `NARRATIVE_PARENT_IDS`, per `skills/review-skill/references/merge-rules.md` §"Perspective Finding Handling"). Advisory perspective findings are demoted to Low at merge time. After Step 2.4, synthesized binary findings (currently emitting non-substring `current`) also fall to Manual-only by construction. Auto-dispatchable Highs are perspective-emitted findings that survive the demote — typically a small set; the rest of the workflow treats them normally.

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

Read own `references/rule-fix-guide.md` for type-specific validation rules.

Locate shared commit conventions via Glob: `**/apply-review-findings/references/commit-conventions.md`. If not found, warn but continue.

## Phase 2 -- Present Summary

Surface any Step 2 log lines first (one line each).

Show a summary table of all dispatchable findings:

```
## Actionable Findings

| # | Recommendation | Impact | File |
|---|----------------|--------|------|
| 1 | Add scope boundaries | High | .claude/rules/foo.md |
```

If manual-only findings are present, also show:

```
## Manual Follow-Up

| # | Recommendation | Impact | Reason | Why it matters |
|---|----------------|--------|--------|----------------|
| 1 | Tighten rationale wording | Medium | Missing Current/Recommended anchors | Aspirational verbs weaken enforcement |
```

The `Why it matters` column gives the user actionable context for findings that cannot drive an automatic Edit.

Confirm via AskUserQuestion (header: "Apply findings"):
- Option 1 label: "Apply N findings" (Recommended) — description: `"Process High/Medium recommendations with preview for each"`
- Option 2 label: "Cancel" — description: `"Stop without making changes"`

On "Cancel": stop.

## Phase 3 -- Apply Recommendations

Example flow: Read `.claude/rules/commit-format.md` -> search for Current text "You should use conventional commits" -> found -> pre-edit: weak verb "should" in replacement flagged as warning (expected — it's being replaced) -> show preview -> user says "yes" -> Edit applied -> post-edit: no frontmatter added, no sibling contradictions found.

For each recommendation (High impact first, then Medium):

1. Read the target rule file at the path from the report's `summary` section.
2. Locate the **Current** text block in the actual file content.
   - If not found, show the user the Current text and confirm via AskUserQuestion (header: "Text not found"):
     - Option 1 label: "Skip this recommendation" (Recommended) — description: `"Move to the next recommendation"`
     - Option 2 label: "Identify correct text" — description: `"Describe where the text is so the edit can be applied"`
     On "Skip this recommendation": skip. On "Identify correct text": ask the user to identify the correct text.
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
5. Confirm via AskUserQuestion (header: "Apply: <recommendation title>"):
   - Option 1 label: "Apply this change" (Recommended) — description: `"Edit the file with the recommended replacement"`
   - Option 2 label: "Skip" — description: `"Move to the next recommendation"`
   - Option 3 label: "Stop" — description: `"End processing, keep changes applied so far"`
   On "Apply this change": apply the edit using the Edit tool. On "Skip": move to next. On "Stop": end processing.
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
1. Introduce aspirational language ("should", "try to", "consider") where the original used constraints ("must", "never", "always").
2. Remove or broaden scope boundaries without documented justification.
3. Create contradictions with sibling rules in the same directory.

If any regression is detected, confirm via AskUserQuestion (header: "Potential regression detected"):
- Option 1 label: "Review before committing" (Recommended) — description: `"Inspect [file]: [description] before proceeding"`
- Option 2 label: "Proceed anyway" — description: `"Continue to the commit step"`

**Commit with audit-fix chain:**

Read the shared commit conventions (loaded in Phase 1 Step 3).

Extract the timestamp from the report filename.

Check whether the review report has been committed: `git log --oneline --all -- <report-path>` via Bash. If not committed:

Tell the user: "The review report is not yet committed. The audit-fix chain requires committing the report first: `docs(reviews): add <timestamp> review report`"

Confirm via AskUserQuestion (header: "Commit report"):
- Option 1 label: "Commit the report now" (Recommended) — description: `"Stage and commit the review report with docs(reviews): add <timestamp> review report"`
- Option 2 label: "Skip" — description: `"Continue without committing the report"`

On "Commit the report now": stage and commit via Bash.

For the fix commit:
- Determine scope from the rule name or directory.
- Compose: `fix(<scope>): address findings from <timestamp> review`
- Show the commit message and confirm via AskUserQuestion (header: "Commit changes"):
  - Option 1 label: "Commit these changes" (Recommended) — description: `"Stage and commit: fix(<scope>): address findings from <timestamp> review"`
  - Option 2 label: "Skip" — description: `"Leave changes uncommitted"`
- On "Commit these changes": stage and commit via Bash.

Present final status:
- Files modified
- Commits created (with hashes)
- Recommendations not applied
Then end your response with this menu (substitute `<path>` with the target rule path):

Present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Verify improvements" (Recommended) — description: `"Run /review-rule <path> to detect cross-dimension regressions"`
- Option 2 label: "Apply findings from another report" — description: `"Provide a report path to apply"`
- Option 3 label: "Done" — description: `"End the workflow"`

On "Verify improvements": invoke `/review-rule` with the rule path. On "Apply findings from another report": ask for the report path, then invoke `/apply-rule-review-findings`. On "Done": acknowledge and stop.

## Hard Rules

- **Edit-only operations.** Never delete files. Never create new files. Only edit existing files.
- **No frontmatter injection.** Rules are plain Markdown. Never add YAML frontmatter to a rule file.
- **Scope restriction.** Only edit files listed in the review report's `summary` section.
- **Preview before every edit.** Always show current and recommended text before applying.
- **Preserve review context.** Always carry `Evidence`, `Why it matters`, and `Validation` through previews even though `Current`/`Recommended` remain the edit anchors.
- **User confirmation at every stage.** Confirm before starting, before each edit, and before committing.
- **Audit-fix chain.** Always commit the report before committing fixes.
- **Preserve file structure.** Edits replace text blocks only. Never rewrite entire files.
- **High/Medium first.** Always process High and Medium recommendations before Low. Low impact recommendations are only offered after High/Medium are resolved, or when no High/Medium exist.
