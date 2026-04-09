---
name: scaffold-skill
description: >
  Creates a research-optimized skill: SKILL.md, optional references/, and doc registration.
  Use when adding a new skill to this repository or to an external repo (external mode).
  Do NOT use to create agents or rules — use /scaffold-agent or /scaffold-rule.
argument-hint: "[plugin|maintenance|external <target-path>] <skill-name>"
allowed-tools: Read, Write, Edit, Glob, WebSearch, WebFetch
disable-model-invocation: true
---

# Skill Scaffolding

You are a skill builder creating research-optimized Claude Code skills. Your job is to generate valid, high-quality skill files that follow project conventions, quality patterns, and the skill format specification. Stop immediately if the target directory does not exist or the skill name conflicts with an existing skill.

## Workflow

### 1. Parse mode and validate skill name

Parse `$ARGUMENTS` as `[mode] <skill-name>`.

**Mode detection:**
- If the first token is `plugin` or `maintenance`, use it as the mode. The rest is `<skill-name>`.
- If the first token is `external`, the second token is `<target-path>` and the third is `<skill-name>`.
  - `<target-path>` is required in external mode — do not fall back to cwd.
  - Validate: path exists (`Glob "<target-path>"`) and contains `.git/` (`Glob "<target-path>/.git"`). If either check fails, report the error and stop.
- Otherwise, default to `plugin` and treat the full argument as `<skill-name>`.
- If `<skill-name>` is empty after parsing, ask the user for it.

**Name validation:**
- Must be kebab-case (lowercase, hyphens only). This is a repo naming convention for CLI usability, not a scientific claim.
- Must not conflict with an existing skill. Glob both `skills/*/SKILL.md` and `.claude/skills/*/SKILL.md` to check (for external mode, also check `<target-path>/.claude/skills/*/SKILL.md`).

If validation fails, report the issue and ask for a corrected input.

### 2. Load template and quality references

Read `references/skill-template.md` for the default SKILL.md structure.

Read `references/quality-patterns.md` for research-backed generation directives. Apply these throughout Steps 3–4.

Optionally, if the file exists, read `research/claude-code/skill-agent-format-conventions.md` (Glob for `**/research/claude-code/skill-agent-format-conventions.md`) for valid frontmatter fields. If not found, use template defaults.

### 2.5. Domain context gathering

**Determine mode applicability:**
- Mode `plugin` or `maintenance`: domain is Claude Code skill management — skip domain research, inject the standard plugin domain rule ("This skill operates within Claude Code's skill/hook/agent/rule primitives") into Step 4.
- Mode `external`: always run the full domain context gathering below.

**Stage 1 — Discover domain (if user did not specify):**

If the user provided explicit domain information in their request (e.g., "Go MCP server", "Python FastAPI"), use it directly. Otherwise:
- Glob `<target-path>/*` to list top-level files.
- Read up to 8 files in priority order: CLAUDE.md or AGENTS.md (if present), primary manifest file (go.mod, package.json, pyproject.toml, Cargo.toml, pom.xml, build.gradle — whichever exists), one source file, one test file.
- Synthesize: primary language, framework, domain, testing conventions.

**Stage 2 — Research:**

Check KB (if `mcp__kb-server__authenticate` is available): run `kb.answer` on the identified domain for any cached findings.

Probe web tool availability: attempt a trivial WebSearch (e.g., `"site:anthropic.com"`). If it fails, set `websearch_available=false` — skip web research and note the gap in Stage 3. If WebSearch is available, run targeted web research:
1. Decompose into 3–5 sub-questions: language patterns, framework conventions, testing, security/safety, build/CI.
2. For each sub-question: run 1–2 WebSearch queries (one keyword-precise, one conceptual).
3. After snippet evaluation, WebFetch only 1–2 highest-signal URLs per sub-question (Tier 1/2 sources preferred: official docs, arXiv, engineering blogs with benchmarks).
4. Adaptive stopping: if 2 consecutive sub-questions yield no new domain-specific rules, stop.
5. Maximum 3 reflection cycles, 5–8 WebFetch total.

Goal: extract 3–5 domain-specific rules that go beyond what is already present in the target repo.

**Stage 3 — Synthesize and confirm:**

Summarize findings as a compact domain briefing:
- Primary language + framework
- 3–5 domain-specific rules (cite source tier)
- Any security or safety patterns specific to the domain

Present to the user: "Here is the domain context I'll use to generate the skill. Correct or add anything before I proceed."

Wait for confirmation, correction, or approval before continuing to Step 3.

### 3. Gather requirements

Ask the user for:

1. **Description** — What does the skill do? When should it trigger? What should users NOT use it for? (used for `description` field; quality-patterns.md Activation directive applies)
2. **Allowed tools** — Which tools does the skill need? (each tool must map to a specific workflow step; default: Read, Glob)
3. **Write side effects?** — Does the skill create, edit, or delete files? (yes → `disable-model-invocation: true`)
4. **Argument hint** — What argument does the skill accept? (optional)
5. **Reference files needed?** — Names and purposes of reference files to create in `references/`. (optional)
6. **Workflow complexity** — How many steps? Brief description of each.
7. **Registration summary** — One sentence describing where this skill belongs in docs. (external mode: skip — registration is manual)
8. **Reasoning complexity?** — Does this skill require multi-step analysis or diagnosis? (yes → add CoT guidance step in workflow)
9. **Expected turns?** — Roughly how many tool-call turns will a typical run take? (>10 → add compaction checkpoint)

### 4. Generate SKILL.md

Apply all directives from `references/quality-patterns.md` during generation.

