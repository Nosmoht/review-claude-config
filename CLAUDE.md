# Review Claude Config

A Claude Code skill that analyzes and optimizes Claude Code skills, agents, and rules using evidence-based prompt and context engineering evaluation.

## Skills

- `/review-claude-config [folder]` — Audit all skills/agents/rules in a folder (defaults to cwd). Delegates to specialized reviewers, adds cross-item analysis. Read-only, produces per-item quality certificates.
- `/review-skill <path>` — Evaluate a single skill's quality across 7 dimensions. Can be used standalone or delegated by /review-claude-config.
- `/review-agent <path>` — Evaluate a single agent's quality across 7 dimensions with agent-specific checks (model selection, activation precision, trigger coverage).
- `/review-rule <path>` — Evaluate a single rule's quality across 3 dimensions (Clarity, Completeness, Goal Alignment).
- `/suggest-skills [folder]` — Analyze a repository to identify missing skills. Read-only, produces prioritized suggestions with skeleton SKILL.md files.
- `/audit-repo [folder]` — Analyze any repository to identify needed Claude Code primitives (CLAUDE.md, skills, agents, hooks/rules). Produces a prioritized intervention matrix mapping error classes to recommended primitives. Read-only, writes report to `.claude/reviews/`.
- `/refresh-engineering-baseline` — Update the engineering baseline with current research via WebSearch.
- `/apply-review-findings [report-path]` — Orchestrate application of High/Medium recommendations from any review report (batch or standalone). Delegates to specialized type-specific appliers.
- `/apply-skill-review-findings [report-path]` — Apply review recommendations to a single skill with skill-specific validation (line count, token budgets, frontmatter, progressive disclosure).
- `/apply-agent-review-findings [report-path]` — Apply review recommendations to a single agent with agent-specific validation (single-file constraint, model selection, trigger keywords, tool minimalism).
- `/apply-rule-review-findings [report-path]` — Apply review recommendations to a single rule with rule-specific validation (no frontmatter, unambiguous verbs, scope explicitness, conflict detection).
- `/skill-scaffolding <skill-name>` — Create new skill directory with SKILL.md, references, and CLAUDE.md registration.
- `/check-repo-health [all|freshness|tokens|integrity]` — Verify reference freshness, token budgets, and cross-skill integrity.
- `/review-analytics [folder]` — Track grade trajectories and detect regressions across review reports.
- `/research-index [folder]` — Detect drift between research/ files and CLAUDE.md Research References.

## Installation

This repository is a Claude Code plugin. Install it locally to make `/review-claude-config` and `/suggest-skills` available in all projects:

```bash
cc --plugin-dir /path/to/review-claude-config
```

**Only local installation via `--plugin-dir` is supported.** Marketplace installation would break domain cache writes since `${CLAUDE_PLUGIN_ROOT}` would point to a read-only directory.

The plugin also installs a PreToolUse hook that automatically injects quality guidelines when editing SKILL.md, agent, or rule files in any project.

For repo-internal skills only (not globally needed):
```
cp -r .claude/skills/refresh-engineering-baseline <target>/.claude/skills/
cp -r .claude/skills/skill-scaffolding <target>/.claude/skills/
cp -r .claude/skills/check-repo-health <target>/.claude/skills/
cp -r .claude/skills/review-analytics <target>/.claude/skills/
cp -r .claude/skills/research-index <target>/.claude/skills/
```

## File Structure

### Plugin (globally available via `--plugin-dir`)
- `.claude-plugin/plugin.json` — Plugin manifest
- `hooks/hooks.json` — Hook registration (PreToolUse quality gate, SessionStart freshness check)
- `hooks/skill_quality_gate.py` — Injects quality guidelines when editing SKILL.md/agent/rule files
- `hooks/session_check.py` — Warns if engineering baseline is stale (>90 days)
- `hooks/guidelines.md` — Distilled quality checklist from rubric + baseline
- `skills/review-claude-config/SKILL.md` — Orchestrator skill (discovery, delegation, cross-item analysis, report persistence)
- `skills/review-claude-config/references/scoring-rubric.md` — 7-dimension A-F grading rubric (shared by all review skills)
- `skills/review-claude-config/references/engineering-baseline.md` — Curated prompt, context, and tool design techniques (shared by all review skills)
- `skills/review-claude-config/references/domain-cache/` — Cached domain research (auto-populated, committed to git)
- `skills/review-skill/SKILL.md` — Single-skill quality evaluation (7 dimensions)
- `skills/review-skill/references/skill-evaluation-guide.md` — Skill-specific evaluation patterns
- `skills/review-agent/SKILL.md` — Single-agent quality evaluation (7 dimensions + agent-specific checks)
- `skills/review-agent/references/agent-evaluation-guide.md` — Agent-specific evaluation patterns
- `skills/review-rule/SKILL.md` — Single-rule quality evaluation (3 dimensions)
- `skills/review-rule/references/rule-evaluation-guide.md` — Rule-specific evaluation patterns
- `skills/suggest-skills/SKILL.md` — Skill gap detection and suggestion skill
- `skills/suggest-skills/references/signal-catalog.md` — Signal patterns and extraction criteria
- `skills/audit-repo/SKILL.md` — Repository audit skill (static analysis, token efficiency, primitives derivation, needs matrix)
- `skills/audit-repo/references/signal-patterns.md` — Glob/Grep patterns per analysis step
- `skills/audit-repo/references/error-class-taxonomy.md` — 7 error classes with indicators and primitive mapping
- `skills/audit-repo/references/primitive-decision-matrix.md` — Decision rules for primitive type selection
- `skills/audit-repo/references/token-heuristics.md` — Thresholds and scoring for token efficiency analysis
- `skills/audit-repo/references/audit-report-schema.md` — YAML frontmatter schema and body structure for audit reports
- `skills/apply-skill-review-findings/SKILL.md` — Single-skill fix application with skill-specific validation
- `skills/apply-skill-review-findings/references/skill-fix-guide.md` — Skill-specific fix validation rules
- `skills/apply-agent-review-findings/SKILL.md` — Single-agent fix application with agent-specific validation
- `skills/apply-agent-review-findings/references/agent-fix-guide.md` — Agent-specific fix validation rules
- `skills/apply-rule-review-findings/SKILL.md` — Single-rule fix application with rule-specific validation
- `skills/apply-rule-review-findings/references/rule-fix-guide.md` — Rule-specific fix validation rules
- `skills/apply-review-findings/SKILL.md` — Orchestrator: delegates to specialized type-specific appliers
- `skills/apply-review-findings/references/commit-conventions.md` — Scoped commit format and audit-fix chain rules

