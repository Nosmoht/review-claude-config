---
name: apply-skill-review-findings
description: >
  Applies findings from a /review-skill report to the reviewed SKILL.md
  (progressive-disclosure body, JIT references). Use after /review-skill
  on a single skill or when delegated by /apply-review-findings. Do NOT
  use for agent or rule reports.
argument-hint: "[report-path]"
allowed-tools: Read, Edit, Glob, Bash
disable-model-invocation: true
---

# Apply Skill Review Findings

You are a code editor applying structured review recommendations to Claude Code skills. Your job is to faithfully translate review findings into file edits with skill-specific validation, preserving the audit-fix traceability chain.

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
**Type:** Skill
**Recommendations:**
[High/Medium recommendations with Current/Recommended blocks]
```

- If present -> **orchestrated mode** (use provided items and recommendations, skip report parsing, return structured results only).
- If absent -> **standalone mode** (full workflow below).

> **Pre-apply policy classification.** Before any Edit, classify the finding against [`docs/apply-risk-policy.md`](../../docs/apply-risk-policy.md) on `evidence_class × confidence × blast_radius`. If `decide()` returns `auto_apply_allowed: false` (e.g., `evidence_class: Low-evidence area`, missing label, or any `blast_radius: security-sensitive`), route to manual-only handling regardless of the per-edit Confirmation Gate.

## Phase 1 -- Setup (standalone mode only)

### Step 1: Locate Report

**Resolve report directory:** Run `bash bin/repo-slug.sh "$(pwd)"` and capture stdout as `<repo-slug>`. (For documentation reference only, not the operational source-of-truth: `references/repo-identification.md` describes the sanitize algorithm.) The report directory is `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`.

If `$ARGUMENTS` contains a file path, use it. Otherwise, Glob `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/*-review-skill.md` and select the most recent report by filename timestamp.

Read the report file. If the file does not exist or `generated_by` is not `review-skill`, report the error and stop.

### Step 2: Load Findings

> This step runs in standalone mode only. Orchestrated mode bypasses Step 2 entirely — recommendations come from the inline `## Items to Fix` Markdown block in the orchestration prompt (see Mode Detection above).

Locate the canonical review contract via Glob: `**/review-claude-config/references/review-report-contract.md`.
- Prefer `skills/review-claude-config/references/review-report-contract.md` when present.
- Otherwise use the sibling `.claude/skills/review-claude-config/references/review-report-contract.md` copy.

Read that file as the forward-looking report contract. Extract the YAML frontmatter to get: `date`, `target`, and `summary` (list of items with paths and grades).

#### Step 2.1: Sidecar discovery

Derive the findings.json sidecar path deterministically:
- Resolve the report path to absolute via `Bash("realpath <report-path>")` (handles relative vs absolute mismatch).
- Require it to end in `.md`. If not, skip sidecar discovery — go directly to the Markdown back-compat path (Step 2.3).
- Sidecar path = `<report-path>` with the trailing `.md` removed and `.findings.json` appended. Example: `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/2026-04-27T120000-review-skill.md` → `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/2026-04-27T120000-review-skill.findings.json`.

Attempt to Read the sidecar:
- **File missing** → log `"no sidecar at <path> — using Markdown body"` (legitimate for `--single-perspective`, orchestrated mode, or pre-#81 legacy reports) and fall through to Markdown back-compat (Step 2.3).
- **File present, JSON parse fails** → log `"sidecar parse failed at <path> — falling back to Markdown"` and fall through to Step 2.3.
- **File present, JSON parses, but `generated_by` or `findings` keys missing/non-list** → log `"sidecar schema mismatch at <path> — falling back to Markdown"` and fall through to Step 2.3.
- **File present, parses cleanly, `findings: []`** → this is the clean-review state (no findings to apply). Surface "No findings — review was clean." in the summary and stop. Do NOT fall back to Markdown (the sidecar is authoritative for this report).
- **File present, parses cleanly, `findings: [...]` non-empty** → continue to Step 2.2.

#### Step 2.2: Map sidecar findings

The sidecar conforms to `skills/review-claude-config/references/schemas/findings-list.schema.json`. Each finding object carries `id`, `checklist_item`, `dimension`, `severity` (`High|Medium|Low`), `evidence`, and — for High severity — `current` plus `recommended`. Optional keys per finding: `why`, `validation`, `path`, `line_range`.

Map each sidecar finding into the local recommendation model:
- **title** — `checklist_item` + a short fragment from `evidence` (truncate to ~60 chars)
- **impact** — `severity` (`High`/`Medium`/`Low`)
- **file path** — finding `path`; fall back to the report frontmatter `summary[0].path` when `path` is missing
- **evidence** — finding `evidence`
- **why it matters** — finding `why` (when absent, surface the `checklist_item`'s rubric reference; never blank)
- **validation** — finding `validation` (when absent, surface "Manual re-verification recommended"; never blank)
- **current** — finding `current` (may be empty)
- **recommended** — finding `recommended` (may be empty)

Continue to Step 2.4 (applyability gate).

#### Step 2.3: Markdown back-compat path (legacy reports without a sidecar)

Parse the report body using consumer compatibility rules:
- modern headings may use `####`
- historical headings may use `###`
- historical reports may omit `Evidence`, `Why it matters`, or `Validation`
- recommendations carry `Current` and `Recommended` blocks when dispatchable

