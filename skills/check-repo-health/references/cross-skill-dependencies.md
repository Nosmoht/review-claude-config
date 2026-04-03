---
name: cross-skill-dependencies
description: Registry of known cross-skill file dependencies for deterministic integrity checking
---

Update when adding skills with cross-skill dependencies. Heuristic scan (5c-ii) flags undocumented references.

| Source | Target | Severity |
|--------|--------|----------|
| review-skill | skills/review-claude-config/references/scoring-rubric.md | fatal |
| review-skill | skills/review-claude-config/references/engineering-baseline.md | fatal |
| review-skill | skills/review-claude-config/references/review-report-contract.md | fatal |
| review-agent | skills/review-claude-config/references/scoring-rubric.md | fatal |
| review-agent | skills/review-claude-config/references/engineering-baseline.md | fatal |
| review-agent | skills/review-claude-config/references/review-report-contract.md | fatal |
| review-rule | skills/review-claude-config/references/scoring-rubric.md | fatal |
| review-rule | skills/review-claude-config/references/engineering-baseline.md | fatal |
| review-rule | skills/review-claude-config/references/review-report-contract.md | fatal |
| review-claude-config | skills/review-skill/SKILL.md | warn |
| review-claude-config | skills/review-skill/references/skill-evaluation-guide.md | warn |
| review-claude-config | skills/review-agent/SKILL.md | warn |
| review-claude-config | skills/review-agent/references/agent-evaluation-guide.md | warn |
| review-claude-config | skills/review-rule/SKILL.md | warn |
| review-claude-config | skills/review-rule/references/rule-evaluation-guide.md | warn |
| review-claude-config | skills/review-claude-config/references/engineering-baseline.md | fatal |
| review-claude-config | skills/review-claude-config/references/source-quality-criteria.md | fatal |
| review-claude-config | skills/review-claude-config/references/review-report-contract.md | fatal |
| review-claude-config | skills/review-claude-config/references/domain-cache/INDEX.md | skip |
| audit-repo | skills/suggest-skills/references/signal-catalog.md | fatal |
| audit-repo | skills/review-claude-config/references/evidence-contract.md | warn |
| audit-repo | skills/review-claude-config/references/source-quality-criteria.md | warn |
| suggest-skills | skills/review-claude-config/references/domain-cache/INDEX.md | skip |
| suggest-skills | skills/review-claude-config/references/evidence-contract.md | warn |
| suggest-skills | skills/review-claude-config/references/source-quality-criteria.md | warn |
| apply-review-findings | skills/review-claude-config/references/review-report-contract.md | fatal |
| apply-skill-review-findings | skills/apply-review-findings/references/commit-conventions.md | warn |
| apply-skill-review-findings | skills/review-claude-config/references/review-report-contract.md | fatal |
| apply-agent-review-findings | skills/apply-review-findings/references/commit-conventions.md | warn |
| apply-agent-review-findings | skills/review-claude-config/references/review-report-contract.md | fatal |
| apply-rule-review-findings | skills/apply-review-findings/references/commit-conventions.md | warn |
| apply-rule-review-findings | skills/review-claude-config/references/review-report-contract.md | fatal |
| apply-audit-findings | skills/apply-review-findings/references/commit-conventions.md | fatal |
| refresh-engineering-baseline | skills/review-claude-config/references/engineering-baseline.md | fatal |
| refresh-engineering-baseline | skills/review-claude-config/references/evidence-contract.md | fatal |
| refresh-engineering-baseline | skills/review-claude-config/references/source-quality-criteria.md | fatal |
| review-analytics | skills/review-claude-config/references/review-report-contract.md | fatal |
| review-analytics | skills/review-analytics/references/report-schema.md | warn |
| review-skill | skills/review-claude-config/references/source-quality-criteria.md | warn |
| review-agent | skills/review-claude-config/references/source-quality-criteria.md | warn |
| review-rule | skills/review-claude-config/references/source-quality-criteria.md | warn |
