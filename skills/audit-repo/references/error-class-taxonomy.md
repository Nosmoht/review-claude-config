---
name: error-class-taxonomy
description: Seven error classes with diagnostic indicators and evidence-informed primitive mappings
last_refreshed: 2026-04-03
---

## Error Classes

| # | Class | What Goes Wrong | Diagnostic Signal | Primary Primitive | Token Impact |
|---|-------|----------------|-------------------|-------------------|-------------|
| 1 | Toolchain | Guesses build/test/lint commands | No explicit command list discoverable | CLAUDE.md | HIGH |
| 2 | Navigation | Opens wrong files, searches wrong dirs | Depth >4, >30 files/dir, naming collisions | CLAUDE.md | HIGH |
| 3 | Convention | Violates project style/patterns | Conventions not in linter, not documented | Hook or CLAUDE.md | LOW |
| 4 | Architecture | Uses wrong pattern/abstraction layer | Implicit architecture, no ADRs | CLAUDE.md | LOW |
| 5 | Repetition | Rewrites boilerplate inconsistently | ≥5 structurally similar files, no codegen | Skill | MEDIUM |
| 6 | Domain | Wrong terms, wrong business logic | No glossary, no domain docs referenced | CLAUDE.md | LOW |
| 7 | Security | Misses security constraints | Secret scanning in CI, branch protection | Hook + Agent | LOW (high risk) |

## Priority Assignment

- **P0**: Toolchain + Navigation — highest leverage for both correctness and token efficiency
- **P1**: Convention + Architecture + Repetition + Security — automatable guardrails and patterns
- **P2**: Domain — highest effort, only when domain docs are missing and domain is complex

Priority tiers are `Repo default` planning conventions for this repository.

## Evidence Mapping

Each intervention must cite:
- **File paths** found during analysis (e.g., "package.json scripts: build, test, lint")
- **Metrics** computed (e.g., "max directory depth: 6, sprawl score: 142")
- **Absence evidence** (e.g., "no .eslintrc found — conventions undocumented")
