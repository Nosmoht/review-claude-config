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

> **Pre-apply policy classification.** Before any Edit, classify the finding against [`docs/apply-risk-policy.md`](../../docs/apply-risk-policy.md) on `evidence_class × confidence × blast_radius`. If `decide()` returns `auto_apply_allowed: false` (e.g., `evidence_class: Low-evidence area`, missing label, or any `blast_radius: security-sensitive`), route to manual-only handling regardless of the per-edit Confirmation Gate.

**Resolve report directory:** Load `repo-identification.md` via Glob `**/review-claude-config/references/repo-identification.md` to compute `<repo-slug>` (= `sanitize(basename(CWD))` — lowercase, alphanumeric + hyphens only). The report directory is `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`.

If `$ARGUMENTS` contains a file path, use it. Otherwise, Glob `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/*-review-*.md` and select the most recent report by filename timestamp.

Read the report file. If the file does not exist or `generated_by` is not one of `review-claude-config`, `review-skill`, `review-agent`, `review-rule`, report the error and stop.

**Single-item report nudge (UX):** If `items_reviewed == 1` and `generated_by` is one of `review-skill` / `review-agent` / `review-rule`, tell the user: "This is a single-item report — `/apply-<type>-review-findings <report-path>` is the more direct entry point. Continue here anyway?" (AskUserQuestion, header: "Single-item report"). On "Use per-type applier" (Recommended): tell the user the exact command and stop. On "Continue with orchestrator": proceed to Step 2.

### 2. Load findings

Locate the canonical review contract via Glob: `**/review-claude-config/references/review-report-contract.md`.
- Prefer `skills/review-claude-config/references/review-report-contract.md` when present.
- Otherwise use the sibling `.claude/skills/review-claude-config/references/review-report-contract.md` copy.

Read that file as the forward-looking parse contract. Extract the YAML frontmatter fields defined there: `date`, `target`, `generated_by`, and `summary` (list of items with paths, types, and grades).

#### 2.1 Sidecar discovery

Resolve `<report-path>` to absolute via `Bash("realpath <report-path>")`. Require it to end in `.md`; otherwise skip sidecar discovery and use the Markdown fallback (Step 2.3). Sidecar path = `<report-path>` with the trailing `.md` removed and `.findings.json` appended.

Try to Read the sidecar. Five outcomes:
- **File missing** → log `"no sidecar at <path> — using Markdown body"` and fall through to Step 2.3.
- **JSON parse fails** → log `"sidecar parse failed at <path> — falling back to Markdown"` and fall through to Step 2.3.
- **`generated_by` or `findings` keys missing/non-list** → log `"sidecar schema mismatch at <path> — falling back to Markdown"` and fall through to Step 2.3.
- **`findings: []`** → clean-review state. Surface "No findings — review was clean." and stop. Do NOT fall back to Markdown.
- **`findings: [...]` non-empty** → continue to Step 2.2.

#### 2.2 Map sidecar findings

The sidecar conforms to `skills/review-claude-config/references/schemas/findings-list.schema.json`. Each finding object carries `id`, `checklist_item`, `dimension`, `severity` (`High|Medium|Low`), `evidence`, optionally `current`, `recommended`, `why`, `validation`, `path`, `line_range`.

Map each sidecar finding into the orchestration model:
- **title** — `checklist_item` + a short fragment from `evidence` (truncate to ~60 chars)
- **impact** — `severity`
- **file path** — finding `path`; fall back to `summary[0].path` only when the report carries exactly one item (`items_reviewed == 1`). For multi-item batch reports, a missing `path` is unrecoverable.
- **type** — looked up from the report frontmatter `summary` array by matching the finding's `path` against `summary[*].path` (exact match). If no match, mark this finding **Manual-only** with reason `"Path not in report scope"` and skip type inference. Per-type appliers in orchestrated mode reject paths outside `summary`, so dispatching with an inferred type would be silently dropped — the Manual-only path surfaces the issue to the user instead.
- **evidence** — finding `evidence`
- **why it matters** — finding `why` (when absent, surface the rubric-item reference; never blank)
- **validation** — finding `validation` (when absent, surface "Manual re-verification recommended"; never blank)
- **current** — finding `current`
- **recommended** — finding `recommended`

Continue to Step 2.4 (applyability gate).

