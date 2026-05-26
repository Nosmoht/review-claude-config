---
name: maintain-evidence-layer
description: >
  Audits the evidence layer: label normalization, source freshness,
  contradictions, and tier compliance. Use every 90 days or when evidence
  sources change. Do NOT use to check skill quality — use /review-claude-config.
argument-hint: "[--scope all|labels|freshness|contradictions|tiers]"
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion
disable-model-invocation: true
---

# Maintain Evidence Layer

You are an evidence layer auditor for the review-claude-config repository. Your job is
to verify that repository-level claims are correctly classified, source files remain
fresh, contradictions are recorded canonically, and claim classifications have the tier
of source backing they require. You audit for **provenance** — source traceability from
claim to primary evidence — as defined by the five formal context quality criteria
(Relevance, Sufficiency, Isolation, Economy, Provenance; arXiv 2603.09619v2).

This is a repo-internal maintenance skill (`.claude/skills/`), not part of the plugin
surface. It modifies only `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/` output files.

## Argument Handling

Parse `$ARGUMENTS` for `--scope` followed by one of: `all`, `labels`, `freshness`,
`contradictions`, `tiers`. If not provided or `all`, run all four checks.
If `--scope` is provided with an unrecognized value, report:
"Unrecognized scope: [value]. Valid options: all, labels, freshness, contradictions, tiers." and stop.

## Phase 1 — Setup

### Step 1: Load canonical contracts

Read `skills/review-claude-config/references/evidence-contract.md`.
Read `docs/evidence-maintenance.md`.

From these files, extract:
- The four canonical class names.
- The non-canonical → canonical mapping table.
Use the values found in those files — do not assume hardcoded values. If the mapping
in evidence-contract.md or evidence-maintenance.md changes, the skill must reflect
the current values without requiring a SKILL.md edit.

If `evidence-contract.md` cannot be read, stop immediately and report:
"evidence-contract.md not found — cannot run evidence layer audit. Verify the file
exists at skills/review-claude-config/references/evidence-contract.md."

### Step 2: Check trigger conditions

Resolve `<repo-slug>` by running `bash bin/repo-slug.sh "$(pwd)"` and capturing stdout. (For documentation reference only, not the operational source-of-truth: `references/repo-identification.md` describes the sanitize algorithm.)

Glob `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/*-evidence-layer.md` to find the most recent run.

For each result, extract the date from the filename (format `YYYY-MM-DDTHHMMSS`).
If a filename does not match this format, skip it with a note: "Skipped unrecognized
filename: [path]" — do not error out.

Select the file with the most recent valid timestamp and compute days since that run.

If the last run was fewer than 90 days ago AND no `--scope` flag was provided:
Inform the user: "Last evidence-layer maintenance run was N days ago — scheduled refresh (90-day cycle) is not yet due."
Confirm via AskUserQuestion (header: "Evidence layer maintenance"):
- Option 1 label: "Proceed anyway" — description: `"Run all checks even though the scheduled refresh is not yet due"`
- Option 2 label: "Cancel" (Recommended) — description: `"Stop — check again when the 90-day cycle is due"`

On "Cancel": stop. On "Proceed anyway": continue with all checks.

If no previous run exists, proceed without prompting.

## Phase 2 — Checks

Run only the steps matching the --scope flag (or all four when scope is `all`). Execute sequentially.

### Step 3: Label normalization check [scope: labels]

Search the following scope for claim-class labels:
- `docs/` (all .md files)
- `research/` (all .md files)
- `skills/review-claude-config/references/` (all .md files)

Grep for each canonical and non-canonical label:

Canonical (count occurrences):
- `Proven result`
- `Engineering guidance`
- `Repo default`
- `Low-evidence area`

Non-canonical (record each occurrence):
- `Local design preference`
- `local policy`
- `novel contribution`
- `limited evidence`

For "heuristic": grep for the word but apply context judgment — flag only occurrences
that appear to be classifying a claim (e.g., "[heuristic]", "heuristic approach" as a
label), not occurrences in prose where it describes a technical method. Record ambiguous
cases as "review needed".

