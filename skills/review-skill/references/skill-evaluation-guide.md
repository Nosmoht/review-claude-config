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
| WS-4 | Stop conditions and recovery actions defined? (binary check: CLAR-3 Stop/Recovery — see scoring-rubric.md) | Safety |
| CLAR-3 | Every `stop/abort/refuse/bail/halt/timeout` paired with named recovery target within 200 chars? | Clarity |
| CLAR-4 | Every numbered upstream dependency names a failure branch (inline or cross-reference)? | Clarity |
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
| SP-2b | Per-tool archetype binding (body OR Hard Rules OR referenced policy) for each `allowed-tools` entry? (binary check — see scoring-rubric.md) | Safety |
| SP-4 | High-risk tool combinations (Tier A/B per `tool-grant-decision-tree.md`) justified if present? | Safety |
| SP-4b | For Tier-A combinations: ≥1 constraint sentence per Tier-A tool (location-agnostic)? (binary check — see scoring-rubric.md) | Safety |
| SP-3 | Stop conditions defined for loops or recursive operations? | Safety |
| RL-1 | Termination conditions defined (step limit, timeout, or success criteria)? [Agentic only] | Safety |
| RL-1b | Numeric/enum termination predicate matches one of the RL-1b regex variants? [Agentic only] | Safety |
| RL-3 | Retry/backoff strategy bounded (not infinite)? [Agentic only] | Safety |
| RL-3b | Every retry/regenerate/redisplay/adjust has a numeric cap within 400 chars? [Agentic only] | Safety |
| RL-4 | Escalation / HITL trigger defined for high-autonomy operations? [Agentic only] | Safety |
| RL-4b | ≥1 literal HITL / `status: partial` / `escalate` token present on autonomy paths? [Agentic only] | Safety |
| RL-9 | Safety/PII/credential scope constraints present? [Agentic only] | Safety |
| RL-9b | ≥1 credential-scope rule matches redact/truncate/skip/token-like regex? [Agentic only] | Safety |
| AP-1 | No content inlined that belongs in a `references/` file? | CE |
| AP-2 | No tools in `allowed-tools` unreferenced in the workflow body? | Meta |
| AP-3 | Output format explicitly specified (not relying on implicit model behavior)? | PE |
| AP-4 | Error handling present for tool failures or unavailable tools? | Compl |
| RD-1 | Trigger phrases specific enough — no common user phrases match unintentionally? | Meta |
| RD-2 | Skill explicitly rejects ≥1 out-of-scope scenario? | Meta |
| RD-3 | No overlapping triggers with sibling skills in same plugin directory? (Glob siblings, compare descriptions) | Meta |
| RD-4 | Error handling covers tool unavailability AND unexpected tool output? | Compl |
| RD-5 | Step dependencies explicit — upstream/downstream stated, not just numbered? | Clarity |
| RD-6 | Tool availability validated before first use (probe or fallback, not assumed)? | Safety |
| RT-1 | Optional-dep failure produces fallback output, not abort? [Agentic] | Compl |
| RT-2 | Output template has status token (success/partial/failure)? [Agentic] | PE |
| RT-3 | Numeric cap for ≥1 resource (files, calls, or depth)? [Agentic] | Safety |
| IJ-1 | External input + write tool, no gate? | Safety |
| IJ-1b | Validation regex/allowlist AND write-gate (AskUserQuestion/preview/confirm before Write/Edit) both present? | Safety |

**Severity guidance:** Broken cross-primitive dependencies (missing referenced files, unavailable tools, dangling skill/agent references) are **High** severity findings.

**Finding identity:** Every FAIL must produce a recommendation with `ID: {item}:{path}:{dim}/v1` in the heading.
