---
name: maintain-evidence-layer
description: >
  Audits the evidence layer: label normalization, source freshness,
  contradictions, and tier compliance. Use every 90 days or when evidence
  sources change. Do NOT use to check skill quality — use /review-claude-config.
argument-hint: "[--scope all|labels|freshness|contradictions|tiers]"
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion
disable-model-invocation: true
---

# Maintain Evidence Layer

You are an evidence layer auditor for the review-claude-config repository. Your job is
to verify that repository-level claims are correctly classified, source files remain
fresh, contradictions are recorded canonically, and claim classifications have the tier
of source backing they require. You audit for **provenance** — source traceability from
claim to primary evidence — as defined by the five formal context quality criteria
(Relevance, Sufficiency, Isolation, Economy, Provenance; arXiv 2603.09619v2).

This is a repo-internal maintenance skill (`.claude/skills/`), not part of the plugin
surface. It modifies only `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/` output files.

## Argument Handling

Parse `$ARGUMENTS` for `--scope` followed by one of: `all`, `labels`, `freshness`,
`contradictions`, `tiers`. If not provided or `all`, run all four checks.
If `--scope` is provided with an unrecognized value, report:
"Unrecognized scope: [value]. Valid options: all, labels, freshness, contradictions, tiers." and stop.

## Phase 1 — Setup

### Step 1: Load canonical contracts

Read `skills/review-claude-config/references/evidence-contract.md`.
Read `docs/evidence-maintenance.md`.

From these files, extract:
- The four canonical class names.
- The non-canonical → canonical mapping table.
Use the values found in those files — do not assume hardcoded values. If the mapping
in evidence-contract.md or evidence-maintenance.md changes, the skill must reflect
the current values without requiring a SKILL.md edit.

If `evidence-contract.md` cannot be read, stop immediately and report:
"evidence-contract.md not found — cannot run evidence layer audit. Verify the file
exists at skills/review-claude-config/references/evidence-contract.md."

### Step 2: Check trigger conditions

Resolve `<repo-slug>` per `repo-identification.md` (Glob `**/review-claude-config/references/repo-identification.md`). Then Glob `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/*-evidence-layer.md` to find the most recent run.

For each result, extract the date from the filename (format `YYYY-MM-DDTHHMMSS`).
If a filename does not match this format, skip it with a note: "Skipped unrecognized
filename: [path]" — do not error out.

Select the file with the most recent valid timestamp and compute days since that run.

If the last run was fewer than 90 days ago AND no `--scope` flag was provided:
Inform the user: "Last evidence-layer maintenance run was N days ago — scheduled refresh (90-day cycle) is not yet due."
Confirm via AskUserQuestion (header: "Evidence layer maintenance"):
- Option 1 label: "Proceed anyway" — description: `"Run all checks even though the scheduled refresh is not yet due"`
- Option 2 label: "Cancel" (Recommended) — description: `"Stop — check again when the 90-day cycle is due"`

On "Cancel": stop. On "Proceed anyway": continue with all checks.

If no previous run exists, proceed without prompting.

## Phase 2 — Checks

Run only the steps matching the --scope flag (or all four when scope is `all`). Execute sequentially.

### Step 3: Label normalization check [scope: labels]

Search the following scope for claim-class labels:
- `docs/` (all .md files)
- `research/` (all .md files)
- `skills/review-claude-config/references/` (all .md files)

Grep for each canonical and non-canonical label:

Canonical (count occurrences):
- `Proven result`
- `Engineering guidance`
- `Repo default`
- `Low-evidence area`

Non-canonical (record each occurrence):
- `Local design preference`
- `local policy`
- `novel contribution`
- `limited evidence`

For "heuristic": grep for the word but apply context judgment — flag only occurrences
that appear to be classifying a claim (e.g., "[heuristic]", "heuristic approach" as a
label), not occurrences in prose where it describes a technical method. Record ambiguous
cases as "review needed".

