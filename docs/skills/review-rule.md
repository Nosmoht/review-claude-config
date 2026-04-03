# Review Rule

Evaluate a single Claude Code rule across the reduced 3-dimension rule rubric and return a review certificate with concrete recommendations.

**Command:** `/review-rule <path-to-rule.md>`
**Location:** `skills/review-rule/SKILL.md`
**Type:** Review
**Allowed Tools:** Read, Write, Glob, WebSearch, WebFetch
**Mode Support:** Standalone + Orchestrated

## Purpose

Rules are plain Markdown directives, so they do not use the full 7-dimension review surface. This page documents the rule-specific behavior only. Shared report structure still lives in [`review-report-contract.md`](../../skills/review-claude-config/references/review-report-contract.md).

## Major Phases

1. Detect standalone vs orchestrated mode.
2. In standalone mode, probe tool availability and load the shared references plus the rule evaluation guide.
3. Validate that the target looks like a rule rather than a skill or agent.
4. Infer the rule goal, gather light domain context, and score only Clarity, Completeness, and Goal Alignment.
5. Return the certificate, and in standalone mode offer report persistence and follow-up actions.

## Runtime-Specific Behavior

- **3 dimensions only:** rules do not use Prompt Engineering, Context Engineering, Safety, or Metadata; the active dimensions are renormalized to 100%.
- **Type guard:** if the target appears to be a skill or agent, the review stops with a type-mismatch error instead of trying to score it as a rule.
- **Standalone vs orchestrated:** standalone handles probes, persistence, and menu flow; orchestrated mode returns only the structured certificate.
- **Null dimensions in saved reports:** when persisted, non-applicable rubric fields remain intentionally `null`.

## Interactions

- **Called by:** user directly or `/review-claude-config`
- **Uses shared references:** rubric, engineering baseline, and review-report contract
- **Follow-up:** `/apply-rule-review-findings` consumes the saved report

## Hard Rules

- Never modify the analyzed rule.
- Score rules only on Clarity, Completeness, and Goal Alignment.
- Every High or Medium recommendation must include evidence and a concrete rewrite.
