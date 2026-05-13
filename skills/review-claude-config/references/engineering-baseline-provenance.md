---
name: engineering-baseline-provenance
description: Source provenance map for engineering-baseline.md — used by evidence-layer audits and baseline refresh, not loaded at runtime by review skills
last_refreshed: 2026-05-13
---

# Engineering Baseline Provenance

Maps each technique in `engineering-baseline.md` to its backing sources and tier classification.

**Consumers:** `/maintain-evidence-layer` (Step 6 tier compliance) and `/refresh-engineering-baseline` (source updates).
**Not loaded by:** runtime review skills (review-skill, review-agent, review-rule, review-hook, review-claude-md, review-claude-config).

## Prompt Engineering Techniques

| Technique | Evidence Class | Sources | Tier |
|-----------|---------------|---------|------|
| Structured Output | Proven result | Schulhoff et al. arXiv:2406.06608 | 1 |
| Role Priming | Engineering guidance | arXiv:2603.18507 (Sclar et al., PRISM — MMLU −5.3pp from long expert persona, length-controlled); arXiv:2311.10054v3 (Zheng et al., EMNLP 2024 Findings — 162 personas, small effects); arXiv:2512.05858 (Basil/Mollick, GPQA+MMLU-Pro) | 1 |
| Stepwise Decision Flow | Engineering guidance | (engineering practice — no primary benchmark) | — |
| Few-Shot Examples | Engineering guidance | arXiv:2509.13196 (7 models); Anthropic Claude 4 Best Practices, April 2026 | 1 |
| Constraint Specification | Proven result | Schulhoff et al. arXiv:2406.06608 | 1 |
| Verification Criteria | Engineering guidance | (engineering practice — no primary benchmark) | — |
| Feedback Loops | Engineering guidance | (engineering practice — no primary benchmark) | — |
| Evidence-First Critique | Engineering guidance | (engineering practice — no primary benchmark) | — |
| Constraint Load | Engineering guidance | arXiv:2603.22608; arXiv:2510.05381; ScaledIF arXiv:2510.14842; arXiv:2512.14754 | 1 |
| Deterministic Conditionals | Proven result | Schulhoff et al. arXiv:2406.06608 | 1 |
| Instruction Calibration | Engineering guidance | Anthropic Claude 4 Best Practices, April 2026 | 1 |
| Subagent Guardrails | Engineering guidance | Anthropic Claude 4 Best Practices, April 2026 | 1 |

## Context Engineering Techniques

| Technique | Evidence Class | Sources | Tier |
|-----------|---------------|---------|------|
| Context Budget | Proven result | Mei et al. arXiv:2507.13334; Anthropic, Effective Context Engineering (2025); Chroma 2025 Context Rot | 1/2 |
| Just-in-Time Retrieval | Engineering guidance | Anthropic, Effective Context Engineering (2025) | 1 |
| Subagent Isolation | Engineering guidance | Anthropic Agent SDK, 26-event hook system with deny>ask>allow priority | 1 |
| Reference File Separation | Engineering guidance | (engineering practice — no primary benchmark) | — |
| Tool Set Curation | Engineering guidance | Progent arXiv:2504.11703; MiniScope arXiv:2512.11147 | 1 |
| Activation Precision | Engineering guidance | Anthropic Claude Code / Agent SDK docs, April 2026 | 1 |
| Error Preservation | Engineering guidance | (engineering practice — no primary benchmark) | — |
| KV-Cache Friendliness | Engineering guidance | (engineering practice — no primary benchmark) | — |
| Confirmation Gates | Engineering guidance | (engineering practice — no primary benchmark) | — |
| Stop Conditions | Engineering guidance | Anthropic Planner-Generator-Evaluator pattern, March 2026 | 1 |
| Retry Ceilings | Repo default | (repo convention — no benchmark) | — |
| Idempotency Design | Engineering guidance | Fast.io, Google Cloud Vertex AI, Inngest (Tier 2 vendor case studies; no Tier 1 for LLM-agent retry rate claim) | 2 |
| Circuit Breaker Pattern | Engineering guidance | AWS Prescriptive Guidance; arXiv:2512.16856; arXiv:2512.09458 | 1 |
| Progressive Fallback | Engineering guidance | Fast.io, Maxim.ai (Tier 2/3 vendor guidance — treat as engineering practice, not benchmark-settled science) | 2/3 |
| Knowledge Gap Detection | Engineering guidance | (engineering practice — no primary benchmark) | — |
| Dynamic Tool Loadout | Low-evidence area | (heuristic — no primary benchmark) | — |
| Context Compression | Engineering guidance | ACON arXiv:2510.00615; Focus arXiv:2601.07190; Context-Folding arXiv:2510.11967 | 1 |
| Context Placement | Proven result | arXiv:2508.07479 (COLM 2025); arXiv:2510.10276; Chroma 2025 Context Rot | 1/2 |

## Tool Design Techniques

| Technique | Evidence Class | Sources | Tier |
|-----------|---------------|---------|------|
| Descriptions as Onboarding | Engineering guidance | Anthropic, Writing Tools for Agents (2025) | 1 |
| High-Signal Returns | Engineering guidance | Anthropic, Writing Tools for Agents (2025) | 1 |
| Meaningful Identifiers | Engineering guidance | (engineering practice — no primary benchmark) | — |
| Actionable Errors | Engineering guidance | (engineering practice — no primary benchmark) | — |
| Avoid Time-Sensitive Guidance | Engineering guidance | (engineering practice — no primary benchmark) | — |
| Poka-Yoke Tool Design | Engineering guidance | (engineering practice — no primary benchmark) | — |
| Typed Schemas | Engineering guidance | (engineering practice — no primary benchmark) | — |

## Full Source Register

**Anthropic (Tier 1):** Effective Context Engineering (2025); Writing Tools for Agents (2025); Building Effective Agents (2025); Claude 4 Best Practices (April 2026); Effective Harnesses for Long-Running Agents (March 2026); Agent SDK Hooks (April 2026); Claude Code Best Practices (2025).

**Research — arXiv (Tier 1):** Schulhoff et al. arXiv:2406.06608; Mei et al. arXiv:2507.13334; Qi et al. arXiv:2505.16944; arXiv:2603.18507 (Sclar PRISM); arXiv:2311.10054v3 (Zheng EMNLP 2024 Findings); arXiv:2512.05858 (Basil/Mollick); arXiv:2509.13196; arXiv:2511.20836; arXiv:2603.22608; arXiv:2510.05381; arXiv:2512.02246; arXiv:2510.00615; arXiv:2601.07190; arXiv:2510.11967; arXiv:2508.07479; arXiv:2510.10276; arXiv:2511.02230; arXiv:2512.11147; arXiv:2601.08012.

**Vendor (Tier 2/3):** Fast.io; Maxim.ai; AWS Prescriptive Guidance; Chroma 2025 Context Rot.

Full research details in `research/` files.
