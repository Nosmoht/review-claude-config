---
name: boundary-exemplars
description: PASS/FAIL boundary examples for skill evaluation checklist items — reduces verdict variance
last_refreshed: 2026-04-14
---

# Boundary Exemplars

Use these when a verdict is uncertain. Each pair shows the minimum PASS and maximum FAIL.

## PD-5 — Description contains ≥1 keyword that excludes unrelated requests?

- **PASS**: Description says "Use when the user asks to review a SKILL.md file" — "SKILL.md" excludes generic review requests.
- **FAIL**: Description says "Use when the user wants to review something" — no keyword narrows the activation scope.

## WS-2 — Every conditional specifies a concrete trigger?

- **PASS**: "If `token_count > 800`, split the reference file" — numeric threshold is testable.
- **FAIL**: "If the file is too large, consider splitting it" — no threshold, no observable test.

## SP-2 — allowed-tools matches actual tool usage and task archetype?

- **PASS**: Read-only review skill grants Read, Glob, Grep, Write (for report only) — matches Analyst archetype in decision tree.
- **FAIL**: Read-only review skill grants Bash and Edit with no justification — exceeds Analyst archetype scope.

## RD-2 — Skill explicitly rejects ≥1 out-of-scope scenario?

- **PASS**: "This skill does NOT apply changes — use `/apply-review-findings` instead."
- **FAIL**: Skill describes what it does but never states what it refuses or delegates.
