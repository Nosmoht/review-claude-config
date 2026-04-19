---
name: injection-regex-library
description: Tier-A deterministic prompt-injection patterns for MCP-output and config scanning (primary scan; LLM Tier-B only on Tier-A hits)
last_refreshed: 2026-04-19
---

# Prompt-Injection Regex Library (Tier A)

Deterministic patterns scanned over MCP server tool outputs, `.mcp.json`
content, and config bodies. Two-tier scan: **Tier A** (this file, regex,
fast, primary). **Tier B** (LLM, only invoked when Tier-A hits) confirms
severity and extracts surrounding context. Hit-then-confirm minimises both
false positives and LLM cost.

Source: April 2026 MCP disclosure mitigations
(`research/mcp-server-quality/mcp-server-configuration-quality.md`
§"Mitigations") + Microsoft indirect-injection guidance + standard
jailbreak corpora.

Each pattern declares `severity` (High = explicit override attempt; Medium
= suspicious framing; Low = supporting signal). Patterns marked
`(case-insensitive)` use the `/i` flag.

## High-severity patterns (explicit override attempts)

| # | Name | Pattern | Notes |
|---|------|---------|-------|
| IL-1 | ignore-prior-instructions | `ignore\s+(all\s+)?(previous\|prior)\s+instructions` (case-insensitive) | Canonical override |
| IL-2 | system-prompt-tag | `<\s*system\s*>` OR `<\s*\|im_start\|\s*>` | XML/ChatML system tag |
| IL-3 | inst-tag | `\[\s*INST\s*\]` OR `\[\s*/INST\s*\]` | Llama-style instruction tag |
| IL-4 | system-marker | `(?m)^\s*###\s*(system\|user\|assistant)\b` (case-insensitive) | Markdown system marker |
| IL-5 | begin-prompt-block | `BEGIN_PROMPT\b` OR `END_PROMPT\b` | Prompt-injection delimiter |
| IL-6 | role-override | `you\s+are\s+now\s+(a\|an)\s+(different\|new)` (case-insensitive) | Role swap |
| IL-7 | forget-instructions | `forget\s+(everything\|all\|prior\|the\s+above)` (case-insensitive) | Instruction-erasure prompt |
| IL-8 | jailbreak-mode | `(jailbreak\|DAN\s+mode\|developer\s+mode\|godmode)` (case-insensitive) | Named jailbreak |
| IL-9 | reveal-system-prompt | `reveal\s+(your\|the)\s+(system\|original)\s+(prompt\|instructions)` (case-insensitive) | System-prompt exfil |
| IL-10 | act-as-ai-must | `as\s+(the\|an)\s+AI[\s,.]+\s*you\s+(must\|should\|will)` (case-insensitive) | Pseudo-authority frame |
| IL-11 | execute-command-frame | `execute\s+(the\s+following\|this)\s+(command\|code\|script)` (case-insensitive) | Action-trigger phrasing |

## Medium-severity patterns (suspicious framing)

| # | Name | Pattern | Notes |
|---|------|---------|-------|
| IL-12 | urgency-block | `\[\s*(IMPORTANT\|URGENT\|CRITICAL\|ATTENTION)\s*\]` | Urgency frame |
| IL-13 | respond-only-with | `respond\s+only\s+with\b` (case-insensitive) | Output-shape hijack |
| IL-14 | template-injection | `\{\{[^}]*\b(system\|prompt\|instruction\|exec)\b[^}]*\}\}` (case-insensitive) | Mustache-style injection |
| IL-15 | hidden-unicode-tags | `[\x{E0000}-\x{E007F}]` | Unicode-tag steganography (renders invisible) |
| IL-16 | base64-blob | `[A-Za-z0-9+/=]{200,}` | Long b64 blob (verify decoding for command/script content) |
| IL-17 | url-with-credentials | `https?://[^/\s]+:[^@/\s]+@` | Embedded creds in URL (auth-header smuggle) |
| IL-18 | dangerous-uri-scheme | `\b(file\|gopher\|jar\|netdoc)://` | SSRF-prone URI in output |

## Low-severity patterns (supporting signal — escalate only on co-occurrence with High/Medium)

| # | Name | Pattern | Notes |
|---|------|---------|-------|
| IL-19 | excessive-newlines | `\n{6,}` | Padding before injected payload |
| IL-20 | invisible-spaces-cluster | `[\x{200B}-\x{200F}\x{202A}-\x{202E}\x{2060}-\x{206F}]{3,}` | Zero-width / RLO clusters |
| IL-21 | role-block-marker | `(?m)^\s*<\s*/?\s*(role\|persona\|context)\s*>` | Persona/role boundary tags |
| IL-22 | shell-redirect-in-arg | `(\s\|\^)(>\|>>\|2>&1)\s*/` | Shell I/O redirection in args field |

## Two-tier scan procedure

1. Run all 22 patterns against (a) every tool-output payload returned by an
   MCP server during the review session and (b) string fields inside the
   parsed `.mcp.json` (`command`, every `args[i]`, every `env` value).
2. For each Tier-A hit, capture `(file, char_offset, pattern_id, matched_text[≤200 chars])`.
3. Tier B (LLM): only invoked when ≥1 Tier-A hit exists. Pass `(matched_text, surrounding_context_300_chars, pattern_id)` and ask the LLM to:
   - Confirm severity (downgrade Medium→Low if benign code sample, etc.).
   - Identify exfil/RCE chain potential.
4. Report only after Tier B confirmation. Tier-A-only hits surface as `Low — pending Tier-B confirmation`.

## Out of scope

- Server-process behavior monitoring (covered by hooks/audit-logger.py, not regex).
- Static binary analysis of MCP packages (supply-chain — see RC5 mitigation).
- Token-level adversarial perturbation (research-grade attack; not in 2026 production traffic).