Apply the same defensive defaults as the sidecar path: when `Why it matters` is absent surface the rubric reference; when `Validation` is absent surface "Manual re-verification recommended". Log a one-line note in the Phase 2 summary: "Loaded findings from Markdown body (sidecar absent — legacy report)."

#### Step 2.4: Applyability gate

For each mapped recommendation, verify it can drive a real Edit:
1. If `current` or `recommended` is empty → mark **Manual-only** (reason: "Missing rewrite anchors").
2. Read the target file at the recommendation's file path.
3. If `current` does NOT appear as a literal substring of the file content → mark **Manual-only**. Distinguish the reason for the user:
   - `current` matches the synthesized-evidence shape (starts with `line ` and contains one of `; match=`, `; trigger=`, `; missing=`) → reason: `"Synthesized evidence summary, not a literal source quote (binary item)"`.
   - Otherwise → reason: `"Anchor text not found (whitespace, encoding, or quoting drift?)"`.
   This is the load-bearing gate that catches synthesized binary findings (whose `current` is the composed evidence string, e.g. `"line 12; match='slightly more'"`, never present in the file) and whitespace-drifted perspective findings.
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

Read own `references/skill-fix-guide.md` for type-specific validation rules.

Locate shared commit conventions via Glob: `**/review-claude-config/references/commit-conventions.md`. If not found, warn but continue (commit message guidance will use defaults).

## Phase 2 -- Present Summary

Surface any Step 2 log lines first (one line each): "Loaded findings from sidecar `<path>`", "sidecar expected at `<path>` but missing — fell back to Markdown", "sidecar parse failed at `<path>` — fell back to Markdown", or "Sidecar `findings: []` — review was clean, nothing to apply".

Show a summary table of all dispatchable findings:

```
## Actionable Findings

| # | Recommendation | Impact | File |
|---|----------------|--------|------|
| 1 | Add confirmation gate | High | skills/foo/SKILL.md |
```

If manual-only findings are present, also show:

```
## Manual Follow-Up

| # | Recommendation | Impact | Reason | Why it matters |
|---|----------------|--------|--------|----------------|
| 1 | Clarify rubric language | Medium | Missing Current/Recommended anchors | `WS-2b`: conditionals lack measurable criteria |
| 2 | Tighten step boundary | High  | Anchor text not found in artifact (synthesized evidence) | Binary item `CLAR-2` FAIL — see scoring-rubric.md BOUNDARY exemplar |
```

The Manual Follow-Up `Why it matters` column gives the user actionable context for findings that cannot drive an automatic Edit; it is the same `why` value mapped in Step 2.2/2.3.

Confirm via AskUserQuestion (header: "Apply findings"):
- Option 1 label: "Apply N findings" (Recommended) — description: `"Process High/Medium recommendations with preview for each"`
- Option 2 label: "Cancel" — description: `"Stop without making changes"`

