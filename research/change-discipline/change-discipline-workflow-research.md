# Change Discipline Workflow Research

Research supporting the global change discipline rule for Claude Code sessions.

## Key Findings

### 1. Proportional review processes outperform uniform ceremony

Requiring uniform high-ceremony review for all changes causes costs to exceed benefits for low-risk changes. Google's 9-million-review study found that knowledge transfer — not defect detection — drives most code-review ROI. PRs under 400 LOC capture 66-75% of defects at 200 LOC/hour; oversized PRs drop below 50% detection rates.

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
- Complementary human+LLM review: LLMs for systematic validity, humans for nuanced judgment (arxiv:2502.17086)
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
- "35-40% bug density increase" claim from AI Code Quality Guide 2026 — Tier 2 source, no primary study linked
- Kim/Yegge "4x commit frequency" is a recommendation, not a measured outcome
- No controlled studies comparing plan-review-implement-review-commit sequences vs simpler workflows for LLM agents specifically

## Retrieval Date

2026-04-03
