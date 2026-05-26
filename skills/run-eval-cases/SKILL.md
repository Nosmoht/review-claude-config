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

Without verification, this skill fails at **EVAL_FALSE_PASS** — a case's evaluation criterion is too loose and reports PASS while the underlying regression slipped through. Canonical example: a `clean`-kind case asserts "zero High findings" but the criterion's grep is `H[Ii]gh` while the actual review report emits uppercase `HIGH`, so the substring match misses entirely and yields a spurious PASS. Without an order-swapped adversarial critic that inspects every `sprint_contract[].description` for grep-too-loose / regex-too-narrow / missing exit-code assertion patterns, the runner becomes a self-confirming oracle: cases pass because their criteria are weak, not because the system is healthy. A second failure class is **NULL_VERDICT_REGRESSION** — a previously-emitted FAIL row silently disappears from the per-case roster because a YAML case file was renamed/removed without a corresponding fix in the system under test; the aggregate PASS rate ticks up without a defensible change. A three-layer pipeline (mechanical invariants / adversarial critic / binary rubric) is required because no single layer catches both classes.

References: CheckEval (arXiv:2403.18771), G-Eval (arXiv:2303.16634), Position bias in LLM-as-a-Judge (arXiv:2406.07791), IFEval (arXiv:2311.07911), FollowBench (ACL 2024), Beyond Consensus (NUS 2025). Per-skill design: `.work/skill-verification/maintain-template.md §Per-skill customization notes → skills/run-eval-cases/SKILL.md`.

Per the MAINTAIN template's per-skill note: this skill produces per-case PASS / FAIL / BLOCKED verdicts (chat output + ephemeral `.claude/eval-temp/` working files) with no persistent repo mutation outside that workspace. Layer A STRICT-1 idempotency must allow `.claude/eval-temp/` deltas (the workspace is rebuilt every run) but require identical case-verdict rows. SOFT row-count-delta is critical here — silent case-count regression is the dominant NULL_VERDICT_REGRESSION vector. Layer C D3 (sync integrity) is N/A (no paired-file invariant). D4 (schema) covers the case YAML required-field set (`id`, `kind`, `description`, `target_skill`, `sprint_contract`). D5 (verdict honesty) carries the highest weight.

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

### Layer B — adversarial critic dispatch (blind, recall-framed)

Dispatch a fresh subagent. The critic must be **seeded with the YAML case definitions** so EVAL_FALSE_PASS judgments are evaluated against each case's actual sprint_contract criteria, not the critic's prior.

