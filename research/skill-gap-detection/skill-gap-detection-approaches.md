---
last_refreshed: 2026-03-24
---

# Skill Gap Detection for LLM Agent Skills

How to identify missing skills in a repository — approaches, criteria, and prior art.

## Key Finding: No Proactive Framework Exists

A [comprehensive survey of agent skills](https://arxiv.org/html/2602.12430v3) (Feb 2026) covering architecture, acquisition, and security found **no dedicated framework for proactive skill gap detection**. Existing skill acquisition is reactive — triggered by user requests or task failures, not by analyzing what's missing. This makes proactive gap analysis a novel contribution.

## Extraction Criteria (from Repository Mining)

[Bi et al. (2026)](https://arxiv.org/html/2603.11808v1) propose a framework for mining skills from open-source repositories using dense retrieval + cross-encoder ranking. They identify four criteria for extracting worthwhile skills:

| Criterion | Definition | Application to Gap Detection |
|-----------|-----------|------------------------------|
| **Recurrence** | Pattern appears across multiple contexts or solves a problem class | Signal must appear in 2+ categories (e.g., deploy mentioned in CLAUDE.md AND in scripts/) |
| **Verification** | Code/workflow is functional, well-documented, bug-free | Workflow must be well-defined enough to express as SKILL.md instructions |
| **Non-obviousness** | Logic requires domain expertise or debugging | Single-command operations (e.g., "run prettier") don't justify skills |
| **Generalizability** | Pattern can be parameterized for different contexts | Too project-specific workflows get downgraded |

These four criteria serve as a false-positive filter: a suggested skill should pass at least 3 of 4.

## Exploration-First Discovery

[EXIF (arxiv 2506.04287)](https://arxiv.org/abs/2506.04287) uses an exploration agent (Alice) to discover skills for a target agent (Bob). Alice explores the environment, generates a skill dataset, and iteratively refines based on Bob's performance gaps. While EXIF operates on runtime environments (not static repos), the **exploration-first strategy** — scan broadly, then analyze signals — translates to repository scanning.

## Progressive Disclosure for Skill Skeletons

The [Agent Skills Specification (agentskills.io)](https://agentskills.io/specification) defines a 3-tier progressive disclosure model:

1. **Metadata** (~100 tokens): `name` + `description` — loaded at startup for all skills
2. **Instructions** (<5000 tokens recommended): Full SKILL.md body — loaded on activation
3. **Resources** (as needed): `scripts/`, `references/`, `assets/` — loaded on demand

Generated skeletons should follow this structure. The `name` (required, max 64 chars, lowercase+hyphens) and `description` (required, max 1024 chars) fields are the minimum viable skill.

## Description as Key Matching Signal

[Claude Code documentation](https://code.claude.com/docs/en/skills) confirms that skill descriptions drive automatic discovery: "Claude matches requests against descriptions using semantic similarity, so write descriptions that include keywords users would naturally say." The [Skills Catalog approach](https://tiberriver256.github.io/ai%20and%20technology/skills-catalog-part-1-indexing-ai-context/) validates this at scale: ~100 skills indexed at 5K-10K tokens, with description-driven matching as the retrieval mechanism.

Implication: suggested skills must include high-quality descriptions with natural trigger keywords.

## Skill-Creator as Reactive Baseline

[Anthropic's skill-creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md) follows a reactive flow: capture intent → interview → write SKILL.md → eval → iterate. It has no discovery capability — the user must already know what skill to build. However, its **analyst pass** (pattern recognition in eval results: repeated scripts → bundle, high-variance → refine) is a useful pattern for post-generation quality checks.

## Eval-Based Gap Identification

[Langfuse's agent skill evaluation guide](https://langfuse.com/blog/2026-02-26-evaluate-ai-agent-skills) defines evals as: prompt → trace → checks → score. Gaps surface during manual trace review as "cases where the skill doesn't trigger at all, triggers too eagerly, or runs but deviates from intended steps." This maps to analyzing repository signals for workflows that have no corresponding skill trigger.

## Hybrid Approach: Static Tables + Open LLM Reasoning

Static pattern-matching (signal tables) catches known opportunities but misses everything not in the table. Pure LLM reasoning is flexible but unpredictable. Research supports a hybrid:

**Layer 1 — Deterministic table matching.** A signal catalog maps file patterns to skill opportunities. Fast, reliable, reproducible. Limitation: blind to anything not in the table.

**Layer 2 — Open LLM reasoning.** The agent receives the full repository context and reasons freely about what's missing. [Claude Code's own skill selection uses pure LLM reasoning](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/) — "no embeddings, classifiers, or pattern matching... the decision happens inside Claude's forward pass." The same reasoning capability can identify gaps, not just match existing skills.

**Why hybrid beats either alone:**
- [Codified Context (arxiv 2602.20478)](https://arxiv.org/html/2602.20478v1) detects missing specifications through "agent confusion" and "null retrieval results" — reactive signals that no static table captures. Their keyword matching misses semantic gaps.
- [SoK: Agentic Skills (arxiv 2602.20867)](https://arxiv.org/html/2602.20867v1) proposes "meta-skills" for gap detection and notes that "unsupervised discovery — identifying skill boundaries without human-provided task definitions — remains an open question." The table provides the human-provided definitions; reasoning handles the unsupervised part.
- [Voyager](https://arxiv.org/html/2602.20867v1) discovers skills through curriculum-driven exploration, but warns: "without external verification, agents may converge on locally optimal but globally suboptimal procedures." The extraction criteria (Recurrence, Verification, Non-obviousness, Generalizability) serve as that verification gate for both layers.

**Repository type matters.** A source code repo and a skills/config repo need fundamentally different signal tables. Application repos need deploy/test/CI skills. Skills repos need meta-skills (quality audit, reference maintenance, portfolio health). The table must be type-aware; reasoning naturally adapts.

## Sources

- [Agent Skills for LLMs: Architecture, Acquisition, Security](https://arxiv.org/html/2602.12430v3) — Survey confirming no proactive gap detection framework exists (Feb 2026)
- [Automating Skill Acquisition through Repository Mining](https://arxiv.org/html/2603.11808v1) — Four extraction criteria: Recurrence, Verification, Non-obviousness, Generalizability (Mar 2026)
- [EXIF: Automated Skill Discovery for Language Agents](https://arxiv.org/abs/2506.04287) — Exploration-first agent skill discovery framework (Jun 2025)
- [Agent Skills Specification](https://agentskills.io/specification) — Official spec: progressive disclosure, required fields
- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills) — Discovery mechanism, frontmatter reference, best practices
- [Skills Catalog Indexing](https://tiberriver256.github.io/ai%20and%20technology/skills-catalog-part-1-indexing-ai-context/) — Description-driven matching at scale
- [Anthropic skill-creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md) — Reactive skill building with eval loop
- [Evaluating AI Agent Skills (Langfuse)](https://langfuse.com/blog/2026-02-26-evaluate-ai-agent-skills) — Eval-based gap identification methodology
- [Claude Skills Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/) — Claude Code uses pure LLM reasoning for skill selection, no pattern matching (Oct 2025)
- [Codified Context (arxiv 2602.20478)](https://arxiv.org/html/2602.20478v1) — Tiered knowledge architecture, gap detection via agent confusion signals (Feb 2026)
- [SoK: Agentic Skills (arxiv 2602.20867)](https://arxiv.org/html/2602.20867v1) — Meta-skills for gap detection, open-ended vs closed-ended discovery (Feb 2026)
