---
name: perspective-dispatch-protocol
description: Protocol for /review-skill to dispatch 3 perspective sub-agents with KV-cache-friendly shared-prefix construction
last_refreshed: 2026-04-20
---

# Perspective Dispatch Protocol

This file is JIT-loaded by `/review-skill` in multi-perspective (standalone) mode only. Not included in the shared prefix passed to perspective sub-agents.

## Request Structure

Each perspective Agent-tool invocation carries 4 blocks with 3 `cache_control` breakpoints:

| Block | Content | Tokens | Cache breakpoint | Byte-stable across |
|-------|---------|--------|------------------|---------------------|
| 1 Shared prefix | scoring-rubric.md + engineering-baseline.md + source-quality-criteria.md + wrapper | ~6,100 | marker 1 | all review types × all perspectives |
| 2 Per-type block | type-evaluation-guide.md + boundary-exemplars.md | ~1,850 (skill type) | marker 2 | one review type × 3 perspectives |
| 3 Per-perspective block | functional-role preamble + ownership contract + output schema reminder | ~400 | marker 3 | one perspective × multiple artifacts |
| 4 Artifact | `## Item Under Review` label + full artifact content | 2,000–4,000 | uncached | per call |

Total per call ≈ 11–12K Opus-4.7 tokens. Above 4,096 floor for Opus cache, well below context-rot 60% threshold.

## Dispatch Order

1. **Clarity synchronous first.** Launch `Agent(subagent_type="review-perspective-clarity", prompt=<blocks 1+2+3a+4>)` and await first-token return. This primes the shared-prefix cache under breakpoint markers 1 and 2.
2. **Correctness + Integration in parallel.** After Clarity's first-token return, launch two Agent tool calls in the same tool-use batch: `Agent(subagent_type="review-perspective-correctness", prompt=<blocks 1+2+3b+4>)` and `Agent(subagent_type="review-perspective-integration", prompt=<blocks 1+2+3c+4>)`. Both read from the already-primed cache.

Expected KV-cache hit rate: Clarity call 0% (cache write); Correctness + Integration ≥80% on markers 1 and 2.

## Per-Perspective Block Construction

Each block 3 contains:

```
You verify <functional role sentence from agent frontmatter>.

Your ownership (attention-directing, not exclusive):
  Primary focus items: <checklist-id list>
  Primary dimensions (weight 2× in orchestrator merge): <dimension list>

Output contract:
  - Grade all 7 dimensions A–F.
  - For primary-focus FAILs, emit High-severity findings with full Evidence/Why/Validation/Current/Recommended.
  - For non-primary FAILs, emit with `primary_focus: false` and `owner_conflict: true` and `hint_owner: <sibling-perspective>`.
  - Your output is the structured certificate only — no prose preamble or summary.
```

## Certificate Capture

After receiving the 3 Agent-tool return values, `/review-skill` writes each to:
  `$CLAUDE_PLUGIN_DATA/audit/perspectives/<session_id>/<perspective>.json`
using the Write tool (orchestrator-side write, NOT via SubagentStop hook — the hook does not have the return value).

File name is derived strictly from the orchestrator's constants `clarity|correctness|integration` — never from sub-agent output — to prevent path injection.

## Merge + Escalation Invocation

Bash-invoke:
1. `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/merge_findings.py $CLAUDE_PLUGIN_DATA/audit/perspectives/<session_id>` → merged cert JSON.
2. Write merged cert to `$CLAUDE_PLUGIN_DATA/audit/perspectives/<session_id>/merged.json`.
3. `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/escalation_decision.py $CLAUDE_PLUGIN_DATA/audit/perspectives/<session_id>/merged.json [--deep]` → `{escalation_required, reasons}`.

Bash is allowed here because the `policy_gate.py` PreToolUse hook allowlists exactly these two script invocations. All other Bash is denied.

## Output Certificate (Phase 3)

`/review-skill` emits the existing certificate format plus:

```
### Merged Findings
[From merged.json findings — each with finding_id, dimensions multi-tag, severity, perspectives (source list), owner_conflict, hint_owner.]

### Owner-Conflict Signals
[Findings where owner_conflict=true, listed separately from graded findings.]

### Escalation
escalation_required: [true|false]
reasons: [list]
design_deviations:
  - "Escalation is flag-only by default (see DEC-6). Auto-re-run only on ESC-5 (malformed cert). Users invoke /review-skill --deep <path> for Opus escalation on ESC-1/2/3/4."
```

## Legacy Orchestrated Mode

When invoked via `/review-claude-config` with the `---orchestration---` metadata block, `/review-skill` continues to use single-perspective evaluation (legacy behavior). Multi-perspective dispatch is pilot-scoped to standalone mode only. Extending to orchestrated mode is a P1.1b follow-up.
