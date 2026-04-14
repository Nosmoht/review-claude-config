---
name: audit-context-budget
description: User-facing documentation for the audit-context-budget skill
---

# /audit-context-budget

Estimates the token footprint of a repo's Claude Code configuration and recommends optimizations.

## When to Use

- Session starts at 20%+ context with a simple "hello" prompt
- After adding MCP servers, skills, or rules
- Before optimizing a Claude Code setup
- To understand what's consuming context at session start

Use `/audit-repo` instead for source code token analysis.

## Usage

```
/audit-context-budget [folder]
```

`folder` defaults to the current working directory.

## What It Analyzes

| Component | What's Measured |
|-----------|----------------|
| CLAUDE.md files | All levels (user-global, project, parent dirs) — size, line count, instruction density |
| Rules | Global (unconditional) vs path-scoped. Unconditional rules re-inject on every tool call |
| MCP servers | Tool count, deferred vs eager loading, disabled servers leaking names |
| Skills | Project skills (Level 1 only) vs plugin skills (full body). `disable-model-invocation` presence |
| Agents | Body size, always-on vs on-invocation loading |
| Git context | Size estimate based on dirty files and commit depth |
| Memory | MEMORY.md cost if present |

## Output

A structured report with:
1. Context Budget Summary — total estimate, % of 200K window, status
2. Limitations — what the estimates can and cannot measure
3. Component Breakdown — per-component token range and status
4. Optimization Recommendations — ranked P0/P1/P2 with expected savings
5. Action Plan — checkbox list

Report is saved to `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-audit-context-budget.md`.

## Key Findings (from Research)

These are the highest-impact optimizations, based on community measurements:

| Issue | Impact | Strategy |
|-------|--------|---------|
| Rules without `paths:` | Re-inject every tool call — 46% of 200K measured | Add `paths:` frontmatter or move to CLAUDE.md |
| Plugin skills (full load) | Up to 34K tokens for 28 skills | Stub SKILL.md + Read-on-invoke pattern |
| MCP tools without deferral | ~480 tokens/tool eager | Enable ENABLE_TOOL_SEARCH |
| CLAUDE.md > 200 lines | Prose uses 3-5x more tokens than tables | Convert to tables, split to topic files |

## Thresholds

| Status | Config Context (excl. baseline) |
|--------|--------------------------------|
| Healthy | < 10K tokens |
| Warning | 10-30K tokens |
| Critical | > 30K tokens |

Unavoidable baseline (system prompt + tools + git): ~14-44K tokens depending on repo and tool loading mode. The skill reports config-controlled costs separately.

## Limitations

- Token estimates use chars/3-4 — actual tokenizer output may differ by ±30%
- Prompt cache hit rates are not measurable (cached tokens cost 10x less)
- No access to actual API token consumption
- Rule re-injection multiplier depends on conversation length
