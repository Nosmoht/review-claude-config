---
name: mcp-server-template
description: Canonical .mcp.json entry templates (stdio + remote) with 2026 schema additions
last_refreshed: 2026-04-19
---

# MCP Server Declaration Templates

Two transport variants: `stdio` (local subprocess, common) and `remote`
(`type: sse` or `type: http`). Both share the 2026 schema additions
(`disabled`, `defer_loading`, `metadata`).

## stdio (local subprocess)

```json
{
  "mcpServers": {
    "<server-name>": {
      "command": "/usr/local/bin/<binary>",
      "args": ["--flag", "value"],
      "env": {
        "API_TOKEN": "${MCP_API_TOKEN}",
        "BASE_URL": "https://api.example.com"
      },
      "disabled": false,
      "defer_loading": false,
      "metadata": {
        "description": "One-line summary of what tools this server exposes.",
        "homepage": "https://example.com/mcp-server"
      }
    }
  }
}
```

## remote (sse / http)

```json
{
  "mcpServers": {
    "<server-name>": {
      "type": "sse",
      "url": "https://mcp.example.com/sse",
      "headers": {
        "Authorization": "Bearer ${MCP_API_TOKEN}"
      },
      "disabled": false,
      "defer_loading": false,
      "metadata": {
        "description": "One-line summary.",
        "homepage": "https://example.com"
      }
    }
  }
}
```

## Field reference (2026 schema)

| Field | Required | Notes |
|-------|----------|-------|
| `command` | stdio only | Absolute or PATH-resolvable binary path |
| `args` | optional | Array of strings; never embed secrets |
| `env` | optional | Map of env var name to value; secrets via `${VAR}` |
| `type` | remote only | `sse` or `http` |
| `url` | remote only | Full URL including protocol |
| `headers` | remote only | Map; secret values via `${VAR}` |
| `disabled` | optional | `true` to keep entry but skip load |
| `defer_loading` | optional | `true` for >50 tools or >10 K desc tokens (TD-1) |
| `metadata.description` | recommended | Surfaces in audit and review reports (MC-9) |
| `metadata.homepage` | recommended | Documentation/source URL |

## Defaults the scaffold applies

- `disabled: false` (unless user opts in).
- `defer_loading: true` if reported tool count >50.
- `metadata.description` always populated (synthesised from user input
  if not provided).
- `env` and `headers` always use `${VAR}` for credential-shaped names.

## Out of scope

- Writing the MCP server's executable code (transport handler, tool
  registry, request loop).
- Authoring tool input schemas — those live in the server's own code.
- Selecting a package manager or registry — operator decision.
