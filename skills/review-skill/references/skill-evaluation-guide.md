---
name: skill-evaluation-guide
description: Type-specific evaluation criteria for Claude Code skills (SKILL.md files)
last_refreshed: 2026-04-08
---

# Skill Evaluation Checklist

Answer EVERY item: PASS | FAIL | NA. No skipping. FAILs map to Dim for scoring.

| ID | Check | Dim |
|----|-------|-----|
| PD-1 | Stable knowledge in `references/`, not inline? | CE |
| PD-2 | SKILL.md under 500 lines? | CE |
| PD-3 | Supplementary files loaded on-demand (Read), not pre-loaded? | CE |
| PD-4 | Subagent isolation used for complex subtasks? | CE |
| PD-5 | Description contains ≥1 keyword that excludes unrelated requests? | Meta |
| WS-1 | Steps numbered with explicit sequential dependencies? | Clarity |
| WS-2 | Every conditional specifies a concrete trigger (value, threshold, file test, or tool output)? | Clarity |
| WS-3 | Parallel vs sequential steps explicitly marked? | Clarity |
| WS-4 | Stop conditions and recovery actions defined? | Safety |
| RF-1 | Reference files within token budgets? | CE |
| RF-2 | Each reference file is single-purpose? | CE |
| RF-3 | No reference content that could be eliminated without capability loss? | CE |
| AH-1 | `$ARGUMENTS` parsed with validation? | Compl |
| AH-2 | Defaults defined for missing arguments? | Compl |
| AH-3 | Error handling for invalid arguments present? | Compl |
| AH-4 | `argument-hint` accurately describes expected input? | Meta |
| OF-1 | Output format specified with a literal template or example? | PE |
| OF-2 | All output sections/fields defined? | Compl |
| OF-3 | Output format prevents downstream context bloat? | CE |
| OF-4 | Review skills: findings include `Evidence:` and `Validation:`? | PE |
| SP-1 | Confirmation gates before destructive/irreversible operations? | Safety |
| SP-2 | `allowed-tools` matches actual tool usage — tools align with task archetype per `tool-grant-decision-tree.md` (least-privilege)? | Safety/Meta |
| SP-4 | High-risk tool combinations (Tier A/B per `tool-grant-decision-tree.md`) justified if present? | Safety |
| SP-3 | Stop conditions defined for loops or recursive operations? | Safety |
| RL-1 | Termination conditions defined (step limit, timeout, or success criteria)? [Agentic only] | Safety |
| RL-3 | Retry/backoff strategy bounded (not infinite)? [Agentic only] | Safety |
| RL-4 | Escalation / HITL trigger defined for high-autonomy operations? [Agentic only] | Safety |
| RL-9 | Safety/PII/credential scope constraints present? [Agentic only] | Safety |
| AP-1 | No content inlined that belongs in a `references/` file? | CE |
| AP-2 | No tools in `allowed-tools` unreferenced in the workflow body? | Meta |
| AP-3 | Output format explicitly specified (not relying on implicit model behavior)? | PE |
| AP-4 | Error handling present for tool failures or unavailable tools? | Compl |
| RD-1 | Trigger phrases specific enough — no common user phrases match unintentionally? | Meta |
| RD-2 | Skill explicitly rejects ≥1 out-of-scope scenario? | Meta |
| RD-3 | No overlapping triggers with sibling skills in same plugin directory? (Glob siblings, compare descriptions) | Meta |
| RD-4 | Error handling covers tool unavailability AND unexpected tool output? | Compl |
| RD-5 | Step dependencies explicit — upstream/downstream relationships stated, not just numbered? | Clarity |
| RD-6 | Tool availability validated before first use (probe or conditional fallback, not assumed present)? | Safety |

**Severity guidance:** Broken cross-primitive dependencies (missing referenced files, unavailable tools, dangling skill/agent references) are **High** severity findings.

**Finding identity:** Every FAIL must produce a recommendation with `ID: {item}:{path}:{dim}/v1` in the heading.
