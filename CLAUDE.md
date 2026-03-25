# Review Claude Config

A Claude Code skill that analyzes and optimizes Claude Code skills, agents, and rules using evidence-based prompt and context engineering evaluation.

## Skills

- `/review-claude-config [folder]` — Audit all skills/agents/rules in a folder (defaults to cwd). Read-only, produces per-item quality certificates. Rules use a 3-dimension subset (Clarity, Completeness, Goal Alignment).
- `/suggest-skills [folder]` — Analyze a repository to identify missing skills. Read-only, produces prioritized suggestions with skeleton SKILL.md files.
- `/refresh-engineering-baseline` — Update the engineering baseline with current research via WebSearch.
- `/apply-review-findings [report-path]` — Apply High/Medium review recommendations with audit-fix chain commits.
- `/skill-scaffolding <skill-name>` — Create new skill directory with SKILL.md, references, and CLAUDE.md registration.
- `/check-repo-health [all|freshness|tokens|integrity]` — Verify reference freshness, token budgets, and cross-skill integrity.
- `/review-analytics [folder]` — Track grade trajectories and detect regressions across review reports.
- `/research-index [folder]` — Detect drift between research/ files and CLAUDE.md Research References.

## Installation

Copy skill directories into any project's `.claude/skills/`:
```
cp -r .claude/skills/review-claude-config <target>/.claude/skills/
cp -r .claude/skills/suggest-skills <target>/.claude/skills/
cp -r .claude/skills/refresh-engineering-baseline <target>/.claude/skills/
cp -r .claude/skills/apply-review-findings <target>/.claude/skills/
cp -r .claude/skills/skill-scaffolding <target>/.claude/skills/
cp -r .claude/skills/check-repo-health <target>/.claude/skills/
cp -r .claude/skills/review-analytics <target>/.claude/skills/
cp -r .claude/skills/research-index <target>/.claude/skills/
```

## File Structure

- `.claude/skills/review-claude-config/SKILL.md` — Main orchestrator skill
- `.claude/skills/review-claude-config/references/scoring-rubric.md` — 7-dimension A-F grading rubric
- `.claude/skills/review-claude-config/references/engineering-baseline.md` — Curated prompt, context, and tool design techniques
- `.claude/skills/review-claude-config/references/domain-cache/` — Cached domain research from review analysis agents (auto-populated, committed to git)
- `.claude/skills/suggest-skills/SKILL.md` — Skill gap detection and suggestion skill
- `.claude/skills/suggest-skills/references/signal-catalog.md` — Signal patterns and extraction criteria for detecting missing skills
- `.claude/skills/refresh-engineering-baseline/SKILL.md` — Baseline refresh skill
- `.claude/skills/apply-review-findings/SKILL.md` — Automated review finding application
- `.claude/skills/apply-review-findings/references/commit-conventions.md` — Scoped commit format and audit-fix chain rules
- `.claude/skills/skill-scaffolding/SKILL.md` — Skill directory scaffolding
- `.claude/skills/skill-scaffolding/references/skill-template.md` — Default SKILL.md template
- `.claude/skills/check-repo-health/SKILL.md` — Repository health dashboard
- `.claude/skills/check-repo-health/references/health-thresholds.md` — Freshness, token, and integrity thresholds
- `.claude/skills/review-analytics/SKILL.md` — Grade trajectory tracking
- `.claude/skills/review-analytics/references/report-schema.md` — Review report frontmatter schema
- `.claude/skills/research-index/SKILL.md` — Research directory drift detection

## Conventions

