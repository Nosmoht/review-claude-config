# Review Skill

Evaluate a single Claude Code skill across the shared review rubric and produce a review certificate plus concrete recommendations.

**Command:** `/review-skill <path-to-SKILL.md>`
**Location:** `skills/review-skill/SKILL.md`
**Type:** Review
**Allowed Tools:** Read, Write, Glob, WebSearch, WebFetch
**Mode Support:** Standalone + Orchestrated

## Purpose

This page documents the behavior that is specific to `review-skill`. Canonical certificate, recommendation, and frontmatter structure live in [`review-report-contract.md`](../../skills/review-claude-config/references/review-report-contract.md). Shared evidence classes and source rules live in the review references.

`review-skill` evaluates one `SKILL.md`, optionally enriches Goal Alignment with light domain research, and returns a structured certificate. In standalone mode it also handles report persistence and the follow-up menu. In orchestrated mode it returns only the structured certificate for `/review-claude-config`.

## Major Phases

1. Detect standalone vs orchestrated mode from the orchestration block.
2. In standalone mode, probe web-tool availability and load shared references.
3. Read the target skill, infer its goal, and synthesize domain expectations.
4. Score all 7 dimensions using the shared rubric plus the skill-specific evaluation guide.
5. Assemble the certificate and, in standalone mode, offer report persistence and follow-up actions.

## Runtime-Specific Behavior

- **Standalone vs orchestrated:** standalone performs tool probes, reference loading, report persistence, and the menu; orchestrated mode skips those and returns only the structured certificate.
- **Safety/Metadata weighting:** if the skill uses `Write`, `Bash`, or `Edit`, Safety becomes 15% and Metadata 5%; otherwise Safety is 10% and Metadata is 10%.
- **Research fallback:** if web tools are unavailable, Goal Alignment falls back to model knowledge and should be marked accordingly.
- **Read-only target:** the reviewed skill file is never modified; standalone mode may write only to `.claude/reviews/`.

## Interactions

- **Called by:** user directly or `/review-claude-config`
- **Uses shared references:** rubric, engineering baseline, and the shared review-report contract
- **Follow-up:** `/apply-skill-review-findings` consumes the saved report

## Hard Rules

- Apply the shared rubric strictly.
- Every High or Medium recommendation needs evidence and a concrete rewrite.
- Present the full certificate before persistence or follow-up actions.
