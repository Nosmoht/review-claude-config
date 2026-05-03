---
name: cross-skill-dependencies
description: Cross-skill dependency registry
last_refreshed: 2026-05-03
---

**Base:** `skills/review-claude-config/references/`

`skills/` prefix = full path; else prepend Base.
Severity: `!`=fatal `?`=warn `-`=skip

| Source | Target | S |
|--------|--------|---|
| review-skill,review-agent,review-rule,check-repo-health | scoring-rubric.md | ! |
| review-skill,review-agent,review-rule,review-claude-config,refresh-engineering-baseline | engineering-baseline.md | ! |
| review-skill,review-agent,review-rule,review-claude-config,apply-review-findings,apply-skill-review-findings,apply-agent-review-findings,apply-rule-review-findings,review-analytics,check-repo-health | review-report-contract.md | ! |
| review-claude-config | skills/review-skill/SKILL.md | ? |
| review-claude-config | skills/review-skill/references/skill-evaluation-guide.md | ? |
| review-claude-config | skills/review-agent/SKILL.md | ? |
| review-claude-config | skills/review-claude-config/references/agent-evaluation-guide.md | ? |
| review-claude-config | skills/review-rule/SKILL.md | ? |
| review-claude-config | skills/review-rule/references/rule-evaluation-guide.md | ? |
| review-claude-config,suggest-skills,review-skill,review-agent,review-rule,review-claude-md,review-hook,check-repo-health | domain-cache/INDEX.md (7 universal entries) | - |
| audit-repo | skills/review-claude-config/references/signal-catalog.md | ! |
| audit-repo,suggest-skills | evidence-contract.md | ? |
| refresh-engineering-baseline | evidence-contract.md | ! |
| maintain-evidence-layer,refresh-engineering-baseline | engineering-baseline-provenance.md | ! |
| review-claude-config,refresh-engineering-baseline | source-quality-criteria.md | ! |
| review-agent,review-skill | tool-grant-decision-tree.md | ? |
| audit-repo,suggest-skills,review-skill,review-agent,review-rule | source-quality-criteria.md | ? |
| apply-skill-review-findings,apply-agent-review-findings,apply-rule-review-findings | skills/review-claude-config/references/commit-conventions.md | ? |
| apply-audit-findings | skills/review-claude-config/references/commit-conventions.md | ! |
| review-analytics | skills/review-claude-config/references/report-schema.md | ? |
| apply-review-findings | skills/apply-*-review-findings/SKILL.md | ? |
| all-report-producers,all-report-consumers | repo-identification.md | ! |
