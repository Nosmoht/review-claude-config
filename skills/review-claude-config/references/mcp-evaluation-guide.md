---
name: mcp-evaluation-guide
description: Type-specific evaluation criteria for MCP server configurations (.mcp.json files)
last_refreshed: 2026-04-19
---

# MCP Server Evaluation Checklist

Answer EVERY item per server entry: PASS | FAIL | NA. No skipping. FAILs map to Dim for scoring.

MCP configs use 4 dimensions (renormalized): Completeness 25%, Goal Alignment 25%, Safety 30%, Metadata 20%. Skip: Clarity, PE, CE (MCP configs are declarations, not prompts or workflows).

Reference catalog: protocol updates (tool-search/lazy-loading,
elicitation, `_meta` annotations, 2026 `.mcp.json` schema additions),
April 2026 vulnerability disclosure, and the 5-tier mitigation list live
in `research/mcp-server-quality/mcp-server-configuration-quality.md`.
Tier-A injection patterns live in `injection-regex-library.md` (sibling
file, ≥20 patterns).

## Correctness & Completeness

| ID | Check | Dim |
|----|-------|-----|
| MC-1 | Config in correct location (`.mcp.json` at project root or `~/.claude.json`, NOT `settings.json`)? | Compl |
| MC-2 | All required fields present (`command` for stdio; `type`+`url` for remote)? | Compl |
| MC-3 | `args` array well-formed — no unquoted shell metacharacters or expansion pitfalls? | Compl |

## Security & Least Privilege

| ID | Check | Dim |
|----|-------|-----|
| MC-4 | No hardcoded secrets in `env` values (API keys, tokens, passwords as literals)? | Safety |
| MC-5 | Env vars use `${VAR}` or `${VAR:-default}` expansion — not plain strings for credentials? | Safety |
| MC-6 | No Tier A servers (shell exec, fs write, db write) without documented justification? | Safety |
| MC-7 | No toxic data flow combinations (external-data-reader + local-file-writer) without justification? | Safety |

## Goal Alignment

| ID | Check | Dim |
|----|-------|-----|
| MG-1 | Each server provides tools relevant to the project's stated domain/purpose? | Goal |
| MG-2 | No duplicate/overlapping servers; total tool count ≤50 (warn) or ≤128 (hard limit)? | Goal |

## Metadata Hygiene

| ID | Check | Dim |
|----|-------|-----|
| MC-8 | No stale/orphan entries; server names descriptive; `disabled: true` for optional servers? | Meta |
| MC-9 | `metadata.description` and `metadata.homepage` populated for non-trivial servers (2026 schema addition); aids audit and reproducibility. | Meta |

## Tool Dimensioning (TD)

| ID | Check | Dim |
|----|-------|-----|
| TD-1 | Servers with >50 tools OR >10 K tool-description tokens declare `defer_loading: true` (otherwise Claude Code auto-injects all tool defs at session start, costing ~10 % of context). | Goal |
| TD-2 | Tools whose results may exceed 5 K chars declare `_meta["anthropic/maxResultSizeChars"]` (10 K–50 K typical, ceiling 500 K). | Goal |

## Elicitation Readiness (EL)

| ID | Check | Dim | Trigger |
|----|-------|-----|---------|
| EL-1 | `mode: "form"` only for non-sensitive inputs; passwords, OAuth/2FA secrets, MFA codes use `mode: "url"`. | Safety | Tool issues `elicitation/create` |
| EL-2 | Server validates `action: "provided" \| "decline" \| "cancel"` paths and never proceeds on "cancel" without explicit handling. | Compl | Tool issues `elicitation/create` |
| EL-3 | Target CLI ≥ v2.1.76 (when `Elicitation` and `ElicitationResult` events became available). | Compl | Tool issues `elicitation/create` |

## Scope & Precedence (SP)

| ID | Check | Dim |
|----|-------|-----|
| SP-1 | No duplicate server name across local / project / user scopes; if shadowed, the higher-priority entry is intended (local > project > user). | Meta |
| SP-2 | `.mcp.json` declared at project root, not nested or in `settings.json` (silently ignored — bug #24477). | Compl |
| SP-3 | `.mcp.json` is in `.gitignore` IF it contains credentials in `env`; non-credentialed `.mcp.json` MAY be committed. | Safety |

## April 2026 Security Disclosure (APR)

APR items live in sibling `mcp-2026-security-checklist.md` (loaded JIT
when `.mcp.json` is present). Five APR items cover Tier-A/B injection
scan (APR-1), RFC 9728 metadata (APR-2), supply-chain pinning (APR-3),
input sanitization (APR-4), and tool registry signatures (APR-5).

**Severity guidance:** Hardcoded credentials (MC-4) and unjustified Tier A servers (MC-6) are **High** severity. Toxic data flow (MC-7) is **High**. APR-1 hits with Tier-B confirmation are **High**. Missing required fields (MC-2) is **Medium**.

**Finding identity:** Every FAIL must produce a recommendation with `ID: {item}:{path}:{dim}/v1` in the heading.
