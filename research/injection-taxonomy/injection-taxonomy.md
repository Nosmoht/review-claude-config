---
last_refreshed: 2026-04-14
---

# Prompt Injection Taxonomy for Claude Code Configurations

## Provenance Metadata

- Strongest source tier: Tier 1
- Source basis: OWASP Top 10 for LLM Applications 2025 (LLM01), Anthropic system prompt documentation, arXiv 2506.08837 (injection via tool outputs), MCP server security research (AgentSeal 43% command injection rate)
- Last reviewed: 2026-04-14

**Sources:**
- [OWASP Top 10 for LLM Applications 2025 — LLM01: Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) (Tier 1)
- [MCP Server Configuration Quality](../mcp-server-quality/mcp-server-configuration-quality.md) (Repo internal — 43% command injection rate from AgentSeal)
- [Least-Privilege Tool Grants for LLM Agents](../tool-least-privilege/tool-least-privilege-agents.md) (Repo internal — "lethal trifecta" pattern)
- [Audit Harness Research Summary](../../audit-harness-research-summary.md) §1.7, §2.12 (Repo internal — injection and memory poisoning vision)

## Key Finding

Prompt injection in Claude Code configurations manifests through four distinct vectors, each with different detection feasibility within a plugin's static analysis scope. Indirect injection via tool outputs and memory injection via persistent state are the highest-risk vectors because they exploit trust boundaries that static config review alone cannot observe. The primary plugin-detectable indicator is the **data flow path** — configurations that combine untrusted input sources (WebFetch, MCP read tools, user-provided files) with privileged action tools (Bash, Write, Edit) without an explicit sanitization or confirmation boundary.

---

## Injection Vectors

### V1 — Direct Injection (user prompt manipulation)

**Description:** Adversarial user crafts prompts to override system instructions or extract system prompt content.

**Detection within plugin:** Not feasible. The plugin reviews configs, not live prompts. Claude's built-in instruction hierarchy and harmlessness training are the primary defense.

**Relevance to review:** Low for config review. Relevant only when evaluating whether CLAUDE.md or skill descriptions contain instructions that could be easily overridden.

### V2 — Indirect Injection via Tool Output

**Description:** Malicious content embedded in web pages, documents, MCP tool responses, or file contents flows into the agent's context and alters behavior. The agent treats attacker-controlled data as trusted instructions.

**Source:** OWASP LLM01 (Tier 1); arXiv 2506.08837 confirms >60% attack success on undefended agents.

**Detection within plugin:** **Feasible via data flow analysis.** Detectable indicator: a skill/agent that has both a read-from-external tool (WebFetch, WebSearch, MCP read) AND a write/execute tool (Bash, Write, Edit) without an explicit boundary (confirmation gate, output validation step, or input sanitization). This is the "lethal trifecta" from tool-least-privilege research: privileged access + untrusted input + no boundary.

**Checklist mapping:** SP-4 (Tier A combinations), new IJ-* items.

### V3 — Injection via Memory (persistent state poisoning)

**Description:** A compromised or careless prior session writes instruction-like content into persistent memory files. Future sessions load this content into context, silently altering agent behavior across session boundaries.

**Source:** Audit harness research §2.12; OWASP AI Agent Security Cheat Sheet.

**Detection within plugin:** **Feasible via memory file analysis.** Detectable indicators: memory files containing imperative instructions ("Always", "Never", "You must"), system prompt syntax (`<system>`, `[INST]`), or contradictory entries. Addressed by `/audit-memory-hygiene`.

### V4 — Injection via Config Manipulation

**Description:** Attacker modifies CLAUDE.md, hooks.json, .mcp.json, or skills to plant malicious instructions or tool grants that persist across sessions.

**Detection within plugin:** **Feasible via existing review skills.** The entire review suite (`/review-skill`, `/review-hook`, `/review-mcp-server`, `/review-settings`, `/review-claude-md`) already evaluates config quality. The gap is cross-file data flow analysis: detecting when multiple configs combine to create an injection path that no single config reveals alone.

**Checklist mapping:** Existing SP-*, TV-*, new IJ-* items.

---

## Detection Feasibility Summary

| Vector | Plugin Can Detect? | Detection Method | Skill Coverage |
|---|---|---|---|
| V1 Direct | No | Built-in model defense | N/A |
| V2 Indirect | Yes (data flow) | Config surface analysis: external-input + privileged-action combinations | IJ-* checklist items |
| V3 Memory | Yes (file analysis) | Memory hygiene checks: instruction patterns, staleness, contradictions | `/audit-memory-hygiene` |
| V4 Config | Yes (config review) | Existing review skills + cross-primitive analysis | `/review-claude-config` |

## Implications

1. **IJ-* checklist items** should focus on V2 (data flow paths) — this is the highest-value gap in existing Safety checklists.
2. **`/audit-memory-hygiene`** directly addresses V3 — no existing skill covers memory files.
3. **V4 is already covered** by the review suite — no new skill needed, but `/review-claude-config` orchestrator could add a cross-primitive injection surface pass in future.
4. **V1 is out of scope** for a config review plugin — document and exclude.
