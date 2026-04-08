---
name: agent-evaluation-guide
description: Type-specific evaluation criteria for Claude Code agents (single-file .md in agents/ directory)
last_refreshed: 2026-04-08
---

# Agent Evaluation Checklist

Answer EVERY item: PASS | FAIL | NA. No skipping. FAILs map to Dim for scoring.

| ID | Check | Dim |
|----|-------|-----|
| MS-1 | Model matches task complexity — no over/under-provisioning (haiku=routing, sonnet=analysis, opus=complex reasoning)? | Meta |
| DA-1 | Description has specific trigger keywords — not generic? | Meta |
| DA-2 | Description precision — narrow enough to avoid false activation yet broad enough for all legitimate triggers? | CE |
| DA-4 | `<example>` blocks present when trigger conditions are non-obvious? | Compl |
| DA-5 | Body instructions do not redefine or contradict the description's trigger logic? | Meta |
| TC-1 | `<example>` blocks cover all primary use cases? | Compl |
| TC-2 | Negative examples present (when NOT to trigger)? | Compl |
| TC-3 | Agent includes verification criteria or success conditions for its primary output? | Compl |
| TV-1 | Tool array matches tools actually referenced in the body? | Meta |
| TV-2 | No unused tools — tool set matches task archetype per `tool-grant-decision-tree.md` (least-privilege)? | Safety |
| TV-3 | High-risk tool combinations (Tier A/B) or `mcpServers`/`skills` surface expansions justified if present? (Plugin agents cannot use `mcpServers`.) | Safety |
| SF-1 | All context self-contained — no external files assumed? | CE |
| SF-2 | Long body uses headings for structure (not dense prose)? | Clarity |
| AP-2 | No tools copied from another agent without pruning unused ones? | Safety |
| AP-3 | `disable-model-invocation: true` present if user-only invocation is appropriate? | Meta |
| AP-4 | Agent avoids aggressive imperative language (MUST/CRITICAL/ALWAYS) where natural phrasing suffices. Safety/guardrail sections exempted. | PE |
| RL-1 | Termination conditions defined (step limit, timeout, success criteria, or bounded retry/backoff; `maxTurns` frontmatter satisfies this)? | Safety |
| RL-2 | Failure paths specified, not just happy path? | Compl |
| RL-4 | Escalation / HITL trigger defined for high-autonomy operations? | Safety |
| RL-5 | State validation or checkpointing for multi-step workflows? | Compl |
| RL-6 | Verification step before declaring success? | Compl |
| RL-7 | Reasoning-action consistency enforced in workflow? | Clarity |
| RL-8 | Role/scope boundaries explicitly stated? | Safety |
| RL-9 | Safety/PII/credential scope constraints present? | Safety |
| RL-10 | Observability hooks or logging specified? | Compl |

## Agent Frontmatter (AF)

Each AF item is NA unless its trigger field is present.

| ID | Check | Dim | Trigger |
|----|-------|-----|---------|
| AF-1 | `background`/`isolation` match autonomy level — background agents need `isolation: worktree` or explicit scope constraints? | Safety | `background` or `isolation` |
| AF-2 | `memory` scope (`user`/`project`/`local`) proportional to task? | CE | `memory` |
| AF-3 | `initialPrompt` structured (goal, constraints, references) — not raw user forwarding? | PE | `initialPrompt` |
