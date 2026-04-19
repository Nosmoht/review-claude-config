---
name: mcp-2026-security-checklist
description: April 2026 MCP vulnerability disclosure — operator-side mitigation checklist (loaded JIT by /review-mcp-server when an .mcp.json is present)
last_refreshed: 2026-04-19
---

# April 2026 Security Disclosure (APR)

Disclosed 2026-04-16: ~200 K MCP servers vulnerable to a protocol-level
flaw across all SDKs (Python, TypeScript, Java, Rust). Anthropic
declined an architectural change, labelling the behavior "expected".
Operators must implement mitigations locally. APR FAIL on any item caps
Safety at Grade B.

Source:
`research/mcp-server-quality/mcp-server-configuration-quality.md`
§"Security Disclosure (2026-04-16)" + 5-tier mitigation list.

| ID | Check | Dim |
|----|-------|-----|
| APR-1 | Tool outputs scanned via sibling `injection-regex-library.md` (Tier A); ≥1 hit triggers Tier-B LLM confirmation; report records both `pattern_id` and Tier-B verdict. | Safety |
| APR-2 | OAuth-authenticated servers expose RFC 9728 `oauth-protected-resource` metadata; tokens scoped to specific resources, not session-wide. | Safety |
| APR-3 | MCP package source pinned (registry entry, version, integrity hash); CVE database scanned on package upgrade (RC5: supply chain). | Safety |
| APR-4 | All user inputs forwarded to MCP server tools pass through input-sanitization (escape, length-cap, type-check) — no raw forward of user prompt to tool args. | Safety |
| APR-5 | Tool registry with digital signatures; reject unknown tool versions when supported by client. | Safety |

## Severity rules

- Any APR-1 hit confirmed by Tier-B → **High** finding (active injection signal in production output).
- APR-2/APR-3/APR-4/APR-5 single-item failure with no exploit observed → **Medium**.
- Two or more APR-* failures co-occurring → **High** (compound exposure surface).

## Cross-references

- Pattern catalog: `injection-regex-library.md` (sibling)
- Threat model: `research/mcp-server-quality/mcp-server-configuration-quality.md` §"Security Disclosure (2026-04-16)"
- Two-tier scan procedure: `injection-regex-library.md` §"Two-tier scan procedure"
