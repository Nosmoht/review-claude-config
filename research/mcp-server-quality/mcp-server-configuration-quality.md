---
last_refreshed: 2026-04-19
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

## Protocol Updates (MCP Spec 2025-11-25, Claude Code v2.1.7+)

*Added 2026-04-19. Three protocol changes shipped between Nov 2025 and Apr 2026; all three relevant for `/review-mcp-server` rubric.*

### Tool-Search / Lazy-Loading

Claude Code auto-activates lazy-loading when tool-definition tokens exceed ~10 K (≥10 % of the context window on standard models):

- Tools marked `defer_loading: true` are not injected up-front.
- A "Tool Search" meta-function is injected instead; it loads 3–5 relevant tools per query (~3 K tokens).
- Token savings: ~85 % for servers with 50+ tools (77 K → 8.7 K).
- Trigger threshold: 10 K tool-description tokens.
- Server-side declaration:
  ```json
  {
    "tool": { "name": "my_large_tool", "defer_loading": true, "inputSchema": {...} }
  }
  ```

### Elicitation

MCP servers can request structured user input mid-tool-call (human-in-the-loop):

- `elicitation/create` request with JSON Schema + `mode: "form" | "url"`.
- Client renders form or redirects to URL.
- Server receives `action: "provided" | "decline" | "cancel"` + `values`.
- Hook integration: `Elicitation` (request fired) and `ElicitationResult` (user response fired) — both gated in v2.1.76+.
- Security rule: **form mode only for non-sensitive inputs** (API keys OK, passwords not OK); URL mode for OAuth/2FA.

### `_meta` Annotations

Tool-output annotations that influence client behavior:

| Annotation | Type | Default | Recommended values |
|------------|------|---------|--------------------|
| `_meta["anthropic/maxResultSizeChars"]` | integer | 5 000 | 10 K–50 K for query results; 100 K–500 K for schema outputs |
| `_meta["cacheControl"]` | string | — | `"public, max-age=86400, s-maxage=604800"` |
| `_meta["cacheTTL"]` | integer | — | 86 400 (24 h), 604 800 (7 d) |
| `_meta["priority"]` | float | 0.5 | 0.0–1.0 |
| `_meta["audience"]` | string | — | `user`, `internal`, `public` |
| `_meta["modifiedAt"]` | ISO 8601 | — | timestamp |

`maxResultSizeChars` is advisory; the client truncates at the declared size. Servers exceeding 500 K are rejected.

### `.mcp.json` Schema Additions (2026)

New top-level fields:

```json
{
  "mcpServers": {
    "server-name": {
      "command": "...", "args": ["..."], "env": {...},
      "disabled": false,             // NEW 2026: toggle without deletion
      "defer_loading": true,         // NEW: explicit lazy-loading signal
      "metadata": {                  // NEW: server documentation
        "description": "...",
        "homepage": "https://..."
      }
    }
  }
}
```

### Scope Precedence

```
Local (.claude/mcp-servers.json in project)
  > Project (.mcp.json)
  > User (~/.claude.json)
```

Duplicate server names across scopes: highest-priority scope wins; server loaded exactly once.

## Security Disclosure (2026-04-16)

*Added 2026-04-19 after disclosure publication. Critical context for `/review-mcp-server` security rubric.*

Publicly disclosed 2026-04-16: approximately 200 000 MCP servers are vulnerable to a protocol-level design flaw in all MCP SDKs (Python, TypeScript, Java, Rust). Anthropic declined an architectural change, labelling the behavior "expected". This forces MCP-server operators to implement mitigations locally.

### Mitigations (required for Grade-A Safety on MCP reviews)

1. **Prompt-shield on tool outputs** — pattern-match against injection signatures (see `skills/review-mcp-server/references/injection-regex-library.md` in P0.3). At minimum: detect `ignore (all )?(previous|prior) instructions`, system-prompt syntax (`<system>`, `[INST]`), base64-suspect blobs >200 chars, `[IMPORTANT]`/`[URGENT]` imperative blocks, Unicode-tag characters (`\u{E0000}–\u{E007F}`).
2. **Tool registry with signatures** — version + digitally-sign tool definitions; reject unknown versions.
3. **Input sanitization** — filter all user inputs before LLM consumption.
4. **Supply-chain discipline** — approved MCP packages only; scan new packages against CVE databases.
5. **OAuth Resource Server Metadata (RFC 9728)** — bind tokens to specific server resources.
6. **`.mcp.json` version-control exclusion** — if `.mcp.json` contains credentials, it must be in `.gitignore`.

### Review-Rubric Implications

New `/review-mcp-server` items (integrated into P0.3):

- **Tool-Dimensioning**: flag when `>50` tools OR `>10 K` description tokens without `defer_loading`.
- **Elicitation-Readiness**: form mode used only for non-sensitive inputs; URL mode for OAuth/2FA; `ElicitationResult` validation implemented.
- **April 2026 security**: prompt-injection scan on tool outputs (Tier A regex library + Tier B LLM confirmation); no hardcoded credentials in `.mcp.json`; RFC 9728 metadata present.
- **Scope-Management**: local/project/user scopes documented; no duplicate names.

## Sources

- [MCP Spec 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25) (Tier 1)
- [MCP Spec — Elicitation (Draft)](https://modelcontextprotocol.io/specification/draft/client/elicitation) (Tier 1)
- [Anthropic: MCP in Claude Code](https://docs.anthropic.com/en/docs/claude-code/mcp) (Tier 1)
- [The Register — Anthropic MCP Design Flaw](https://www.theregister.com/2026/04/16/anthropic_mcp_design_flaw) (Tier 1 — 2026-04-16 disclosure)
- [Microsoft: Indirect Prompt Injection on MCP](https://developer.microsoft.com/blog/protecting-against-indirect-injection-attacks-mcp) (Tier 1)
- [OWASP LLM06:2025](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/) (Tier 1)
- [AgentSeal: 1808 MCP Servers Scanned](https://agentseal.org/blog/mcp-server-security-findings) (Tier 1/2)
- [Docker: MCP Security](https://www.docker.com/blog/mcp-security-explained/) (Tier 2)
- [Apideck: MCP Context Window](https://www.apideck.com/blog/mcp-server-eating-context-window-cli-alternative) (Tier 2)
- [Spring AI: MCP Annotations](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-annotations-overview.html) (Tier 2)
- [FastMCP: .mcp.json Configuration](https://gofastmcp.com/integrations/mcp-json-configuration) (Tier 2)