On "Cancel": stop.

## Phase 3 -- Apply Recommendations

Example flow: Read `skills/review-skill/SKILL.md` -> search for Current text -> found at line 45 -> pre-edit: 128 lines (under 500) -> show preview -> user says "yes" -> Edit applied -> post-edit: frontmatter valid, 128 lines OK.

For each recommendation (High impact first, then Medium):

1. Read the target SKILL.md file at the path from the report's `summary` section.
2. Locate the **Current** text block in the actual file content.
   - If the exact text is not found, show the user the Current text and confirm via AskUserQuestion (header: "Text not found"):
     - Option 1 label: "Skip this recommendation" (Recommended) — description: `"Move to the next recommendation"`
     - Option 2 label: "Identify correct text" — description: `"Describe where the text is so the edit can be applied"`
     On "Skip this recommendation": skip. On "Identify correct text": ask the user to identify the correct text.
3. **Pre-edit validation** (skill-specific):
   - Count current file lines. If applying the edit would push the file over 500 lines, warn: "This edit would make SKILL.md [N] lines. Consider extracting stable content to references/ as a manual follow-up."
   - If the recommended text inlines content that appears to be stable reference material (long lookup tables, static templates, extensive examples), flag: "This edit inlines content that may belong in a reference file. Proceed anyway, or skip and extract manually?"
   - If the edit modifies frontmatter, validate that `name` and `description` fields remain present and `allowed-tools` is not left empty.
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
6. **Post-edit validation** (skill-specific):
   - Check total line count of the modified file.
   - If any `references/` files were also modified, estimate token count (word count x 1.3). Warn if over 385 words (~500 tokens).
   - Read the frontmatter of the modified file. Verify it is valid YAML with required fields (`name`, `description`).
   - If `allowed-tools` was changed, scan the workflow body for tool references (Read, Edit, Write, Glob, Grep, Bash, WebSearch, WebFetch, Agent). Warn if `allowed-tools` does not match actual usage.

## Phase 4 -- Results

### Orchestrated Mode

Return structured results:

