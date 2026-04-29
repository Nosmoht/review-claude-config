---
name: instruction-following-benchmark-comparison
description: Comparison of IFEval / FollowBench / ComplexBench for instruction-completeness evaluation; operationalization status for Completeness rubric
last_refreshed: 2026-04-29
---

# Instruction-Following Benchmarks: Comparison + Operationalization

Three Tier-1 instruction-following benchmarks back the Completeness dimension of the Review Suite. This file maps each benchmark's findings to artifact-level patterns and identifies which produce new rubric items vs. corroborate existing ones.

## Benchmarks

### IFEval — Verifiable-Instruction Approach

- **Source**: Zhou et al. 2023. *Instruction-Following Evaluation for Large Language Models*. arXiv:2311.07911. Google.
- **Method**: 25 verifiable instruction types, ~500 prompts. Programmatic verification (no LLM-judge bias).
- **Examples**: "write more than 400 words", "mention keyword X at least 3 times", "use only lowercase letters".
- **Key insight**: Instruction success can be made *programmatically verifiable* via specific format/length/keyword constraints — eliminating LLM-judge bias and human-evaluation cost.
- **Implication for skill artifacts**: Success criteria should be expressible as programmatic predicates (count thresholds, regex matches, exit codes, schema validation), not subjective judgments.

### FollowBench — Multi-Level Constraint Following

- **Source**: Jiang et al. 2024. *FollowBench: A Multi-level Fine-grained Constraints Following Benchmark for LLMs*. arXiv:2310.20410. ACL 2024.
- **Method**: 5 constraint types (Content, Situation, Style, Format, Example) × multi-level mechanism that incrementally adds constraints.
- **Key findings**: Condition constraints fail at 19.1% adherence vs 66.8% for formatting constraints (already cited in `scoring-rubric.md` §CE C-test). LLMs degrade unevenly across constraint types — formatting is the easiest, conditional logic is the hardest.
- **Implication for skill artifacts**: Skills that mix constraint types should not assume uniform agent compliance; condition constraints (`if X then Y`) carry the highest risk.

### ComplexBench — Constraint Composition

- **Source**: Wen et al. 2024. *Benchmarking Complex Instruction-Following with Multiple Constraints Composition*. arXiv:2407.03978. NeurIPS 2024 Datasets and Benchmarks Track.
- **Method**: 4 constraint types × 19 dimensions × 4 composition types (And, Chain, Selection — plus implicit composition). Hierarchical taxonomy.
- **Key findings**: Significant LLM deficiencies on multi-constraint composition. Composition type matters: Chain (sequential dependencies) and Selection (mutually-exclusive branches) are the highest-failure axes.
- **Implication for skill artifacts**: Skills with multiple instructions need to declare *how* the instructions compose. Without explicit composition markers, the agent may treat sequential steps as parallel, or treat exclusive branches as additive.

## Comparison Table

| Aspect | IFEval | FollowBench | ComplexBench |
|---|---|---|---|
| Year | 2023 | 2024 (ACL) | 2024 (NeurIPS) |
| Verification | Programmatic (regex, count) | LLM + rules | LLM + rules + composition dependency |
| Constraint coverage | 25 verifiable types | 5 types × multi-level | 4 types × 19 dims × 4 compositions |
| Bias | Minimal (programmatic) | Moderate (LLM-judge for some constraints) | Moderate (LLM-judge for semantic constraints) |
| Scope | Instruction-level | Instruction-level + density | Instruction-level + composition |
| Best fit for our review use-case | **Predicate verifiability of success criteria** | Already cited for CE density (line 41 of scoring-rubric.md) — no new item needed | **Composition clarity in multi-step skills** |

**Selection rationale**: IFEval and ComplexBench produce distinct, non-overlapping new rubric items. FollowBench's primary finding (condition vs format constraint adherence) is already operationalized in CE narrative §C-test.

## Operationalized Items

### COMP-V Verifiable-Predicate-Required (IFEval-derived)

**Iff-predicate**

> If the skill declares a success or completion criterion (`/(?:complete|success|done|valid|pass(?:es|ing)?)\s+when/i`) AND the criterion text within 200 chars contains NO programmatically-verifiable component (regex match, numeric threshold, exit-code reference, schema-match keyword) → Completeness capped at C.

**Verification components** (LLM-binary OR regex):
- Numeric threshold: `/\b\d+\b/`
- Regex match indicator: `/regex|matches?\s+\^|matches\s+pattern/i`
- Exit-code reference: `/exit(?:\s+code)?\s*[=:]?\s*0|exit(?:s)?\s+0|returns?\s+0|\bnon-?zero\b/i`
- Schema-match: `/schema|frontmatter|required\s+field|JSON\s+valid/i`
- Tool-output binding: `/`make\s+\w+`\s+(passes|succeeds|exits)|`\w+`\s+returns?/i`

**PASS examples**
- "Complete when `make validate` exits 0 AND token-budget check passes"
- "Success when verdict count equals 28 AND every High finding cites ≥1 verbatim quote"
- "Done when the file contains ≥3 `## Phase N` headings"

