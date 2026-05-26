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

Resolve `<repo-slug>` by running `bash bin/repo-slug.sh "$(pwd)"` and capturing stdout. (For documentation reference only, not the operational source-of-truth: `references/repo-identification.md` describes the sanitize algorithm.)

Confirm via AskUserQuestion (header: "Save report"):
- Option 1 label: "Save report" (Recommended) — description: `"Write to ${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-eval-cases.md"`
- Option 2 label: "Skip" — description: `"Discard the report"`

On "Save report": write the report. Use today's date and current time in the filename. If the directory does not exist, create it first.

### Step 4: What's Next

Present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Re-run a specific case" — description: `"Run /run-eval-cases <case-number> to retest a single eval case"`
- Option 2 label: "Review the review system" — description: `"Run /review-claude-config . to audit overall quality"`
- Option 3 label: "Done" (Recommended) — description: `"End the workflow"`

On "Re-run a specific case": invoke `/run-eval-cases` with the specified case number. On "Review the review system": invoke `/review-claude-config .`. On "Done": acknowledge and stop.

## Quality measurement (mandatory before Output)

Per `docs/skill-verification-architecture.md` (2026-05-26 retrofit), MAINTAIN-class verification is deterministic: schema invariants (closed-set verdict vocab, YAML required-field set), idempotency `f(f(x)) == f(x)` (re-running the same case selection on unchanged input produces identical Verdict/Passed/Failed columns), and roster-coverage predicates fully cover this skill's failure surface. There is no judgment-shaped output to evaluate, so the historical Layer B (adversarial critic) and Layer C (binary rubric) were dropped — they added token cost and false-positive surface without raising assurance. Layer A below is the complete verification.

This skill produces per-case PASS / FAIL / BLOCKED verdicts (chat output + ephemeral `.claude/eval-temp/` working files) with no persistent repo mutation outside that workspace. Layer A idempotency must allow `.claude/eval-temp/` deltas (the workspace is rebuilt every run) but require identical case-verdict rows.

Capture the per-case verdict roster the skill just produced (and, if available, the prior-run roster) to a tempdir so subsequent steps can read both deterministically:

```bash
TMPDIR=$(mktemp -d -t rec-XXXX)
CURRENT="$TMPDIR/current-roster.md"
# Write the per-case verdict table (one row per case, columns: Case | Description | Criteria | Passed | Failed | Verdict)
# to "$CURRENT". If a prior-run roster snapshot exists, export PRE_VERDICT=<path>;
# otherwise leave unset and the row-count-delta SOFT row is skipped.
CASE_DIR="tests/eval_cases"   # YAML case definitions
```

### Layer A — mechanical invariants (deterministic, fail-fast)

Run against the produced per-case roster, the YAML case directory, the prior-run roster snapshot (if any), and a second invocation of the same case selection on unchanged input. `STRICT` rows abort; `SOFT` rows warn and continue.

```bash
python3 - "$CURRENT" "$CASE_DIR" "${PRE_VERDICT:-/dev/null}" <<'PY'
import sys, re, os
from pathlib import Path

CURRENT, CASE_DIR, PRE_VERDICT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])

VERDICT_STATUSES = {"PASS", "FAIL", "BLOCKED", "SKIPPED"}
REQUIRED_FIELDS = {"id", "kind", "description", "target_skill", "sprint_contract"}

text = CURRENT.read_text(errors="ignore")
rows = []  # (sev, metric, before, after, delta, flag)

# STRICT-1 VERDICT_STATUS_VOCAB — every Verdict cell uses a token in the closed set
verdict_cells = re.findall(r"\|\s*(PASS|FAIL|BLOCKED|SKIPPED|[A-Z][A-Z_-]+)\s*\|", text)
bad = [s for s in verdict_cells if s not in VERDICT_STATUSES]
rows.append(("STRICT", "verdict_status_vocab_violations",
             0, len(bad), f"+{len(bad)}" if bad else "0",
             f" FAIL unknown={sorted(set(bad))[:5]}" if bad else ""))

# STRICT-2 CASE_YAML_SCHEMA — every YAML case file declares the required field set
schema_violations = []
if CASE_DIR.is_dir():
    for yml in sorted(CASE_DIR.glob("case_*.yaml")):
        body = yml.read_text(errors="ignore")
        present = {k for k in REQUIRED_FIELDS if re.search(rf"^{k}\s*:", body, re.M)}
        missing = REQUIRED_FIELDS - present
        if missing:
            schema_violations.append((yml.name, sorted(missing)))
rows.append(("STRICT", "case_yaml_missing_required_fields",
             0, len(schema_violations), f"+{len(schema_violations)}" if schema_violations else "0",
             f" FAIL {schema_violations[:3]}" if schema_violations else ""))

# STRICT-3 ROSTER_COVERS_SELECTED_CASES — every selected YAML case appears as a
# row in the roster (catches NULL_VERDICT_REGRESSION via silent drop)
roster_ids = set(re.findall(r"\|\s*(case_\d+_[a-z0-9_-]+|case-\d+|\d+)\s*\|", text))
yaml_ids = {p.stem for p in CASE_DIR.glob("case_*.yaml")} if CASE_DIR.is_dir() else set()
dropped = yaml_ids - roster_ids if (roster_ids and yaml_ids) else set()
rows.append(("STRICT", "selected_cases_missing_from_roster",
             len(yaml_ids), len(roster_ids), f"-{len(dropped)}" if dropped else "0",
             f" FAIL dropped={sorted(dropped)[:5]}" if dropped else ""))

# SOFT-1 ROSTER_ROW_COUNT_DELTA — vs prior snapshot (NULL_VERDICT_REGRESSION smell)
if PRE_VERDICT.exists() and str(PRE_VERDICT) != "/dev/null":
    prev = PRE_VERDICT.read_text(errors="ignore")
    prev_rows = len(re.findall(r"^\|\s*case", prev, re.M))
    curr_rows = len(re.findall(r"^\|\s*case", text, re.M))
    delta = curr_rows - prev_rows
    flag = ""
    if prev_rows and abs(delta) >= max(2, prev_rows // 4):
        flag = f" warn prev={prev_rows} curr={curr_rows}"
    rows.append(("SOFT", "roster_row_count_delta",
                 prev_rows, curr_rows, f"{delta:+d}", flag))

# SOFT-2 FAIL_TOTAL — count of FAIL+BLOCKED rows (operator glance)
non_pass = sum(1 for s in verdict_cells if s in {"FAIL", "BLOCKED"})
rows.append(("SOFT", "non_pass_rows", 0, non_pass, f"+{non_pass}", ""))

fail = 0
print(f"{'severity':9} {'metric':40} {'before':>8} {'after':>8} {'delta':>8}")
for sev, metric, before, after, delta, flag in rows:
    if "FAIL" in flag: fail += 1
    print(f"{sev:9} {metric:40} {str(before):>8} {str(after):>8} {delta:>8}{flag}")
sys.exit(1 if fail else 0)
PY
```

