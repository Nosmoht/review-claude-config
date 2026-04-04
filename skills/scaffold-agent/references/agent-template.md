---
name: agent-template
description: Canonical structure for Claude Code agent files (.md format). Keep under 500 tokens.
---

## Frontmatter Template

```yaml
---
name: <agent-name>              # Required: kebab-case, max 64 chars, no "anthropic"/"claude"
description: >                  # Required: what it does, when to trigger; max 1024 chars
  <multi-line description>
  <example>
  Context: <situation that warrants triggering this agent>
  user: "<message the user sends>"
  assistant: "<how the assistant responds>"
  <commentary>
  <why this example triggers the agent>
  </commentary>
  </example>
model: sonnet                   # Optional: haiku | sonnet | opus | inherit
color: blue                     # Optional: visual indicator
tools:                          # Optional: array form — prefer this for multi-tool lists
  - Read
  - Glob
allowed-tools: Read, Glob       # Optional: inline form — use for 1-2 tools
---
```

Use `tools` (array) or `allowed-tools` (inline string) — not both. Omit the field to allow all tools.

## Model Selection

| Model  | When to use                                          |
|--------|------------------------------------------------------|
| haiku  | Simple checks, fast lookups, cheap repetitive tasks  |
| sonnet | Most analysis and review tasks — recommended default |
| opus   | Complex reasoning, architecture, deep review         |

## Body Structure

```markdown
# <Agent Name>

<Role statement: "You are a [functional role] that [purpose].">

## Workflow

### 1. <First step>
<What to do; include conditionals and stop conditions>

### 2. <Next step>
<Continue sequential workflow>

### N. <Final step>
<Present results or output>

## Hard Rules

- <Safety constraint>
- <Scope restriction>
- <Error handling guarantee>
```

## Conventions

- `<example>` blocks go inside the `description` field, not the body.
- 1-2 examples is the recommended range; use them when trigger conditions are non-obvious.
- Body: role statement first, then `## Workflow`, then `## Hard Rules`.
- Hard Rules: negative constraints only — what the agent must never do.
