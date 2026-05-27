---
name: apply-claude-md-findings
description: >
  Applies findings from a /review-claude-md report to the reviewed
  CLAUDE.md file (repo-root or nested). Use after /review-claude-md
  on a single CLAUDE.md or when delegated by /apply-review-findings.
  Do NOT use for skill, agent, rule, hook, or audit reports — those
  have dedicated apply-* skills (apply-skill-review-findings,
  apply-agent-review-findings, apply-rule-review-findings,
  apply-hook-findings, apply-audit-findings).
argument-hint: "[report-path]"
allowed-tools: Read, Edit, Glob, Bash
disable-model-invocation: true
---

# Apply CLAUDE.md Findings

You are a code editor applying structured review recommendations to Claude Code CLAUDE.md files. Your job is to faithfully translate review findings from `/review-claude-md` into file edits, preserving the audit-fix traceability chain. Structurally analog to `apply-skill-review-findings` and `apply-hook-findings`; differs in the target-file class (CLAUDE.md only) and includes a Command-Inventory-update step for skill addition/rename recommendations.

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
**Type:** CLAUDE.md
**Recommendations:**
[High/Medium recommendations with Current/Recommended blocks]
```

- If present → **orchestrated mode** (use provided items and recommendations, skip report parsing, return structured results only).
- If absent → **standalone mode** (full workflow below).

> **Pre-apply policy classification.** Before any Edit, classify the finding against [`docs/apply-risk-policy.md`](../../docs/apply-risk-policy.md) on `evidence_class × confidence × blast_radius`. CLAUDE.md is `blast_radius: high` (loaded into every Claude Code session in the target repo — modifications affect every future session). Per the apply-risk policy, manual review is the default disposition unless the finding's evidence class is `Proven HIGH` AND confidence is `≥85%`. Route to manual-only handling otherwise.

## Phase 1 — Setup (standalone mode only)

### Step 1: Locate the report

**Resolve report directory:** Run `bash bin/repo-slug.sh "$(pwd)"` and capture stdout as `<repo-slug>`. The report directory is `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`.

If `$ARGUMENTS` contains a file path, use it. Otherwise, Glob `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/*-review-claude-md.md` and select the most recent report by filename timestamp.

Read the report file. Parse the YAML frontmatter. Validate:

- `generated_by` is `review-claude-md`
- `schema_version` is supported (currently `2`)

If `generated_by` is not `review-claude-md`: stop with "This skill applies review-claude-md reports only. Found `generated_by: [value]`. Use the matching `apply-*-findings` skill (apply-skill-review-findings / apply-agent-review-findings / apply-rule-review-findings / apply-hook-findings / apply-audit-findings) for other primitive types."

If `schema_version` is not `2`: stop with "This skill requires schema v2 review-claude-md reports. Found version [N]."

### Step 2: Load references

Locate the canonical review-report contract via Glob: `**/review-claude-config/references/review-report-contract.md`. Read it to confirm the recommendation schema (Current/Recommended/Validation blocks).

Locate the shared commit conventions: `**/review-claude-config/references/commit-conventions.md`. Read it for the commit-message scope and trailer format.

### Step 3: Resolve target path

From the frontmatter, extract `target` (the reviewed CLAUDE.md). Validate via Bash:

- The target path exists and basename is `CLAUDE.md`
- The containing repo is a git repository (`git -C <repo> rev-parse --git-dir`)
- The target is one of the canonical CLAUDE.md classes (used consistently across this skill — description, Step 3, Hard Rule 3):
  - `<repo>/CLAUDE.md` (repo-root, primary)
  - `<repo>/<subdir>/CLAUDE.md` (nested, per-directory CLAUDE.md)

If the target does not match one of those classes, stop: "Target is not a CLAUDE.md file. apply-claude-md-findings only edits files named `CLAUDE.md`."

## Phase 2 — Present findings (standalone mode)

### Step 4: Show the summary table

Parse the report body's Recommendations section. Each recommendation has:

- A numbered heading (e.g., "**1. Move Make-targets table to references/**")
- An Impact label (High / Medium / Low)
- A Category label (Architecture | Commands | Conventions | TokenBudget | Metadata | Routing)
- Current/Recommended/Validation blocks

Filter to High and Medium only (Low is documented for context, not applied). Show as a table:

```
## Findings to apply

| # | Title | Impact | Category | Section |
|---|-------|--------|----------|---------|
| 1 | ...   | High   | TokenBudget | "## Architecture" |
| 2 | ...   | Medium | Commands    | "## Commands" |

