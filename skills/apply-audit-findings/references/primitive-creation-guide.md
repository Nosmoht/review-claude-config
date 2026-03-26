---
name: primitive-creation-guide
description: Validation rules and conventions for creating each Claude Code primitive type from audit recommendations
---

## CLAUDE.md Sections

- Use `##` headings for new sections
- Keep each section under 20 lines — bullet points, not prose
- Include specific commands, file paths, line ranges — not generic advice
- Progressive disclosure: point to docs/references, don't inline full content
- Total CLAUDE.md budget: <200 lines. Warn if exceeded after edit

## Hooks

- **Config location:** `<target>/.claude/settings.local.json` under the `hooks` key
- **Script location:** `<target>/hooks/<script-name>.sh` (or `.py`)
- **Hook types:** `PreToolUse` (blocks tool call if non-zero exit), `PostToolUse` (runs after tool completes)
- **Matcher:** tool name pattern (e.g., `Edit`, `Write`, `Bash`)
- **Script conventions:** shebang line (`#!/bin/bash` or `#!/usr/bin/env python3`), exit 0 = pass, non-zero = block
- Use `PreToolUse` for guards (secret detection, file restrictions). Use `PostToolUse` for formatters (ruff, prettier)

## Rules

- **Location:** `<target>/.claude/rules/<name>.md`
- **Format:** Plain Markdown only — NO YAML frontmatter, no `---` delimiters
- Use strong action verbs: "must", "never", "always" — not "should" or "consider"
- One constraint per rule file — keep focused
- Include scope qualifiers (which files, which operations, which contexts)
- Naming: kebab-case, descriptive (`no-secrets.md`, `test-before-commit.md`)

## Skills

- **Never create inline.** Skill creation requires frontmatter, workflow steps, references, and CLAUDE.md registration
- Present the recommendation and instruct: "Run `/scaffold-skill plugin <name>` to create this skill"
- Provide: name, one-line description, and key context from the audit recommendation
