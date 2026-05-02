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

## IJ-1 — external input reaches a write tool without a gate?

- **PASS**: Skill reads user-supplied path, validates against an allowlist regex BEFORE any Write/Edit call; rejects on miss.
- **FAIL**: Skill reads user-supplied template content and writes it verbatim to `${HOME}/.claude/plugins/data/claude-config/reports/` without sanitization or confirmation gate.

## SP-1 — confirmation gate before destructive or irreversible operations?

- **PASS**: "Before `rm -rf`, ask via AskUserQuestion; on decline, stop and report."
- **FAIL**: "Delete the stale cache entries under `references/domain-cache/`." No confirmation step, no dry-run.

## SP-3 — stop conditions defined for loops or recursive operations?

- **PASS**: "Retry up to 3 times with exponential backoff; after 3 failures, emit status=failure and stop."
- **FAIL**: "Keep retrying until the fetch succeeds." No upper bound.

## SP-4 — high-risk tool combinations (Tier A/B) justified if present?

- **PASS**: "Write + WebFetch justified: Write restricted to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`; WebFetch used only for domain research (read-only). No file-modification risk from network content."
- **FAIL**: `allowed-tools: Bash, Write, WebFetch` with no Hard-Rules section scoping any of the three.

## RL-1 — termination conditions defined (step limit, timeout, or success criteria)?

- **PASS**: "Stop when `findings_count == 0` OR after 10 review iterations, whichever comes first."
- **FAIL**: "Iterate until the agent is confident." No observable stop predicate.

## RL-4 — escalation / HITL trigger defined for high-autonomy operations?

- **PASS**: "On two consecutive validation failures of the same fix, emit status=partial and request user review before proceeding."
- **FAIL**: Agent autonomously decides whether to re-attempt or skip; no user-escalation path declared.

## RL-9 — safety/PII/credential scope constraints present?

- **PASS**: "Never log the content of files matching `**/credentials.json`, `**/*.env`, or `**/.ssh/**`. Redact token-like substrings (`[A-Za-z0-9_-]{20,}`) in error messages."
- **FAIL**: Skill reads arbitrary files and writes full content to audit logs; no redaction or scope statement.

## RD-1 — trigger phrases specific enough to avoid accidental activation?

- **PASS**: "Use when the user asks to review an MCP server configuration or hands you a `.mcp.json` file."
- **FAIL**: "Use when the user has a configuration question." Common user phrases match unintentionally.

## RD-3 — no overlapping triggers with sibling skills in same plugin directory?

- **PASS**: `review-skill` description uses "SKILL.md file" + "single skill"; `review-agent` uses "agent definition" + "Agent/.md". Token-set overlap ≤1 token.
- **FAIL**: Two sibling skills both trigger on "review this file" — ≥2-token trigger overlap.
