---
name: refresh-engineering-baseline
description: >
  Updates the engineering baseline with current prompt, context, and tool-
  design best practices from web research. Use when the baseline's
  last_refreshed is older than 3 months. Do NOT use for other reference
  files — each has its own update path.
disable-model-invocation: true
allowed-tools: WebSearch, WebFetch, Read, Write, AskUserQuestion
tool-justification: >
  Write+WebFetch (Tier A): WebFetch retrieves research sources; Write updates
  only two hardcoded reference files (engineering-baseline.md and
  engineering-baseline-provenance.md) after explicit AskUserQuestion confirmation.
  No raw fetch output is forwarded to Write — findings are classified and
  merged before any file is modified.
---

# Refresh Engineering Baseline

You are a research librarian maintaining a curated technical reference. Your job is to verify sources rigorously, preserve what works, and add only well-evidenced new techniques.

Update `references/engineering-baseline.md` with current research findings.

## Workflow

### 1. Locate the baseline file

Read `skills/review-claude-config/references/engineering-baseline.md`. If the file is not found, report the error and stop.
Read `skills/review-claude-config/references/engineering-baseline-provenance.md` to load the current source provenance map. If not found, report the error and stop — the provenance map must stay in sync with the baseline.
Read `skills/review-claude-config/references/evidence-contract.md` to load the canonical evidence classes and source precedence rules.
Read `skills/review-claude-config/references/source-quality-criteria.md` to load the source filtering criteria used in Step 3.

Read the current file content and extract the `last_refreshed` date from frontmatter. If `last_refreshed` is missing or unparseable, treat the baseline as stale and proceed directly to Step 3.

Attempt a trivial WebFetch (e.g., fetch "https://docs.anthropic.com"). If it fails or is unavailable, set `webfetch_available = false` and continue with WebSearch-only mode.

### 2. Freshness gate

If `last_refreshed` is less than 90 days ago:
- Tell the user: "Baseline was last refreshed on [date] ([N] days ago). Refresh is recommended after 90 days."
- Confirm via AskUserQuestion (header: "Force refresh"):
  - Option 1 label: "Force refresh anyway" — description: `"Proceed with the baseline refresh despite it being less than 90 days old"`
  - Option 2 label: "Cancel" (Recommended) — description: `"Stop — refresh again when 90 days have passed"`
- On "Cancel": stop. On "Force refresh anyway": continue.

### 3. Research current best practices

Run these WebSearch queries sequentially (early termination requires evaluating each before proceeding). Replace `[current year]` with the actual year. After each query, check if new actionable techniques were found for the three baseline sections. If two consecutive queries yield no new techniques beyond what earlier queries found, skip remaining queries and note skipped queries in the change report.

- "agentic workflow patterns multi-agent orchestration [current year]"
- "prompt engineering techniques evidence research [current year]"
- "context engineering LLM agents best practices [current year]"
- "AI agent tool design best practices [current year]"
- "AI agent safety guardrails best practices [current year]"
- "LLM instruction following clarity research [current year]"

For each search, extract only actionable techniques with evidence.

Deduplicate across queries: if the same technique appears in multiple search results, consolidate into a single entry citing the strongest source. Do not list the same technique multiple times in the preview.

#### Source quality criteria

Apply shared criteria from `skills/review-claude-config/references/source-quality-criteria.md` (discard rules, tier classification, cross-validation). For baseline techniques, add these task-specific filters:

1. **Actionable** — Must describe a specific, implementable technique (not a general principle like "be clear")
2. **Evidence fit** — Prefer official vendor docs, peer-reviewed research, and documented production systems when choosing which supported technique to keep

#### WebSearch failure handling

- If WebSearch is completely unavailable (tool error), stop and tell the user: "WebSearch is required for baseline refresh but is unavailable. Baseline was not modified."
- If fewer than 4 of 6 queries return useful results, warn the user: "Only [N]/6 searches returned actionable results. Proceeding with limited data — review changes carefully."
- If no queries return useful results, stop and report: "No actionable search results. Baseline was not modified."