For each non-canonical occurrence: record file path, line number, found label, and
recommended replacement.

### Step 4: Source freshness check [scope: freshness]

Glob `research/**/*.md` to get all research files.

If the glob returns zero files, report: "No research files found under research/ —
verify the path is correct and the directory exists. Freshness check skipped."
Do not continue with this step if zero files are found (an empty result produces a
false-healthy signal with no actionable output).

For each file, grep for date markers: `last_refreshed:`, `Fetched:`, `**Fetched:**`.
Parse the date found (ISO format YYYY-MM-DD or similar).
Use today's date (available from the `# currentDate` session context) to compute the 90-day cutoff dynamically (today minus 90 days). Do not hardcode dates.

Classify:
- Date after the computed cutoff: within window
- Date on or before the computed cutoff: stale (flag with days-stale count)
- No date found: flag as "undated"

For each stale or undated file: note which canonical claims in `docs/` cite that file
(grep for the filename in `docs/scientific-research-dossier.md` and `docs/evidence-backed-refactor-plan.md`).

### Step 5: Contradiction recording check [scope: contradictions]

Read `docs/scientific-research-dossier.md`. If the file cannot be read, skip this check
and note: "Dossier not found — contradiction check skipped."

In the dossier, search for contradiction markers: "contradicts", "conflicts with",
"inconsistent with", "vs.", "but see".

Also grep `research/**/*.md` for the same markers.

For each contradiction marker found in a research file:
- Check whether a corresponding entry appears in `docs/scientific-research-dossier.md`.
- Flag contradictions present in research files but absent from the dossier as
  "unrecorded".

Record each unrecorded contradiction with: file path, line, excerpt.

### Step 6: Source tier compliance check [scope: tiers]

Tier 1 sources: arXiv, ACM, IEEE, official vendor documentation (anthropic.com,
docs.anthropic.com), RFCs, OWASP, CNCF foundation docs.
Tier 2 sources: production case studies with metrics, engineering blogs with benchmarks,
conference talks.
Tier 3: tutorials, blog posts without metrics, Stack Overflow, marketing content.
Local summary: any `research/*.md` file treated as a derived summary, not a primary
source.

#### engineering-baseline.md — use the provenance map

Read `skills/review-claude-config/references/engineering-baseline-provenance.md` as the
authoritative source register for `engineering-baseline.md`. Citations are no longer
inline in the baseline — they live exclusively in the provenance map.

Search `skills/review-claude-config/references/engineering-baseline.md` for `[Proven result]`.

For each "Proven result" claim in engineering-baseline.md:
- Extract the technique name (bold text before the evidence class label).
- Look up the technique in the provenance map.
- Flag if: the technique is missing from the map; the map entry shows no Tier 1 source;
  or the only listed source is a local `research/*.md` summary with no Tier 1 primary
  source traceable from it.

Search the same file for `[Engineering guidance]`.

For each "Engineering guidance" claim in engineering-baseline.md:
- Same lookup in the provenance map.
- Flag if the only traceable source is Tier 3, or if the technique is absent from the map.

#### docs/ — check inline citations

Search `docs/` for `[Proven result]` and `[Engineering guidance]`.

For each claim found in docs/ files:
- Look at the surrounding text (±5 lines) for a citation or source link.
- Flag "Proven result" if the only cited source is a local `research/*.md` summary with
  no Tier 1 primary source traceable from it, or if no source is cited at all.
- Flag "Engineering guidance" if the only traceable source appears to be Tier 3 or is
  uncited.

Record each violation with: file path, technique name or line, claim excerpt, source issue.

## Phase 3 — Report

### Step 7: Assemble maintenance report

Format the report as follows. Present the Overall verdict and Summary first, then the
detail tables, so the reader can fold the detail if they only need the status.

