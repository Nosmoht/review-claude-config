---
name: validate-primitive-dependencies
description: >
  Maps cross-primitive references and flags integrity problems: broken refs,
  orphaned files, cycles. Use before committing a skill, after renaming
  primitives, or as a pre-release gate. Do NOT use for quality review — use
  /review-claude-config.
argument-hint: "[folder]"
allowed-tools: Agent, Read, Glob, Grep, Write
disable-model-invocation: true
---

# Validate Primitive Dependencies

You are a dependency integrity checker. Your job is to map every cross-primitive
reference in the target repository and surface integrity problems before they
reach production. This skill is read-only on analyzed files; the only file it
writes is the health report.

## Argument Handling

- `$ARGUMENTS` is the target folder path. If empty, use the current working
  directory.
- Validate that the folder exists. If it does not exist or contains no files,
  report that and stop.

## Phase 1 — Setup

### Step 1: Load reference patterns

Read `references/reference-patterns.md` from this skill's own `references/`
directory. This file provides the regex patterns and known non-dependency
indicators used in Phase 2.

### Step 2: Discover all primitives

Build a primitive inventory — `{type, path, name}` — by globbing:

- `<folder>/skills/*/SKILL.md`
- `<folder>/.claude/skills/*/SKILL.md`
- `<folder>/.claude/agents/*.md`
- `<folder>/**/.claude/agents/*.md` (exclude node_modules, .git)
- `<folder>/.claude/rules/*.md`
- `<folder>/**/.claude/rules/*.md` (exclude node_modules, .git)

Also check for hook configuration:

- `<folder>/hooks/hooks.json`
- `<folder>/.claude/hooks/hooks.json`
- `<folder>/.claude/settings.json` (hooks may live here)

Also check for MCP and settings:

- `<folder>/.mcp.json` (MCP server declarations)
- `<folder>/.claude/settings.json` (project settings — permissions, MCP governance)

If no primitives are found, report that and stop.

## Phase 2 — Dependency Extraction (subagent)

Launch a **Dependency Scanner Agent** with allowed-tools: Read, Glob, Grep.

```
You are scanning Claude Code primitives to extract dependency references.
Return a structured dependency map only — no recommendations or interpretations.

SCAN LIMITS:
- Read at most 200 lines per file
- Cap file listings at 500 entries

ERROR HANDLING:
- If a file cannot be read, report "ERROR: [path] — [reason]" and continue.
- Produce output for every category even if empty.

## Reference Patterns
[Insert reference-patterns.md content here]

## Task A: Scan each SKILL.md

For each SKILL.md in the inventory:
1. Grep for Read patterns targeting references/ files:
   pattern: Read.*references/[^\s"']+
   → each match is a forward reference of type "reference-file"

2. Grep for Read patterns targeting sibling skill paths:
   pattern: Read.*skills/[^\s"']+\.md
   → each match is a forward reference of type "sibling-skill"

3. Grep for slash command invocations:
   pattern: `/[a-z][a-z0-9-]+`
   → each match is a forward reference of type "slash-command"
   → resolve: the skill name is the text after /
   → ignore inline code examples (surrounded by backtick pairs on same line)

4. Grep for Agent delegation patterns:
   pattern: Launch.*Agent|Agent.*prompt|Launch a \*\*
   → each match is a forward reference of type "subagent-delegation"
   → note: subagent tool grants do not inherit parent — record for context only

## Task D: Scan each agent .md file

For each agent .md file in the inventory:
1. Read the file content.
2. Grep for slash command invocations:
   pattern: `/[a-z][a-z0-9-]+`
   → each match is a forward reference of type "slash-command"
   → ignore inline code examples (surrounded by backtick pairs on same line)

3. Grep for reference file Read patterns:
   pattern: Read.*references/[^\s"']+
   → each match is a forward reference of type "reference-file"

4. Grep for WebFetch and WebSearch calls that reference local paths (rare but possible):
   pattern: Read.*\.md
   → if the path resolves under the repo, record as "sibling-read"

## Task B: Scan hooks configuration

For each hooks config file found (hooks.json, settings.json with hooks key):
1. Read the file.
2. Extract every "command" field value that contains a file path (e.g., "python3 ./hooks/foo.py").
3. Record each as a forward reference of type "hook-script" from the hooks file to the script path.

## Task C: Scan CLAUDE.md Research References

Read <folder>/CLAUDE.md.
Extract the ## Research References section.
For each line matching: `[^\]]+\]\(([^)]+\.md)\)` — capture the path.
Record each as a forward reference of type "research-ref" from CLAUDE.md to the path.

## Task E: Scan MCP cross-references

If <folder>/.mcp.json exists:
1. Parse it and extract all server name keys.
2. For each agent in the inventory that has `mcpServers:` in its frontmatter, extract the server name list.
3. Record a forward reference of type "mcp-ref" from each agent to each declared server name.
4. Cross-check: every agent `mcpServers` entry should resolve to a key in `.mcp.json`. Record MISSING if not found.
5. Reverse check: every `.mcp.json` server should be referenced by at least one agent or skill. Record ORPHAN if unreferenced (Low severity — server may be used interactively).

If <folder>/.claude/settings.json exists:
6. Check if `permissions.deny` key exists. Record MISSING-DENY if absent (High severity).

## Output format

Return one row per reference:
| source_path | ref_type | target_path |
|-------------|----------|-------------|

Use NONE for target_path when a slash-command cannot be resolved to a file path
(e.g., `/review-skill` → look for `skills/review-skill/SKILL.md` or
`.claude/skills/review-skill/SKILL.md`; if ambiguous, record the best guess).

COMPLETION: Output the table when all tasks are done.
```

