---
name: dimension-evidence-coverage
description: Per-dimension Tier-1 evidence inventory + gap ranking for the 7-dimension Review Suite rubric
last_audited: 2026-04-29
---

# Dimension Evidence Coverage Matrix

Inventory of Tier-1 arXiv / peer-reviewed / foundation-lab sources backing each of the 7 review dimensions in `skills/review-claude-config/references/scoring-rubric.md`. Used to drive gap-driven evidence research instead of recency-biased ad-hoc paper hunting.

**Methodology**

1. **Tier-1 source** = arXiv preprint, peer-reviewed paper, RFC/spec, or foundation-lab publication (Anthropic / DeepMind / OpenAI / CNCF / OWASP). Cited inline in `scoring-rubric.md`, `engineering-baseline.md`, `skill-evaluation-guide.md`, or as a dedicated file in `research/`.
2. **Grounded rubric item** = a binary or narrative-grade-test item whose source is explicitly an arXiv ID, OWASP entry, or foundation-lab document.
3. **Coverage score** = (grounded items + 1) / (total scoring items + 1). Laplace-smoothed to avoid zero-divisor on empty dimensions; 0 - 1 scale.
4. **Known failure modes** = failure-modes plausibly present in reviewed artifacts (skills/agents/rules) and either (a) currently rubric-tested or (b) identified during this audit but not yet operationalized.

## Coverage Table

| Dimension | Weight | Tier-1 sources | Rubric items | Grounded items | Coverage score | Status |
|---|---|---|---|---|---|---|
| Clarity | 15% | 4 | 7 | 6 | 0.88 | Strong |
| Completeness | 15% | 5 | 5 | 5 | 1.00 | Strong |
| Prompt Engineering | 15% | 3 | 5 | 3 | 0.67 | Adequate |
| Context Engineering | 15% | 8+ | 5 | 5 | 1.00 | Strong |
| Goal Alignment | 20% | 2 | 2 | 2 | 1.00 (narrow) | **Narrow** |
| Safety | 10-15% | 10+ | 8 | 8 | 1.00 | Strong |
| Metadata | 5-10% | 0 arXiv (1 Anthropic) | 6 | 1 | 0.29 | **Weak** |

Score is high for several dimensions because few items exist, not because evidence is broad. The "Status" column reflects qualitative judgment about *coverage breadth* (how many failure-modes are addressed at all), not just *grounding depth* (how well existing items are sourced).

## Per-Dimension Detail

### 1. Clarity (15%)

**Tier-1 sources cited**

| ID | Source | Used in |
|---|---|---|
| arXiv:2306.08189 | Truong et al. — LLMs negation-insensitive | WS-5, baseline §Positive Framing |
| arXiv:2507.11525 | Ambiguity taxonomy (Gemma 3 12B F1=0.83) | Clarity grade-boundary block |
| arXiv:2512.14754 | IFEval++ reliable@k (61.8% accuracy drop) | Clarity grade-boundary block |
| arXiv:2503.13657 | MAST F7/F8 (silent recovery, dependency-skip) | CLAR-3, CLAR-4 |

**Grounded items:** WS-5, CLAR-1, CLAR-2, CLAR-3, CLAR-4, WS-2b. **Ungrounded:** WS-4 (pinned dim, LLM-interpretive only), RD-5b (formatting heuristic).

**Research files dedicated:** none. WS-5 and Truong currently live only in baseline + rubric.

**Identified gaps**

- Quantifier-scope ambiguity (Talmor oLMpics arXiv:1912.13283)
- Comparative / monotonicity reasoning (oLMpics, McCoy HANS arXiv:1902.01007)
- Presupposition / implicature handling
- Reference / pronoun resolution failures (Kassner & Schütze arXiv:1911.03343)
- Order-sensitivity of instructions

Tracked in #93.

### 2. Completeness (15%)

**Tier-1 sources cited**

| ID | Source | Used in |
|---|---|---|
| arXiv:2503.13657 | MAST F14 (unterminated reasoning) | RL-1b, COMP-W |
| arXiv:2603.29231 | MOP framework | COMP-W |
| arXiv:2505.16944 | AgentIF (ISR <30% at avg 11.9 constraints) | CE narrative (also Completeness-relevant) |
| arXiv:2507.11538 | IFScale (model taxonomy, density curves) | CE narrative |
| `research/llm-evaluator-consistency` | ICC3 +46% behavioral anchoring | COMP-X review-skill clause |

