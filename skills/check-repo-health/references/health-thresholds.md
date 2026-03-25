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

Binary pass/fail — no thresholds. A reference either resolves or it does not.
