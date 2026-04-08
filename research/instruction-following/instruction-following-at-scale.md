---
last_refreshed: 2026-04-08
---

# Instruction Following at Scale: Evidence-Based Thresholds

## Provenance Metadata

- Strongest source tier: Tier 1
- Source basis: arXiv:2505.16944 (AgentIF), arXiv:2507.11538 (IFScale/"How Many Instructions"), arXiv:2307.03172 (Lost in the Middle, TACL 2024), arXiv:2404.13208 (Instruction Hierarchy). Supplemental Tier 2 sources: HumanLayer engineering blog, dbreunig.com Claude Code system prompt analysis.
- Last reviewed: 2026-04-08

**Sources:**
- [AgentIF: Benchmarking Instruction Following of LLMs in Agentic Applications (arXiv:2505.16944)](https://keg.cs.tsinghua.edu.cn/persons/xubin/papers/AgentIF.pdf)
- [How Many Instructions Can LLMs Follow at Once? (arXiv:2507.11538)](https://arxiv.org/html/2507.11538v1)
- [IFScale Benchmark](https://distylai.github.io/IFScale/)
- [Lost in the Middle: How Language Models Use Long Contexts (arXiv:2307.03172, TACL 2024)](https://arxiv.org/abs/2307.03172)
- [The Instruction Hierarchy: Training LLMs to Prioritize Privileged Instructions (arXiv:2404.13208)](https://arxiv.org/html/2404.13208v1)
- [Writing a Good CLAUDE.md — HumanLayer Blog](https://www.humanlayer.dev/blog/writing-a-good-claude-md)
- [How Claude Code Builds a System Prompt — dbreunig.com](https://www.dbreunig.com/2026/04/04/how-claude-code-builds-a-system-prompt.html)
- [The Instruction Gap: LLMs get lost in Following Instruction (arXiv:2601.03269)](https://arxiv.org/html/2601.03269)

## Key Finding

Under realistic agentic instruction loads (avg 11.9 constraints, avg 1,723 words), the best available LLMs achieve fewer than 30% perfect Instruction Success Rate — even when Constraint Success Rate reaches ~60% (AgentIF, Tier 1). A separate benchmark (IFScale) confirms that frontier models sustain near-perfect performance only up to ~150 instructions before entering threshold or linear decay, and that Claude Code's base system prompt already consumes approximately 50 of those instruction slots before any user-authored rules or skills are applied.

## Evidence

### Instruction Success Rate Under Realistic Load

#### AgentIF Benchmark (50 Real-World Agentic Tasks)

**Source:** [AgentIF — arXiv:2505.16944](https://keg.cs.cs.tsinghua.edu.cn/persons/xubin/papers/AgentIF.pdf)

- Benchmark: 707 human-annotated instructions, 50 tasks from industrial and open-source agentic applications
- Average constraint count: **11.9 per instruction**; average instruction length: **1,723 words** (max: 15,630 words)
- Best model (o1-mini): **59.8% Constraint Success Rate (CSR)** but only **27.2% Instruction Success Rate (ISR)** — fewer than 30% of full instructions followed perfectly
- GPT-4o: drops from 87.0% on IFEval to **58.5% CSR** in AgentIF — a ~28-point degradation when moving to realistic agentic conditions
- Performance by instruction length:
  - Under 200 words: ~80% average success
  - 1,000–3,000 words: ~40% average success
  - Over 6,000 words: near 0% ISR across all models
- Performance by constraint type:
  - Formatting constraints: **87.0%** success (most robust)
  - Semantic constraints: **62.5%** success
  - Example constraints: **66.1%** success
  - Tool constraints: **45.7%** success
  - Condition constraints: **19.1%** success (most fragile — requires two-step inference: determine if condition is triggered, then apply constraint)
- ~25% of instructions include meta-constraints governing other constraints; 91.4% of meta-constraint instances are constraint-selection decisions
- Evaluation reliability: 94% agreement between GPT-4o automated evaluation and human manual assessment

#### Instruction Count vs. Adherence (IFScale, 20 State-of-the-Art Models)

**Source:** [How Many Instructions Can LLMs Follow at Once? — arXiv:2507.11538](https://arxiv.org/html/2507.11538v1)

- Benchmark tests 10–500 simultaneous instructions across 20 frontier models from 7 providers
- At maximum density (500 instructions): even the best frontier models achieve only **68% accuracy**
- Three distinct degradation patterns:
  1. **Threshold Decay** (reasoning models: o3, Gemini-2.5-Pro): near-perfect performance sustained through ~150+ instructions, then steeper decline with higher variance
  2. **Linear Decay** (mid-tier: GPT-4.1, Claude-3.7-Sonnet): steady, predictable accuracy loss from early density increases
  3. **Exponential Decay** (smaller models: Claude-3.5-Haiku, Llama-4-Scout): rapid drop after minimal instruction counts, plateauing at 7–15% accuracy floors
- At maximum density, error distribution shifts overwhelmingly to **omission-dominated failures** — some models show omission-to-modification ratios exceeding **34:1**, indicating complete instruction abandonment rather than degraded compliance

### Claude Code System Prompt Baseline Consumption

**Source:** [How Claude Code Builds a System Prompt — dbreunig.com](https://www.dbreunig.com/2026/04/04/how-claude-code-builds-a-system-prompt.html)

- Claude Code assembles its system prompt from **30+ conditional modular components**, plus ~50 separate tool definitions
- The base system prompt contains approximately **50 individual instructions** before any CLAUDE.md, rules, skills, or user messages are included
- Stacked layers added on top: CLAUDE.md/AGENT.md files, rules (injected as context), skills (injected at activation), conversation history, attachments
- Implication: if frontier models sustain reliable adherence up to ~150–200 instructions, Claude Code developers have roughly **100–150 instruction slots** remaining for CLAUDE.md + rules + skills combined

**Corroboration (Tier 2):** [HumanLayer Blog](https://www.humanlayer.dev/blog/writing-a-good-claude-md) independently cites the same ~150–200 frontier model ceiling and the ~50-instruction base consumption, recommending CLAUDE.md stay under 300 lines, with their own production CLAUDE.md at under 60 lines.

### Positional Effects: Lost in the Middle

**Source:** [Lost in the Middle — arXiv:2307.03172, TACL 2024](https://arxiv.org/abs/2307.03172)

- Performance is highest when relevant information appears at the **beginning or end** of context; performance degrades substantially when it sits in the middle
- Degradation can exceed **30%** when relevant information shifts from start/end positions to the middle of a long context
- Cause: RoPE positional encoding introduces attention decay that produces a U-shaped attention distribution
- Practical implication: rules buried in the middle of a stacked CLAUDE.md + rules + skills assembly are systematically less attended to, even if they appear within the model's nominal context window
- IFScale finding (corroborating): primacy bias peaks around **150–200 instructions**, then diminishes at extreme densities; at 500 instructions all models converge toward uniform failure regardless of position

### Instruction Hierarchy and Conflict Resolution

**Source:** [Instruction Hierarchy — arXiv:2404.13208](https://arxiv.org/html/2404.13208v1)

- Four-tier privilege model: System (developer) > User > In-context media > Tool outputs
- When lower-privileged instructions conflict with higher-privileged ones, models should ignore or refuse the lower-priority instruction
- Hierarchy-aware training achieved **63% improvement** in system prompt extraction defense and **30% improvement** in jailbreak robustness
- Relevant for Claude Code: CLAUDE.md occupies a developer-privilege position but skills and injected rules compete at the same level — no automatic priority ordering exists between them

### Condition and Conditional Constraints Are Highest-Risk

**Source:** AgentIF (arXiv:2505.16944)

- Condition constraints ("if X then do Y") achieve only **19.1% success** versus **66.8%** for the baseline "vanilla" constraint category
- Root cause: models must first determine whether the condition is triggered before applying the constraint — a two-step inference that fails frequently even when the underlying constraint logic is straightforward
- Over 30% of condition constraint errors stem from incorrect condition checking, not constraint non-compliance
- Implication for rules authoring: conditional rules ("NEVER do X when Y") are significantly more fragile than unconditional rules ("ALWAYS do X")

### Uniform Degradation Across All Instructions

**Source:** [HumanLayer Blog — Writing a Good CLAUDE.md](https://www.humanlayer.dev/blog/writing-a-good-claude-md)

- Adding more rules causes **uniform degradation across all rules**, not selective ignoring of newer ones
- This is distinct from a "last instruction wins" failure mode — the entire instruction set becomes less reliably followed as density increases
- Cross-validated against IFScale omission-dominated failure pattern: models shift to abandoning instructions uniformly rather than selectively

---

## Rubric Guidance

### Instruction Density Thresholds

Apply these thresholds when reviewing CLAUDE.md files, rules, and skill bodies for instruction overload risk. All thresholds are `Repo default` — derived from the research above but not empirically calibrated to this repo's specific model deployment.

| Scope | Threshold | Action |
|-------|-----------|--------|
| CLAUDE.md line count | > 300 lines | Warn; recommend pruning to universally applicable rules only |
| CLAUDE.md line count | > 500 lines | Flag as High finding; instruction density likely exceeds reliable adherence range |
| Constraint count per rule file | > 15 constraints | Warn; approaching AgentIF's avg 11.9-constraint zone where ISR drops to <30% |
| Total stacked instruction count (CLAUDE.md + all rules + all skills active simultaneously) | > 100 net new instructions above base ~50 | Warn |
| Total stacked instruction count | > 150 net new instructions above base ~50 | Flag as High finding; in exponential-decay territory for non-reasoning models |
| Instruction length (single rule or skill body) | > 1,000 words | Warn; AgentIF shows ~40% success at this length |
| Instruction length | > 6,000 words | Flag as High finding; near-zero ISR across all models |
| Conditional constraints ("if X then Y") as fraction of total | > 30% of rules | Warn; condition constraints fail at 19.1% — three times worse than formatting constraints |

**Penalty mapping:**
- **Completeness**: Penalize if a rule or skill omits its core intent because it is buried in overlong preamble or dense adjacent rules — a constraint that cannot be found is not complete.
- **Clarity**: Penalize if conditional constraints ("if/when/unless") exceed 30% of total rule body, or if a rule combines more than ~5 independent constraints without grouping — each compound condition multiplies failure probability.

### Robust Instruction Patterns

Based on cross-validated evidence from AgentIF (Tier 1), IFScale (Tier 1), and Lost in the Middle (Tier 1):

1. **Place critical rules at the beginning or end of CLAUDE.md, not the middle.** The U-shaped attention curve means the middle of a long stacked prompt receives systematically less attention. Reserve the middle for lower-stakes conventions.

2. **Prefer unconditional constraints over conditional ones.** "ALWAYS use scoped commits" (unconditional) has ~3.5× higher adherence than "when committing code, if the change touches multiple modules, use scoped commits" (conditional). AgentIF: 66.8% vs 19.1%.

3. **Use negative framing for safety-critical constraints.** "NEVER commit plaintext secrets" is more robust than "always encrypt secrets before committing." Negative constraints target specific failure modes and are harder to satisfy-away by generalization.

4. **Keep per-rule constraint count under 5–7.** Above ~12 constraints (AgentIF avg), ISR collapses toward 27%. Group related constraints under named headers rather than stacking them in a single block.

5. **Prefer unconditional meta-instructions sparingly.** Meta-constraints (constraints that govern other constraints) appear in 25% of AgentIF instructions and 91.4% of those are constraint-selection decisions — they add reasoning overhead and should be used only when truly necessary.

6. **Skills should be self-contained with minimal external rule dependencies.** If a skill relies on CLAUDE.md rules being followed simultaneously, the effective instruction count is additive — model must hold both instruction sets in working attention simultaneously.

7. **For reasoning models (Claude-3.5+), the ~150-instruction cliff is soft.** Reasoning models show threshold decay (near-perfect until ~150+ instructions) rather than immediate linear decay. Non-reasoning and smaller models degrade exponentially from low densities.

### Unverified Claims (Flagged)

- The exact token budget consumed by Claude Code's base system prompt is not disclosed by Anthropic. The ~50-instruction estimate from dbreunig.com is based on reverse-engineering analysis (Tier 2, single source). Treat as directionally correct but not a precise threshold.
- The "uniform degradation" claim from HumanLayer is not independently verified with a Tier 1 citation — IFScale's omission-dominated failure pattern partially corroborates it but tests a different task format. Flag as likely-true but unverified.
- Interaction effects between Claude Code's specific cache-boundary architecture (cacheable prefix vs session-specific suffix) and instruction adherence are not yet studied. Instructions injected post-cache-boundary may behave differently under load — this is an open question.
