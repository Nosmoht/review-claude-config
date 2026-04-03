# Skill & Hook Documentation

System map for the plugin's skills and hooks. Use this page for component inventory, workflow chains, and compact comparisons. Detailed behavior for a specific command lives in its own page.

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
| [hook-skill-quality-gate](hook-skill-quality-gate.md) | Hook | `PreToolUse` | Automatic |
| [hook-session-check](hook-session-check.md) | Hook | `SessionStart` | Automatic |

## By Function

- **Review:** `review-claude-config`, `review-skill`, `review-agent`, `review-rule`, `review-analytics`
- **Fix/Apply:** `apply-review-findings`, `apply-skill-review-findings`, `apply-agent-review-findings`, `apply-rule-review-findings`, `apply-audit-findings`
- **Discovery:** `audit-repo`, `suggest-skills`
- **Development:** `scaffold-skill`
- **Maintenance:** `check-repo-health`, `refresh-engineering-baseline`, `sync-research-index`
- **Hooks:** `hook-skill-quality-gate`, `hook-session-check`

## Workflow Chains

```
Review Chain:
  /review-claude-config -> /review-skill, /review-agent, /review-rule
  /review-claude-config -> /apply-review-findings, /review-analytics

Apply Chain:
  /apply-review-findings -> /apply-skill-review-findings
                           /apply-agent-review-findings
                           /apply-rule-review-findings

Audit Chain:
  /audit-repo -> /apply-audit-findings -> /scaffold-skill
              -> /suggest-skills

Maintenance Chain:
  hook-session-check -> /refresh-engineering-baseline
  /check-repo-health -> /refresh-engineering-baseline
                     -> /review-claude-config
```

## Mode and Research Summary

| Component | Mode Summary | Research Summary |
|-----------|--------------|------------------|
| `review-claude-config` | Standalone orchestrator | Domain cache + WebSearch/WebFetch coordination |
| `review-skill`, `review-agent`, `review-rule` | Standalone + orchestrated workers | Light domain research |
| `apply-review-findings` and specialized appliers | Standalone orchestrator + orchestrated workers | No web research |
| `audit-repo`, `suggest-skills` | Standalone discovery | Heuristic analysis with optional validation |
| `refresh-engineering-baseline` | Standalone maintenance | Heavy structured research |
| All other skills/hooks | Standalone or automatic | No web research |
