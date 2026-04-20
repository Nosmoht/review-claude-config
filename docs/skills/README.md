# Skill & Hook Documentation

System map for the plugin's skills and hooks. Use this page for component inventory, workflow chains, and compact comparisons. Detailed behavior for a specific command lives in its own page.

## Quick Reference

| Component | Type | Command / Event | Mode |
|-----------|------|-----------------|------|
| [review-claude-config](review-claude-config.md) | Review | `/review-claude-config [folder]` | Standalone |
| [review-skill](review-skill.md) | Review | `/review-skill <path>` | Standalone + Orchestrated |
| [review-agent](review-agent.md) | Review | `/review-agent <path>` | Standalone + Orchestrated |
| [review-rule](review-rule.md) | Review | `/review-rule <path>` | Standalone + Orchestrated |
| [review-mcp-server](review-mcp-server.md) | Review | `/review-mcp-server <path>` | Standalone + Orchestrated |
| [review-settings](review-settings.md) | Review | `/review-settings <path>` | Standalone + Orchestrated |
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
| review-session-trace | Runtime | `/review-session-trace <path>` | Standalone |
| classify-trace-errors | Runtime | `/classify-trace-errors <path>` | Standalone |
| audit-policy-compliance | Runtime | `/audit-policy-compliance <path>` | Standalone |
| audit-trust-chain | Runtime | `/audit-trust-chain <path>` | Standalone |
| audit-memory-hygiene | Security | `/audit-memory-hygiene [dir]` | Standalone |
| review-hook | Review | `/review-hook <path>` | Standalone + Orchestrated |
| review-claude-md | Review | `/review-claude-md <path>` | Standalone |
| [hook-skill-quality-gate](hook-skill-quality-gate.md) | Hook | `PreToolUse` | Automatic |
| [hook-session-check](hook-session-check.md) | Hook | `SessionStart` | Automatic |
| hook-audit-logger | Hook | `PostToolUse`, `PostToolUseFailure` | Automatic (async) |
| hook-delegation-tracker | Hook | `SubagentStart`, `SubagentStop` | Automatic (async) |
| hook-session-audit | Hook | `SessionEnd` | Automatic |
| hook-policy-gate | Hook | `PreToolUse` | Automatic (opt-in via policy.json) |

## By Function

- **Review:** `review-claude-config`, `review-skill`, `review-agent`, `review-rule`, `review-hook`, `review-claude-md`, `review-mcp-server`, `review-settings`, `review-analytics`
- **Runtime:** `review-session-trace`, `classify-trace-errors`, `audit-policy-compliance`, `audit-trust-chain`
- **Security:** `audit-memory-hygiene`
- **Fix/Apply:** `apply-review-findings`, `apply-skill-review-findings`, `apply-agent-review-findings`, `apply-rule-review-findings`, `apply-audit-findings`
- **Discovery:** `audit-repo`, `suggest-skills`
- **Development:** `scaffold-skill`, `scaffold-agent`, `scaffold-rule`, `develop-hooks`
- **Maintenance:** `audit-context-budget`, `check-repo-health`, `refresh-engineering-baseline`, `sync-research-index`, `run-eval-cases`, `validate-primitive-dependencies`, `maintain-evidence-layer`
- **Hooks:** `hook-skill-quality-gate`, `hook-session-check`, `hook-audit-logger`, `hook-delegation-tracker`, `hook-session-audit`, `hook-policy-gate`

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

## Multi-Perspective Review Pattern (P1.1 pilot)

`/review-skill` in standalone mode defaults to **three parallel perspective sub-agents** (Clarity, Correctness, Integration) dispatched via the `Agent` tool. Sibling review skills (`/review-agent`, `/review-rule`, `/review-hook`) retain single-perspective dispatch pending pilot convergence.

- **Agents:** `agents/review-perspective-{clarity,correctness,integration}.md` — Haiku-4.5 default, Read/Grep/Glob only (Integration adds WebSearch), `Agent` + `Task*` + `Bash` + `Write` explicitly in `disallowedTools`, `mcpServers: []`, `memory: none`, `permissionMode: default`.
- **Shared prefix** (byte-identical across all 3 perspectives, ~6,100 Opus-4.7 tokens): `scoring-rubric.md` + `engineering-baseline.md` + `source-quality-criteria.md`. Cached under `cache_control` marker 1. Break-even after ~12 hits (Aperant orchestration research).
- **Per-type block** (byte-identical across 3 perspectives for one review type, ~1,850 tokens): `skill-evaluation-guide.md` + `boundary-exemplars.md`. Cached under marker 2.
- **Per-perspective block** (~400 tokens): ownership contract + functional role + output schema reminder. Cached under marker 3.
- **Artifact** (~2–4K tokens, uncached): `## Item Under Review` + full content.
- **Dispatch order:** Clarity synchronous first (primes cache); Correctness + Integration parallel after first-token return. Target cost ≈ 1.3× baseline.
- **Merge:** `scripts/merge_findings.py` applies Layer 0 content-dedup (path + line-range + token-overlap ≥0.80), Layer 1 owner-weighted vote (owner weight 2×), Layers 2–4 (max-severity, lexicographic, manual-review).
- **Escalation:** `scripts/escalation_decision.py` flags `escalation_required: true` on ESC-1..5 triggers. Auto-re-run only on ESC-5 (degraded mode). Users invoke `/review-skill --deep <path>` for Opus-tier escalation on ESC-1/2/3/4.
- **Full spec:** `skills/review-skill/references/perspective-dispatch-protocol.md` and `merge-rules.md`.