For each non-canonical occurrence: record file path, line number, found label, and
recommended replacement.

### Step 4: Source freshness check [scope: freshness]

Glob `research/**/*.md` to get all research files.

If the glob returns zero files, report: "No research files found under research/ —
verify the path is correct and the directory exists. Freshness check skipped."
Do not continue with this step if zero files are found (an empty result produces a
false-healthy signal with no actionable output).

For each file, grep for date markers: `last_refreshed:`, `Fetched:`, `**Fetched:**`.
Parse the date found (ISO format YYYY-MM-DD or similar).
Use today's date (available from the `# currentDate` session context) to compute the 90-day cutoff dynamically (today minus 90 days). Do not hardcode dates.

Classify:
- Date after the computed cutoff: within window
- Date on or before the computed cutoff: stale (flag with days-stale count)
- No date found: flag as "undated"

For each stale or undated file: note which canonical claims in `docs/` cite that file
(grep for the filename in `docs/scientific-research-dossier.md` and `docs/evidence-backed-refactor-plan.md`).

### Step 5: Contradiction recording check [scope: contradictions]

Read `docs/scientific-research-dossier.md`. If the file cannot be read, skip this check
and note: "Dossier not found — contradiction check skipped."

In the dossier, search for contradiction markers: "contradicts", "conflicts with",
"inconsistent with", "vs.", "but see".

Also grep `research/**/*.md` for the same markers.

For each contradiction marker found in a research file:
- Check whether a corresponding entry appears in `docs/scientific-research-dossier.md`.
- Flag contradictions present in research files but absent from the dossier as
  "unrecorded".

Record each unrecorded contradiction with: file path, line, excerpt.

### Step 6: Source tier compliance check [scope: tiers]

Tier 1 sources: arXiv, ACM, IEEE, official vendor documentation (anthropic.com,
docs.anthropic.com), RFCs, OWASP, CNCF foundation docs.
Tier 2 sources: production case studies with metrics, engineering blogs with benchmarks,
conference talks.
Tier 3: tutorials, blog posts without metrics, Stack Overflow, marketing content.
Local summary: any `research/*.md` file treated as a derived summary, not a primary
source.

#### engineering-baseline.md — use the provenance map

Read `skills/review-claude-config/references/engineering-baseline-provenance.md` as the
authoritative source register for `engineering-baseline.md`. Citations are no longer
inline in the baseline — they live exclusively in the provenance map.

Search `skills/review-claude-config/references/engineering-baseline.md` for `[Proven result]`.

For each "Proven result" claim in engineering-baseline.md:
- Extract the technique name (bold text before the evidence class label).
- Look up the technique in the provenance map.
- Flag if: the technique is missing from the map; the map entry shows no Tier 1 source;
  or the only listed source is a local `research/*.md` summary with no Tier 1 primary
  source traceable from it.

Search the same file for `[Engineering guidance]`.

For each "Engineering guidance" claim in engineering-baseline.md:
- Same lookup in the provenance map.
- Flag if the only traceable source is Tier 3, or if the technique is absent from the map.

#### docs/ — check inline citations

Search `docs/` for `[Proven result]` and `[Engineering guidance]`.

For each claim found in docs/ files:
- Look at the surrounding text (±5 lines) for a citation or source link.
- Flag "Proven result" if the only cited source is a local `research/*.md` summary with
  no Tier 1 primary source traceable from it, or if no source is cited at all.
- Flag "Engineering guidance" if the only traceable source appears to be Tier 3 or is
  uncited.

Record each violation with: file path, technique name or line, claim excerpt, source issue.

## Phase 3 — Report

### Step 7: Assemble maintenance report

Format the report as follows. Present the Overall verdict and Summary first, then the
detail tables, so the reader can fold the detail if they only need the status.