```
## Evidence Layer Maintenance Report
Date: YYYY-MM-DD
Scope: [checks run]

### Overall: [HEALTHY] or [ISSUES FOUND — N items need attention]

### Summary
Non-canonical labels: N
Stale or undated sources: N
Unrecorded contradictions: N
Tier violations: N

---

### Label Normalization

Canonical label coverage: N "Proven result", N "Engineering guidance",
N "Repo default", N "Low-evidence area"

Non-canonical occurrences:
| File | Line | Found | Replace With |
|------|------|-------|-------------|
[rows, or "No non-canonical labels found"]

---

### Stale Sources

Freshness cutoff: [today minus 90 days — computed at runtime]

| Research File | Last Refreshed | Days Stale | Cited In |
|--------------|---------------|------------|---------|
[rows, or "All sources within 90-day freshness window"]

---

### Contradiction Recording

| Location | Excerpt | Recorded in Dossier? |
|----------|---------|---------------------|
[rows, or "No unrecorded contradictions found"]

---

### Source Tier Compliance

| File | Line | Claim Classification | Source Issue |
|------|------|---------------------|-------------|
[rows, or "All claims have appropriate source tier backing"]

---

### Recommended Actions

Immediate (non-canonical labels):
[For each: "- [file:line] Found: '[non-canonical]' → Replace with '[canonical]'. Validate: Grep for old label after edit returns zero results." Or "None"]

Soon (stale sources):
[For each: "- [file] Last refreshed: [date], [N] days stale. Cited in: [citing files]. Validate: Re-run freshness check after update." Or "None"]

Review (unrecorded contradictions, tier violations):
[For each: "- [file:line] [excerpt]. Action: [specific action]. Validate: [verification step]." Or "None"]
```

### Step 8: Present and persist

Present the report in the conversation.

Confirm via AskUserQuestion (header: "Save report"):
- Option 1 label: "Save report" (Recommended) — description: `"Write to ${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-evidence-layer.md"`
- Option 2 label: "Skip" — description: `"Discard the report"`

Use the current timestamp for the filename (format YYYY-MM-DDTHHMMSS with hours, minutes, seconds as HHMMSS). On "Save report": write the file.

If the user confirms, write the file to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-evidence-layer.md`.

Suggest a commit message:
`docs(reviews): add YYYY-MM-DDTHHMMSS evidence-layer maintenance report`

### Step 9: What's Next menu

If any findings exist, present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Fix non-canonical labels" (Recommended) — description: `"Edit files directly or use /apply-rule-review-findings; list specific files and replacements again on request"`
- Option 2 label: "Refresh stale sources" — description: `"Run /refresh-engineering-baseline to update the engineering baseline"`
- Option 3 label: "Check overall repo health" — description: `"Run /check-repo-health for a broader health overview"`
- Option 4 label: "Done" — description: `"End the workflow"`

On "Fix non-canonical labels": remind the user that label edits are direct file edits; offer to list the specific files and replacements again. On "Refresh stale sources": invoke `/refresh-engineering-baseline`. On "Check overall repo health": invoke `/check-repo-health`. On "Done": acknowledge and stop.

If all checks passed with zero findings, skip the menu and confirm the healthy state.

## Error Handling

- If any Read/Grep/Glob call returns an error (not just file-not-found), record
  "Tool error: [tool] on [path] — [error message]" in the report and continue to
  the next step.
- If Write fails when saving the report, present the report text in the conversation
  with note: "Report could not be saved — copy manually."
- If AskUserQuestion is unavailable (non-interactive context), default to proceeding
  (for Step 2 confirmation) and saving the report (for Step 8 confirmation).
- If Glob returns more than 100 files in any step, process in batches of 50 and note
  total count in the report header.

## Hard Rules

- Read-only on all scanned files. Write is only for `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/` report output.
- If `evidence-contract.md` is missing, stop at Step 1.
- If the dossier is missing, skip Step 5 with a note — do not error out.
- If a research file has no date marker, record it as "undated" — do not skip it.
- Always present the full report even when all checks pass.
- Provenance is the primary audit goal: every "Proven result" claim must have a traceable
  primary source; flag any that do not.

## Quality measurement

Without verification, this skill fails at **evidence-label inconsistency (F6)** and **false-stale (F3)** — for example, emitting a normalization that maps "local design preference" → "Repo default" when `references/evidence-contract.md` actually maps it to "Engineering guidance", or flagging a fresh research file as stale because the freshness check reads body markers (`**Fetched:**`, `Last reviewed:`) instead of the canonical `last_refreshed:` frontmatter field (CLAUDE.md §Development Conventions). The three-layer pipeline below catches each class before the report is published.

References: CheckEval (arXiv:2403.18771), G-Eval (arXiv:2303.16634), Position bias in LLM-as-a-Judge (arXiv:2406.07791), IFEval (arXiv:2311.07911), FollowBench (ACL 2024), Beyond Consensus (NUS 2025).

Before running Layer A, capture pre/post/post2 snapshots and the verdict report:

```bash
TMPDIR=$(mktemp -d -t maint-evlayer-XXXX)
PRE="$TMPDIR/pre"
POST="$TMPDIR/post"
POST2="$TMPDIR/post2"
mkdir -p "$PRE" "$POST" "$POST2"
# Copy the report directory before/after each run; copy the contract file too.
# VERDICT points at the just-written report under
# ${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/<ts>-evidence-layer.md
CONTRACT="skills/review-claude-config/references/evidence-contract.md"
```

### Layer A — mechanical invariants (deterministic, fail-fast)

Run on the pre-state, post-state, deterministic re-run, the verdict report, and the contract file. Any `STRICT` row failure → abort and report; `SOFT` rows warn and surface to user.

```python
# Layer A — maintain-evidence-layer mechanical invariants
import sys, re, os
from pathlib import Path

