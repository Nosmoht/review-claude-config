---
name: run-eval-cases
description: >
  Runs regression test cases to verify review system correctness after changes.
  Use after changing the rubric, baseline, reviewer prompts, analytics, or
  scaffold workflow. Do NOT use to review actual skills — use
  /review-claude-config.
argument-hint: "[case-number|all|case1,case3]"
allowed-tools: Agent, Read, Write, Glob, Edit, Bash
disable-model-invocation: true
---

# Run Eval Cases

You are a regression test runner for the review system. Your job is to load YAML test definitions from `tests/eval_cases/`, execute the named case's sprint-contract dispatch, compare actual output against the criteria declared in the YAML, and report a verdict. Sprint contracts live in YAML — do NOT inline new criteria here.

## Argument Handling

Parse `$ARGUMENTS`:
- Empty or `all` → run every YAML case under `tests/eval_cases/case_*.yaml`
- A digit `1`–`N` → run the case whose `id` ends with `-<n>` or whose filename starts with `case_0n_`
- Comma-separated like `case1,case3` or `1,3` → run every named case

If the argument cannot be parsed as a valid case selection, default to `all` and note the fallback.

## Phase 1 — Setup

### Step 0: Pre-clean eval workspace

Run via Bash: `rm -rf .claude/eval-temp && mkdir -p .claude/eval-temp`

This prevents stale artifacts from prior runs. If the removal fails, report and stop — do not write over potentially important leftover files.

### Step 1: Load case definitions

Glob `tests/eval_cases/case_*.yaml`. For each file matching the argument selection:
1. Read the YAML body
2. Validate it carries `id`, `kind`, `description`, `target_skill`, `sprint_contract`
3. Record `case.execution.dispatch.command` to verify the dispatched skill exists in Step 2

If a referenced fixture path (in `artifacts.*` or `findings_fixture`) does not exist, mark that case BLOCKED with note "fixture path missing: <path>" and continue to the next case.

### Step 2: Verify required skills

For every selected case, Glob the skill referenced by `target_skill` (e.g. `target_skill: review-skill` → `skills/review-skill/SKILL.md`). If a required skill is missing for a selected case, mark that case BLOCKED and continue with remaining cases. If all selected cases are blocked, report and stop.

## Phase 2 — Case Execution

For each selected case, execute the dispatch declared in `case.execution.dispatch` and evaluate the criteria declared in `case.sprint_contract`. The YAML carries the contract verbatim — do not edit it during execution.

### Case kinds

The YAML's `kind` field discriminates execution shape:

- **`detection`** — synthetic defective input → review skill expected to surface the planted defects. Stage `case.artifacts.primary` to a temp path under `.claude/eval-temp/<case-id>/` (Bash `cp`), dispatch `case.execution.dispatch.command <staged-path>`, capture output, evaluate every `sprint_contract[].description` against the captured output (PASS/FAIL with one-sentence excerpt).
- **`clean`** — pristine input → review skill expected to emit zero High/Medium findings. Same staging + dispatch flow as detection. Evaluate sprint_contract against output.
- **`behavior_analytics`** — multi-artifact analytics input → analytics skill exercises diff-tracking heuristics. Stage every entry of `case.artifacts.<name>` to `.claude/eval-temp/`, dispatch `case.execution.dispatch.command .claude/eval-temp/`, evaluate sprint_contract against analytics output.
- **`behavior_scaffold`** — scaffold-induced filesystem changes. Iterate `case.scenarios` (each scenario has `mode` + `name` + `expected_writes_under` + `expected_doc_updates` + `forbidden_doc_targets`). For each scenario:
  1. Read `README.md` + `CLAUDE.md` and store as `<file>_before_<mode>`
  2. Dispatch `/scaffold-skill <mode> <name>` and answer "yes" to all confirmations
  3. Verify `expected_writes_under` exists with the new SKILL.md
  4. Diff `README.md` and `CLAUDE.md` against the stored snapshot — pass entries from `expected_doc_updates`, fail entries that landed under any `forbidden_doc_targets` heading
  5. After verification, ALWAYS run `case.execution.cleanup` regardless of scenario outcome (scaffold writes to shared docs)

If a dispatch agent produces no tool calls within `case.execution.timeout_seconds` or returns an error, mark every sprint_contract criterion FAIL with note "agent timeout or crash" and proceed to the next case. Do not retry.

### Per-case execution recipe

For every case kind:

1. Stage required artifacts (per `kind` rule above).
2. Dispatch the command. Compose the agent prompt as:
   ```
   ---orchestration---
   websearch_available: <case.execution.dispatch.orchestration.websearch_available>
   webfetch_available: <case.execution.dispatch.orchestration.webfetch_available>
   ---
   <case.execution.dispatch.command> <resolved-target-arg>
   ```
   Use the case's `allowed-tools: Read, Glob, Write, Bash, Edit` set on the dispatched Agent.