If the subagent fails entirely, report the error and stop. If partial results
are returned, continue with what is available and note the gap.

## Phase 3 — Validation

### Step 1: Forward reference check

For each row in the dependency map, resolve paths as follows. All path resolution is
anchored at the **target folder** root (the `$ARGUMENTS` path, not the skill's own
directory). Reference-file paths are relative to their **source file's parent directory**
— this applies to both SKILL.md files and agent .md files:
- `Read references/foo.md` in `skills/bar/SKILL.md` → `<target>/skills/bar/references/foo.md`
- `Read references/foo.md` in `.claude/agents/baz.md` → `<target>/.claude/agents/references/foo.md`

- **reference-file**: Resolve relative to the source SKILL.md's parent directory.
  Glob for the resolved path. If not found, status = MISSING.
- **sibling-skill**: Resolve relative to the target folder root.
  Glob for the path. If not found, status = MISSING.
- **slash-command**: Derive expected skill path (`<target>/skills/<name>/SKILL.md` and
  `<target>/.claude/skills/<name>/SKILL.md`). Glob both. If neither exists, status = MISSING.
- **hook-script**: Resolve relative to the target folder root.
  Glob for the script path. If not found, status = MISSING.
- **research-ref**: Resolve relative to the target folder root.
  Glob for the path. If not found, status = MISSING.
- **subagent-delegation**: Record as informational (subagent permissions do not
  inherit — no file existence to check).

Collect results as: `{source, ref_type, target, status: MISSING | OK}`.

### Step 2: Orphan check

Glob all reference files:

- `<folder>/skills/*/references/*.md`
- `<folder>/.claude/skills/*/references/*.md`

For each reference file: check whether it appears as a target in the dependency
map. If it does not appear, classify as ORPHANED.

Research files in `<folder>/research/` are checked separately: for each
`research/**/*.md`, verify it appears in the CLAUDE.md Research References
section (from Phase 2 Task C). If not, classify as ORPHANED.

### Step 3: Cycle detection

Build an adjacency map from slash-command references only:

```
skill A → skill B  (A's SKILL.md contains /skill-b invocation)
```

Perform a transitive DFS (depth-first search) to detect cycles of any length.
Use only the current `path` for cycle detection — no separate `visited` set,
since a visited set without backtracking would suppress valid cycle branches:

```
cycles = []

For each skill node A (as starting point):
  DFS(node, path):
    for each neighbor B of node (from adjacency map):
      if B in path → cycle found: cycles.append(path + [B]); continue
      else: DFS(B, path + [B])

  DFS(A, [A])
```

Record each cycle as the full chain: `A → B → C → A`. If multiple cycles share
edges, record each independently. Depth-2 cycles (A→B→A) are a special case of this.
To avoid redundant reporting, skip starting nodes that already appear mid-chain in a
previously recorded cycle.

### Step 4: Registration check

Read the following registration documents (skip gracefully if any are missing,
noting the skip):

