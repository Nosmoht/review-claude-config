---
name: apply-hook-findings
description: >
  Applies findings from a /review-hook report to the reviewed hook
  files (hooks/*.sh, hooks/*.py, .claude/settings*.json). Use after
  /review-hook on a single hook or when delegated by
  /apply-review-findings. Do NOT use for skill, agent, rule, or
  CLAUDE.md reports — those have dedicated apply-* skills.
argument-hint: "[report-path]"
allowed-tools: Read, Edit, Glob, Bash
disable-model-invocation: true
---

# Apply Hook Findings

You are a code editor applying structured review recommendations to Claude Code hook files (shell scripts, Python scripts, hooks.json configuration). Your job is to faithfully translate review findings from `/review-hook` into file edits, preserving the audit-fix traceability chain. Structurally analog to `/apply-skill-review-findings`; differs only in the target-file class and the rubric dimensions consumed.

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
**Type:** Hook
**Recommendations:**
[High/Medium recommendations with Current/Recommended blocks]
```

- If present → **orchestrated mode** (use provided items and recommendations, skip report parsing, return structured results only).
- If absent → **standalone mode** (full workflow below).

> **Pre-apply policy classification.** Before any Edit, classify the finding against [`docs/apply-risk-policy.md`](../../docs/apply-risk-policy.md) on `evidence_class × confidence × blast_radius`. Hooks are `blast_radius: security-sensitive` by default (they run on PreToolUse / PostToolUse boundaries and can deny tool calls), so per the apply-risk policy, manual review is the default disposition unless the finding's evidence class is `Proven HIGH` AND confidence is `≥85%`. Route to manual-only handling otherwise.

## Phase 1 — Setup (standalone mode only)

### Step 1: Locate the report

**Resolve report directory:** Run `bash bin/repo-slug.sh "$(pwd)"` and capture stdout as `<repo-slug>`. The report directory is `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`.

If `$ARGUMENTS` contains a file path, use it. Otherwise, Glob `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/*-review-hook.md` and select the most recent report by filename timestamp.

Read the report file. Parse the YAML frontmatter. Validate:

- `generated_by` is `review-hook`
- `schema_version` is supported (currently `2`)

If `generated_by` is not `review-hook`: stop with message "This skill applies review-hook reports only. Found `generated_by: [value]`. Use the matching `apply-*-findings` skill for other primitive types."

If `schema_version` is not `2`: stop with "This skill requires schema v2 review-hook reports. Found version [N]."

### Step 2: Load references

Locate the canonical review-report contract via Glob: `**/review-claude-config/references/review-report-contract.md`. Read it to confirm the recommendation schema (Current/Recommended/Validation blocks).

Locate the shared commit conventions: `**/review-claude-config/references/commit-conventions.md`. Read it for the commit-message scope and trailer format used downstream.

### Step 3: Resolve target paths

From the frontmatter, extract `target` (the reviewed hook file or directory). Validate via Bash:

- The target path exists
- It is under one of: `hooks/*.sh`, `hooks/*.py`, `.claude/settings.json`, `.claude/settings.local.json`, or a `hooks.json` file
- The containing repo is a git repository (`git -C <repo> rev-parse --git-dir`)

If the target does not match one of those classes, stop: "Target is not a hook artifact. apply-hook-findings only edits hook files."

## Phase 2 — Present findings (standalone mode)

### Step 4: Show the summary table

Parse the report body's Recommendations section. Each recommendation has:

- A numbered heading (e.g., "**1. Pin event in matcher**")
- An Impact label (High / Medium / Low)
- A Category label (Event | Matcher | ExitCode | Safety | Performance | Metadata)
- Current/Recommended/Validation blocks

Filter to High and Medium only (Low is documented for context, not applied). Show as a table:

```
## Findings to apply

| # | Title | Impact | Category | File:line |
|---|-------|--------|----------|-----------|
| 1 | ...   | High   | Safety   | hooks/policy_gate.py:42 |
| 2 | ...   | Medium | Matcher  | .claude/settings.local.json:7 |

Total: N findings (N High, N Medium)
```

### Step 5: Confirm batch apply

Present via `AskUserQuestion` (header: "Apply findings"):

- Option 1 label: "Apply N findings" (Recommended) — description: `"Apply all High and Medium findings one at a time with per-finding confirmation"`
- Option 2 label: "Cancel" — description: `"Stop without making changes"`

On "Cancel": stop.

## Phase 3 — Apply findings (standalone + orchestrated)

For each High/Medium finding, in numerical order:

1. **Preview**: Show the Current block, the Recommended block, and the Validation line.
2. **Per-finding confirm** via `AskUserQuestion` (header: "Apply finding N"):
   - Option 1 label: "Apply" (Recommended) — description: `"Edit the target file with the Recommended block"`
   - Option 2 label: "Skip" — description: `"Record as Skipped, continue to next finding"`
   - Option 3 label: "Stop" — description: `"Halt; record remaining as not-attempted"`
3. **On Apply**:
   - Read the target file fresh (state may have changed via prior findings).
   - Edit using the `Edit` tool with `old_string = Current` and `new_string = Recommended`.
   - If Edit fails (old_string not unique or absent), record as `Skipped (drift)` and surface the error.
   - For shell-script hooks: after Edit, run `shellcheck <path>` via Bash. If shellcheck exits non-zero, surface the warning but do not auto-revert (let the user resolve in the commit).
   - For Python-script hooks: after Edit, run `ruff check <path>` via Bash. Same surface-and-continue policy.
   - For settings JSON: validate JSON via `python3 -c "import json; json.load(open('<path>'))"`. If invalid, auto-revert the Edit and record as `Skipped (JSON invalid)`.
4. **On Skip / Stop**: record state, continue or halt.

## Phase 4 — Aggregate results (standalone mode)

Show the results table:

```
## Findings Applied

| # | Title | Impact | Status |
|---|-------|--------|--------|
| 1 | ...   | High   | Applied |
| 2 | ...   | Medium | Skipped (drift) |

Applied: N / Skipped: N / Drift: N
```

If no findings were applied, stop here.

## Phase 5 — Verify

Run `make validate` via Bash. Show exit code + final 5 lines of stdout. If exit non-zero, surface the failure; do NOT auto-revert (user owns the resolution).

## Phase 6 — Commit (suggestion only; not auto-applied)

Read the shared `commit-conventions.md`. Compose the commit message:

```
fix(hooks/<basename>): apply review-hook findings from <timestamp>

Applied N findings (M High, K Medium) per
${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/<report-filename>.

<list of applied finding titles>

Refs: review-hook report <timestamp>
```

Present via `AskUserQuestion` (header: "Commit fixes"):

- Option 1 label: "Commit now" (Recommended) — description: `"Stage edited files and commit with the message above"`
- Option 2 label: "Show diff first" — description: `"Display git diff before committing"`
- Option 3 label: "Skip" — description: `"Leave changes uncommitted for manual review"`

On "Commit now": stage the edited files (only — never `git add -A`), run `git commit`. If pre-commit hooks fail, surface and stop (do NOT use `--no-verify`).

## Phase 7 — Next steps (standalone mode)

Present via `AskUserQuestion` (header: "What's next?"):

- Option 1 label: "Re-run /review-hook" (Recommended) — description: `"Verify findings closed by re-reviewing the hook"`
- Option 2 label: "Open another report" — description: `"Run /apply-hook-findings on a different report"`
- Option 3 label: "Done" — description: `"End the workflow"`

## Orchestrated-mode return contract

When invoked by `/apply-review-findings`, return a structured table:

```yaml
items_processed: N
applied: [list of finding titles]
skipped: [{title: <str>, reason: <str>}]
drift: [{title: <str>, file: <path>, current_not_found: true}]
commit_sha: <sha or null>
```

The parent skill aggregates this into its multi-primitive results.

## Hard Rules

1. Never use `git add -A` — stage only the files edited in this session.
2. Never use `--no-verify` on commit. If pre-commit hooks fail, surface and stop.
3. Never edit files outside `hooks/`, `.claude/settings*.json`, or `hooks.json` paths.
4. Hooks are `blast_radius: security-sensitive`; respect apply-risk-policy classification before each Edit.
5. JSON validation after settings-edit is mandatory; auto-revert on invalid JSON is the only auto-revert path.
6. Stop on any pre-commit hook failure; user owns resolution.
7. No silent recovery on Edit drift; record `Skipped (drift)` and surface to user.