### Repo-internal skills
- `.claude/skills/refresh-engineering-baseline/SKILL.md` — Baseline refresh skill
- `.claude/skills/skill-scaffolding/SKILL.md` — Skill directory scaffolding
- `.claude/skills/skill-scaffolding/references/skill-template.md` — Default SKILL.md template
- `.claude/skills/check-repo-health/SKILL.md` — Repository health dashboard
- `.claude/skills/check-repo-health/references/health-thresholds.md` — Freshness, token, and integrity thresholds
- `.claude/skills/review-analytics/SKILL.md` — Grade trajectory tracking
- `.claude/skills/review-analytics/references/report-schema.md` — Review report frontmatter schema
- `.claude/skills/research-index/SKILL.md` — Research directory drift detection

## Conventions

- Language: English
- Reference files must stay within token budgets: rubric <1K, baseline <2K, signal-catalog <1K, guidelines ≤500 tokens, domain cache entries ≤500 tokens each, evaluation guides (skill-evaluation-guide, agent-evaluation-guide, rule-evaluation-guide) ≤500 tokens each, fix guides (skill-fix-guide, agent-fix-guide, rule-fix-guide) ≤500 tokens each, audit-repo references (signal-patterns, error-class-taxonomy, primitive-decision-matrix, token-heuristics, audit-report-schema) ≤500 tokens each, other skill reference files (commit-conventions, skill-template, health-thresholds, report-schema) ≤500 tokens each
- Domain cache entries are committed to track research evolution and enable offline reuse. Refreshed on the same 90-day cycle as the engineering baseline.
- Web content fetching (WebFetch) is optional in both skills. Skills degrade gracefully to WebSearch-only when WebFetch is unavailable.
- The review, suggest, and audit skills are read-only on analyzed files — review writes reports to `.claude/reviews/` and domain cache entries to its own `references/domain-cache/`; suggest and audit-repo write only reports to `.claude/reviews/`
- Review reports are saved to `.claude/reviews/YYYY-MM-DDTHHMMSS-review-claude-config.md` (batch), `.claude/reviews/YYYY-MM-DDTHHMMSS-review-{skill|agent|rule}.md` (standalone), `.claude/reviews/YYYY-MM-DDTHHMMSS-suggest-skills.md` (suggestions), and `.claude/reviews/YYYY-MM-DDTHHMMSS-audit-repo.md` (audit) — all should be committed to track quality evolution
- The baseline is static at review time; updates happen via `/refresh-engineering-baseline`
- Commits use scoped conventional format: `type(scope): description` (e.g., `feat(review-skill):`, `fix(refresh-skill):`, `docs(project):`)
- Review audit→fix chain commits use the report timestamp as shared identifier: `docs(reviews): add <timestamp> review report` → `fix(<scope>): address findings from <timestamp> review`
- When acting on review findings: commit the report first, then commit fixes. This creates a traceable audit → fix chain in git history. The `/apply-review-findings` skill automates this workflow.
- `/apply-review-findings`, `/apply-skill-review-findings`, `/apply-agent-review-findings`, `/apply-rule-review-findings`, and `/skill-scaffolding` modify files — they require `disable-model-invocation: true` and user confirmation gates
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
- [Repo Readiness Frameworks](research/repo-static-analysis/repo-readiness-frameworks.md) — Static analysis frameworks predicting AI tool effectiveness
- [Context Window Optimization](research/token-efficiency/context-window-optimization.md) — Context rot, token density, navigation cost heuristics
- [Architecture Pattern Recognition](research/architecture-detection/architecture-pattern-recognition.md) — Hybrid detection, signature directories, domain docs
- [Error Class to Primitive Mapping](research/primitive-derivation/error-class-to-primitive-mapping.md) — IFScale limits, error taxonomy, primitive decision framework
- [Repo Audit Methodology](research/repo-audit/repo-audit-methodology.md) — Systematic 6-phase methodology for deducing Claude Code primitives from repo structure

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
