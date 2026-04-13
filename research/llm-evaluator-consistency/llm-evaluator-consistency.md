---
last_refreshed: 2026-04-14
---

# Reducing LLM Evaluation Variance

## Key Findings

**Behavioral rubrics are the highest-leverage intervention.** ICC3 improves from 0.560 to 0.819 (+46%) when using question-specific behavioral rubrics vs generic ones (ACM ICER 2025, [doi:10.1145/3702652.3744220](https://dl.acm.org/doi/10.1145/3702652.3744220)).

**Criteria decomposition into independent binary judgments** eliminates cross-dimension interference. RULERS compiles criteria into binary/ternary checklist items: QWK 0.7276 vs baselines 0.43-0.56 ([arXiv:2601.08654](https://arxiv.org/abs/2601.08654)).

**Majority voting (k=3-5)** accounts for most variance reduction gains typically attributed to multi-agent debate. Debate alone induces a martingale (no expected improvement) (ACL Findings 2025, [doi](https://aclanthology.org/2025.findings-acl.606.pdf)).

**Order randomization** improves Kappa from 0.639 to 0.807 ([Judge's Verdict](https://openreview.net/forum?id=jVyUlri4Rw)).

**Explanation-before-score ordering** is preferable to CoT for evaluation; CoT shows mixed evidence for straightforward tasks ([Arize AI](https://arize.com/blog/evidence-based-prompting-strategies-for-llm-as-a-judge-explanations-and-chain-of-thought/), confirmed by Tier 1 surveys).

**Graded reference examples** with RAG-based selection outperform random selection ([arXiv:2502.13337](https://arxiv.org/html/2502.13337)).

## Actionable Recommendations

1. Convert all rubric criteria from evaluative adjectives to observable behavioral checks (ICC3 +46%)
2. Evaluate each dimension in isolation to eliminate cross-dimension interference
3. Enforce explanation-before-score ordering in reviewer prompts
4. Add 1-2 graded reference examples per grade level per dimension
5. For borderline items, majority-vote scoring (k=3) is the most reliable second layer
6. Version-stamp rubric text to detect drift between sessions

## Sources

| Claim | Source | Tier |
|-------|--------|------|
| ICC3 0.560→0.819 with behavioral rubrics | ACM ICER 2025, doi:10.1145/3702652.3744220 | 1 |
| RULERS QWK 0.7276 | arXiv:2601.08654 | 1 |
| Majority voting > debate | ACL Findings 2025 | 1 |
| Kappa 0.639→0.807 with randomization | Judge's Verdict, OpenReview | 1 |
| G-Eval probability normalization | arXiv:2303.16634, NeurIPS 2023 | 1 |
| RAG-based example selection | arXiv:2502.13337 | 1 |
| LMSYS bootstrap aggregation | arXiv:2403.04132, ICLR 2025 | 1 |
