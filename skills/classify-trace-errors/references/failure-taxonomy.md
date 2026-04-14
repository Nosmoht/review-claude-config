---
name: failure-taxonomy
description: MAST failure modes mapped to trace detection heuristics for runtime error classification
last_refreshed: 2026-04-14
---

# Failure Taxonomy Codebook

MAST failure modes (arXiv 2503.13657) mapped to trace detection patterns.

## FC1 — Specification/Design

| Code | Name | Heuristic | Sev |
|---|---|---|---|
| FM-1.1 | Disobey task spec | Tool targets path outside stated scope | H |
| FM-1.2 | Disobey role spec | Tool not in declared allowed-tools | H |
| FM-1.3 | Step repetition | Same tool+input ≥3 consecutive | M |
| FM-1.4 | Context loss | Compaction + duplicate pattern within 5 turns | M |
| FM-1.5 | No termination | >200 tool calls, no stop signal | H |

## FC2 — Misalignment

| Code | Name | Heuristic | Sev |
|---|---|---|---|
| FM-2.1 | Conversation reset | Delegation stop→start same type, no tool calls between | M |
| FM-2.3 | Task derailment | >30% tool calls outside dominant tool pattern | M |
| FM-2.6 | Reasoning mismatch | Thinking names tool A, next call is tool B | M |

## FC3 — Verification/Termination

| Code | Name | Heuristic | Sev |
|---|---|---|---|
| FM-3.1 | Premature termination | Last tool_use has no matching tool_result | H |
| FM-3.2 | No verification | Write/Edit with no Read/Grep within 5 turns | M |
| FM-3.3 | Wrong verification | Post-Write Read targets different path | M |

## Output Schema

```json
{"code": "FM-1.3", "name": "Step repetition", "severity": "M", "count": 3, "evidence": {"line": 142, "excerpt": "..."}, "category": "FC1"}
```
