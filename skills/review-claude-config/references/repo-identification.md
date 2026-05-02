---
name: repo-identification
description: Slug algorithm and report storage path for review/audit reports
last_refreshed: 2026-05-03
---

# Repo Identification

## Report Path

`${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-<skill>.md`

Skills MUST use the deterministic literal `${HOME}/.claude/plugins/data/claude-config/...`
for all read and write operations on report and audit data. Do NOT use the harness-injected
`CLAUDE_PLUGIN_DATA` env var in skill/agent/doc inline content; the harness sets it
per-active-plugin, which is incorrect under multi-plugin installs
(see https://github.com/Nosmoht/review-claude-config/issues/144).
Hooks may continue to use the env var because hook subprocesses are launched per-plugin and
the value is contract-reliable for hook Python.

## Slug Derivation

`slug = sanitize(basename(target_dir))`

Sanitize: lowercase, keep alphanumeric and hyphens, strip trailing slashes.

No git dependency. Slug is stable regardless of whether the target gains or loses git state.

## Frontmatter Fields

- `repo: <slug>` — required, derived from slug algorithm above
- `origin: <git-remote-url>` — optional, from `git remote get-url origin` when available

## Collision Detection

Before writing a report, if `${HOME}/.claude/plugins/data/claude-config/reports/<slug>/` already has reports with a different `origin:` value, warn the user about a potential slug collision.
