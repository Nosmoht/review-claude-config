---
name: settings-evaluation-guide
description: Type-specific evaluation criteria for Claude Code settings.json files
last_refreshed: 2026-04-14
---

# Settings Evaluation Checklist

Answer EVERY item: PASS | FAIL | NA. No skipping. FAILs map to Dim for scoring.

Settings use 4 dimensions (renormalized): Completeness 25%, Goal Alignment 25%, Safety 30%, Metadata 20%. Skip: Clarity, PE, CE (settings are configuration, not prompts).

## Schema Correctness

| ID | Check | Dim |
|----|-------|-----|
| SS-1 | Valid JSON (parse failure silently disables ALL permission rules)? | Compl |
| SS-2 | `$schema` field present (enables IDE validation)? | Meta |
| SS-3 | No misplaced `mcpServers` key (silently ignored in settings.json — belongs in .mcp.json)? | Compl |

## Security & Permissions

| ID | Check | Dim |
|----|-------|-----|
| SP-1 | `permissions.deny` covers credential paths (~/.ssh, ~/.aws, ~/.kube, .env, .npmrc, .pypirc)? | Safety |
| SP-2 | No `bypassPermissions` in project-level settings? | Safety |
| SP-3 | No `enableAllProjectMcpServers: true` (supply-chain attack vector)? | Safety |
| SP-4 | MCP server approval is explicit per server, not blanket? | Safety |
| SP-5 | No secrets in `env` section (API keys, tokens as literal values)? | Safety |

## Goal Alignment

| ID | Check | Dim |
|----|-------|-----|
| SG-1 | Config complexity proportional to project needs (not over/under-configured)? | Goal |
| SG-2 | `claudeMdExcludes` present if monorepo (prevents loading irrelevant CLAUDE.md)? | Goal |

## Metadata & Scope

| ID | Check | Dim |
|----|-------|-----|
| SM-1 | Settings in correct scope (project-specific in `.claude/settings.json`, personal in local/user)? | Meta |
| SM-2 | `.claude/settings.local.json` in `.gitignore` (contains personal overrides, not committed)? | Meta |

**Severity guidance:** Invalid JSON (SS-1) is **Critical** — all rules disabled. Missing `permissions.deny` (SP-1) is **High**. `enableAllProjectMcpServers: true` (SP-3) is **High**. `bypassPermissions` in project (SP-2) is **High**.

**Finding identity:** Every FAIL must produce a recommendation with `ID: {item}:{path}:{dim}/v1` in the heading.
