# Skill & Hook Documentation

Process flow documentation for all skills and hooks in the review-claude-config plugin. Each file contains a complete process description, Mermaid flowchart diagram, research behavior details, and reference file inventory.

## Quick Reference

| Component | Type | Command / Event | Mode |
|-----------|------|-----------------|------|
| [review-claude-config](review-claude-config.md) | Review | `/review-claude-config [folder]` | Standalone |
| [review-skill](review-skill.md) | Review | `/review-skill <path>` | Standalone + Orchestrated |
| [review-agent](review-agent.md) | Review | `/review-agent <path>` | Standalone + Orchestrated |
| [review-rule](review-rule.md) | Review | `/review-rule <path>` | Standalone + Orchestrated |
| [review-analytics](review-analytics.md) | Review | `/review-analytics [folder]` | Standalone |
| [apply-review-findings](apply-review-findings.md) | Fix/Apply | `/apply-review-findings [report]` | Standalone |
| [apply-skill-review-findings](apply-skill-review-findings.md) | Fix/Apply | `/apply-skill-review-findings [report]` | Standalone + Orchestrated |
| [apply-agent-review-findings](apply-agent-review-findings.md) | Fix/Apply | `/apply-agent-review-findings [report]` | Standalone + Orchestrated |
| [apply-rule-review-findings](apply-rule-review-findings.md) | Fix/Apply | `/apply-rule-review-findings [report]` | Standalone + Orchestrated |
| [apply-audit-findings](apply-audit-findings.md) | Fix/Apply | `/apply-audit-findings [report]` | Standalone |
| [audit-repo](audit-repo.md) | Discovery | `/audit-repo [folder]` | Standalone |
| [suggest-skills](suggest-skills.md) | Discovery | `/suggest-skills [folder]` | Standalone |
| [scaffold-skill](scaffold-skill.md) | Development | `/scaffold-skill [plugin\|maintenance] <name>` | Standalone |
| [check-repo-health](check-repo-health.md) | Maintenance | `/check-repo-health [all\|freshness\|tokens\|integrity]` | Standalone |
| [refresh-engineering-baseline](refresh-engineering-baseline.md) | Maintenance | `/refresh-engineering-baseline` | Standalone |
| [sync-research-index](sync-research-index.md) | Maintenance | `/sync-research-index [folder]` | Standalone |
| [hook-skill-quality-gate](hook-skill-quality-gate.md) | Hook | PreToolUse: `Edit\|Write\|MultiEdit` | Automatic |
| [hook-session-check](hook-session-check.md) | Hook | SessionStart | Automatic |

## By Function

### Review Skills (read-only analysis)

- [review-claude-config](review-claude-config.md) — Batch audit all skills/agents/rules with per-item quality certificates
- [review-skill](review-skill.md) — Evaluate a single skill across 7 dimensions
- [review-agent](review-agent.md) — Evaluate a single agent with model selection and activation precision checks
- [review-rule](review-rule.md) — Evaluate a single rule across 3 dimensions (Clarity, Completeness, Goal Alignment)
- [review-analytics](review-analytics.md) — Grade trajectories, regression detection, portfolio health dashboard

### Fix/Apply Skills (modify files)

- [apply-review-findings](apply-review-findings.md) — Orchestrator that delegates to type-specific appliers
- [apply-skill-review-findings](apply-skill-review-findings.md) — Apply recommendations to SKILL.md files with skill-specific validation
- [apply-agent-review-findings](apply-agent-review-findings.md) — Apply recommendations to agent files with single-file constraint enforcement
- [apply-rule-review-findings](apply-rule-review-findings.md) — Apply recommendations to rule files with weak-verb and contradiction detection
- [apply-audit-findings](apply-audit-findings.md) — Create CLAUDE.md sections, hooks, and rules from audit reports

### Discovery Skills (read-only analysis)

- [audit-repo](audit-repo.md) — Static analysis for Claude Code primitive needs with intervention matrix
- [suggest-skills](suggest-skills.md) — Two-layer skill gap detection (table matching + open reasoning)

### Development Skills (create files)

- [scaffold-skill](scaffold-skill.md) — Generate new skills from template with interactive requirements gathering

### Maintenance Skills

- [check-repo-health](check-repo-health.md) — Reference freshness, token budgets, and integrity dashboard
- [refresh-engineering-baseline](refresh-engineering-baseline.md) — Update baseline with current web research (6 queries, source quality criteria)
- [sync-research-index](sync-research-index.md) — Detect and fix drift between research/ files and CLAUDE.md references

### Hooks (automatic, event-driven)

- [hook-skill-quality-gate](hook-skill-quality-gate.md) — Injects quality guidelines when editing skill/agent/rule files
- [hook-session-check](hook-session-check.md) — Warns at session start if engineering baseline is stale

## Workflow Chains

The skills form several workflow chains:

```
Review Chain:
  /review-claude-config ──delegates──> /review-skill, /review-agent, /review-rule
  /review-claude-config ──suggests──> /apply-review-findings, /review-analytics

Apply Chain:
  /apply-review-findings ──delegates──> /apply-skill-review-findings
                                        /apply-agent-review-findings
                                        /apply-rule-review-findings

Audit Chain:
  /audit-repo ──suggests──> /apply-audit-findings ──defers──> /scaffold-skill
              ──suggests──> /suggest-skills

Maintenance Chain:
  hook-session-check ──suggests──> /refresh-engineering-baseline
  /check-repo-health ──suggests──> /refresh-engineering-baseline
                     ──suggests──> /review-claude-config
```

## Research Behavior Summary

| Component | Research Level | Details |
|-----------|--------------|---------|
| review-claude-config | Domain cache + WebSearch/WebFetch | Cache-mediated, researcher/consumer roles |
| review-skill | Light (1-2 queries) | Domain best practices for reviewed skill |
| review-agent | Light (1-2 queries) | Domain best practices for reviewed agent |
| review-rule | Light (1-2 queries) | Domain best practices for reviewed rule |
| refresh-engineering-baseline | Heavy (6 queries + 6-9 fetches) | Structured queries with two-tier fetch strategy |
| suggest-skills | Medium (Layer 2 agent) | Open reasoning agent validates with WebSearch |
| audit-repo | Light (optional) | Web validation of top 3 P0 recommendations |
| All other skills/hooks | None | No web research |
