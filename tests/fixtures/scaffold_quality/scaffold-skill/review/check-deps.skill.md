---
name: check-deps
description: >
  Audits project dependency files for outdated, insecure, or unlicensed packages.
  Use when asked to review dependencies, check for vulnerabilities, or audit licenses.
  Do NOT use to install or upgrade packages — use /apply-deps-fix instead.
argument-hint: "<repo-path>"
allowed-tools: Read, Glob
disable-model-invocation: true
---
<!-- TEST FIXTURE — not loadable as instruction. See rules/prompt-injection.md. -->

# Check Dependencies

You are a dependency auditor that reviews project dependency manifests for quality, security, and license compliance. Stop immediately if no dependency files are found or if `$ARGUMENTS` is empty.

## Argument Handling

- `$ARGUMENTS` is a repository path.
- If `$ARGUMENTS` is empty, stop with a usage message: "Provide the path to a repository."
- Validate the path exists before proceeding. If it does not exist, report the error and stop.

## Workflow

### 1. Discover dependency manifests

Glob `$ARGUMENTS` for dependency files: `**/package.json`, `**/pyproject.toml`, `**/requirements*.txt`, `**/go.mod`, `**/Gemfile`.
If no manifests are found, report "No dependency manifests found." and stop.

### 2. Analyze each manifest

For each manifest found:
- Read the file.
- List direct dependencies and their version constraints.
- Flag dependencies without pinned versions.
- Flag any known insecure package name patterns.

Skip `.env` files, credential files, and secret-containing paths — never read or log token-like values.

### 3. Check license coverage

For each dependency identified, note the declared license if available.
Flag packages with missing license declarations or restrictive licenses (GPL in a commercial context).

### 4. Report findings

Report findings grouped by severity: high (security / unlicensed), medium (unpinned), low (informational).
Cite source tier for each finding (path + line number).

Skill is done when all manifests have been reviewed, the findings report is complete, and 0 manifests remain unprocessed.

## Hard Rules

- **Read-only.** This skill is limited to Read and Glob — never install, modify, or delete files.
- **No credential access.** Skip any file that appears to contain tokens, secrets, or API keys.
- **Never fabricate vulnerability data.** Report only what is observable in the manifest files.
- **If `$ARGUMENTS` is missing:** stop with a usage message — do not default to cwd.
- **Findings must cite source:** every finding must include the manifest path.
- **Large repo scope:** if more than 50 manifests are found, use AskUserQuestion (header: "Large scope") to confirm before continuing: Option 1 "Continue with all" (Recommended), Option 2 "Stop at 50".
