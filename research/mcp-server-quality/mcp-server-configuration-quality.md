---
last_refreshed: 2026-04-14
---

# MCP Server Configuration Quality

## Schema

Stdio servers: `command` (required), `args`, `env` (supports `${VAR}` expansion). Remote servers: `type` ("sse"/"http", required), `url` (required), `headers`. Both: `disabled: true` to deactivate without removing.

Config locations: `.mcp.json` (project root, committed), `~/.claude.json` (user, not committed). Agent frontmatter `mcpServers:` (agent-scoped). NOT in `settings.json` — silently ignored there ([#24477](https://github.com/anthropics/claude-code/issues/24477)).

## Security Risk Taxonomy

| Risk | Severity | Evidence |
|------|----------|---------|
| RC1: Excessive Functionality (write/delete when only read needed) | High | OWASP LLM06:2025 |
| RC2: Credential Exposure (secrets in env committed to git) | High | AgentSeal: hardcoded creds in scanned servers |
| RC3: Command Injection (unvalidated args to shell) | Critical | 43% of 1808 servers vulnerable (AgentSeal) |
| RC4: Toxic Data Flow (read-server + write-server = injection path) | High | 843 findings in AgentSeal scan |
| RC5: Supply Chain (malicious/compromised MCP package) | Critical | CVE-2025-6514 in mcp-remote |

## Quantitative Thresholds

| Metric | Threshold | Source |
|--------|-----------|-------|
| Tool token cost | 550-1400 per tool | Apideck, jentic |
| Context budget warning | >30% consumed by tool defs | 72% = severe degradation (Apideck) |
| Tool count soft warning | >50 total | Repo default |
| Tool count hard limit | 128 | GitHub Copilot |
| Security finding rate | 66% of scanned servers | AgentSeal (1808 servers) |

## Server Risk Tiers

- **Tier A (High):** Shell/code execution, filesystem write, database write (Bash, fs-write, postgres-write, Docker)
- **Tier B (Medium):** External API with credentials, network access (GitHub, Slack, email, cloud APIs)
- **Tier C (Low):** Read-only data, local computation (fs-read-only, SQLite read, search, calculator)

## Sources

- [MCP Spec 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25) (Tier 1)
- [Anthropic: MCP in Claude Code](https://docs.anthropic.com/en/docs/claude-code/mcp) (Tier 1)
- [OWASP LLM06:2025](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/) (Tier 1)
- [AgentSeal: 1808 MCP Servers Scanned](https://agentseal.org/blog/mcp-server-security-findings) (Tier 1/2)
- [Docker: MCP Security](https://www.docker.com/blog/mcp-security-explained/) (Tier 2)
- [Apideck: MCP Context Window](https://www.apideck.com/blog/mcp-server-eating-context-window-cli-alternative) (Tier 2)
