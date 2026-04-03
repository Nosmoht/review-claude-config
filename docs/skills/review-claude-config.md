# Review Claude Config

Batch-audit all Claude Code skills, agents, and rules in a target repo and assemble the results into one portfolio review.

**Command:** `/review-claude-config [folder] [--validation]`
**Location:** `skills/review-claude-config/SKILL.md`
**Type:** Review (Batch Orchestrator)
**Allowed Tools:** Agent, Read, Write, Glob, WebSearch, WebFetch
**Mode Support:** Standalone only

## Purpose

`review-claude-config` is the batch orchestrator. It discovers items under `.claude/`, coordinates shared references and domain cache usage, dispatches the type-specific review workers, and persists the combined report. Canonical report structure lives in [`review-report-contract.md`](../../skills/review-claude-config/references/review-report-contract.md). Evidence classes and source policy live in the shared evidence references.

## Major Phases

1. Probe tool availability and load the shared references.
2. Discover all skills, agents, and rules in the target repo.
3. Coordinate domain-cache lookup and researcher/consumer assignment.
4. Dispatch review workers by type in bounded parallel batches.
5. Present the combined results, optionally persist domain-cache updates, and write the aggregate report.

## Runtime-Specific Behavior

- **Discovery:** discovery runs through a sub-agent with read-only tools and supports monorepos while excluding generated/vendor paths.
- **Domain-cache coordination:** cache matching, freshness checks, and one-researcher-per-domain assignment are repo defaults for reuse and consistency, not claims of settled optimal caching science.
- **Research gating:** domain-cache persistence is allowed only when at least one live web tool is available; model-only runs never write new cache entries.
- **Batching:** worker dispatch happens in bounded parallel batches with type-shared prefixes to improve cache efficiency.
- **Large portfolio output:** the saved report may condense high-performing items while still preserving the frontmatter summary for analytics.
- **Validation mode:** `--validation` is a bounded release/CI path. It disables live web research and domain-cache writes, analyzes at most 3 deterministic sample items, skips report persistence, and prints only a concise validation summary. Normal portfolio review behavior remains unchanged.

## Interactions

- **Calls:** `/review-skill`, `/review-agent`, `/review-rule` in orchestrated mode
- **Shares references with workers:** rubric, engineering baseline, evidence contract, source-quality criteria, review-report contract
- **Follow-up:** menus lead to `/apply-review-findings` and `/review-analytics`

## Hard Rules

- Never modify analyzed `.claude/` files directly.
- Keep domain-cache updates explicit and user-confirmed.
- Continue the batch even when an individual worker fails; surface the error in the report.
