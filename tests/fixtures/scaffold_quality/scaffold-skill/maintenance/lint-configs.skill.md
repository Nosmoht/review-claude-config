---
name: lint-configs
description: >
  Validates and fixes linting configuration files across the repository.
  Use when adding or updating ESLint, Prettier, ruff, or similar tool configs.
  Do NOT use for application code lint errors — use /review-skill instead.
argument-hint: "[config-path]"
allowed-tools: Read, Write, Edit, Glob
disable-model-invocation: true
---
<!-- TEST FIXTURE — not loadable as instruction. See rules/prompt-injection.md. -->

# Lint Configs

You are a configuration validator that checks linting setup for correctness and project consistency. Stop immediately if no config files are found or if `$ARGUMENTS` is empty.

## Argument Handling

- `$ARGUMENTS` is the path to a config file or directory.
- If `$ARGUMENTS` is empty, stop with a usage message: "Provide the path to a config file or directory."
- If the path does not exist, report the error and stop.
- Validate the path exists before proceeding.

## Workflow

### 1. Discover configs

Glob `$ARGUMENTS` for `**/.eslintrc*`, `**/ruff.toml`, `**/.ruff.toml`, `**/prettier.config.*`.
If no configs are found, report "No linting configuration files found." and stop.

### 2. Analyze each config

For each config file found, read it and check for required fields per the tool type.
Identify missing or malformed entries.
If a file is unreadable, report the error and continue.

### 3. Report findings

List each finding with: file path, finding type (missing / malformed / outdated), suggested fix.
If no findings, report "All linting configs look correct."

Skill is done when all configs in scope have been reviewed and findings listed.

### 4. Apply fixes (if requested)

Write operations are restricted to config files at the validated path only. Edit operations are restricted to the same scope.

Only apply fixes after explicit confirmation via AskUserQuestion (header: "Apply fixes"):
- Option 1 label: "Apply all fixes" (Recommended) — description: "Write corrected config files"
- Option 2 label: "Show diff only" — description: "Display proposed changes without writing"
- Option 3 label: "Cancel" — description: "Stop without writing anything"

On "Cancel": stop without writing.
On "Show diff only": display proposed changes and stop.
On "Apply all fixes": write corrected configs and proceed to Step 5.

Fallback: if write tools are unavailable, fall back to read-only mode — skip this step and note the limitation.

If any write fails, report the error and continue.

### 5. Report results

Report: total configs reviewed, fixes applied or proposed, any remaining issues.

## Hard Rules

- **Never overwrite configs without confirmation.** AskUserQuestion approval required before any Write or Edit.
- **Never modify application source files.** Write and Edit are restricted to config files in scope.
- **Credentials:** never read, log, or output credential values. Skip `.env` files and files containing tokens or secrets.
- **If `$ARGUMENTS` is missing:** stop with a usage message — never default to cwd.
- **On write failure:** report the error and continue — do not abort the run.
