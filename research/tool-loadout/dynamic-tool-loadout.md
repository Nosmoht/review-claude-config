---
name: dynamic-tool-loadout
description: Tier-1 evidence on accuracy degradation with growing tool catalogs and pre-filter / retrieval mitigations; backs the engineering-baseline §"Dynamic Tool Loadout" upgrade
last_refreshed: 2026-04-29
---

# Dynamic Tool Loadout — Evidence Base

When an LLM agent is given a large tool catalog (50+ tools), tool-selection accuracy degrades sharply. Pre-filtering the catalog to a small relevant subset (3-5 tools) restores accuracy. This pattern is now sufficiently corroborated to upgrade the baseline label from `[Low-evidence area]` to `[Engineering guidance]`.

## Tier-1 Evidence

### Tool-Catalog Size vs Accuracy (Empirical Curve)

Measured across multiple LLMs:

| Catalog size | Accuracy range | Source |
|---|---|---|
| ~50 tools (~8K tokens) | 84-95% | Vector-based tool selection survey (multiple sources) |
| ~200 tools (~32K tokens) | 41-83% | Same |
| ~740 tools (~120K tokens) | 0-20% | Same |
| Claude-specific cutoff | accuracy degrades **>30-50 tools** | Anthropic / litellm Tool Search docs |

The curve is monotonically decreasing and steeper for non-frontier models. Position bias (Lost-in-the-Middle, see `research/context-engineering/lost-in-the-middle.md`) compounds the effect — at 741 tools, middle positions show 22-52% accuracy vs 31-32% at start/end, but the absolute degradation overwhelms positional remediation.

### AutoTool — Dynamic Tool Selection

- **Source**: arXiv:2511.14650 (AutoTool: Efficient Tool Selection for Large Language Model Agents); arXiv:2512.13278 (AutoTool: Dynamic Tool Selection and Integration for Agentic Reasoning).
- **Method**: Dual-phase optimization pipeline; agent alternates between rationale generation and tool selection from a large evolving toolset.
- **Headline metrics**: average gains over fixed-toolset baselines — **+6.4% math/science**, **+4.5% search-QA**, **+7.7% code-generation**, **+6.9% multimodal**.
- **Implication**: dynamic loadout is a *measurable* improvement over static toolset exposure — not a low-evidence heuristic.

### Vector-Based Tool Retrieval (Semantic Tool Discovery)

- **Source**: arXiv:2603.20313 (*Semantic Tool Discovery for Large Language Models*).
- **Method**: Index MCP tools as dense embeddings; perform similarity search at request time; expose top 3-5 most semantically relevant tools instead of full catalog.
- **Headline metric**: **92.1% precision at K=1** when retrieving a single tool — i.e., the system's top retrieval is correct >9 times in 10.
- **Mechanism**: reduces decision complexity (small relevant set) and avoids long-context position bias.

### Anthropic Tool Search

- **Source**: Anthropic API documentation (litellm provider docs `litellm.ai/docs/providers/anthropic_tool_search`); Anthropic Contextual Retrieval blog.
- **Method**: Claude-native tool search primitive — explicitly designed to expose only the tools relevant to the current turn.
- **Implication**: the issue is acknowledged at the model-vendor level. Static-toolset exposure is no longer the recommended pattern for >50-tool catalogs.

### Tool Attention (Dynamic Tool Gating)

- **Source**: arXiv:2604.21816 (*Tool Attention Is All You Need: Dynamic Tool Gating and Lazy Schema Loading*).
- **Method**: Lazy schema loading — load full tool schemas only when the gating layer scores the tool above a threshold for the current turn.
- **Implication**: reinforces the lazy-loading pattern as a robust mitigation across architectures.

## Decision Rules for Skill Authors

1. **≤ 10 tools in `allowed-tools`**: no dynamic loadout needed. Static exposure is fine.
2. **11-30 tools**: consider whether a curated subset would improve clarity. Document the rationale per tool (already covered by SP-2b rubric item).
3. **>30 tools**: dynamic loadout strongly recommended. Either:
   - Use Anthropic's tool search primitive when available
   - Decompose the skill into archetype-specific subagents that each see a small relevant subset
   - Move infrequent tools to a documented escalation path
4. **External MCP servers with >50 exposed tools**: pre-filter via the MCP server itself (server-side gating) rather than relying on agent-side selection.

## Rubric Cross-References

- `engineering-baseline.md` §"Tool Set Curation" (existing) — establishes least-privilege as default
- `engineering-baseline.md` §"Dynamic Tool Loadout" (this commit upgrades the label) — establishes pre-filter pattern for large catalogs
- `scoring-rubric.md` §"Tool-Grant Alignment" SP-2b/4b — already enforce per-tool justification
- `skills/review-claude-config/references/tool-grant-decision-tree.md` — Tier A/B/C combinations + this evidence informs the catalog-size escalation tier

No new rubric item added — the existing SP-2b ("per-tool sentence binding each `allowed-tools` entry to an archetype use-case") already enforces the discipline at small catalog sizes. Large-catalog cases (>30 tools) are rare in this repo's skills (most use ≤10 tools); when they arise, SP-2b's per-tool justification requirement compounds with the >10-tool guidance to produce natural pressure toward dynamic loadout.

## Self-Application

| Skill | Tool count | Above >30 cutoff? | Verdict |
|---|---|---|---|
| `review-skill` | 7 (Read, Write, Glob, WebSearch, WebFetch, Agent, Bash) | No | Compliant |
| `audit-repo` | 7 (Agent, Read, Write, Glob, Grep, WebSearch, WebFetch) | No | Compliant |
| `scaffold-skill` | typical 5-7 | No | Compliant |

All sampled skills sit well below the >30-tool cutoff. Dynamic Tool Loadout becomes operationally relevant if the repo ever introduces an MCP-server-backed skill exposing the full server catalog — that path is governed by the new evidence + SP-2b together.

## Cross-Validation Posture

Five independent sources (4 arXiv + 1 Anthropic vendor docs):
- AutoTool (×2 papers) — empirical gains
- Semantic Tool Discovery — precision@K metric
- Tool Attention — gating mechanism
- Anthropic — vendor confirmation

Two are 2026-recent (post-original-issue-filing), three are 2024-2025. Passes web-research rule (≥2 Tier-1 sources, ≥1 vendor confirmation).

## References

- arXiv:2511.14650 — AutoTool: Efficient Tool Selection
- arXiv:2512.13278 — AutoTool: Dynamic Tool Selection and Integration
- arXiv:2603.20313 — Semantic Tool Discovery for LLMs
- arXiv:2604.21816 — Tool Attention / Dynamic Tool Gating
- https://www.anthropic.com/news/contextual-retrieval — Anthropic Contextual Retrieval
- https://docs.litellm.ai/docs/providers/anthropic_tool_search — Claude Tool Search primitive

## Repo Cross-References

- `research/context-engineering/lost-in-the-middle.md` — position-bias compounds tool-list-position effects
- `skills/review-claude-config/references/tool-grant-decision-tree.md` — Tier A/B/C tool combinations
- `research/tool-least-privilege/tool-least-privilege-agents.md` — Progent / least-privilege foundation
