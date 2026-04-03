# apply-review-findings

Orchestrate fixes from a review report by parsing findings, separating dispatchable vs manual-only work, and delegating edits to the specialized appliers.

## Overview

| Property | Value |
|----------|-------|
| **Name** | apply-review-findings |
| **Location** | `skills/apply-review-findings/SKILL.md` |
| **Type** | Fix/Apply (Orchestrator) |
| **Allowed Tools** | Agent, Read, Edit, Glob, Bash |
| **disable-model-invocation** | true |
| **Argument Hint** | `[report-path]` |
| **Mode** | Standalone only |
| **Research Behavior** | None |

## Purpose

`apply-review-findings` owns report discovery, report parsing, dispatchability classification, delegation to the type-specific appliers, and the commit workflow. Canonical report structure lives in [`review-report-contract.md`](/home/nos-ai/workspace/review-claude-config/skills/review-claude-config/references/review-report-contract.md); this page documents only the orchestrator behavior that is specific to the apply flow.

## Major Phases

1. Locate the review report from the argument or newest matching file.
2. Parse frontmatter and recommendation sections using the shared contract, with legacy tolerance for older report shapes.
3. Separate findings into dispatchable work and manual-only follow-up.
4. Present the actionable summary, then delegate per type to the specialized appliers.
5. Aggregate results and manage the audit-fix commit chain.

## Runtime-Specific Behavior

- **Manual-only preservation:** findings without safe `Current` / `Recommended` anchors stay visible as manual follow-up items and are never silently dropped.
- **Low-only path:** if no High or Medium dispatchable findings remain, manual-only items are shown first, then the optional Low-impact pass is offered.
- **Type routing:** dispatchable items are grouped by the `summary.type` field and sent only to the matching specialized applier.
- **Legacy compatibility:** historical reports may use shallower headings or omit some modern recommendation fields; parsing remains tolerant enough for classification and visibility.
- **Scope restriction:** only files listed in the report summary are eligible for delegated edits.

## Interactions

- **Delegates to:** `/apply-skill-review-findings`, `/apply-agent-review-findings`, `/apply-rule-review-findings`
- **Consumes:** reports from `/review-claude-config`, `/review-skill`, `/review-agent`, `/review-rule`
- **Follow-up:** the final menu points back to the matching review command

## Hard Rules

- Never create or delete files directly in this orchestrator.
- Never dispatch a finding that lacks safe rewrite anchors.
- Keep report-first then fix-commit ordering in the commit workflow.