PRE, POST, POST2, VERDICT, CONTRACT = (Path(p) for p in sys.argv[1:6])

TIMESTAMP_FIELDS = {"generated_at", "run_id", "report_timestamp"}
TS_LINE = re.compile(r"^(?:" + "|".join(TIMESTAMP_FIELDS) + r")\s*[:=]\s*\S+", re.M)
VERDICT_STATUSES = {"PASS", "WARN", "FAIL", "BLOCKED", "SKIPPED", "up-to-date",
                    "HEALTHY", "ISSUES FOUND"}

def walk(root):
    for p in sorted(Path(root).rglob("*")):
        if p.is_file() and ".git" not in p.parts:
            yield p.relative_to(root), p.read_bytes()

def canon(b):
    try: return TS_LINE.sub("", b.decode("utf-8")).encode("utf-8")
    except UnicodeDecodeError: return b

def diff_dirs(a, b):
    af = {r: canon(c) for r, c in walk(a)}
    bf = {r: canon(c) for r, c in walk(b)}
    out = []
    for k in set(af) | set(bf):
        if k not in af: out.append((k, "add"))
        elif k not in bf: out.append((k, "del"))
        elif af[k] != bf[k]: out.append((k, "mod"))
    return out

rows = []

# STRICT-1 IDEMPOTENCY — re-run on unchanged input produces zero diff (F1)
idem = diff_dirs(POST, POST2)
rows.append(("STRICT", "idempotent_rerun_diff", 0, len(idem),
             f"+{len(idem)}" if idem else "0",
             f" FAIL items={[str(p)+':'+k for p,k in idem[:5]]}" if idem else ""))

# STRICT-2 EVIDENCE_LABEL_CONTRACT — every label emitted by the verdict
# must appear in the contract's canonical set (F6 — load-bearing here)
if VERDICT.exists() and CONTRACT.exists():
    ctext = CONTRACT.read_text()
    canonical = set(re.findall(
        r"\b(Proven result|Engineering guidance|Repo default|Low-evidence area)\b",
        ctext))
    vtext = VERDICT.read_text()
    # extract labels appearing in the "Replace With" column of the verdict
    proposals = re.findall(
        r"\|\s*([A-Za-z][A-Za-z -]+?)\s*\|\s*$", vtext, re.M)
    illegal = {p.strip() for p in proposals
               if p.strip() and p.strip() not in canonical
               and re.match(r"^[A-Z]", p.strip())
               and p.strip() not in {"Replace With", "Source Issue", "Cited In"}}
    rows.append(("STRICT", "evidence_label_contract_violations",
                 0, len(illegal), f"+{len(illegal)}" if illegal else "0",
                 f" FAIL {sorted(illegal)}" if illegal else ""))

