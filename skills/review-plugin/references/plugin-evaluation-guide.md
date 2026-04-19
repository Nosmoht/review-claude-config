---
name: plugin-evaluation-guide
description: Type-specific evaluation criteria for Claude Code plugins (.claude-plugin/plugin.json + component layout)
last_refreshed: 2026-04-19
---

# Plugin Evaluation Checklist

Answer EVERY item: PASS | FAIL | NA. No skipping. FAILs map to Dim for scoring.

Plugins use 4 dimensions (renormalized): Completeness 25%,
Goal Alignment 25%, Safety 30%, Metadata 20%. Skip Clarity, PE, CE
(plugin manifests are declarations, not prompts or workflows).

Authoritative reference: `research/claude-code/plugin-system.md` —
schema fields, marketplace variants, namespacing, and the canonical
top-5 failure modes.

## Plugin Manifest (PM)

| ID | Check | Dim |
|----|-------|-----|
| PM-1 | `.claude-plugin/plugin.json` parses as valid JSON. | Compl |
| PM-2 | `name` present, kebab-case (`^[a-z][a-z0-9-]{0,62}[a-z0-9]$`), max 64 chars. | Compl |
| PM-3 | `name` does not contain `anthropic` or `claude` as substring (Anthropic naming policy). | Compl |
| PM-4 | `description` present, ≤1024 chars, no XML tags (`<`, `>`). | Compl |
| PM-5 | `version` present and valid semver (`^\d+\.\d+\.\d+(-[\w.]+)?$`). | Compl |
| PM-6 | If `author` present, it is `{name: string, email?: string}` — not a bare string. | Meta |
| PM-7 | If `homepage` or `repository` present, full URL with scheme. | Meta |
| PM-8 | If `license` present, valid SPDX identifier (`MIT`, `Apache-2.0`, etc.). | Meta |
| PM-9 | If `keywords` present, array of short strings (≤32 chars each). | Meta |
| PM-10 | `name` not on the reserved-name list (`claude-code-marketplace`, `claude-code-plugins`, `claude-plugins-official`, `anthropic-marketplace`, `anthropic-plugins`, `official-claude-plugins`, `official-anthropic-*`). | Safety |
| PM-11 | `description` ≥40 chars and free of placeholder text (`TODO`, `Lorem ipsum`, `FIXME`). | Meta |
| PM-12 | If `marketplace.json` co-located, its declared version for this plugin matches `plugin.json` `version` exactly. | Compl |

## Component Layout (CL)

| ID | Check | Dim |
|----|-------|-----|
| CL-1 | Components live in plugin root, NOT inside `.claude-plugin/` (canonical failure mode F1). Glob `<plugin-root>/.claude-plugin/skills/*` returns 0 entries. | Compl |
| CL-2 | Declared `skills` path resolves under plugin root (default `skills/`). If declared explicitly, the path exists. | Compl |
| CL-3 | Declared `agents` path resolves under plugin root. | Compl |
| CL-4 | Declared `hooks` is either a relative path to a `hooks.json` OR an inline event object — both forms valid; mixed (object with `path` field) is invalid. | Compl |
| CL-5 | No skill name collides with another loaded plugin's skill name; plugin namespacing (`/<plugin-name>:<skill-name>`) is reachable for every skill. | Goal |

## Top-5 Failure Modes (F)

| ID | Failure mode | Check | Dim |
|----|--------------|-------|-----|
| F-1 | Components in `.claude-plugin/` | Glob `.claude-plugin/{skills,agents,hooks,commands}` returns 0 hits. | Compl |
| F-2 | Relative paths in URL marketplaces | If `marketplace.json` source is `url` or `github`, no plugin entry uses bare `./` source. | Compl |
| F-3 | Version conflict | `plugin.json.version == marketplace.json.plugins[name].version` (when both present). | Compl |
| F-4 | Non-kebab-case skill names | Every `<plugin-root>/skills/*/SKILL.md` directory is kebab-case. | Compl |
| F-5 | Private repo without auth token | If `repository` URL is private (heuristic: contains `git@` or known-private-host pattern), `plugin.json` includes a `private: true` flag OR `keywords` contains `auth-required`. | Safety |

## Injection Hardening (IJ)

Two-tier scan over plugin manifest body fields (`description`,
`keywords[]`, `author.name`, `metadata.*` strings, every `args[i]` in
`hooks` if inline). Tier A (regex, primary) is a strict subset of
`skills/review-mcp-server/references/injection-regex-library.md`:

| ID | Pattern | Severity |
|----|---------|----------|
| IJ-1 | `<\s*system\s*>` OR `\[\s*INST\s*\]` OR `(?m)^\s*###\s*system\b` | High |
| IJ-2 | `ignore\s+(all\s+)?(previous\|prior)\s+instructions` (case-insensitive) | High |
| IJ-3 | `forget\s+(everything\|all\|prior)` (case-insensitive) | High |
| IJ-4 | `\[\s*(IMPORTANT\|URGENT\|CRITICAL)\s*\]` followed by an imperative verb (`execute`, `run`, `install`, `download`) | Medium |
| IJ-5 | `[\x{E0000}-\x{E007F}]` (Unicode tag steganography) | Medium |
| IJ-6 | URL with embedded credentials (`https?://[^/\s]+:[^@/\s]+@`) | High |

A Tier-A hit alone is **Low — pending Tier-B confirmation**. Confirmation
requires either (a) another tool (the LLM in this skill is read-only
and cannot self-confirm) OR (b) a maintainer review. Without
confirmation, do not raise above Low.

## Marketplace Compliance Subset (MS)

| ID | Check | Dim |
|----|-------|-----|
| MS-1 | All directory names under `<plugin-root>/skills/` and `<plugin-root>/agents/` are kebab-case. | Compl |
| MS-2 | No hardcoded credentials in any inspected file (regex `/(api[_-]?key\|secret\|token\|password)\s*[:=]\s*["'][\w!@#$%-]{16,}["']/i`). | Safety |
| MS-3 | `description` ≥40 chars and not placeholder (cross-references PM-11; flagged separately for marketplace gating). | Meta |

## Severity Guidance

- Hardcoded credentials (MS-2) and reserved-name use (PM-10) are **High** severity.
- Component layout F1 is **High** (silent component-load failure breaks the plugin without error).
- IJ-* High patterns confirmed are **High**; unconfirmed Tier-A only are **Low**.
- Schema PM-1/PM-2/PM-5 failures (manifest broken) are **Critical**.

## Finding Identity

Every FAIL must produce a recommendation with `ID: {item}:{path}:{dim}/v1` in the heading.