**Grounded items:** COMP-X, COMP-Y, COMP-Z, COMP-W, AH-2b. All grounded.

**Research files dedicated:** `instruction-following/`, `fix-completeness/` (2), `verification-methods/`, `structured-output-recovery-patterns.md`.

**Identified gaps**

- Constraint-type decomposition (FollowBench arXiv:2310.20410)
- Compound / logical-operator instructions (ComplexBench arXiv:2407.03978)
- Programmatic-verifiable instruction tests (IFEval arXiv:2311.07911)
- Missing-precondition detection from formal-verification literature (untapped)

Tracked in #96.

### 3. Prompt Engineering (15%)

**Tier-1 sources cited**

| ID | Source | Used in |
|---|---|---|
| arXiv:2306.08189 | Truong negation | WS-5, baseline §Positive Framing |
| Opus 4.7 sampling-param removal | Anthropic API spec | SAMP-1, SAMP-2 |
| `research/prompt-engineering/` synthesis | Few-shot, role priming, CoT studies | baseline §PE Techniques |

**Grounded items:** SAMP-1, SAMP-2, WS-5. **Ungrounded:** PE-1 (CoT scaffolding — Repo default), PE-2 (hedge — Repo default).

**Research files dedicated:** `research/prompt-engineering/prompt-engineering-techniques.md` (synthesis only — no single Tier-1 anchor).

**Identified gaps**

- Chain-of-Verification (Dhuliawala et al. arXiv:2309.11495)
- Self-Consistency (Wang et al. arXiv:2203.11171)
- Step-Back Prompting (Zheng et al. arXiv:2310.06117)
- Constitutional AI / principle-based prompting (Anthropic 2022)

Tracked in #97. Open question: are these *static-artifact* techniques or *runtime-orchestration* techniques?

### 4. Context Engineering (15%)

**Tier-1 sources cited**

| ID | Source | Used in |
|---|---|---|
| arXiv:2505.16944 | AgentIF density curves | CE narrative C-test |
| arXiv:2507.11538 | IFScale model taxonomy | CE model-taxonomy note |
| arXiv:2508.21433 | ACE compression pattern | baseline §Observation Masking |
| Liu et al. arXiv:2307.03172 | Lost-in-the-Middle | baseline §Context Placement (no dedicated research file) |
| (multiple) | Anthropic effective-CE, Manus lessons, KV-cache, JIT | baseline §CE Techniques |

**Grounded items:** all CE narrative tests + CE-X.

**Research files dedicated:** 8+ (`context-engineering/` 3 files, `instruction-following`, `token-efficiency`, `selective-context-injection`, `agent-knowledge-caching/` 3 files). Strongest single dimension.

**Identified gaps**

- Lost-in-the-Middle has no dedicated research file (only baseline mention) — tracked in #94. Consolidating Liu et al. as a standalone reference would close this.
- Position-bias under multi-agent dispatch (open research area)

### 5. Goal Alignment (20%)

**Tier-1 sources cited**

| ID | Source | Used in |
|---|---|---|
| arXiv:2512.12791v2 | Scenario S1 baseline (33% policy adherence) | GA-X checkpoint-decomposition |
| arXiv:2601.15153 | +206% lift via codified expert rules | GA-X checkpoint-decomposition |

**Grounded items:** GA-X. The narrative grade tests for A/B/D/F do not cite specific sources beyond the GA-X axis.

**Research files dedicated:** 0. `research/domain-knowledge/domain-knowledge-impact-on-quality.md` adjacent but framed around domain-cache justification, not Goal Alignment failure modes.

**Identified gaps (largest cluster in the suite)**

- **Sycophancy** — Sharma et al. 2023 (Anthropic, arXiv:2310.13548): models systematically agree with users even when wrong
- **Goal Misgeneralization** — Langosco et al. 2022, Shah et al. 2022 (DeepMind): agents pursue proxy goals correlated with training objective
- **Specification Gaming** — Krakovna et al. ongoing taxonomy: agents exploit reward function loopholes
- **Reward Hacking** in skill-context (analogue of overfitting to rubric items vs. underlying user goal)

Goal Alignment is the **highest-weighted dimension (20%)** with the **narrowest evidence base** (1 axis covered, 3+ failure-mode clusters absent). Tracked in #92.

### 6. Safety (10-15%)