# STRICT-3 VERDICT_STATUS_VOCAB — closed-set status tokens (F10)
if VERDICT.exists():
    bad = re.findall(r"\b(?:status|verdict|Overall)\s*[:=]?\s*\[?([A-Za-z_ -]+?)\]?\s*$",
                     VERDICT.read_text(), re.M)
    bad = [b.strip() for b in bad
           if b.strip() and not any(s in b for s in VERDICT_STATUSES)]
    rows.append(("STRICT", "verdict_status_vocab_violations",
                 0, len(bad), f"+{len(bad)}" if bad else "0",
                 f" FAIL unknown={sorted(set(bad))[:5]}" if bad else ""))

# STRICT-4 TIMESTAMP_SOURCE_FIDELITY — freshness check must read
# `last_refreshed:` frontmatter, not body markers (F3 FALSE_STALE).
# Heuristic: the verdict's "Stale Sources" table must cite the same
# date field that the source file's frontmatter exposes. If the verdict
# quotes a body-marker date (`Fetched:` / `Last reviewed:`) that differs
# from the frontmatter `last_refreshed:`, that is a F3 violation.
if VERDICT.exists():
    body_marker_in_verdict = re.findall(
        r"\b(?:Fetched|Last reviewed):\s*\d{4}-\d{2}-\d{2}",
        VERDICT.read_text())
    rows.append(("STRICT", "body_marker_freshness_citations",
                 0, len(body_marker_in_verdict),
                 f"+{len(body_marker_in_verdict)}" if body_marker_in_verdict else "0",
                 f" FAIL body markers cited as freshness source: "
                 f"{body_marker_in_verdict[:3]}" if body_marker_in_verdict else ""))

# SOFT-1 MUTATION_SET_SIZE — only the report file should be written
mut = [p for p, k in diff_dirs(PRE, POST)
       if "evidence-layer" not in str(p) or k != "add"]
rows.append(("SOFT", "non_report_mutations", 0, len(mut),
             f"+{len(mut)}" if mut else "0",
             f" warn unexpected mutations={[str(p) for p in mut[:5]]}" if mut else ""))

