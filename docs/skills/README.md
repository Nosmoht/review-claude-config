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
| [audit-context-budget](audit-context-budget.md) | Maintenance | `/audit-context-budget [folder]` | Standalone |
| [suggest-skills](suggest-skills.md) | Discovery | `/suggest-skills [folder]` | Standalone |
| [scaffold-skill](scaffold-skill.md) | Development | `/scaffold-skill [plugin\|maintenance\|external <target-path>] <name>` | Standalone |
| [check-repo-health](check-repo-health.md) | Maintenance | `/check-repo-health [all\|freshness\|tokens\|integrity]` | Standalone |
| [refresh-engineering-baseline](refresh-engineering-baseline.md) | Maintenance | `/refresh-engineering-baseline` | Standalone |
| [sync-research-index](sync-research-index.md) | Maintenance | `/sync-research-index [folder]` | Standalone |
| [scaffold-agent](scaffold-agent.md) | Development | `/scaffold-agent <agent-name>` | Standalone |
| [scaffold-rule](scaffold-rule.md) | Development | `/scaffold-rule <rule-name>` | Standalone |
| [run-eval-cases](run-eval-cases.md) | Maintenance | `/run-eval-cases [all\|N]` | Standalone |
| [validate-primitive-dependencies](validate-primitive-dependencies.md) | Maintenance | `/validate-primitive-dependencies [folder]` | Standalone |
| [develop-hooks](develop-hooks.md) | Development | `/develop-hooks [type] <name>` | Standalone |
| [maintain-evidence-layer](maintain-evidence-layer.md) | Maintenance | `/maintain-evidence-layer [--scope ...]` | Standalone |
| [hook-skill-quality-gate](hook-skill-quality-gate.md) | Hook | `PreToolUse` | Automatic |
| [hook-session-check](hook-session-check.md) | Hook | `SessionStart` | Automatic |

## By Function

- **Review:** `review-claude-config`, `review-skill`, `review-agent`, `review-rule`, `review-analytics`
- **Fix/Apply:** `apply-review-findings`, `apply-skill-review-findings`, `apply-agent-review-findings`, `apply-rule-review-findings`, `apply-audit-findings`
- **Discovery:** `audit-repo`, `suggest-skills`
- **Development:** `scaffold-skill`, `scaffold-agent`, `scaffold-rule`, `develop-hooks`
- **Maintenance:** `audit-context-budget`, `check-repo-health`, `refresh-engineering-baseline`, `sync-research-index`, `run-eval-cases`, `validate-primitive-dependencies`, `maintain-evidence-layer`
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

Development Chain:
  /scaffold-skill, /scaffold-agent, /scaffold-rule -> /review-skill, /review-agent, /review-rule
  /develop-hooks

Validation Chain:
  /audit-repo -> /validate-primitive-dependencies
  /run-eval-cases -> /review-claude-config

Maintenance Chain (additions):
  /maintain-evidence-layer -> /refresh-engineering-baseline
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

## Conventions

**Workflow menus:** Every skill ends with a "What's next?" menu presented via `AskUserQuestion` (header: `"What's next?"`) with action-oriented option labels. Menu is skipped in orchestrated mode and conditionally shown in diagnostic skills (only when issues are found).

**Confirmation gates:** Write-capable skills confirm destructive or irreversible actions via `AskUserQuestion` before proceeding. Use a contextual header and action-oriented option labels. The recommended option is always listed first with a `(Recommended)` annotation.
