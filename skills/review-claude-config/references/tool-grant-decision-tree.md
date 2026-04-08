---
name: tool-grant-decision-tree
description: Archetype-to-tool mapping and high-risk combination flags for Safety dimension tool grant evaluation
last_refreshed: 2026-04-08
---

# Tool Grant Decision Tree

## Archetypes → Minimal Tool Sets

| Archetype | Minimal Tools |
|-----------|--------------|
| Read-only analyst | `Read, Grep, Glob` (+`Bash` for grep/find only) |
| Code modifier | `Read, Grep, Glob, Edit` (+`Bash` for build/test) |
| File creator | `Read, Grep, Glob, Edit, Write` |
| Orchestrator/executor | Above + `Bash`, MCP — justify each tool individually |

*Claude Code sub-agents docs; OWASP AI Agent Security Cheat Sheet (Tier 1).*

## High-Risk Combinations

**[Engineering guidance]** Tier A without justification → Safety capped at **C** (High finding).

**Tier A — critical (mandatory justification):**
- `Bash` + network tool (`WebFetch`/`WebSearch`/MCP web)
- `Bash` + `Write`/`Edit`
- `Write`/`Edit` + `WebFetch`/`WebSearch`
- Broad `Bash` (no allowlist) + untrusted input
- Communication MCP + file read + no approval gate

**Tier B — high (justify; Medium finding):**
- `Write`/`Edit` without path restriction + external input
- DB MCP with write/delete, no read-only enforcement
- `Bash` without allowlist on auto-dispatched agent
- No `tools:` declared (inherits all from parent)
- `Bash` + credential/secrets file access

**Tier C — medium (document rationale):**
- `WebFetch` + `Write` without sandboxing
- Read tools + unrestricted path + untrusted input
- `allowedTools` + `bypassPermissions` active (allowlist nullified)

*OWASP LLM06:2025; Progent arXiv:2504.11703; MiniScope arXiv:2512.11147 (Tier 1).*

## Permission Mode

- `bypassPermissions` nullifies `allowedTools` — use `disallowedTools` for hard deny in all modes
- Locked-down unattended: `tools: [Read, Grep]` + `permissionMode: dontAsk`
- Sub-agents do NOT inherit parent permissions — declare `tools:` or `disallowedTools:` explicitly

*Claude Agent SDK Permissions (Tier 1).*
