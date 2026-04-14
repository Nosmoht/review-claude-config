---
name: trust-chain-model
description: Trust violation types detectable from audit traces with optional CLAUDE.md enrichment
last_refreshed: 2026-04-14
---

# Trust Chain Model

## Trace-Only Checks (no config needed)

| ID | Check | Heuristic | Severity |
|---|---|---|---|
| TC-1 | Orphan agent | delegation start with no matching stop (same agent_id) | High |
| TC-2 | CWD escape | tool_call.cwd outside delegation.cwd subtree | Medium |
| TC-3 | Depth violation | Delegation depth >3 (configurable) | Medium |
| TC-4 | Re-delegation | delegation stop→start same type, no tool_calls between | Low |
| TC-5 | Tool escalation | Child agent uses L4/L5 tools parent never used | Medium |

## Config-Enriched Checks (optional, requires CLAUDE.md at delegation CWD)

| ID | Check | Heuristic | Severity |
|---|---|---|---|
| TC-6 | Scope violation | Agent used tool not in declared allowed-tools | High |
| TC-7 | Undeclared agent | No agent config found matching agent_type at CWD | Medium |

When CLAUDE.md unavailable: skip TC-6/TC-7, note "config not available" per agent.

## Delegation Tree Reconstruction

1. Extract all delegation entries, group by agent_id
2. Pair start/stop events by agent_id + timestamp ordering
3. Nesting: a start that occurs between another agent's start/stop is a child
4. Depth = max nesting level in tree
