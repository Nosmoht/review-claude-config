---
name: health-thresholds
description: Configurable thresholds for repository health checks — freshness, token budgets, integrity
---

## Freshness Thresholds

| Status | Days Since Refresh |
|--------|--------------------|
| PASS   | < 60               |
| WARN   | 60 – 89            |
| FAIL   | ≥ 90               |

## Token Budgets

| File Pattern | Budget (tokens) |
|-------------|-----------------|
| scoring-rubric.md | 1000 |
| engineering-baseline.md | 2000 |
| signal-catalog.md | 1000 |
| domain-cache/*.md (excl. INDEX.md) | 500 |
| Other reference files | 500 |

Token budget status:
- PASS: < 80% of budget
- WARN: 80–100% of budget
- FAIL: > 100% of budget

## Integrity

References either resolve or they do not. Severity from the dependency registry determines status:

| Sub-check | Behavior |
|-----------|----------|
| 5c-i: Registry (fatal) | FAIL if target missing |
| 5c-i: Registry (warn) | WARN if target missing |
| 5c-i: Registry (skip) | PASS (info only) if target missing |
| 5c-ii: Heuristic | WARN if reference found but UNREGISTERED |
