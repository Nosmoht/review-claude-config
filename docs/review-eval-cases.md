# Review Eval Cases

Regression cases for the prompt/context-first review flow. Use these when changing the rubric, shared baseline, reviewer prompts, analytics logic, or scaffold workflow.

## Source of truth

**Cases C1–C5 are pinned in YAML** under `tests/eval_cases/case_*.yaml`. Each YAML carries the synthetic artifact path, sprint-contract criteria, expected findings, acceptance precision/recall thresholds, dispatch instructions, and fix-target mapping. `/run-eval-cases` reads those YAMLs as its source of truth; `tests/test_eval_cases.py` enforces the schema and replays detection/clean cases against synthesised `findings.json` fixtures programmatically.

| YAML | Kind | Description |
|---|---|---|
| [`case_01_real_issue.yaml`](../tests/eval_cases/case_01_real_issue.yaml) | detection | Real Issue, Should Be Caught |
| [`case_02_cosmetic.yaml`](../tests/eval_cases/case_02_cosmetic.yaml) | clean | Cosmetic Difference, Should Not Be Overstated |
| [`case_03_analytics_rename.yaml`](../tests/eval_cases/case_03_analytics_rename.yaml) | behavior_analytics | Analytics Rename/Move Candidate |
| [`case_04_scaffold_registration.yaml`](../tests/eval_cases/case_04_scaffold_registration.yaml) | behavior_scaffold | Scaffold Registration Targets |
| [`case_05_reliability.yaml`](../tests/eval_cases/case_05_reliability.yaml) | detection | Reliability Pattern Detection |

