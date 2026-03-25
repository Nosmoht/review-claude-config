# Claude Code Skill and Agent Format Conventions

**Sources:**
- [Anthropic: Equipping agents with agent skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills) (official skill format documentation)
- [Anthropic: Building agents with Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk) (agent format)
- Exploration of real-world projects using Claude Code skills and agents (Talos-Homelab, private-site repositories)

**Fetched:** 2026-03-24

## Skills

### Location and Structure
```
.claude/skills/<skill-name>/
├── SKILL.md          (required — frontmatter + instructions)
├── scripts/          (optional — executable scripts)
├── references/       (optional — reference materials)
└── assets/           (optional — other bundled resources)
```

### Frontmatter Fields
```yaml
---
name: skill-name                    # Required: kebab-case identifier
description: "..."                  # Required: what it does and when to trigger
argument-hint: [arg1|arg2]          # Optional: hint for arguments
disable-model-invocation: true      # Optional: Claude cannot invoke (user only)
user-invocable: false               # Optional: user cannot invoke (Claude only)
allowed-tools: Read, Grep, Glob     # Optional: restrict tool access
context: fork                       # Optional: run in isolated subagent
agent: Explore                      # Optional: which agent type when forked
---
```

### Invocation Control Matrix
- **Default** — Both users and Claude can invoke
- `disable-model-invocation: true` — Users only (use for side effects like deploys, commits)
- `user-invocable: false` — Claude only (use for background knowledge)

### Body Conventions
- Heading and narrative explanation of purpose
- Workflow sections with numbered steps
- Inline bash commands in code blocks
- Safety gates, stop conditions, recovery actions
- Output format specification
- Hard rules at the end

## Agents

### Location and Structure
```
.claude/agents/<agent-name>.md      (single file, self-contained)
```

### Frontmatter Fields
```yaml
---
name: agent-name                    # Required: kebab-case
description: "..."                  # Required: when/how to trigger
model: sonnet                       # Optional: sonnet, opus, haiku, inherit
color: blue                         # Optional: visual indicator
tools: ["Read", "Write"]            # Optional: array of allowed tools
allowed-tools:                      # Alternative array format
  - Read
  - Glob
---
```

### Description Patterns
Agent descriptions can include `<example>` blocks:
```xml
<example>
Context: User wants to create a code review agent
user: "Create an agent that reviews code for quality issues"
assistant: "I'll use the agent-creator agent to generate the configuration."
<commentary>
User requesting new agent creation, trigger agent-creator.
</commentary>
</example>
```

## Model Selection Conventions
- **Haiku** — Simple checks, fast, cheap
- **Sonnet** — Most review/analysis tasks (recommended default)
- **Opus** — Complex reasoning, architecture, migrations, deep reviews

## Rules

### Location and Structure
```
.claude/rules/*.md                  (one rule per file, plain Markdown)
```

### Observed Conventions
- No standardized frontmatter (unlike skills/agents)
- Always-active constraints applied to all conversations
- Plain Markdown content — directives, not workflows
- No tool access, no invocation control, no model selection
- Quality factors differ from skills/agents: rules are constraints, not prompts

### Applicable Review Dimensions
Rules lack tools, frontmatter, and workflow structure. Of the 7 standard review dimensions, only 3 apply:
- **Clarity** — Is the rule unambiguous?
- **Completeness** — Are edge cases and scope boundaries defined?
- **Goal Alignment** — Does the rule achieve its stated constraint?

Not applicable: Prompt Engineering (rules are directives, not prompts), Context Engineering (no tools or progressive disclosure), Safety (no tool access), Metadata (no standardized frontmatter).

**Note:** This section is based on observed usage patterns, not official Anthropic documentation. The dimension selection is derived from structural analysis: rules have no tools (→ Safety, CE irrelevant), no frontmatter (→ Metadata irrelevant), and are directives not prompts (→ PE irrelevant). Update when official rule format docs are published.

## Naming Conventions
- **Skills:** Kebab-case directory names (`gitops-health-triage`, `cilium-policy-debug`)
- **Agents:** Kebab-case filenames (`gitops-operator.md`, `talos-sre.md`)
- **Rules:** Kebab-case filenames (`no-force-push.md`, `require-tests.md`)
- Descriptive, action-oriented names
