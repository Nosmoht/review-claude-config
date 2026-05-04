# Contributing

Thanks for your interest in `review-claude-config`. This guide covers the
contribution workflow. Maintainer-level operating policy (architecture,
hard constraints, command inventory) lives in [CLAUDE.md](CLAUDE.md).

## Prerequisites

- **Python 3.11+** — required for hooks and validation scripts
- **Claude Code CLI** — for testing skills/agents/hooks in dev mode
- **`uv`** (recommended) or `pip` — Python dependency manager
- **`make`** — drives the validation pipeline

## Local Setup

```bash
git clone https://github.com/Nosmoht/review-claude-config.git
cd review-claude-config

# Create a venv and install dev dependencies
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

The Makefile auto-detects `.venv/bin/python` and falls back to `python3`
when no venv is present.

## Running Validation

A single command runs every gate:

```bash
make validate
```

This executes:

| Step | Command | Purpose |
|------|---------|---------|
| Lint | `make lint` | `ruff check hooks/ scripts/` |
| Format | `make format` | `ruff format --check hooks/ scripts/` |
| Schema | `make schema-validate` | Validates JSON schemas under `schemas/` |
| Token budget | `make token-budget` | Enforces per-file token budgets |
| Tests | `make test` | `pytest tests/ -v --tb=short` |

`make validate` must pass before any commit lands on `main`.

## Commit Format

Conventional commits, scoped:

```
type(scope): short imperative description

Optional body, wrapped at 72 chars. Self-contained — no tracker IDs
(no NOS-, JIRA-, LIN-, GH issue links etc.) in the body.
```

Common types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`.

Commit signing and pre-commit hooks must run — never bypass with
`--no-verify` or `--no-gpg-sign`.

## Pull Request Process

1. Branch from latest `main`:
   ```bash
   git fetch origin && git pull origin main --ff-only
   git checkout -b <type>/<short-slug>
   ```
2. Make changes and run `make validate`.
3. For changes to skills, agents, rules, hooks, or CLAUDE.md, also run
   the matching review skill (see CLAUDE.md §"Verify changes with the
   repo's own review skills").
4. Open a PR against `main`. Keep PRs small and scoped.
5. Address review feedback; squash fixup commits into meaningful units
   before merge.

## Reporting Issues

Search existing issues first:

```bash
gh issue list --repo Nosmoht/review-claude-config
```

When opening a new issue, populate the testable acceptance criteria
(R1), defined deliverable (R2), single interpretation path (R3), and
bounded scope (R4) sections — see CLAUDE.md §"Issue Lifecycle" for the
canonical readiness predicates.

## Release Workflow

Releases are owned by [release-please](https://github.com/googleapis/release-please).
A push to `main` containing one or more conventional commits with type
`feat`, `fix`, `perf`, or `refactor` (or a `BREAKING CHANGE:` footer)
opens or updates the bot's release-PR. Merging that PR creates the Git
tag `vX.Y.Z` and the GitHub Release in the same workflow run.

The bot manages three places automatically:

- `.claude-plugin/plugin.json` → `version` (release-please `extra-files`)
- `.claude-plugin/marketplace.json` → `plugins[0].version` and
  `plugins[0].source.ref` (post-step via `scripts/sync_marketplace_ref.py`)
- `CHANGELOG.md` (release-please appends a generated section)

Maintainers may edit the bot's release-PR before merging — for example,
to add Keep-a-Changelog `### Migration` prose for breaking changes.
Manual edits on the bot-PR branch are preserved.

**Release-workflow rules — never:**

- Run `git tag vX.Y.Z` manually on `main`. The bot owns version state.
- Edit `.release-please-manifest.json` outside a release-PR merge.
- Edit `.claude-plugin/plugin.json#version` or
  `.claude-plugin/marketplace.json#plugins[0].version` directly. Bumps
  come from a release-PR merge.

To trigger a release: write conventional commits on `main`. The bot
opens or updates the release-PR within the next CI run.

To dry-run the workflow without producing a release: GitHub UI →
Actions → "Release Please" → Run workflow → branch=main → dry-run=true.

## Maintainer Reference

For architecture, hard constraints, label taxonomy, evidence layer,
and the full command inventory, see [CLAUDE.md](CLAUDE.md).
