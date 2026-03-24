# Review Claude Config

A Claude Code skill that analyzes and optimizes Claude Code skills and agents using evidence-based prompt and context engineering evaluation.

## Skills

- `/review-claude-config [folder]` — Audit all skills/agents in a folder (defaults to cwd). Read-only, produces per-item quality certificates.
- `/refresh-engineering-baseline` — Update the engineering baseline with current research via WebSearch.

## Installation

Copy both skill directories into any project's `.claude/skills/`:
```
cp -r .claude/skills/review-claude-config <target>/.claude/skills/
cp -r .claude/skills/refresh-engineering-baseline <target>/.claude/skills/
```

## File Structure

- `.claude/skills/review-claude-config/SKILL.md` — Main orchestrator skill
- `.claude/skills/review-claude-config/references/scoring-rubric.md` — 7-dimension A-F grading rubric
- `.claude/skills/review-claude-config/references/engineering-baseline.md` — Curated prompt, context, and tool design techniques
- `.claude/skills/review-claude-config/references/domain-cache/` — Cached domain research from review analysis agents (auto-populated, committed to git)
- `.claude/skills/refresh-engineering-baseline/SKILL.md` — Baseline refresh skill

## Conventions

- Language: English
- Reference files must stay within token budgets: rubric <1K, baseline <2K, domain cache entries ≤500 tokens each
- Domain cache entries are committed to track research evolution and enable offline reuse. Refreshed on the same 90-day cycle as the engineering baseline.
- Web content fetching (WebFetch) is optional in both skills. Skills degrade gracefully to WebSearch-only when WebFetch is unavailable.
- The review skill is read-only on analyzed files — it writes review reports to `.claude/reviews/` and domain cache entries to its own `references/domain-cache/`
- Review reports are saved to `.claude/reviews/YYYY-MM-DDTHHMMSS-review-claude-config.md` and should be committed to track skill quality evolution
- The baseline is static at review time; updates happen via `/refresh-engineering-baseline`
- Commits use scoped conventional format: `type(scope): description` (e.g., `feat(review-skill):`, `fix(refresh-skill):`, `docs(project):`)
- Review audit→fix chain commits use the report timestamp as shared identifier: `docs(reviews): add <timestamp> review report` → `fix(<scope>): address findings from <timestamp> review`
- When acting on review findings: commit the report first, then commit fixes. This creates a traceable audit → fix chain in git history.

## Research References

Evidence-based research informing the rubric and baseline. Consult these when modifying skills or reviewing results:

- [Skill & Agent Format Conventions](research/claude-code/skill-agent-format-conventions.md) — Valid frontmatter fields, body conventions, safety gates
- [Prompt Engineering Techniques](research/prompt-engineering/prompt-engineering-techniques.md) — Evidence-backed techniques with academic sources
- [Context Engineering Overview](research/context-engineering/context-engineering-overview.md) — Core principles, context rot, ACE framework
- [Anthropic: Effective Context Engineering](research/context-engineering/anthropic-effective-context-engineering.md) — Official Anthropic guidance
- [Manus Context Engineering Lessons](research/context-engineering/manus-context-engineering-lessons.md) — Production lessons, KV-cache, error preservation
- [Tool Design for Agents](research/tool-design/anthropic-writing-tools-for-agents.md) — Anthropic's tool design best practices
- [Agent Skills Architecture](research/agent-skills/anthropic-equipping-agents-with-skills.md) — Progressive disclosure, skill format
- [Domain Knowledge Impact](research/domain-knowledge/domain-knowledge-impact-on-quality.md) — 30-206% quality improvement from domain rules
- [Documentation Best Practices](research/documentation/engineering-documentation-best-practices.md) — Hyperlink everything, document rationale
- [LLM Agent Caching Patterns](research/agent-knowledge-caching/llm-agent-caching-patterns.md) — File-based memory, CAG vs RAG, token-efficient formats, KV-cache optimization
- [Web Content Scraping Tools](research/web-scraping/web-content-scraping-tools.md) — Tool evaluation for full-content retrieval (WebFetch, Jina Reader, Firecrawl, Crawl4AI)

## Working Guidelines

- **Verify subagent claims with evidence.** When a subagent/reviewer recommends changing the approach, verify the underlying assumptions with WebSearch or other evidence before accepting. Do not remove features without proof they don't add value. (Context: a reviewer once recommended dropping domain-specific research — we verified and found the reviewer was wrong, domain knowledge improves quality by 30-206%.)
- **Iterate reviews until convergence.** After each review round, address findings, then launch another review. Stop only when a review returns no high/medium priority findings. Don't accept the first review as final.
- **Every claim needs a source.** All research files, documentation, and recommendations must link to verifiable sources. Follow the [documentation best practices](research/documentation/engineering-documentation-best-practices.md) used in this project.

## Mandatory Plan Review

**NEVER present a plan to the user without first having it reviewed by a subagent.** This is a hard rule, not a suggestion.

Before finalizing any plan (ExitPlanMode, or presenting a plan for approval), launch a review subagent with ALL of:

1. **The plan content** — the full plan file or plan text
2. **CLAUDE.md** — so the reviewer can check alignment with project conventions
3. **Relevant research references** — the specific `research/` files that apply to the planned changes (consult the Research References section above)
4. **The files being changed** — so the reviewer can verify feasibility and catch conflicts
5. **A review checklist** — explicit questions the reviewer must answer (e.g., "Does the commit order follow audit→fix?", "Are conventional commits specified?", "Do proposed changes follow skill-agent-format-conventions.md?")

Address all High and Medium findings from the review before presenting the plan. If the review surfaces new High findings after your fixes, review again. Only present the plan when a review returns no High/Medium findings.
