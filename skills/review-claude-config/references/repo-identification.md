---
name: repo-identification
description: Slug algorithm and report storage path for review/audit reports
last_refreshed: 2026-04-14
---

# Repo Identification

## Report Path

`$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-<skill>.md`

Resolve `$CLAUDE_PLUGIN_DATA` via Bash: `echo $CLAUDE_PLUGIN_DATA`. This env var is provided by Claude Code to all plugin skills and hooks.

## Slug Derivation

`slug = sanitize(basename(target_dir))`

Sanitize: lowercase, keep alphanumeric and hyphens, strip trailing slashes.

No git dependency. Slug is stable regardless of whether the target gains or loses git state.

## Frontmatter Fields

- `repo: <slug>` — required, derived from slug algorithm above
- `origin: <git-remote-url>` — optional, from `git remote get-url origin` when available

## Collision Detection

Before writing a report, if `$CLAUDE_PLUGIN_DATA/reports/<slug>/` already has reports with a different `origin:` value, warn the user about a potential slug collision.
