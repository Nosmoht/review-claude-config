# LLM Agent Caching and Knowledge Persistence Patterns

**Sources:**
- [Letta: Is a Filesystem All You Need?](https://www.letta.com/blog/benchmarking-ai-agent-memory) — Agent memory benchmarks
- [Don't Do RAG: When CAG is All You Need (arXiv:2412.15605)](https://arxiv.org/abs/2412.15605) — Cache-Augmented Generation
- [Claude Code Memory Docs](https://code.claude.com/docs/en/memory) — File-based memory architecture
- [Anthropic: Effective Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — Structured note-taking, JIT retrieval
- [Anthropic: Prompt Caching Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) — KV-cache mechanics
- [Best Nested Data Format for LLMs](https://www.improvingagents.com/blog/best-nested-data-format/) — Format benchmarks
- [Token Optimization Strategies](https://www.glukhov.org/post/2025/11/cost-effective-llm-applications) — Bullet vs prose efficiency
- [When to Cache LLM Responses](https://particula.tech/blog/when-to-cache-llm-responses-decision-guide) — Invalidation strategies
- [Redis: What is Semantic Caching?](https://redis.io/blog/what-is-semantic-caching/) — Semantic cache tradeoffs
- [OpenAI: Harness Engineering](https://openai.com/index/harness-engineering/) — Doc-gardening agents, AGENTS.md

**Fetched:** 2026-03-24

## File-Based vs Graph/Vector Memory

Letta benchmark (LoCoMo): simple filesystem memory (74.0%) outperformed Mem0's graph-based system (68.5%). Agent capability with available tools matters more than retrieval mechanism sophistication. For bounded knowledge bases (<128K tokens), file-based storage with direct context loading is both simpler and more effective.

## CAG vs RAG for Bounded Knowledge

Cache-Augmented Generation preloads all relevant documents into context and caches the KV representation. Benchmarks (Llama 3.1 8B): CAG 0.827 vs RAG 0.819 BERTScore on SQuAD, with 40x latency reduction (2.33s vs 94.35s). CAG wins when knowledge fits in context window, updates infrequently, and low latency matters. RAG wins when knowledge exceeds context window or changes frequently.

## Token-Efficient Storage Formats

- **Markdown with YAML frontmatter:** 34-38% fewer tokens than JSON, best accuracy for 2 of 3 tested models (GPT-5 Nano, Gemini 2.5 Flash Lite)
- **Bullet points vs prose:** ~70% token reduction with identical output quality
- **TOON format:** 30-60% reduction vs JSON for tabular data, but Markdown sufficient for knowledge entries
- 40-70% of typical LLM context is wasted on formatting overhead — every token matters

## KV-Cache Optimization for Agents

Anthropic prompt caching requires 100% identical prefixes. Content cached in strict order: tools -> system -> messages. Key rules:
- Static content first (tool definitions, system instructions, reference material), dynamic content last
- Up to 4 cache breakpoints per request; minimum thresholds vary by model (1K-4K tokens)
- Cache reads cost 0.1x base input (90% savings)
- For multi-agent workflows: shared prefix (rubric, baseline) must be byte-identical across agents; per-item content (including cached domain knowledge) goes after the shared prefix

## Index + On-Demand Loading Pattern

Claude Code's memory: MEMORY.md index (200-line cap) with topic files loaded on-demand. 92% rule application rate under 200 lines vs 71% beyond 400 lines. The pattern: lightweight index for fast lookup, full content loaded via tool calls only when needed. This is Anthropic's "just-in-time retrieval" — maintain lightweight identifiers, dynamically load data via tools.

## Cache Invalidation Strategies

Ranked by reliability for LLM knowledge:
1. **Version-based** (primary): Include knowledge base version in cache keys; model updates automatically invalidate
2. **Event-driven** (selective): Emit invalidation when source data changes
3. **TTL as safety net** (fallback): Time-based expiration as secondary measure — never TTL alone

Recommended TTLs: knowledge base answers 12-48h, classification results 24-72h, structured extraction indefinite (hash-keyed). Domain best practices (slowly changing) suit 90-day TTL.

## Semantic Caching: When to Use

Semantic caching (GPTCache, Redis) converts queries to embeddings and uses cosine similarity (0.85-0.95 threshold) for fuzzy matching. Achieves 30-68% hit rates on repetitive workloads. However, it adds infrastructure complexity (vector DB, embedding model) that only pays off at scale (thousands of queries). For bounded domain knowledge with predictable keys, exact-match file lookup is simpler and equally effective.

## Production Patterns

- **OpenAI Harness:** AGENTS.md as context map (~100 lines), structured docs/ directory, doc-gardening agent for staleness detection
- **Claude Code Memory:** File hierarchy (managed -> project -> user -> rules), auto-memory with date-stamped lessons, 200-line cap enforced
- **Industry convergence:** Two-layer architecture — timeless knowledge in Markdown skill files, live connections via MCP servers. Cuts token costs ~100x vs bloated tool descriptions
