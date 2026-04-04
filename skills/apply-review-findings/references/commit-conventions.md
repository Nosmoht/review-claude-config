---
name: commit-conventions
description: Scoped conventional commit format and audit-fix chain linking rules for review finding application
last_refreshed: 2026-03-25
---

## Commit Format

`type(scope): description`

## Valid Types

- `feat` — New skill or feature
- `fix` — Bug fix or review finding remediation
- `refactor` — Restructuring without behavior change
- `docs` — Documentation, reports, research files
- `test` — Test additions or modifications
- `chore` — Maintenance tasks

## Scope Rules

- Skill name without suffix: `review-claude-config` → `review-skill` is NOT used; use the full skill name or a short form like `review-skill`
- For CLAUDE.md changes: `project`
- For review reports: `reviews`
- For research files: `research`
- Multiple scopes: comma-separated — `fix(review-skill,refresh-skill): ...`

## Audit-Fix Chain

1. **Report commit first:** `docs(reviews): add YYYY-MM-DDTHHMMSS review report`
2. **Fix commit after:** `fix(<scope>): address findings from YYYY-MM-DDTHHMMSS review`
3. The timestamp links report and fixes for traceability in git history.

## Timestamp Format

`YYYY-MM-DDTHHMMSS` — extracted from the report filename (e.g., `2026-03-24T161200-review-claude-config.md` → `2026-03-24T161200`).
