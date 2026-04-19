---
name: hook-evaluation-guide
description: Type-specific evaluation criteria for Claude Code hooks (hooks.json + Python scripts)
last_refreshed: 2026-04-19
---

# Hook Evaluation Checklist

Answer EVERY item: PASS | FAIL | NA. No skipping. FAILs map to Dim for scoring.

The 26-event catalog (with min-CLI per event) lives in
`research/hook-observation/hook-based-runtime-observation-patterns.md`
§"Full Event Catalog (26 events, v2.1.114 baseline)". Programmatic
verification is via `scripts/verify_hook_events.py <hooks.json>
[--cli-version X.Y.Z]`, which emits per-event status (`ok`,
`version_too_old`, `unknown_event`). Unknown events do NOT FAIL — they
emit `unknown_event` (forward-compat). Use the script's output to
populate HC-1 verdicts.

## hooks.json Configuration

| ID | Check | Dim |
|----|-------|-----|
| HC-1 | Event name is in the 26-event catalog AND installed CLI ≥ event's min-version (run `scripts/verify_hook_events.py`; `unknown_event` → flag for manual review, not FAIL). | Compl |
| HC-2 | Matcher pattern targets a single tool name or explicit glob — not a catch-all? | Clarity |
| HC-3 | `on_error` behavior is defined or default (non-blocking) is appropriate for this hook's risk level? | Safety |
| HC-4 | `timeout` is set and reasonable for the hook's runtime type (see Hook Runtime Types below). Default `command` cap 600 s; `prompt`/`http` 30 s; `agent` 60 s; PreToolUse handlers ≤10 s when blocking. | Safety |
| HC-5 | `description` field present in hooks.json explaining the hook's purpose? | Meta |
| HC-6 | Hook fires at the correct lifecycle event for its stated purpose? | Goal |
| HC-7 | If event has `Blocking: Yes` per catalog (PreToolUse, Stop, SubagentStop, TaskCreated, ConfigChange, etc.), exit-code semantics handled (exit 2 blocks; non-blocking events ignore exit 2). | Safety |
| HC-8 | Events added in 2026-Q1 (`PostToolUseFailure` v2.1.76, `CwdChanged`/`FileChanged` v2.1.83, `TaskCreated` v2.1.84, `PermissionDenied` v2.1.89) are not used unless target CLI version is pinned ≥ that release. | Compl |

## Python Script Quality

| ID | Check | Dim |
|----|-------|-----|
| PY-1 | Script reads input from `sys.stdin` (not args) when hook event provides JSON input? | Compl |
| PY-2 | Script always outputs valid JSON to `stdout` (including on error paths)? | Safety |
| PY-3 | Script exits with correct code: 0=pass, 2=block with message, 1/other=non-blocking error? | Safety |
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
| SR-4 | Block decision (exit 2) includes a user-readable message on stderr explaining why? | Clarity |
| SR-5 | Hook does not modify the files it is triggered on (read-only where possible)? | Safety |

## Goal Alignment

| ID | Check | Dim |
|----|-------|-----|
| GA-1 | Hook's stated purpose matches its event trigger (e.g., quality gate on PreToolUse, not PostToolUse)? | Goal |
| GA-2 | Hook's output (systemMessage, additionalContext, or block) is appropriate for the event type? | Goal |
| GA-3 | Matcher scope is minimal — does not fire on events outside the hook's responsibility? | Goal |

## Hook Runtime Types (HRT)

Four handler types with distinct execution contracts. Each HRT item is NA
unless the hook declares the corresponding `type:` field.

| Type | Input | Output | Default timeout | Async support | Notes |
|------|-------|--------|-----------------|---------------|-------|
| `command` | stdin JSON | stdout JSON + exit code | 600 s | Yes (`async: true`) | Standard shell/script handler |
| `http` | POST body JSON | HTTP response JSON | 30 s | No | Remote endpoint |
| `prompt` | stdin + prompt template | stdout JSON `{"ok": bool, "reason": str}` | 30 s | No | LLM judge |
| `agent` | stdin + prompt template | stdout JSON + tool calls (multi-turn ≤50 tool-use turns) | 60 s | No | Sub-agent verification |

| ID | Check | Dim | Trigger |
|----|-------|-----|---------|
| HRT-1 | Hook output schema matches its declared `type:` (e.g., `prompt` returns `{"ok", "reason"}`; `command` returns arbitrary JSON + exit code). | Compl | `type` |
| HRT-2 | `agent` hook tool grants restricted to `Read, Grep, Glob` only (matches Explore/Plan archetype). Bash/Edit/Write FAIL. | Safety | `type: agent` |
| HRT-3 | `agent` hook respects 60 s default timeout AND ~50 tool-call turn cap; body includes early-stop guards if approaching limits. | Safety | `type: agent` |
| HRT-4 | `command` hook with `async: true` only when downstream observation can tolerate non-blocking semantics (PostToolUse, SessionEnd OK; PreToolUse not safe async). | Safety | `async: true` |

## Known Open Bugs to Detect (BUG)

| ID | Check | Dim |
|----|-------|-----|
| BUG-1 | If hook script exits 0 on success path, ensure no extraneous stderr output that the bug #34713 mislabels as "Hook Error" (avoid fake-error noise in transcript). | Clarity |
| BUG-2 | Hooks declared inside agent frontmatter (`hooks:` field on an agent) are NOT executed in current CLI versions (#18392). Move to project/global `hooks.json` instead. | Compl |

**Finding identity:** Every FAIL must produce a recommendation with `ID: {item}:{path}:{dim}/v1` in the heading.
