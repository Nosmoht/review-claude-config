---
last_refreshed: 2026-04-14
---

# Evidence-Based Rubric Design for LLM Evaluators

## Key Findings

**Binary decomposition maximizes decision-level reliability.** Accuracy: 76% (binary) vs 57% (5-way); Kappa: 0.51 vs 0.34. "Partially Correct" middle category is the primary error cluster ([arXiv:2601.08843](https://arxiv.org/html/2601.08843)).

**Prometheus behavioral anchoring** achieves Pearson r=0.897 with human evaluators vs r=0.392 without ([arXiv:2310.08491](https://arxiv.org/abs/2310.08491), ICLR 2024).

**RULERS evidence-cap mechanism** (score mechanically capped if evidence count < m): QWK 0.7276 vs 0.2643 without calibration ([arXiv:2601.08654](https://arxiv.org/html/2601.08654)).

**0-5 scale is optimal for human-LLM alignment.** ICC=0.853; 0-100 gets ICC=0.840; 0-10 gets ICC=0.805 ([arXiv:2601.03444](https://arxiv.org/html/2601.03444v1)).

**LLM-hostile patterns:** subjective thresholds ("likely", "obvious"), counterfactual reasoning, implicit grade boundaries, compound multi-factor criteria.

**LLM-friendly patterns:** observable behavioral indicators, binary decomposition, extractive evidence requirements, deterministic scoring rules.

**Verdict-balanced examples** are critical — imbalanced examples cause systematic bias (Autorubric, [arXiv:2603.00077](https://arxiv.org/html/2603.00077v1)).

## Design Principles

| # | Principle | Evidence |
|---|-----------|----------|
| P1 | Decompose each dimension into 4-6 binary checklist items | Binary 76% acc vs 5-way 57% |
| P2 | Anchor each grade with observable behavioral descriptions | Prometheus r=0.897 vs 0.392 |
| P3 | Keep final scale at 5 points (A-F maps naturally) | ICC=0.853, best across scales |
| P4 | Require extractive evidence for each sub-score | RULERS QWK 0.7276 vs 0.2643 |
| P5 | Define B/C boundary with maximum precision | "Partially Correct" is primary error cluster |
| P6 | Eliminate subjective threshold language | Counterfactual reasoning is LLM-hostile |
| P7 | Use verdict-balanced examples at boundaries | Imbalanced → systematic bias |
| P8 | Aggregate binary sub-decisions deterministically | Holistic synthesis introduces variance |

## Sources

| Claim | Source | Tier |
|-------|--------|------|
| Binary 76% vs 5-way 57% | arXiv:2601.08843 | 1 |
| Prometheus r=0.897 | arXiv:2310.08491, ICLR 2024 | 1 |
| RULERS QWK 0.7276 | arXiv:2601.08654 | 1 |
| ICC=0.853 for 0-5 scale | arXiv:2601.03444 | 1 |
| Autorubric verdict-balanced | arXiv:2603.00077 | 1 |
| LLM-Rubric 2.2x RMSE improvement | arXiv:2501.00274 | 1 |
| Few-shot RAG > random | arXiv:2502.13337 | 1 |
