---
last_refreshed: 2026-04-14
---

# Cost-Efficient Selective Multi-Rating for LLM Evaluation

## Key Findings

**Trust or Escalate (ICLR 2025 Oral):** 82.5% of evaluations handled by cheap models, only 17.5% escalated to expensive model. 78.5% cost reduction with BETTER human agreement (80.2% vs GPT-4's 77.8%) ([arXiv:2407.18370](https://arxiv.org/abs/2407.18370)).

**PoLL:** Panel of 3 diverse models achieves higher correlation (kappa 0.763-0.906) than single GPT-4 (0.627-0.841) at 7x lower cost. Diversity of model families matters more than panel size ([arXiv:2404.18796](https://arxiv.org/abs/2404.18796)).

**Diminishing returns beyond k=3:** Only +2-5% agreement improvement for k=5. Most gains captured by k=3.

**Sample consistency is the most reliable uncertainty proxy** (ROC AUC 0.68-0.79), outperforming verbalized confidence and token probabilities (KDD 2025, [arXiv:2503.15850](https://arxiv.org/html/2503.15850v1)).

**Adaptive stopping** achieves identical ranking quality (Kendall's tau 0.73) with 32% fewer items and 42% less cost ([arXiv:2601.13885](https://arxiv.org/html/2601.13885)).

**FrugalGPT:** LLM cascade with trained scoring achieves up to 98% cost reduction matching GPT-4 accuracy ([arXiv:2305.05176](https://arxiv.org/abs/2305.05176)).

## Selective Multi-Rating Strategy

| Strategy | Calls (30 items) | Cost | Quality |
|----------|-----------------|------|---------|
| Always k=1 | 30 | 1.0x | Baseline |
| Selective k=3 | ~48 | 1.6x | Near-k=3 on borderline |
| Always k=3 | 90 | 3.0x | Full majority vote |

**Trigger criteria for escalation to k=3:**
1. Grade boundary proximity (within 2 points of B/C boundary)
2. High finding count with mixed severity (3+ findings, 1+ Medium)
3. Score inconsistency across dimensions (2+ grade-level spread)

**Expected distribution:** ~70% clear-cut (single), ~20% borderline (k=3), ~10% complex (k=3).

## Sources

| Claim | Source | Tier |
|-------|--------|------|
| Trust or Escalate 78.5% cost reduction | arXiv:2407.18370, ICLR 2025 Oral | 1 |
| PoLL kappa 0.763-0.906 | arXiv:2404.18796 | 1 |
| Sample consistency ROC AUC 0.68-0.79 | arXiv:2503.15850, KDD 2025 | 1 |
| Adaptive stopping 42% cost reduction | arXiv:2601.13885 | 1 |
| FrugalGPT 98% cost reduction | arXiv:2305.05176, TMLR 2024 | 1 |
