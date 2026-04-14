---
last_refreshed: 2026-04-14
---

# Claude Code settings.json Quality Criteria

## Schema

60+ fields across 8 categories. Official JSON schema: `https://json.schemastore.org/claude-code-settings.json`. Scope precedence: Managed > Local > Project > User. Arrays concatenated across scopes; deny always wins over allow.

## Critical Security Fields

| Field | Risk | Evidence |
|-------|------|---------|
| `permissions.deny` absent | Credentials readable by default | Trail of Bits; most common misconfiguration |
| `enableAllProjectMcpServers: true` | Auto-approves any MCP server in cloned repos | Supply-chain attack vector (Anthropic docs) |
| `bypassPermissions` in project scope | Bypasses all permission checks | Should only exist in user/managed scope |
| Invalid JSON | Silently disables ALL permission rules | GitHub #44912 |
| `env` section with secrets | Credentials in committed file | Tier 2 common finding |

## Recommended Deny Paths (Trail of Bits)

`~/.ssh/**`, `~/.aws/**`, `~/.kube/**`, `.env`, `.npmrc`, `.pypirc`, shell configs (`~/.bashrc`, `~/.zshrc`), macOS keychain paths.

## Scope Locations

| Scope | Path | Committed? |
|-------|------|-----------|
| Project | `.claude/settings.json` | Yes |
| Project local | `.claude/settings.local.json` | No (gitignore) |
| User | `~/.claude/settings.json` | No |
| Managed | Enterprise-managed | N/A |

## Sources

- [Anthropic: Claude Code Settings](https://docs.anthropic.com/en/docs/claude-code/settings) (Tier 1)
- [JSON Schema: claude-code-settings](https://json.schemastore.org/claude-code-settings.json) (Tier 1)
- [Trail of Bits: Claude Code Security](https://blog.trailofbits.com/) (Tier 2)
- [GitHub #44912: Invalid JSON disables rules](https://github.com/anthropics/claude-code/issues/44912) (Tier 2)