### 3.5. Full-content retrieval (when WebFetch is available)

If `webfetch_available = true`, after completing all WebSearch queries, fetch URLs in two tiers. Tier 1 guarantees every topic gets at least one full-text source; Tier 2 adds depth on the strongest results.

**Tier 1 — Coverage (1 fetch per executed query):**
For each query that was actually executed (not skipped by early termination), identify the single most promising URL from its search results and fetch it with WebFetch. This yields 4-6 fetches depending on how many queries ran.

**Tier 2 — Depth (2-3 additional fetches):**
From all remaining search results across all queries, identify the 2-3 most promising URLs not already fetched in Tier 1 (prefer: official Anthropic docs, peer-reviewed research, documented production systems). No duplicates across tiers or within Tier 2.

Fetch each URL with WebFetch using a targeted prompt: "Extract actionable prompt engineering, context engineering, tool design, safety, and instruction clarity techniques with evidence. Max 500 words."

Use full article content — not just search snippets — when extracting techniques in Step 4. Full content provides benchmarks, nuanced conditions, and code examples that snippets miss.

**Total: 6-9 fetches.** If `webfetch_available = false`, skip this step entirely and proceed with search snippets as before.

### 4. Merge findings

For each baseline section (Prompt Engineering, Context Engineering, Tool Design):
- Route safety and guardrail techniques (least-privilege, confirmation gates, stop conditions) to Context Engineering
- Route instruction clarity techniques (constraint limits, deterministic conditionals) to Prompt Engineering
- Route agentic workflow techniques to the best-fit section (decomposition patterns to PE, orchestration patterns to CE)

Note: Completeness, Goal Alignment, Safety, and Metadata are rubric dimensions, not separate baseline sections. Safety and instruction-clarity findings are routed into the three baseline sections above rather than creating new domains.

- Add new techniques not already covered
- Update existing techniques if newer evidence contradicts or supplements them
- Spot-check 2-3 existing techniques per section against current sources to verify they remain accurate and well-evidenced
- Remove techniques that have been superseded or debunked
- Classify each claim cluster using the canonical evidence classes from `evidence-contract.md`
- If a technique mixes multiple evidence classes, split it into smaller claim clusters rather than hiding the difference under one label
- Preserve the section structure, but do not preserve the previous prose format if it prevents clear evidence classification

Example merge decision:
- Existing: "Few-Shot Examples — Provide 2-3 diverse examples. Source: Brown et al. 2020"
- New finding: "Anthropic 2026 reports few-shot is less effective for Claude 4 on structured tasks but still valuable for ambiguous formats. Source: docs.anthropic.com/..."
- Action: UPDATE — refine the description to note the nuance, cite both sources. Do NOT remove, since it remains valid for ambiguous formats.

### 5. Preview and confirm

Present the proposed changes to the user using the report format from Step 7. Include:
- Techniques to ADD (with source)
- Techniques to UPDATE (show before/after)
- Techniques to REMOVE (with justification)
- Evidence-class changes for any rewritten techniques
- Projected token count

Confirm via AskUserQuestion (header: "Apply baseline changes"):
- Option 1 label: "Apply these changes" (Recommended) — description: `"Update engineering-baseline.md with the proposed additions, updates, and removals"`
- Option 2 label: "Cancel" — description: `"Stop and preserve the current file"`

On "Cancel": stop and preserve the current file.

### 6. Write the updated files

Only after user confirmation. Update `engineering-baseline.md` with:
- Set `last_refreshed` in frontmatter to today's date
- Before writing, estimate the token count of the updated file. If it would exceed 2K tokens, remove the lowest-evidence techniques until it fits, and note the removals in the change report. If removing techniques would compromise coverage of a full section, warn the user before proceeding.
- Preserve the Prompt / Context / Tool section headings
- Preserve explicit evidence-class labels on each claim cluster
- Do NOT add a Sources section — all source provenance belongs in `engineering-baseline-provenance.md`