3. Capture the full output.
4. For each `sprint_contract[].id` + `description`, record PASS/FAIL with a quoted excerpt of the relevant output passage.

## Compaction Checkpoint

After all selected cases have executed, pause and compact context before assembling the final report. Summarise per-case results into a structured intermediate record:

```
Case <id>: <description> — criteria <C-id>: PASS/FAIL, <C-id>: PASS/FAIL, ...
```

## Phase 3 — Cleanup and Report

### Step 1: Remove synthetic artifacts

```bash
rm -rf .claude/eval-temp
```

If the directory does not exist (e.g. all cases were BLOCKED before staging), note that and continue. If removal fails, report which paths remain and need manual cleanup.

### Step 2: Assemble results report

Present the report with the overall verdict first, then per-case details.

```
## Eval Cases Results — YYYY-MM-DD

## Overall: N/M cases passed  [CLEAN — safe to commit] or [REGRESSION DETECTED — do not commit until fixed]

| Case | Description                    | Criteria | Passed | Failed | Verdict     |
|------|--------------------------------|----------|--------|--------|-------------|
| <id> | <description>                  | N        | N      | N      | PASS / FAIL |

## Regression Verdict
[CLEAN — safe to commit] or [REGRESSION DETECTED — do not commit until fixed]

## Detection Accuracy (cases with defects array)

For cases whose YAML has `defects: [<...>]` (not `N/A`, not `[]`), parse `finding_id` from the dispatched skill's recommendation headings. Match `checklist_item` prefix against each defect's `item` field (bidirectional prefix to handle the rubric's `<item>` → `<item>b` migrations like SP-2 → SP-2b):
- **TP** = finding matches a defect by item prefix + dimension (with alias collapsing for "Meta"→"Metadata", "PE"→"Prompt Engineering", "Compl"→"Completeness", etc.)
- **FP** = finding has no matching defect
- **FN** = defect has no matching finding

| Case | Defects | TP | FP | FN | Precision | Recall | F1 |
|------|---------|----|----|----|-----------| -------|----|

Cases with `defects: N/A` show "N/A — tests behavior". Cases with `defects: []` show precision 1.00 if zero High/Medium findings, else flag the FP count.
```

For each FAIL: show the criterion ID, what was expected, what the actual output showed (quote or paraphrase the relevant excerpt), and a `Fix target:` line with the file path and section to edit. Use the `case.fix_target` block from the YAML — `case.fix_target.artifact` for artifact-side fixes, `case.fix_target.reviewer_behavior` for reviewer-skill fixes.

When the dispatched output is correct but the criterion wording is too strict, the fix target is the criterion definition in the case YAML (`tests/eval_cases/<case>.yaml` `sprint_contract[]`). Include both the artifact path and the criterion line reference so the user can navigate directly.

For BLOCKED cases: show which skill or fixture was missing and what it would have tested.

### Step 3: Persist

Confirm via AskUserQuestion (header: "Save report"):
- Option 1 label: "Save report" (Recommended) — description: `"Write to $CLAUDE_PLUGIN_DATA/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-eval-cases.md"`
- Option 2 label: "Skip" — description: `"Discard the report"`

On "Save report": write the report. Use today's date and current time in the filename. If the directory does not exist, create it first.

### Step 4: What's Next

Present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Re-run a specific case" — description: `"Run /run-eval-cases <case-number> to retest a single eval case"`
- Option 2 label: "Review the review system" — description: `"Run /review-claude-config . to audit overall quality"`
- Option 3 label: "Done" (Recommended) — description: `"End the workflow"`

On "Re-run a specific case": invoke `/run-eval-cases` with the specified case number. On "Review the review system": invoke `/review-claude-config .`. On "Done": acknowledge and stop.

## Hard Rules

- **YAML is the source of truth.** Do NOT inline sprint contracts, defects arrays, or synthetic artifact content in this skill body. Add new cases by writing a new `tests/eval_cases/case_<n>_<slug>.yaml` and any required `tests/fixtures/eval/<...>` fixtures.
- **Cleanup runs even on failure.** Delete `.claude/eval-temp/` at the end of Phase 3 regardless of case outcomes. For `behavior_scaffold` cases, run `case.execution.cleanup` immediately after each scenario, BEFORE moving to the next.
- **BLOCKED is not FAIL.** If a required skill or fixture is missing, mark the case BLOCKED, exclude it from the pass/fail count, and report it separately.
- **Stop conditions.** If a Phase 2 dispatch agent fails entirely (crash or error), mark every sprint_contract criterion FAIL for that case, note the error, and continue with the next case. Do not retry.
- **Sprint contracts are fixed.** Do not adjust criteria based on what the review actually produces. Evaluate actual output against the YAML criteria as written.
- **Present all results before asking** about persistence.
- **Scaffold doc revert is mandatory** for `behavior_scaffold` cases. The scaffold writes to shared docs (README.md, CLAUDE.md). Always revert those changes after each scenario, even if criteria passed. Record whether revert succeeded.
