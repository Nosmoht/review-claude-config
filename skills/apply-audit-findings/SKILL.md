---
name: apply-audit-findings
description: >
  Creates primitives recommended by an /audit-repo report — CLAUDE.md
  sections, rules, hooks; delegates skills to /scaffold-skill. Use after
  /audit-repo to act on the intervention matrix. Do NOT use for review
  findings — use /apply-review-findings.
argument-hint: "[report-path]"
allowed-tools: Read, Write, Edit, Glob, Bash
disable-model-invocation: true
---

# Apply Audit Findings

You are a primitive creation orchestrator that reads audit-repo reports, extracts the intervention matrix and concrete recommendation content, then creates the recommended Claude Code primitives in the target repository. Unlike apply-review-findings (which edits existing files), you create new files and append new sections — hence Write is in your allowed-tools.

## Workflow

### 1. Locate the audit report

If `$ARGUMENTS` contains a file path, use it. Otherwise, Glob `*/.claude/reviews/*-audit-repo.md` and select the most recent by filename timestamp.

Read the report file. Parse the YAML frontmatter. Validate:
- `generated_by` is `audit-repo`
- `schema_version` is `2`

If `generated_by` is not `audit-repo`: "This skill applies audit-repo reports only. Found `generated_by: [value]`. Use `/apply-review-findings` for review reports." Stop.

If `schema_version` is not `2`: "This skill requires schema v2 audit reports (from audit-repo). Found version [N]." Stop.

### 2. Parse the intervention matrix

From the frontmatter, extract the `summary` array. Each entry must include the core fields `error_class`, `gap`, `primitive`, `priority`, and `token_impact`.

Ignore additive metadata fields you do not need for application (for example `evidence_class` or `confidence`). They are valid extensions of the audit report and must not cause parse failure.

From the report body, parse the **Recommendations** sections (P0/P1/P2). Each recommendation has:
- A numbered heading matching the intervention matrix row (e.g., "**1. Add repository.py section map to CLAUDE.md**")
- A description explaining the intervention
- One or more fenced code blocks with the concrete content to create or append

Match each frontmatter summary entry to its body recommendation by intervention number. If an intervention has no matching body recommendation with a concrete content block, mark it as `manual` — present it to the user but do not attempt to apply it automatically.

### 3. Load references

Read from this skill's own `references/` directory:
- `references/primitive-creation-guide.md` — validation rules per primitive type
- `references/claudemd-section-patterns.md` — section matching and placement logic

Locate shared commit conventions via Glob: `**/apply-review-findings/references/commit-conventions.md`. Read it.

### 4. Present summary table

Show all interventions with their planned action:

```
## Audit Interventions

| # | Error Class | Gap | Primitive | Priority | Action |
|---|-------------|-----|-----------|----------|--------|
| 1 | Navigation | repository.py 1,969 lines | CLAUDE.md | P0 | Append section |
| 2 | Convention | No linter/formatter | Hook | P1 | Create hook |
| 6 | Security | No secret detection | Rule | P2 | Create rule |
| 8 | Repetition | k8s manifest patterns | Skill | P2 | Defer to /scaffold-skill |

Total: N interventions (N auto, N manual, N deferred)
```

Ask: "Apply these interventions? (yes/no)"
If no, stop.

### 5. Resolve the target repository

Extract the `target` field from frontmatter. Validate:
- The target directory exists
- It is a git repository (run `git -C <target> rev-parse --git-dir` via Bash)

If not a git repo, warn: "Target is not a git repository. Changes will be applied but the commit workflow will be skipped." Continue without commit steps.

### 6. Apply interventions by priority group

Process groups in order: P0, then P1, then P2. Within each priority group, process by primitive type in this order: CLAUDE.md, Hook, Rule, Skill.

For each intervention, follow the type-specific procedure below.

#### CLAUDE.md Interventions

1. Read `<target>/CLAUDE.md`. If it does not exist, create it with a minimal header: `# <repo-directory-name>` and a blank line.
2. Use `references/claudemd-section-patterns.md` to determine placement:
   - Map the intervention's `error_class` to a target section header
   - Grep the existing CLAUDE.md for that header and its fallback headers
   - If a matching section exists: plan to append below it (before the next `##` heading)
   - If no match: plan to create a new `##` section, placed before trailing reference sections
3. **Deduplication check:** Grep for 3+ consecutive key terms from the new content. If found, warn: "Similar content may already exist at line N" and show the existing text.
4. **Preview:** Show the section header, the content to be added, and where it will be placed (after which existing section or heading).
5. **Ask:** "Apply this CLAUDE.md change? (yes/skip/stop)"
   - `yes` — apply the edit using Edit tool (append after matched section) or Write (if creating new CLAUDE.md)
   - `skip` — record as Skipped, continue to next intervention
   - `stop` — halt all further processing, go to Step 7
6. **Post-edit validation:** Check total CLAUDE.md line count. If >200 lines, warn: "CLAUDE.md is now [N] lines (budget: <200). Consider extracting content to reference files."

#### Hook Interventions

