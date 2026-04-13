---
name: boundary-exemplars
description: PASS/FAIL boundary examples for hook evaluation checklist items — reduces verdict variance
last_refreshed: 2026-04-14
---

# Boundary Exemplars

## HC-2 — Matcher pattern targets a single tool name or explicit glob — not a catch-all?

**PASS:** `"matcher": "Write"` or `"matcher": "mcp__github__*"` — single tool or scoped glob.
**FAIL:** `"matcher": "*"` or matcher omitted on a PreToolUse hook that should only fire for Bash.

## PY-3 — Script exits with correct code: 0=pass, 1=block with message, 2=non-blocking error?

**PASS:** Script uses `sys.exit(0)` for pass, `sys.exit(1)` after printing JSON `{"decision":"block","reason":"..."}`, and `sys.exit(2)` for recoverable failures.
**FAIL:** Script raises unhandled exception (implicit exit 1 without message) or uses `sys.exit(3)` which is undefined.

## SR-3 — Hook is idempotent — running it twice produces the same result?

**PASS:** Hook reads a file, checks a condition, and outputs a decision — no state mutation between runs.
**FAIL:** Hook appends a line to a log file on every invocation — second run doubles the entry, third triples it.