```
Agent({
  description: "Adversarial run-eval-cases critic",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind reviewer auditing a run-eval-cases verdict roster against the YAML case definitions it claims to evaluate. " +
    "You are given:\n" +
    "  A: <the per-case verdict roster the skill produced>\n" +
    "  B: <the prior-run roster snapshot, or null>\n" +
    "  Y: <the full text of every YAML case file under tests/eval_cases/>\n" +
    "  C: <skill body §Phase 2 — Case Execution + §Hard Rules from skills/run-eval-cases/SKILL.md>\n" +
    "Neither label tells you which is the current vs prior.\n\n" +
    "Find:\n" +
    "1. EVAL_FALSE_PASS — sprint_contract[].description entries in Y whose evaluation criterion is too loose to detect the regression class the case targets. Examples: substring grep `H[Ii]gh` when the report emits uppercase `HIGH`; regex with anchored `^` that misses indented matches; missing exit-code assertion on a Bash dispatch; criterion checks for presence of a header but not the body content under it. For each suspect criterion, quote the literal criterion text and explain the input shape that would slip through.\n" +
    "2. DROPPED — case IDs present in B that are absent from A without a corresponding case-file removal in Y.\n" +
    "3. WEAKENED — case rows in A whose verdict was relaxed vs B (FAIL→PASS, BLOCKED→PASS) without a citable change in the system under test or the case YAML.\n" +
    "4. ADDED — case rows in A with no traceable YAML definition in Y (orphan verdict).\n" +
    "5. FIXTURE_DRIFT — case rows whose YAML references `artifacts.*` / `findings_fixture` paths that no longer exist on disk, but the roster shows PASS instead of BLOCKED.\n" +
    "6. CRITERIA_AMBIGUITY — sprint_contract[].description entries phrased in vague terms (`should consider`, `improve`, `appropriate`) that cannot be mechanically evaluated; the runner is forced to LLM-judge against a moving target.\n" +
    "7. KIND_MISMATCH — case rows whose verdict path does not match the documented kind contract in C (e.g., a `clean`-kind case marked PASS without checking the zero-High-Medium invariant, or a `behavior_scaffold` case marked PASS without the `expected_writes_under` + `forbidden_doc_targets` checks).\n\n" +
    "For each item: quote the literal criterion or row, name the YAML file and case id, classify with one of the seven tokens above. " +
    "Report under 600 words. Do not rate quality. Do not praise the skill's design.\n\n" +
    "A:\n<paste $CURRENT contents>\n\n" +
    "B:\n<paste PRE_VERDICT contents or 'null'>\n\n" +
    "Y:\n<paste every tests/eval_cases/case_*.yaml body>\n\n" +
    "C:\n<paste skills/run-eval-cases/SKILL.md §Phase 2 + §Hard Rules>"
})
```

Then **dispatch a second time with A and B swapped** (and, where applicable, with the YAML concatenation order in Y reversed) — position bias is the dominant LLM-judge artifact in pairwise settings (Shi et al. 2024, arXiv:2406.07791). Take the union of items flagged across both runs.

### Layer C — rubric reconciliation (binary CheckEval-style)

Six yes/no dimensions specialized to the verdict-roster output. Any `NO` blocks the report until resolved.

```
D1 IDEMPOTENT              Second run of the skill against the same case
                           selection on unchanged repo state produces a roster
                           with identical per-case Verdict / Passed / Failed
                           columns (modulo the date header and explicit
                           timestamp lines; the .claude/eval-temp/ workspace
                           is rebuilt and is NOT compared).
                           Layer A idempotency rerun passes.
                           Ties to F1 IDEMPOTENCY_BREAK.

D2 FRESHNESS_RESPECT       Every fixture path referenced from case YAML
                           (artifacts.*, findings_fixture) is checked for
                           existence before the case is marked PASS; missing
                           fixtures route to BLOCKED, not silent PASS.
                           Layer B finds zero FIXTURE_DRIFT.
                           Ties to F2 STALE_MISS.

D3 SYNC_INTEGRITY          N/A — this skill does not maintain a sync invariant
                           across paired files. Auto-PASS with note.

D4 SCHEMA_AND_CONTRACT     Every YAML case file declares the required field
                           set {id, kind, description, target_skill,
                           sprint_contract}. Every Verdict cell uses a token
                           in the closed set {PASS, FAIL, BLOCKED, SKIPPED}.
                           Layer A STRICT-1 + STRICT-2 pass.
                           Ties to F5 STATE_FORMAT_DRIFT.

D5 VERDICT_HONESTY         Every selected case appears as a row in the
                           roster (no silent drop). No case marked PASS via
                           a criterion the Layer B critic flagged as
                           EVAL_FALSE_PASS / CRITERIA_AMBIGUITY /
                           KIND_MISMATCH. No row from the prior roster
                           silently disappeared without a corresponding
                           YAML removal. No row was emitted with a weaker
                           verdict than the prior run absent a citable fix.
                           Layer A STRICT-3 passes; Layer B finds zero
                           EVAL_FALSE_PASS / DROPPED / WEAKENED / ADDED /
                           CRITERIA_AMBIGUITY / KIND_MISMATCH.
                           Ties to F7 EVAL_FALSE_PASS, F10
                           NULL_VERDICT_REGRESSION. HIGHEST WEIGHT.

D6 DEPGRAPH_COMPLETENESS   N/A — this skill is not a dependency-graph emitter.
                           Auto-PASS with note.
```

