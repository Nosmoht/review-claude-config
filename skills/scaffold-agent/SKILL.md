---
name: scaffold-agent
description: >
  Create a new Claude Code agent (.md file) with valid frontmatter, example blocks,
  and a numbered workflow body, then register it in repository docs. Use when adding
  a new subagent to this repository or to any project's .claude/agents/ directory.
argument-hint: "<agent-name>"
allowed-tools: Read, Write, Edit, Glob
disable-model-invocation: true
---

# Agent Scaffolding

You are an agent builder creating correctly structured Claude Code agent files. Your job is to generate valid agent .md files that follow the project's format specification and register them in the relevant documentation. Naming guidance here is a repo convention for consistency, not a claim of universal naming science.

## Workflow

### 1. Validate agent name

Parse `$ARGUMENTS` as `<agent-name>`.

- If the argument is empty, ask the user for the agent name.

Validate:
- Name must be kebab-case (lowercase, hyphens only, no spaces or underscores). This is a repo naming convention for CLI and filesystem usability.
- Name must not exceed 64 characters.
- Name must not contain `anthropic` or `claude` as a substring.
- Name must not conflict with an existing agent. Glob `.claude/agents/*.md` and `**/.claude/agents/*.md` to check.

If validation fails, report the specific issue and ask for a corrected name. Stop and wait — do not continue until a valid name is provided.

### 2. Load template and conventions

Read `references/agent-template.md` for the canonical agent .md structure and model selection guidance.

If the file cannot be read (missing or unreadable), stop and report:
"agent-template.md not found — cannot scaffold without format conventions. Verify the file exists at skills/scaffold-agent/references/agent-template.md."

Optionally, if the file exists, read `research/claude-code/skill-agent-format-conventions.md` (Glob for `**/research/claude-code/skill-agent-format-conventions.md`) for additional valid frontmatter fields. If not found, use the template defaults.

### 3. Gather requirements

Ask the user for the following. Collect all answers before proceeding:

1. **Description** — What does the agent do? When should it trigger? (required, max 1024 chars; the description becomes the frontmatter `description` field and guides activation)
2. **Example blocks** — Provide 1-2 activation examples showing the context, user message, and assistant response? (recommended for precise trigger targeting; format is shown in the template)
3. **Model** — haiku / sonnet / opus. Default: sonnet. See the template for when-to-use guidance.
4. **Color** — Optional visual indicator (e.g., `blue`, `green`, `purple`). Skip if not needed.
5. **Tools / allowed-tools** — Which tools does the agent need? Apply least-privilege: list only the tools the agent's workflow actually requires.
6. **Workflow complexity** — How many steps? Brief description of each step. (used to generate numbered workflow stubs in the body)

If any required field is missing after asking, prompt again. Do not generate the agent .md with empty required fields.

### 4. Generate and validate agent .md

Build the content from `references/agent-template.md`:

- **Frontmatter:** `name`, `description` (with any `<example>` blocks embedded), `model`, and optionally `color` and `tools`/`allowed-tools`.
- **Body heading:** `# <Agent Name>` (title-cased version of the name).
- **Role statement:** One sentence: "You are a [functional role] that [purpose]."
- **Workflow section:** Numbered steps based on the user's workflow description. Each step gets a heading and a 1-2 sentence placeholder — enough to show structure.
- **Hard Rules section:** Standard constraints appropriate to the agent's write-capability and scope.

Example generated output:

    ---
    name: pr-reviewer
    description: >
      Review pull request diffs for correctness, style, and test coverage.
      Use when a user asks to review a PR or check code quality before merging.
    model: sonnet
    tools:
      - Read
      - Glob
    ---

    # PR Reviewer

    You are a code review agent that inspects pull request diffs and reports findings
    grouped by severity.

    ## Workflow

    ### 1. Fetch PR diff
    [step placeholder]

    ## Hard Rules

    - Never approve or merge PRs; analysis only.

Before presenting, run these validation checks against the generated content:
- Name length ≤ 64 characters (count characters in the `name` field)
- Description length ≤ 1024 characters (count characters in the full `description` value, excluding YAML key and quotes)
- No XML tags (`<`, `>`) appear in the description field (XML tags are not allowed in description)
- Only documented frontmatter keys are present: `name`, `description`, `model`, `color`, `tools`, `allowed-tools`

If any check fails, report the specific violation and correct it before presenting.

Present the full generated content to the user for review. Ask: "Does this look correct? (yes/edit/cancel)"
- **yes** — Proceed to writing the file.
- **edit** — Ask what to change, regenerate, and preview again.
- **cancel** — Stop without writing anything.

### 5. Write file

Write the agent file:

1. Check whether `.claude/agents/` exists. If not, create it by writing the file — the Write tool will create intermediate directories.
2. Write `.claude/agents/<agent-name>.md` with the approved content.

If the write fails, report the error clearly. Do not proceed to Step 6 until the file is written successfully.

### 6. Register in repository docs

Use only the stable surviving headings. Do not invent new top-level sections.

- Update `README.md` under `## Command Families` if the agent is user-invocable.
- Update `CLAUDE.md` under `## Commands`.
- Update `docs/skills/README.md` under `## Quick Reference` and `## By Function` when applicable.

Use Edit to make targeted additions. Never rewrite unrelated sections or depend on prose outside those headings. If a heading does not exist in the target file, skip that registration step and note it in your report.

### 7. Suggest commit and next steps

Tell the user:
```
Agent scaffolded. Suggested commit:
  feat(<agent-name>): add <agent-name> agent
```

Then end your response with this menu (substitute `<agent-path>` with the actual path):

---
**What's next?**
1. Review the new agent → `/review-agent <agent-path>`
2. Scaffold another agent
3. Done

_Type a number to continue._

---

When the user responds: **1** → invoke `/review-agent` with the new agent's path. **2** → ask for the agent name, then invoke `/scaffold-agent`. **3** → acknowledge and stop.

## Hard Rules

- **Never overwrite existing agents.** If `.claude/agents/<agent-name>.md` already exists, refuse and ask for a different name.
- **Preview before writing.** Show the full generated .md content before creating any file.
- **Frontmatter must be valid.** Only use documented fields: `name`, `description`, `model`, `color`, `tools`, `allowed-tools`. Do not invent new frontmatter keys.
- **Name constraints are enforced before generation.** kebab-case, max 64 chars, no "anthropic"/"claude" substring.
- **Example blocks belong inside the description field, not in the body.**
- **Documentation edits are additive.** Append concise entries under stable headings. Never modify or remove unrelated entries.
- **Least-privilege tools.** Only include tools the agent's workflow actually uses. Keep the list minimal.
- **Stop conditions apply.** Stop immediately if: name is invalid and user does not supply a corrected one, user chooses cancel, or file write fails.
