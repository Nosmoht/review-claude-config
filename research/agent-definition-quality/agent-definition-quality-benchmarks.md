---
last_refreshed: 2026-04-06
---

# Agent Definition Quality Benchmarks

## Provenance Metadata

- **Strongest source tier:** Tier 1 (Anthropic official docs, KDD 2025 peer-reviewed survey)
- **Source basis:** KDD 2025 survey; ICLR 2026 Workshop paper; arXiv reliability framework; Anthropic Claude Code best practices
- **Last reviewed:** 2026-04-06

## Key Finding

No academic benchmark evaluates agent definition quality at design time — all existing benchmarks measure runtime performance. However, three converging research lines provide proxy evaluation dimensions for design-time review: (1) a KDD 2025 systematic survey confirms the absence of design-time benchmarks (arXiv:2507.21504); (2) psychometric decomposition via Item Response Theory (ICLR 2026 Workshop, arXiv:2604.00594) shows that definition quality and runtime performance are independent dimensions; (3) reliability research (arXiv:2602.16666) identifies implicit step dependencies as a root cause of execution order variance. Separately, Anthropic Tier 1 documentation establishes that the agent description is the sole activation signal for auto-dispatch, making description-body consistency a high-leverage design-time check.

## Evidence

### 1. No Design-Time Benchmark Exists

`[Proven result]`

The KDD 2025 survey "Evaluation and Benchmarking of LLM Agents" (arXiv:2507.21504, Proceedings of the 31st ACM SIGKDD) systematically covers agent evaluation across behavior, capabilities, reliability, and safety. It explicitly does not include benchmarks evaluating agent instruction or tool description quality at design time. All referenced frameworks (TaskBench, ToolBench, TheAgentCompany) assess downstream agent performance against predefined specifications, not the quality of the specifications themselves.

Adjacent fields in software engineering — requirements specification quality (IEEE 830, ISO/IEC/IEEE 29148), natural language ambiguity metrics, and requirements smell detection — address specification quality for human-authored documents but lack LLM-specific validation. They establish that the field of design-time specification quality is not novel conceptually, but no direct adaptation to LLM agent definitions has been benchmarked.

**Implication:** The agent evaluation checklist in this repo operates without direct benchmark grounding. Each new checklist item represents a proxy dimension informed by adjacent research, not a validated predictor of agent performance.

### 2. Definition Quality and Runtime Performance Are Independent

`[Engineering guidance]`

The paper "Agent Psychometrics" (arXiv:2604.00594, ICLR 2026 Workshop — note: workshop track, not main conference peer review) applies Item Response Theory (IRT) and generalizability theory to agent benchmark evaluation. Its LLM-Scaffold decomposition framework separates performance variation attributable to agent structure (definition quality) from variation attributable to runtime conditions (model capability, environment state).

Key finding: heterogeneous failure profiles — agents fail differently on different tasks for structural reasons rather than uniform capability limitations. A single overall score conceals this structure. IRT-derived task difficulty and agent ability coefficients can separate these effects in principle, though direct application to agent definition review has not been tested.

**Implication for review:** When scoring an agent, reviewers should distinguish definition defects (ambiguous instructions, missing constraints, weak trigger logic) from runtime capability limitations (model cannot perform the task). Conflating these leads to incorrect remediation: a definition defect needs a rewrite; a capability limitation needs a different model.

### 3. Implicit Step Dependencies Cause Execution Order Variance

`[Engineering guidance]`

"Towards a Science of AI Agent Reliability" (arXiv:2602.16666) proposes twelve reliability metrics across four dimensions: consistency, robustness, predictability, and safety. The prompt robustness metric (R_prompt) measures whether agents maintain consistent behavior under semantically equivalent instruction rephrasings.

The paper reports that agents "reliably select similar action types across runs but vary in execution order." This plan's interpretation: execution order variance is a signal of implicit step dependencies in the agent's instructions — if step A must run before step B but the dependency is unstated, a rephrase can reverse the order. This "what but not when" framing is **interpretive synthesis by this document**, not a direct term from the paper. The R_prompt finding itself is framework-level: the paper proposes the metric but does not benchmark design-time instruction quality remediation strategies.

Cross-validation: the Clarity rubric in this repo ("deterministic behavior across runs," "two models would sequence steps differently" as a B/C discriminator) captures the same phenomenon at the dimension-scoring level.

**Implication:** Checklists for agent Clarity should verify that step dependencies are stated explicitly when ordering matters. This is partially covered by existing rubric Clarity criteria.

### 4. Instruction Compliance Ceiling

`[Engineering guidance]`

ScaledIF (arXiv:2510.14842) and arXiv:2512.14754 establish that LLM instruction compliance degrades in the range of ~150-200 simultaneous instruction instances. These are model-level findings for large instruction sets, not per-section thresholds for agent bodies.

**Note on ID-1 proposal:** An earlier draft of this research proposed a ">10 constraints per section" threshold for agent bodies. This specific number has no benchmark support and would be a `[Repo default]` at best. The researched ceiling applies at the whole-agent or whole-prompt level, not per-section. The existing Constraint Load baseline entry ("Performance collapses beyond ~100 simultaneous instances") covers this finding at the appropriate granularity. Agents are typically short (under 200 instructions total), so the ceiling is rarely reached — but per-section density is a reasonable heuristic for structural decomposition.

