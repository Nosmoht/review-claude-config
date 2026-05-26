---
name: apply-rule-review-findings
description: >
  Applies findings from a /review-rule report to the reviewed rule file
  (always-loaded directives, imperatives). Use after /review-rule on a
  single rule or when delegated by /apply-review-findings. Do NOT use for
  skill or agent reports.
argument-hint: "[report-path]"
allowed-tools: Read, Edit, Glob, Bash
disable-model-invocation: true
---

# Apply Rule Review Findings

You are a code editor applying structured review recommendations to Claude Code rules. Your job is to faithfully translate review findings into file edits with rule-specific validation, preserving the audit-fix traceability chain.

## Mode Detection

Check whether the prompt contains an orchestration metadata block:

```
---orchestration---
mode: orchestrated
report_timestamp: YYYY-MM-DDTHHMMSS
---

## Items to Fix

### Item: [name]
**Path:** [file path]
**Type:** Rule
**Recommendations:**
[High/Medium recommendations with Current/Recommended blocks]
```

- If present -> **orchestrated mode** (use provided items, skip report parsing, return structured results only).
- If absent -> **standalone mode** (full workflow below).

> **Pre-apply policy classification.** Before any Edit, classify the finding against [`docs/apply-risk-policy.md`](../../docs/apply-risk-policy.md) on `evidence_class × confidence × blast_radius`. If `decide()` returns `auto_apply_allowed: false` (e.g., `evidence_class: Low-evidence area`, missing label, or any `blast_radius: security-sensitive`), route to manual-only handling regardless of the per-edit Confirmation Gate.

## Phase 1 -- Setup (standalone mode only)

### Step 1: Locate Report

**Resolve report directory:** Run `bash bin/repo-slug.sh "$(pwd)"` and capture stdout as `<repo-slug>`. (For documentation reference only, not the operational source-of-truth: `references/repo-identification.md` describes the sanitize algorithm.) The report directory is `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`.

If `$ARGUMENTS` contains a file path, use it. Otherwise, Glob `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/*-review-rule.md` and select the most recent report by filename timestamp.

Read the report file. If the file does not exist or `generated_by` is not `review-rule`, report the error and stop.

### Step 2: Load Findings

> This step runs in standalone mode only. Orchestrated mode bypasses Step 2 entirely — recommendations come from the inline `## Items to Fix` Markdown block in the orchestration prompt (see Mode Detection above).

Locate the canonical review contract via Glob: `**/review-claude-config/references/review-report-contract.md`.
- Prefer `skills/review-claude-config/references/review-report-contract.md` when present.
- Otherwise use the sibling `.claude/skills/review-claude-config/references/review-report-contract.md` copy.

Read that file as the forward-looking report contract. Extract the YAML frontmatter to get: `date`, `target`, and `summary`.

#### Step 2.1: Sidecar discovery

Resolve the report path to absolute via `Bash("realpath <report-path>")`. Require it to end in `.md`; otherwise skip sidecar discovery and use the Markdown fallback (Step 2.3). Sidecar path = `<report-path>` with the trailing `.md` removed and `.findings.json` appended.

