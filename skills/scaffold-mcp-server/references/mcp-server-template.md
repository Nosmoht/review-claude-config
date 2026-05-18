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

## Quality-Gate Mapping

Each template field exists to satisfy specific item IDs from
`skills/review-claude-config/references/mcp-evaluation-guide.md`. A scaffolded
entry that follows this template literally targets ≥4 distinct IDs and
should pass `/review-mcp-server` with zero High findings:

| Field / convention | Item IDs | Failure if omitted |
|---|---|---|
| File at `.mcp.json` root | MC-1, SP-2 | Nested in `settings.json` → silently ignored (bug #24477) |
| `command` + `args` (stdio) or `type` + `url` (remote) | MC-2, MC-3 | Missing required fields → server fails to start |
| `${VAR}` in `env`/`headers` (never literal) | MC-4, MC-5 | Hardcoded token → High severity, public-leak risk |
| `metadata.description` + `metadata.homepage` | MC-8, MC-9 | Audit reports can't trace server intent |
| `defer_loading: true` when tools >50 | TD-1 | Auto-injects ~10% context budget at session start |
| `.mcp.json` in `.gitignore` IF env contains credentials | SP-3 | Credential commit on next push |
| Single tool relevance, no duplicate servers | MG-1, MG-2 | Tool cap 128 hard, 50 soft — duplicates burn budget |

## Out of scope

- Writing the MCP server's executable code (transport handler, tool
  registry, request loop).
- Authoring tool input schemas — those live in the server's own code.
- Selecting a package manager or registry — operator decision.
