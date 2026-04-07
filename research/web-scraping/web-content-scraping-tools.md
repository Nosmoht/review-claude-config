---
last_refreshed: 2026-04-07
---

# Web Content Scraping Tools for LLM Agents

**Sources:**
- [Jina Reader API](https://jina.ai/reader/) — URL-to-markdown/JSON conversion service (Tier 1)
- [ReaderLM-v2 product blog](https://jina.ai/news/readerlm-v2-frontier-small-language-model-for-html-to-markdown-and-json/) — Release notes, benchmarks, Jan 2025 (Tier 1)
- [Jina Reader GitHub](https://github.com/jina-ai/reader) — Canonical source with advanced headers (Tier 1)
- [Jina Reader MCP](https://github.com/jina-ai/MCP) — Official MCP server
- [Firecrawl](https://www.firecrawl.dev/) — Cloud web scraping API
- [Firecrawl MCP Server](https://github.com/firecrawl/firecrawl-mcp-server) — Official MCP server
- [Firecrawl Pricing](https://www.firecrawl.dev/pricing) — Credit-based tiers
- [Crawl4AI](https://github.com/unclecode/crawl4ai) — Open-source LLM-friendly crawler (50K+ GitHub stars)
- [Claude Code Web Tools Internals](https://quercle.dev/blog/claude-code-web-tools) — WebFetch summarizes via Haiku 3.5, never returns raw content
- [Exa vs Tavily vs Serper vs Brave — AN Score comparison](https://dev.to/supertrained/exa-vs-tavily-vs-serper-vs-brave-search-for-ai-agents-an-score-comparison-2l1g) — Tier 2 benchmark

**Fetched:** 2026-04-07

## Problem: WebSearch Snippet Limitations

WebSearch returns 2-3 line snippets per result. When skills use these to research domain best practices or update baselines, they lose:
- Full benchmark data and metrics
- Conditional guidance (e.g., "technique X works for Y but not Z")
- Code examples and configuration patterns
- Source verification — cannot read the actual article to assess credibility

## Integration Pattern: WebSearch-then-Fetch

Scraping does not replace WebSearch. It follows it in a two-step pattern:

1. **WebSearch** identifies relevant URLs and provides snippet-level context
2. **Fetch** the top 1-2 most promising URLs for full page content
3. **Distill** the full content into cache entries or baseline updates

This matches how humans research: search first, then read the best results.

## Tool Comparison

### Claude Code Built-in WebFetch (Recommended Default)

- Zero configuration — available immediately
- Content processed through Haiku 3.5 (summarized, not raw markdown)
- 100KB page size limit, no JavaScript execution
- Supports a `prompt` parameter to focus extraction (critical for token budget management)
- Sufficient for the WebSearch-then-Fetch pattern: targeted extraction of best practices from known URLs

### Jina Reader (Alternative for Raw Markdown or Structured JSON)

- Free tier: 10M tokens, 500 RPM — generous for skill usage
- Converts pages to clean, raw markdown via ReaderLM-v2 (1.5B parameter model, released Jan 2025)
- **New in ReaderLM-v2**: Direct HTML→JSON extraction via `x-json-schema` header (JSON schema) or `x-instruction` header (natural language) — eliminates intermediate Markdown conversion
- Benchmark: ROUGE-L 0.84 (main content), F1 0.81 (JSON extraction), 98% pass rate; outperforms Qwen2.5-32B, Gemini2-flash, GPT-4o on HTML-to-Markdown despite 20x smaller size
- Handles up to 512K combined input/output tokens, 29 languages
- Advanced headers: `x-token-budget: <N>` (cap output tokens on long pages), `x-engine: readerlm-v2` (3x token cost vs. default — use only when table/code/LaTeX fidelity matters or JSON schema output needed), CSS selectors for target/exclude, `x-javascript: true` for JS-rendered pages
- Two API modes: `r.jina.ai/<url>` (single page) and `s.jina.ai` (web search returning top 5 results with full extracted content per URL — 10,000-token minimum per query)
- Official MCP server: `npx @jina-ai/mcp@latest`
- Best choice when unprocessed markdown is needed (e.g., preserving code blocks, tables) or when structured JSON extraction from HTML is required

### Firecrawl (Alternative for Site Crawling)

- Cloud API with excellent markdown output
- Can crawl entire sites, map site structure, extract structured data
- Official MCP server: `npx firecrawl-mcp`
- Paid: $16+/mo after 500 lifetime free credits
- Best choice when crawling documentation sites (e.g., all of docs.anthropic.com)

### Crawl4AI (Self-Hosted Alternative)

- Open-source, self-hosted, free
- Good markdown output, site crawling, JavaScript rendering
- Community MCP servers only (quality varies across implementations)
- Requires local infrastructure — higher setup cost

## Search API Comparison for LLM Agents

When WebSearch (Claude built-in) is insufficient, external search APIs vary significantly. Three Tier-2 benchmarks (AN Score framework, Firecrawl blog, AIM Multiple) converge on the following directional rankings. Note: no Tier-1 academic benchmark exists for commercial search APIs — treat as directional guidance.

| API | AN Score | Best For | Content Return |
|-----|----------|----------|----------------|
| Exa | 8.7 | Semantic/conceptual research, technical docs | Full text via `contents` param (no separate fetch needed) |
| Tavily | 8.6 | Agent-native synthesis from multiple sources | Full text via `include_raw_content`; `search_depth: "advanced"` costs 2x |
| Serper | 8.0 | News/current events, Google index freshness | Snippets + structured JSON; separate fetch required for full content |
| Brave | 7.1 | Privacy-sensitive workloads (healthcare, legal) | Snippets + `extra_snippets`; independent index, no query logging |

**For this repo's use case** (technical documentation, arXiv papers, engineering blogs): **Exa** is the preferred option due to neural embedding retrieval that finds semantically related content keyword search misses. Exa returns extracted full text in the search response, saving a separate fetch round-trip. Use Tavily when synthesis across multiple sources is needed.

## Token Budget Impact

Scraping provides more input content but does not change output budgets:
- Domain cache entries: ≤500 tokens (richer source → better distilled bullets)
- Engineering baseline: ≤2K tokens (full articles → more nuanced technique descriptions)
- Analysis agent context: use WebFetch `prompt` parameter to constrain extraction to ~500 words

The key insight: better source material improves **distillation quality** without increasing **output size**.
