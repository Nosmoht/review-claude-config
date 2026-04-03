---
domain: research-sourcing
last_refreshed: 2026-04-02
queries:
  - "LLM citation bias web research quality 2025 academic"
  - "deep search agent source credibility evaluation 2025"
sources:
  - arXiv:2512.09483 (Source Coverage and Citation Bias in LLM-Based Search)
  - arXiv:2508.05668 (A Survey of Deep Search Agents)
---

# Research Sourcing — Domain Best Practices

## Source Coverage and Citation Bias (arXiv 2512.09483)
- LLM-based search does NOT outperform traditional search on source credibility
- LLMs show strong citation bias toward popular/high-traffic sources independent of factual accuracy
- Without explicit tier requirements in agent instructions, models mix Tier 1 and Tier 3 sources without flagging the difference
- Cross-validation requirement (2+ independent sources OR 1 Tier 1 with benchmarks) is the minimum standard to catch citation bias
- Marketing and SEO-optimized content is systematically over-represented in LLM search results vs. traditional search

## Deep Search Agent Survey (arXiv 2508.05668)
- Iterative retrieval (multiple targeted queries) outperforms single broad queries for research accuracy
- Source tiering must be encoded as hard constraints in agent instructions, not as soft preferences
- Agents without source quality gates produce outputs that are superficially plausible but factually inconsistent
- Verification step (checking source against official docs or primary data) should be mandatory for Tier 2 claims

## Tier Framework
See [source-quality-criteria.md](../source-quality-criteria.md) for canonical tier definitions and discard rules.
