---
name: refresh-engineering-baseline
description: >
  Update the engineering baseline reference file with current best practices
  from web research. Searches for latest prompt engineering, context engineering,
  and Claude Code configuration guidance, then merges findings into the baseline.
  Use when the baseline's last_refreshed date is older than 3 months.
disable-model-invocation: true
allowed-tools: WebSearch, WebFetch, Read, Write
---

# Refresh Engineering Baseline

You are a research librarian maintaining a curated technical reference. Your job is to verify sources rigorously, preserve what works, and add only well-evidenced new techniques.

Update `references/engineering-baseline.md` with current research findings.

## Workflow

### 1. Locate the baseline file

Read `skills/review-claude-config/references/engineering-baseline.md`. If the file is not found, report the error and stop.

Read the current file content and extract the `last_refreshed` date from frontmatter. If `last_refreshed` is missing or unparseable, treat the baseline as stale and proceed directly to Step 3.

Attempt a trivial WebFetch (e.g., fetch "https://docs.anthropic.com"). If it fails or is unavailable, set `webfetch_available = false` and continue with WebSearch-only mode.

### 2. Freshness gate

If `last_refreshed` is less than 90 days ago:
- Tell the user: "Baseline was last refreshed on [date] ([N] days ago). Refresh is recommended after 90 days."
- Ask: "Force refresh anyway? (yes/no)"
- If no, stop. If yes, continue.

### 3. Research current best practices

Run these WebSearch queries (replace `[current year]` with the actual year). After each query, check if new actionable techniques were found. If two consecutive queries yield no new techniques beyond what earlier queries found, skip remaining queries and note skipped queries in the change report.

- "Claude Code skills agents best practices [current year]"
- "prompt engineering techniques evidence research [current year]"
- "context engineering LLM agents best practices [current year]"
- "AI agent tool design best practices [current year]"
- "Anthropic Claude Code documentation skills"

For each search, extract only actionable techniques with evidence.

Deduplicate across queries: if the same technique appears in multiple search results, consolidate into a single entry citing the strongest source. Do not list the same technique multiple times in the preview.

#### Source quality criteria

Accept a technique only if it meets ALL of:
1. **Credible source** — Official vendor documentation (Anthropic, OpenAI, Google DeepMind), peer-reviewed research (arXiv with citations), or documented production system (Manus, Vercel, LangChain, etc.)
2. **Actionable** — Describes a specific, implementable technique (not a general principle like "be clear")
3. **Cross-validated** — Either (a) appears in 2+ independent credible sources, OR (b) comes from a primary vendor source with concrete evidence (benchmarks, A/B tests, production metrics)

Discard: marketing content, opinion pieces without evidence, tutorials without primary sources, sources older than 18 months.

#### WebSearch failure handling

- If WebSearch is completely unavailable (tool error), stop and tell the user: "WebSearch is required for baseline refresh but is unavailable. Baseline was not modified."
- If fewer than 3 of 5 queries return useful results, warn the user: "Only [N]/5 searches returned actionable results. Proceeding with limited data — review changes carefully."
- If no queries return useful results, stop and report: "No actionable search results. Baseline was not modified."

### 3.5. Full-content retrieval (when WebFetch is available)

If `webfetch_available = true`, after completing all WebSearch queries:

1. From all search results across queries, identify the 3-5 most promising URLs (prefer: official Anthropic docs, peer-reviewed research, documented production systems).
2. Fetch each URL with WebFetch using a targeted prompt: "Extract actionable prompt engineering, context engineering, and tool design techniques with evidence. Max 500 words."
3. Use full article content — not just search snippets — when extracting techniques in Step 4. Full content provides benchmarks, nuanced conditions, and code examples that snippets miss.

If `webfetch_available = false`, skip this step and proceed with search snippets as before.

### 4. Merge findings

For each section (Prompt Engineering, Context Engineering, Tool Design):
- Add new techniques not already covered
- Update existing techniques if newer evidence contradicts or supplements them
- Spot-check 2-3 existing techniques per section against current sources to verify they remain accurate and well-evidenced
- Remove techniques that have been superseded or debunked
- Preserve the existing format: technique name, description, evidence source, check question

Example merge decision:
- Existing: "Few-Shot Examples — Provide 2-3 diverse examples. Source: Brown et al. 2020"
- New finding: "Anthropic 2026 reports few-shot is less effective for Claude 4 on structured tasks but still valuable for ambiguous formats. Source: docs.anthropic.com/..."
- Action: UPDATE — refine the description to note the nuance, cite both sources. Do NOT remove, since it remains valid for ambiguous formats.

### 5. Preview and confirm

Present the proposed changes to the user using the report format from Step 7. Include:
- Techniques to ADD (with source)
- Techniques to UPDATE (show before/after)
- Techniques to REMOVE (with justification)
- Projected token count

Ask: "Apply these changes to engineering-baseline.md? (yes/no)"
If no, stop and preserve the current file.

### 6. Write the updated file

Only after user confirmation. Update `engineering-baseline.md` with:
- Set `last_refreshed` in frontmatter to today's date
- Before writing, estimate the token count of the updated file. If it would exceed 2K tokens, remove the lowest-evidence techniques until it fits, and note the removals in the change report. If removing techniques would compromise coverage of a full section, warn the user before proceeding.
- Preserve the existing structure and section headings
- Add new sources to the Sources section at the bottom

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

- Preserve the file structure and format exactly
- Do not exceed 2K tokens in the output file
- Every technique must cite an evidence source
- Do not remove techniques unless evidence shows they are wrong or superseded
- If WebSearch fails or user declines changes, leave the baseline unchanged
