---
name: agent-evaluation-guide
description: Type-specific evaluation criteria for Claude Code agents (single-file .md in agents/ directory)
last_refreshed: 2026-04-08
---

# Agent Evaluation Checklist

Answer EVERY item: PASS | FAIL | NA. No skipping. FAILs map to Dim for scoring.

| ID | Check | Dim |
|----|-------|-----|
| MS-1 | Model matches task complexity (haiku=routing, sonnet=analysis, opus=complex reasoning)? | Meta |
| DA-1 | Description has specific trigger keywords — not generic? | Meta |
| DA-2 | Description narrow enough to avoid false activation on unrelated requests? | CE |
| DA-3 | Description broad enough to catch all legitimate triggers? | CE |
| DA-4 | `<example>` blocks present when trigger conditions are non-obvious? | Compl |
| DA-5 | Body instructions do not redefine or contradict the description's trigger logic? | Meta |
| TC-1 | `<example>` blocks cover all primary use cases? | Compl |
| TC-2 | Negative examples present (when NOT to trigger)? | Compl |
| TC-3 | Agent includes verification criteria or success conditions for its primary output? | Compl |
| TV-1 | Tool array matches tools actually referenced in the body? | Meta |
| TV-2 | No unused tools — tool set matches task archetype per `tool-grant-decision-tree.md` (least-privilege)? | Safety |
| TV-3 | High-risk tool combinations (Tier A/B per `tool-grant-decision-tree.md`) justified if present? | Safety |
| SF-1 | All context self-contained — no external files assumed? | CE |
| SF-2 | Long body uses headings for structure (not dense prose)? | Clarity |
| AP-1 | No model over-provisioned for task complexity (e.g., opus for simple routing)? | Meta |
| AP-2 | No tools copied from another agent without pruning unused ones? | Safety |
| AP-3 | `disable-model-invocation: true` present if user-only invocation is appropriate? | Meta |
| AP-4 | Agent avoids aggressive imperative language (MUST/CRITICAL/ALWAYS) where natural phrasing suffices? Safety/guardrail sections exempted. | PE |
| RL-1 | Termination conditions defined (step limit, timeout, or success criteria)? | Safety |
| RL-2 | Failure paths specified, not just happy path? | Compl |
| RL-3 | Retry/backoff strategy bounded (not infinite)? | Safety |
| RL-4 | Escalation / HITL trigger defined for high-autonomy operations? | Safety |
| RL-5 | State validation or checkpointing for multi-step workflows? | Compl |
| RL-6 | Verification step before declaring success? | Compl |
| RL-7 | Reasoning-action consistency enforced in workflow? | Clarity |
| RL-8 | Role/scope boundaries explicitly stated? | Safety |
| RL-9 | Safety/PII/credential scope constraints present? | Safety |
| RL-10 | Observability hooks or logging specified? | Compl |
