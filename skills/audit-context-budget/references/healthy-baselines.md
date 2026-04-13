---
name: healthy-baselines
description: Per-component thresholds and unavoidable baseline for context budget assessment
last_refreshed: 2026-04-11
---

## Component Thresholds

`Repo default` — informed by community measurements, not Tier 1 research.

| Component | Healthy | Warning | Critical |
|-----------|---------|---------|----------|
| Total config context (excl. system/tools/git) | <10K | 10-30K | >30K |
| CLAUDE.md (all files combined) | <3K | 3-6K | >6K |
| Single CLAUDE.md file | <200 lines | 200-400 lines | >400 lines |
| Rules (unconditional only) | <1K | 1-3K | >3K |
| MCP tool overhead | <5K | 5-20K | >20K |
| Skills (always-on loaded content) | <2K | 2-8K | >8K |
| Instruction density (all sources) | <80 | 80-120 | >120 |

## Instruction Density Rationale

Claude Code base prompt consumes ~50 instruction slots. Frontier models sustain ~150-200 instructions before entering decay. Remaining budget: ~100-150 slots. [Tier 2: dbreunig.com + Tier 1: AgentIF arXiv:2505.16944 confirmed ISR <30% at avg 11.9 constraints]

## Unavoidable Baseline

These tokens cannot be reduced through configuration changes:

| Source | Estimate |
|--------|---------|
| Claude Code system prompt | ~5,000 tokens |
| Built-in tools (deferred) | ~6,000 tokens |
| Built-in tools (eager) | ~16,000 tokens |
| Git context (typical repo) | 3,000-23,000 tokens |
| Environment info | ~280 tokens |
| **Total unavoidable** | ~14,000-44,000 tokens |

Report config-controlled costs separately from unavoidable baseline. Users can only act on the config-controlled portion.
