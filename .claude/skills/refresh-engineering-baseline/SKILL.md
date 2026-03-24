---
name: refresh-engineering-baseline
description: >
  Update the engineering baseline reference file with current best practices
  from web research. Searches for latest prompt engineering, context engineering,
  and Claude Code configuration guidance, then merges findings into the baseline.
  Use when the baseline's last_refreshed date is older than 3 months.
disable-model-invocation: true
allowed-tools: WebSearch, Read, Write, Glob
---

# Refresh Engineering Baseline

Update `references/engineering-baseline.md` with current research findings.

## Workflow

### 1. Locate the baseline file

Use Glob to find the engineering-baseline.md file:
- `.claude/skills/review-claude-config/references/engineering-baseline.md`
- If not found, report the error and stop.

Read the current file content and extract the `last_refreshed` date from frontmatter.

### 2. Freshness gate

If `last_refreshed` is less than 90 days ago:
- Tell the user: "Baseline was last refreshed on [date] ([N] days ago). Refresh is recommended after 90 days."
- Ask: "Force refresh anyway? (yes/no)"
- If no, stop. If yes, continue.

### 3. Research current best practices

Run these WebSearch queries (replace `[current year]` with the actual year):
- "Claude Code skills agents best practices [current year]"
- "prompt engineering techniques evidence research [current year]"
- "context engineering LLM agents best practices [current year]"
- "AI agent tool design best practices [current year]"
- "Anthropic Claude Code documentation skills"

For each search, extract only actionable techniques with evidence.

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

### 4. Merge findings

For each section (Prompt Engineering, Context Engineering, Tool Design):
- Add new techniques not already covered
- Update existing techniques if newer evidence contradicts or supplements them
- Remove techniques that have been superseded or debunked
- Preserve the existing format: technique name, description, evidence source, check question

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
- Keep the file under 2K tokens — if it exceeds this, prioritize techniques with strongest evidence
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
