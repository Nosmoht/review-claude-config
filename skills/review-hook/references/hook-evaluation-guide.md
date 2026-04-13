---
name: hook-evaluation-guide
description: Type-specific evaluation criteria for Claude Code hooks (hooks.json + Python scripts)
last_refreshed: 2026-04-07
---

# Hook Evaluation Checklist

Answer EVERY item: PASS | FAIL | NA. No skipping. FAILs map to Dim for scoring.

## hooks.json Configuration

| ID | Check | Dim |
|----|-------|-----|
| HC-1 | Event name is a valid Claude Code hook event (SessionStart, PreToolUse, PostToolUse, Stop, etc.)? | Compl |
| HC-2 | Matcher pattern targets a single tool name or explicit glob — not a catch-all? | Clarity |
| HC-3 | `on_error` behavior is defined or default (non-blocking) is appropriate for this hook's risk level? | Safety |
| HC-4 | `timeout` is set and reasonable for the hook's operation (≤10s for PreToolUse, ≤30s for async events)? | Safety |
| HC-5 | `description` field present in hooks.json explaining the hook's purpose? | Meta |
| HC-6 | Hook fires at the correct lifecycle event for its stated purpose? | Goal |

## Python Script Quality

| ID | Check | Dim |
|----|-------|-----|
| PY-1 | Script reads input from `sys.stdin` (not args) when hook event provides JSON input? | Compl |
| PY-2 | Script always outputs valid JSON to `stdout` (including on error paths)? | Safety |
| PY-3 | Script exits with correct code: 0=pass, 1=block with message, 2=non-blocking error? | Safety |
| PY-4 | No side effects on error paths (no partial writes, no external API calls without cleanup)? | Safety |
| PY-5 | Heavy imports (network libs, large frameworks) avoided for PreToolUse hooks? | Goal |
| PY-6 | `CLAUDE_PLUGIN_ROOT` env var checked before use; graceful exit if absent? | Compl |
| PY-7 | File paths constructed with `os.path.join` or `pathlib` (not string concatenation)? | Clarity |
| PY-8 | Exception handler at top level prevents unhandled exceptions from crashing the hook? | Safety |

## Safety and Reliability

| ID | Check | Dim |
|----|-------|-----|
| SR-1 | No credentials, tokens, or secrets accessed or logged? | Safety |
| SR-2 | No unbounded loops or operations without timeout/limit? | Safety |
| SR-3 | Hook is idempotent — running it twice produces the same result? | Safety |
| SR-4 | Block decision (exit 1) includes a user-readable message explaining why? | Clarity |
| SR-5 | Hook does not modify the files it is triggered on (read-only where possible)? | Safety |

## Goal Alignment

| ID | Check | Dim |
|----|-------|-----|
| GA-1 | Hook's stated purpose matches its event trigger (e.g., quality gate on PreToolUse, not PostToolUse)? | Goal |
| GA-2 | Hook's output (systemMessage, additionalContext, or block) is appropriate for the event type? | Goal |
| GA-3 | Matcher scope is minimal — does not fire on events outside the hook's responsibility? | Goal |
