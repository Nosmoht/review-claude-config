---
name: skill-template
description: Default SKILL.md template with valid frontmatter fields and body structure
---

## Frontmatter Template

```yaml
---
name: <skill-name>                        # Required: kebab-case identifier
description: >                            # Required: what it does, trigger keywords
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

## Conventions

- Read-only skills: omit `disable-model-invocation`
- Write-capable skills: set `disable-model-invocation: true` and add confirmation gates
- Reference files: create in `references/` subdirectory, keep ≤500 tokens each
- Workflow steps: sequential numbering, explicit conditionals, stop conditions
- Hard Rules: negative constraints at the end of the file
