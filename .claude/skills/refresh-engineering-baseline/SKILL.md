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

Per `docs/skill-verification-architecture.md` (2026-05-26 retrofit), MAINTAIN-class verification is deterministic: schema invariants (canonical `YYYY-MM-DD` `last_refreshed:`, three section headings preserved, 2K token budget), idempotency `f(f(x)) == f(x)` (re-run on unchanged input produces zero diff), sync-pair integrity (baseline ↔ provenance: every technique requires a paired provenance row), and freshness predicates (90-day cadence) fully cover this skill's mechanical failure surface. There is no judgment-shaped output to evaluate, so the historical Layer B (adversarial critic) and Layer C (binary rubric) were dropped — they added token cost and false-positive surface without raising assurance. Layer A below is the complete verification.

This skill produces paired mutations to `engineering-baseline.md` + `engineering-baseline-provenance.md`, both written only after explicit `AskUserQuestion` confirmation. Layer A idempotency must be checked with `last_refreshed` rolled back to >90 days (otherwise the freshness gate early-returns in Step 2 and the test is trivial). External-dependency drift applies — idempotency is relaxed to "no mutations beyond those traceable to a recorded fetch event in the change report". Session-boundary breach (recursive-discipline) is tracked as an Acknowledged Residual since Layer A cannot fully verify session boundaries — surfaced as operator glance, not a mechanical failure.

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

### Reconciliation outcomes

- **All STRICT pass** → finalize the refresh. Write both files, render the change report, surface follow-up actions.
- **Any STRICT fail** → propose targeted restorations (re-write the bad `last_refreshed:` in canonical format, add the missing provenance row for the unpaired technique, restore the dropped section heading, trim lowest-evidence techniques to fit the 2K budget) and re-run Layer A on the patched state. **Hard cap: 2 iterations** (per `rules/contract-authoring.md §Small-bound carve-out`; bound = 2 → hard rule, no graceful +1). If still failing after iteration 2, surface to the user; do not auto-publish the refresh.
- **Only SOFT warnings** (`added_techniques_vs_cited_sources` skew, `last_refreshed_backward_motion`) → finalize but surface the warnings in the change-report Summary so the operator gets a final-glance opportunity.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **Cross-session state corruption / session-boundary breach.** This skill is the named gateway for baseline mutation (CLAUDE.md §Hard Constraints #6), but the rule says "no mid-session edits" — legitimate path is invocation between sessions. A run that mutates the baseline within an already-running review session passes STRICT-1 (idempotent within itself) and STRICT-4 (sync integrity holds) yet still violates the rule. Only Builder-agent session-state awareness surfaces this; the diff is silent on session boundaries.
2. **External-dependency drift.** This skill consults `WebSearch` / `WebFetch` to discover current best-practice techniques; the same repo state on different days can legitimately yield different mutations because the external corpus moved. Idempotency is relaxed to "no mutations beyond those traceable to a recorded fetch event in the change report".
3. **Semantic correctness of evidence-class assignment.** Layer A treats the four canonical labels as a self-contained predicate. It does not catch the case where the skill labeled a technique "Proven result" when the cited source is actually a single benchmark with N=1. NLI on the source's body is required and not implemented here.

## Hard Rules

- Preserve the three section headings, but allow prose structure changes needed for evidence classification
- Do not exceed 2K tokens in the output file
- Every technique must have an entry in engineering-baseline-provenance.md
- Do not remove techniques unless evidence shows they are wrong or superseded
- If WebSearch fails or user declines changes, leave the baseline unchanged