#### 2.3 Markdown back-compat path

Parse the report body using consumer compatibility rules:
- modern recommendation headings may use `####`
- historical recommendation headings may use `###`
- heading: `#### N. Title (Impact: High/Medium/Low[, Category: ...])`
- forward-looking fields: `Evidence`, `Why it matters`, `Validation`
- historical reports may omit one or more of those fields
- optional fields: `Current`, `Recommended`

Example extraction: Given heading "#### 2. Add confirmation gate (Impact: High, Category: Safety)" with Evidence/Why it matters/Validation plus Current/Recommended blocks, extract: title="Add confirmation gate", impact=High, category=Safety, evidence=<text>, why=<text>, validation=<text>, item=<from nearest item heading or frontmatter summary>.

Apply the same defensive defaults as the sidecar path (never blank `Why it matters` / `Validation` previews). Log a one-line note in the Step 3 summary: "Loaded findings from Markdown body (sidecar absent — legacy report)."

#### 2.4 Applyability gate

For each mapped recommendation, verify it can drive a real Edit before dispatching:
1. If `current` or `recommended` is empty → mark **Manual-only** (reason: "Missing rewrite anchors").
2. Read the recommendation's target file.
3. If `current` does NOT appear as a literal substring of the file content → mark **Manual-only**. Distinguish reasons: synthesized-evidence shape (`current` starts with `line ` and contains `; match=` / `; trigger=` / `; missing=`) → "Synthesized evidence summary, not a literal source quote (binary item)"; otherwise → "Anchor text not found (whitespace, encoding, or quoting drift?)".
4. Otherwise → mark **Dispatchable**.

Split Dispatchable into **High/Medium** and **Low** groups. Group remaining Dispatchable by item `type` for the per-type dispatch (Step 4–5).

> Reports produced after issue #72 ship only the **deterministic subset** at H+M severity (items in `BINARY_ITEM_IDS` or `NARRATIVE_PARENT_IDS`, per `skills/review-claude-config/references/merge-rules.md` §"Perspective Finding Handling"). Advisory perspective findings are demoted to Low at merge time. After Step 2.4, synthesized binary findings (currently emitting non-substring `current`) also fall to Manual-only by construction. The orchestrator dispatches only Dispatchable recommendations; per-type appliers receive only edit-ready inputs in orchestrated mode.

If no dispatchable High or Medium recommendations are found:
- if dispatchable Low recommendations exist, skip to **Step 2a: Low Impact Offer**
- otherwise show any manual-only findings and stop

### 2a. Low Impact Offer

If manual-only findings are present, show them before offering the Low-impact pass. Keep them visible even when dispatchable Low findings exist.

If dispatchable Low recommendations exist, tell the user:

Confirm via AskUserQuestion (header: "Low-impact findings only"):
- Option 1 label: "Address N low-impact findings" — description: `"Process Low recommendations to reach A-grade"`
- Option 2 label: "Skip" (Recommended) — description: `"Stop — preserve manual-only findings as follow-up items"`

On "Skip": stop after preserving the manual-only findings as follow-up items. On "Address N low-impact findings": promote the Low recommendations into the actionable set and continue to Step 3.

Group dispatchable recommendations by item type using the `type` field in the `summary` array (Skill, Agent, or Rule). For single-item reports (`review-skill`, `review-agent`, `review-rule`), there is one group.

If no dispatchable recommendations exist at all, show any manual-only findings and stop.

### 3. Present summary

Surface any Step 2 log lines first (one line each): "Loaded findings from sidecar `<path>`", "no sidecar at `<path>` — using Markdown body", "sidecar parse failed at `<path>` — falling back to Markdown", "sidecar schema mismatch at `<path>` — falling back to Markdown", or "Sidecar `findings: []` — review was clean, nothing to apply".

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