1. `<folder>/CLAUDE.md` — look for the `## Commands` section; extract skill
   names mentioned under slash-command entries (pattern: `/skill-name`).
2. `<folder>/README.md` — look for Command Families or similar section; extract
   skill names.
3. `<folder>/docs/skills/README.md` — look for Quick Reference section; extract
   skill names.

For each skill in the primitive inventory:

- Check presence in each of the three registration documents.
- Flag **UNREGISTERED** if missing from CLAUDE.md (primary).
- Flag **PARTIAL** if present in CLAUDE.md but missing from README.md or
  docs/skills/README.md.
- Flag **OK** if present in all applicable documents.

Also check for **ghost registrations**: slash-command entries in CLAUDE.md,
README.md, or docs/skills/README.md that do not correspond to an existing
`SKILL.md`. Flag each as GHOST.

## Phase 4 — Report

Assemble the report in this structure:

```markdown
# Dependency Health Report

**Target:** <folder>
**Date:** YYYY-MM-DD
**Primitives scanned:** N skills, N agents, N rules, hooks: yes/no

---

## Forward References

| Source | Ref Type | Target | Status |
|--------|----------|--------|--------|
| skills/foo/SKILL.md | slash-command | skills/bar/SKILL.md | OK |
| skills/foo/SKILL.md | reference-file | skills/foo/references/missing.md | MISSING |

Forward refs: N pass, N fail

---

## Orphaned References

| File | Type | Note |
|------|------|------|
| skills/foo/references/unused.md | reference-file | Not read by any skill |
| research/some/file.md | research-file | Not in CLAUDE.md Research References |

Orphans: N found

---

## Circular Dependencies

[cycle chains, one per line, e.g.: skills/a/SKILL.md → skills/b/SKILL.md → skills/a/SKILL.md]

[or: None detected]

Cycles: N found

---

## Registration Consistency

| Skill | CLAUDE.md | README.md | docs/skills | Status |
|-------|-----------|-----------|-------------|--------|
| review-skill | yes | yes | yes | OK |
| new-skill | no | no | no | UNREGISTERED |

Ghost registrations (in docs, directory missing):
- /ghost-skill (in CLAUDE.md)

Registration: N consistent, N issues

---

## Summary

Forward refs: N pass, N fail
Orphans: N found
Cycles: N found
Registration: N consistent, N issues

**Overall: [HEALTHY] / [ISSUES FOUND — N items need attention]**
```

Present the full report.

Confirm via AskUserQuestion (header: "Save report"):
- Option 1 label: "Save report" (Recommended) — description: `"Write to .claude/reviews/YYYY-MM-DDTHHMMSS-validate-deps.md"`
- Option 2 label: "Skip" — description: `"Display the path that would have been used"`

On "Save report": write the report file. On "Skip": display the path that would have been used.

---

If any dependencies are broken, present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Fix broken references" (Recommended) — description: `"Edit files manually to fix broken dependencies, then re-run /validate-primitive-dependencies"`
- Option 2 label: "Check repo health" — description: `"Run /check-repo-health for a broader health overview"`
- Option 3 label: "Done" — description: `"End the workflow"`

On "Fix broken references": acknowledge and remind them to re-run this skill after fixing. On "Check repo health": invoke `/check-repo-health`. On "Done": acknowledge and stop.

If the overall verdict is HEALTHY, skip the menu — just present the report.

## Hard Rules

- **Read-only on analyzed files.** Never modify any primitive. The only file
  this skill writes is the health report.
- **Graceful degradation.** If hooks.json is missing, skip hook checks and note
  the skip. If registration docs are missing, skip those checks and note the skip.
  If CLAUDE.md has no Research References section, skip that orphan check.
- **Explicit stop conditions.** Stop if the target folder does not exist. Stop
  if the Phase 2 subagent fails entirely (report the error).
- **Functional role, not persona.** The subagent receives a task description,
  not a demographic or broad expert role.
- **Least-privilege subagent.** The scanner agent receives only Read, Glob,
  Grep — no Write, no Edit, no Bash.
- **Non-dependency patterns.** Inline code examples (pattern surrounded by
  backtick pairs on the same line) are not dependency references. The
  reference-patterns.md file documents additional known non-dependency patterns.
- **Present all findings before asking** about persistence.
- **Subagent permission isolation.** Subagent-delegation references are
  informational only — subagents do not inherit parent tool grants.
