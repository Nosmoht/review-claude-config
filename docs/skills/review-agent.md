# Review Agent

Evaluate a single Claude Code agent across the shared review rubric with agent-specific checks for activation precision, examples, and model selection.

**Command:** `/review-agent <path-to-agent.md>`
**Location:** `skills/review-agent/SKILL.md`
**Type:** Review
**Allowed Tools:** Read, Write, Glob, WebSearch, WebFetch
**Mode Support:** Standalone + Orchestrated

## Purpose

This page keeps the agent-specific behavior that is not obvious from the shared contracts. Canonical review output lives in [`review-report-contract.md`](/home/nos-ai/workspace/review-claude-config/skills/review-claude-config/references/review-report-contract.md).

`review-agent` treats agents as single-file primitives. That means Context Engineering focuses on activation precision, Completeness checks `<example>` coverage, and Metadata validates model/tool selection against the task.

## Major Phases

1. Detect standalone vs orchestrated mode.
2. In standalone mode, probe tool availability and load the shared references plus the agent evaluation guide.
3. Read the target agent, infer its goal, and gather light domain expectations.
4. Score the 7 dimensions using the shared rubric plus agent-specific checks.
5. Return the structured certificate, and in standalone mode offer report persistence and next actions.

## Runtime-Specific Behavior

- **Standalone vs orchestrated:** standalone owns probes, persistence, and menu handling; orchestrated mode returns only the certificate.
- **Agent-specific checks:** evaluate `model`, `tools`, `description`, and optional `<example>` blocks for activation precision and coverage.
- **Single-file constraint:** if the content would benefit from extracted reference material, recommendations may suggest conversion to a skill rather than a larger agent.
- **Safety/Metadata weighting:** write-capable tool sets shift the Safety and Metadata weights just like the other 7-dimension reviewers.

## Interactions

- **Called by:** user directly or `/review-claude-config`
- **Uses shared references:** rubric, engineering baseline, and review-report contract
- **Follow-up:** `/apply-agent-review-findings` consumes the saved report

## Hard Rules

- Never modify the analyzed agent.
- Use the shared rubric as the primary grading basis.
- Every High or Medium recommendation must include evidence and a concrete rewrite when one is feasible.
