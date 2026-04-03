# Review Claude Config

Maintainer operating guide for this repository (Clarity, Completeness, Prompt Engineering, Context Engineering, Goal Alignment, Safety, Metadata). Use this file for active repo conventions, command inventory, and maintenance workflow. User-facing orientation lives in [`README.md`](/home/nos-ai/workspace/review-claude-config/README.md). Skill and hook navigation lives in [`docs/skills/README.md`](/home/nos-ai/workspace/review-claude-config/docs/skills/README.md).

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

- **Verify claims before acting on them.** Check the repo, reports, or git history instead of accepting a proposed problem at face value.
- **Use the canonical evidence layer for repo-wide claims.** Classify repository-level statements with [`evidence-contract.md`](/home/nos-ai/workspace/review-claude-config/skills/review-claude-config/references/evidence-contract.md) and follow [`evidence-maintenance.md`](/home/nos-ai/workspace/review-claude-config/docs/evidence-maintenance.md) for maintenance process.
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

- [`skills/review-claude-config/references/evidence-contract.md`](/home/nos-ai/workspace/review-claude-config/skills/review-claude-config/references/evidence-contract.md) - canonical claim classes and source precedence
- [`docs/evidence-maintenance.md`](/home/nos-ai/workspace/review-claude-config/docs/evidence-maintenance.md) - evidence-layer maintenance process
- [`skills/review-claude-config/references/review-report-contract.md`](/home/nos-ai/workspace/review-claude-config/skills/review-claude-config/references/review-report-contract.md) - canonical review/report contract
- [`skills/review-claude-config/references/source-quality-criteria.md`](/home/nos-ai/workspace/review-claude-config/skills/review-claude-config/references/source-quality-criteria.md) - research filtering and cross-validation
- [`skills/review-claude-config/references/engineering-baseline.md`](/home/nos-ai/workspace/review-claude-config/skills/review-claude-config/references/engineering-baseline.md) - prompt/context/tool design baseline
- [`research/claude-code/skill-agent-format-conventions.md`](/home/nos-ai/workspace/review-claude-config/research/claude-code/skill-agent-format-conventions.md)
- [`research/context-engineering/anthropic-effective-context-engineering.md`](/home/nos-ai/workspace/review-claude-config/research/context-engineering/anthropic-effective-context-engineering.md)
- [`research/tool-design/anthropic-writing-tools-for-agents.md`](/home/nos-ai/workspace/review-claude-config/research/tool-design/anthropic-writing-tools-for-agents.md)
- [`research/agent-skills/anthropic-equipping-agents-with-skills.md`](/home/nos-ai/workspace/review-claude-config/research/agent-skills/anthropic-equipping-agents-with-skills.md)
- [`research/domain-knowledge/domain-knowledge-impact-on-quality.md`](/home/nos-ai/workspace/review-claude-config/research/domain-knowledge/domain-knowledge-impact-on-quality.md)
- [`research/source-quality/web-research-quality-evaluation.md`](/home/nos-ai/workspace/review-claude-config/research/source-quality/web-research-quality-evaluation.md)

## Change Discipline

[`docs/change-discipline-rule.md`](/home/nos-ai/workspace/review-claude-config/docs/change-discipline-rule.md) is authoritative for the plan -> review -> implement -> review -> commit sequence and the zero-Medium rule.

## Manual Regression Cases

Use [`docs/review-eval-cases.md`](/home/nos-ai/workspace/review-claude-config/docs/review-eval-cases.md) after changing the rubric, baseline, review prompts, analytics conventions, or scaffold workflow.