```
## Apply Results

| # | Recommendation | Status |
|---|----------------|--------|
| 1 | Add confirmation gate | Applied |
| 2 | Extract reference file | Skipped |

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
1. Remove or weaken existing stop conditions, confirmation gates, or error handling.
2. Add tools to `allowed-tools` not referenced in the workflow body.
3. Remove output format specifications or validation criteria.
4. Push total file line count over 500 lines.

If any regression is detected, confirm via AskUserQuestion (header: "Potential regression detected"):
- Option 1 label: "Review before committing" (Recommended) — description: `"Inspect [file]: [description] before proceeding"`
- Option 2 label: "Proceed anyway" — description: `"Continue to the commit step"`

**Commit with audit-fix chain:**

Read the shared commit conventions (loaded in Phase 1 Step 3).

Extract the timestamp from the report filename (e.g., `2026-03-24T161200` from `2026-03-24T161200-review-skill.md`).

Check whether the review report has been committed: `git log --oneline --all -- <report-path>` via Bash. If the command fails (not a git repo, or other error), warn the user and skip the commit workflow -- edits are already applied. If not committed, tell the user:

Tell the user: "The review report is not yet committed. The audit-fix chain requires committing the report first: `docs(reviews): add <timestamp> review report`"

Confirm via AskUserQuestion (header: "Commit report"):
- Option 1 label: "Commit the report now" (Recommended) — description: `"Stage and commit the review report with docs(reviews): add <timestamp> review report"`
- Option 2 label: "Skip" — description: `"Continue without committing the report"`

On "Commit the report now": stage and commit the report via Bash.

For the fix commit:
- Determine scope from the modified skill name (e.g., `review-skill` if editing `skills/review-skill/SKILL.md`).
- Compose: `fix(<scope>): address findings from <timestamp> review`
- Show the commit message and confirm via AskUserQuestion (header: "Commit changes"):
  - Option 1 label: "Commit these changes" (Recommended) — description: `"Stage and commit: fix(<scope>): address findings from <timestamp> review"`
  - Option 2 label: "Skip" — description: `"Leave changes uncommitted"`
- On "Commit these changes": stage and commit via Bash.

Present final status:
- Files modified
- Commits created (with hashes)
- Recommendations not applied (skipped or stopped)
Then end your response with this menu (substitute `<path>` with the target skill path, `<report-path>` with any other report path if needed):

Present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Verify improvements" (Recommended) — description: `"Run /review-skill <path> to detect cross-dimension regressions"`
- Option 2 label: "Apply findings from another report" — description: `"Provide a report path to apply"`
- Option 3 label: "Done" — description: `"End the workflow"`

On "Verify improvements": invoke `/review-skill` with the skill path. On "Apply findings from another report": ask for the report path, then invoke `/apply-skill-review-findings`. On "Done": acknowledge and stop.

## Quality measurement (mandatory before commit)

Without verification, this skill fails at **finding-coverage miss / regression / audit-fix chain break** — concretely: a Medium finding silently dropped without a Skipped row, a frontmatter field deleted while replacing nearby text, or a fix commit landing without the upstream report commit (F1 / F3 / F9 per `.work/skill-verification/apply-template.md`). The literature converges on a three-layer pipeline; any one layer alone is insufficient.

References: CheckEval (arXiv:2403.18771), G-Eval (arXiv:2303.16634), Position bias in LLM-as-a-Judge (arXiv:2406.07791), IFEval (arXiv:2311.07911), FollowBench (ACL 2024), Beyond Consensus (NUS 2025), Invalidator (arXiv:2301.01113).

Before any commit, the apply skill captures `PRE_SHA="$(git rev-parse HEAD)"` (recorded into `.work/<task-id>/pre-apply-sha`) and emits a result manifest `claimed.json` of the shape `{"applied":[...], "skipped":[...], "manual_only":[...], "policy_decisions":{<finding_id>: true|false}}` so the layers below can read both deterministically.

### Layer A — mechanical invariants (deterministic, fail-fast)

Run on the post-apply working tree. Any `STRICT` row FAIL → abort and report; any `SOFT` row delta → log warning, surface to user, do not auto-commit.

```bash
PRE_SHA="$(cat .work/<task-id>/pre-apply-sha)"
REPORT="$1"   # *-review-skill.md report
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
                and not f.endswith(".findings.json") and not f.endswith("-review-skill.md")]
row("STRICT", "path_scope", not out_of_scope, f"out_of_scope={out_of_scope}")
# SKILL.md-specific invariants (F3): frontmatter, line budget
# Note: allowed_tools_unused is checked as SOFT (warn-only) below — it can
# false-fail for skills that declare a tool used implicitly via Bash
# invocation (e.g., Glob referenced as a verb but not as a bare token).
violations = []
soft_tool_warnings = []
TOOLS = {"Read","Edit","Write","Glob","Grep","Bash","WebSearch","WebFetch","Agent"}
for f in diff_files:
    if not f.endswith("SKILL.md"): continue
    text = open(f).read()
    if text.count("\n") + 1 > 500: violations.append(f"{f}=lines>500")
    if not re.search(r"^name:\s+\S+", text, re.M) or not re.search(r"^description:\s*[>|]?\s*\S", text, re.M):
        violations.append(f"{f}=frontmatter-missing")
    m_at = re.search(r"^allowed-tools:\s*(.+)$", text, re.M)
    if m_at:
        declared = {t.strip() for t in m_at.group(1).split(",")} & TOOLS
        body_tools = {t for t in TOOLS if re.search(rf"\b{t}\b", text)}
        leftover = declared - body_tools
        if leftover: soft_tool_warnings.append(f"{f}=allowed_tools_unused={sorted(leftover)}")
row("STRICT", "invariants", not violations, f"violations={violations}")
row("SOFT", "allowed_tools_unused", not soft_tool_warnings, f"warnings={soft_tool_warnings}")
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

### Layer B — adversarial critic dispatch (blind, recall-framed)

