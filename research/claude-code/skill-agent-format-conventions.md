---
last_refreshed: 2026-04-19
---

# Claude Code Skill and Agent Format Conventions

**Sources:**
- [Anthropic: Equipping agents with agent skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills) (official skill format documentation)
- [Anthropic: Building agents with Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk) (agent format)
- [Anthropic: Agent Skills Specification](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) (April 2026)
- [Anthropic: Claude 4 Best Practices](https://platform.claude.com/docs/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices) (April 2026)
- [Anthropic: Agent SDK Hooks](https://platform.claude.com/docs/en/agent-sdk/hooks) (April 2026)
- Exploration of real-world projects using Claude Code skills and agents (Talos-Homelab, private-site repositories)

**Fetched:** 2026-04-04 (updated from 2026-03-24)

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
name: skill-name                    # Required: kebab-case, max 64 chars, no "anthropic"/"claude"
description: "..."                  # Required: what it does and when to trigger; max 1024 chars, no XML tags
argument-hint: [arg1|arg2]          # Optional: hint for arguments
disable-model-invocation: true      # Optional: Claude cannot invoke (user only)
user-invocable: false               # Optional: user cannot invoke (Claude only)
allowed-tools: Read, Grep, Glob     # Optional: restrict tool access
context: fork                       # Optional: run in isolated subagent
agent: Explore                      # Optional: which agent type when forked
---
```

**Frontmatter constraints (Anthropic April 2026):**
- `name`: max 64 characters, lowercase letters + hyphens + numbers only, cannot contain "anthropic" or "claude" as a substring
- `description`: max 1024 characters, non-empty, no XML tags (`<`, `>`)
- Use `tools` (array form) or `allowed-tools` (inline string) — not both

### Token Budget (Progressive Disclosure)

Skills load in three levels (Anthropic Agent Skills Specification, April 2026):

| Level | Content | Token target | When loaded |
|-------|---------|-------------|-------------|
| Level 1 | Frontmatter metadata | ~100 tokens | Always |
| Level 2 | SKILL.md instructions | < 5,000 tokens | On trigger |
| Level 3+ | Reference files | Effectively unlimited | Loaded as needed via Read |

Keep SKILL.md under 5,000 tokens. Move stable knowledge (lookup tables, templates, checklists) to `references/` so it's loaded only when the skill needs it.

### Cross-Surface Constraints

Skills now work across Claude.ai, Claude API, Claude Code, and Claude Agent SDK. Constraints vary by surface:
- **Claude Code** — full network access, Bash available
- **Claude API** — no network access, no runtime package install
- **Claude.ai** — varying network access depending on plan

Skills should degrade gracefully when a tool (WebFetch, WebSearch, Bash) is unavailable — probe availability before depending on it.

### Invocation Control Matrix
- **Default** — Both users and Claude can invoke
- `disable-model-invocation: true` — Users only (use for side effects like deploys, commits)
- `user-invocable: false` — Claude only (use for background knowledge)

### Body Conventions
- Heading and narrative explanation of purpose
- Functional role statement first: "You are a [functional role] that [purpose]."
- Workflow sections with numbered steps
- Inline bash commands in code blocks
- Safety gates, stop conditions, recovery actions
- Output format specification
- Hard rules at the end (negative constraints only)

## Agents

### Location and Structure
```
.claude/agents/<agent-name>.md      (single file, self-contained)
```

### Frontmatter Fields
```yaml
---
name: agent-name                    # Required: kebab-case, max 64 chars
description: "..."                  # Required: when/how to trigger; max 1024 chars, no XML tags
model: sonnet                       # Optional: sonnet, opus, haiku, inherit
color: blue                         # Optional: visual indicator
tools:                              # Optional: array form (prefer for multi-tool lists)
  - Read
  - Glob
allowed-tools: Read, Glob           # Optional: inline form (use for 1-2 tools)
maxTurns: 10                        # Optional: max conversation turns (runaway prevention)
background: true                    # Optional: run as background agent
isolation: worktree                 # Optional: worktree isolation for background agents
memory: user                        # Optional: persistence scope (user/project/local)
initialPrompt: "..."                # Optional: structured initial context injected at start
mcpServers:                         # Optional: additional MCP server access
  - server-name
skills:                             # Optional: skills available to the agent
  - skill-name
---
```

Use `tools` (array) or `allowed-tools` (inline string) — not both. Omit to allow all tools.

> **Agent-exclusive fields** ([source](https://docs.anthropic.com/en/docs/claude-code/sub-agents)): `maxTurns` prevents runaway agents. `background: true` + `isolation: worktree` recommended for long-running background tasks. `mcpServers` and `skills` expand attack surface — apply least-privilege. Plugin agents (installed via `--plugin-dir`) cannot use `mcpServers` or `permissionMode`. `skills` injects full skill content into subagent context at startup (token cost). Subagent nesting is prohibited.

### Example Block Placement

`<example>` blocks belong inside the `description` field, not the body. 1-2 examples is the recommended range; use them when trigger conditions are non-obvious.

```yaml
description: >
  Reviews pull request diffs for correctness and style.
  Use when a user asks to review a PR or check code quality before merging.
  <example>
  Context: User is about to merge a feature branch
  user: "Can you review my PR before I merge?"
  assistant: "I'll use the pr-reviewer agent to check the diff."
  <commentary>
  User explicitly requesting review of a pull request — clear trigger.
  </commentary>
  </example>
```

## Hook Events

The Agent SDK supports 26 hook event types (Anthropic Agent SDK Hooks, April 2026). The `allowed-tools` frontmatter field in skills maps to the PreToolUse permission model. Key events:

| Category | Events |
|----------|--------|
| Tool lifecycle | PreToolUse, PostToolUse, PostToolUseFailure |
| Session | SessionStart, SessionEnd, UserPromptSubmit, Stop, StopFailure |
| Subagents | SubagentStart, SubagentStop |
| Compaction | PreCompact, PostCompact |
| Permissions | PermissionRequest, PermissionDenied |
| Tasks | TaskCreated, TaskCompleted |
| Config/workspace | ConfigChange, CwdChanged, FileChanged, WorktreeCreate, WorktreeRemove |
| Agent coordination | TeammateIdle, InstructionsLoaded |
| Notifications | Notification |
| Elicitation | Elicitation, ElicitationResult |

**Permission priority**: deny > ask > allow when multiple hooks conflict.
**Subagent isolation**: Subagents do NOT inherit parent permissions — tool grants must be declared explicitly.
**Command handler timeout**: 600 seconds default (10 minutes). Async hooks (`{"async": true}`) return immediately without blocking.

See `skills/develop-hooks/` for the full scaffolding skill.

## Model Selection Conventions
- **Haiku** — Simple checks, fast, cheap, repetitive tasks
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

## Skill Writing Best Practices

These rules apply when writing or generating Claude Code skills, agents, or rules. Derived from Tier 1 research (2026-04-04).

### Instruction Language
Use natural phrasing — avoid MUST/CRITICAL/ALWAYS. Claude 4.6 overtriggers on aggressive language (Anthropic Claude 4 Best Practices). Write "use this tool when…" not "ALWAYS use this tool when…".

### Role Statements
Use functional roles only: "You are a [functional role] that [purpose]." Demographic or broad expert personas (e.g., "You are a senior SRE") cause up to 26.2% performance degradation from irrelevant persona cues (arXiv:2602.12285, AAAI 2026). Expert personas help generative tasks but hurt discriminative tasks (arXiv:2603.18507).

### Examples
3-5 examples maximum, in `<example>` tags. Over-prompting actively degrades performance (arXiv:2509.13196). For agents, examples go in the `description` field frontmatter. For skills, they may appear in the body's trigger/activation section.

### Output Contracts (Foldable)
Design outputs as: essential findings first, supporting detail second. This enables context-folding by orchestrators and safe summarization (Context-Folding, arXiv:2510.11967).

### DAG Composition
Skills should work standalone AND as nodes in workflow chains. Design for composability — inputs and outputs should be parseable by other skills (arXiv:2603.02176).

### Least-Privilege Tools
Declare only the tools the skill's workflow actually uses. Least-privilege enforcement incurs only 1-6% latency overhead and significantly improves safety (MiniScope, arXiv:2512.11147).

## Agent Frontmatter 2026 Catalog

*Added 2026-04-19 after Opus 4.7 release (2026-04-16, CLI v2.1.111). Previously implicit fields are now documented explicitly with semantics and model-compatibility.*

### Full 15-Field Catalog

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `name` | string | Yes | — | kebab-case, max 64 chars, no "anthropic"/"claude" substring |
| `description` | string | Yes | — | max 1024 chars, no XML tags |
| `model` | string | No | `inherit` | `sonnet`, `opus`, `haiku`, `inherit`, or full model ID (e.g. `claude-opus-4-7`) |
| `color` | string | No | — | Visual ID: red, blue, green, yellow, purple, orange, pink, cyan |
| `tools` | array\|string | No | all | Allowlist; mutually exclusive with `disallowedTools` in spirit |
| `disallowedTools` | array\|string | No | — | Denylist; subtracted from inherited tools |
| `maxTurns` | integer | No | ∞ | Runaway prevention |
| `background` | boolean | No | `false` | Pre-approves permissions, disables AskUserQuestion |
| `isolation` | string | No | `shared` | `worktree` spawns isolated git worktree with auto-cleanup |
| `memory` | string | No | `none` | `user` / `project` / `local` — first 200 lines / 25 KB injected |
| `initialPrompt` | string | No | — | Auto-submitted on start via `--agent` or `agent` setting |
| `mcpServers` | array | No | — | Additional MCP server access; NOT supported in plugin agents |
| `skills` | array | No | — | Full skill content injected at startup; NOT inherited from parent |
| `hooks` | object | No | — | Lifecycle hooks (PreToolUse, PostToolUse, PostToolUseFailure, Stop) |
| `permissionMode` | string | No | `default` | 6 modes; see hierarchy below |
| `effort` | string | No | `inherit` | Opus 4.7 exclusive for `xhigh` level |

### `effort` Field (Opus 4.7+)

| Level | Compatible models | Use case |
|-------|-------------------|----------|
| `low` | Sonnet, Opus, Haiku | Fast, simple tasks; aggressive scoping |
| `medium` | Sonnet, Opus, Haiku | Balanced agentic workflows |
| `high` (default) | Sonnet, Opus, Haiku | Complex reasoning, standard agentic |
| `xhigh` | **Opus 4.7 only** | Long-horizon work (30+ min), exploratory multi-step |
| `max` | Opus 4.7 | Frontier problems without cost ceiling |

### `permissionMode` Hierarchy

6 values: `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`.

**Parent-overrides-child rule** (subagent dispatch):
- Parent `bypassPermissions` or `acceptEdits` → sub-agent inherits, cannot override.
- Parent `auto` → sub-agent inherits classifier rules, frontmatter override ignored.
- Otherwise: sub-agent frontmatter wins.

### Opus 4.7 Breaking Changes (SAMP-1 / SAMP-2)

Opus 4.7 (released 2026-04-16) removes sampling parameters and changes the tokenizer. Review rules:

- **SAMP-1** (PE dimension, body check): skill/agent body must not contain hardcoded `temperature`, `top_p`, `top_k` references. Regex: `/\b(temperature|top_p|top_k)\s*[:=]/i`. FAIL caps PE at Grade C.
- **SAMP-2** (Metadata dimension, frontmatter check): frontmatter override block must be free of removed sampling params. FAIL is hard F — at runtime, Opus 4.7 returns 400-error.
- **Extended thinking budgets removed**: only adaptive thinking (`thinking: {type: "adaptive"}`) supported.
- **New tokenizer**: ~1×–1.35× more tokens per text vs Opus 4.6 (up to ~35 % more). Cached prefixes sized for 4.6 may drop below the 4,096-token Opus cache minimum on 4.7. Re-size prefixes accordingly.
- **Thinking omitted by default**: `display: "omitted"` (previous: `"summarized"`).
- **Task Budgets (Beta)**: advisory token limit across the agentic loop; not a hard cap like `max_tokens`.
- **Literal instruction following**: less inference; does not generalize unstated requests.
- **Fewer tool calls by default**: more reasoning, fewer tool invocations.
- **Fewer subagents spawned by default**: steerable via prompting.
- **High-resolution vision**: max 2576 px / 3.75 MP (previously 1568 px / 1.15 MP).

### Archetype Defaults

Review agent (for `/review-agent`):
```yaml
name: review-agent
model: opus
effort: high
tools: Read, Grep, Bash
permissionMode: plan
memory: user
```

Build agent (CI-fix, async):
```yaml
name: build-agent
model: sonnet
effort: xhigh
tools: Read, Edit, Bash, Glob
maxTurns: 15
background: true
isolation: worktree
```

Research agent (knowledge gathering):
```yaml
name: research-agent
model: haiku
effort: medium
tools: Read, Grep, Glob, WebSearch, WebFetch
maxTurns: 20
memory: project
```

### Sources for This Section

Tier 1:
- [Anthropic — Opus 4.7 release notes](https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-7) — 2026-04-16
- [Anthropic — Effort Parameter](https://platform.claude.com/docs/en/build-with-claude/effort)
- [Claude Code — Sub-Agents](https://code.claude.com/docs/en/sub-agents)

Tier 2:
- [GitHub Blog: Claude Opus 4.7 GA](https://github.blog/changelog/2026-04-16-claude-opus-4-7-is-generally-available/)

Gaps flagged (unverified in docs): when `effort` is evaluated in a subagent vs main-thread dispatch; worktree cleanup criteria (git-clean vs uncommitted-tolerance); memory-injection timing (session start vs per-turn); Task-Budgets interaction with `effort`; hook execution order in subagent chains.
