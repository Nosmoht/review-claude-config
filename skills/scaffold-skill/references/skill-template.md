---
name: skill-template
description: Default SKILL.md template with valid frontmatter fields and body structure for plugin or maintenance skills
last_refreshed: 2026-04-04
---

## Frontmatter Template

```yaml
---
name: <skill-name>                        # Required: kebab-case, max 64 chars, no "anthropic"/"claude"
description: >                            # Required: what it does, trigger keywords; max 1024 chars, no XML tags
  <multi-line description, max 1024 chars>
argument-hint: "<hint>"                   # Optional: e.g., [folder], <file-path>
allowed-tools: Read, Glob                 # Optional: minimal tool set needed
disable-model-invocation: true            # Optional: set if skill writes/edits/deletes
user-invocable: false                     # Optional: set if Claude-only (rare)
---
```

## Body Structure

```markdown
# <Skill Name>

<Role statement: "You are a [role] that [purpose]. Your job is to [core task].">

## Workflow

### 1. <First step>
<What to do, with conditionals and stop conditions>

### 2. <Next step>
<Continue sequential workflow>

### N. <Final step>
<Present results, suggest commit if applicable>

## Hard Rules

- <Safety constraint>
- <Scope restriction>
- <Confirmation requirement if write-capable>
- <Error handling guarantee>
```

## Reference File Template

Reference files in `references/` use minimal YAML frontmatter followed by structured body sections:

```yaml
---
name: <reference-name>            # Required: kebab-case, matches filename
description: <one-line summary>   # Required: what this reference contains
last_refreshed: YYYY-MM-DD        # Required: ISO date; participates in check-repo-health freshness
---

## Overview

<Describe the purpose and scope of this reference. One or two sentences.>

## Key Points

- <Key point 1>
- <Key point 2>
```

Set `last_refreshed` to today's date on creation and update it on any substantive content change.

## Conventions

- Read-only skills: omit `disable-model-invocation`
- Write-capable skills: set `disable-model-invocation: true` and add confirmation gates
- Reference files: create in `references/` subdirectory, keep ≤500 tokens each, include `last_refreshed` in frontmatter
- Workflow steps: sequential numbering, explicit conditionals, stop conditions
- Hard Rules: negative constraints at the end of the file
- Registration must target existing `README.md`/`CLAUDE.md` sections only; never assume `## Skills`, `## File Structure`, or `## Installation` exist
- Token budget: SKILL.md Level 2 target is <5,000 tokens; move stable content to `references/`
- Role statement: use functional roles ("You are a [role] that [purpose]") — no demographic or expert personas
- Instruction language: use natural phrasing; avoid MUST/CRITICAL/ALWAYS (overtrigger risk on Claude 4.6)

For full format conventions and skill writing best practices, see `research/claude-code/skill-agent-format-conventions.md`.
