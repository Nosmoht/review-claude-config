---
name: agent-fix-guide
description: Type-specific validation rules for applying fixes to Claude Code agents
last_refreshed: 2026-03-25
---

# Agent Fix Guide

## Single-File Constraint

Agents are single .md files with no `references/` directory. If a recommendation suggests creating external files, transform it to inline content or reject the recommendation. Never create directories or additional files for an agent.

## Model Selection

Validate the `model` field against task complexity:
- **haiku**: Simple routing, checks, formatting, classification
- **sonnet**: Analysis, review, moderate reasoning (default if omitted)
- **opus**: Complex multi-step reasoning, architecture decisions, nuanced judgment

Flag mismatches: e.g., opus for a simple formatter, or haiku for a code reviewer.

## Description Quality

The `description` field serves as the trigger for agent activation. After edits:
- Must contain natural keywords matching the agent's purpose
- Must be specific enough to avoid false activation on unrelated requests
- Must be broad enough to catch legitimate triggers
- Avoid generic phrases like "help with tasks" or "assist the user"

## Example Blocks

`<example>` blocks demonstrate when and how the agent activates. After edits:
- Must cover the primary use case
- Each example should show user message, assistant response, and commentary
- Edge cases strengthen activation precision

## Tool Minimalism

The `tools` array must match tools actually referenced in the agent body:
- Remove tools not used in the agent's workflow
- Don't add tools speculatively ("in case they're needed")
- Fewer tools = clearer scope and fewer failure modes

## Common Pitfalls

- Don't create reference files (agents are single-file)
- Don't broaden description beyond the agent's intended scope
- Don't add example blocks that overlap with other agents' triggers
- Don't change model without verifying task complexity justifies it
