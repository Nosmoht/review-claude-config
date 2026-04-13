---
last_refreshed: 2026-04-14
---

# LLM Fix Completeness

## Key Findings

**LLM-based repair agents produce incomplete fixes in 10-16% of attempts.** SWE-Agent v1.0: 15.85% incomplete; AutoCodeRover v2.0: 10.61% incomplete ([arXiv:2411.10213](https://arxiv.org/abs/2411.10213)).

**LLMs cannot self-correct reasoning without external feedback.** Performance can degrade after intrinsic self-correction (Huang et al. [arXiv:2310.01798](https://arxiv.org/abs/2310.01798), ICLR 2024). Self-correction succeeds only with reliable external validation signals (Kamoi et al. TACL 2025, [arXiv:2406.01297](https://arxiv.org/abs/2406.01297)).

**DRV (Detect-Repair-Verify) with K=2 iterations** raises secure-and-correct yield from 0-54% (single pass) to 50-77% ([arXiv:2603.00897](https://arxiv.org/abs/2603.00897)).

**Per-finding tracking** raises resolution rates. Cursor BugBot: 52%→70% across 40 experiments ([Cursor blog](https://cursor.com/blog/building-bugbot)).

**Bounded iteration at K=2-3** captures most gains; later stages show diminishing returns (LLMLOOP, ICSME 2025).

## Actionable Recommendations

1. Decompose findings into individual tracked tasks (not batch)
2. Fix one finding at a time with verification between each (DRV pattern)
3. Use external verification signals, never self-assessment
4. Bound iteration at 2-3 attempts per finding; escalate to human if failing
5. Gate completion on all-findings-verified state

## Sources

| Claim | Source | Tier |
|-------|--------|------|
| 10-16% incomplete fix rate | arXiv:2411.10213 | 1 |
| Self-correction degrades without external feedback | Huang et al. arXiv:2310.01798, ICLR 2024 | 1 |
| Self-correction needs external validation | Kamoi et al. TACL 2025 | 1 |
| DRV K=2: 0-54%→50-77% | arXiv:2603.00897 | 1 |
| BugBot per-finding tracking 52%→70% | Cursor engineering blog | 2 |
| LLMLOOP diminishing returns | ICSME 2025 | 1 |
| SWE-bench+ score inflation 6-7% | arXiv:2410.06992 | 1 |
