---
last_refreshed: 2026-03-24
---

# Web Content Scraping Tools for LLM Agents

**Sources:**
- [Jina Reader API](https://jina.ai/reader/) — URL-to-markdown conversion service
- [Jina Reader MCP](https://github.com/jina-ai/MCP) — Official MCP server
- [Firecrawl](https://www.firecrawl.dev/) — Cloud web scraping API
- [Firecrawl MCP Server](https://github.com/firecrawl/firecrawl-mcp-server) — Official MCP server
- [Firecrawl Pricing](https://www.firecrawl.dev/pricing) — Credit-based tiers
- [Crawl4AI](https://github.com/unclecode/crawl4ai) — Open-source LLM-friendly crawler (50K+ GitHub stars)
- [Claude Code Web Tools Internals](https://quercle.dev/blog/claude-code-web-tools) — WebFetch summarizes via Haiku 3.5, never returns raw content

**Fetched:** 2026-03-24

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

### Jina Reader (Alternative for Raw Markdown)

- Free tier: 10M tokens, 100 RPM — generous for skill usage
- Converts pages to clean, raw markdown via ReaderLM-v2 (1.5B parameter model)
- Official MCP server: `npx @jina-ai/mcp@latest`
- Single-page only (no site crawling) — sufficient for URL follow-up
- Best choice when unprocessed markdown is needed (e.g., preserving code blocks, tables)

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

## Token Budget Impact

Scraping provides more input content but does not change output budgets:
- Domain cache entries: ≤500 tokens (richer source → better distilled bullets)
- Engineering baseline: ≤2K tokens (full articles → more nuanced technique descriptions)
- Analysis agent context: use WebFetch `prompt` parameter to constrain extraction to ~500 words

The key insight: better source material improves **distillation quality** without increasing **output size**.