- Language: English
- Reference files must stay within token budgets: rubric <1K, baseline <2K, signal-catalog <1K, domain cache entries ≤500 tokens each, new skill reference files (commit-conventions, skill-template, health-thresholds, report-schema) ≤500 tokens each
- Domain cache entries are committed to track research evolution and enable offline reuse. Refreshed on the same 90-day cycle as the engineering baseline.
- Web content fetching (WebFetch) is optional in both skills. Skills degrade gracefully to WebSearch-only when WebFetch is unavailable.
- The review and suggest skills are read-only on analyzed files — review writes reports to `.claude/reviews/` and domain cache entries to its own `references/domain-cache/`; suggest writes only reports to `.claude/reviews/`
- Review reports are saved to `.claude/reviews/YYYY-MM-DDTHHMMSS-review-claude-config.md` and suggestion reports to `.claude/reviews/YYYY-MM-DDTHHMMSS-suggest-skills.md` — both should be committed to track skill quality evolution
- The baseline is static at review time; updates happen via `/refresh-engineering-baseline`
- Commits use scoped conventional format: `type(scope): description` (e.g., `feat(review-skill):`, `fix(refresh-skill):`, `docs(project):`)
- Review audit→fix chain commits use the report timestamp as shared identifier: `docs(reviews): add <timestamp> review report` → `fix(<scope>): address findings from <timestamp> review`
- When acting on review findings: commit the report first, then commit fixes. This creates a traceable audit → fix chain in git history. The `/apply-review-findings` skill automates this workflow.
- `/apply-review-findings` and `/skill-scaffolding` modify files — they require `disable-model-invocation: true` and user confirmation gates
- `/check-repo-health` and `/review-analytics` are read-only diagnostic skills
- `/research-index` edits only the Research References section of CLAUDE.md

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
- [Skill Gap Detection Approaches](research/skill-gap-detection/skill-gap-detection-approaches.md) — Extraction criteria, prior art survey, proactive gap analysis methodology

## Working Guidelines

- **Verify ALL claims with evidence — including from the user.** When anyone (subagent, reviewer, or user) suggests a problem exists or recommends changing the approach, verify the underlying assumptions before accepting. Check git history, inspect actual data, and look for concrete evidence of failure. Do not redesign a working system based on theoretical concerns. (Context: a reviewer once recommended dropping domain-specific research — we verified and found the reviewer was wrong. In another session, a user suggested the domain cache key mechanism was broken — we checked and found 14 clean entries with zero issues.)
- **Iterate reviews until convergence.** After each review round, address findings, then launch another review. Stop only when a review returns no high/medium priority findings. Don't accept the first review as final.
- **Verify the problem before solving it.** Before proposing changes, check if the problem actually exists: inspect the data, check git history for fix-commits, and look for concrete evidence of failure. A working system with zero demonstrated issues does not need a redesign based on theoretical concerns.
- **Research before design.** When working in novel domains (caching patterns, gap detection, new skill types), conduct WebSearch research before proposing architecture. Save findings as research files in `research/` with full source citations.
- **Every claim needs a source.** All research files, documentation, and recommendations must link to verifiable sources. Follow the [documentation best practices](research/documentation/engineering-documentation-best-practices.md) used in this project.
- **No external memory.** This repository must be portable. All project knowledge belongs in repo files (CLAUDE.md, research/, skill references), not in Claude's auto-memory system.

## Mandatory Plan Review

**NEVER present a plan to the user without first having it reviewed by a subagent.** This is a hard rule, not a suggestion.

Before finalizing any plan (ExitPlanMode, or presenting a plan for approval), launch a review subagent with ALL of:

1. **The plan content** — the full plan file or plan text
2. **CLAUDE.md** — so the reviewer can check alignment with project conventions
3. **Relevant research references** — the specific `research/` files that apply to the planned changes (consult the Research References section above)
4. **The files being changed** — so the reviewer can verify feasibility and catch conflicts
5. **A review checklist** — explicit questions the reviewer must answer (e.g., "Does the commit order follow audit→fix?", "Are conventional commits specified?", "Do proposed changes follow skill-agent-format-conventions.md?")

Address all High and Medium findings from the review before presenting the plan. If the review surfaces new High findings after your fixes, review again. Only present the plan when a review returns no High/Medium findings.
