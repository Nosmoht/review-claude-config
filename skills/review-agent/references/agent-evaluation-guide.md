---
name: agent-evaluation-guide
description: Type-specific evaluation criteria for Claude Code agents (single-file .md in agents/ directory)
last_refreshed: 2026-04-03
---

# Agent Evaluation Guide

## Model Selection
- **haiku**: Simple checks, fast routing, low-stakes decisions
- **sonnet**: Analysis, review, code generation (recommended default)
- **opus**: Complex reasoning, architecture decisions, deep analysis
- If `model` is specified, verify it matches task complexity; if clearly mismatched, Metadata is C or below
- If `model` is omitted, it inherits the parent's model

## Description and Activation Precision
- Description must contain natural trigger keywords matching intended use
- Specific enough to avoid false activation; broad enough to catch all legitimate triggers
- Check for `<example>` blocks — these significantly improve activation precision
- If description is generic enough to match unrelated requests, Context Engineering is C or below

## Trigger Pattern Coverage
- Do `<example>` blocks cover the primary use cases?
- Are edge-case triggers represented (both positive and negative)?
- If no examples and description is ambiguous → Completeness is C or below

## Tool Array Validation
- `tools:` array and `allowed-tools:` string are both valid
- Tool set must match what the agent body actually references; no unused tools
- Is the tool set minimal (least-privilege)?
- `color`: visual indicator only, no quality impact

## Single-File Constraint
- Agents are single-file (no `references/` directory)
- All context must be self-contained; evaluate information density, not progressive disclosure
- Long agents should use clear section structure (headings, not prose)

## Common Agent Anti-Patterns
- `model: opus` for simple routing/checks (over-provisioned)
- Generic description matching too many unrelated requests
- Missing `<example>` blocks when trigger conditions are non-obvious
- Tool list copied from another agent without pruning unused tools
