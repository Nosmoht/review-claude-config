# Review Eval Cases

Manual regression cases for the prompt/context-first review flow. Use these when changing the rubric, shared baseline, reviewer prompts, analytics logic, or scaffold workflow.

## Defect Annotation Convention

Cases that test finding detection include a `defects:` block listing expected defects. Each defect has `{item, dim, sev, desc}`. Cases testing behavior (not detection) have `defects: N/A`. Clean-artifact cases have `defects: []`. Used by `/run-eval-cases` for FP/FN precision/recall measurement.

## Case 1 — Real Issue, Should Be Caught

Artifact: a skill with `Write` in `allowed-tools`, no `disable-model-invocation: true`, vague description, and no output format.

defects:
- {item: SP-2, dim: Safety, sev: High, desc: "Write without disable-model-invocation"}
- {item: PD-5, dim: Meta, sev: Medium, desc: "Vague description lacks discriminating keywords"}
- {item: OF-1, dim: PE, sev: Medium, desc: "No output format specified"}

Expected review behavior:
- Surfaces at least one High or Medium finding.
- Includes `Evidence:` tied to the exact text.
- Includes `Validation:` that can be checked by a follow-up review.
- Recommends a concrete rewrite in `Current:`/`Recommended:` format.

## Case 2 — Cosmetic Difference, Should Not Be Overstated

Artifact: a skill with solid workflow, correct argument handling, correct tool set, and a clear output format — with only one slightly awkward (but functionally correct) sentence in the workflow body.

defects: []

Expected review behavior:
- Does not invent structural defects.
- Keeps findings Low impact or omits them entirely.
- Avoids claiming that the artifact is unsafe or incomplete without evidence.

## Case 3 — Analytics Rename/Move Candidate

defects: N/A (tests analytics behavior, not finding detection)

Artifact set: two reports where a primitive disappears at one path and a similar one appears at another path.

Expected analytics behavior:
- Tracks stable items by `type + path`.
- Flags the new path as a rename/move candidate instead of silently merging by `name`.
- Uses `name` as display label only.

## Case 4 — Scaffold Registration Targets

defects: N/A (tests scaffold behavior, not finding detection)

Artifact: `scaffold-skill plugin foo` vs `scaffold-skill maintenance foo`.

Expected scaffold behavior:
- Plugin mode writes under `skills/` and updates only existing command/architecture sections in `README.md` and `CLAUDE.md`.
- Maintenance mode writes under `.claude/skills/` and updates only `CLAUDE.md`.
- Neither mode refers to `## Skills`, `## File Structure`, or `## Installation` as registration targets.

## Case 6 — Cross-Run Consistency

defects: N/A (tests cross-run stability, not detection accuracy)

Artifact: a skill with exactly 3 known defects (one each in Clarity, Safety, and Completeness) and 2 clear strengths.

Expected review behavior:
- Two consecutive runs produce the same `finding_id` values for the 3 defects.
- All checklist items have a PASS/FAIL/NA verdict in every run (no blanks).
- Grade variance ≤1 letter in any single dimension (accounts for boundary effects).
- No High/Medium finding in one run absent from the other (finding-level stability).
- Rules always evaluated with all 3 dimensions (never null).
- If Goal Alignment uses the domain cache, justifications reference the same cached evidence in both runs.

## Case 7 — New Checklist Item Discrimination

defects:
- {item: DA-5, dim: Meta, sev: Medium, desc: "Description-body contradiction on trigger logic"}
- {item: TC-3, dim: Compl, sev: Medium, desc: "No verification criteria for primary output"}

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

defects:
- {item: RL-1, dim: Safety, sev: High, desc: "No termination condition for recursion/retries"}
- {item: RL-2, dim: Compl, sev: High, desc: "No failure path for external dependencies"}

Artifact: an agent that spawns subagents or calls external dependencies (MCP tools, WebFetch, subprocess tools) with no failure path defined, no stop condition for recursion/retries, and continues execution even when dependencies return stub data or fail silently.

Expected review behavior:
- Surfaces at least one High or Medium finding from Safety dimension citing missing "failure path defined for every external dependency" or missing "stop condition prevents infinite recursion."
- Surfaces at least one High or Medium finding citing missing chain-level completeness (failure to propagate [INCOMPLETE] or stub-dependency states) — dimension label may be Safety, Completeness, or Workflow.
- Includes `Evidence:` tied to exact workflow text showing unchecked dependency calls.
- Includes `Validation:` that can be checked by inspecting failure scenarios or recursion bounds.
- Recommends concrete reliability patterns in `Current:`/`Recommended:` format (circuit breakers, progressive fallback, bounded execution with thresholds/timeouts).


## Case 8 — Tool Grant Least-Privilege Detection

defects:
- {item: TV-3, dim: Safety, sev: High, desc: "Tier A combinations (Bash+WebFetch, Write+WebFetch) without justification"}
- {item: TV-2, dim: Safety, sev: Medium, desc: "Tool set exceeds read-only analyst archetype"}