Cases C6–C18 below remain as narrative specifications — they enumerate gaps that a future YAML migration should close (see issue #22).

## Defect Annotation Convention

Cases that test finding detection include a `defects:` block listing expected defects. Each defect has `{item, dim, sev, desc}`. Cases testing behavior (not detection) have `defects: N/A`. Clean-artifact cases have `defects: []`. Used by `/run-eval-cases` for FP/FN precision/recall measurement.

The C1–C5 narrative sections were removed when those cases moved to YAML. The C6–C18 sections below preserve the narrative format pending a follow-up migration.

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
- Every High/Medium finding **whose `checklist_item` is in the deterministic subset** (see `skills/review-claude-config/references/merge-rules.md` §"Convergence Policy") appears with the same `finding_id` in both runs. Advisory findings may differ.
- The finding delta table shows all deterministic-subset findings as `recurring` — zero `new`, zero `fixed` within the deterministic subset. Advisory `new`/`fixed` entries are tolerated.
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
- Report A: finding_ids `[META-1a:path:Metadata/v1, SP-2:path:Safety/v1]`, grades Metadata=C, Safety=C
- Report B: finding_ids `[META-1a:path:Metadata/v1, AH-2b:path:Safety/v1]`, grades Metadata=C, Safety=B

Both `META-1a`, `SP-2`, and `AH-2b` are in the deterministic subset (binary or narrative-parent), so deltas on them are convergence-blocking under the post-#71 scoped policy.

Expected analytics behavior:
- C18-1: Analytics View 4 identifies `SP-2` as `fixed` and `AH-2b` as `new`.
- C18-2: `META-1a` classified as `recurring`.
- C18-3: Convergence verdict is "Not converged" — `SP-2` differs between reports and is in the deterministic subset (NARRATIVE_PARENT).
- C18-4: Grade variance for Safety reported as 1 (C→B).
- C18-5: If both differing finding_ids were advisory (e.g. `WS-1`, `RF-1`), verdict would be "Converged" under the post-#71 scoped policy. View 4 may still report "Not converged" until the analytics scope filter ships in #72 — see the banner in `skills/review-analytics/SKILL.md` View 4.

## Case 19 — D5 Apply Round-Trip

YAML: [`case_15_apply_round_trip.yaml`](../tests/eval_cases/case_15_apply_round_trip.yaml)

defects:
- {item: SP-2b, dim: Safety, sev: High, desc: "Write in allowed-tools without disable-model-invocation gate"}
- {item: META-2, dim: Metadata, sev: Medium, desc: "Description lacks do-not-use exclusion phrase"}

Fixture: `tests/fixtures/eval/case_15_apply_round_trip.SKILL.md` — a known-bad skill
with exactly two deterministic-subset findings of known impact and known mechanical
fixes. The fixture is otherwise structurally clean (all other binary rubric items are
PASS or NA) so that a correctly-applied fix produces zero new Medium/High findings on
re-review.

Sprint contract:
- **C15-1 (zero remaining original finding_ids):** After `/apply-skill-review-findings`
  fixes SP-2b and META-2, a re-review produces zero remaining instances of the original
  finding_ids (`SP-2b:...:Safety/v1` and `META-2:...:Metadata/v1`).
- **C15-2 (no new Medium/High findings introduced):** Re-review after apply introduces
  no new Medium or High findings — since the fixture is otherwise clean, any new
  Medium/High would be a regression introduced by the fix itself.
- **C15-3 (≤1-letter dimension grade change):** Dimension grade change after apply is
  at most one letter in any single dimension, confirming the fix does not destabilise
  unrelated grades.
- **C15-4 (regression signal):** If a re-review still flags SP-2b or META-2, or
  introduces a new High finding, the apply-findings skill failed to converge — this
  signals a regression in the apply pipeline.

Mechanical fixes:
- **SP-2b:** Add `disable-model-invocation: true` to the fixture's frontmatter.
- **META-2:** Append a `do not use` exclusion clause to the description, e.g.
  "Do not use for read-only audits."

This case is the first to exercise the full D5 round-trip. It is a `kind: detection`
YAML case under `tests/eval_cases/` (not a narrative-only case) and is replayed
programmatically by `tests/test_eval_cases.py`. The live review → apply → re-review
loop is driven by `/run-eval-cases`.

## Case 20 — D8 Analytics Regression

YAML: [`case_16_analytics_regression.yaml`](../tests/eval_cases/case_16_analytics_regression.yaml)

defects: N/A (tests analytics regression detection, not finding detection)

Fixture: `tests/fixtures/analytics-regression/` — three timestamped review reports
for the same artifact (`type: skill`, `path: skills/test-safety-skill/SKILL.md`,
`name: test-safety-skill`) with dates 2026-01-01, 2026-02-01, and 2026-03-01. The
`safety` dimension drops B→C→D (score 82→68→55) across the three reports, while all
other dimensions remain stable at B.

Sprint contract:
- **C16-1 (regression flagged with correct dimension):** `/review-analytics` surfaces
  the `safety` dimension as the dropping axis in the regression report.
- **C16-2 (trajectory direction = Regressing):** The artifact's overall trajectory is
  classified as Regressing or decline — not Stable or Improving.
- **C16-3 (regression signal):** Trajectory drop goes unflagged OR direction is
  inverted (Stable/Improving reported instead of Regressing) — signals a regression
  in the analytics detection logic.

Regression signal: if `/review-analytics` fails to flag the safety dimension drop or
classifies the trajectory as Stable/Improving, the grade-step (C→D) and score-drop
(≥5 points: 68→55) classifier branches have both been bypassed.

This case exercises the analytics trajectory-detection path defined in
`skills/review-analytics/SKILL.md` §4 "Compute trajectories" (Regressing predicate:
latest grade lower than previous report OR score dropped by ≥5).

## Case 21 — D7 Oversized Primitive

(YAML: `tests/eval_cases/case_17_oversized_primitive.yaml`)

defects:
- {item: verbosity-token-density, dim: Context Engineering, sev: Medium, desc: "Skill body ~4200 estimated tokens with repeated prose; exceeds 2× typical reference-file budget"}

Fixture: `tests/fixtures/skill-oversized.md` — a syntactically valid skill with correct
frontmatter (`name`, `description`) but a deliberately verbose, redundant body of
approximately 4200 estimated tokens (chars/4). The body describes a data pipeline
orchestrator with multiple sections that repeat the same policy information (retry
logic appears in Configuration Schema and again in Execution Step 4; error classes
appear in Execution Steps and again in the Error Handling section). The verbosity is
plausibly real — structured prose, not lorem ipsum — so the reviewer has genuine
signal-density concerns to flag.

The verbosity-token-density finding is a **judgment-based finding**, NOT a binary
rubric item (no BINARY_ITEM_IDS predicate). The pytest layer validates the
findings fixture schema and precision/recall internal consistency only. The real
reviewer-judgment assertion is driven by `/run-eval-cases`.

Sprint contract:
- **C21-1:** reviewer flags a Completeness OR Context Engineering finding citing
  token-density / verbosity
- **C21-2:** reviewer does NOT silently accept the oversized skill (no clean pass)
- **C21-3 (regression signal):** review passes the oversized fixture without a
  token-density-related finding — signals that the reviewer is failing to apply
  signal-density heuristics to oversized primitives