### 5. Description as Sole Activation Signal

`[Proven result]`

Anthropic's Claude Code documentation (claude-code/skill-agent-format-conventions.md, code.claude.com/docs/en/best-practices) and "Writing Tools for Agents" (anthropic.com/engineering/writing-tools-for-agents) establish:

- The `description` frontmatter field is the sole signal used by Claude Code for auto-dispatch of agents
- "Small refinements to tool descriptions can yield dramatic improvements" — Claude Sonnet achieved SWE-bench state-of-the-art performance through precise description adjustments
- Trigger logic embedded only in the agent body is invisible to the auto-dispatch mechanism

**Implication:** Any mismatch between what the description says ("use this when X") and what the body says ("run this when Y") creates a dispatch confusion vector. This is a concrete, low-overlap design-time check.

### 6. Claude 4.6 Instruction Calibration

`[Engineering guidance]`

Anthropic Claude 4 Best Practices (April 2026) documents a behavior change: Claude 4.6 overtriggers on aggressive imperative language (MUST, CRITICAL, ALWAYS). The recommendation is to use natural phrasing ("use this tool when…") rather than imperatives. This is already captured in the engineering baseline under "Instruction Calibration." The agent-specific implication is that agent body instructions written for earlier Claude versions may need recalibration when deployed on Claude 4.6.

**Exception:** Safety-critical sections and guardrail instructions where strong language is intentional should be exempted from this check. Automatic FAIL on any MUST/CRITICAL usage would produce false positives.

## Limitations

1. **Novel heuristic system** `[Low-evidence area]` — The checklist items derived from this research (TC-3, DA-5, AP-4) form a novel proxy evaluation system. Individual items draw from the evidence above, but the composite claim "these three checks together improve agent review quality" is unvalidated. The system carries a `[Low-evidence area]` label at the system level until discrimination and false-positive validation produce positive results.

2. **Adjacent prior art not adapted** — Requirements engineering quality frameworks (IEEE 830, ISO/IEC/IEEE 29148, requirements smell detection) have decades of specification quality research. Direct adaptation to LLM agent definitions has not been attempted. The claim "no design-time benchmark exists" is accurate for LLM-specific benchmarks; it overstates novelty in the broader specification quality field.

3. **Single-source design-time application** — The R_prompt finding (arXiv:2602.16666) supports prompt robustness as a runtime metric. The design-time interpretation (implicit step dependencies cause the observed variance) is this document's synthesis. It is not directly validated.

4. **ICLR Workshop status** — arXiv:2604.00594 is from an ICLR 2026 Workshop, not the main conference. Workshop papers receive lighter peer review. The IRT decomposition idea is sound conceptually but should not be treated as main-conference validated.

## Cross-Validation Notes

- Evidence 1 (no benchmark) and Evidence 5 (description as sole signal) are independently confirmed: the KDD survey gap finding is peer-reviewed, and Anthropic's documentation is Tier 1 vendor guidance. These are the two strongest claims.
- Evidence 3 (R_prompt) partially cross-validates the existing Clarity rubric discriminator ("two models would sequence steps differently"). The rubric captures the same phenomenon at a coarser granularity.
- Evidence 4 (instruction ceiling) cross-validates the existing Constraint Load baseline entry. No new finding beyond what is already captured.
- Evidence 6 (Claude 4.6 calibration) cross-validates the existing Instruction Calibration baseline entry.

## Implications for Agent Definition Review

The research supports three non-redundant checklist additions:

1. **TC-3** — Verification criteria or success conditions: not covered by any existing checklist item; Anthropic best practices explicitly recommend it; high actionability.
2. **DA-5** — Description-body trigger consistency: not covered by existing DA-1 through DA-4 which check description quality but not description-body consistency; Proven result basis.
3. **AP-4** — Instruction language calibration: not directly covered by existing AP-1 through AP-3; Claude 4.6 specific; safety section exemption prevents Case 2 false positives.

Reviewers should additionally apply the definition-runtime separation principle: distinguish defects in the definition itself from limitations of the agent's model or environment.

## Source Register

### Tier 1

- KDD 2025 / ACM SIGKDD, "Evaluation and Benchmarking of LLM Agents: A Survey" (arXiv:2507.21504)
  https://arxiv.org/abs/2507.21504
- Anthropic, "Writing Tools for Agents"
  https://www.anthropic.com/engineering/writing-tools-for-agents
- Anthropic, Claude Code Best Practices
  https://code.claude.com/docs/en/best-practices
- Anthropic, Claude 4 Best Practices (April 2026) — internal citation in engineering-baseline.md

### Workshop / Preprint (Engineering guidance tier)

- "Agent Psychometrics" (arXiv:2604.00594, ICLR 2026 Workshop)
  https://arxiv.org/abs/2604.00594
- "Towards a Science of AI Agent Reliability" (arXiv:2602.16666)
  https://arxiv.org/abs/2602.16666
- ScaledIF (arXiv:2510.14842)
  https://arxiv.org/abs/2510.14842
- arXiv:2512.14754 (instruction following reliability)
  https://arxiv.org/abs/2512.14754

### Adjacent Prior Art (not directly applicable)

- IEEE 830: Recommended Practice for Software Requirements Specifications
- ISO/IEC/IEEE 29148: Systems and Software Engineering — Requirements Engineering