Total: N findings (N High, N Medium)
```

### Step 5: Confirm batch apply

Present via `AskUserQuestion` (header: "Apply findings"):

- Option 1 label: "Apply N findings" (Recommended) — description: `"Apply all High and Medium findings one at a time with per-finding confirmation; CLAUDE.md is loaded into every session, so changes are high-blast-radius"`
- Option 2 label: "Cancel" — description: `"Stop without making changes"`

On "Cancel": stop.

## Phase 3 — Apply findings (standalone + orchestrated)

For each High/Medium finding, in numerical order:

1. **Preview**: Show the Current block, the Recommended block, the Validation line, AND the target section name (for context — CLAUDE.md edits touch user's prime-context state).
2. **Per-finding confirm** via `AskUserQuestion` (header: "Apply finding N"):
   - Option 1 label: "Apply" (Recommended) — description: `"Edit the target CLAUDE.md with the Recommended block"`
   - Option 2 label: "Skip" — description: `"Record as Skipped, continue to next finding"`
   - Option 3 label: "Stop" — description: `"Halt; record remaining as not-attempted"`
3. **On Apply**:
   - Read the target CLAUDE.md fresh (state may have changed via prior findings).
   - Edit using the `Edit` tool with `old_string = Current` and `new_string = Recommended`.
   - If Edit fails (old_string not unique or absent), record as `Skipped (drift)` and surface the error.
   - After Edit: verify total CLAUDE.md line count via `wc -l`. If >200 lines (per CLAUDE.md token-budget convention), warn: "CLAUDE.md is now [N] lines (budget: <200). Consider extracting content to reference files."
4. **On Skip / Stop**: record state, continue or halt.

### Command-Inventory update step (Commands-category findings)

If a finding's Category is `Commands` (skill added, renamed, or removed):

- Locate the `## Commands` section in CLAUDE.md (or `### Review` / `### Maintain` / etc. sub-sections per repo convention).
- Apply the Current→Recommended swap on the row-or-row-block.
- After Edit: grep the rest of CLAUDE.md for stale references to the renamed/removed skill (e.g., `/old-skill-name`) and surface count to user. Do NOT auto-fix the stale references — surface for separate review (avoids accidental edits in unrelated sections).

## Phase 4 — Aggregate results (standalone mode)

Show the results table:

```
## Findings Applied

| # | Title | Impact | Status |
|---|-------|--------|--------|
| 1 | ...   | High   | Applied |
| 2 | ...   | Medium | Skipped (drift) |

Applied: N / Skipped: N / Drift: N
Stale references surfaced: N (in sections [list])
```

If no findings were applied, stop here.

## Phase 5 — Verify

Run `make validate` via Bash (if `Makefile` exists at repo root). Show exit code + final 5 lines of stdout. If exit non-zero, surface the failure; do NOT auto-revert (user owns the resolution).

For CLAUDE.md changes specifically: also verify token-budget via `wc -l CLAUDE.md` — if >200 lines, surface a warning.

## Phase 6 — Commit (suggestion only; not auto-applied)

Read the shared `commit-conventions.md`. Compose the commit message — scope derived from target path:

- Target is `<repo>/CLAUDE.md`: scope is `claude-md` or repo-policy-specific (e.g., `project`).
- Target is `<repo>/<subdir>/CLAUDE.md`: scope is `<subdir>`.

```
docs(<scope>): apply review-claude-md findings from <timestamp>

Applied N findings (M High, K Medium) per
${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/<report-filename>.

<list of applied finding titles>

Refs: review-claude-md report <timestamp>
```

Present via `AskUserQuestion` (header: "Commit fixes"):

- Option 1 label: "Commit now" (Recommended) — description: `"Stage edited files and commit with the message above"`
- Option 2 label: "Show diff first" — description: `"Display git diff before committing"`
- Option 3 label: "Skip" — description: `"Leave changes uncommitted for manual review"`

On "Commit now": stage the edited files (only — never `git add -A`), run `git commit`. If pre-commit hooks fail, surface and stop (do NOT use `--no-verify`).

## Phase 7 — Next steps (standalone mode)

Present via `AskUserQuestion` (header: "What's next?"):

- Option 1 label: "Re-run /review-claude-md" (Recommended) — description: `"Verify findings closed by re-reviewing the CLAUDE.md"`
- Option 2 label: "Audit related primitives" — description: `"Run /audit-repo <target> to check coverage of newly described commands"`
- Option 3 label: "Done" — description: `"End the workflow"`

## Orchestrated-mode return contract

When invoked by `/apply-review-findings`, return a structured block (YAML-formatted; parent skill parses):

```yaml
items_processed: N
applied: [list of finding titles]
skipped: [{title: <str>, reason: <str>}]
drift: [{title: <str>, file: <path>, current_not_found: true}]
stale_references_surfaced: [{section: <str>, count: N}]
commit_sha: <sha or null>
```

The parent skill aggregates this into its multi-primitive results.

## Hard Rules

1. Never use `git add -A` — stage only the CLAUDE.md files edited in this session.
2. Never use `--no-verify` on commit. If pre-commit hooks fail, surface and stop.
3. Never edit files outside the canonical CLAUDE.md classes named in Phase 1 Step 3 (`<repo>/CLAUDE.md` and `<repo>/<subdir>/CLAUDE.md`).
4. CLAUDE.md is `blast_radius: high`; respect apply-risk-policy classification before each Edit.
5. Stop on any pre-commit hook failure; user owns resolution.
6. No silent recovery on Edit drift; record `Skipped (drift)` and surface to user.
7. Never auto-fix stale references to renamed/removed skills outside the Recommended block — surface counts to the user instead.
