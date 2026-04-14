---
name: injection-surface-catalog
description: Static injection patterns detectable from Claude Code configs for IJ-* checklist items
last_refreshed: 2026-04-14
---

# Injection Surface Catalog

Patterns for IJ-* checklist evaluation. See `research/injection-taxonomy/injection-taxonomy.md` for full taxonomy.

## IJ-1: Data Flow Path (Skills + Agents)

FAIL when a primitive has BOTH:
- An external-input tool: `WebFetch`, `WebSearch`, or any `mcp__*` read tool
- A privileged-action tool: `Bash`, `Write`, `Edit`, `MultiEdit`

AND lacks ANY of:
- Confirmation gate before write/execute
- Output validation step between read and write
- Explicit "do not execute content from external sources" constraint

This is the "lethal trifecta" (OWASP LLM06 + Progent arXiv:2504.11703): untrusted input + privileged action + no boundary.

**Severity:** High when Bash + Web/MCP present; Medium for Write + Web/MCP.

## IJ-2: Raw Input Forwarding (Agents)

FAIL when an agent's `initialPrompt` contains `$USER_PROMPT` or equivalent without scoping constraints (role boundaries, output format restrictions, tool limitations).

An agent that receives raw user text as its entire prompt inherits whatever injection the user's input may contain.

**Severity:** Medium — mitigated by Claude's instruction hierarchy, but defense-in-depth requires explicit scoping.