Try to Read the sidecar. Five outcomes:
- **File missing** → log `"no sidecar at <path> — using Markdown body"` (legitimate for `--single-perspective`, orchestrated mode, or pre-#81 legacy reports — `/review-rule` does not yet emit sidecars) and fall through to Step 2.3.
- **JSON parse fails** → log `"sidecar parse failed at <path> — falling back to Markdown"` and fall through to Step 2.3.
- **`generated_by` or `findings` keys missing/non-list** → log `"sidecar schema mismatch at <path> — falling back to Markdown"` and fall through to Step 2.3.
- **`findings: []`** → clean-review state. Surface "No findings — review was clean." and stop. Do NOT fall back to Markdown.
- **`findings: [...]` non-empty** → continue to Step 2.2.

#### Step 2.2: Map sidecar findings

The sidecar conforms to `skills/review-claude-config/references/schemas/findings-list.schema.json`. Map each finding to the local recommendation model:
- **title** — `checklist_item` + a short fragment from `evidence` (truncate to ~60 chars)
- **impact** — `severity` (`High`/`Medium`/`Low`)
- **file path** — finding `path`; fall back to `summary[0].path` (the canonical rule path) when `path` is missing
- **evidence** — finding `evidence`
- **why it matters** — finding `why` (when absent, surface the rubric-item reference; never blank)
- **validation** — finding `validation` (when absent, surface "Manual re-verification recommended"; never blank)
- **current** — finding `current`
- **recommended** — finding `recommended`

Continue to Step 2.4 (applyability gate).

#### Step 2.3: Markdown back-compat path

Parse the report body using consumer compatibility rules:
- modern headings may use `####`
- historical headings may use `###`
- historical reports may omit `Evidence`, `Why it matters`, or `Validation`
- recommendations carry `Current` and `Recommended` blocks when dispatchable

Apply the same defensive defaults as the sidecar path. Log a one-line note: "Loaded findings from Markdown body (sidecar absent — legacy report)."

#### Step 2.4: Applyability gate

For each mapped recommendation, verify it can drive a real Edit:
1. If `current` or `recommended` is empty → mark **Manual-only** (reason: "Missing rewrite anchors").
2. Read the target rule file.
3. If `current` does NOT appear as a literal substring of the file content → mark **Manual-only**. Distinguish reasons: synthesized-evidence shape (`current` starts with `line ` and contains `; match=` / `; trigger=` / `; missing=`) → "Synthesized evidence summary, not a literal source quote (binary item)"; otherwise → "Anchor text not found (whitespace, encoding, or quoting drift?)".
4. Otherwise → mark **Dispatchable**.

Filter Dispatchable into **High/Medium** and **Low** groups.

> Reports produced after issue #72 ship only the **deterministic subset** at H+M severity (items in `BINARY_ITEM_IDS` or `NARRATIVE_PARENT_IDS`, per `skills/review-claude-config/references/merge-rules.md` §"Perspective Finding Handling"). Advisory perspective findings are demoted to Low at merge time. After Step 2.4, synthesized binary findings (currently emitting non-substring `current`) also fall to Manual-only by construction. Auto-dispatchable Highs are perspective-emitted findings that survive the demote — typically a small set; the rest of the workflow treats them normally.

If no High/Medium dispatchable recommendations exist:
- if dispatchable Low recommendations exist, skip to **Step 2a: Low Impact Offer**
- otherwise present any manual-only findings as manual follow-up items and stop

### Step 2a: Low Impact Offer

If manual-only findings are present, show them before offering the Low-impact pass. Keep them visible even when dispatchable Low findings exist.

If dispatchable Low recommendations exist, tell the user:

Confirm via AskUserQuestion (header: "Low-impact findings only"):
- Option 1 label: "Address N low-impact findings" — description: `"Process Low recommendations to reach A-grade"`
- Option 2 label: "Skip" (Recommended) — description: `"Stop — preserve manual-only findings as follow-up items"`

On "Skip": stop after preserving the manual-only findings as follow-up items. On "Address N low-impact findings": promote the Low recommendations into the actionable set and continue to Phase 2.

If there are no dispatchable recommendations but manual-only findings exist, present them as manual follow-up items and stop. Do not attempt file edits without rewrite anchors.

### Step 3: Load References

Read own `references/rule-fix-guide.md` for type-specific validation rules.

Locate shared commit conventions via Glob: `**/review-claude-config/references/commit-conventions.md`. If not found, warn but continue.

## Phase 2 -- Present Summary

Surface any Step 2 log lines first (one line each).

Show a summary table of all dispatchable findings:

```
## Actionable Findings

| # | Recommendation | Impact | File |
|---|----------------|--------|------|
| 1 | Add scope boundaries | High | .claude/rules/foo.md |
```

If manual-only findings are present, also show:

```
## Manual Follow-Up

| # | Recommendation | Impact | Reason | Why it matters |
|---|----------------|--------|--------|----------------|
| 1 | Tighten rationale wording | Medium | Missing Current/Recommended anchors | Aspirational verbs weaken enforcement |
```

The `Why it matters` column gives the user actionable context for findings that cannot drive an automatic Edit.

Confirm via AskUserQuestion (header: "Apply findings"):
- Option 1 label: "Apply N findings" (Recommended) — description: `"Process High/Medium recommendations with preview for each"`
- Option 2 label: "Cancel" — description: `"Stop without making changes"`

On "Cancel": stop.

## Phase 3 -- Apply Recommendations

Example flow: Read `.claude/rules/commit-format.md` -> search for Current text "You should use conventional commits" -> found -> pre-edit: weak verb "should" in replacement flagged as warning (expected — it's being replaced) -> show preview -> user says "yes" -> Edit applied -> post-edit: no frontmatter added, no sibling contradictions found.

For each recommendation (High impact first, then Medium):

1. Read the target rule file at the path from the report's `summary` section.
2. Locate the **Current** text block in the actual file content.
   - If not found, show the user the Current text and confirm via AskUserQuestion (header: "Text not found"):
     - Option 1 label: "Skip this recommendation" (Recommended) — description: `"Move to the next recommendation"`
     - Option 2 label: "Identify correct text" — description: `"Describe where the text is so the edit can be applied"`
     On "Skip this recommendation": skip. On "Identify correct text": ask the user to identify the correct text.
3. **Pre-edit validation** (rule-specific):
   - If the recommended text starts with `---` (YAML frontmatter delimiters), block: "Rules must not have frontmatter. This edit would add YAML delimiters. Remove frontmatter from the recommendation before applying."
   - Scan the recommended text for weak verbs: "should", "try to", "when possible", "consider", "might want to". Warn: "Rule contains aspirational language. Consider replacing with 'must'/'never'/'always' for unambiguous enforcement."
   - If the edit removes scope qualifiers (file types, operation types, directory patterns, context conditions), warn: "This edit narrows or removes scope boundaries. Verify the rule still applies to the intended targets."
4. Show the user:
   - File path
   - Evidence / Why it matters / Validation (from the report)
   - Current text (from the actual file)
   - Recommended replacement (from the report)
   - Any validation warnings from step 3
5. Confirm via AskUserQuestion (header: "Apply: <recommendation title>"):
   - Option 1 label: "Apply this change" (Recommended) — description: `"Edit the file with the recommended replacement"`
   - Option 2 label: "Skip" — description: `"Move to the next recommendation"`
   - Option 3 label: "Stop" — description: `"End processing, keep changes applied so far"`
   On "Apply this change": apply the edit using the Edit tool. On "Skip": move to next. On "Stop": end processing.
6. **Post-edit validation** (rule-specific):
   - Verify no YAML frontmatter was added (file must not start with `---`).
   - Read sibling rules in the same directory (Glob `<rule-dir>/*.md`). Scan for contradictions with the edited rule (e.g., one rule says "always X" while another says "never X" for overlapping scope). Warn if found.
   - Verify action verbs are unambiguous: directives should use "must", "never", "always" -- not "should", "try", "consider".

## Phase 4 -- Results

### Orchestrated Mode

Return structured results:

```
## Apply Results

| # | Recommendation | Status |
|---|----------------|--------|
| 1 | Add scope boundaries | Applied |
| 2 | Strengthen verbs | Skipped |

Applied: N / Total: M
Validation warnings: [list any warnings]
```

### Standalone Mode

Present the change summary table (same format as above).

If any manual-only findings were not dispatchable, list them separately as manual follow-up items.

If no changes were applied, stop here.

**Low Impact Pass (standalone mode only):**

If Low impact recommendations were set aside in Step 2 and at least one High/Medium change was applied, confirm via AskUserQuestion (header: "Low-impact findings"):
- Option 1 label: "Address N low-impact findings" — description: `"Process remaining Low recommendations to reach A-grade"`
- Option 2 label: "Skip" (Recommended) — description: `"Leave low-impact findings for later"`

On "Address N low-impact findings": loop back to Phase 3 with the Low recommendations. Process through the same preview/confirm/validate pipeline. Append results to the change summary table. On "Skip": note: "N Low impact findings were not applied."

In orchestrated mode, do not prompt — process whatever recommendations the orchestrator sends.
The orchestrator must send only dispatchable recommendations with both `Current` and `Recommended`.

**Regression check (after all edits applied):**

For each modified file, verify that applied changes did not:
1. Introduce aspirational language ("should", "try to", "consider") where the original used constraints ("must", "never", "always").
2. Remove or broaden scope boundaries without documented justification.
3. Create contradictions with sibling rules in the same directory.

If any regression is detected, confirm via AskUserQuestion (header: "Potential regression detected"):
- Option 1 label: "Review before committing" (Recommended) — description: `"Inspect [file]: [description] before proceeding"`
- Option 2 label: "Proceed anyway" — description: `"Continue to the commit step"`

**Commit with audit-fix chain:**

Read the shared commit conventions (loaded in Phase 1 Step 3).

Extract the timestamp from the report filename.

Check whether the review report has been committed: `git log --oneline --all -- <report-path>` via Bash. If not committed:

Tell the user: "The review report is not yet committed. The audit-fix chain requires committing the report first: `docs(reviews): add <timestamp> review report`"

Confirm via AskUserQuestion (header: "Commit report"):
- Option 1 label: "Commit the report now" (Recommended) — description: `"Stage and commit the review report with docs(reviews): add <timestamp> review report"`
- Option 2 label: "Skip" — description: `"Continue without committing the report"`

On "Commit the report now": stage and commit via Bash.

For the fix commit:
- Determine scope from the rule name or directory.
- Compose: `fix(<scope>): address findings from <timestamp> review`
- Show the commit message and confirm via AskUserQuestion (header: "Commit changes"):
  - Option 1 label: "Commit these changes" (Recommended) — description: `"Stage and commit: fix(<scope>): address findings from <timestamp> review"`
  - Option 2 label: "Skip" — description: `"Leave changes uncommitted"`
- On "Commit these changes": stage and commit via Bash.

Present final status:
- Files modified
- Commits created (with hashes)
- Recommendations not applied
Then end your response with this menu (substitute `<path>` with the target rule path):

Present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Verify improvements" (Recommended) — description: `"Run /review-rule <path> to detect cross-dimension regressions"`
- Option 2 label: "Apply findings from another report" — description: `"Provide a report path to apply"`
- Option 3 label: "Done" — description: `"End the workflow"`

On "Verify improvements": invoke `/review-rule` with the rule path. On "Apply findings from another report": ask for the report path, then invoke `/apply-rule-review-findings`. On "Done": acknowledge and stop.

## Quality measurement (mandatory before commit)

Without verification, this skill fails at **finding-coverage miss / scope-fidelity break / always-loaded-rule regression / audit-fix chain break** — concretely: a Medium finding silently dropped without a Skipped row, a `paths:` glob pattern mutated while replacing nearby text (breaks harness path-scoping for every future session), a cross-link to `rules/<sibling>.md` left dangling after a rename, or a fix commit landing without the upstream report commit (F1 / F2 / F3 / F7 / F9 per `.work/skill-verification/apply-template.md`). Rule files are loaded into every session in `~/workspace/` via the `~/.claude/rules/` symlink — a DROPPED constraint here has session-wide blast radius. The literature converges on a three-layer pipeline; any one layer alone is insufficient.

References: CheckEval (arXiv:2403.18771), G-Eval (arXiv:2303.16634), Position bias in LLM-as-a-Judge (arXiv:2406.07791), IFEval (arXiv:2311.07911), FollowBench (ACL 2024), Beyond Consensus (NUS 2025), Invalidator (arXiv:2301.01113).

Before any commit, the apply skill captures `PRE_SHA="$(git rev-parse HEAD)"` (recorded into `.work/<task-id>/pre-apply-sha`) and emits a result manifest `claimed.json` of the shape `{"applied":[...], "skipped":[...], "manual_only":[...], "policy_decisions":{<finding_id>: true|false}}` so the layers below can read both deterministically.

### Layer A — mechanical invariants (deterministic, fail-fast)

Run on the post-apply working tree. Any `STRICT` row FAIL → abort and report; any `SOFT` row delta → log warning, surface to user, do not auto-commit.

```bash
PRE_SHA="$(cat .work/<task-id>/pre-apply-sha)"
REPORT="$1"   # *-review-rule.md report
CLAIMED="$2"  # claimed.json {applied, skipped, manual_only, policy_decisions}

python3 - "$REPORT" "$PRE_SHA" "$CLAIMED" <<'PY'
import json, os, re, subprocess, sys
report_path, pre_sha, claimed_path = sys.argv[1], sys.argv[2], sys.argv[3]
sidecar = report_path.removesuffix(".md") + ".findings.json"
findings = []
if os.path.exists(sidecar):
    findings = json.load(open(sidecar)).get("findings", [])
else:
    body = open(report_path).read()
    for m in re.finditer(r"^#{3,4}\s+\d+\.\s+(.+?)\s+\(Impact:\s+(High|Medium|Low)", body, re.M):
        findings.append({"id": m.group(1)[:60], "severity": m.group(2)})
claimed = json.load(open(claimed_path))
applied = set(claimed["applied"])
body = open(report_path).read()
fm = re.match(r"---\n(.*?)\n---", body, re.S)
allowed_paths = set(re.findall(r"-\s+path:\s+([^\s]+)", fm.group(1))) if fm else set()
diff_files = [f for f in subprocess.check_output(
    ["git", "diff", "--name-only", pre_sha], text=True).strip().split("\n") if f]
report_committed = subprocess.run(
    ["git", "log", "--oneline", "--all", "--", report_path],
    capture_output=True, text=True).stdout.strip()
rows = []
def row(sev, name, ok, detail=""): rows.append((sev, name, ok, detail))
hm = [f for f in findings if f.get("severity") in ("High", "Medium")]
applied_hm = [f for f in hm if f.get("id") in applied]
row("STRICT", "hm_coverage",
    len(applied_hm) + len(claimed["manual_only"]) + len(claimed["skipped"]) == len(hm),
    f"hm={len(hm)} applied={len(applied_hm)} manual={len(claimed['manual_only'])} skipped={len(claimed['skipped'])}")
out_of_scope = [f for f in diff_files if allowed_paths and f not in allowed_paths
                and not f.endswith(".findings.json") and not f.endswith("-review-rule.md")]
row("STRICT", "path_scope", not out_of_scope, f"out_of_scope={out_of_scope}")
# Rule-specific invariants (F3, F7): paths:-field byte-identity, no frontmatter injection,
# cross-link integrity. Rule files in this repo's .claude/rules/ are plain Markdown
# (Hard Rule: no frontmatter); rule files in ~/workspace/claude-config/rules/ MAY carry
# `paths:` globs that are LOAD-BEARING (harness path-scoping contract).
violations = []
REF_RE = r"\b(?:rules|references|agents|skills|hooks|bin)/[A-Za-z0-9._/-]+\.[a-z]+\b"
for f in diff_files:
    if not (f.endswith(".md") and "/rules/" in f and not f.endswith("-review-rule.md")):
        continue
    text = open(f).read()
    # No frontmatter injection (Hard Rule, also F3 SKILL declaration)
    pre_text = subprocess.run(["git", "show", f"{pre_sha}:{f}"],
                              capture_output=True, text=True).stdout
    pre_has_fm = pre_text.startswith("---\n")
    post_has_fm = text.startswith("---\n")
    if post_has_fm and not pre_has_fm:
        violations.append(f"{f}=frontmatter-injected")
    # paths: byte-identity when present (D2 SCOPE_FIDELITY load-bearing for rules)
    pre_paths_m = re.search(r"^paths:\s*\n((?:\s+-\s+.+\n)+)", pre_text, re.M)
    post_paths_m = re.search(r"^paths:\s*\n((?:\s+-\s+.+\n)+)", text, re.M)
    if pre_paths_m and (not post_paths_m or pre_paths_m.group(1) != post_paths_m.group(1)):
        violations.append(f"{f}=paths-mutated")
    # Cross-link integrity: every intra-repo reference in the post-edit body must
    # resolve to a file that exists in the working tree.
    repo_root = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True).strip()
    for ref in set(re.findall(REF_RE, text)):
        if not os.path.exists(os.path.join(repo_root, ref)):
            violations.append(f"{f}=broken-link:{ref}")
row("STRICT", "invariants", not violations, f"violations={violations}")
unresolved_high = [f for f in findings if f.get("severity") == "High"
                   and f.get("id") not in applied and f.get("id") not in claimed["manual_only"]]
applied_low = [f for f in findings if f.get("severity") == "Low" and f.get("id") in applied]
row("STRICT", "severity_order", not (unresolved_high and applied_low),
    f"unresolved_high={len(unresolved_high)} applied_low={len(applied_low)}")
row("STRICT", "report_committed", bool(report_committed), f"log='{report_committed[:60]}'")
policy = claimed.get("policy_decisions", {})
policy_viol = [fid for fid in applied if policy.get(fid) is False]
row("STRICT", "policy_gate", not policy_viol, f"violations={policy_viol}")
row("SOFT", "idempotency_marker", True, "second-run dispatched separately")
row("SOFT", "files_touched", True, f"n={len(diff_files)}")
row("SOFT", "applied_count", True, f"applied={len(applied)}")
fail = 0
print(f"{'severity':9} {'metric':22} {'ok':>4}  detail")
for sev, name, ok, detail in rows:
    flag = "PASS" if ok else ("FAIL" if sev == "STRICT" else "warn")
    if not ok and sev == "STRICT": fail += 1
    print(f"{sev:9} {name:22} {flag:>4}  {detail}")
sys.exit(1 if fail else 0)
PY
```

**Idempotency (F5) sub-test (separate dispatch).** After Layer A passes and before commit, re-run this apply skill in dry-run mode against the same report on the now-mutated working tree; the second run's `git diff` against the post-first-run state MUST be empty. Non-empty → STRICT fail D4.

### Pipeline — Layer B (structural primitives)

Per `docs/skill-verification-architecture.md`, adversarial-critic on a
diff is wrong-shape for APPLY. Replace with deterministic structural
primitives:

**B1. AST-diff equivalence** (RefDiff, arXiv:1704.01544, precision
100% / recall 88%). For each modified file:
- Extract the AST / structural representation before and after the
  edit (Markdown heading tree for SKILL.md / rule files; JSON tree
  for .mcp.json; Python AST for hook scripts).
- Assert: the structural diff matches the finding's claimed scope.
  Edits outside the claimed-scope hunks → STRICT FAIL (F2 scope creep).
- Assert: every claimed-resolved finding has at least ONE structural
  change in its claimed-scope region.

**B2. Mutation-survival check** (Property-Based Mutation,
arXiv:2301.13615; PGS framework FSE 2025 +37.3% correctness):
- For each addressed finding, identify the failure-pattern the
  finding flagged (regex, missing section, etc.).
- Re-run that failure-pattern check against the post-edit file. If
  the pattern STILL matches → STRICT FAIL (D5 PREDICATE_REVERIFIED
  fails: the fix did not survive the pattern it claims to fix).

**B3. Refactoring-aware diff classification** (RefDiff-style):
- Classify each edit as one of: {bug-fix, refactor, formatting,
  comment-only, structural}. Refactors that introduce new
  functionality without a corresponding finding → STRICT FAIL
  (F2 over-application).

No subagent dispatch required for Layer B. All checks are
mechanical / regex / AST-based.

### Layer C — rubric reconciliation (binary CheckEval-style)

Six binary dimensions. Any `NO` blocks the commit. CheckEval (arXiv:2403.18771) reports +0.45 inter-evaluator agreement for binary vs. Likert.

```
D1 APPLY_COVERAGE         Every report H+M finding is accounted-for in claimed.json:
                          count(applied ∪ manual_only ∪ skipped) == count(H+M findings).
                          No silent drops. (F1, F4)

D2 SCOPE_FIDELITY         Anchored to B1 (AST-diff scope-match). Every diff hunk
                          maps to a `current` block in the report. Files modified
                          ⊆ report frontmatter `summary[*].path` whitelist. Every
                          `paths:` glob pattern in the pre-edit rule frontmatter
                          is byte-identical in the post-edit file (harness
                          path-scoping contract) UNLESS the report finding
                          explicitly addresses path-scoping. B1 STRICT FAIL → D2
                          NO. (F2)

D3 INVARIANT_PRESERVATION Anchored to B3 (no spurious structural changes). Each
                          modified rule file still passes: no YAML frontmatter
                          injected (Hard Rule: rules in .claude/rules/ are plain
                          Markdown); `paths:` field (when present in workspace
                          rules) remains a non-empty list of glob patterns; every
                          intra-repo cross-link (`rules/<other>.md`,
                          `references/<other>.md`, `agents/<other>.md`) in the
                          post-edit body resolves to an existing file; existing
                          Hard Rules and scope qualifiers intact; directive verbs
                          'must'/'never'/'always' not replaced with aspirational
                          'should'/'try'/'consider'. B3 classification of a
                          refactor without a corresponding finding → D3 NO.
                          (F3, F7)

D4 IDEMPOTENCY            Re-running this apply skill in dry-run mode on the same
                          report against the now-mutated tree produces an empty
                          diff. (F5)

D5 PREDICATE_REVERIFIED   Anchored to B2 (mutation-survival proves predicate
                          re-verification). For every applied finding, the
                          finding's failure-pattern no longer matches the
                          post-edit rule body. B2 STRICT FAIL → D5 NO. Rules
                          have no executable form, so for findings whose
                          validation criterion is beyond AST/regex scope,
                          re-invoke `/review-rule` on the modified file and
                          confirm the originally-flagged finding is gone. (F8)

D6 AUDIT_FIX_CHAIN        The upstream `*-review-rule.md` report is committed AND
                          its commit precedes the fix commit AND the fix commit
                          message carries the report timestamp per
                          `commit-conventions.md`
                          (`fix(<scope>): address findings from <timestamp> review`).
                          (F9)
```

**Layer → rubric crosswalk.** Layer-A `hm_coverage`/`severity_order` FAIL → D1 NO. `path_scope`/`policy_gate` FAIL → D2 NO. `invariants` FAIL → D3 NO (or D2 NO when `paths-mutated`). `report_committed` FAIL → D6 NO. Second-run non-empty diff → D4 NO. **B1** scope-match FAIL → D2 NO. **B2** mutation-survival FAIL (failure-pattern still matches post-edit) → D5 NO. **B3** uncorroborated refactor / over-application → D3 NO.

### Reconciliation outcomes

- **All STRICT Layer-A pass + B1/B2/B3 all PASS + D1–D6 = YES** → commit (report first, then fix, per Phase 4 audit-fix chain).
- **Any STRICT Layer-A fail OR any B1/B2/B3 STRICT FAIL** → propose specific restorations inline (finding IDs with file:line for missed coverage; named diff hunks for B1 scope-violations or B3 over-applications; failure-pattern names for B2 survivors; byte-identical `paths:` block restoration for path-mutation), then re-run Layer A + B. Maximum **2 iterations**; if still failing, surface to user and do NOT commit.
- **Layer-A STRICT pass + B1/B2/B3 PASS + only SOFT warnings + D1–D6 = YES** → report warnings in Phase 4 change summary, then commit.
- **D6 NO (audit-fix chain broken)** → halt. Surface the missing report commit per Phase 4 "Commit with audit-fix chain"; the reconciliation does not fix this silently.

### Acknowledged residuals (the pipeline does NOT catch these)

Adversarial-critic Layer B is replaced by structural primitives per docs/skill-verification-architecture.md; semantic equivalence checks beyond AST scope are out-of-scope and route to `/review-rule` post-apply.

1. **R1 Semantic equivalence under syntactic divergence.** Recommendation text and actual edit may be syntactically different but semantically equivalent (reordered list items, paraphrased prose, synonyms for the same constraint). B1's AST-diff treats reorderings as structural changes; operator reconciles via post-apply `/review-rule`. Source: arXiv:2301.01113 (Invalidator).
2. **R2 Cross-file semantic coupling.** An edit to one rule may break an unstated assumption in a sibling rule or in `references/*.md` (e.g. a constraint removed here that another rule's body silently relies on). The pipeline checks intra-repo link existence but not behavioral coupling. Mitigation: run `/review-claude-config` on the broader repo after apply.
3. **R3 Validation criteria beyond AST/regex scope.** When `validation:` requires observing operational behavior (e.g. "rule loads in next session", "harness path-scoping fires correctly"), B2 cannot decide. Operator must invoke `/review-rule` on the modified file or observe behavior in a fresh session.
4. **R4 Pragmatic / register drift in prose edits.** Curt "Never bypass." vs softer "Bypassing is discouraged" — both directions entail under NLI; only register-aware human review catches.

## Hard Rules

- **Edit-only operations.** Never delete files. Never create new files. Only edit existing files.
- **No frontmatter injection.** Rules are plain Markdown. Never add YAML frontmatter to a rule file.
- **Scope restriction.** Only edit files listed in the review report's `summary` section.
- **Preview before every edit.** Always show current and recommended text before applying.
- **Preserve review context.** Always carry `Evidence`, `Why it matters`, and `Validation` through previews even though `Current`/`Recommended` remain the edit anchors.
- **User confirmation at every stage.** Confirm before starting, before each edit, and before committing.
- **Audit-fix chain.** Always commit the report before committing fixes.
- **Preserve file structure.** Edits replace text blocks only. Never rewrite entire files.
- **High/Medium first.** Always process High and Medium recommendations before Low. Low impact recommendations are only offered after High/Medium are resolved, or when no High/Medium exist.

## Tier A Tool Justification

**Tier A tool justification (Bash):** Bash is granted for git operations, `realpath`, and `bash bin/repo-slug.sh "$(pwd)"` to compute the canonical `<repo-slug>` deterministically per `references/repo-identification.md`. The command-level allowlist `Bash(bash bin/repo-slug.sh:*)` enforces the slug-resolver scope. The slug-resolver script is read-only (stdout slug, no FS writes), so that grant carries no write-amplification risk.
