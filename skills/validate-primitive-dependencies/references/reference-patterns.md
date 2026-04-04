---
name: reference-patterns
description: Dependency detection patterns for Claude Code skills, agents, rules, and hooks. Used by validate-primitive-dependencies.
---

# Reference Patterns

Detection patterns for cross-primitive dependency extraction.

## 1. Slash Command Invocations

**Pattern:** `` `/[a-z][a-z0-9-]+` `` (backtick-enclosed) or `/[a-z][a-z0-9-]+` in prose

**Where they appear:** SKILL.md body — "What's next?" menus, workflow steps, hard rules.

**Resolution:** `/skill-name` maps to `skills/skill-name/SKILL.md` or `.claude/skills/skill-name/SKILL.md`.

**Non-dependency indicators:** Tokens inside fenced code blocks showing sample output are illustrative, not live invocations.

---

## 2. Reference File Reads

**Pattern:** `Read.*references/[^\s"']+\.md`

**Where they appear:** Phase 1 setup steps — "Read `references/foo.md`" or `Read "path/to/references/foo.md"`.

**Resolution:** Resolve relative to the skill directory. Absolute paths starting with `skills/` or `.claude/skills/` are used as-is.

**Non-dependency indicators:** Paths inside triple-backtick fenced blocks that are clearly schema examples rather than instructions.

---

## 3. Sibling Skill Cross-Reads

**Pattern:** `Read.*skills/[a-z][a-z0-9-]+/references/[^\s"']+\.md`

**Where they appear:** Phase 1 steps where one skill reads another skill's reference file (e.g., `audit-repo` reading `suggest-skills/references/signal-catalog.md`).

**Resolution:** Paths starting with `skills/` are repo-root-relative; `**/` patterns are resolved via Glob.

---

## 4. Subagent Delegation

**Pattern:** `Launch.*Agent|Launch a \*\*.*Agent|Agent.*allowed-tools`

**Where they appear:** Phase headings in SKILL.md — "Launch a **Repo Scanner Agent**".

**Meaning:** Indicates the skill forks a subagent. Subagents do not inherit parent tool grants (per SDK hooks isolation model). Record as informational — no file existence check applies.

---

## 5. Hook Script Paths

**Pattern:** In hooks.json or settings.json hooks array — `"command"` field values containing `.py`, `.sh`, or `./` prefixes.

**Example:** `"command": "python3 ./hooks/pre-commit-check.py"`

**Resolution:** Extract the file path argument. Resolve relative to the hooks config file's directory.

---

## 6. Research References in CLAUDE.md

**Pattern:** Markdown link syntax `[label](path/to/research/file.md)` inside the `## Research References` section.

**Resolution:** Paths are relative to the repo root.

---

## Known Non-Dependency Patterns

| Pattern | Reason to exclude |
|---------|-------------------|
| Paths inside ` ``` ` fenced blocks labeled as output examples | Illustrative, not live reads |
| `/help`, `/clear`, `/exit` | Built-in Claude Code commands, no SKILL.md |
| `**/node_modules/**` paths | Build artifacts |
| Inline variable references like `$ARGUMENTS` or `$PATH` | Shell variables, not file paths |
| `references/` inside a quoted string that is itself inside a code block schema | Schema documentation |
