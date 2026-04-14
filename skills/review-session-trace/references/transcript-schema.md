---
name: transcript-schema
description: Claude Code JSONL transcript entry structure and content block types for trace analysis parsing
last_refreshed: 2026-04-14
---

# Transcript JSONL Schema

Each line is a JSON object. Parse line-by-line.

## Entry Fields

| Field | Type | Notes |
|---|---|---|
| `uuid` | string | Unique entry ID |
| `parentUuid` | string/null | Previous entry (null = root) |
| `sessionId` | string | Session ID |
| `timestamp` | ISO-8601 | Entry creation time |
| `type` | string | `user`, `assistant`, `system`, `queue-operation`, `file-history-snapshot` |
| `message.role` | string | `user` or `assistant` |
| `message.content` | array | Content blocks (see below) |
| `usage` | object/null | Token counts (assistant only) |
| `cwd` | string | Working directory |

## Content Block Types

**Tool use** (assistant calls tool):
```json
{"type": "tool_use", "id": "toolu_...", "name": "Bash", "input": {"command": "..."}}
```

**Tool result** (tool returns):
```json
{"type": "tool_result", "tool_use_id": "toolu_...", "content": "..."}
```

**Text**: `{"type": "text", "text": "..."}`

**Thinking**: `{"type": "thinking", "thinking": "..."}`

## Token Usage Object

```json
{"input_tokens": N, "output_tokens": N, "cache_read_input_tokens": N, "cache_creation_input_tokens": N}
```

## Matching Tool Calls to Results

Join `tool_use.id` with `tool_result.tool_use_id`. A tool_use in an assistant entry is answered by a tool_result in the next user entry.
