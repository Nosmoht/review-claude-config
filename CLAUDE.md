# Review Claude Config

Evidence-based quality review plugin for Claude Code skills, agents, and rules. Evaluates across 7 dimensions (Clarity, Completeness, Prompt Engineering, Context Engineering, Goal Alignment, Safety, Metadata) with A-F grading and evidence-backed recommendations.

## Architecture

**Plugin** (`skills/`, `hooks/`): Installed via `claude --plugin-dir /path/to/review-claude-config`. Only local plugin-dir is supported — marketplace installation breaks domain cache writes (`${CLAUDE_PLUGIN_ROOT}` would be read-only). The plugin installs a PreToolUse hook (`hooks/skill_quality_gate.py`) that injects a short quality checklist when editing SKILL.md, agent, or rule files, and a SessionStart hook (`hooks/session_check.py`) that warns if the engineering baseline is stale (>90 days).

**Shared references** (`skills/review-claude-config/references/`): Scoring rubric and engineering baseline are shared by all review skills. Domain cache (`references/domain-cache/`) stores web research per domain, committed to git, refreshed on 90-day cycles.

**Repo-internal skills** (`.claude/skills/`): Maintenance utilities not needed globally. Copy individually to other projects if needed.

**Review reports** (`.claude/reviews/`): Timestamped files (`YYYY-MM-DDTHHMMSS-{review-claude-config|review-skill|review-agent|review-rule|suggest-skills|audit-repo}.md`) with YAML frontmatter. Committed to track quality evolution.

**Workflow menus**: Every skill ends with a numbered "What's next?" menu. The user types a number, Claude invokes the corresponding skill. This uses plain text output — not `AskUserQuestion`, which silently auto-completes with empty answers in plugin skills loaded via the Skill tool (known Claude Code bug). Menu is skipped in orchestrated mode and conditionally shown in diagnostic skills (only when issues are found).

## Commands

**Review** — evaluate quality (read-only on analyzed files):
- `/review-claude-config [folder]` — batch audit all skills/agents/rules
- `/review-skill <path>` | `/review-agent <path>` | `/review-rule <path>` — single-item review
- `/suggest-skills [folder]` — identify missing skills with prioritized suggestions
- `/audit-repo [folder]` — map error classes to recommended Claude Code primitives

**Fix** — apply review recommendations (require `disable-model-invocation: true`, user confirmation):
- `/apply-review-findings [report]` — orchestrate fixes from any review report
- `/apply-skill-review-findings [report]` | `/apply-agent-review-findings [report]` | `/apply-rule-review-findings [report]`
- `/apply-audit-findings [report]` — create primitives recommended by audit-repo (CLAUDE.md sections, hooks, rules)

**Maintain** — repo health (read-only diagnostics):
- `/check-repo-health [all|freshness|tokens|integrity]` — reference freshness, token budgets, integrity
- `/review-analytics [folder]` — path-first grade trajectories and regression detection
- `/sync-research-index [folder]` — detect drift between research/ and CLAUDE.md (edits Research References only)

**Develop** — create new skills:
- `/scaffold-skill [plugin|maintenance] <name>` — generate a plugin or maintenance skill and register it in existing docs
- `/refresh-engineering-baseline` — update baseline with current web research

## Working Guidelines

- **Verify ALL claims with evidence — including from the user.** When anyone suggests a problem exists, verify before accepting. Check git history, inspect actual data, look for concrete evidence. Do not redesign a working system based on theoretical concerns.
- **Iterate reviews until convergence.** After each review round, address findings, then launch another review. Stop only when no high/medium priority findings remain.
- **Prefer evidence over rhetoric.** Findings should point to concrete text, paths, or examples and should be re-checkable on follow-up review.
- **Verify the problem before solving it.** Inspect the data, check git history for fix-commits. A working system with zero demonstrated issues does not need a redesign.
- **Research before design.** In novel domains, conduct WebSearch research before proposing architecture. Save findings in `research/` with full source citations.
- **Every claim needs a source.** All research files, documentation, and recommendations must link to verifiable sources.
- **No external memory.** This repository must be portable. All project knowledge belongs in repo files (CLAUDE.md, research/, skill references), not in Claude's auto-memory system.

