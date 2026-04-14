---
name: audit-trace-schema
description: Canonical JSONL schema for audit trace entries produced by observation hooks and consumed by review-session-trace
last_refreshed: 2026-04-14
---

# Audit Trace Schema

One JSONL file per session at `$CLAUDE_PLUGIN_DATA/audit/{session_id}.audit.jsonl`. Each line is a JSON object with a `type` field.

## Entry Types

### tool_call (PostToolUse / PostToolUseFailure)

```json
{
  "type": "tool_call",
  "ts": "2026-04-14T12:34:56.789Z",
  "session_id": "abc123",
  "agent_id": "agent-xyz",
  "agent_type": "Explore",
  "tool_name": "Bash",
  "tool_use_id": "toolu_01ABC",
  "input_hash": "sha256:abcdef12",
  "success": true,
  "cwd": "/path/to/dir"
}
```

`success`: true for PostToolUse, false for PostToolUseFailure.
`input_hash`: SHA-256 of JSON-serialized `tool_input` (privacy — no raw args logged).
`agent_id`/`agent_type`: from common hook fields; null when not in subagent.

### delegation (SubagentStart / SubagentStop)

```json
{
  "type": "delegation",
  "ts": "2026-04-14T12:35:00.000Z",
  "session_id": "abc123",
  "agent_id": "agent-xyz",
  "agent_type": "Plan",
  "event": "start",
  "cwd": "/path/to/dir"
}
```

`event`: `"start"` or `"stop"`.

### session_summary (SessionEnd)

```json
{
  "type": "session_summary",
  "ts": "2026-04-14T13:00:00.000Z",
  "session_id": "abc123",
  "duration_sec": 1523,
  "tool_calls": 47,
  "tool_errors": 2,
  "delegations": 5,
  "max_depth": 2
}
```

Appended as the final entry by the SessionEnd hook.

## Storage Convention

- Path: `$CLAUDE_PLUGIN_DATA/audit/{session_id}.audit.jsonl`
- One file per session; append-only during session
- SessionEnd hook appends summary as last line
- Retention: no auto-pruning; user manages via filesystem