# SOFT-2 VERDICT_ROW_COUNT_DELTA — silent regression vs prior run (F10)
PRE_V = os.environ.get("PRE_VERDICT")
if PRE_V and Path(PRE_V).exists() and VERDICT.exists():
    prev = len(re.findall(r"^\|", Path(PRE_V).read_text(), re.M))
    curr = len(re.findall(r"^\|", VERDICT.read_text(), re.M))
    flag = (f" warn prev={prev} curr={curr}"
            if abs(curr-prev) >= max(5, prev//4) else "")
    rows.append(("SOFT", "verdict_row_count_delta", prev, curr,
                 f"{curr-prev:+d}", flag))

fail = 0
print(f"{'severity':9} {'metric':40} {'before':>8} {'after':>8} {'delta':>8}")
for sev, m, b, a, d, f in rows:
    if "FAIL" in f: fail += 1
    print(f"{sev:9} {m:40} {str(b):>8} {str(a):>8} {d:>8}{f}")
sys.exit(1 if fail else 0)
```

Invoke: `python3 layer_a.py "$PRE" "$POST" "$POST2" "$VERDICT" "$CONTRACT"`.

What each STRICT row catches:

| Row | Failure class |
|---|---|
| `idempotent_rerun_diff` | **F1** — re-run produces drift |
| `evidence_label_contract_violations` | **F6** — non-canonical label proposed (load-bearing) |
| `verdict_status_vocab_violations` | **F10** — status outside closed set |
| `body_marker_freshness_citations` | **F3** — freshness cites body marker instead of `last_refreshed:` |

### Layer B — adversarial critic dispatch (blind, recall-framed, order-swapped)

Dispatch a fresh general-purpose subagent with the **single task** of finding evidence-layer audit defects the report should have caught but did not — or claims the report makes that are not traceable to the post-state. Adversarial framing is the only layer that catches semantic label-mapping errors (e.g. "local design preference" mapped to wrong canonical class).

```
Agent({
  description: "Adversarial maintenance-skill critic",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind reviewer auditing a maintenance skill's effect on the evidence layer.\n" +
    "You are given:\n" +
    "  A: <pre-run snapshot of docs/, research/, and references/ that the skill scanned>\n" +
    "  B: <post-run snapshot of the same files>\n" +
    "  V: <verdict report the skill produced>\n" +
    "  C: <skills/review-claude-config/references/evidence-contract.md + " +
    "      docs/evidence-maintenance.md + CLAUDE.md §Development Conventions>\n" +
    "Neither label tells you which is the original.\n\n" +
    "Find:\n" +
    "1. STALE_MISS — research/*.md entries in A whose `last_refreshed:` frontmatter " +
    "   is past the 90-day cutoff but V did not flag.\n" +
    "2. FALSE_STALE — entries V flagged stale where the canonical `last_refreshed:` " +
    "   frontmatter is in fact fresh (V may have read a body marker by mistake).\n" +
    "3. EVIDENCE_LABEL_DRIFT — proposed normalizations in V's Label Normalization " +
    "   table whose target label does not match the contract's canonical mapping " +
    "   in C (e.g. 'local design preference' → 'Repo default' when C says " +
    "   → 'Engineering guidance').\n" +
    "4. PARTIAL_UPDATE — pairs of files that must stay in sync per C " +
    "   (engineering-baseline.md ↔ engineering-baseline-provenance.md) where V " +
    "   flags one for tier compliance but ignores the other.\n" +
    "5. RECURSIVE_DISCIPLINE_BREACH — V proposes a fix that itself would violate " +
    "   a hard constraint in C (e.g. inline edit to a frontmatter-only field).\n" +
    "6. DROPPED — checks/rows present in the prior verdict that disappeared from V " +
    "   without an underlying fix to A→B.\n" +
    "7. WEAKENED — checks that survived but with looser criteria.\n" +
    "8. ADDED — verdict claims with no traceable evidence in B or C.\n\n" +
    "For each item: quote the literal line, name file:line, classify with one of " +
    "the eight tokens above. Report under 600 words. Do not rate quality. " +
    "Do not praise the skill's design.\n\n" +
    "A:\n<paste pre snapshot>\n\nB:\n<paste post snapshot>\n\n" +
    "V:\n<paste verdict>\n\nC:\n<paste contract+conventions>"
})
```

Then **dispatch a second time with A and B swapped** (and C reordered where applicable) — position bias is the dominant LLM-judge artifact in pairwise settings (Shi et al. 2024 arXiv:2406.07791). Take the union of items flagged across both runs.

### Layer C — rubric reconciliation (binary, CheckEval-style)

Six yes/no dimensions. Any `NO` blocks publication until resolved. CheckEval (arXiv:2403.18771) reports +0.45 inter-evaluator agreement for binary vs. Likert.

```
D1 IDEMPOTENT              Second invocation on the same repo state produces zero
                           new mutations beyond whitelisted timestamp fields.
                           Layer A STRICT-1 passes. Ties to F1.

D2 FRESHNESS_RESPECT       The freshness check reads `last_refreshed:` from YAML
                           frontmatter ONLY — body markers (`**Fetched:**`,
                           `Last reviewed:`) are distinct fields and must not be
                           conflated (CLAUDE.md §Development Conventions). Stale
                           rows are flagged; fresh rows are not falsely flagged.
                           Layer A STRICT-4 passes; Layer B finds zero
                           STALE_MISS / FALSE_STALE. Ties to F2, F3.

D3 SYNC_INTEGRITY          engineering-baseline.md ↔ engineering-baseline-
                           provenance.md treated as a sync pair: tier-compliance
                           flags either both or neither. Layer B finds zero
                           PARTIAL_UPDATE. Ties to F4.

D4 SCHEMA_AND_CONTRACT     Every proposed normalization target is one of the four
                           canonical labels in references/evidence-contract.md
                           (Proven result / Engineering guidance / Repo default /
                           Low-evidence area). Layer A STRICT-2 passes; Layer B
                           finds zero EVIDENCE_LABEL_DRIFT. Ties to F6 (load-
                           bearing here).

D5 VERDICT_HONESTY         Every verdict row traces to evidence in the post-state
                           or to a structured BLOCKED/SKIPPED reason. No DROPPED
                           row hiding an unfixed defect; no ADDED claim without
                           citable evidence. Layer A STRICT-3 passes; Layer B
                           finds zero ADDED / DROPPED-without-fix / WEAKENED.
                           Ties to F7, F10.

D6 DEPGRAPH_COMPLETENESS   N/A for this skill — auto-PASS with note. The skill
                           does not produce a dependency graph; D6 is reserved
                           for validate-primitive-dependencies.
```

Mapping Layer-A failures → rubric:

- STRICT-1 fail → D1 NO
- STRICT-2 fail → D4 NO
- STRICT-3 fail → D5 NO
- STRICT-4 fail → D2 NO

Mapping Layer-B critic tokens → rubric:

- `STALE_MISS` / `FALSE_STALE` → D2 NO
- `PARTIAL_UPDATE` → D3 NO
- `EVIDENCE_LABEL_DRIFT` → D4 NO
- `RECURSIVE_DISCIPLINE_BREACH` → D1 NO
- `DROPPED` / `ADDED` / `WEAKENED` → D5 NO

### Reconciliation outcomes

- **All STRICT pass + zero blocking critic tokens** → publish the report.
- **Any STRICT fail OR any blocking critic token** → propose targeted restoration (revert specific row, fix label mapping, restore dropped check) and re-run Layers A + B on the patched verdict. **Hard cap: 2 iterations** (per `rules/contract-authoring.md §Small-bound carve-out`; this is a bound = 2 case → hard rule, no graceful +1). If still failing after iteration 2, surface to the user; do not auto-publish.
- **Only SOFT warnings** (`non_report_mutations`, `verdict_row_count_delta`) → publish and surface in the report's Recommended Actions block so the operator gets a final-glance opportunity.

### Acknowledged residuals (the pipeline does NOT catch)

1. **Semantic correctness of label normalization context.** Layer A checks the proposed label is in the canonical set; Layer B compares the proposal against the contract's documented mapping. Neither catches the case where the contract itself is ambiguous about which canonical class fits a piece of source prose — NLI on the surrounding paragraph would be needed and is not implemented here.
2. **Tier-classification of novel research files.** The tier compliance check (Step 6) uses prefix heuristics (arXiv, ACM, IEEE, etc.) to classify sources. A newly added Tier 1 source from a domain outside the cited prefix list (e.g. a NIST publication, an ISO/IEC standard PDF) may be silently misclassified as untiered. The skill flags absent-from-map but cannot disambiguate "absent because untiered" from "absent because not yet registered".
3. **External-dependency drift in research/*.md.** Research files may cite URLs that 404 or change content between runs. Layer A's idempotency check (D1) covers the local filesystem only; whether the cited primary sources themselves remain stable is out of scope.
4. **Cross-session staleness of the contract.** If `references/evidence-contract.md` itself is edited between sessions, Layer A's STRICT-2 comparison still uses the current contract — a label that was canonical last session but renamed this session will pass STRICT-2 without flagging the rename's downstream effect on prior reports.
5. **Quiet success-mode masking partial failure.** A scope-limited invocation (`--scope freshness`) produces a single-dimension verdict that hides label/contradiction/tier defects the operator may assume were also checked. Layer C's D5 (verdict honesty) requires the report header to enumerate which scopes ran; absence of that line is a verdict-honesty violation.

## Tier A Tool Justification

**Tier A tool justification (Bash):** Bash is granted exclusively for
`bash bin/repo-slug.sh "$(pwd)"` to compute the canonical `<repo-slug>`
deterministically per `references/repo-identification.md`. The
command-level allowlist `Bash(bash bin/repo-slug.sh:*)` enforces scope.
The script is read-only (stdout slug, no FS writes), so this Tier-A grant
carries no write-amplification risk.
