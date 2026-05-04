---
name: description-disambiguation
description: Tool/skill selection accuracy under description contention; evidence base for META-3* rubric items in Metadata dimension
last_refreshed: 2026-04-29
---

# Description Disambiguation Under Skill Contention

## Definition

When 2+ tools/skills could plausibly match a user request based on their descriptions, the LLM dispatcher must select one. **Routing accuracy degrades sharply when descriptions overlap** — a robust empirical finding across the tool-routing literature. For Claude Code skill plugins, the activation signal is the skill's frontmatter `description:` field (officially confirmed by Anthropic). Description-collision is therefore a first-class Metadata-dimension failure mode.

## Tier-1 Evidence

### MetaTool — Tool Selection With Similar Choices

- **Source**: Huang et al. 2024. *MetaTool Benchmark for Large Language Models: Deciding Whether to Use Tools and Which to Use*. arXiv:2310.03128. ICLR 2024.
- **Method**: ToolE Dataset, 21,127 user queries; four subtasks including **tool selection with similar choices**. Embedding-similarity retrieval via Milvus vector store.
- **Headline metrics**:
  - **30% accuracy gap** between best (Vicuna-7b) and worst (Llama2-13b) LLMs on similar-tool selection under zero-shot prompts.
  - "Most LLMs struggle to effectively select tools" with similar choices — a robust failure mode.
- **Implication for skill artifacts**: descriptions must contain *discriminating* keywords. Two descriptions that share too many tokens routinely cause selection failures.

### ToolLLM / ToolBench — Neural API Retrieval

- **Source**: Qin et al. 2024. *ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs*. arXiv:2307.16789. ICLR 2024 spotlight.
- **Method**: 16,464 RESTful APIs across 49 categories. Neural API retriever (embedding-based) recommends APIs per instruction. ToolLLaMA model trained with depth-first decision-tree search (DFSDT).
- **Headline finding**: embedding-retrieval-based tool selection is the *standard primitive* for systems with >100 tools. Description quality directly affects retrieval recall@k.
- **Implication for skill artifacts**: at-scale (32+ skills), routing is governed by embedding-space distance, not literal token match. Descriptions must occupy distinct points in embedding space.

### Gorilla — Retriever-Aware Training

- **Source**: Patil et al. 2024. *Gorilla: Large Language Model Connected with Massive APIs*. arXiv:2305.15334. NeurIPS 2024 (workshop iteration; updated arXiv version).
- **Method**: APIBench (HuggingFace, TorchHub, TensorHub), retriever-aware training (RAT), AST tree matching evaluation. 1,600+ APIs.
- **Headline finding**: integrating a retriever during both training AND inference reduces hallucination on tool calls. Without retriever-quality, Gorilla baselines collapse to GPT-4-comparable hallucination.
- **Implication for skill artifacts**: even with strong models, weak description disambiguation degrades routing. Strong descriptions are a *first* line of defense, before retrieval-time reranking.

### Anthropic Skills — Confirmed Activation Primitive

- **Source**: Claude Help Center / Anthropic engineering posts (2026 Q1).
- **Quote (paraphrased from Claude Help Center)**: "A specific description tells Claude when to invoke your skill." Skills are model-invoked; the AI determines when each skill is needed based on context. December 2025 Agent Skills specification published as open standard.
- **Implication**: in Claude Code's specific runtime, the skill's frontmatter `description:` is the activation primitive. No public Anthropic detail on whether the dispatcher uses embedding similarity vs LLM-judge vs token match — but the literature establishes that the failure-mode (similar-description confusion) is robust across primitive choices.

## Comparison Table

| Source | Primitive | Headline metric | Best-fit for repo use-case |
|---|---|---|---|
| MetaTool (arXiv:2310.03128) | Embedding similarity | 30% gap on similar-choice subtask | **Justifies META-3c discriminating-keyword item** |
| ToolLLM/ToolBench (arXiv:2307.16789) | Embedding retriever | 16,464 APIs at-scale | Confirms embedding primitive at scale |
| Gorilla (arXiv:2305.15334) | Retrieval + AST eval | Reduces hallucination via retriever | Confirms retriever-quality dependency |
| Anthropic Help Center | "Specific description" | Confirmed activation primitive | Justifies that META-3* items target the right surface |

**Selection rationale**: MetaTool's "similar-choice" subtask is the most directly applicable axis. ToolLLM and Gorilla corroborate that the failure mode generalizes. Anthropic's confirmation that description is the activation primitive removes ambiguity about whether META-* items target the right field.

## Operationalized Item

### META-3c Discriminating-Keyword-Presence

**Iff-predicate (LLM-binary, with regex preflight)**

> Each skill's description contains ≥1 token (after stopword filter, length > 2) that does NOT appear in any sibling skill's description in the same plugin. Verification: compute `unique_tokens = own_tokens - union(sibling_tokens)`; PASS if `len(unique_tokens) >= 1`. **NA exemption**: if `find_sibling_skills(path)` returns empty (single-skill plugin), item is NA.

