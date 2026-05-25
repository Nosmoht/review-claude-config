---
name: review-analytics
description: >
  Parses accumulated review reports, computes grade trajectories, and detects
  regressions. Use to 'track review results', 'show quality trends', or
  'analyze review history'. Do NOT use for freshness or integrity — use
  /check-repo-health.
argument-hint: "[folder] [--validation]"
allowed-tools: Bash, Read, Glob
---

# Review Analytics

You are a quality analyst tracking skill grades over time. Your job is to surface trends, regressions, and improvements from the review report archive.

## Workflow

### 1. Discover review reports

If `$ARGUMENTS` contains the standalone token `--validation`, set `validation_mode = true` and remove that token from the argument string. Use the remaining argument text as the target folder.

If no target folder remains, use the current working directory.

**Resolve report directory:** Run `bash bin/repo-slug.sh "$(pwd)"` and capture stdout as `<repo-slug>`. (For documentation reference only, not the operational source-of-truth: `references/repo-identification.md` describes the sanitize algorithm.) The report directory is `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`.

Glob `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/*-review-*.md` to find all review reports. Sort by filename (timestamps sort lexicographically).

When no target is specified (CWD mode), also support cross-repo analysis: Glob `${HOME}/.claude/plugins/data/claude-config/reports/**/*-review-*.md` to discover reports across all repos.

If no reports are found, tell the user: "No review reports found in `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`." Stop.

### 2. Parse report frontmatter

Locate the canonical review contract via Glob: `**/review-claude-config/references/review-report-contract.md`.
- Prefer `skills/review-claude-config/references/review-report-contract.md` when present.
- Otherwise use the sibling `.claude/skills/review-claude-config/references/review-report-contract.md` copy.

Read that file for the forward-looking frontmatter and identity contract. Use `skills/review-claude-config/references/report-schema.md` for analytics-specific compatibility notes and producer partition rules.

For each report, read the YAML frontmatter and extract:
- `date` — report date
- `generated_by` — report producer (`review-claude-config`, `review-skill`, `review-agent`, `review-rule`)
- `items_reviewed` — count
- `summary` — array of items with: `name`, `type`, `path`, `overall`, `score`, `clarity`, `completeness`, `prompt_engineering`, `context_engineering`, `goal_alignment`, `safety`, `metadata`

Skip any report whose `generated_by` is not one of the supported review producers above.

