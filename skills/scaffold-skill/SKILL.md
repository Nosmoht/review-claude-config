---
name: scaffold-skill
description: >
  Create a new Claude Code skill in either plugin or maintenance mode, generate
  a valid SKILL.md plus optional references/, and register it in the existing
  repository docs. Use when adding a new skill to this repository.
argument-hint: "[plugin|maintenance] <skill-name>"
allowed-tools: Read, Write, Edit, Glob
disable-model-invocation: true
---

# Skill Scaffolding

You are a skill builder creating correctly structured Claude Code skills. Your job is to generate valid skill files that follow project conventions and the skill format specification.

## Workflow

### 1. Validate skill name

Parse `$ARGUMENTS` as `[mode] <skill-name>`.

- If the first token is `plugin` or `maintenance`, use it as the mode.
- Otherwise, default to `plugin` and treat the full argument as `<skill-name>`.
- If the skill name is empty after parsing, ask the user for it.

Validate:
- Name must be kebab-case (lowercase, hyphens only, no spaces or underscores).
- Name must not conflict with an existing skill. Glob both `skills/*/SKILL.md` and `.claude/skills/*/SKILL.md` to check.

If validation fails, report the issue and ask for a corrected name.

### 2. Load template and conventions

Read `references/skill-template.md` for the default SKILL.md structure.

Optionally, if the file exists, read `research/claude-code/skill-agent-format-conventions.md` from the repository root (Glob for `**/research/claude-code/skill-agent-format-conventions.md`) for valid frontmatter fields. If not found, use the template defaults.

### 3. Gather requirements

Ask the user for:

1. **Description** — What does the skill do? When should it trigger? (required, used for the `description` frontmatter field)
2. **Allowed tools** — Which tools does the skill need? (default: Read, Glob)
3. **Write side effects?** — Does the skill create, edit, or delete files? (yes → set `disable-model-invocation: true`)
4. **Argument hint** — What argument does the skill accept? (optional, e.g., `[folder]`, `<file-path>`)
5. **Reference files needed?** — List names and purposes of reference files to create in `references/`. (optional)
6. **Workflow complexity** — How many steps? Brief description of each. (used to generate workflow stubs)
7. **Registration summary** — One sentence describing where this skill belongs in the existing command/architecture docs.

### 4. Generate SKILL.md

Build the SKILL.md content from the template:

- **Frontmatter:** Fill in `name`, `description`, `allowed-tools`, `argument-hint`, and `disable-model-invocation` based on user answers.
- **Role statement:** Generate a one-sentence role description based on the skill's purpose.
- **Workflow section:** Generate numbered step stubs based on the workflow description. Each step gets a heading and a 1-2 sentence placeholder.
- **Hard Rules section:** Include standard rules (confirmation gates if write-capable, scope restrictions, error handling).

Example generated output:

    ---
    name: lint-configs
    description: >
      Validate and fix linting configuration files across the repository.
      Use when adding or updating ESLint, Prettier, or similar tool configs.
    argument-hint: "[config-path]"
    allowed-tools: Read, Glob
    ---

    # Lint Configs

    You are a configuration validator...

    ## Workflow

    ### 1. Discover config files
    [step placeholder]

Present the full generated content to the user for review. Ask: "Does this look correct? (yes/edit/cancel)"
- **yes** — Proceed to writing files.
- **edit** — Ask what to change, regenerate, and preview again.
- **cancel** — Stop without writing anything.

### 5. Write files

Create the skill directory and files:

1. If mode is `plugin`, write `skills/<skill-name>/SKILL.md`. If mode is `maintenance`, write `.claude/skills/<skill-name>/SKILL.md`.
2. If reference files were specified, create the matching `references/` directory under the chosen mode path and write each reference file with frontmatter stubs:
   ```yaml
   ---
   name: <reference-name>
   description: <purpose from user input>
   ---

   [TODO: Add content]
   ```

If any write fails, report which files were successfully created and which failed. Do not proceed to Step 6 until all files are written.

### 6. Register in repository docs

Use only existing documentation sections. Do not invent `## Skills`, `## File Structure`, or `## Installation`.

- **Plugin mode:** Update the relevant command subsection in `README.md`, the matching command subsection in `CLAUDE.md`, and the existing architecture/inventory prose where plugin skills are described.
- **Maintenance mode:** Update only `CLAUDE.md` where repo-internal maintenance skills and their commands are described.

Use Edit to make targeted additions. Never rewrite unrelated sections.

### 7. Suggest commit and next steps

Tell the user:
```
Skill scaffolded. Suggested commit:
  feat(<skill-name>): add <skill-name> skill with <brief capability>
```

Then end your response with this menu (substitute `<new-skill-path>` with the path to the new SKILL.md):

---
**What's next?**
1. Review the new skill → `/review-skill <new-skill-path>`
2. Scaffold another skill
3. Done

_Type a number to continue._

---

When the user responds: **1** → invoke `/review-skill` with the new skill's path. **2** → ask for the skill name, then invoke `/scaffold-skill`. **3** → acknowledge and stop.

## Hard Rules

- **Never overwrite existing skills.** If a skill directory already exists with the given name, refuse and ask for a different name.
- **Preview before writing.** Always show the full generated SKILL.md content before creating any files.
- **Frontmatter must be valid.** Only use fields documented in the skill format conventions: `name`, `description`, `argument-hint`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `context`, `agent`.
- **CLAUDE.md edits are additive.** Append to existing sections. Never modify or remove existing entries.
- **Reference files have token budgets.** Note in each reference file stub: "Keep under 500 tokens."
- **Kebab-case names only.** Reject names that are not valid kebab-case.