**Tier-1 sources cited**

| ID | Source | Used in |
|---|---|---|
| arXiv:2503.13657 | MAST | R1-R11, RL-1b, RL-3b, RL-4b |
| arXiv:2508.14925 | MCPTox (72.8% tool-poisoning attack success) | Safety C-test |
| OWASP LLM01:2025 | Prompt Injection | IJ-1b |
| OWASP LLM05:2025 | Improper Output Handling | CLAR-3 |
| OWASP LLM06:2025 | Excessive Agency | SP-2b |
| OWASP LLM10:2025 | Unbounded Consumption / Data Leakage | RL-9b |
| OWASP ASI06/08/09 | Agentic Security Initiative | R4b, R9, R11 |
| Progent | Tool least-privilege (41-70% → 2-7% reduction) | SP-2b, baseline |

**Grounded items:** SP-2b, SP-4b, IJ-1b, RL-1b, RL-3b, RL-4b, RL-9b, R1-R11. All grounded.

**Research files dedicated:** 9 (tool-design, tool-least-privilege, autonomous-agent-reliability, multi-primitive-dependencies, hook-observation, injection-taxonomy, memory-poisoning, claude-code/auto-memory, claude-code/known-issues).

**Identified gaps**

- Empirical adversarial benchmarks: ToolEmu (arXiv:2309.15817), AgentDojo (arXiv:2406.13352), InjecAgent (arXiv:2403.02691) — tracked in #95
- Jailbreak-taxonomy (Wei 2023, Zou GCG 2023) — less applicable to skill-author surface; defer

### 7. Metadata (5-10%)

**Tier-1 sources cited**

| ID | Source | Used in |
|---|---|---|
| Anthropic Skills best-practices | Third-person warning block | META-4 |

No arXiv sources. Anthropic blog content is Tier-2 (vendor-authored). Six rubric items rely largely on common-sense routing patterns.

**Grounded items:** META-4 (and that only via Anthropic blog). META-1a/1b/2/3a/3b are Repo-default heuristics.

**Research files dedicated:** 2 (`agent-skills/anthropic-equipping-agents-with-skills.md`, `agent-definition-quality/agent-definition-quality-benchmarks.md`). Both Tier-2 (vendor / synthesis).

**Identified gaps**

- Description-collision under skill contention (no Tier-1 source identified — tracked in #98 with potential null-result outcome)
- Routing accuracy under sibling-keyword overlap
- Frontmatter field-staleness as a quality signal

Metadata is the **second-largest gap** behind Goal Alignment by Tier-1 evidence count.

## Gap Ranking (priority-ordered)

Ranking criteria: (a) dimension weight × (b) gap breadth × (c) operationalization tractability.

1. **Goal Alignment** — weight 20%, 3 uncovered clusters, well-cited literature exists. **Largest impact**, tracked in **#92**.
2. **Metadata** — weight 5-10%, but 5/6 items rely on Repo-default heuristics, and the dimension governs auto-dispatch reliability. Tracked in **#98**.
3. **Clarity (linguistic-cluster extension)** — weight 15%, methodology already proven via WS-5. Tracked in **#93**.
4. **Completeness (instruction-following benchmarks)** — weight 15%, well-grounded already; benchmark-decomposition is incremental. Tracked in **#96**.
5. **Safety (tool-misuse benchmarks)** — weight 10-15%, already strongest dimension; benchmarks add validation infrastructure but limited new failure-modes. Tracked in **#95**.
6. **Context Engineering (Lost-in-the-Middle research file)** — already cited in baseline; adding research file is housekeeping. Tracked in **#94**.
7. **Prompt Engineering (reasoning techniques)** — open question whether techniques apply at static-artifact authoring time. Tracked in **#97**.

## Maintenance

Per #99, this matrix is re-audited quartärly (90-day cadence, mirroring domain-cache rhythm). The `last_audited` field at the top of this document is the authoritative timestamp. Each per-dimension section's Tier-1 source list is the working set.

## Cross-References

- Source-quality classification rules: [source-quality-criteria.md](../skills/review-claude-config/references/source-quality-criteria.md)
- Evidence labels & maintenance: [evidence-maintenance.md](evidence-maintenance.md)
- Web-research workflow: `~/.claude/CLAUDE.md` rule "web-research"
- Tracking issues: #91 (this matrix), #92-#98 (per-dimension gap-fill), #99 (cadence)