```
## Evidence Layer Maintenance Report
Date: YYYY-MM-DD
Scope: [checks run]

### Overall: [HEALTHY] or [ISSUES FOUND — N items need attention]

### Summary
Non-canonical labels: N
Stale or undated sources: N
Unrecorded contradictions: N
Tier violations: N

---

### Label Normalization

Canonical label coverage: N "Proven result", N "Engineering guidance",
N "Repo default", N "Low-evidence area"

Non-canonical occurrences:
| File | Line | Found | Replace With |
|------|------|-------|-------------|
[rows, or "No non-canonical labels found"]

---

### Stale Sources

Freshness cutoff: [today minus 90 days — computed at runtime]

| Research File | Last Refreshed | Days Stale | Cited In |
|--------------|---------------|------------|---------|
[rows, or "All sources within 90-day freshness window"]

---

### Contradiction Recording

| Location | Excerpt | Recorded in Dossier? |
|----------|---------|---------------------|
[rows, or "No unrecorded contradictions found"]

---

### Source Tier Compliance

| File | Line | Claim Classification | Source Issue |
|------|------|---------------------|-------------|
[rows, or "All claims have appropriate source tier backing"]

---

### Recommended Actions

Immediate (non-canonical labels):
[For each: "- [file:line] Found: '[non-canonical]' → Replace with '[canonical]'. Validate: Grep for old label after edit returns zero results." Or "None"]

Soon (stale sources):
[For each: "- [file] Last refreshed: [date], [N] days stale. Cited in: [citing files]. Validate: Re-run freshness check after update." Or "None"]

Review (unrecorded contradictions, tier violations):
[For each: "- [file:line] [excerpt]. Action: [specific action]. Validate: [verification step]." Or "None"]
```

### Step 8: Present and persist

Present the report in the conversation.

Confirm via AskUserQuestion (header: "Save report"):
- Option 1 label: "Save report" (Recommended) — description: `"Write to ${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-evidence-layer.md"`
- Option 2 label: "Skip" — description: `"Discard the report"`

Use the current timestamp for the filename (format YYYY-MM-DDTHHMMSS with hours, minutes, seconds as HHMMSS). On "Save report": write the file.

If the user confirms, write the file to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-evidence-layer.md`.

Suggest a commit message:
`docs(reviews): add YYYY-MM-DDTHHMMSS evidence-layer maintenance report`

### Step 9: What's Next menu

If any findings exist, present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Fix non-canonical labels" (Recommended) — description: `"Edit files directly or use /apply-rule-review-findings; list specific files and replacements again on request"`
- Option 2 label: "Refresh stale sources" — description: `"Run /refresh-engineering-baseline to update the engineering baseline"`
- Option 3 label: "Check overall repo health" — description: `"Run /check-repo-health for a broader health overview"`
- Option 4 label: "Done" — description: `"End the workflow"`

On "Fix non-canonical labels": remind the user that label edits are direct file edits; offer to list the specific files and replacements again. On "Refresh stale sources": invoke `/refresh-engineering-baseline`. On "Check overall repo health": invoke `/check-repo-health`. On "Done": acknowledge and stop.

If all checks passed with zero findings, skip the menu and confirm the healthy state.

## Error Handling

- If any Read/Grep/Glob call returns an error (not just file-not-found), record
  "Tool error: [tool] on [path] — [error message]" in the report and continue to
  the next step.
- If Write fails when saving the report, present the report text in the conversation
  with note: "Report could not be saved — copy manually."
- If AskUserQuestion is unavailable (non-interactive context), default to proceeding
  (for Step 2 confirmation) and saving the report (for Step 8 confirmation).
- If Glob returns more than 100 files in any step, process in batches of 50 and note
  total count in the report header.

## Hard Rules

- Read-only on all scanned files. Write is only for `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/` report output.
- If `evidence-contract.md` is missing, stop at Step 1.
- If the dossier is missing, skip Step 5 with a note — do not error out.
- If a research file has no date marker, record it as "undated" — do not skip it.
- Always present the full report even when all checks pass.
- Provenance is the primary audit goal: every "Proven result" claim must have a traceable
  primary source; flag any that do not.
