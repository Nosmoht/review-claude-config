---
name: context-report-schema
description: YAML frontmatter schema and body structure for audit-context-budget reports
last_refreshed: 2026-04-11
---

## Frontmatter Fields

```yaml
---
generated_by: audit-context-budget
schema_version: 2
date: YYYY-MM-DD
repo: <slug>                           # required — basename(target_dir), sanitized
origin: <git-remote-url>               # optional — git remote URL when available
# MUST use the literal token `$HOME/` (not the resolved absolute home prefix). block-sensitive-content.sh denies Write otherwise.
target: $HOME/path/to/repo
total_tokens_low: N
total_tokens_high: N
status: healthy|warning|critical
instruction_density: N
instruction_status: healthy|warning|critical
component_count: N
optimization_count: N
estimated_savings_low: N
estimated_savings_high: N
components:
  - name: CLAUDE.md files
    tokens_low: N
    tokens_high: N
    status: ok|warn|critical
  - name: Rules (unconditional)
    tokens_low: N
    tokens_high: N
    status: ok|warn|critical
  - name: Rules (path-scoped)
    tokens_low: N
    tokens_high: N
    status: ok
  - name: MCP servers
    tokens_low: N
    tokens_high: N
    status: ok|warn|critical
  - name: Skills (always-on content)
    tokens_low: N
    tokens_high: N
    status: ok|warn|critical
  - name: Git context
    tokens_low: N
    tokens_high: N
    status: ok
---
```

## Body Section Order

1. Context Budget Summary — verdict first (status, instruction density status, total range, % of 200K)
2. Limitations — estimation uncertainty, cache alignment warning, unmeasurable factors
3. Component Breakdown — table: component, token range, % of total, status, key observation
4. Optimization Recommendations — grouped P0/P1/P2
5. Action Plan — checkbox list

## Recommendation Format

Per recommendation:
- **File:** specific path(s)
- **Change:** what to do
- **Estimated savings:** X-Y tokens
- **Evidence:** [Tier N: source]

## Status Rules

Overall status = highest severity component status.
Instruction status = healthy (<80), warning (80-120), critical (>120).
