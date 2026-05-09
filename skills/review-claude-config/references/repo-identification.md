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

## Canonical Implementation

The slug derivation is implemented as a deterministic Bash helper:

```bash
bash bin/repo-slug.sh "$(pwd)"
```

All emitting skills MUST invoke this helper to compute `<repo-slug>` rather than
re-implementing the sanitize algorithm from prose. The helper is the single source
of truth; the prose above is documentation.

**Canonical examples:**

| Input path | Slug output |
|---|---|
| `/tmp/FlugFunkApp` | `flugfunkapp` |
| `/tmp/review-claude-config` | `review-claude-config` |
| `/tmp/MyRepo/` (trailing slash) | `myrepo` |
| `/tmp/my_repo` | `myrepo` (underscore stripped — see Collision Detection) |

**Cross-repo CWD convention:** All emitting skills derive the slug from CWD
(`$(pwd)`). When running a review or audit skill against an artifact in a
different repo, the user MUST `cd` into the target repo first before invoking
the skill. Failing to do so silently attributes the report to the wrong repo.
This convention matches the existing `apply-review-findings` precedent.

**Adding the allowlist entry** (for downstream plugin consumers): add
`"Bash(bash bin/repo-slug.sh:*)"` to `permissions.allow` in
`.claude/settings.local.json` to suppress the per-invocation permission prompt.

**SessionStart-hook alternative (rejected):** A hook that pre-computes the slug
at session start and injects it as an env var was considered but rejected because:
(1) the hook fires before the user sets a target, so CWD is the cloning/launch
dir, not the review target; (2) hook env vars are not available to skill prose
contexts; (3) just-in-time derivation from `$(pwd)` at invocation time is
architecturally simpler and matches Anthropic's context-engineering doctrine.

## Frontmatter Fields

- `repo: <slug>` — required, derived from slug algorithm above
- `origin: <git-remote-url>` — optional, from `git remote get-url origin` when available

## Collision Detection

Before writing a report, if `${HOME}/.claude/plugins/data/claude-config/reports/<slug>/` already has reports with a different `origin:` value, warn the user about a potential slug collision.

Note: underscores in repo names are stripped by `tr -cd 'a-z0-9-'`, so `my_repo`
and `myrepo` produce the same slug. The `origin:` mismatch warning handles this
post-hoc. File a follow-up issue if underscore-collision frequency warrants
extending the keep-set or adding pre-write collision detection logic.
