---
name: boundary-exemplars
description: PASS/FAIL boundary examples for agent evaluation checklist items — reduces verdict variance
last_refreshed: 2026-04-19
---

# Boundary Exemplars

One BOUNDARY PASS and one BOUNDARY FAIL per item. Boundary = closest plausible case to the threshold.

## DA-2a — Description contains >=1 discriminating keyword not in unrelated requests?

- **PASS**: Description says "generate Helm chart values from Kustomize overlays" — "Kustomize overlays" discriminates from generic config tasks.
- **FAIL**: Description says "help with configuration files" — every repo task could match.

## DA-2b — Description covers all documented example triggers?

- **PASS**: Three example triggers listed; description mentions all three verbs/nouns used in examples.
- **FAIL**: Examples include "migrate database schema" but description only mentions "query databases."

## TV-2 — No unused tools; tool set matches task archetype (least-privilege)?

- **PASS**: Read-only analysis agent lists `Read`, `Grep`, `Glob` — all used in body, no write tools.
- **FAIL**: Read-only analysis agent lists `Bash` and `Edit` but body never writes or executes.

## AP-4 — Non-guardrail sections use MUST/CRITICAL <=3 times total?

- **PASS**: Body has 2 MUST outside guardrail section, 5 MUST inside guardrail section (only non-guardrail counted).
- **FAIL**: Body has 4 MUST and 1 CRITICAL in workflow instructions (non-guardrail) — total 5 exceeds threshold.

## TV-4 — disallowedTools does not overlap with tools allowlist?

- **PASS**: `tools: [Read, Grep]`, `disallowedTools: [Bash, Edit]` — denylist subtracts further from inherited tools, no overlap with allowlist.
- **FAIL**: `tools: [Read, Bash]`, `disallowedTools: [Bash]` — overlap creates contradictory grant; either remove Bash from `tools` or drop the redundant denylist.

## TV-6 — hooks reference valid event names from 26-event catalog?

- **PASS**: `hooks: { PostToolUseFailure: ./on_fail.sh }` — event exists since CLI v2.1.76, target runtime ≥2.1.76.
- **FAIL**: `hooks: { OnError: ./handler.sh }` — `OnError` is not a documented event; no runtime registration occurs (silent no-op).

## AF-4 — maxTurns set when agent does multi-step work?

- **PASS**: Agent body describes 5-step workflow; `maxTurns: 15` (3× headroom) prevents runaway.
- **FAIL**: Agent body describes 5-step workflow; no `maxTurns` set — single classifier loop can spin indefinitely.

## AF-5 — permissionMode value valid + bypassPermissions justified?

- **PASS**: `permissionMode: bypassPermissions` with body comment "Required for git push to release branch — restricted to `git push` invocation only via Bash allowlist".
- **FAIL**: `permissionMode: bypassPermissions` with no rationale — silently disables every prompt.

## AF-6 — effort value compatible with model?

- **PASS**: `effort: xhigh`, `model: claude-opus-4-7` — `xhigh` is Opus-4.7-only, model pinned correctly.
- **FAIL**: `effort: xhigh`, `model: sonnet` — sonnet does not support `xhigh`; runtime ignores or rejects.

## SAMP-1 — body free of removed sampling params?

- **PASS**: Body says "Adjust verbosity via `effort: medium` instead of decoding params."
- **FAIL**: Body says "Set `temperature=0.2` for deterministic output." — Opus 4.7 ignores; perpetuates dead pattern.

## SAMP-2 — frontmatter free of removed sampling params?

- **PASS**: Frontmatter declares only `model`, `effort`, `maxTurns` — no decoding overrides.
- **FAIL**: Frontmatter contains `temperature: 0` — runtime returns 400-error on Opus 4.7 dispatch.
