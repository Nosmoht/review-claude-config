---
last_refreshed: 2026-04-14
---

# Verification Methods for Non-Functional Quality Fixes

## Key Findings

**Verification is narrower than evaluation → lower variance.** CheckEval: decomposing into binary yes/no checks improves inter-model agreement by +0.45 across 12 evaluator models ([arXiv:2403.18771](https://arxiv.org/abs/2403.18771), EMNLP 2025).

**Anthropic's eval hierarchy:** deterministic graders > LLM-based graders > human graders. Use the cheapest tier that provides a reliable signal ([Anthropic: Demystifying Evals, 2026-01](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)).

**Same model CAN verify binary questions** — self-review problem applies to open-ended evaluation, not narrow binary verification (CheckEval evidence).

**Generate verification assertions at detection time** (~50 tokens per finding). Each finding produces 1-3 binary yes/no checks that can be evaluated independently.

## Three-Tier Architecture

| Tier | Method | Dimensions | Cost |
|------|--------|-----------|------|
| 1 — Deterministic | Regex, schema validation, grep, token count | Clarity (vague predicates), Safety (tool grants), Completeness (required sections), PE (example tags), CE (token count), Metadata (YAML) | Cheapest |
| 2 — LLM-Binary | 1-3 yes/no questions per finding | All dimensions when Tier 1 insufficient | Medium |
| 3 — Functional | Execute skill on eval case | Goal Alignment (weakest automated signal) | Expensive |

## Per-Dimension Verification

| Dimension | Tier 1 (Deterministic) | Tier 2 (LLM-Binary) |
|-----------|----------------------|---------------------|
| Clarity | Regex: `if needed`, `as appropriate`, `consider` | "Does this conditional have an observable test condition?" |
| Completeness | Grep for required sections, schema validation | "Does the artifact include [specific missing element]?" |
| PE | Count `<example>` tags, verify output template | "Do examples cover the ambiguous case cited?" |
| CE | Token count delta, JIT pattern check | "Is context loaded conditionally?" |
| Safety | Parse allowedTools, Tier-A combination check | "Is the justification adequate for [tool combo]?" |
| Metadata | YAML schema validation, description word count | Contrastive: description + 5 requests → activation accuracy |
| Goal Alignment | Weak automated signal | Tier 3 preferred: functional test |

## Sources

| Claim | Source | Tier |
|-------|--------|------|
| CheckEval +0.45 agreement | arXiv:2403.18771, EMNLP 2025 | 1 |
| Anthropic eval hierarchy | Anthropic engineering blog 2026-01 | 1 |
| LLM verification false negatives in broad scope | arXiv:2508.12358 | 1 |
| PBT 23-37% improvement | FSE 2025 | 1 |
| NLP conformance checking | TSE 2015 | 2 |