Treat `type + path` as the artifact key and `repo + generated_by + type + path` as the series key (where `repo` is the `<repo-slug>` derived from the report's parent directory under `reports/`). Treat `name` as a display label only.

If a report has malformed or missing frontmatter, skip it with a warning: "Skipped report `<filename>`: could not parse frontmatter."

Extract the timestamp from each filename for display (e.g., `2026-03-24T161200`).

If `validation_mode = true`, after filtering unsupported or malformed reports, keep only the 10 most recent supported, parseable reports.

After filtering (and validation-mode capping, if active):
- If no supported, parseable reports remain, tell the user: "No supported review reports found in `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`." Stop.
- If exactly one supported, parseable report remains, present the single-report summary path and note: "Trend analysis requires at least 2 supported review reports." Stop.

### 3. Build time series

For each unique `generated_by + type + path` combination across all reports, build a time series:
- Track the `overall` grade and `score` at each report timestamp.
- Track per-dimension grades: clarity, completeness, prompt_engineering, context_engineering, goal_alignment, safety, metadata.

For Rule reports, `prompt_engineering`, `context_engineering`, `safety`, and `metadata` are `null`. Exclude `null` values from all dimension averages, lowest-item selection, and systemic-regression logic.

Handle items that appear or disappear across reports:
- **New item:** First appearance marked as "New" (no prior data point).
- **Removed item:** Last seen in an older report but absent in the most recent. Marked as "Removed."
- **Rename/move candidate:** A path disappears and a new path appears for the same producer and type in the next report. Flag it as a candidate instead of silently merging by `name`.

### 4. Compute trajectories

For each item, classify its overall trajectory:
- **Improving** — Latest grade is higher than the earliest, OR score increased by ≥5 points.
- **Stable** — Grade unchanged across all reports, AND score variation < 5 points.
- **Regressing** — Latest grade is lower than the previous report, OR score dropped by ≥5 points.

Example: B(82) → B(86) → B(81) is Stable (grade unchanged, variation < 5). B(82) → A(90) → B(85) is Regressing (latest grade lower than previous by ≥1 grade-step or ≥5 score points).

For each dimension, compute the average grade across only the items where that dimension is non-null in the most recent report and compare against the earliest report to determine dimension-level trends.

### 5. Present analysis

If `validation_mode = true`, present only:

```markdown
## Validation Summary

- Mode: validation
- Reports analyzed: M
- Series analyzed: N
- Latest regressions: X
- New items: Y
- Removed items: Z

### Regressions
- ...

### New Items
- ...

### Removed Items
- ...
```

In validation mode:
- do not render the full timestamp-wide trajectory matrix
- do not render the full dimension heatmap table
- keep producer partitioning and path-first identity exactly the same
- omit the follow-up menu

Otherwise present the normal three views below.

Present three views:

**View 1: Grade Trajectories**
```
## Grade Trajectories

| Producer | Item Path | Display Name | [timestamp 1] | [timestamp 2] | ... | Trend |
|----------|-----------|--------------|---------------|---------------|-----|-------|
| review-claude-config | skills/review-claude-config/SKILL.md | review-claude-config | B (85.0) | A (93.5) | ... | Improving |
| review-skill | .claude/skills/refresh-engineering-baseline/SKILL.md | refresh-engineering-baseline | B (82.0) | A (93.1) | ... | Improving |

Items tracked: N | Reports analyzed: M
```

**View 2: Dimension Heatmap**
```
## Dimension Analysis (Latest Report)

| Dimension | Avg Grade | Lowest Item | Trend vs First |
|-----------|-----------|-------------|----------------|
| Clarity | A | refresh-baseline (A) | Stable |
| Safety | A | review-config (B) | Improving |
```

**View 3: Alerts**
```
## Alerts

### Regressions
- [item]: [dimension] dropped from [grade] to [grade] between [timestamp] and [timestamp]

### New Items (since first report)
- [item]: first appeared in [timestamp] with grade [grade]

### Removed Items
- [item]: last seen in [timestamp] with grade [grade]

### Rename/Move Candidates
- [old path] → [new path]: same type, path changed, review manually before treating as continuity

### Systemic Issues
- [dimension] regressed across 2+ items simultaneously (possible systemic cause)
```

If no regressions, new items, removed items, or systemic issues exist, show: "No alerts. All items stable or improving."

**View 4: Convergence Analysis**

For each artifact with 2+ reports, analyze finding-level stability:

1. Parse recommendation headings in report bodies for `finding_id` values (format: `{checklist_item}:{path}:{dimension}/v1`). If report bodies are not available (frontmatter-only), skip View 4 with note "Convergence analysis requires report bodies."

2. For the two most recent reports per artifact, classify each finding_id:
   - `recurring` — present in both reports
   - `new` — present only in latest
   - `fixed` — present only in previous

3. For each artifact with 3+ reports, compute max grade variance per dimension (difference between highest and lowest grade across all reports).

4. Convergence verdict per artifact:
   - **Converged** — latest two reports share all High/Medium finding_ids AND max grade variance ≤1 per dimension AND no dimension is null in latest where previous had a non-null grade
   - **Not converged** — any High/Medium finding_id differs OR dimension variance >1 OR null-dimension regression

```
## Convergence Analysis

| Artifact | Reports | Recurring | New | Fixed | Max Grade Var | Converged? |
|----------|---------|-----------|-----|-------|---------------|------------|

[If no artifact has 2+ reports: "Insufficient data for convergence analysis (requires 2+ reports per artifact)."]
```

### 6. Summary

Present a one-line summary:
```
**Portfolio quality: [Improving/Stable/Declining]** — N items across M reports, X regressions detected.
```

Classification:
- **Improving** — Majority of items improving, no regressions in latest report.
- **Stable** — No items regressing, majority stable.
- **Declining** — Any item regressing in the latest report, or systemic dimension regression.

If any regressions were detected (classification is "Declining"), present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Review regressing items" (Recommended) — description: `"Run /review-claude-config to re-evaluate and detect regressions"`
- Option 2 label: "Done" — description: `"End the workflow"`

On "Review regressing items": invoke `/review-claude-config`. On "Done": acknowledge and stop.

If no regressions (classification is "Improving" or "Stable"), skip the menu — just present the dashboard.

## Quality measurement (mandatory before presenting the dashboard)

Without verification, this skill fails at TRAJECTORY-WRONG (a series classified Improving / Stable / Regressing whose dimension-grade history as cited in the dashboard does not match the rule from §"Compute trajectories" — e.g., B(82) → A(90) → B(85) labeled Stable when the latest-vs-previous drop ≥1 grade step makes it Regressing), ALERT-MISSED (a regression in the underlying time series — latest grade lower than previous OR score drop ≥5 — that the Alerts view does not surface), SERIES-MERGED-BY-NAME (two distinct `(repo, generated_by, type, path)` series collapsed on `name` alone, contradicting §"Track by path first, partition by producer"), and SCOPE-DROP (a report present in the requested folder but absent from the analyzed set without a documented filter-reason — malformed, unsupported `generated_by`, or validation-mode 10-report cap). The three-layer pipeline below catches all four.

References: CheckEval (arXiv:2403.18771), G-Eval (arXiv:2303.16634), Position bias in LLM-as-a-Judge (arXiv:2406.07791), IFEval (arXiv:2311.07911), FollowBench (Jiang et al. ACL 2024), Beyond Consensus (NUS 2025), `skills/review-claude-config/references/review-report-contract.md`, `skills/review-claude-config/references/report-schema.md`, `skills/review-claude-config/references/merge-rules.md`.

Serialize the assembled dashboard (all rendered views from §5 plus the §6 Summary line) to a tempfile for the duration of this section. Set `DASHBOARD_PATH` to that tempfile. Set `REPORTS_DIR` to the resolved `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/` (or the cross-repo glob root when in CWD mode). Set `CONSUMED_LIST` to the explicit list of report filenames whose frontmatter was successfully parsed and included in the time series (post-filter, post-validation-cap).

### Layer A — mechanical invariants (deterministic, fail-fast)

Run on the assembled dashboard. STRICT failures block dashboard presentation; SOFT warnings surface as a `Layer-A warnings` note appended to the dashboard.

```bash
python3 - "$DASHBOARD_PATH" "$REPORTS_DIR" "$CONSUMED_LIST" "${VALIDATION_MODE:-false}" <<'PY'
import sys, re, os, glob
from pathlib import Path

DASH      = Path(sys.argv[1])
REPDIR    = sys.argv[2]
CONSUMED  = set(l.strip() for l in Path(sys.argv[3]).read_text().splitlines() if l.strip())
VALIDATION = sys.argv[4].lower() == "true"

GRADE_VOCAB = {"A","B","C","D","F"}
TREND_VOCAB = {"Improving","Stable","Regressing"}
PORTFOLIO_VOCAB = {"Improving","Stable","Declining"}

text = DASH.read_text()
errors, warns = [], []

# --- Required sections per mode ---
sections = [s.group(1).strip() for s in re.finditer(r"^##\s+(.+)$", text, re.M)]
if VALIDATION:
    required = ["Validation Summary"]
    forbidden = ["Grade Trajectories","Dimension Analysis","Alerts","Convergence Analysis"]
    for k in required:
        if not any(s.startswith(k) for s in sections):
            errors.append(f"STRICT: validation mode missing required section '{k}'; found={sections}")
    for k in forbidden:
        if any(s.startswith(k) for s in sections):
            errors.append(f"STRICT: validation mode must not render section '{k}'")
else:
    required = ["Grade Trajectories","Dimension Analysis","Alerts","Convergence Analysis"]
    pos = {k: next((i for i,s in enumerate(sections) if s.startswith(k)), -1) for k in required}
    if any(v == -1 for v in pos.values()):
        errors.append(f"STRICT: missing required section heading from {required}; found={sections}")
    elif sorted(pos.values()) != list(pos.values()):
        errors.append("STRICT: section order violates Grade Trajectories->Dimension Analysis->Alerts->Convergence Analysis")

# --- Scope discipline: every parseable report in REPORTS_DIR must be in CONSUMED (D6) ---
if os.path.isdir(REPDIR):
    on_disk = {os.path.basename(p) for p in glob.glob(os.path.join(REPDIR, "*-review-*.md"))}
    if not VALIDATION:
        missing = on_disk - CONSUMED
        if missing:
            errors.append(f"STRICT: SCOPE-DROP — reports present in {REPDIR} not in analyzed set: {sorted(missing)} (must be documented as filtered: malformed | unsupported generated_by)")
    else:
        # In validation mode the 10-most-recent cap is expected; only fail if
        # CONSUMED exceeds 10 or if filter-skipped reports were never noted.
        if len(CONSUMED) > 10:
            errors.append(f"STRICT: validation mode kept {len(CONSUMED)} reports; cap is 10")

# --- Series identity: every trajectory row cites path, not name alone (D6) ---
# The Grade Trajectories table header must include both "Item Path" and "Producer".
if not VALIDATION:
    traj_hdr = re.search(r"\|\s*Producer\s*\|\s*Item Path\s*\|", text)
    if not traj_hdr:
        errors.append("STRICT: SERIES-MERGED-BY-NAME risk — Grade Trajectories table missing 'Producer | Item Path' columns (series identity requires (repo, generated_by, type, path))")

# --- Trend vocabulary in trajectory column ---
for m in re.finditer(r"\|\s*(Improving|Stable|Regressing|New|Removed)\s*\|?\s*$", text, re.M):
    pass  # presence is fine; check no foreign tokens
foreign_trend = re.findall(r"\|\s*(Declining|Plateau|Volatile|Up|Down)\s*\|", text)
if foreign_trend:
    errors.append(f"STRICT: trajectory column carries non-vocabulary tokens {set(foreign_trend)}; allowed={TREND_VOCAB} plus 'New'|'Removed'")

# --- Portfolio summary line vocabulary ---
portfolio = re.search(r"\*\*Portfolio quality:\s*(\w+)\*\*", text)
if not portfolio:
    errors.append("STRICT: missing Portfolio quality summary line per §6")
elif portfolio.group(1) not in PORTFOLIO_VOCAB:
    errors.append(f"STRICT: Portfolio quality='{portfolio.group(1)}' not in {PORTFOLIO_VOCAB}")

# --- Grade tokens in cells must be in vocabulary (or 'New'/'Removed') ---
for cell in re.findall(r"\|\s*([A-F])\s*\(", text):
    if cell not in GRADE_VOCAB:
        errors.append(f"STRICT: grade token '{cell}' in trajectory cell not in {GRADE_VOCAB}")

# --- Reports/series counts present (line "Items tracked: N | Reports analyzed: M") ---
if not VALIDATION:
    if not re.search(r"Items tracked:\s*\d+\s*\|\s*Reports analyzed:\s*\d+", text):
        warns.append("SOFT: missing 'Items tracked: N | Reports analyzed: M' line under Grade Trajectories")

warns.append(f"INFO: reports_consumed={len(CONSUMED)} dashboard_bytes={len(text)} (Layer B verifies trajectory + alert calibration)")

print(f"=== Layer A — {DASH.name} ===")
for w in warns:  print(f"warn  {w}")
for e in errors: print(f"FAIL  {e}")
print(f"--- {len(errors)} STRICT, {len(warns)} SOFT ---")
sys.exit(1 if errors else 0)
PY
```

What each metric catches: section presence + order → structural validity of the dashboard (validation mode vs full mode); SCOPE-DROP diff against `REPORTS_DIR` glob → D6 SCOPE_DISCIPLINE ("every report in the requested folder appears in the analysis"); series-identity column check → SERIES-MERGED-BY-NAME (Grade Trajectories header must carry Producer + Item Path); trend / portfolio vocabulary → TRAJECTORY-WRONG form-level (the analytics-adapted vocabulary from the template); grade-token vocabulary → DIMENSION-GRADE-ABSENCE form-level. The 10-report cap check enforces the §2 validation-mode rule.

### Layer B — adversarial critic dispatch (blind, recall-framed)

Dispatch a fresh subagent whose ONLY task is to find what the dashboard MISSED, FABRICATED, or MIS-CLASSIFIED versus the source report archive. Adversarial framing is load-bearing — non-adversarial dispatch loses trajectory-calibration and alert-recall.

```
Agent({
  description: "Adversarial review-analytics dashboard critic",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind reviewer. Two markdown payloads are attached: " +
    "ARCHIVE and DASHBOARD. Neither label tells you which is which until " +
    "you read them. ARCHIVE is a concatenation of the YAML frontmatter " +
    "blocks (one per report) from the review-report archive under " +
    "${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/. " +
    "DASHBOARD is the trend-analysis output emitted by /review-analytics " +
    "(Grade Trajectories table, Dimension Analysis, Alerts, Convergence " +
    "Analysis, Portfolio quality summary) — or in validation mode, the " +
    "Validation Summary block.\n\n" +
    "Your only task is to find what the DASHBOARD got wrong. List every " +
    "item that meets one of:\n" +
    "- TRAJECTORY-WRONG — a series whose classification (Improving | " +
    "  Stable | Regressing) in DASHBOARD does not match the grade-vs- " +
    "  previous-grade history in ARCHIVE per the §'Compute trajectories' " +
    "  rule (Improving: latest > earliest OR score +5; Stable: grade " +
    "  unchanged AND score variation < 5; Regressing: latest < previous " +
    "  OR score drop >= 5). Cite the series + the grade history.\n" +
    "- ALERT-MISSED — a regression in ARCHIVE (latest grade lower than " +
    "  previous OR score drop >= 5) that DASHBOARD's Alerts section does " +
    "  not surface. Cite the series + the grade transition.\n" +
    "- ALERT-FABRICATED — a regression in DASHBOARD's Alerts that has no " +
    "  matching grade transition in ARCHIVE. Cite the alert + the absent " +
    "  transition.\n" +
    "- SERIES-MERGED-BY-NAME — two distinct (repo, generated_by, type, " +
    "  path) series in ARCHIVE collapsed in DASHBOARD on 'name' alone. " +
    "  Cite both source series.\n" +
    "- SCOPE-DROP — a report in ARCHIVE whose `generated_by` is in the " +
    "  supported set {review-claude-config, review-skill, review-agent, " +
    "  review-rule, review-hook, review-mcp-server, review-plugin, " +
    "  review-settings, review-claude-md} that DASHBOARD did not include " +
    "  in its time series without a documented filter reason (malformed " +
    "  frontmatter explicitly logged, or validation-mode 10-cap).\n" +
    "- DIMENSION-MISCLASSIFIED — a dimension trend in DASHBOARD's " +
    "  Dimension Analysis (Latest Report) table that does not match the " +
    "  earliest-vs-latest delta in ARCHIVE for the items that are " +
    "  non-null on that dimension. Cite the dimension + items.\n" +
    "- CONVERGENCE-MISCALIBRATED — a Convergence Analysis row marked " +
    "  Converged when ARCHIVE shows max grade variance > 1 per dimension " +
    "  OR a High/Medium finding_id present in only one of the latest two " +
    "  reports OR a non-null-to-null dimension regression.\n\n" +
    "Do not rate quality. Do not praise. Do not propose fixes. List " +
    "items only. Quote the literal series identifier or grade transition " +
    "and name which payload (ARCHIVE or DASHBOARD). Report under 500 " +
    "words.\n\n" +
    "ARCHIVE:\n<paste concatenated YAML frontmatter blocks>\n\n" +
    "DASHBOARD:\n<paste dashboard contents>"
})
```

**Dispatch twice with order swapped** (ARCHIVE↔DASHBOARD label position) — position bias is the dominant pairwise-judge artifact (Shi et al. 2024 arXiv:2406.07791). Take the union of items flagged across both runs.

### Layer C — binary rubric reconciliation

Six binary dimensions, each yes/no, each tied to ≥1 failure class. Any `NO` blocks dashboard presentation until resolved. Dimensions adapt the category D1-D6 to the TREND output shape per `.work/skill-verification/review-template.md` §"Per-skill customization notes → review-analytics".

```
D1 CONVERGENCE_STABILITY  Determinism invariant for the TREND skill: re-running
                          /review-analytics on an UNCHANGED report archive
                          (same set of input report filenames, same parsed
                          frontmatter content) produces the SAME trend verdict
                          per series, the SAME Alerts set, the SAME Convergence
                          Analysis verdicts, and the SAME Portfolio quality
                          classification. Semantics differ from per-item REVIEW
                          skills: convergence here is over (input archive ->
                          output dashboard), not finding_id set stability.
                          When no prior dashboard for the same archive is
                          supplied, D1 is N/A (declared as such in Output;
                          not a NO).
                          (Catches: TRAJECTORY-WRONG non-determinism)

D2 ALERT_CALIBRATION      Every entry in the Alerts section (Regressions,
                          New Items, Removed Items, Systemic Issues) is
                          justified by the underlying ARCHIVE time series
                          per §"Compute trajectories" — latest grade lower
                          than previous OR score drop >= 5; first-appearance
                          and last-seen are determined by report filename
                          timestamp order. No Layer-B ALERT-MISSED or
                          ALERT-FABRICATED item open. (Reframed from category
                          D2 SEVERITY_JUSTIFIED for the TREND output shape.)
                          (Catches: ALERT-MISSED, ALERT-FABRICATED,
                          SEVERITY-MISCALIBRATION analog)

D3 TRAJECTORY_COMPLETENESS Every series appearing in the LATEST analyzed
                          report has a trajectory classification in the
                          Grade Trajectories table (Improving | Stable |
                          Regressing | New | Removed); no series is silently
                          dropped. Dimension Analysis (Latest Report) carries
                          exactly the dimensions that are non-null across
                          the items in the latest report; null dimensions
                          (e.g., Rule reports' prompt_engineering) are
                          excluded from the average per §"Build time series".
                          (Reframed from category D3 DIMENSION_COVERAGE.)
                          (Catches: DIMENSION-MISCLASSIFIED,
                          DIMENSION-GRADE-ABSENCE analog)

D4 EVIDENCE_RESOLVED      Every report cited in the dashboard (by filename,
                          timestamp column, or Alerts reference) was
                          actually read in the producing session — verifiable
                          from the tool-use log (Read calls on report files
                          under REPORTS_DIR). No external URLs are emitted
                          by this skill (the analytics output cites only
                          local report filenames), so the URL-resolution
                          subset of D4 is trivially satisfied; the binding
                          requirement is filename-to-source-file integrity.
                          (Catches: CITATION-ROT analog — dashboard cites
                          a report timestamp that does not exist in
                          REPORTS_DIR)

D5 NO_FABRICATED_TRENDS   No trajectory classification, alert, dimension
                          trend, or Convergence verdict cites a series, a
                          grade transition, or a finding_id that does not
                          appear in ARCHIVE. No SERIES-MERGED-BY-NAME, no
                          ALERT-FABRICATED, no CONVERGENCE-MISCALIBRATED
                          Layer-B item open. (Reframed from category D5
                          NO_FABRICATED_FINDINGS for the TREND output shape:
                          "no alerts cite series that don't exist in the
                          report archive" per the template.)
                          (Catches: ALERT-FABRICATED,
                          CONVERGENCE-MISCALIBRATED, fabrication analog)

D6 SCOPE_DISCIPLINE       Every report present in REPORTS_DIR with a
                          supported `generated_by` and parseable frontmatter
                          appears in CONSUMED (the analyzed set); any report
                          excluded is explicitly noted as malformed or
                          unsupported-producer. In validation mode, exactly
                          the 10 most-recent supported parseable reports are
                          analyzed and the cap is honored. Series identity
                          uses the canonical (repo, generated_by, type,
                          path) tuple — never `name` alone (Grade
                          Trajectories table carries both Producer and
                          Item Path columns). No SCOPE-DROP or
                          SERIES-MERGED-BY-NAME Layer-B item open.
                          (Catches: SCOPE-DROP, SERIES-MERGED-BY-NAME)
```

Map Layer-A SCOPE-DROP failure → D6. Map series-identity-column failure → D6. Map trend / portfolio vocabulary failure → D2 / D3. Map section-order failure → D3. Map Layer-B `TRAJECTORY-WRONG` → D2 + D3. Map `ALERT-MISSED` / `ALERT-FABRICATED` → D2. Map `SERIES-MERGED-BY-NAME` / `SCOPE-DROP` → D6. Map `DIMENSION-MISCLASSIFIED` → D3. Map `CONVERGENCE-MISCALIBRATED` → D5.

### Reconciliation outcomes

- **All Layer-A STRICT pass + zero Layer-B `TRAJECTORY-WRONG`/`ALERT-MISSED`/`ALERT-FABRICATED`/`SERIES-MERGED-BY-NAME`/`SCOPE-DROP`/`CONVERGENCE-MISCALIBRATED`** → present the dashboard to the user.
- **Any Layer-A STRICT fail OR any of those Layer-B classes** → propose corrections inline (name each trajectory / alert / convergence row to revise with the ARCHIVE grade transition + the rule citation from §"Compute trajectories"), re-run Layer A on the patched dashboard. Max two iterations. If still failing at iteration 2, surface to the user and do NOT auto-present the dashboard.
- **Only Layer-A SOFT warnings + Layer-B `DIMENSION-MISCLASSIFIED` items** → record in Output under `### Layer-B Findings (Advisory)` and proceed. These do not block presentation; reviewer triages.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **Calibration drift across reports of differing baseline versions** — the trend logic compares grades across reports that may have been produced under different `engineering-baseline.md` versions (>90-day refresh cadence per CLAUDE.md). A grade improvement could reflect rubric loosening, not artifact quality improvement. Layer A surfaces the baseline_version field's presence but does NOT verify the comparison is rubric-stable; reviewer must spot-check the Portfolio quality verdict when baseline versions differ across the analyzed window.
2. **Report-vs-tool-use-log audit** — D4 verifies that referenced report filenames exist in REPORTS_DIR but does NOT prove that the producing session actually Read each one (the tool-use log lives in the session JSONL at `$HOME/.claude/projects/<project>/<sessionId>.jsonl`). A dashboard could in principle cite a filename it never opened; Layer B's blind critic mitigates by checking ARCHIVE-vs-DASHBOARD consistency but cannot prove session-level resolution.
3. **Rename/move ambiguity** — §3 flags rename candidates rather than silently merging; the pipeline does NOT decide whether a `path A → path B` transition is a genuine rename or two distinct artifacts. Convergence Analysis treats the two as separate series; a human reviewer must confirm continuity before treating them as one trajectory.
4. **Cross-repo aggregation correctness** — in CWD mode, the skill globs `${HOME}/.claude/plugins/data/claude-config/reports/**/*-review-*.md` across all repos. The pipeline verifies SCOPE_DISCIPLINE per-repo-slug but does NOT verify that the cross-repo aggregation column itself (when rendered) is internally consistent — e.g., it does not catch a repo-slug typo that splits one repo's reports across two slugs. Reviewer must spot-check the unique repo-slug count.
5. **Convergence verdict beyond H+M deterministic subset** — the Convergence Analysis view applies §4-style grade-variance and finding_id checks; the deterministic-subset bound from `merge-rules.md` §"Convergence Policy" still applies. Low-severity advisory drift is by-design unbounded; the pipeline accepts variance. If an advisory finding silently migrates between reports without a deterministic-subset change, Convergence Analysis can still verdict Converged.

The Output report MUST list which residual classes apply when the critic returns any `UNCERTAIN` flags or when `--validation` is supplied (D1 N/A — validation mode caps the input archive at 10 reports and does not establish a determinism baseline against an unbounded archive).

## Hard Rules

- **Read-only.** Never modify any file. This is a diagnostic skill only.
- **Handle malformed reports gracefully.** Skip with a warning, never error out.
- **Present all data before conclusions.** Show all four views before the summary.
- **Timestamp sorting is lexicographic.** YYYY-MM-DDTHHMMSS format sorts correctly as strings.
- **Track by path first, partition by producer.** `type + path` identifies the artifact; `generated_by + type + path` identifies the analytics series. `name` is only a label.
- **Grade comparison order.** A > B > C > D > F for trend computation.

## Tier A Tool Justification

**Tier A tool justification (Bash):** Bash is granted exclusively for
`bash bin/repo-slug.sh "$(pwd)"` to compute the canonical `<repo-slug>`
deterministically per `references/repo-identification.md`. The
command-level allowlist `Bash(bash bin/repo-slug.sh:*)` enforces scope.
The script is read-only (stdout slug, no FS writes), so this Tier-A grant
carries no write-amplification risk.
