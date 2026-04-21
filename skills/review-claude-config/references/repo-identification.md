---
name: repo-identification
description: Slug algorithm and report storage path for review/audit reports
last_refreshed: 2026-04-14
---

# Repo Identification

## Report Path

`${CLAUDE_PLUGIN_DATA}/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-<skill>.md`

`${CLAUDE_PLUGIN_DATA}` is substituted inline by Claude Code wherever it appears in skill, agent, hook, or MCP content — the rendered value reaches the model as a literal absolute path. Do **not** resolve it via Bash (`echo $CLAUDE_PLUGIN_DATA`): the variable is not reliably exported to Bash-tool subprocesses, and when present it may carry the value of a different installed plugin. The official contract covers inline substitution and hook/MCP/LSP subprocess env only — see https://code.claude.com/docs/en/plugins-reference.

## Slug Derivation

`slug = sanitize(basename(target_dir))`

Sanitize: lowercase, keep alphanumeric and hyphens, strip trailing slashes.

No git dependency. Slug is stable regardless of whether the target gains or loses git state.

## Frontmatter Fields

- `repo: <slug>` — required, derived from slug algorithm above
- `origin: <git-remote-url>` — optional, from `git remote get-url origin` when available

## Collision Detection

Before writing a report, if `${CLAUDE_PLUGIN_DATA}/reports/<slug>/` already has reports with a different `origin:` value, warn the user about a potential slug collision.
