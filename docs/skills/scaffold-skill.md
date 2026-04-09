# scaffold-skill

Create a new Claude Code skill from a template and register it in the surviving documentation surfaces.

**Command:** `/scaffold-skill [plugin|maintenance|external <target-path>] <skill-name>`
**Location:** `skills/scaffold-skill/SKILL.md`
**Type:** Development
**Allowed Tools:** Read, Write, Edit, Glob, WebSearch, WebFetch
**disable-model-invocation:** true
**Mode Support:** Standalone only

## Purpose

`scaffold-skill` generates a new `SKILL.md`, optional reference stubs, and targeted documentation registrations. This page documents the behavior that must remain stable after the docs trim, especially the registration targets.

## Major Phases

1. Parse mode and validate the skill name.
2. Load the template and optional format-conventions reference.
3. Gather 2–3 core requirements via AskUserQuestion menus with contextual suggestions; auto-derive remaining parameters from description and domain context.
4. Generate and preview the `SKILL.md`.
5. Write the files after confirmation.
6. Register the new skill in the surviving documentation sections.

## Runtime-Specific Behavior

- **Plugin mode output:** writes to `skills/<name>/SKILL.md`.
- **Maintenance mode output:** writes to `.claude/skills/<name>/SKILL.md`.
- **Registration targets:**
  - plugin mode updates `README.md` user-facing command families, `CLAUDE.md` command inventory, and `docs/skills/README.md` inventory/system map when relevant
  - maintenance mode updates `CLAUDE.md` and `docs/skills/README.md` where the new skill belongs in the maintained inventory
- **System-map upkeep:** when a new skill changes workflow composition or comparative mode/research behavior, registration must also update the matching sections in `docs/skills/README.md`, not just the inventory rows.
- **Registration is additive:** it must target stable headings and append concise entries rather than depending on removed prose blocks.

## Interactions

- **Called by:** user directly
- **May be suggested by:** `/apply-audit-findings`, `/suggest-skills`
- **Follow-up:** `/review-skill` for the newly generated skill

## Hard Rules

- Never overwrite an existing skill.
- Always preview before writing.
- Use only valid frontmatter fields.
- Keep documentation registrations additive and anchored to the surviving headings.
