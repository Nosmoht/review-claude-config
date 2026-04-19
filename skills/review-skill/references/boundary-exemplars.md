---
name: boundary-exemplars
description: PASS/FAIL boundary examples for skill evaluation checklist items — reduces verdict variance
last_refreshed: 2026-04-20
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

## META-1a — description contains body's primary trigger keyword?

- **PASS**: "Use when reviewing MCP server configs" + body triggers on `.mcp.json`. Token-set overlap on "mcp".
- **FAIL**: body triggers on `.mcp.json` but description says "Use for configurations" — no overlap with `.mcp.json` keyword.

## META-2 — description contains anti-pattern (do-not / not-for) example?

- **PASS**: "Do NOT use for agents or rules — use /review-agent instead." Includes explicit anti-trigger.
- **FAIL**: "Use this skill when you need to review a skill." Self-tautology, no negative scope.

## META-3a — description avoids vague triggers (as needed / if appropriate)?

- **PASS**: "when file contains hooks.json".
- **FAIL**: "use as appropriate" — vague predicate; reviewer cannot verify.

## CE-X — compaction-strategy declared when summarisation chosen over masking?

- **PASS** (masking): "Rotating window: drop entries older than 20 tool-calls" — declares strategy.
- **PASS** (summarisation justified): "Summarise every 10 turns because semantic condensation is required — masking would lose dependency-graph signal."
- **FAIL**: "Summarise prior conversation every 10 turns via LLM call" — no justification for choice over masking.

## COMP-X — explicit success condition (not just output format)?

- **PASS**: "Complete when token-budget validator returns 0 and `make validate` exit-code 0."
- **FAIL**: "Output a JSON report with the findings." Format declared, success condition implicit.

## COMP-Y — verification method is programmatic or binary, not holistic?

- **PASS**: "Verify by re-running `verify_hook_events.py` and confirming `status: ok` for every event."
- **FAIL**: "Confirm the report looks good" — `looks good` is excluded by regex.

## COMP-Z — verification-decision evidence recorded?

- **PASS**: "Record the validator output and cite the line numbers that the recommendation references."
- **FAIL**: "Note that verification passed." Decision without evidence trail.