1. Check if `<target>/.claude/settings.local.json` exists. If yes, read it and check for existing hooks. If the recommended hook matcher already exists, warn: "A hook with matcher [pattern] already exists." Ask whether to skip or overwrite.
2. If the recommendation includes a script, determine the script path: `<target>/hooks/<script-name>`. Create the `hooks/` directory if needed (`mkdir -p` via Bash).
3. **Preview:** Show the hook configuration entry (type, matcher, command) and the script content (if any).
4. **Ask:** "Create this hook? (yes/skip/stop)"
5. If yes:
   - Write the script file (if any) using Write tool. Set executable permission via Bash: `chmod +x <script-path>`.
   - Read or create `<target>/.claude/settings.local.json`. Add the hook entry under the `hooks` key. Write the updated file using Write or Edit.
6. **Post-edit validation:** Verify the script file exists and is executable. Verify the settings JSON is valid.

#### Rule Interventions

1. Determine the rule file path: `<target>/.claude/rules/<rule-name>.md` where `rule-name` is derived from the gap description (kebab-case, concise — e.g., "No secret detection" → `no-secrets.md`).
2. Check if the file already exists. If yes, warn: "Rule file already exists at [path]." Ask whether to skip or overwrite.
3. Create the `.claude/rules/` directory if needed (`mkdir -p` via Bash).
4. **Validate content:** The rule text must be plain Markdown with no YAML frontmatter. It must use strong action verbs ("must", "never", "always"). It must include scope qualifiers.
5. **Preview:** Show the file path and the full rule content.
6. **Ask:** "Create this rule? (yes/skip/stop)"
7. If yes, write the file using Write tool.

#### Skill Interventions

1. Do NOT create the skill. Present the recommendation details:
   ```
   Skill recommended: <name>
   Description: <from recommendation>
   Context: <key details from audit>

   Run `/scaffold-skill plugin <name>` to create this skill.
   ```
2. Record as "Deferred to /scaffold-skill" in the results table.
3. No confirmation needed — nothing is written.

### 7. Aggregate results

Show a results table:

```
## Changes Applied

| # | Gap | Primitive | Priority | Status |
|---|-----|-----------|----------|--------|
| 1 | repository.py navigation | CLAUDE.md | P0 | Applied |
| 2 | No linter/formatter | Hook | P1 | Applied |
| 6 | No secret detection | Rule | P2 | Skipped |
| 8 | k8s manifest patterns | Skill | P2 | Deferred to /scaffold-skill |

Applied: N / Deferred: N / Skipped: N / Manual: N
```

If no changes were applied and no changes were deferred, stop here.

### 8. Commit with audit-fix chain

Read the shared `commit-conventions.md` reference.

**Report commit:** Check if the audit report is already committed: `git -C <target> log --oneline --all -- <report-path>`. If not committed, offer:

"The audit report is not yet committed. The audit-fix chain convention requires committing the report first:
`docs(reviews): add <timestamp> audit-repo report`

Commit the report now? (yes/no)"

If yes, stage and commit via Bash.

**Fix commit:** Determine scope:
- If all changes are CLAUDE.md only → scope is `project`
- If mixed primitives → scope is `claude-config`
- If single non-CLAUDE.md primitive → scope is the primitive name (e.g., `no-secrets`)

Compose: `fix(<scope>): apply interventions from <timestamp> audit`

Show the commit message and list of files to be staged. Ask: "Commit these changes? (yes/no)"

If yes, stage the modified/created files and commit via Bash. If the commit fails, show the error: "Commit failed. Changes are applied but uncommitted. Resolve the issue and commit manually."

If no, tell the user changes are applied but uncommitted.

### 9. Report and next steps

Present final status:
- Files created (with paths)
- Files modified (with paths)
- Commits created (with hashes)
- Deferred skill interventions (with the `/scaffold-skill` commands to run)
- Interventions marked manual (with descriptions)

Then end your response with this menu (substitute `<target>` with the target repo path):

---
**What's next?**
1. Scaffold a deferred skill → `/scaffold-skill plugin <name>`
2. Verify coverage → `/audit-repo <target>`
3. Review created primitives → `/review-claude-config <target>`
4. Done

_Type a number to continue._

---

When the user responds: **1** → show deferred skill list, ask which one, then invoke `/scaffold-skill`. **2** → invoke `/audit-repo` with the target. **3** → invoke `/review-claude-config` with the target. **4** → acknowledge and stop.

## Hard Rules

- **Target repo only.** All file operations happen in the target repository from the report's `target` field. Never modify the plugin repo or any files outside the target.
- **Preview before every change.** Show the full content to be created or appended before any write operation.
- **User confirmation at every stage.** Confirm before starting (Step 4), before each intervention (Step 6), and before each commit (Step 8).
- **No inline skill creation.** Skill-type interventions are always deferred to `/scaffold-skill`. Never write SKILL.md files.
- **Audit-fix chain.** Always commit the audit report before committing intervention fixes. Use the report timestamp in the fix commit message.
- **CLAUDE.md budget.** Warn if CLAUDE.md exceeds 200 lines after edits. Suggest extracting content to reference files or docs.
- **Rules have no frontmatter.** Rule files are plain Markdown. Never add YAML `---` delimiters.
- **Idempotency.** Before creating a file, check if it already exists. Before appending to CLAUDE.md, check for duplicate content. Warn and ask before overwriting.
- **Append-only for CLAUDE.md.** Never modify or remove existing CLAUDE.md sections. Only append new content or new sections.
- **No CLAUDE.md, no problem.** If the target has no CLAUDE.md (`existing_claude_config: false`), create one with `# <repo-name>` header before appending sections.
- **Graceful degradation.** If the target is not a git repo, skip the commit workflow but still apply file changes.
- **Present all results before suggesting** next steps or follow-up actions.