| # | Item | Type | Recommendation | Impact | Reason | Why it matters |
|---|------|------|----------------|--------|--------|----------------|
| 1 | review-skill | Skill | Clarify workflow policy | Medium | Missing Current/Recommended anchors | `WS-2b`: conditionals lack measurable criteria |
| 2 | my-agent | Agent | Tighten step boundary | High | Synthesized evidence summary | Binary item `CLAR-1` FAIL — see scoring-rubric.md BOUNDARY exemplar |
```

The Manual Follow-Up `Why it matters` column gives the user actionable context for findings that cannot drive an automatic Edit.

If there are no dispatchable findings and at least one manual-only finding, stop after showing the manual follow-up section.

Confirm via AskUserQuestion (header: "Apply findings"):
- Option 1 label: "Apply N findings" (Recommended) — description: `"Dispatch High/Medium recommendations to specialized appliers"`
- Option 2 label: "Cancel" — description: `"Stop without making changes"`

On "Cancel": stop.

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

If Low impact recommendations were set aside in Step 2 and at least one High/Medium change was applied, confirm via AskUserQuestion (header: "Low-impact findings"):
- Option 1 label: "Address N low-impact findings" — description: `"Re-enter Step 5 with Low recommendations to reach A-grade"`
- Option 2 label: "Skip" (Recommended) — description: `"Leave low-impact findings for later"`

On "Address N low-impact findings": re-enter Step 5 with the Low recommendations. Use the same orchestration payload format but with `(Impact: Low)` on each recommendation heading. Collect results and append to the change summary table. On "Skip": note in the final report: "N Low impact findings were not applied."

### 7. Commit with audit-fix chain

Read `skills/review-claude-config/references/commit-conventions.md` for the commit format.

Check whether the review report itself has been committed. Run `git log --oneline --all -- <report-path>` via Bash. If the report is not yet committed, tell the user:

Tell the user: "The review report is not yet committed. The audit-fix chain requires committing the report first: `docs(reviews): add <timestamp> review report`"

Confirm via AskUserQuestion (header: "Commit report"):
- Option 1 label: "Commit the report now" (Recommended) — description: `"Stage and commit the review report with docs(reviews): add <timestamp> review report"`
- Option 2 label: "Skip" — description: `"Continue without committing the report"`

On "Commit the report now": stage and commit the report via Bash.

Then, for the fix commit:
- Determine scope from the modified files. If all edits are within one skill/agent/rule, use that item's name. If multiple items were edited, use comma-separated scopes.
- Compose the commit message: `fix(<scope>): address findings from <timestamp> review`
- Show the commit message and confirm via AskUserQuestion (header: "Commit changes"):
  - Option 1 label: "Commit these changes" (Recommended) — description: `"Stage and commit: fix(<scope>): address findings from <timestamp> review"`
  - Option 2 label: "Skip" — description: `"Leave changes uncommitted"`
- On "Commit these changes": stage the modified files and commit via Bash. If the commit fails (non-zero exit), show the error and tell the user: "Commit failed. Changes are applied but uncommitted. Resolve the issue and commit manually."
- On "Skip": tell the user the changes are applied but uncommitted.

### 8. Report

Present the final status:
- Files modified
- Commits created (with hashes)
- Recommendations not applied (skipped or stopped)
- Manual-only findings not dispatched
Then end your response with this menu. Determine the verify command from `generated_by`: if `review-skill` → `/review-skill <path>`, if `review-agent` → `/review-agent <path>`, if `review-rule` → `/review-rule <path>`, if `review-claude-config` → `/review-claude-config <target>`.

Present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Verify improvements" (Recommended) — description: `"Run <verify-command> to detect cross-dimension regressions"`
- Option 2 label: "Review a specific item" — description: `"Invoke the matching /review-* command for a specific file"`
- Option 3 label: "Done" — description: `"End the workflow"`

On "Verify improvements": invoke the verify command. On "Review a specific item": ask which item, then invoke the matching `/review-*` command. On "Done": acknowledge and stop.

## Hard Rules

- **Edit-only operations.** Never delete files. Never create new files. Only edit existing files.
- **Scope restriction.** Only edit files listed in the review report's `summary` section. Never edit files outside the report's scope.
- **Preview before every edit.** Always show the current and recommended text before applying.
- **User confirmation at every stage.** Confirm before starting, before each edit, and before committing.
- **Audit-fix chain.** Always commit the report before committing fixes. Use the report timestamp in the fix commit message.
- **Preserve file structure.** Edits replace text blocks only. Never rewrite entire files.
- **High/Medium first.** Always process High and Medium recommendations before Low. Low impact recommendations are only offered after High/Medium are resolved, or when no High/Medium exist.
- **Delegate type-specific validation.** The orchestrator does not validate edits. Specialized appliers handle all type-specific checks.
