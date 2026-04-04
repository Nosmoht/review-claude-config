---
last_refreshed: 2026-04-03
---

# Web Research Quality Evaluation

## Provenance Metadata

- Strongest source tier: Tier 1
- Source basis: Mixed sources - arXiv 2410.21360, Google quality guidelines, library-science evaluation guidance, Perplexity docs, and Semantic Scholar docs summarized in this file
- Last reviewed: 2026-04-03

How to evaluate and filter web research results by source credibility, with focus on automated approaches suitable for LLM agent workflows.

**Sources:**
- [CRAAP Test — Meriam Library, CSU Chico](https://researchguides.ben.edu/source-evaluation) (evaluation framework)
- [Google E-E-A-T Quality Rater Guidelines](https://developers.google.com/search/blog/2022/12/google-raters-guidelines-e-e-a-t) (quality evaluation)
- [arXiv 2410.21360: Automatic Credibility Assessment Survey](https://arxiv.org/abs/2410.21360) (175-paper LLM credibility survey)
- [Perplexity Sonar API — Academic Filter Guide](https://docs.perplexity.ai/guides/academic-filter-guide) (academic search mode)
- [Semantic Scholar Academic Graph API](https://www.semanticscholar.org/product/api) (200M papers, citation filtering)
- [Semantic Scholar MCP Server](https://github.com/zongmin-yu/semantic-scholar-fastmcp-mcp-server) (MCP integration)
- [Google Search Quality Rater Guidelines (Sept 2025)](https://guidelines.raterhub.com/searchqualityevaluatorguidelines.pdf) (full document)

**Fetched:** 2026-03-27

## Evaluation Frameworks

### CRAAP Test (Library Science)
Five dimensions: Currency, Relevance, Authority, Accuracy, Purpose. Designed for manual evaluation by researchers. Efficient but encourages surface evaluation — ignores actual claims in source ([Benedictine Univ Library](https://researchguides.ben.edu/source-evaluation)).

### Google E-E-A-T
Experience, Expertise, Authoritativeness, Trustworthiness. Trust is the most important dimension. Not a direct ranking factor but an evaluation methodology applied by human quality raters. Google's automated systems aim to identify content demonstrating these aspects ([Google Search Central](https://developers.google.com/search/blog/2022/12/google-raters-guidelines-e-e-a-t)).

### Automated Credibility Assessment (arXiv 2410.21360)
Comprehensive survey of 175 papers on textual credibility signals. Three key signal categories: (1) factuality, subjectivity, and bias, (2) persuasion techniques and logical fallacies, (3) check-worthy and fact-checked claims. BERT models achieved AUC 0.96-1.00 for various credibility criteria. LLMs show higher consistency in credibility assessment but are more susceptible to the decoy effect than humans ([arXiv](https://arxiv.org/abs/2410.21360)).

## Available APIs for Quality Filtering

### Perplexity Sonar API — Academic Mode
Set `search_mode: "academic"` to filter for scholarly/peer-reviewed content. Combinable with `search_domain_filter` for domain-level filtering. Known issue: `search_after_date_filter` is ignored in academic mode ([Perplexity Docs](https://docs.perplexity.ai/guides/academic-filter-guide)).

### Semantic Scholar API
Free access to 200M papers. Supports citation count filtering, year range, venue data, and "influential citation" detection via ML model. 1000 req/s without auth. MCP server available for Claude Code integration. Does not expose journal impact factors directly but provides citation metrics as proxy ([Semantic Scholar](https://www.semanticscholar.org/product/api)).

### Other Academic APIs
- **Scopus (Elsevier)**: Peer-reviewed metadata, citations, PlumX metrics. Requires API key.
- **Web of Science Lite (Clarivate)**: Peer-reviewed metadata. Requires API key.
- **Google Scholar API** (via Serply/similar): Academic search, citation counts, author data. Third-party wrappers.

## Research-Level Implication

The sources in this note support using explicit source filtering and transparent tiering when evaluating research quality. Project-specific policy decisions about external APIs or tooling should be made in repo-level interpretation, not in this summary.
