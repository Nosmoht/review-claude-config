---
name: mcp-evaluation-guide
description: Type-specific evaluation criteria for MCP server configurations (.mcp.json files)
last_refreshed: 2026-04-14
---

# MCP Server Evaluation Checklist

Answer EVERY item per server entry: PASS | FAIL | NA. No skipping. FAILs map to Dim for scoring.

MCP configs use 4 dimensions (renormalized): Completeness 25%, Goal Alignment 25%, Safety 30%, Metadata 20%. Skip: Clarity, PE, CE (MCP configs are declarations, not prompts or workflows).

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

**Severity guidance:** Hardcoded credentials (MC-4) and unjustified Tier A servers (MC-6) are **High** severity. Toxic data flow (MC-7) is **High**. Missing required fields (MC-2) is **Medium**.

**Finding identity:** Every FAIL must produce a recommendation with `ID: {item}:{path}:{dim}/v1` in the heading.
