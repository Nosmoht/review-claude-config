---
name: source-quality-criteria
description: Shared source credibility criteria for all skills performing web research — discard rules, tier classification, cross-validation
---

# Source Quality Criteria

## Discard Rules (hard filter)

Reject any source that matches:
- Marketing content or product announcements without technical evidence
- Opinion pieces without data, benchmarks, or production metrics
- Tutorials or articles without primary sources or citations
- Sources older than 18 months (unless foundational/canonical)
- SEO-farm content (thin aggregation, no original analysis)

## Source Tiers (classification)

Tag each source used in domain research or cache entries:

- **Tier 1 — Authoritative**: Official vendor documentation, peer-reviewed papers (arXiv with citations, ACM, IEEE), RFCs/specs, CNCF/foundation docs
- **Tier 2 — Credible**: Documented production case studies, engineering blogs with benchmarks or metrics, conference talks with slides/recordings, industry reports with methodology
- **Tier 3 — Supplementary**: Blog posts without metrics, Stack Overflow answers, tutorials from known practitioners, community documentation

Prefer higher-tier sources when multiple sources cover the same topic.

## Cross-Validation Rule

Claims used in Goal Alignment scoring must meet one of:
- Appear in 2+ independent sources (any tier), OR
- Come from 1 Tier 1 source with concrete evidence (benchmarks, A/B tests, production metrics)

## Notes

- The "actionable" criterion (technique must be specific and implementable) applies to `refresh-engineering-baseline` only, not to domain research generally.
- Existing domain cache entries without `tier` fields are valid (grandfathered).