**Distinction from META-3b**: META-3b is a *bilateral negative* check (no sibling pair shares ≥2 tokens); META-3c is a *unilateral positive* check (each skill has ≥1 unique discriminator). A skill can pass META-3b (low pairwise overlap with each individual sibling) but fail META-3c (every token in own description appears in some sibling). They cover orthogonal failure modes.

**PASS examples**

- `review-skill` description contains `skill.md` token (no sibling description contains exactly `skill.md`).
- `audit-mcp-auth` contains `mcp`, `oauth`, `keychain` — all discriminators against other audit-* siblings.
- `scaffold-rule` contains `rule-template` — unique among scaffold-* family.

**FAIL examples (hypothetical)**

- A new skill with description "Evaluates Claude Code primitives across dimensions" — every meaningful token (`evaluates`, `claude`, `code`, `primitives`, `dimensions`) appears in at least one existing skill's description. No discriminator → FAIL.
- An adversarial `review-thing` skill whose description is verbatim a paraphrase of `review-skill` minus one filler word — high overlap, no unique token → FAIL.

Source: arXiv:2310.03128 (Huang et al. MetaTool, ICLR 2024 — 30% gap on similar-choice tool selection); cross-validation arXiv:2307.16789 (Qin et al. ToolLLM, ICLR 2024 spotlight — embedding retrieval as standard primitive); arXiv:2305.15334 (Patil et al. Gorilla — retriever-quality dependency).

## Self-Application Audit (2026-04-29)

Snapshot from `scripts/audit_description_collision.py 0.3`:

**Total skills audited**: 32

**META-3b PASS/FAIL/NA distribution (current threshold: shared >= 2 OR counter-reference)**:
- PASS via counter-reference: 29
- **FAIL: 3** — actual rubric violations in the current state:
  1. `skills/classify-trace-errors/SKILL.md` ↔ `skills/review-session-trace/SKILL.md` (5+ shared tokens, no counter-reference)
  2. `skills/review-session-trace/SKILL.md` (mirror of above — same pair)
  3. `skills/suggest-skills/SKILL.md` ↔ `skills/audit-repo/SKILL.md` (5+ shared tokens, no counter-reference)
- NA: 0

**Counter-reference regex coverage**: 24 / 32 skills carry the counter-reference pattern in their own description. The 8 skills without are: classify-trace-errors, review-session-trace, suggest-skills, run-eval-cases (rescued by sibling counter-ref), and four others.

**META-3c projection** (positive-discriminator check, manually inspected):
- All 32 skills carry a discriminating token in their description by inspection (e.g., `mcp`, `hook`, `oauth`, `frontmatter`, `rubric`, `policy`, etc. — domain-specific terms).
- Projected verdict: 32/32 PASS on META-3c.
- The check therefore acts as a *forward gate* — future skills with generic descriptions will be flagged.

**Action items from audit**:
- 2 follow-up issues opened (classify-trace-errors / review-session-trace / suggest-skills lack counter-references) — these are pre-existing META-3b violations now surfaced by the snapshot.
- META-3c added as preventive check.

## Cross-Validation Posture

Three Tier-1 sources (MetaTool ICLR 2024, ToolLLM ICLR 2024 spotlight, Gorilla 2024) plus Anthropic confirmation that description is the activation primitive. All peer-reviewed or vendor-authored. Passes web-research rule (≥2 Tier-1 sources, ≥1 Tier-1 corroboration).

## Pre-Existing Repo Coverage

META-3b sibling-distinguishability already addresses the *negative* axis (no excessive token overlap with siblings, rescued by counter-reference). MetaTool/ToolLLM evidence strengthens META-3b's source citation. META-3c adds the orthogonal *positive* axis (each skill has unique tokens) that prior rubric did not cover.

## References

- arXiv:2310.03128 — Huang et al., MetaTool (ICLR 2024)
- arXiv:2307.16789 — Qin et al., ToolLLM/ToolBench (ICLR 2024 spotlight)
- arXiv:2305.15334 — Patil et al., Gorilla
- https://support.claude.com/en/articles/12512180-use-skills-in-claude — Anthropic Skills activation primitive
- https://github.com/anthropics/skills — Public Skills repository (activation behavior reference)
- https://github.com/HowieHwong/MetaTool — MetaTool code
- https://github.com/OpenBMB/ToolBench — ToolBench code

## Repo Cross-References

- `scripts/rubric_binary_evaluator.py` L284-323, L633-664 — META-3b implementation, `META_3B_COUNTER_REFERENCE` regex, `STOPWORDS`, `tokenize_description`, `find_sibling_skills`, `has_sibling_counter_reference`
- `scripts/audit_description_collision.py` — one-off audit script using the above as a library
- `docs/audits/2026-04-29-description-collision-baseline.txt` — baseline snapshot from 2026-04-29
- `skills/review-claude-config/references/scoring-rubric.md` §"Trigger-Consistency" — rubric items live here
