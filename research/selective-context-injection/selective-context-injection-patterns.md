---
last_refreshed: 2026-04-08
---

# Selective Context Injection for LLM Agents: Evidence-Based Patterns

## Provenance Metadata

- Strongest source tier: Tier 1
- Source basis: arXiv:2412.15605 (CAG), arXiv:2501.09136 (Agentic RAG), arXiv:2602.03442 (A-RAG), arXiv:2403.12968 (LLMLingua-2, ACL 2024), arXiv:2510.14337 (Stop-RAG). Supplemental Tier 2: Anthropic context engineering guidance, GitHub Copilot architecture blog. Tier 3: Cursor context discovery article (flagged where sole source).
- Last reviewed: 2026-04-08

**Sources:**
- [Don't Do RAG: Cache-Augmented Generation (arXiv 2412.15605)](https://arxiv.org/html/2412.15605v2)
- [Agentic RAG: A Survey (arXiv 2501.09136)](https://arxiv.org/abs/2501.09136)
- [A-RAG: Hierarchical Retrieval Interfaces (arXiv 2602.03442)](https://arxiv.org/html/2602.03442v1)
- [Stop-RAG: Value-Based Retrieval Control (arXiv 2510.14337)](https://arxiv.org/abs/2510.14337)
- [LLMLingua-2: Data Distillation for Efficient Prompt Compression (arXiv 2403.12968, ACL 2024)](https://arxiv.org/html/2403.12968v2)
- [Anthropic Engineering: Equipping Agents with Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [GitHub Blog: Agentic Primitives and Context Engineering](https://github.blog/ai-and-ml/github-copilot/how-to-build-reliable-ai-workflows-with-agentic-primitives-and-context-engineering/)
- [Anthropic Context Engineering Best Practices](https://01.me/en/2025/12/context-engineering-from-claude/)

---

## Key Finding

For bounded, stable knowledge corpora that fit within ~64K tokens, **Cache-Augmented Generation (CAG) outperforms RAG** by eliminating retrieval errors entirely. For larger or dynamic corpora, **three-layer progressive disclosure** (metadata always-on → full document JIT → sub-files on-demand) is the production-proven pattern. The critical bottleneck in both approaches is **description quality**, not retrieval mechanism.

---

## Evidence

### 1. CAG vs RAG: The Decision Boundary

**Source:** arXiv:2412.15605 (Tier 1)

CAG preloads all documents into the LLM's extended context and precomputes the KV cache offline. Queries skip retrieval entirely.

| Dataset | CAG BERTScore | Sparse RAG | Dense RAG |
|---------|--------------|------------|-----------|
| HotPotQA Small | 0.7951 | 0.7676 | 0.7582 |
| SQuAD Small | 0.7695 | 0.7616 | 0.7586 |
| HotPotQA Medium | 0.7821 | 0.7633 | — |

**CAG wins** because it eliminates retrieval errors — you cannot miss a relevant passage if everything is loaded. The performance gap narrows as corpus size increases.

**Decision boundary:** CAG is practical when the knowledge base fits in 32K–128K tokens. For corpora beyond context window capacity, Agentic RAG with adaptive retrieval classifiers is the alternative (arXiv:2501.09136).

**Application to this repo:** 24 research files at ~500–1,500 tokens each = ~12K–36K tokens total. This corpus fits squarely in CAG territory for models with 200K context. Full corpus loading is technically viable.

### 2. Three-Layer Progressive Disclosure (Industry Convergence)

**Sources:** Anthropic Engineering Blog (Tier 1), GitHub Copilot Docs (Tier 2), Cursor Architecture (Tier 3)

All three major AI coding tools independently converged on the same three-layer architecture:

| Layer | Content | Always-on tokens | Loaded when |
|-------|---------|-----------------|-------------|
| 0 | Name + description only | ~20–50 tokens/entry | Always |
| 1 | Full skill/instruction file | ~500–2,000 tokens | Task matches description |
| 2 | Referenced sub-files (forms, references) | varies | Sub-task requires it |

**Anthropic Agent Skills pattern (Tier 1):** The system prompt contains only skill `name` + `description`. Full `SKILL.md` is loaded when metadata signals relevance. Referenced supplementary files (`reference.md`, `forms.md`) are loaded within a skill execution only when needed.

**GitHub Copilot `applyTo` pattern (Tier 2):** Domain-specific `.instructions.md` files activate only when the current file path matches the glob pattern — deterministic routing via file path, not semantic embedding.

**Adoption:** Anthropic published the Agent Skills open standard in Dec 2025; adopted by OpenAI, Google, GitHub Copilot, and Cursor within weeks. This constitutes strong convergent evidence.

### 3. A-RAG: Hierarchical Retrieval for Large Corpora

**Source:** arXiv:2602.03442 (Tier 1, Feb 2026)

For corpora too large for CAG, A-RAG exposes three tool-level interfaces:
1. Keyword search → abbreviated snippet previews (cheap, fast)
2. Semantic search → embedding-ranked results
3. Chunk read → full content for identified chunks

The agent operates in a ReAct loop, choosing which interface to use. Token tracking prevents redundant loads (zero tokens on re-read). Performance: superior accuracy with comparable or fewer tokens vs. flat RAG.

The index-first pattern: lightweight manifest → LLM decides which entries to fetch → full content loaded JIT. This is what a well-described CLAUDE.md index implements without any infrastructure.

### 4. Description Quality Is the Entire Bottleneck

**Sources:** Anthropic Engineering (Tier 1), A-RAG paper (Tier 1)

Neither Anthropic's production system nor any production AI coding assistant uses embedding-based routing for skills/instructions. **The agent routes based on reading descriptions.**

A poor description causes:
- False negatives: relevant file not loaded because description was too vague
- False positives: irrelevant file loaded, wasting tokens and diluting context

**Critical finding:** Improving description quality is strictly better ROI than improving retrieval mechanism. A perfect embedding model on bad descriptions performs worse than a simple keyword match on rich descriptions.

**What makes a good routing description:**
- States the primary use trigger in user-task terms ("Load when evaluating token efficiency...")
- Includes the single most important metric or threshold ("key finding: ISR <30% at 11.9 constraints")
- Names the output type ("produces Grade C if unmitigated, Grade B if mitigated")

### 5. Knowledge Compression: LLMLingua-2

**Source:** arXiv:2403.12968 (ACL 2024, Tier 1)

| Compression Ratio | Performance Retention | Latency Benefit |
|------------------|-----------------------|-----------------|
| 2x | ~99.1% | 1.6x |
| 5x | ~95% | 2.9x |

**Key insight:** GPT-4 trained on compression tasks learned to preserve **nouns, adjectives, and numerals** as highest-value tokens. Connective tissue (prepositions, conjunctions, filler) is safe to drop.

This finding validates manual compression: a human editor applying noun/metric/recommendation preservation achieves similar compression ratios as LLMLingua-2 without specialized tooling.

**Practical target:** Each research file can be compressed to a ~100-token "always-on" snippet preserving all key findings. 24 files × 100 tokens = 2,400 tokens always-on. Compared to loading all 24 files (~36K tokens), this achieves 15x compression.

### 6. Stop-RAG: When to Stop Retrieving

**Source:** arXiv:2510.14337 (Oct 2025, Tier 1)

Models the "should I retrieve again?" decision as a finite-horizon Markov decision process with value-based control. Trained to recognize when sufficient evidence has been gathered.

**Application:** Relevant for iterative retrieval skills (e.g., `/refresh-engineering-baseline`). Prevents over-retrieval loops. Not needed for static file loading.

---

## Recommendations for Bounded Research Corpora

### Recommendation 1: Enhance Index Descriptions as Routing Signals (High priority, no tooling)

**Current state:** CLAUDE.md research index has one-liners like `— constraint density thresholds, <30% ISR at high load, rubric guidance`.

**Target state:** 2-sentence format per entry:
```
[File](path) — Key finding with primary metric. Load when: [trigger condition].
```

Example:
```
[Instruction Following at Scale](research/instruction-following/...) — ISR drops to <30% at avg 11.9 constraints (AgentIF); Claude Sonnet follows linear decay from first density increase. Load when reviewing skill/rule body for instruction overload or writing new constraints.
```

**Cost:** ~300–500 additional tokens always-on for 24 entries. **ROI:** Eliminates false negatives from vague descriptions; enables accurate JIT loading without any infrastructure.

### Recommendation 2: Compact Always-On Digest (Medium priority, ~2,400 tokens)

Create `skills/review-claude-config/references/research-digest.md` — one entry per research file, ~100 tokens each using LLMLingua-2 compression principles (keep key findings, metrics, applicability; drop methodology).

Skills can load this single file JIT instead of individual research files for quick context orientation. Full research files remain available for deep dives.

### Recommendation 3: CAG for Maintainer Sessions (Optional, highest fidelity)

The full 24-file corpus (~36K tokens) is within CAG range for Claude Sonnet 4.6 (200K context). For maintainer sessions doing deep work (rubric updates, baseline refreshes), loading all research files is technically viable and produces the best recall. The decision boundary: is this session doing research-dependent work? If yes, load selectively; if no, skip.

A session_check.py extension could emit a one-liner: "Research corpus available: 24 files, ~36K tokens. Load all with `/load-research-corpus` or selectively via CLAUDE.md index."

---

## Unverified Claims (Flagged)

- **"46.9% token reduction"** from storing MCP tool descriptions as files: from a Tier 3 blog post about Cursor. Directionally plausible (matches Anthropic Layer 0 pattern) but magnitude unverified independently.
- **"0.2% of total tokens per skill"** in metadata mode: from Tier 3 source. Anthropic confirms metadata-only loading but provides no token percentage.
- **CompactPrompt 60% cost reduction** (arXiv:2510.18043, Oct 2025): single Tier 1 source, not yet independently replicated.
