---
last_refreshed: 2026-04-14
---

# Binary-Reliable Checklist Items for LLM Evaluators

## Key Findings

**LLM evaluators achieve only 55.97% accuracy on "hard" rubric-level binary judgments** (RubricEval, [arXiv:2603.25133](https://arxiv.org/abs/2603.25133)). Items requiring abstract quality interpretation are the primary failure mode.

**IFEval programmatic verifiability** achieves perfect inter-rater reliability by restricting criteria to code-verifiable checks ([arXiv:2311.07911](https://arxiv.org/abs/2311.07911)). Before writing any LLM-judge item, ask: "Can a script verify this?"

**BARS (Behaviorally Anchored Rating Scales)** achieve kappa >0.80 by providing boundary examples at each level. Counterexample anchoring IS the operational definition, more than the text description.

**Single observable per item (unidimensionality)** is critical. Compound items force balancing competing assessments — primary source of inter-run variance (Autorubric, [arXiv:2603.00077](https://arxiv.org/html/2603.00077v1)).

**Gawande constraint (5-9 items):** WHO Surgical Safety Checklist and aviation checklists focus on "killer items" — highest error susceptibility + highest consequence. If an item rarely discriminates, remove or automate it.

**AutoChecklist pattern** separates human-readable labels from scoring prompts. Checklist table keeps short labels; evaluation prompt includes full text + boundary examples ([arXiv:2603.07019](https://arxiv.org/abs/2603.07019)).

## Design Principles

1. **Programmatic first:** Can a script verify it? → deterministic check, not LLM judgment
2. **Single observable:** Split compound items (look for "and", "yet", "but", dash-joined clauses)
3. **Counterexample anchoring:** BOUNDARY PASS + BOUNDARY FAIL per item
4. **Operational definition:** Replace abstract qualities with concrete observable tests
5. **Killer items only:** Cap 5-9 per dimension; remove non-discriminating items
6. **Separate label from scoring prompt:** AutoChecklist pattern for boundary examples

## Before/After Examples

| Item | Before | After |
|------|--------|-------|
| WS-2 | "Conditional branches have measurable criteria (not 'if needed')?" | "Every conditional specifies a concrete trigger — named value, threshold, file-system test, or tool output check?" BOUNDARY PASS: `if token_count > 500` / BOUNDARY FAIL: `if the response is too long` |
| DA-2 | "Description precise — narrow + broad enough?" | Split: DA-2a "Contains discriminating keyword not in unrelated requests?" + DA-2b "Covers all documented example triggers?" |
| CL-1 | "Two models would interpret this rule the same way?" | "Rule contains no term admitting two plausible opposite actions?" |

## Sources

| Claim | Source | Tier |
|-------|--------|------|
| 55.97% accuracy on hard binary | RubricEval arXiv:2603.25133 | 1 |
| IFEval programmatic reliability | arXiv:2311.07911 | 1 |
| BARS kappa >0.80 | Educational psychology foundational | 1 |
| Autorubric unidimensionality | arXiv:2603.00077 | 1 |
| AutoChecklist label separation | arXiv:2603.07019 | 1 |
| WHO checklist 5-9 items | Gawande, NEJM 2009 | 1 |