Also update `engineering-baseline-provenance.md`:
- For each added technique: add a row with technique name, evidence class, sources, and tier
- For each updated technique: update the corresponding provenance row with new or changed sources
- For each removed technique: remove its provenance row
- Set `last_refreshed` in frontmatter to today's date

### 7. Report changes

Present the change report in this format:

```
## Baseline Refresh Report — YYYY-MM-DD

| Action | Count |
|--------|-------|
| Added | N |
| Updated | N |
| Removed | N |
| Unchanged | N |
| Token count | NNNN / 2000 |

### Added
- **[Technique Name]** — [One sentence]. Source: [URL or citation]

### Updated
- **[Technique Name]** — Changed: [what changed]. Source: [URL or citation]

### Removed
- **[Technique Name]** — Reason: [why removed]. Evidence: [source]
```

## Quality measurement (mandatory before Output)

Without verification, this skill fails at **RECURSIVE_DISCIPLINE_BREACH** — the skill is the **named gateway** for baseline mutation (CLAUDE.md §Hard Constraints #6 forbids mid-session edits to `engineering-baseline.md`; this skill IS the legitimate path, but each invocation must terminate at a session boundary). A successful run invoked **from inside an already-running review session** would itself violate the rule the skill is built to honor. A second dominant failure class is **SYNC_INTEGRITY breach** between `engineering-baseline.md` and `engineering-baseline-provenance.md` — the two files MUST be mutated together (every added/updated/removed technique requires a paired provenance row) or neither at all; an Edit-loop early-exit on the second file leaves the repo in inconsistent state. A third is **STATE_FORMAT_DRIFT** in `last_refreshed:`: a value written as `2026/05/26` instead of `2026-05-26` breaks downstream freshness parsers (`check-repo-health freshness`, `session_check.py`). A three-layer pipeline (mechanical invariants / adversarial critic / binary rubric) is required because no single layer catches all three classes.

References: CheckEval (arXiv:2403.18771), G-Eval (arXiv:2303.16634), Position bias in LLM-as-a-Judge (arXiv:2406.07791), IFEval (arXiv:2311.07911), FollowBench (ACL 2024), Beyond Consensus (NUS 2025). Per-skill design: `.work/skill-verification/maintain-template.md §Per-skill customization notes`.

Per the MAINTAIN template's per-skill note: this skill produces (a) mutations to `skills/review-claude-config/references/engineering-baseline.md` + (b) paired mutations to `skills/review-claude-config/references/engineering-baseline-provenance.md`, both written only after explicit `AskUserQuestion` confirmation. Layer A idempotency must be checked with `last_refreshed` rolled back to >90 days (otherwise the freshness gate early-returns in Step 2 and the test is trivial). External-dependency drift (residual #5) applies — D1 is relaxed to "no mutations beyond those traceable to a recorded fetch event in the change report". Layer B's dominant risk is RECURSIVE_DISCIPLINE_BREACH (the skill MUST be invoked between sessions, not inside an active review session). D1 IDEMPOTENT and D3 SYNC_INTEGRITY (baseline ↔ provenance) are load-bearing; D2 carries the freshness-gate check; D6 N/A.

Snapshot the pre-run and post-run state for both files plus a deterministic re-run so subsequent steps can compare:

```bash
TMPDIR=$(mktemp -d -t reb-XXXX)
PRE_BASELINE="$TMPDIR/engineering-baseline.pre.md"
POST_BASELINE="$TMPDIR/engineering-baseline.post.md"
POST2_BASELINE="$TMPDIR/engineering-baseline.post2.md"
PRE_PROVENANCE="$TMPDIR/engineering-baseline-provenance.pre.md"
POST_PROVENANCE="$TMPDIR/engineering-baseline-provenance.post.md"
REPORT="$TMPDIR/change-report.md"
# Copy both files to PRE_* before Step 6.
# After Step 6, copy mutated files to POST_*.
# Re-invoke the skill on POST state (without rolling last_refreshed back)
# and capture engineering-baseline.md to POST2_BASELINE — idempotency probe.
# Copy the change report rendered in Step 7 to REPORT.
```

### Layer A — mechanical invariants (deterministic, fail-fast)

Run against PRE / POST / POST2 snapshots and the change report. `STRICT` rows abort with exit 1; `SOFT` rows warn and continue.

```bash
python3 - "$PRE_BASELINE" "$POST_BASELINE" "$POST2_BASELINE" "$PRE_PROVENANCE" "$POST_PROVENANCE" "$REPORT" <<'PY'
import sys, re
from pathlib import Path

PRE_B, POST_B, POST2_B, PRE_P, POST_P, REPORT = (Path(p) for p in sys.argv[1:7])

CANONICAL_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LAST_REFRESHED_LINE = re.compile(r"^last_refreshed\s*:\s*(\S+)\s*$", re.M)
SECTION_HEADINGS = {"Prompt Engineering", "Context Engineering", "Tool Design"}
# Technique entries are bold-led list items: `- **Name** — ...`
TECH_RE = re.compile(r"^\s*-\s+\*\*([^*]+?)\*\*", re.M)

def read(p): return p.read_text(errors="ignore") if p.exists() else ""

pre_b, post_b, post2_b = read(PRE_B), read(POST_B), read(POST2_B)
pre_p, post_p, report = read(PRE_P), read(POST_P), read(REPORT)
rows = []  # (sev, metric, before, after, delta, flag)

# STRICT-1 IDEMPOTENCY — second run on unchanged input MUST be no-op
# (modulo whitelisted timestamp fields).
def canonicalize(text):
    return re.sub(r"^(?:generated_at|run_id|report_timestamp)\s*[:=]\s*\S+\s*$",
                  "", text, flags=re.M)
idem_delta = 1 if canonicalize(post_b) != canonicalize(post2_b) else 0
rows.append(("STRICT", "idempotent_rerun_diff",
             0, idem_delta, f"+{idem_delta}" if idem_delta else "0",
             " FAIL second_run_mutated_baseline" if idem_delta else ""))

# STRICT-2 DATE_FORMAT — every last_refreshed: value in POST_B and POST_P
# matches YYYY-MM-DD canonical format.
bad_dates = []
for label, txt in (("baseline", post_b), ("provenance", post_p)):
    for v in LAST_REFRESHED_LINE.findall(txt):
        if not CANONICAL_DATE.match(v): bad_dates.append((label, v))
rows.append(("STRICT", "last_refreshed_date_format_violations",
             0, len(bad_dates), f"+{len(bad_dates)}" if bad_dates else "0",
             f" FAIL non_canonical={bad_dates[:5]}" if bad_dates else ""))

# STRICT-3 SECTION_PRESERVATION — the three section headings MUST survive.
post_headings = set(re.findall(r"^##\s+(Prompt Engineering|Context Engineering|Tool Design)\s*$",
                               post_b, re.M))
missing_sections = SECTION_HEADINGS - post_headings
rows.append(("STRICT", "baseline_section_headings_missing",
             3, len(post_headings),
             f"-{len(missing_sections)}" if missing_sections else "0",
             f" FAIL missing={sorted(missing_sections)}" if missing_sections else ""))

# STRICT-4 SYNC_INTEGRITY — every technique in POST_BASELINE MUST have a
# matching row in POST_PROVENANCE (and vice versa, modulo techniques the
# report explicitly removed).
post_b_techs = set(TECH_RE.findall(post_b))
post_p_techs = set(TECH_RE.findall(post_p))
# Allow trivial whitespace/case normalization for matching
def norm(s): return re.sub(r"\s+", " ", s).strip().lower()
norm_b = {norm(t): t for t in post_b_techs}
norm_p = {norm(t): t for t in post_p_techs}
unpaired_b = [norm_b[k] for k in (set(norm_b) - set(norm_p))]
unpaired_p = [norm_p[k] for k in (set(norm_p) - set(norm_b))]
sync_breaks = len(unpaired_b) + len(unpaired_p)
rows.append(("STRICT", "baseline_provenance_unpaired_techniques",
             0, sync_breaks, f"+{sync_breaks}" if sync_breaks else "0",
             f" FAIL baseline_only={unpaired_b[:3]} provenance_only={unpaired_p[:3]}"
             if sync_breaks else ""))

# STRICT-5 TOKEN_BUDGET — baseline output MUST NOT exceed 2K tokens.
# Coarse estimate: 1 token ≈ 4 chars for English prose.
approx_tokens = len(post_b) // 4
rows.append(("STRICT", "baseline_token_budget_2k",
             0, approx_tokens, f"{approx_tokens}",
             f" FAIL approx={approx_tokens}>2000" if approx_tokens > 2000 else ""))

# SOFT-1 PROVENANCE_DRIFT — every added/updated technique in the report
# should pair with a citation (URL or arXiv/RFC/DOI). If techniques added
# in the report outnumber distinct cited sources, flag for operator glance.
added_in_report = len(re.findall(r"^###\s+Added\s*$", report, re.M)) and \
                  len(re.findall(r"^\s*-\s+\*\*", report.split("### Added", 1)[-1].split("###", 1)[0], re.M)) \
                  if "### Added" in report else 0
url_cites = set(re.findall(r"https?://\S+", report))
id_cites = set(re.findall(r"\b(?:arXiv:[0-9.]+|RFC\s*\d+|DOI:[^\s)]+)", report))
src_count = len(url_cites) + len(id_cites)
flag = ""
if added_in_report and added_in_report > src_count + 2:
    flag = f" warn added={added_in_report} cited_sources={src_count}"
rows.append(("SOFT", "added_techniques_vs_cited_sources",
             0, added_in_report, f"+{added_in_report}", flag))

# SOFT-2 LAST_REFRESHED_FORWARD_MOTION — POST last_refreshed >= PRE.
def first_last_refreshed(text):
    m = LAST_REFRESHED_LINE.search(text)
    return m.group(1) if m else ""
pre_d = first_last_refreshed(pre_b)
post_d = first_last_refreshed(post_b)
backward = bool(pre_d and post_d and CANONICAL_DATE.match(pre_d)
                and CANONICAL_DATE.match(post_d) and post_d < pre_d)
rows.append(("SOFT", "last_refreshed_backward_motion",
             0, 1 if backward else 0, "+1" if backward else "0",
             f" warn pre={pre_d} post={post_d}" if backward else ""))

fail = 0
print(f"{'severity':9} {'metric':46} {'before':>8} {'after':>8} {'delta':>10}")
for sev, metric, before, after, delta, flag in rows:
    if "FAIL" in flag: fail += 1
    print(f"{sev:9} {metric:46} {str(before):>8} {str(after):>8} {delta:>10}{flag}")
sys.exit(1 if fail else 0)
PY
```

If exit non-zero → STOP, do not finalize the refresh. Report failures and propose targeted restorations (re-write the bad `last_refreshed:` in canonical format, add the missing provenance row for the unpaired technique, restore the dropped section heading, trim lowest-evidence techniques to fit the 2K budget), then re-run Layer A on the patched state.

### Layer B — adversarial critic dispatch (blind, recall-framed)

Dispatch a fresh subagent with the **single task** of finding what was lost, falsely mutated, or breached the discipline. Seed the critic with `CLAUDE.md §Hard Constraints` (especially #6 mid-session freeze), `references/evidence-contract.md`, and the skill's own "must stay in sync" claim (Step 1: provenance map stays in sync with baseline) so judgments are evaluated against documented conventions, not the critic's prior.

```
Agent({
  description: "Adversarial refresh-engineering-baseline critic",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind reviewer auditing a refresh-engineering-baseline skill run. " +
    "You are given:\n" +
    "  A: <pre-run snapshot of engineering-baseline.md>\n" +
    "  B: <post-run snapshot of engineering-baseline.md>\n" +
    "  AP: <pre-run snapshot of engineering-baseline-provenance.md>\n" +
    "  BP: <post-run snapshot of engineering-baseline-provenance.md>\n" +
    "  V: <the change report the skill rendered in Step 7>\n" +
    "  C: <CLAUDE.md Hard Constraints + Development Conventions excerpt>\n" +
    "  E: <references/evidence-contract.md>\n" +
    "Neither label (A/B, AP/BP) tells you which is the original.\n\n" +
    "Find:\n" +
    "1. RECURSIVE_DISCIPLINE_BREACH — any claim or evidence in V indicating " +
    "the refresh was invoked mid-session (not at a session boundary), " +
    "or any mutation in B to scoring-rubric.md / other frozen files outside " +
    "the two baseline files (forbidden by C §Hard Constraints #6).\n" +
    "2. STALE_MISS — claims in V that last_refreshed is still <90 days when " +
    "A's last_refreshed is in fact >90 days from today.\n" +
    "3. FALSE_STALE — refresh proceeded even though A's last_refreshed was " +
    "<90 days from today and V does NOT cite a 'force refresh' confirmation.\n" +
    "4. PARTIAL_UPDATE — techniques present in B but missing from BP " +
    "(or vice versa); section headings preserved in only one file when " +
    "the report claimed both updated.\n" +
    "5. STATE_FORMAT_DRIFT — last_refreshed: values in B or BP not matching " +
    "YYYY-MM-DD; technique entries that conflate multiple evidence classes " +
    "under one label (forbidden by E and by the skill's Step 4 rule).\n" +
    "6. EVIDENCE_LABEL_DRIFT — labels in V (or in B's claim clusters) not " +
    "appearing in E's canonical set " +
    "(Proven result / Engineering guidance / Repo default / Low-evidence area).\n" +
    "7. DROPPED — techniques in A removed from B without an underlying " +
    "supersession-citation in V's 'Removed' section.\n" +
    "8. ADDED — techniques in B's claim clusters with no traceable source " +
    "in V (no URL, no arXiv/RFC/DOI ID, no documented production system).\n" +
    "9. WEAKENED — existing techniques whose evidence-class label was " +
    "downgraded (e.g. 'Proven result' -> 'Repo default') without V citing " +
    "a contradicting source.\n\n" +
    "For each item: quote the literal sentence, name file:line, classify with " +
    "one of the nine tokens above. Report under 600 words. Do not rate " +
    "quality. Do not praise the skill's design.\n\n" +
    "A:\n<paste $PRE_BASELINE contents>\n\n" +
    "B:\n<paste $POST_BASELINE contents>\n\n" +
    "AP:\n<paste $PRE_PROVENANCE contents>\n\n" +
    "BP:\n<paste $POST_PROVENANCE contents>\n\n" +
    "V:\n<paste $REPORT contents>\n\n" +
    "C:\n<paste CLAUDE.md Hard Constraints + Development Conventions excerpt>\n\n" +
    "E:\n<paste references/evidence-contract.md>"
})
```

Then **dispatch a second time with A/B and AP/BP swapped** (and C/E reordered) — position bias is the dominant LLM-judge artifact in pairwise settings (Shi et al. 2024, arXiv:2406.07791). Take the union of items flagged across both runs.

### Layer C — rubric reconciliation (binary CheckEval-style)

Six yes/no dimensions specialized to this skill. Any `NO` blocks finalization until resolved. CheckEval (arXiv:2403.18771) reports +0.45 inter-evaluator agreement for binary vs. Likert.

```
D1 IDEMPOTENT              Second run of the skill within 90 days of the
                           bumped last_refreshed produces ZERO mutations to
                           engineering-baseline.md AND engineering-baseline-
                           provenance.md (modulo whitelisted timestamp
                           fields). External-dependency drift (residual #5)
                           is acknowledged but does not excuse same-day
                           mutation. Recursive-discipline overlay: the skill
                           MUST early-return when invoked from inside an
                           already-running review session — session-boundary
                           detection is Builder-state-aware (Acknowledged
                           Residual #1) and Layer A cannot fully enforce it.
                           Layer A STRICT-1 (idempotent_rerun_diff) passes.
                           Ties to F1 IDEMPOTENCY_BREAK, F9 RECURSIVE_DISCIPLINE_BREACH.
                           HIGHEST WEIGHT.

D2 FRESHNESS_RESPECT       last_refreshed <90 days in PRE leads to either
                           early-return ("Cancel" path) or explicit Force-
                           refresh confirmation cited in the change report.
                           last_refreshed >=90 days proceeds to research +
                           preview. The 90-day cadence from CLAUDE.md
                           §Development Conventions is honored verbatim.
                           Layer B finds zero STALE_MISS / FALSE_STALE.
                           Ties to F2 STALE_MISS, F3 FALSE_STALE.

D3 SYNC_INTEGRITY          Every technique present in POST baseline has a
                           matching row in POST provenance, and every row
                           in POST provenance has a matching technique in
                           POST baseline. Edit-loop early-exit on either
                           file is a hard FAIL.
                           Layer A STRICT-4 (unpaired_techniques) passes;
                           Layer B finds zero PARTIAL_UPDATE.
                           Ties to F4 PARTIAL_UPDATE. LOAD-BEARING.

D4 SCHEMA_AND_CONTRACT     Every last_refreshed: value in POST baseline and
                           POST provenance matches the canonical YYYY-MM-DD
                           format. Every evidence-class label cited in the
                           change report and on each claim cluster appears
                           in references/evidence-contract.md's canonical
                           set (Proven result / Engineering guidance / Repo
                           default / Low-evidence area). The three section
                           headings (Prompt Engineering / Context
                           Engineering / Tool Design) survive the rewrite.
                           Token-budget invariant (2K) holds.
                           Layer A STRICT-2 + STRICT-3 + STRICT-5 pass;
                           Layer B finds zero STATE_FORMAT_DRIFT /
                           EVIDENCE_LABEL_DRIFT.
                           Ties to F5 STATE_FORMAT_DRIFT,
                           F6 EVIDENCE_LABEL_INCONSISTENCY.

D5 VERDICT_HONESTY         Every ADDED technique in the change report is
                           paired with a cited source (URL or
                           arXiv/RFC/DOI). Every REMOVED technique cites
                           the superseding source or debunking evidence.
                           Every UPDATED technique shows before/after.
                           No baseline technique was silently dropped
                           between PRE and POST without a corresponding
                           "Removed" row in the report. No new claim
                           appears in POST that lacks a Step-3.5 fetch
                           event or Step-3 search result in the report.
                           Layer B finds zero ADDED / DROPPED / WEAKENED.
                           Ties to F7 EVAL_FALSE_PASS, F10 NULL_VERDICT_REGRESSION.

D6 DEPGRAPH_COMPLETENESS   N/A — this skill is not a dependency-graph
                           emitter. Auto-PASS with note.
```

Mapping Layer-A failures → rubric:

- STRICT-1 (idempotent_rerun_diff) fail → D1 NO
- STRICT-2 (date format) fail → D4 NO
- STRICT-3 (section headings) fail → D4 NO
- STRICT-4 (unpaired techniques) fail → D3 NO
- STRICT-5 (token budget) fail → D4 NO

Mapping Layer-B critic tokens → rubric:

- `RECURSIVE_DISCIPLINE_BREACH` → D1 NO (re-classifies as idempotency-of-the-discipline)
- `STALE_MISS` / `FALSE_STALE` → D2 NO
- `PARTIAL_UPDATE` → D3 NO
- `STATE_FORMAT_DRIFT` → D4 NO
- `EVIDENCE_LABEL_DRIFT` → D4 NO
- `ADDED` / `DROPPED` / `WEAKENED` → D5 NO

### Reconciliation outcomes

- **All STRICT pass + Layer B yields zero RECURSIVE_DISCIPLINE_BREACH / STALE_MISS / FALSE_STALE / PARTIAL_UPDATE / STATE_FORMAT_DRIFT / EVIDENCE_LABEL_DRIFT / ADDED / DROPPED / WEAKENED** → finalize the refresh. Write both files, render the change report, surface follow-up actions.
- **Any STRICT fail OR any blocking critic token** → propose targeted restorations (re-write the bad `last_refreshed:` in canonical format, add the missing provenance row for the unpaired technique, restore the dropped section heading, cite the orphan source, revert the weakened evidence-class label) and re-run Layers A + B on the patched state. **Hard cap: 2 iterations** (per `rules/contract-authoring.md §Small-bound carve-out`; bound = 2 → hard rule, no graceful +1). If still failing after iteration 2, surface to the user; do not auto-publish the refresh.
- **Only SOFT warnings** (`added_techniques_vs_cited_sources` skew, `last_refreshed_backward_motion`) → finalize but surface the warnings in the change-report Summary so the operator gets a final-glance opportunity.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **Cross-session state corruption / session-boundary breach.** This skill is the **named gateway** for baseline mutation (CLAUDE.md §Hard Constraints #6), but the rule says "no mid-session edits" — the legitimate path is invocation between sessions. A run that happens to mutate the baseline within an already-running review session passes STRICT-1 (idempotent within itself) and STRICT-4 (sync integrity holds) yet still violates the rule. Only Builder-agent session-state awareness surfaces this; the diff is silent on session boundaries. This residual is the recursive-discipline case explicitly named in the brief (Wave 8 brief + maintain-template per-skill note); full enforcement is upstream of Layer A.
2. **External-dependency drift.** This skill consults `WebSearch` / `WebFetch` to discover current best-practice techniques; the same repo state on different days can legitimately yield different mutations because the external corpus moved. D1 is relaxed to "no mutations beyond those traceable to a recorded fetch event in the change report"; whether the fetched sources themselves are stable is out of scope.
3. **Semantic correctness of evidence-class assignment.** Layer A and B both treat the four canonical labels (Proven result / Engineering guidance / Repo default / Low-evidence area) as a self-contained predicate. Neither catches the case where the skill labeled a technique "Proven result" when the cited source is actually a single benchmark with N=1. NLI on the source's body is required and not implemented here.
4. **Claim-cluster boundary correctness.** Step 4 instructs "if a technique mixes multiple evidence classes, split it into smaller claim clusters" — the critic can detect a label conflict but cannot infer optimal cluster boundaries from prose. Operator review at the preview step (Step 5) is the load-bearing check.
5. **Provenance-row body drift.** The provenance map's per-row source URLs may rot between refreshes (link-rot, paper retraction). Layer A and B read the local file, not the live source. Stale provenance rows are invisible to the pipeline and surface only via `check-repo-health integrity` mode.

The change report MUST list which residual classes apply to passages the critic flagged as `UNCERTAIN`, so the operator has one last human-glance opportunity before the baseline + provenance mutations land.

## Hard Rules

- Preserve the three section headings, but allow prose structure changes needed for evidence classification
- Do not exceed 2K tokens in the output file
- Every technique must have an entry in engineering-baseline-provenance.md
- Do not remove techniques unless evidence shows they are wrong or superseded
- If WebSearch fails or user declines changes, leave the baseline unchanged
