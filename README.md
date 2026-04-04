# Review Claude Config

Evidence-based review plugin for Claude Code skills, agents, and rules.

## What It Is

`review-claude-config` audits Claude Code primitives, produces review reports, helps apply findings, and provides maintenance utilities for the review system itself.

Use this file as the user-facing entrypoint. Maintainer policy lives in [`CLAUDE.md`](/home/nos-ai/workspace/review-claude-config/CLAUDE.md). System documentation lives in [`docs/skills/README.md`](/home/nos-ai/workspace/review-claude-config/docs/skills/README.md).

## Installation

Install as a local Claude Code plugin:

```bash
claude --plugin-dir /path/to/review-claude-config
```

Only local `--plugin-dir` is supported. Marketplace-style installation would make the plugin directory read-only and break domain-cache writes.

> **Self-contained**: All knowledge needed for review, scaffold, and audit quality lives in the repo. External services (KB, web) provide optional enrichment but are not required. Research findings are distilled into `engineering-baseline.md` (review quality) and `skill-agent-format-conventions.md` (scaffold quality) — keep these refreshed after research updates.

Repo-internal maintenance skills can also be copied into a target repo when needed:

```bash
cp -r .claude/skills/refresh-engineering-baseline <target>/.claude/skills/
cp -r .claude/skills/sync-research-index <target>/.claude/skills/
```

## Workflow

### Quality Review

1. Run `/review-claude-config [folder]` for a full portfolio review, or `/review-skill`, `/review-agent`, `/review-rule` for a single item.
2. Apply findings with `/apply-review-findings [report]`.
3. Re-run the relevant review to verify improvements.
4. Use `/review-analytics [folder]` to inspect grade trajectories across review cycles.

### Repo Setup

1. Run `/audit-repo [folder]` to identify missing Claude Code primitives.
2. Apply structural findings with `/apply-audit-findings [report]`.
3. Create missing skills with `/scaffold-skill`.
4. Review the resulting primitives with `/review-claude-config`.

### Skill Discovery

1. Run `/suggest-skills [folder]` for open-ended skill opportunity analysis.
2. Create suggested skills with `/scaffold-skill`.
3. Review the generated skills with `/review-claude-config` or `/review-skill`.

## Command Families

### Review

- Batch review: `/review-claude-config [folder]`
- Single-item review: `/review-skill`, `/review-agent`, `/review-rule`
- Discovery: `/suggest-skills [folder]`, `/audit-repo [folder]`

### Apply

- Review findings: `/apply-review-findings [report]`
- Type-specific appliers: `/apply-skill-review-findings`, `/apply-agent-review-findings`, `/apply-rule-review-findings`
- Audit findings: `/apply-audit-findings [report]`

### Maintain

- Health and analytics: `/check-repo-health`, `/review-analytics`
- Research maintenance: `/sync-research-index`, `/refresh-engineering-baseline`
- Regression testing: `/run-eval-cases [case-number|all]`
- Dependency integrity: `/validate-primitive-dependencies [folder]`

### Develop

- Skill creation: `/scaffold-skill [plugin|maintenance] <name>`
- Agent creation: `/scaffold-agent <agent-name>`
- Rule creation: `/scaffold-rule <rule-name>`
- Hook development: `/develop-hooks [hook-type] <hook-name>`

## Where To Look Next

- [`CLAUDE.md`](/home/nos-ai/workspace/review-claude-config/CLAUDE.md) - maintainer operating guide and authoritative maintainer command inventory
- [`docs/skills/README.md`](/home/nos-ai/workspace/review-claude-config/docs/skills/README.md) - skill and hook index, workflow chains, and system map
- [`docs/evidence-maintenance.md`](/home/nos-ai/workspace/review-claude-config/docs/evidence-maintenance.md) - evidence maintenance policy
- [`docs/scientific-research-dossier.md`](/home/nos-ai/workspace/review-claude-config/docs/scientific-research-dossier.md) - current evidence narrative and open questions