Artifact: an agent with the following frontmatter:
```yaml
tools: [Read, Grep, Glob, Bash, Write, WebFetch]
```
And description: "Reads log files and summarizes recurring patterns."

No justification for `Bash`, `Write`, or `WebFetch` anywhere in the body. No `disallowedTools` declared.

Expected review behavior:
- **TV-3 FAIL**: Surfaces a High finding citing Tier A combinations present without documented justification: `Bash`+`WebFetch` (A1), `Write`+`WebFetch` (A3).
- **TV-2 FAIL**: Surfaces a Medium finding that the tool set does not match the read-only analyst archetype (`Read, Grep, Glob` expected for a log summarizer).
- Safety dimension capped at C due to unmitigated Tier A combination.
- Recommendation includes concrete `Current:`/`Recommended:` blocks reducing tools to `[Read, Grep, Glob]` with justification for what would re-admit each removed tool.
- **No false positive on Bash** if the agent description explicitly states "runs shell commands to parse binary log formats" — justification present, Tier A flag should not appear.

## Case 9 — Finding-ID Stability

defects: N/A (tests finding-ID stability, not detection accuracy)

Artifact: same skill reviewed twice without changes.

Expected review behavior:
- Both reports contain `finding_id` values in recommendation headings.
- Every High/Medium finding appears with the same `finding_id` in both runs.
- The finding delta table shows all findings as `recurring` — zero `new`, zero `fixed`.
- `finding_id` format matches `{checklist_item}:{path}:{dimension}/v1`.

## Case 10 — Baseline Version Lock

defects: N/A (tests baseline version handling, not detection)

Artifact: a repo with a prior review report using `baseline_version: 2026-04-04` when the current engineering baseline is `2026-04-08`.

Expected review behavior:
- Reviewer detects the baseline mismatch and presents a choice to the user.
- Report uses the baseline version the user chose (prior or current).
- Report does NOT silently switch to the newer baseline.

## Case 11 — Rule Dimension Completeness

defects: N/A (tests dimension completeness, not detection)

Artifact: a rule file reviewed twice.

Expected review behavior:
- Both reports produce grades for all 3 rule dimensions (Clarity, Completeness, Goal Alignment).
- No dimension is `null` in either report.
- Grade variance ≤1 letter per dimension between runs.

## Case 12 — MCP Server Misconfiguration Detection

defects:
- {item: MC-4, dim: Safety, sev: High, desc: "Hardcoded API key in env"}
- {item: MC-6, dim: Safety, sev: High, desc: "Tier A server without justification"}
- {item: MC-8, dim: Compl, sev: Low, desc: "Stale orphan server entry"}

Artifact: a `.mcp.json` with:
- A hardcoded API key in `env` (`"API_KEY": "sk-live-abc123"`)
- A Tier A server (filesystem write mode) with no justification comment
- A stale orphan server entry (`"old-server": { "command": "removed-tool", "disabled": true }`)

Expected review behavior:
- **MC-4 FAIL (High):** Surfaces hardcoded secret with evidence citing the literal value.
- **MC-6 FAIL (High):** Surfaces unjustified Tier A server. Safety capped at C.
- **MC-8 FAIL (Low):** Surfaces orphan/stale entry.
- Does NOT flag servers that are properly configured with `${VAR}` expansion.

## Case 13 — Clean Settings.json (No False Positives)

defects: []

Artifact: a well-configured `.claude/settings.json` with:
- Valid JSON with `$schema` field
- `permissions.deny` covering `~/.ssh/**`, `~/.aws/**`, `.env`
- No `bypassPermissions`, no `enableAllProjectMcpServers`
- `.claude/settings.local.json` in `.gitignore`

Expected review behavior:
- All checklist items PASS.
- Overall grade A.
- Zero findings (no false positives on well-configured settings).

## Case 14 — Silent Error Swallowing

defects:
- {item: RD-4, dim: Compl, sev: Medium, desc: "No error handling for WebSearch failure"}
- {item: RT-1, dim: Compl, sev: Medium, desc: "No fallback output when upstream data missing"}
- {item: RT-2, dim: PE, sev: Medium, desc: "No status token in output template"}

Artifact: a skill that calls WebSearch in step 2, then uses the results in step 3 to produce a summary. No error handling for WebSearch failure. No conditional path. No indication in the output that data may be missing. The skill produces a "complete" summary even when the search returned nothing.

