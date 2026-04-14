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

## Hard Rules

- Preserve the three section headings, but allow prose structure changes needed for evidence classification
- Do not exceed 2K tokens in the output file
- Every technique must have an entry in engineering-baseline-provenance.md
- Do not remove techniques unless evidence shows they are wrong or superseded
- If WebSearch fails or user declines changes, leave the baseline unchanged
