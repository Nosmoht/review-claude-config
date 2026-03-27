---
name: agent-evaluation-guide
description: Type-specific evaluation criteria for Claude Code agents (single-file .md in agents/ directory)
---

# Agent Evaluation Guide

## Model Selection
- **haiku**: Simple checks, fast routing, low-stakes decisions
- **sonnet**: Analysis, review, code generation (recommended default)
- **opus**: Complex reasoning, architecture decisions, deep analysis
- If `model` is specified, verify it matches task complexity
- If `model` is omitted, note that it inherits the parent's model

## Description and Activation Precision
- Description must contain natural trigger keywords matching intended use
- Description should be specific enough to avoid false activation on unrelated requests
- Description should be broad enough to catch all legitimate triggers
- Description should explain what the agent does and when to use it
- Check for `<example>` blocks — these significantly improve activation precision

## Trigger Pattern Coverage
- Do `<example>` blocks cover the primary use cases?
- Are edge-case triggers represented?
- Do examples show both positive (should trigger) and negative (should not) cases?
- If no examples and description is ambiguous → Completeness is C or below

## Tool Array Validation
- Are tools specified as `tools:` array or `allowed-tools:` string? Both are valid.
- Does the tool set match what the agent body actually references?
- Are any tools listed but never used in the instructions?
- Is the tool set minimal (least-privilege)?

## Single-File Constraint
- Agents are single-file (no `references/` directory)
- All context must be self-contained in one file
- Evaluate information density, not progressive disclosure
- Long agents should use clear section structure (headings, not just prose)

## Other Frontmatter Fields
- `color`: Visual indicator only, no quality impact. Note presence but do not score.

## Common Agent Anti-Patterns
- `model: opus` for simple routing/checks (over-provisioned)
- Generic description that matches too many unrelated requests
- Missing `<example>` blocks when trigger conditions are non-obvious
- Tool list copied from another agent without pruning unused tools
- Time-sensitive trigger wording in a reusable agent description