**FAIL examples**
- "Complete when the review is finished"
- "Success when the report looks good"
- "Done when all checks pass" (which checks? what does "pass" mean operationally?)

Source: IFEval arXiv:2311.07911 (25 verifiable instruction types, programmatic verification eliminates LLM-judge bias).

### COMP-Sel Selection-Composition (ComplexBench-derived)

**Iff-predicate**

> If the body contains ≥2 conditional branches that are mutually exclusive (only one should fire per invocation) AND the branches lack an explicit selection marker (`EITHER/OR`, `exactly one of`, `whichever applies`, `select one`) AND the agent could plausibly fire multiple branches simultaneously → Completeness capped at C.

**Verification** (LLM-binary):
1. Identify conditional groups (≥2 `if` clauses with parallel structure)
2. Determine if the conditions are mutually exclusive (e.g., "if file is empty" vs "if file has >100 lines")
3. Check for selection marker within the conditional group

**PASS examples**
- "Select exactly one: EITHER the file matches `*.skill.md` (treat as skill), OR `*.agent.md` (treat as agent), OR `*.rule.md` (treat as rule). If none match, abort."
- "Whichever applies first: (a) frontmatter `type:` is set → use it; (b) filename suffix matches → use it; (c) prompt user."

**FAIL examples**
- "If the file is a skill, do X. If the file is an agent, do Y. If the file is a rule, do Z." (no marker — agent may apply X and Y to a file that satisfies both heuristics)
- "If the user provided `--mode review`, run review. If the user provided `--mode audit`, run audit." (mutually exclusive flags, but no marker — what if both flags supplied?)

Source: ComplexBench arXiv:2407.03978 (Selection composition is high-failure-rate axis; explicit composition markers reduce ambiguity).

## Deferred / Already-Covered

### FollowBench condition-vs-format adherence asymmetry

Already cited in `scoring-rubric.md` line 41 as part of CE narrative C-test ("condition constraints fail at 19.1% vs 66.8% for formatting constraints"). The asymmetry is best-fit for CE density evaluation, not Completeness rubric. No new item.

### ComplexBench And/Chain composition

Chain (sequential dependencies) is already covered by WS-1 (numbered steps) and CLAR-4 (step-dependency-mitigation). And (parallel) is covered by WS-3 (parallel-vs-sequential marker). No new items needed for these compositions.

### IFEval 25 specific instruction types

Each individual IFEval instruction type (e.g., "use only lowercase", "mention keyword 3 times") is too narrow for a general rubric item. Operationalization is at the meta-level (require *some* programmatic predicate), not at the per-type level. The 25-type catalog is reference material, not a rubric expansion target.

## Self-Application Audit (2026-04-29)

Three skills sampled against COMP-V and COMP-Sel:

| Skill | COMP-V | COMP-Sel | Notes |
|---|---|---|---|
| `skills/review-skill/SKILL.md` | PASS — line 99-105 success criteria are explicitly programmatic ("verdict_count == expected_count", "the certificate table has exactly 7 dimension rows plus Overall", "every High/Medium finding has non-empty Evidence") | PASS — multi-perspective dispatch is Chain (sequential), explicitly numbered; standalone vs multi-perspective uses `--single-perspective` flag as explicit selection | All pass |
| `skills/audit-repo/SKILL.md` | PASS (after #100 fix) — completion criteria now require concrete numeric values per metric or explicit "N/A with cause" | NA — no mutually-exclusive branches at the orchestration level; phases run sequentially | Pass / NA |
| `skills/scaffold-skill/SKILL.md` | PASS — workflow steps include programmatic predicates (`Glob "<target-path>"`, `Glob "<target-path>/.git"`, kebab-case regex check, name-collision Glob) | PASS — mode branches (`plugin`/`maintenance`/`external`) are token-equality checks that cannot fire simultaneously; iff-predicate's "could plausibly fire multiple branches" condition does not hold | All pass |

**Result**: All three sampled skills pass COMP-V and COMP-Sel. As with #93's WS-6/7/8, the existing repo discipline already complies — new items are preventive going forward, caught at review-time for new artifacts.

## Cross-Validation Posture

All three benchmarks are peer-reviewed (Google research, ACL 2024, NeurIPS 2024 Datasets and Benchmarks Track) — all Tier-1. Cross-validation status:

- IFEval + ComplexBench corroborate each other on the value of structured/programmatic verification
- FollowBench corroborates the asymmetric-failure pattern across constraint types

Passes web-research rule (≥2 Tier-1 sources for the operationalized items: IFEval as primary for COMP-V, ComplexBench as primary for COMP-Sel; FollowBench corroborates both via shared paradigm of constraint decomposition).

## References

- arXiv:2311.07911 — Zhou et al., IFEval (Google 2023)
- arXiv:2310.20410 — Jiang et al., FollowBench (ACL 2024)
- arXiv:2407.03978 — Wen et al., ComplexBench (NeurIPS 2024 Datasets and Benchmarks Track)
- https://github.com/google-research/google-research/tree/master/instruction_following_eval — IFEval code+data
- https://github.com/YJiangcm/FollowBench — FollowBench code+data
- https://github.com/thu-coai/ComplexBench — ComplexBench code+data
