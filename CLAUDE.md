# Review Claude Config

Maintainer operating guide for this repository (Clarity, Completeness, Prompt Engineering, Context Engineering, Goal Alignment, Safety, Metadata). Use this file for active repo conventions, command inventory, and maintenance workflow. User-facing orientation lives in [README.md](README.md). Skill and hook navigation lives in [docs/skills/README.md](docs/skills/README.md).

## Architecture

- **Plugin surface**: `skills/` and `hooks/`, installed via `claude --plugin-dir`
- **Shared references**: `skills/review-claude-config/references/`, including the rubric, baseline, evidence contract, source-quality criteria, and review-report contract
- **Domain cache**: `skills/review-claude-config/references/domain-cache/`, committed to git and maintained on the repo's 90-day rhythm; this is a repo default, not a scientific claim
- **Repo-internal skills**: `.claude/skills/` for maintenance utilities not needed globally
- **Review reports**: `.claude/reviews/` for timestamped reports consumed by analytics and apply flows

## Commands

This is the authoritative maintainer command inventory for the repo.

### Review

- `/review-claude-config [folder] [--validation]` - batch audit of skills, agents, and rules
- `/review-skill <path>` - single skill review
- `/review-agent <path>` - single agent review
- `/review-rule <path>` - single rule review
- `/suggest-skills [folder]` - heuristic skill discovery
- `/audit-repo [folder]` - repo-structure audit for Claude Code primitives

### Fix

- `/apply-review-findings [report]` - orchestrate fixes from a review report
- `/apply-skill-review-findings [report]`
- `/apply-agent-review-findings [report]`
- `/apply-rule-review-findings [report]`
- `/apply-audit-findings [report]` - create primitives recommended by `audit-repo`

### Maintain

- `/check-repo-health [all|freshness|tokens|integrity] [--validation]`
- `/review-analytics [folder] [--validation]`
- `/sync-research-index [folder]`
- `/refresh-engineering-baseline`

### Develop

- `/scaffold-skill [plugin|maintenance] <name>`

## Working Guidelines

- **Every claim needs a source.** All research files, documentation, and recommendations must link to verifiable sources.
- **Verify claims before acting on them.** Check git history, inspect actual data. Do not redesign a working system based on theoretical concerns.
- **Use the canonical evidence layer for repo-wide claims.** Classify repository-level statements with [evidence-contract.md](skills/review-claude-config/references/evidence-contract.md) and follow [evidence-maintenance.md](docs/evidence-maintenance.md) for maintenance process.
- **Iterate reviews until convergence.** Address findings, then re-review. Medium and High findings block completion.
- **Prefer evidence over rhetoric.** Findings should cite concrete paths, text, or examples.
- **Research before design in novel areas.** Save results in `research/` with sources.
- **Keep project knowledge in the repo.** No reliance on external memory.

## Development Conventions

- Language: English
- Reference file budgets: rubric `<1K`, baseline `<2K`, all others `<=500` tokens
- Treat exact thresholds and workflow conventions as `Repo default` unless stronger evidence exists
- Domain cache refresh discipline follows the repo's 90-day cadence
- WebFetch is optional; skills must degrade gracefully to WebSearch-only when needed
- Baseline updates happen only through `/refresh-engineering-baseline`
- Baseline refresh covers only `Prompt Engineering`, `Context Engineering`, and `Tool Design`
- Artifact identity is `type + path`; analytics series identity is `generated_by + type + path`; `name` is display-only
- Commit format: `type(scope): description`
- Audit-fix chain: commit review report first, then commit fixes
- Review, suggest, and audit skills are read-only on analyzed files except for reports and domain cache
- Apply skills and `scaffold-skill` modify files and require confirmation gates

## Research References