Mapping Layer-A failures → rubric:

- STRICT-1 (verdict status vocab) fail → D4 NO
- STRICT-2 (YAML missing required fields) fail → D4 NO
- STRICT-3 (selected cases missing from roster) fail → D5 NO
- Idempotency rerun delta on Verdict / Passed / Failed columns → D1 NO

Mapping Layer-B critic tokens → rubric:

- `EVAL_FALSE_PASS` / `CRITERIA_AMBIGUITY` / `KIND_MISMATCH` → D5 NO
- `DROPPED` / `WEAKENED` / `ADDED` → D5 NO
- `FIXTURE_DRIFT` → D2 NO

### Reconciliation outcomes

- **All STRICT pass + Layer B yields zero EVAL_FALSE_PASS / DROPPED / WEAKENED / ADDED / FIXTURE_DRIFT / CRITERIA_AMBIGUITY / KIND_MISMATCH** → present the report.
- **Any STRICT fail OR any blocking critic token** → propose targeted restorations (tighten the loose criterion in the case YAML, restore the dropped case row, mark the missing-fixture case as BLOCKED, fix the schema-violating YAML) and re-run Layers A + B on the patched state. **Hard cap: 2 iterations** (per `rules/contract-authoring.md §Small-bound carve-out`; bound = 2 → hard rule, no graceful +1). If still failing after iteration 2, surface to the user; do not auto-publish the report.
- **Only SOFT warnings** (`roster_row_count_delta` jump, large `non_pass_rows` total) → present the report but include the warnings in the Regression Verdict line so the operator has a final-glance opportunity.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **Eval-case meta-staleness.** Cases may PASS every check while the cases themselves no longer reflect the current skill behavior — the cases were authored before a rubric rewrite and assert against the OLD criteria. Layer B's critic inspects one case at a time; whole-corpus drift requires a periodic case-meta-audit (e.g., re-derive expected sprint contracts from the current rubric and diff against existing case YAML), not this per-run pipeline. (Cross-link: maintain-template residual #3.)
2. **Quiet success-mode masking partial failure.** A future variant of this skill that aggregates per-case results into a single roster row (`all → PASS`) without per-case enumeration would defeat the pipeline's D5 check; the present `## Phase 3 — Cleanup and Report` structure already enumerates per-case, so this residual is latent rather than active.
3. **Dispatch-agent non-determinism.** A Phase 2 dispatch agent may produce different output across runs even on identical input (LLM stochasticity), which can flip a borderline criterion's PASS↔FAIL. Layer A's idempotency rerun would surface this as a delta but cannot distinguish "real regression" from "sampling jitter"; the operator must inspect the failing criterion's quoted excerpt and decide. This is not pipeline-fixable without bounded-temperature dispatch.
4. **Criterion-LLM-judge correlation.** If a case's sprint_contract relies on LLM-judge phrasing identical to the dispatched skill's own self-evaluation prompt, both agents may agree by shared bias rather than by genuine signal. The Layer B critic inspects criterion phrasing but does not run a counter-judge with a different prompt; this residual maps onto the LLM-as-judge position-bias literature without a complete in-pipeline mitigation.
5. **YAML-to-roster identity-mapping fragility.** STRICT-3 matches roster `case_*` IDs against YAML stems via regex. If a case YAML adopts a renamed `id:` field that diverges from its filename stem (legitimate — the spec allows `id` to be free-form), STRICT-3 may flag a false-DROPPED. The operator can disambiguate manually; tightening STRICT-3 to read the YAML `id:` field would add I/O without resolving the residual that emerges when the YAML file is itself missing.

The report MUST surface which residual classes apply to non-PASS or borderline rows the operator should still review by hand.

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
