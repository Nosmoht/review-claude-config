---
last_refreshed: 2026-04-19
---

# Change Discipline Workflow Research

Research supporting the global change discipline rule for Claude Code sessions.

## Key Findings

### 1. Proportional review processes outperform uniform ceremony

Requiring uniform high-ceremony review for all changes causes costs to exceed benefits for low-risk changes. Google's 9-million-review study found that knowledge transfer — not defect detection — drives most code-review ROI. Separately, a large-scale PR analysis (cited via Augment Code) found PRs under 400 LOC capture 66-75% of defects at 200 LOC/hour; oversized PRs drop below 50% detection rates. (These are distinct studies; the LOC metrics do not originate from the Google study.)

Agentic workflow research recommends SIMPLE/COMPLEX classification to scale ceremony proportionally: simple changes plan all tasks upfront; complex changes plan one task at a time.

**Implication for rule:** Tiered approach — trivial changes use a shortened sequence; behavior-altering changes use the full sequence.

Sources:
- [Code Review Best Practices That Actually Scale](https://www.augmentcode.com/guides/code-review-best-practices-that-scale) — Augment Code, citing Google, Microsoft Research, Meta studies
- [The Three Developer Loops](https://itrevolution.com/articles/the-three-developer-loops-a-new-framework-for-ai-assisted-coding/) — Gene Kim, Steve Yegge (IT Revolution)
- [Designing Agentic Workflows: The Core Loop](https://dev.to/danielbutlerirl/designing-agentic-workflows-the-core-loop-166d) — Daniel Butler

### 2. AI-assisted development requires independent verification

Teams using AI assistants without quality guardrails report a 35-40% increase in bug density within 6 months. AI output should be treated as suggestions that must pass quality gates before entering the codebase.

Key practices from multiple sources converge:
- Run tests independently — never trust AI self-reports of "tests passing" (Kim/Yegge)
- Commit frequently as save points enabling quick rollback — 4x traditional frequency (Kim/Yegge)
- Treat AI output like work from a junior developer (Osmani)
- Gates must be independently verifiable — invalid gates rely on agent judgment like "looks correct" (Butler)

**Implication for rule:** Verification step is mandatory. "Verify" means independently confirm, not accept AI self-assessment.

Sources:
- [My LLM Coding Workflow Going into 2026](https://addyosmani.com/blog/ai-coding-workflow/) — Addy Osmani
- [The Three Developer Loops](https://itrevolution.com/articles/the-three-developer-loops-a-new-framework-for-ai-assisted-coding/) — Gene Kim, Steve Yegge
- [AI Code Quality Guide 2026](https://codeintelligently.com/blog/ai-code-quality-guide-2026) — CodeIntelligently

### 3. Multi-perspective review reduces LLM self-review blindspots

LLMs overemphasize technical validity in reviews and systematically underweight other dimensions (F1=0.126 for novelty/originality weakness detection). Self-review by the same model has inherent blindspots — the reasoning that produced a bug is unlikely to catch it.

Mitigations:
- Multi-lens assessment: security, quality, architecture perspectives (Salesforce Prizm)
- Cross-model reviews: one model writes, another critiques (Osmani)
- Complementary human+LLM review: LLMs for systematic validity, humans for nuanced judgment (arxiv:2502.17086 — note: this paper studies LLMs reviewing academic papers; the blind-spot pattern is directionally relevant to code/config review but domain transfer is unvalidated)
- Adversarial, user-perspective, and security-focused review perspectives reduce blindspots

**Implication for rule:** Review step should mandate different perspectives, especially in autonomous mode where human review is absent.

Sources:
- [Mind the Blind Spots: A Focus-Level Evaluation Framework for LLM Reviews](https://arxiv.org/abs/2502.17086) — academic paper (2025)
- [Scaling Code Reviews: AI-Generated Code](https://engineering.salesforce.com/scaling-code-reviews-adapting-to-a-surge-in-ai-generated-code/) — Salesforce Engineering
- [My LLM Coding Workflow Going into 2026](https://addyosmani.com/blog/ai-coding-workflow/) — Addy Osmani

### 4. Agentic workflows need explicit failure mode constraints

Six identified failure modes for agentic workflows, each requiring a specific constraint:

| Failure Mode | Constraint Mechanism |
|---|---|
| Shortcuts / half-assing | Project rules enforcing sequence |
| Premature completion claims | Independent gate verification |
| Review fatigue | Commit-sized tasks limit scope |
| Decision delegation to AI | Human-controlled commit gate |
| Knowledge loss across sessions | Implementation notes in repository |
| Quality residue | Cleanup/review step catches accumulated issues |

Sessions should be disposable; all durable state belongs in the repository.

**Implication for rule:** The rule itself is the "project rules" constraint. Verification must be independent. State must be in repo, not in session memory.

Source:
- [Designing Agentic Workflows: The Core Loop](https://dev.to/danielbutlerirl/designing-agentic-workflows-the-core-loop-166d) — Daniel Butler

### 5. Verification means different things in different contexts

For code: run test suites, check for regressions, validate behavior.
For non-code (skills, agents, rules, config, docs): inspect output, check cross-references, validate syntax, verify correctness by re-reading.

The obligation is "confirm the change works as intended" — the method scales to what the project offers.

**Implication for rule:** Use "Verify" not "Test" as the step name. Define verification broadly with context-specific examples.

Sources:
- Synthesized from Osmani (test after every task), Kim/Yegge (independent verification), Butler (independently verifiable gates)

## Evidence Gaps

- No quantitative studies on optimal number of review perspectives for LLM self-review
- "35-40% bug density increase" claim from AI Code Quality Guide 2026 — Tier 3 source (consultant blog, anecdotal "I've seen this across three organizations," no primary study linked; no methodology)
- Kim/Yegge "4x commit frequency" is a recommendation, not a measured outcome
- No controlled studies comparing plan-review-implement-review-commit sequences vs simpler workflows for LLM agents specifically

## Retrieval Date

2026-04-03; refreshed 2026-04-19 with updated multi-perspective metrics (see next section).

---

## Multi-Perspective Review Patterns (Updated 2026-04-19)

*Supersedes Finding 3 above where the "<44 %" claim appeared. Evidence updated; perspective set corrected for skill/agent/rule review.*

### Updated Effectiveness Metrics

- Coverage: **45 % → 94 %** of errors detectable when moving from single-model review to multi-model ensemble ([arXiv:2512.16272 — Beyond Blind Spots](https://arxiv.org/abs/2512.16272)).
- Inter-rater reliability: single GPT-4 κ=0.627–0.841 vs. PoLL (Panel of Diverse Models, k=3) κ=0.763–0.906 ([arXiv:2404.18796](https://arxiv.org/abs/2404.18796)).
- Technical-validity bias remains: LLM-only review achieves 87 % focus on technical validity while underweighting novelty, long-term maintainability, adversarial risks. Multi-perspective mitigates via explicit role separation.

The original F1=0.126 novelty-detection figure ([arXiv:2502.17086](https://arxiv.org/abs/2502.17086)) remains valid but is domain-specific to paper review. Code/skill review shows a different blind-spot profile (above metrics).

### Perspective Set for Code Review vs. Skill/Agent/Rule Review

| Review target | Perspective triad | Notes |
|---------------|-------------------|-------|
| Code/PR review (standard) | Risk + Convention + Dependency | Security-first tie-break |
| **Skill/Agent/Rule review (this repo)** | **Clarity + Correctness + Integration** | Different ownership from code review |

Ownership assignments for skill/agent/rule review:
- **Clarity** owns: WS-*, RD-5, PD-1 (readability, structure).
- **Correctness** owns: COMP-X/Y/Z, CE-X, SAMP-*, RD-4, RD-6 (factual, robustness).
- **Integration** owns: IJ-*, SP-*, META-* (dependency, lifecycle, safety-of-chain).

### Trust-or-Escalate Cost Model (preferred over Selective-k=3)

From [arXiv:2407.18370](https://arxiv.org/abs/2407.18370) (ICLR 2025 Oral) — "Trust or Escalate":

- Default: single cheap-tier perspective (Haiku 4.5).
- Escalation to full 3-perspective Opus review only on:
  - ESC-1: weighted score within 2.5 points of a grade boundary,
  - ESC-2: finding severity set is (High + Low without Medium) — U-shape anomaly,
  - ESC-3: perspective-score divergence ≥ 2 letter grades,
  - ESC-4: explicit `--deep` flag.
- Cost: **1.35× baseline** with **80.2 % human agreement** — strictly better than single GPT-4 (77.8 %) and than always-k=3 (3.0× cost).

Supersedes the previous Selective-k=3 / 1.6× cost model referenced in earlier drafts.

### Escalation Execution Order (KV-cache-friendly)

First perspective runs **synchronously** to prime the shared-prefix cache. Perspectives 2 and 3 run in **parallel** only after the first perspective's first-token return confirms cache write. Expected cost breakdown: 1× P1 + 2 × 0.15× P2/P3 ≈ 1.3× baseline — matches the Trust-or-Escalate 1.35× target.

### Merge Rule (layered)

1. **Layer 0 content-dedup** (runs first): findings sharing (path, line-range, ≥80 % token-overlap on evidence quote) merge into one multi-tagged finding `dimensions={A,B,...}`.
2. **Layer 1 domain-ownership**: Safety → Correctness perspective; Clarity → Clarity perspective; Integration/Dependencies → Integration perspective.
3. **Layer 2 weighted vote** by perspective confidence.
4. **Layer 3 deterministic lexicographic tie-break** on perspective name.
5. **Layer 4 manual-review escalation** when conflicting high-confidence votes remain.

Shared boundary-exemplars across all 3 perspectives (BARS evidence: shared exemplars reduce rater divergence 30 % → <5 %).

### Sources for This Section

Tier 1:
- [arXiv:2512.16272 — Beyond Blind Spots](https://arxiv.org/abs/2512.16272) — 45 %→94 % multi-model coverage.
- [arXiv:2404.18796 — PoLL](https://arxiv.org/abs/2404.18796) — diverse-model panel κ.
- [arXiv:2407.18370 — Trust or Escalate](https://arxiv.org/abs/2407.18370) — ICLR 2025 Oral — 78.5 % cost reduction, 80.2 % agreement.
- [arXiv:2502.17086 — Mind the Blind Spots](https://arxiv.org/abs/2502.17086) — original F1=0.126 claim, paper-review domain.

Tier 2:
- Anthropic behavioral-anchored rating scale (BARS) conventions.
