---
name: boundary-exemplars
description: PASS/FAIL boundary examples for agent evaluation checklist items — reduces verdict variance
last_refreshed: 2026-04-14
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