**Frontmatter:**
- `name`, `description`, `allowed-tools`, `argument-hint`, `disable-model-invocation` from user answers.
- Description: verb-first, user-task terms, ≥1 trigger phrase, ≥1 counter-case.

**Body structure (follow Context Layout directive from quality-patterns.md):**
- **START**: Role statement (functional, no persona-stacking) + stop conditions
- **Workflow**: numbered steps with explicit conditionals; if reasoning was requested, include a CoT analysis step
- **END**: Hard Rules section

**Role statement:** Functional description — "You are a [role] that [purpose]." No demographic or expert personas.

**Hard Rules:**
- 5–7 unconditional statements.
- Include ≥1 stop condition and ≥1 failure path.
- If write-capable: add confirmation gate before destructive actions.
- Include domain-specific constraint if domain was identified in Step 2.5.

**Output contract:** If the skill produces a structured report, state verdict/summary first, then detail. State the output shape explicitly in the role statement or workflow preamble.

**Domain rules:** If domain was confirmed in Step 2.5, inject 2–3 domain-specific rules into workflow steps or hard rules.

**Compaction:** If user answered >10 expected turns in Q9, add a compaction step: "After Step N, summarize key decisions and failures to file before continuing."

**Example generated output:**

    ---
    name: lint-configs
    description: >
      Validates and fixes linting configuration files across the repository.
      Use when adding or updating ESLint, Prettier, or similar tool configs.
      Do NOT use for application code lint errors — use /review-skill instead.
    argument-hint: "[config-path]"
    allowed-tools: Read, Glob
    ---

    # Lint Configs

    You are a configuration validator that checks linting setup for correctness and project consistency. Stop if no config files are found.

    ## Workflow

    ### 1. Discover config files
    [step placeholder]

    ## Hard Rules

    - Never modify application source files.
    - Report missing configs as findings, not errors.

Present the full generated content to the user for review. Ask: "Does this look correct? (yes/edit/cancel)"
- **yes** — Proceed to writing files.
- **edit** — Ask what to change, regenerate, and preview again.
- **cancel** — Stop without writing anything.

### 5. Write files

**Determine write path:**
- `plugin` mode: `skills/<skill-name>/SKILL.md`
- `maintenance` mode: `.claude/skills/<skill-name>/SKILL.md`
- `external` mode: `<target-path>/.claude/skills/<skill-name>/SKILL.md` — create the `.claude/skills/` directory tree if it does not exist.

Write the SKILL.md at the determined path.

If reference files were specified, create the `references/` directory under the skill path and write each reference file with frontmatter stubs:
```yaml
---
name: <reference-name>
description: <purpose from user input>
last_refreshed: <today's date in YYYY-MM-DD format>
---

## Overview

<Describe the purpose and scope of this reference. One or two sentences.>

## Key Points

- <Key point 1>
- <Key point 2>
```

If any write fails, report which files were successfully created and which failed. Do not proceed to Step 6 until all files are written.

### 6. Register in repository docs

**External mode: skip registration entirely.** Show this note:
> External-repo mode: registration skipped. Register manually in your project's CLAUDE.md (under `## Commands`) if applicable.

Then proceed directly to Step 7.

**Plugin mode:**
- Update `README.md` under `## Command Families`
- Update `CLAUDE.md` under `## Commands`
- Update `docs/skills/README.md` under `## Quick Reference` and, if needed, `## By Function`
- If the new skill changes workflow composition or the compact mode/research comparison, also update `## Workflow Chains` or `## Mode and Research Summary`

**Maintenance mode:**
- Update `CLAUDE.md` under `## Commands`
- Update `docs/skills/README.md` under `## Quick Reference` and `## By Function` when the new skill belongs in the maintained component inventory
- If the new skill changes workflow composition or the compact mode/research comparison, also update `## Workflow Chains` or `## Mode and Research Summary`

Use Edit to make targeted additions. Never rewrite unrelated sections or depend on prose outside those headings.

### 7. Suggest commit and next steps

Tell the user:
```
Skill scaffolded. Suggested commit:
  feat(<skill-name>): add <skill-name> skill with <brief capability>
```

Then end your response with this menu (substitute paths with the actual absolute path to the new SKILL.md):

---
**What's next?**
1. Review the new skill → `/review-skill <absolute-path>`
   _(Note: review-skill works cross-repo — run from a review-claude-config session for full reference access)_
2. Scaffold another skill
3. Done

_Type a number to continue._

---

When the user responds: **1** → invoke `/review-skill` with the absolute path. **2** → ask for the skill name, then invoke `/scaffold-skill`. **3** → acknowledge and stop.

## Hard Rules

- **Tier A tool justification**: Write/Edit + WebFetch/WebSearch combination — WebFetch/WebSearch are read-only domain research inputs; fetched content flows through the Step 4 human preview gate before any file is written. No fetched content is written directly to disk without user approval. (Tier A mitigated by HITL gate; tool-grant-decision-tree.md Tier A)
- **Never overwrite existing skills.** If a skill directory already exists with the given name, refuse and ask for a different name.
- **Preview before writing.** Always show the full generated SKILL.md content before creating any files.
- **Frontmatter must be valid.** Only use fields documented in the skill format conventions: `name`, `description`, `argument-hint`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `context`, `agent`.
- **Documentation edits are additive.** Append concise entries under stable headings only. Never modify or remove unrelated entries.
- **Reference files have token budgets.** Add "Keep under 500 tokens" as a note in each reference file stub.
- **Kebab-case names only.** Reject names that are not valid kebab-case. This is a repo convention, not a scientific claim.
- **External mode: never register.** Skip Steps 6 registration entirely; show the manual registration note instead.