Expected review behavior:
- **RD-4 FAIL (Medium)**: Surfaces a finding in Completeness citing absent error handling for WebSearch unavailability or unexpected output.
- **RT-1 FAIL (Medium)**: Surfaces a finding in Completeness citing no fallback output — skill produces complete-looking output when upstream data is missing, with no reduced-capability path.
- **RT-2 FAIL (Medium)**: Surfaces a finding in **Prompt Engineering** citing no status token in output template — downstream consumers cannot distinguish sourced from unsourced results.
- Completeness dimension ≤ C due to >25% Completeness FAILs (RD-4 + RT-1 among Compl items).
- Distinct from Case 5: Case 5 tests multi-dependency chain propagation with subagents; Case 14 tests single-tool failure with output that *conceals* the missing data (deceptive completeness vs missing completeness).
- Recommendation includes concrete `Current:`/`Recommended:` blocks showing: (1) conditional check after WebSearch, (2) output status field, (3) fallback output path.

## Case 15 — Circular Delegation

defects:
- {item: SP-3, dim: Safety, sev: High, desc: "No stop condition for recursive delegation"}
- {item: RL-1, dim: Safety, sev: High, desc: "No termination condition — cycle runs indefinitely"}

Artifact: a skill `analyze-deps` whose workflow step 3 says "Spawn the `dep-checker` agent to validate results." The `dep-checker` agent body says "Use /analyze-deps to cross-check findings." This creates a skill→agent→skill cycle with no termination condition.

Expected review behavior:
- **SP-3 FAIL (High)**: Surfaces a High finding in Safety citing missing stop condition for recursive operation — the delegation chain has no depth limit or cycle guard.
- **RL-1 FAIL**: Surfaces a finding citing no termination condition — the cycle can run indefinitely.
- **RT-3 FAIL** (skill) or **RT-4 FAIL** (agent, if reviewing the agent side): Surfaces resource consumption or subagent failure propagation concern.
- Safety dimension capped at C or lower due to unbounded recursion risk.
- Evidence cites the exact text of both the skill's spawn instruction and the agent's cross-check instruction.
- Recommendation includes concrete cycle-breaking pattern: depth counter, seen-set, or explicit "do not re-invoke the parent skill" constraint.

## Case 16 — Unbounded Retry on Flaky MCP Tool

defects:
- {item: RL-1, dim: Safety, sev: High, desc: "No termination condition — unbounded retry loop"}
- {item: RL-2, dim: Compl, sev: Medium, desc: "No failure path when tool never succeeds"}

Artifact: an agent whose workflow says: "Call the `code-search` MCP tool. If it returns an error, retry the call. Continue retrying until the tool returns a valid response."

No maximum retry count. No backoff delay. No timeout. No fallback for persistent failure. Tool description does not guarantee eventual success.

Expected review behavior:
- **RL-1 FAIL (High)**: Surfaces a High finding citing absent termination condition — "continue retrying until" with no bound is an infinite loop.
- **RL-2 FAIL (Medium)**: Surfaces a finding in Completeness citing no failure path — what happens if the tool never succeeds?
- Safety dimension capped at C due to missing High-severity reliability check (RL-1).
- Should NOT require new checklist items to catch — validates that existing RL-1 and RL-2 discriminate correctly against this pattern.
- Distinct from Case 5: Case 5 tests multi-dependency chains with subagents and silent stub-data continuation; Case 16 tests a single explicit retry loop with no bound — a tighter, more mechanical failure mode.
- Recommendation includes bounded retry with exponential backoff, max attempts, and fallback action.

## Case 17 — FP/FN Accuracy on Known-Defect Artifact

defects:
- {item: WS-2, dim: Clarity, sev: Medium, desc: "Conditional uses 'if appropriate' without concrete trigger"}
- {item: SP-2, dim: Safety, sev: High, desc: "Bash in allowed-tools for read-only skill"}
- {item: AH-3, dim: Compl, sev: Medium, desc: "No error for invalid argument format"}

Artifact: a synthetic skill with exactly 3 planted defects (one vague conditional, one overprivileged tool, one missing argument validation) and no other structural issues. Solid output format, clear description, correct reference files.

Expected meta-evaluation behavior:
- C17-1: Precision ≥ 0.75 (at most 1 FP for 3 TP)
- C17-2: Recall ≥ 0.67 (at least 2 of 3 defects found)
- C17-3: No High/Medium finding on a dimension where no defect was planted (no phantom findings in PE, CE, GA, Meta)
- C17-4: Each found defect's `finding_id` contains the correct `checklist_item` prefix

## Case 18 — Convergence Detection Accuracy

defects: N/A (tests analytics convergence detection, not finding detection)

Artifact set: two synthetic review reports for the same skill path:
- Report A: finding_ids `[WS-2:path:Clarity/v1, SP-2:path:Safety/v1]`, grades Clarity=C, Safety=C
- Report B: finding_ids `[WS-2:path:Clarity/v1, AH-3:path:Compl/v1]`, grades Clarity=C, Safety=B

Expected analytics behavior:
- C18-1: Analytics View 4 identifies `SP-2` as `fixed` and `AH-3` as `new`
- C18-2: `WS-2` classified as `recurring`
- C18-3: Convergence verdict is "Not converged" (SP-2 differs between reports)
- C18-4: Grade variance for Safety reported as 1 (C→B)
