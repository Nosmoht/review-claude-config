# Review Eval Cases

Manual regression cases for the prompt/context-first review flow. Use these when changing the rubric, shared baseline, reviewer prompts, analytics logic, or scaffold workflow.

## Case 1 — Real Issue, Should Be Caught

Artifact: a skill with `Write` in `allowed-tools`, no `disable-model-invocation: true`, vague description, and no output format.

Expected review behavior:
- Surfaces at least one High or Medium finding.
- Includes `Evidence:` tied to the exact text.
- Includes `Validation:` that can be checked by a follow-up review.
- Recommends a concrete rewrite in `Current:`/`Recommended:` format.

## Case 2 — Cosmetic Difference, Should Not Be Overstated

Artifact: a skill with solid workflow and safety, but slightly awkward wording in one sentence.

Expected review behavior:
- Does not invent structural defects.
- Keeps findings Low impact or omits them entirely.
- Avoids claiming that the artifact is unsafe or incomplete without evidence.

## Case 3 — Analytics Rename/Move Candidate

Artifact set: two reports where a primitive disappears at one path and a similar one appears at another path.

Expected analytics behavior:
- Tracks stable items by `type + path`.
- Flags the new path as a rename/move candidate instead of silently merging by `name`.
- Uses `name` as display label only.

## Case 4 — Scaffold Registration Targets

Artifact: `scaffold-skill plugin foo` vs `scaffold-skill maintenance foo`.

Expected scaffold behavior:
- Plugin mode writes under `skills/` and updates only existing command/architecture sections in `README.md` and `CLAUDE.md`.
- Maintenance mode writes under `.claude/skills/` and updates only `CLAUDE.md`.
- Neither mode refers to `## Skills`, `## File Structure`, or `## Installation` as registration targets.

## Case 5 — Reliability Pattern Detection

Artifact: an agent that spawns subagents or calls external dependencies (MCP tools, WebFetch, subprocess tools) with no failure path defined, no stop condition for recursion/retries, and continues execution even when dependencies return stub data or fail silently.

Expected review behavior:
- Surfaces at least one High or Medium finding from Safety dimension citing missing "failure path defined for every external dependency" or missing "stop condition prevents infinite recursion."
- Surfaces at least one High or Medium finding from Completeness dimension citing missing "chain-level completeness" (failure to propagate [INCOMPLETE] or stub-dependency states).
- Includes `Evidence:` tied to exact workflow text showing unchecked dependency calls.
- Includes `Validation:` that can be checked by inspecting failure scenarios or recursion bounds.
- Recommends concrete reliability patterns in `Current:`/`Recommended:` format (circuit breakers, progressive fallback, bounded execution with thresholds/timeouts).
