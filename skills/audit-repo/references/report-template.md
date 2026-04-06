---
name: report-template
description: Report body template for the audit-repo skill output — use as the structure for the assembled report body
last_refreshed: 2026-04-06
---

```
# Repository Audit Report

## Repository Profile
- **Target:** [absolute path]
- **Languages:** [detected]
- **Frameworks:** [detected]
- **Existing Claude Config:** [yes/no — N skills, N agents, N rules, hooks: yes/no]
- **Repository Type:** [Application / Skills-Config / Mixed]

## Static Analysis Findings

### Toolchain
[findings with specific file paths and extracted commands]

### Ambiguity Metrics
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Max directory depth | N | >4 | OK/WARN |
| Max files per directory | N | >30 | OK/WARN |
| Naming collisions | N | >5 | OK/WARN |
| Sprawl score | N | >100 | OK/WARN |

### Convention Enforcement
| Convention | Tier | Tool/Config | Gap |
|-----------|------|-------------|-----|
| [convention] | [1-4] | [config file] | [gap or "covered"] |

### Architecture
[detected patterns, evidence, ADR presence]

### Domain Knowledge
[available docs with paths, identified gaps]

## Token Efficiency Findings

### File Size Distribution
[top N large files with line counts and estimated token costs]

### Navigation Sprawl Score
Score: [N] — [classification]
Breakdown: depth [N] × files/dir [N] × collisions [N]

### Build Error Verbosity
[toolchain → verbosity → token cost]

### Monorepo Isolation
[workspace count, cross-package imports, assessment]

### Context Burn Rate
| Task Type | Estimated Tokens |
|-----------|-----------------|
| Simple edit | [N]K |
| Exploration + edit | [N]K |
| Multi-file refactor | [N]K |

## Intervention Matrix

| # | Error Class | Gap | Primitive | Priority | Token Impact | Evidence Class | Confidence | Signal Source | Evidence |
|---|-------------|-----|-----------|----------|-------------|----------------|------------|--------------|----------|
| 1 | [class] | [description] | [type] | [P0-P2] | [H/M/L] | [class] | [H/M/L] | [source*] | [cite] |

*Signal Source: For Skill primitives, include "repetition" or the catalog signal name (e.g., "Database migrations"). For other primitives, use "—".
*Evidence Class: Use the canonical vocabulary from `skills/review-claude-config/references/evidence-contract.md`.

## Recommendations

### P0 — Immediate (CLAUDE.md Basics)
[detailed recommendations with specific content to add]

### P1 — Short-term (Hooks + Skills)
[detailed recommendations with specific configurations]

### P2 — Medium-term (Agents + Domain)
[detailed recommendations]
```
