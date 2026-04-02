---
domain: research-sourcing
last_refreshed: 2026-04-02
queries:
  - "LLM citation bias web research quality 2025 academic"
  - "deep search agent source credibility evaluation 2025"
  - "source quality tiering AI agent research academic"
sources:
  - url: https://arxiv.org/abs/2512.09483
    title: "Source Coverage and Citation Bias in LLM-Based Search — arXiv 2512.09483"
  - url: https://arxiv.org/abs/2508.05668
    title: "A Survey of Deep Search Agents — arXiv 2508.05668"
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

## Tier Framework (from engineering baseline + papers)
- Tier 1 (require for factual claims): Official vendor docs, peer-reviewed papers (arXiv/ACM/IEEE), RFCs, foundation docs (CNCF/OWASP)
- Tier 2 (acceptable with corroboration): Production case studies with metrics, engineering blogs with benchmarks, conference talks
- Tier 3 (flag explicitly, do not treat as authoritative): Tutorials, blog posts, Stack Overflow answers
- Discard without exception: marketing content, opinion without evidence, sources >18 months old (unless foundational), SEO-farm content without original analysis
