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

Read the current file content and note the `last_refreshed` date.

### 2. Research current best practices

Run these WebSearch queries (adapt based on current year):
- "Claude Code skills agents best practices [current year]"
- "prompt engineering techniques evidence research [current year]"
- "context engineering LLM agents best practices [current year]"
- "AI agent tool design best practices [current year]"
- "Anthropic Claude Code documentation skills"

For each search, extract only actionable techniques with evidence. Discard marketing content, opinion pieces without evidence, and duplicate information.

### 3. Merge findings

Read the existing baseline. For each section (Prompt Engineering, Context Engineering, Tool Design):
- Add new techniques not already covered
- Update existing techniques if newer evidence contradicts or supplements them
- Remove techniques that have been superseded or debunked
- Preserve the existing format: technique name, description, evidence source, check question

### 4. Write the updated file

Update `engineering-baseline.md` with:
- Set `last_refreshed` in frontmatter to today's date
- Keep the file under 2K tokens — if it exceeds this, prioritize techniques with strongest evidence
- Preserve the existing structure and section headings
- Add new sources to the Sources section at the bottom

### 5. Report changes

Tell the user:
- How many new techniques were added
- How many existing techniques were updated
- What was removed (if anything)
- The new `last_refreshed` date

## Hard Rules

- Preserve the file structure and format exactly
- Do not exceed 2K tokens in the output file
- Every technique must cite an evidence source
- Do not remove techniques unless evidence shows they are wrong or superseded