- [Evidence Contract](skills/review-claude-config/references/evidence-contract.md) — canonical claim classes and source precedence
- [Evidence Maintenance Guide](docs/evidence-maintenance.md) — evidence-layer maintenance process
- [Review Report Contract](skills/review-claude-config/references/review-report-contract.md) — canonical review/report contract
- [Source Quality Criteria](skills/review-claude-config/references/source-quality-criteria.md) — research filtering and cross-validation
- [Engineering Baseline](skills/review-claude-config/references/engineering-baseline.md) — prompt/context/tool design baseline
- [Scientific Research Dossier](docs/scientific-research-dossier.md) — repo-level evidence synthesis and theme matrix
- [Claude Code Skill and Agent Format Conventions](research/claude-code/skill-agent-format-conventions.md) — frontmatter, body, safety
- [Prompt Engineering Techniques: Evidence-Based Summary](research/prompt-engineering/prompt-engineering-techniques.md) — evidence-backed techniques
- [Context Engineering: Overview and Industry Adoption](research/context-engineering/context-engineering-overview.md) — principles, context rot, ACE
- [Effective Context Engineering for AI Agents](research/context-engineering/anthropic-effective-context-engineering.md) — official guidance
- [Context Engineering for AI Agents: Lessons from Building Manus](research/context-engineering/manus-context-engineering-lessons.md) — KV-cache, error preservation
- [Writing Effective Tools for AI Agents](research/tool-design/anthropic-writing-tools-for-agents.md) — tool design best practices
- [Equipping Agents for the Real World with Agent Skills](research/agent-skills/anthropic-equipping-agents-with-skills.md) — progressive disclosure
- [Domain Knowledge Impact on LLM Agent Quality](research/domain-knowledge/domain-knowledge-impact-on-quality.md) — 30-206% quality improvement
- [Engineering Documentation Best Practices](research/documentation/engineering-documentation-best-practices.md) — rationale, hyperlinks
- [LLM Agent Caching and Knowledge Persistence Patterns](research/agent-knowledge-caching/llm-agent-caching-patterns.md) — file-based memory, CAG vs RAG
- [Web Content Scraping Tools for LLM Agents](research/web-scraping/web-content-scraping-tools.md) — WebFetch, Jina, Firecrawl
- [Skill Gap Detection for LLM Agent Skills](research/skill-gap-detection/skill-gap-detection-approaches.md) — extraction criteria
- [Repo Readiness Frameworks for AI Coding Assistants](research/repo-static-analysis/repo-readiness-frameworks.md) — static analysis frameworks
- [Context Window Optimization for AI Coding Assistants](research/token-efficiency/context-window-optimization.md) — context rot, token density
- [Architecture Pattern Recognition from Repository Structure](research/architecture-detection/architecture-pattern-recognition.md) — hybrid detection
- [Error Class to Primitive Mapping for AI Coding Assistants](research/primitive-derivation/error-class-to-primitive-mapping.md) — IFScale, error taxonomy
- [Systematische Claude Code Optimierung für unbekannte Repositories](research/repo-audit/repo-audit-methodology.md) — 6-phase primitive derivation
- [Command Naming Conventions: Evidence-Based Findings](research/command-naming/command-naming-conventions.md) — CLI, slash command, plugin naming patterns
- [Web Research Quality Evaluation](research/source-quality/web-research-quality-evaluation.md) — CRAAP, E-E-A-T, credibility assessment
- [Change Discipline Workflow Research](research/change-discipline/change-discipline-workflow-research.md) — multi-perspective review, LLM self-review blindspots

## Change Discipline

Change Discipline Rule ([docs/change-discipline-rule.md](docs/change-discipline-rule.md)) — mandatory plan→review→implement→review→commit; **subagent must receive plan+CLAUDE.md+research+target files+checklist** before any plan approval. Zero Medium findings before commit. Applies to all changes: skills, agents, rules, code, docs.

## Research Backlog

[Research Backlog](docs/research-backlog.md) — 5 deep research topics for review suite quality gaps (autonomous reliability, dependency integrity, instruction following at scale, tool least-privilege, low-evidence baseline refresh).

## Manual Regression Cases

Use [Review Eval Cases](docs/review-eval-cases.md) after changing the rubric, baseline, review prompts, analytics conventions, or scaffold workflow.