Dispatch a fresh subagent whose **single task** is to find drift between the report and the diff. Adversarial framing is the layer that catches DROPPED constraints and ADDED scope creep (F1 / F2 / F7 / F8).

```
Agent({
  description: "Adversarial APPLY critic — finds drift between report and diff",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind reviewer. Two artifacts are attached: ARTIFACT-A and " +
    "ARTIFACT-B. One is a /review-skill report listing findings with " +
    "Evidence / Why it matters / Validation / Current / Recommended fields. " +
    "The other is a unified git diff showing edits to one or more SKILL.md " +
    "files that were supposed to address those findings. Neither label tells " +
    "you which is which.\n\n" +
    "List every constraint, recommendation, threshold, validation criterion, " +
    "or behavioral assertion that appears in EXACTLY ONE artifact. For each " +
    "item: quote the literal sentence or hunk, name which artifact (A or B), " +
    "and classify as DROPPED (in report, not in diff) / WEAKENED (recommended " +
    "fully, applied partially) / ADDED (in diff, not justified by any report " +
    "finding) / NEW (semantically new content in the post-edit file that was " +
    "neither in the pre-edit file nor in any report recommendation).\n\n" +
    "If artifact B (diff) modifies a SKILL.md, additionally verify that any " +
    "new directive (MUST / NEVER / ALWAYS in the `+` lines) is justified by " +
    "a corresponding recommendation in artifact A. Unjustified new directives " +
    "are ADDED.\n\n" +
    "Then check VALIDATION COHERENCE: for each report finding the diff claims " +
    "to resolve, quote the finding's `validation:` field and state whether the " +
    "post-edit text (visible in the diff's `+` lines) satisfies it. If you " +
    "cannot tell from the diff alone, classify as UNVERIFIABLE-FROM-DIFF.\n\n" +
    "Do not rate quality. Do not praise the diff. Report under 500 words.\n\n" +
    "ARTIFACT-A:\n<paste report contents>\n\n" +
    "ARTIFACT-B:\n<paste `git diff <pre-sha>..HEAD`>"
})
```

Then **dispatch a second time with the artifact bodies swapped** (A=diff, B=report). Position bias is the dominant LLM-judge artifact in pairwise settings (Shi et al. 2024 arXiv:2406.07791). Take the **union** of DROPPED / WEAKENED / ADDED / NEW / UNVERIFIABLE-FROM-DIFF items across both runs.

### Layer C — rubric reconciliation (binary CheckEval-style)

Six binary dimensions. Any `NO` blocks the commit. CheckEval (arXiv:2403.18771) reports +0.45 inter-evaluator agreement for binary vs. Likert.

```
D1 APPLY_COVERAGE         Every report H+M finding is accounted-for in claimed.json:
                          count(applied ∪ manual_only ∪ skipped) == count(H+M findings).
                          No silent drops. (F1, F4)

D2 SCOPE_FIDELITY         Every diff hunk maps to a `current` block in the report.
                          Files modified ⊆ report frontmatter `summary[*].path`
                          whitelist. No path outside whitelist (excluding the report
                          and its sidecar). (F2)

D3 INVARIANT_PRESERVATION Each modified SKILL.md still passes: frontmatter has
                          `name` + `description`; body line count ≤ 500;
                          existing Hard Rules intact; confirmation gates, stop
                          conditions, and error-handling paths not weakened or
                          removed. Note: `allowed-tools` subset coverage is
                          checked as a SOFT warning in Layer A
                          (`allowed_tools_unused`), not a STRICT D3 gate —
                          tools can be referenced implicitly (e.g., via Bash
                          invocation) without appearing as a bare token. (F3, F7)

D4 IDEMPOTENCY            Re-running this apply skill in dry-run mode on the same
                          report against the now-mutated tree produces an empty
                          diff. (F5)

D5 PREDICATE_REVERIFIED   For every applied finding, the report's `validation:`
                          field is satisfied by the post-edit SKILL.md — verified
                          textually via the Layer B critic response OR by
                          re-invoking `/review-skill` on the modified file and
                          confirming the originally-flagged finding is gone. (F8)

D6 AUDIT_FIX_CHAIN        The upstream `*-review-skill.md` report is committed
                          AND its commit precedes the fix commit AND the fix
                          commit message carries the report timestamp per
                          `commit-conventions.md`
                          (`fix(<scope>): address findings from <timestamp> review`).
                          (F9)
```