Then run the same case selection a **second time on the unchanged repo** and diff the two roster outputs (modulo the report's `YYYY-MM-DD` date header and any explicit `generated_at`-class lines). Any non-whitespace delta in the per-case verdict columns (Passed / Failed / Verdict) → STRICT-IDEMPOTENT fail.

If exit non-zero → STOP, do not present the report. Report failures and propose specific restorations (re-include the dropped case row, normalise the bad Verdict cell, fix the YAML missing-fields case), then re-run Layer A.

### Reconciliation outcomes

- **All STRICT pass** → present the report.
- **Any STRICT fail** → propose targeted restorations (restore the dropped case row, normalise the bad Verdict cell, fix the YAML missing-fields case) and re-run Layer A on the patched state. **Hard cap: 2 iterations** (per `rules/contract-authoring.md §Small-bound carve-out`; bound = 2 → hard rule, no graceful +1). If still failing after iteration 2, surface to the user; do not auto-publish the report.
- **Only SOFT warnings** (`roster_row_count_delta` jump, large `non_pass_rows` total) → present the report but include the warnings in the Regression Verdict line so the operator has a final-glance opportunity.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **Eval-case meta-staleness.** Cases may PASS every check while the cases themselves no longer reflect the current skill behavior — authored before a rubric rewrite and asserting against the OLD criteria. Whole-corpus drift requires a periodic case-meta-audit (re-derive expected sprint contracts from the current rubric and diff against existing case YAML), not this per-run pipeline.
2. **Dispatch-agent non-determinism.** A Phase 2 dispatch agent may produce different output across runs on identical input (LLM stochasticity), flipping a borderline criterion's PASS↔FAIL. Layer A's idempotency rerun surfaces this as a delta but cannot distinguish "real regression" from "sampling jitter"; operator inspects the failing criterion's quoted excerpt.
3. **YAML-to-roster identity-mapping fragility.** STRICT-3 matches roster `case_*` IDs against YAML stems via regex. If a YAML adopts a renamed `id:` field diverging from its filename stem (legitimate — spec allows free-form `id`), STRICT-3 may flag a false-DROPPED. Operator disambiguates manually.

## Hard Rules

- **YAML is the source of truth.** Do NOT inline sprint contracts, defects arrays, or synthetic artifact content in this skill body. Add new cases by writing a new `tests/eval_cases/case_<n>_<slug>.yaml` and any required `tests/fixtures/eval/<...>` fixtures.
- **Cleanup runs even on failure.** Delete `.claude/eval-temp/` at the end of Phase 3 regardless of case outcomes. For `behavior_scaffold` cases, run `case.execution.cleanup` immediately after each scenario, BEFORE moving to the next.
- **BLOCKED is not FAIL.** If a required skill or fixture is missing, mark the case BLOCKED, exclude it from the pass/fail count, and report it separately.
- **Stop conditions.** If a Phase 2 dispatch agent fails entirely (crash or error), mark every sprint_contract criterion FAIL for that case, note the error, and continue with the next case. Do not retry.

## Tier A Tool Justification

**Tier A tool justification (Bash):** Bash is granted for: (1) workspace
pre-clean (`rm -rf .claude/eval-temp && mkdir -p .claude/eval-temp`), (2)
artifact staging (`cp`) per the `behavior_scaffold` case kind, (3) cleanup
(`rm -rf .claude/eval-temp`), and (4) `bash bin/repo-slug.sh "$(pwd)"` to
compute the canonical `<repo-slug>` deterministically per
`references/repo-identification.md`. The command-level allowlist
`Bash(bash bin/repo-slug.sh:*)` enforces scope for the slug resolver; the
workspace and staging commands are bounded to `.claude/eval-temp/`.
- **Sprint contracts are fixed.** Do not adjust criteria based on what the review actually produces. Evaluate actual output against the YAML criteria as written.
- **Present all results before asking** about persistence.
- **Scaffold doc revert is mandatory** for `behavior_scaffold` cases. The scaffold writes to shared docs (README.md, CLAUDE.md). Always revert those changes after each scenario, even if criteria passed. Record whether revert succeeded.
