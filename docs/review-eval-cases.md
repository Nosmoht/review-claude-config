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

Artifact: a skill with solid workflow, correct argument handling, correct tool set, and a clear output format — with only one slightly awkward (but functionally correct) sentence in the workflow body.

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

## Case 6 — Cross-Run Consistency

Artifact: a skill with exactly 3 known defects (one each in Clarity, Safety, and Completeness) and 2 clear strengths.

Expected review behavior:
- Two consecutive runs on the same unchanged file produce the same set of findings: same dimensions flagged, same defects identified.
- All 27 checklist items (PD-1 through AP-4) have a PASS/FAIL/NA verdict in every run.
- Grade variance across runs is zero for all dimensions.
- If Goal Alignment uses the domain cache, justifications reference the same cached evidence in both runs.

## Case 7 — New Checklist Item Discrimination

Artifact: a synthetic agent with these specific properties:
- Description says "Use when user asks to audit dependencies" but body says "Activate when the user wants to check code quality" — a description-body contradiction.
- No verification criteria or success conditions for its primary output anywhere in the body.
- One MUST in a safety-critical guardrail section: "You MUST NOT modify files outside the target directory."

Expected review behavior:
- **DA-5 FAIL**: Surfaces a Medium or High finding in Metadata citing the contradiction between description trigger logic ("audit dependencies") and body activation framing ("check code quality").
- **TC-3 FAIL**: Surfaces a finding in Completeness citing absent verification criteria or success conditions.
- **AP-4 PASS**: Does NOT flag the MUST in the safety guardrail section — the safety/guardrail exemption applies.
- **Existing items unaffected**: DA-1 through DA-4, TC-1, TC-2, AP-1 through AP-3 and all other existing checks do not regress.
- Overall grade reflects new FAIL findings without dropping more than one letter grade below what the structural quality alone would produce.

## Case 5 — Reliability Pattern Detection

Artifact: an agent that spawns subagents or calls external dependencies (MCP tools, WebFetch, subprocess tools) with no failure path defined, no stop condition for recursion/retries, and continues execution even when dependencies return stub data or fail silently.

Expected review behavior:
- Surfaces at least one High or Medium finding from Safety dimension citing missing "failure path defined for every external dependency" or missing "stop condition prevents infinite recursion."
- Surfaces at least one High or Medium finding citing missing chain-level completeness (failure to propagate [INCOMPLETE] or stub-dependency states) — dimension label may be Safety, Completeness, or Workflow.
- Includes `Evidence:` tied to exact workflow text showing unchecked dependency calls.
- Includes `Validation:` that can be checked by inspecting failure scenarios or recursion bounds.
- Recommends concrete reliability patterns in `Current:`/`Recommended:` format (circuit breakers, progressive fallback, bounded execution with thresholds/timeouts).
