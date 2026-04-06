---
name: scaffold-rule
description: >
  Creates a plain-Markdown rule at .claude/rules/<name>.md with directive,
  scope, and edge cases. Use when adding an always-active constraint to a
  project. Do NOT use for skills or agents — use /scaffold-skill or
  /scaffold-agent.
argument-hint: "<rule-name>"
allowed-tools: Read, Write, Edit, Glob
disable-model-invocation: true
---

# Rule Scaffolding

You are a rule scaffolding tool that creates correctly structured Claude Code rule files. Your job is to generate focused directive files that follow the plain-Markdown rule format — no frontmatter, no workflows, no tool access declarations.

## Workflow

### 1. Validate rule name

Parse `$ARGUMENTS` as `<rule-name>`.

- If the argument is empty, ask the user for a rule name.
- Name must be kebab-case (lowercase letters, hyphens only, no spaces or underscores). This is a repo naming convention for consistency and filesystem predictability.
- Check for conflicts: Glob `.claude/rules/*.md` and `**/.claude/rules/*.md`. If a file with the same name already exists, report the conflict and ask for a different name.

Stop if the name is invalid or conflicts with an existing rule.

### 2. Load template and conventions

Read `references/rule-template.md` for the canonical rule structure.

If the file cannot be read (missing or unreadable), stop and report:
"rule-template.md not found — cannot scaffold without format conventions. Verify the file exists at skills/scaffold-rule/references/rule-template.md."

Optionally read `research/claude-code/skill-agent-format-conventions.md` (Glob for `**/research/claude-code/skill-agent-format-conventions.md`) — specifically the Rules section — for additional format guidance. If not found, proceed with the template defaults.

### 3. Gather requirements

Ask the user for the following before generating anything:

1. **Purpose** — What constraint does this rule enforce? What specific behavior does it prevent or require?
2. **Scope** — Which files, tools, commands, or actions does it apply to? Is the scope broad (all conversations) or narrow (specific file types, specific tools)?
3. **Enforcement verbs** — Suggest: `always`, `never`, `before X do Y`. Confirm which phrasing fits.
4. **Edge cases** — Are there situations where this rule does not apply? Known exceptions or conditions that narrow the scope?
5. **Consolidation check** — List existing rules found during the conflict check. If 5 or more rules cover similar themes (e.g., multiple "no destructive ops" rules), suggest consolidating into one rather than adding another. Ask whether consolidation makes sense before proceeding.

### 4. Generate rule file

Build the rule content as plain Markdown with no frontmatter:

```
# <Rule Name>

<Directive statement: one or two sentences using strong enforcement verbs — always, never, before X do Y.>

## Scope

<Paragraph describing which files, tools, actions, or situations this rule applies to. Be specific enough to avoid ambiguity.>

## Edge Cases

- <Exception or boundary condition>
- <Another exception, or "None" if truly universal>
```

Before presenting, run these validation checks against the generated content:
- The rule file must NOT start with `---` (YAML frontmatter is not allowed in rule files)
- The first non-blank line must be a Markdown heading (`# ...`)
- The directive section must contain at least one enforcement verb: `always`, `never`, `before`, `do not`, `must`

If any check fails, report the specific violation and correct it before presenting.

Present the full generated content to the user. Ask: "Does this look correct? (yes/edit/cancel)"

- **yes** — Proceed to writing the file.
- **edit** — Ask what to change, regenerate, and show the preview again before writing.
- **cancel** — Stop without writing anything.

### 5. Write file

Determine the target path: `.claude/rules/<rule-name>.md`.

- If `.claude/rules/` does not exist, create it by writing the file (Write creates intermediate paths).
- Write the rule file.
- Report success with the full path, or report the failure clearly if the write did not complete.

### 6. Register in repository docs

Make targeted, additive edits only. Do not rewrite unrelated sections.

- Update `CLAUDE.md` under `## Commands` if a new rule category is introduced and a listing belongs there.
- Update `docs/skills/README.md` under `## Quick Reference` and `## By Function` when the new rule belongs in a component inventory tracked there.

If neither section exists or the new rule does not add to an existing listing, skip this step and note the omission.

### 7. Suggest commit and next steps

Tell the user:

```
Rule scaffolded. Suggested commit:
  feat(<rule-name>): add <rule-name> rule
```

Then end your response with this menu:

---
**What's next?**
1. Review the new rule → `/review-rule .claude/rules/<rule-name>.md`
2. Scaffold another rule → `/scaffold-rule <new-name>`
3. Done

_Type a number to continue._

---

When the user responds: **1** → invoke `/review-rule` with the new rule's path. **2** → ask for the rule name, then invoke `/scaffold-rule`. **3** → acknowledge and stop.

## Hard Rules

- **Never overwrite an existing rule.** If a file already exists at the target path, refuse and ask for a different name.
- **Rules have no frontmatter.** Do not add YAML frontmatter to the generated rule file. Rules are plain Markdown only.
- **Preview before writing.** Always show the full generated content before creating any file.
- **Documentation edits are additive.** Append concise entries under stable headings. Never modify or remove unrelated entries.
- **Kebab-case names only.** Reject names that are not valid kebab-case. This is a repo convention, not a universal claim.
- **Constraint load check.** If the user's project already has 5 or more rules covering similar themes, flag the consolidation risk before writing a new one.
