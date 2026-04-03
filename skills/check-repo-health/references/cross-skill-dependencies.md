---
name: cross-skill-dependencies
description: Registry of known cross-skill file dependencies for deterministic integrity checking
---

**Base:** `skills/review-claude-config/references/`

Path resolution: targets starting with `skills/` are full paths; others prepend Base.
Severity: `!`=fatal `?`=warn `-`=skip

Update when adding skills with cross-skill dependencies. Heuristic scan (5c-ii) flags undocumented references.

| Source | Target | S |
|--------|--------|---|
| review-skill,review-agent,review-rule | scoring-rubric.md | ! |
| review-skill,review-agent,review-rule,review-claude-config,refresh-engineering-baseline | engineering-baseline.md | ! |
| review-skill,review-agent,review-rule,review-claude-config,apply-review-findings,apply-skill-review-findings,apply-agent-review-findings,apply-rule-review-findings,review-analytics | review-report-contract.md | ! |
| review-claude-config | skills/review-skill/SKILL.md | ? |
| review-claude-config | skills/review-skill/references/skill-evaluation-guide.md | ? |
| review-claude-config | skills/review-agent/SKILL.md | ? |
| review-claude-config | skills/review-agent/references/agent-evaluation-guide.md | ? |
| review-claude-config | skills/review-rule/SKILL.md | ? |
| review-claude-config | skills/review-rule/references/rule-evaluation-guide.md | ? |
| review-claude-config,suggest-skills | domain-cache/INDEX.md | - |
| audit-repo | skills/suggest-skills/references/signal-catalog.md | ! |
| audit-repo,suggest-skills | evidence-contract.md | ? |
| refresh-engineering-baseline | evidence-contract.md | ! |
| review-claude-config,refresh-engineering-baseline | source-quality-criteria.md | ! |
| audit-repo,suggest-skills,review-skill,review-agent,review-rule | source-quality-criteria.md | ? |
| apply-skill-review-findings,apply-agent-review-findings,apply-rule-review-findings | skills/apply-review-findings/references/commit-conventions.md | ? |
| apply-audit-findings | skills/apply-review-findings/references/commit-conventions.md | ! |
| review-analytics | skills/review-analytics/references/report-schema.md | ? |