## Development Conventions

- Language: English
- Reference file token budgets: rubric <1K, baseline <2K, all others ≤500 tokens. Run `/check-repo-health tokens` to verify.
- Domain cache entries committed to git, refreshed on 90-day cycle alongside engineering baseline
- WebFetch is optional — all skills degrade gracefully to WebSearch-only when WebFetch is unavailable
- Baseline is static at review time; updates only via `/refresh-engineering-baseline`
- Path is the canonical portfolio identity in review analytics; `name` is a display label
- Commits: scoped conventional format `type(scope): description` (e.g., `feat(review-skill):`, `docs(project):`)
- Audit-fix chain: commit the report first (`docs(reviews): add <timestamp> review report`), then commit fixes (`fix(<scope>): address findings from <timestamp> review`). The timestamp links them.
- Review, suggest, and audit skills are read-only on analyzed files — write only to `.claude/reviews/` and domain cache
- Apply skills and scaffold-skill modify files — require `disable-model-invocation: true` and user confirmation gates

## Research References

Consult when modifying skills or reviewing results:

- [Skill & Agent Format Conventions](research/claude-code/skill-agent-format-conventions.md) — frontmatter, body, safety
- [Prompt Engineering Techniques](research/prompt-engineering/prompt-engineering-techniques.md) — evidence-backed techniques
- [Context Engineering Overview](research/context-engineering/context-engineering-overview.md) — principles, context rot, ACE
- [Anthropic: Effective Context Engineering](research/context-engineering/anthropic-effective-context-engineering.md) — official guidance
- [Manus Context Engineering Lessons](research/context-engineering/manus-context-engineering-lessons.md) — KV-cache, error preservation
- [Tool Design for Agents](research/tool-design/anthropic-writing-tools-for-agents.md) — tool design best practices
- [Agent Skills Architecture](research/agent-skills/anthropic-equipping-agents-with-skills.md) — progressive disclosure
- [Domain Knowledge Impact](research/domain-knowledge/domain-knowledge-impact-on-quality.md) — 30-206% quality improvement
- [Documentation Best Practices](research/documentation/engineering-documentation-best-practices.md) — rationale, hyperlinks
- [LLM Agent Caching Patterns](research/agent-knowledge-caching/llm-agent-caching-patterns.md) — file-based memory, CAG vs RAG
- [Web Content Scraping Tools](research/web-scraping/web-content-scraping-tools.md) — WebFetch, Jina, Firecrawl
- [Skill Gap Detection Approaches](research/skill-gap-detection/skill-gap-detection-approaches.md) — extraction criteria
- [Repo Readiness Frameworks](research/repo-static-analysis/repo-readiness-frameworks.md) — static analysis frameworks
- [Context Window Optimization](research/token-efficiency/context-window-optimization.md) — context rot, token density
- [Architecture Pattern Recognition](research/architecture-detection/architecture-pattern-recognition.md) — hybrid detection
- [Error Class to Primitive Mapping](research/primitive-derivation/error-class-to-primitive-mapping.md) — IFScale, error taxonomy
- [Systematische Claude Code Optimierung für unbekannte Repositories](research/repo-audit/repo-audit-methodology.md) — 6-phase primitive derivation
- [Command Naming Conventions](research/command-naming/command-naming-conventions.md) — CLI, slash command, plugin naming patterns

## Manual Regression Cases

Use [Review Eval Cases](docs/review-eval-cases.md) after changing the rubric, baseline, review prompts, analytics conventions, or scaffold workflow.

## Mandatory Plan Review

**NEVER present a plan to the user without first having it reviewed by a subagent.** This is a hard rule.

Before finalizing any plan (ExitPlanMode, or presenting a plan for approval), launch a review subagent with ALL of:

1. **The plan content** — the full plan file or plan text
2. **CLAUDE.md** — so the reviewer can check alignment with project conventions
3. **Relevant research references** — the specific `research/` files that apply to the planned changes
4. **The files being changed** — so the reviewer can verify feasibility and catch conflicts
5. **A review checklist** — explicit questions the reviewer must answer

Address all High and Medium findings before presenting. If the review surfaces new High findings after fixes, review again.