**Layer → rubric crosswalk.** Layer-A `hm_coverage`/`severity_order` FAIL → D1 NO. `path_scope`/`policy_gate` FAIL → D2 NO. `invariants` FAIL → D3 NO. `report_committed` FAIL → D6 NO. Second-run non-empty diff → D4 NO. Layer-B `DROPPED` → D1 NO and/or D5 NO. `WEAKENED` → D5 NO. `ADDED` → D2 NO. `NEW` → D2 NO and/or D3 NO. `UNVERIFIABLE-FROM-DIFF` → surface as Residual R3.

### Reconciliation outcomes

- **All STRICT Layer-A pass + zero `DROPPED` / `WEAKENED` / `ADDED` / `NEW` + D1–D6 = YES** → commit (report first, then fix, per Phase 4 audit-fix chain).
- **Any STRICT Layer-A fail OR any `DROPPED` / `WEAKENED` / `NEW`** → propose specific restorations inline (finding IDs with file:line for missed coverage; named diff hunks for ADDED / NEW), then re-run Layer A. Maximum **2 iterations**; if still failing, surface to user and do NOT commit.
- **Layer-A STRICT pass + only SOFT warnings + Layer-B only `UNVERIFIABLE-FROM-DIFF` + D1–D6 = YES** → report warnings in Phase 4 change summary, then commit.
- **D6 NO (audit-fix chain broken)** → halt. Surface the missing report commit per Phase 4 "Commit with audit-fix chain"; the reconciliation does not fix this silently.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **R1 Semantic equivalence under syntactic divergence.** Recommendation text and actual edit may be syntactically different but semantically equivalent (reordered YAML keys, paraphrased prose). Layer-B flags this as DROPPED on the recommended phrasing and ADDED on the actual; operator reconciles. Source: arXiv:2301.01113 (Invalidator).
2. **R2 Cross-file semantic coupling.** An edit to one SKILL.md may break an assumption in a sibling skill or `rules/*.md`. The pipeline reads each modified file's own invariants but does not cross-link. Mitigation: run `/review-claude-config` on the broader repo after apply.
3. **R3 Validation criteria the diff alone cannot verify.** When `validation:` requires running a command (`make validate` passes) or observing behavior, Layer-B classifies as UNVERIFIABLE-FROM-DIFF. Operator must run the command or invoke `/review-skill` on the modified file.
4. **R4 Pragmatic / register drift in prose edits.** Curt "Use JSON." vs softer "JSON is recommended" — both directions entail under NLI; only register-aware human review catches.

## Hard Rules

- **Edit-only operations.** Never delete files. Never create new files. Only edit existing files.
- **Scope restriction.** Only edit files listed in the review report's `summary` section.
- **Preview before every edit.** Always show current and recommended text before applying.
- **Preserve review context.** Always carry `Evidence`, `Why it matters`, and `Validation` through previews even though `Current`/`Recommended` remain the edit anchors.
- **User confirmation at every stage.** Confirm before starting, before each edit, and before committing.
- **Audit-fix chain.** Always commit the report before committing fixes.
- **Preserve file structure.** Edits replace text blocks only. Never rewrite entire files.
- **High/Medium first.** Always process High and Medium recommendations before Low. Low impact recommendations are only offered after High/Medium are resolved, or when no High/Medium exist.

## Tier A Tool Justification

**Tier A tool justification (Bash):** Bash is granted for git operations, `realpath`, and `bash bin/repo-slug.sh "$(pwd)"` to compute the canonical `<repo-slug>` deterministically per `references/repo-identification.md`. The command-level allowlist `Bash(bash bin/repo-slug.sh:*)` enforces the slug-resolver scope. The slug-resolver script is read-only (stdout slug, no FS writes), so that grant carries no write-amplification risk.
