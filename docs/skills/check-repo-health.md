# check-repo-health

Verify freshness, token budgets, and reference integrity across the repository and present one health dashboard.

## Overview

| Property | Value |
|----------|-------|
| **Name** | check-repo-health |
| **Location** | `skills/check-repo-health/SKILL.md` |
| **Type** | Maintenance |
| **Allowed Tools** | Read, Glob |
| **Argument Hint** | `[all\|freshness\|tokens\|integrity] [--validation]` |
| **Mode** | Standalone only |
| **Research Behavior** | None |

## Purpose

`check-repo-health` is a read-only diagnostic skill. It verifies freshness of maintained references, token-budget compliance, and integrity of cross-file references. This page keeps the behavior that is specific to the health dashboard. Shared contract details remain in the reference files it consumes.

## Major Phases

1. Parse the requested check set and load threshold defaults.
2. Discover the relevant skill, reference, cache, research, and top-level docs.
3. Run freshness, token, and/or integrity checks.
4. Present one dashboard and, when needed, targeted remediation suggestions.

## Runtime-Specific Behavior

- **Freshness:** evaluates reference files with `last_refreshed` metadata and cache entries using the configured thresholds.
- **Token budgets:** uses the repo's `chars/4` approximation and always labels it as approximate.
- **Integrity:** checks top-level doc references, cross-skill references, and the Package-3 review/apply/doc alignment rules.
- **Package-3 semantics:** integrity results may surface `PASS`, `WARN`, `FAIL`, or `UNREGISTERED`. `UNREGISTERED` is used when drift exists without a hard missing-target failure.
- **Doc/runtime drift detection:** the integrity pass explicitly checks low/manual-only behavior, analytics discovery and partitioning rules, and canonical review-contract usage where relevant.
- **Validation mode:** `--validation` is the bounded release gate. It skips the heuristic `UNREGISTERED` scan, reports only PASS/WARN/FAIL counts plus non-PASS rows, and omits the follow-up menu. The normal full dashboard remains the default behavior.

## Interactions

- **Called by:** user directly
- **May suggest:** `/refresh-engineering-baseline`
- **May suggest:** `/review-claude-config`

## Hard Rules

- Read-only only.
- Always show the full dashboard in normal mode. In `--validation` mode, show the bounded validation dashboard instead.
- Report missing or unreadable references as health failures rather than hard aborting.
