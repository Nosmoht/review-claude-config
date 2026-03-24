# Planning Process Learnings: How We Built review-claude-config

A walkthrough of the planning and implementation process for colleagues who want to get better with Claude Code.

> **How to read this doc:** Every claim links to its source — either a research file in `../research/` or an external URL. Follow the links to verify and go deeper. This doc was written following [engineering documentation best practices](https://koliber.com/articles/engineering-documentation-best-practices) — hyperlink everything, document decision rationale, organize for discoverability.

## What We Built

A Claude Code skill that audits the quality of other Claude Code skills and agents, using evidence-based prompt and context engineering evaluation. It produces per-item quality certificates with A-F grades across 7 dimensions and concrete optimization recommendations.

- **Main skill:** [`.claude/skills/review-claude-config/SKILL.md`](../.claude/skills/review-claude-config/SKILL.md)
- **Scoring rubric:** [`.claude/skills/review-claude-config/references/scoring-rubric.md`](../.claude/skills/review-claude-config/references/scoring-rubric.md)
- **Engineering baseline:** [`.claude/skills/review-claude-config/references/engineering-baseline.md`](../.claude/skills/review-claude-config/references/engineering-baseline.md)
- **Baseline refresh skill:** [`.claude/skills/refresh-engineering-baseline/SKILL.md`](../.claude/skills/refresh-engineering-baseline/SKILL.md)

## Key Lessons from the Process

### 1. Start by Exploring, Not Assuming

Before writing any plan, we launched **parallel Explore agents** to understand:
- The existing repo structure (just a README)
- How skills and agents are defined across existing projects
- File formats, frontmatter fields, naming conventions → saved in [`research/claude-code/skill-agent-format-conventions.md`](../research/claude-code/skill-agent-format-conventions.md)

**Takeaway:** Don't assume you know the conventions. Read existing code first. Launch multiple Explore agents in parallel to save time.

### 2. Use WebFetch to Go Deep on Key Sources

We didn't just WebSearch — we **fetched and read full articles** from:
- [Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) → saved in [`research/context-engineering/anthropic-effective-context-engineering.md`](../research/context-engineering/anthropic-effective-context-engineering.md)
- [Anthropic: Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) → saved in [`research/tool-design/anthropic-writing-tools-for-agents.md`](../research/tool-design/anthropic-writing-tools-for-agents.md)
- [Anthropic: Equipping agents with agent skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills) → saved in [`research/agent-skills/anthropic-equipping-agents-with-skills.md`](../research/agent-skills/anthropic-equipping-agents-with-skills.md)
- [Manus/Meta: Context Engineering for AI Agents](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) → saved in [`research/context-engineering/manus-context-engineering-lessons.md`](../research/context-engineering/manus-context-engineering-lessons.md)
- Multiple academic papers on domain knowledge → saved in [`research/domain-knowledge/domain-knowledge-impact-on-quality.md`](../research/domain-knowledge/domain-knowledge-impact-on-quality.md)

**Takeaway:** WebSearch gives you headlines. WebFetch gives you substance. For foundational research, always fetch the full content.

### 3. Context Engineering is Not Prompt Engineering

This was a critical insight that changed the entire design. We initially had "Prompt Engineering" as the main evaluation dimension. Research showed:
- Context engineering is the broader discipline; prompt engineering is a subset ([context engineering overview](../research/context-engineering/context-engineering-overview.md))
- For agents (multi-turn, tool-using), context engineering matters MORE than prompt engineering ([Anthropic article](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents))
- Key concerns: context budget, JIT retrieval, tool set curation, reference file separation, KV-cache friendliness ([Manus lessons](../research/context-engineering/manus-context-engineering-lessons.md))

**Takeaway:** When the user pointed out we were missing context engineering, we researched it properly rather than just adding a bullet point. This fundamentally changed the architecture — it became a 7-dimension evaluation instead of 5.

### 4. Don't Trust Subagent Reviews Blindly

We launched a review agent to critique our plan. It recommended **dropping domain-specific WebSearch per item**, arguing that "domain expertise ≠ prompt engineering expertise."

The user challenged this: *"Did you trust the review blindly? Did the reviewer research whether domain knowledge affects quality?"*

We then researched the actual evidence ([domain knowledge research](../research/domain-knowledge/domain-knowledge-impact-on-quality.md)) and found:
- **30% better performance** with domain rules ([arXiv 2601.15153](https://arxiv.org/html/2601.15153))
- **206% improvement** in output quality with domain knowledge ([arXiv 2601.15153](https://arxiv.org/html/2601.15153))
- **Procedural knowledge significantly increases task success** regardless of base LLM ([arXiv 2511.07568](https://arxiv.org/pdf/2511.07568))
- The reviewer was wrong — and we almost accepted the recommendation without verifying

**Takeaway:** When a subagent makes a recommendation that changes your approach, **verify the underlying assumptions with evidence**. Don't remove features without proof they don't add value.

### 5. Iterate Reviews Until Convergence

We ran **4 review rounds**:
- **Round 1:** Found major issues (missing context engineering, self-contradictions, architecture gaps)
- **Round 2:** Found domain WebSearch was valuable (contradicting round 1), added Goal Alignment dimension, token budgets, scoring determinism
- **Round 3:** Only 3 minor edge-case findings (WebSearch geo-restriction, glob patterns, batch justification)
- **Round 4:** Confirmed convergence — no new structural issues

**Takeaway:** Don't stop after one review. Keep iterating until a review round finds only minor issues. The plan improved dramatically between rounds 1 and 3.

### 6. Separate Concerns: Static Baseline + Refresh Skill

Initially the plan had the review skill updating its own baseline at runtime. This created:
- Race conditions (concurrent runs)
- Ownership confusion (is it a reference doc or a living document?)
- Inconsistent results (different baseline state per run)

Solution: **Two separate skills.** [`/review-claude-config`](../.claude/skills/review-claude-config/SKILL.md) is read-only and uses a static baseline. [`/refresh-engineering-baseline`](../.claude/skills/refresh-engineering-baseline/SKILL.md) is a separate skill that handles updates.

**Takeaway:** When a single component has conflicting responsibilities, split it. This is the Single Responsibility Principle applied to skills.

### 7. Practice What You Preach

The skill evaluates context engineering quality — so it must itself follow context engineering best practices (sourced from [Anthropic](../research/context-engineering/anthropic-effective-context-engineering.md) and [Manus](../research/context-engineering/manus-context-engineering-lessons.md)):
- **Progressive disclosure:** SKILL.md is a compact orchestrator. Rubric and baseline are in `references/` files, loaded by subagents only when needed. This follows Anthropic's "[table of contents → chapters → appendix](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills)" pattern.
- **Minimal tool set:** Only 5 tools (Agent, Read, Glob, Grep, WebSearch). No Bash — enforces read-only via tooling, not just rules. Follows "[if a human can't say which tool to use, the agent can't either](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)."
- **Token budgets:** Baseline <2K tokens, rubric <1K tokens. Because "[a focused 300-token context often outperforms an unfocused 113K-token context](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)."
- **Cache-friendly dispatch:** Shared prefix (rubric + baseline) is byte-identical across all Phase 2 agents. Because KV-cache hit rate is "[the single most important metric for production agents](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)" (10x cost difference).

**Takeaway:** If your skill evaluates a quality, it should exemplify that quality. This is both a design constraint and a test — running the skill on itself should yield a good score.

### 8. Evidence-Based Decision Making

Every design decision in the final plan cites research:

| Decision | Evidence | Source |
|----------|----------|--------|
| Domain WebSearch per item | 30-206% quality improvement | [arXiv 2601.15153](https://arxiv.org/html/2601.15153) |
| Context engineering as separate dimension | "Prompt engineering is a subset of context engineering" | [Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| Token budgets (baseline <2K, rubric <1K) | "300 focused tokens > 113K unfocused" | [Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| No Bash tool | Principle of least privilege, minimal tool sets | [Anthropic: Writing tools](https://www.anthropic.com/engineering/writing-tools-for-agents) |
| Cache-friendly dispatch | 10x cost difference cached vs uncached | [Manus/Meta](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) |
| Progressive disclosure | "Amount of context bundled into a skill is effectively unbounded" | [Anthropic: Agent skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills) |
| Error preservation in context | "One of the clearest indicators of true agentic behavior" | [Manus/Meta](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) |

**Takeaway:** Don't design based on intuition alone. Research the evidence and cite it. This makes decisions defensible and teaches the next person why choices were made.

### 9. Save Research Results

We saved all research in a structured `research/` folder organized by topic:
```
research/
├── context-engineering/     (3 files: Anthropic, Manus, overview)
├── prompt-engineering/      (1 file: techniques summary)
├── tool-design/             (1 file: Anthropic article)
├── agent-skills/            (1 file: Anthropic article)
├── domain-knowledge/        (1 file: academic evidence)
└── claude-code/             (1 file: format conventions)
```

**Takeaway:** Research is expensive (WebSearch + WebFetch + synthesis). Save it in a structured, topic-organized format so it can be reused. Don't let it disappear when the conversation ends.

## Process Summary

```
1. Explore codebase (parallel agents)
2. Research (WebSearch + WebFetch for full articles)
3. Design initial plan
4. Review with subagent (evidence-required rules)
5. Verify subagent claims (don't trust blindly!)
6. Iterate until convergence (4 rounds)
7. Implement
8. Save research + document process
```

## Tools Used and When

| Tool | When to Use | Example from This Project |
|------|------------|--------------------------|
| **Explore agent** | Understanding codebase structure, finding conventions | Finding skill/agent formats across user's projects |
| **Plan agent** | Designing implementation approach | Creating the initial architecture |
| **WebSearch** | Finding current best practices, academic evidence | "context engineering vs prompt engineering 2025 2026" |
| **WebFetch** | Reading full articles (not just search snippets) | Fetching complete Anthropic engineering blog posts |
| **Review agent** | Critiquing plans — but verify their claims! | 4 rounds of evidence-backed review |
| **Read/Glob/Grep** | Direct file operations when you know what to look for | Reading existing SKILL.md files for format conventions |

## Claude Code Features That Helped

- **Parallel tool calls** — launching multiple agents/searches simultaneously
- **Plan mode** — forced us to think before coding
- **Agent tool** — delegating focused tasks to subagents with clean context
- **Memory system** — saved feedback for future conversations
- **Task tracking** — organized implementation steps

## Anti-Patterns We Avoided

- Coding before understanding the problem
- Accepting subagent recommendations without evidence
- One-shot reviews (we did 4 rounds)
- Monolithic files (split into skill + references + research)
- Self-updating references at runtime (separated into 2 skills)
- Kitchen-sink tool lists (only 5 tools, no Bash)
- Writing docs without sources (every claim links to evidence)

## Sources

### Primary Research (fetched and read in full)
- [Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Anthropic: Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)
- [Anthropic: Equipping agents with agent skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills)
- [Manus/Meta: Context Engineering for AI Agents](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)

### Academic Papers
- [arXiv 2601.15153: How to Build AI Agents by Augmenting LLMs with Codified Human Expert Domain Knowledge](https://arxiv.org/html/2601.15153)
- [arXiv 2511.07568: Procedural Knowledge Improves Agentic LLM Workflows](https://arxiv.org/pdf/2511.07568)
- [arXiv 2507.13334: A Survey of Context Engineering for Large Language Models](https://arxiv.org/abs/2507.13334)
- [arXiv 2505.17037: Prompt Engineering: How Prompt Vocabulary affects Domain Knowledge](https://arxiv.org/abs/2505.17037)
- [Chroma Research: Context Rot](https://research.trychroma.com/context-rot)

### Documentation Best Practices (meta — how this doc was written)
- [Koliber: Practical Engineering Documentation Best Practices](https://koliber.com/articles/engineering-documentation-best-practices)
- [Stepsize: Engineer's Guide to Internal Documentation](https://www.stepsize.com/blog/the-engineers-complete-guide-to-writing-excellent-internal-documentation)
