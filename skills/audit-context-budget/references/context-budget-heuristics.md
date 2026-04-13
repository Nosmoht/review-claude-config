---
name: context-budget-heuristics
description: Token estimation formulas and optimization multipliers for audit-context-budget
last_refreshed: 2026-04-12
---

## Token Estimation

Formula: `chars / 4` (low bound), `chars / 3` (high bound). Always report ranges.

Fixed estimates:
- System prompt base: 5,000 tokens [Tier 2: dbreunig.com]
- Built-in tools: 6,000 (deferred) / 16,000 (eager) [Tier 3: #45188]
- Environment info: 280 tokens [Tier 1: Anthropic]

## MCP Per-Tool Heuristic

- Deferred (ENABLE_TOOL_SEARCH, default): ~0.85 tokens/tool [Tier 1]
- Eager (no deferral): ~480 tokens/tool [Tier 3: #40314]
- Disabled servers still leak names: ~10 tokens/tool [Tier 3: #41809]
- Unknown tool count: assume 10 tools/server

## Git Context Estimate

`min(23000, 3000 + dirty_files * 200 + min(commit_count, 50) * 100)` [Tier 3: #8245]

## Instruction Count Heuristic

Count lines starting with: `- `, `* `, digit+`.`, or imperative verbs: Add|Run|Use|Check|Do|Set|Never|Always|Avoid|Prefer|Keep|Load|Read|Create|Write|Ensure|Follow|Apply|Review|Report

## Optimization Multipliers

| Strategy | Savings | Evidence |
|----------|---------|----------|
| CLAUDE.md prose → tables | ~82% | Tier 3: #33464 |
| Rules: add `paths:` frontmatter | ~24% | Tier 3: #25005 |
| Plugin skills: stub + Read-on-invoke | ~91% | Tier 3: #44371 |
| `disable-model-invocation: true` | 100% always-on | Tier 1 |
| Enable ENABLE_TOOL_SEARCH | eager → deferred cost | Tier 1 |

## Rule Re-Injection

Unconditional rules re-inject on every tool call.
Session cost: `rule_tokens × avg_tool_calls` (typical: 10-30 calls/conversation) [Tier 3: #32057]
