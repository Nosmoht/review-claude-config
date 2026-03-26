---
name: scaffold-skill
description: >
  Create a new Claude Code skill directory with SKILL.md, optional references/,
  and CLAUDE.md registration. Generates valid frontmatter and phase-based body
  following project conventions. Use when adding a new skill to the repository.
argument-hint: "<skill-name>"
allowed-tools: Read, Write, Edit, Glob
disable-model-invocation: true
---

# Skill Scaffolding

You are a skill builder creating correctly structured Claude Code skills. Your job is to generate valid skill files that follow project conventions and the skill format specification.

## Workflow

### 1. Validate skill name

Parse `$ARGUMENTS` as the skill name. If empty, ask the user for a skill name.

Validate:
- Name must be kebab-case (lowercase, hyphens only, no spaces or underscores).
- Name must not conflict with an existing skill. Glob `.claude/skills/*/SKILL.md` to check.

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

1. Write `.claude/skills/<skill-name>/SKILL.md` with the generated content.
2. If reference files were specified, create `.claude/skills/<skill-name>/references/` and write each reference file with frontmatter stubs:
   ```yaml
   ---
   name: <reference-name>
   description: <purpose from user input>
   ---

   [TODO: Add content]
   ```

If any write fails, report which files were successfully created and which failed. Do not proceed to Step 6 until all files are written.

### 6. Register in CLAUDE.md

Read CLAUDE.md. Add entries to three sections:

- **`## Skills`** — Append: `- /<skill-name> [args]` — Description.`
- **`## File Structure`** — Append the new skill's directory listing.
- **`## Installation`** — Append a `cp -r` command for the new skill.

Use Edit to make targeted additions to each section. Never rewrite existing entries.

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
