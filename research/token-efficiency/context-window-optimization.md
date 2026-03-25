# Context Window Optimization for AI Coding Assistants

Sources:
- [Context Rot: How Increasing Input Tokens Impacts LLM Performance](https://research.trychroma.com/context-rot) — Chroma Research study measuring degradation across 18 models
- [Effective Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — Anthropic's guide to context curation strategies
- [Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172) — Stanford/UC Berkeley research on positional retrieval accuracy (Liu et al., 2023)
- [Code to Tokens Conversion: A Developer's Guide](https://prompt.16x.engineer/blog/code-to-tokens-conversion) — Token density measurements by programming language
- [Which Programming Languages Are Most Token-Efficient?](https://martinalderson.com/posts/which-programming-languages-are-most-token-efficient/) — Rosetta Code analysis across 19 languages using GPT-4 tokenizer
- [Token-Efficient Programming Languages: Rankings and Insights](https://ubos.tech/news/token%E2%80%91efficient-programming-languages-rankings-and-insights/) — Language efficiency rankings and methodology
- [How I Cut My AI Coding Agent's Token Usage by 120x With a Code Knowledge Graph](https://dev.to/deusdata/how-i-cut-my-ai-coding-agents-token-usage-by-120x-with-a-code-knowledge-graph-4a3d) — Knowledge graph approach to navigation cost reduction
- [How Long Contexts Fail](https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html) — Taxonomy of context failure modes (poisoning, distraction, confusion, clash)
- [How to Fix Your Context](https://www.dbreunig.com/2025/06/26/how-to-fix-your-context.html) — Remediation strategies for context failure modes
- [Context Dilution: When More Tokens Hurt AI](https://diffray.ai/blog/context-dilution/) — Empirical data on accuracy degradation with token count
- [Claude Code Pricing: Optimize Your Token Usage & Costs](https://claudefa.st/blog/guide/development/usage-optimization) — Real-world token consumption by task type
- [Claude Code Token Limits: A Guide for Engineering Leaders](https://www.faros.ai/blog/claude-code-token-limits) — Token budget planning data

Fetched: 2026-03-26

## Context Rot

Context windows have a nominal capacity (e.g., 200K tokens) but effective capacity is significantly lower. Key findings:

**Chroma Research (2025):** Evaluated 18 state-of-the-art models (GPT-4.1, Claude 4, Gemini 2.5, Qwen3) and found performance degrades well before the window fills. A model with a 200K window can exhibit significant degradation at 50K tokens. Factors compounding rot include needle-question similarity, distractor presence, haystack structure, and semantic relationships.

**Lost-in-the-Middle (Liu et al., 2023):** LLMs exhibit a U-shaped attention curve -- strong retrieval at the start and end, 30%+ accuracy drop for information in the middle. Measured across GPT-3.5-Turbo, Claude, and other production models. This is a fundamental architectural property of transformer attention.

**Effective capacity rule of thumb:** 60-70% of nominal window size before meaningful degradation begins. At 100K tokens the model processes 10 billion pairwise attention relationships (n-squared scaling), creating computational pressure that reduces precision for retrieval and long-range reasoning.

**Anthropic's guidance:** Find "the smallest possible set of high-signal tokens that maximize the likelihood of some desired outcome." Context engineering is iterative curation, not one-time prompt design.

## Token Density by Language

Token counts per line of code vary by language syntax, keyword length, and tokenizer training distribution. Measurements using GPT-4/Claude tokenizers:

| Language | Tokens/Line | Tokens/100 Lines | Notes |
|----------|-------------|-------------------|-------|
| Python | ~10 | ~1,000 | Clean syntax, minimal punctuation |
| JavaScript | ~7 | ~700 | Shorter keywords, but verbose at task level (148 tokens/task in Rosetta study) |
| TypeScript | ~8-10 | ~800-1,000 | Type annotations add density over JS |
| Rust | ~12-15 | ~1,200-1,500 | Lifetime annotations, trait bounds, explicit types |
| C/C++ | ~12-15 | ~1,200-1,500 | Header includes, pointer syntax, verbose error handling; C measured at 182 tokens/task (2.6x worst vs best) |
| SQL | ~11-12 | ~1,150 | Verbose keywords (SELECT, FROM, WHERE) |
| Go | ~8-10 | ~800-1,000 | Compact syntax, but explicit error handling adds lines |

**Most token-efficient languages** (Rosetta Code study, 19 languages): J (70 tokens/task), Clojure (109), Haskell (115), F# (118). These achieve compile-time guarantees or array-oriented brevity with minimal token overhead.

**Practical implication:** A 200K context window holds roughly 20,000 lines of Python but only 13,000-16,000 lines of Rust/C++. Language choice directly affects how much code an agent can reason about simultaneously.

## Navigation Cost

Codebase exploration is the dominant token consumer in AI coding sessions. An agent answering "what calls ProcessOrder?" performs:

**Typical exploration breakdown (45K-60K tokens):**
- Grep/search across files: ~15,000 tokens (directory listings, search results, file paths)
- Reading matched files for context: ~25,000 tokens (full file contents, surrounding code)
- Following imports and indirect callers: ~15,000-20,000 tokens (transitive dependency chains)

A single exploration question on a mid-size project triggers 10-20 tool calls before the agent begins answering. Each tool call adds request overhead (tool schemas, conversation history replay).

**Knowledge graph optimization:** Pre-parsing the codebase into a persistent graph of functions, classes, call chains, and imports reduces the same query from 45,000 tokens to ~200 tokens -- a 99.2% reduction. Structured summaries injected into prompts cost ~4,000 tokens with ~150ms latency.

**Implication for skill design:** Skills that provide pre-computed structural context (file maps, dependency graphs, API summaries) dramatically reduce per-task token burn. A well-designed CLAUDE.md file listing key entry points prevents repeated exploration.

## Context Failure Modes

Four distinct failure modes identified in research (Breunig, 2025):

**Context Poisoning:** A hallucination or error enters the context and gets repeatedly referenced in subsequent turns. Because agents reuse and build upon context, errors compound. Particularly dangerous in multi-turn coding sessions where an incorrect assumption about an API propagates through generated code.

**Context Distraction:** The context grows so large the model over-focuses on conversation history rather than applying its training. The model repeats past patterns instead of reasoning fresh. Databricks research found model correctness begins falling around 32K tokens for Llama 3.1 405B, and earlier for smaller models.

**Context Confusion:** Irrelevant tools, documents, or instructions crowd the context, causing the model to use the wrong tool or follow the wrong instructions. Each additional tool definition occupies tokens and creates potential for misapplication.

**Context Clash:** Accumulated information contradicts other information in the prompt. New instructions conflict with earlier ones. The model must resolve contradictions, often unpredictably. Common when system prompts evolve but conversation history retains outdated guidance.

## Build Error Verbosity

Build and compiler error output consumes context tokens and varies dramatically by toolchain:

| Toolchain | Error Style | Approx. Tokens/Error | Notes |
|-----------|-------------|----------------------|-------|
| Go | Compact single-line | 50-150 | `file.go:12:5: undefined: foo` -- minimal, structured, machine-parseable |
| TypeScript (tsc) | Medium multi-line | 200-500 | Type mismatch errors include expected/actual types, sometimes with chain |
| Rust (rustc) | Verbose but structured | 300-800 | Includes suggestions, help text, ASCII art spans; educational but costly |
| Webpack | Extreme, unstructured | 1,000-5,000+ | Stack traces, loader chains, module resolution paths, often duplicated across chunks |
| ESLint/Prettier | Medium, repetitive | 100-300 per violation | Multiplied across hundreds of files in CI output |

**Impact:** A Webpack build failure can dump 10,000+ tokens of error output into context. Go's compact errors leave budget for actual problem-solving. Truncating or summarizing build output before injecting it into context is a high-value optimization.

## Heuristic Consumption by Task Type

Approximate token consumption for common AI coding assistant tasks (based on Claude Code usage data):

| Task Type | Input Tokens | Output Tokens | Total Budget |
|-----------|-------------|---------------|-------------|
| Simple edit (typo, rename, add log line) | 5,000-20,000 | 1,000-3,000 | 6K-23K |
| Targeted bug fix (known location) | 15,000-40,000 | 3,000-8,000 | 18K-48K |
| Codebase exploration / understanding | 40,000-80,000 | 5,000-10,000 | 45K-90K |
| Multi-file refactor (rename API, update callers) | 50,000-100,000 | 10,000-20,000 | 60K-120K |
| Full feature implementation (DB + API + UI) | 100,000-200,000 | 30,000-50,000 | 130K-250K |
| Large investigation + fix (unknown root cause) | 150,000-300,000 | 10,000-30,000 | 160K-330K |

**Key observations:**
- Exploration dominates input tokens; generation dominates output tokens
- Plan mode reduces total consumption by 40-60% by separating thinking from execution
- Context compaction (summarizing conversation history) is critical for tasks exceeding 100K tokens
- A productive full-time developer typically consumes $5-15/day on API pricing
