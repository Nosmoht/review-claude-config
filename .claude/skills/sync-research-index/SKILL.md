---
name: sync-research-index
description: >
  Scans research/ and CLAUDE.md Research References for drift — unlinked
  files, broken links, description mismatches. Use after adding or removing
  research files. Do NOT use to check skill quality — use /review-claude-config.
argument-hint: "[folder]"
allowed-tools: Read, Edit, Glob, AskUserQuestion
disable-model-invocation: true
---

# Research Index

You are an index maintainer ensuring the CLAUDE.md Research References section stays in sync with research files on disk. Your job is to detect drift and offer to fix it.

## Workflow

### 1. Discover research files

If `$ARGUMENTS` contains a non-empty folder path, use it as the target. If `$ARGUMENTS` is empty, absent, or whitespace-only, use the current working directory.

Verify `<target>` exists by reading `<target>/CLAUDE.md`. If it does not exist or cannot be read, tell the user: "Target folder not found or has no CLAUDE.md at `<target>/CLAUDE.md`." Stop.

Glob `<target>/research/**/*.md` to find all research files. If the `research/` directory does not exist or contains no `.md` files, tell the user: "No research files found in `<target>/research/`. Nothing to sync." Stop.

For each research file, read the first 5 lines to extract the title (first `# ` heading).

### 2. Parse CLAUDE.md references

Read `<target>/CLAUDE.md`. Locate the `## Research References` section. If the section does not exist, tell the user: "No `## Research References` section found in CLAUDE.md. Cannot sync without this section." Stop.

Parse each entry in the section. Expected format:
```
- [Title](relative/path) — Description
```

Extract for each entry: title, relative path, description.

### 3. Compare and classify

Build two sets:
- **On disk:** All research file paths found by Glob, with their extracted titles.
- **In CLAUDE.md:** All paths referenced in the Research References section, with their titles.

Classify each item:
- **OK** — File exists on disk AND is referenced in CLAUDE.md with a matching title.
- **UNLINKED** — File exists on disk but is NOT referenced in CLAUDE.md.
- **BROKEN** — Referenced in CLAUDE.md but file does NOT exist on disk.
- **STALE** — File exists and is referenced, but the CLAUDE.md link text (inside `[...]`) does not match the file's first `# ` heading.

### 4. Present drift report

```
## Research Index Report

| Status | Path | Detail |
|--------|------|--------|
| OK | research/prompt-engineering/... | Linked |
| UNLINKED | research/new-topic/file.md | Not in CLAUDE.md |
| BROKEN | research/removed/old.md | File missing |

**Summary:** X files on disk, Y linked in CLAUDE.md, Z unlinked, W broken links.
```

If all files are OK (no UNLINKED, BROKEN, or STALE entries), tell the user: "Research index is in sync. No changes needed." Stop.

### 5. Offer to sync

Confirm via AskUserQuestion (header: "Sync research index"):
- Option 1 label: "Update CLAUDE.md to fix drift" (Recommended) — description: `"Add unlinked files, remove broken links, update stale titles"`
- Option 2 label: "Cancel" — description: `"Stop without making changes"`

On "Cancel": stop. On "Update CLAUDE.md to fix drift":
- **For UNLINKED files:** Read each file to extract its title and a one-line summary. Add an entry to the Research References section following the existing format: `- [Title](relative/path) — Description`
- **For BROKEN links:** Remove the entry from the Research References section.
- **For STALE entries:** Update the title in the CLAUDE.md entry to match the file's current `# ` heading.

Use Edit to make targeted changes to the `## Research References` section only. Never modify other sections of CLAUDE.md. Apply changes one entry at a time. If an Edit fails (e.g., non-unique match), stop applying further edits and report to the user: "Edit failed for [entry]. Applied N of M changes successfully. Remaining changes: [list]. Review CLAUDE.md before continuing." Ask the user via AskUserQuestion whether to retry the remaining changes or stop.

After editing, re-run the comparison from Step 3 against the updated CLAUDE.md (at most once). If drift remains after one fix cycle, report the remaining issues to the user and stop — do not attempt further fixes without user confirmation. Otherwise, confirm: "All drift resolved."

### 6. Suggest commit

Tell the user:
```
Research index synced. Suggested commit:
  docs(project): sync research references in CLAUDE.md
```

## Hard Rules

- **Only modify the Research References section.** Never edit any other part of CLAUDE.md.
- **Present the full report before offering to sync.** User sees all drift before deciding.
- **Preserve existing entry format.** New entries match the style of existing entries.
- **Never modify research files.** This skill only reads research files and edits CLAUDE.md.
- **One-line descriptions only.** Generated descriptions for new entries are concise (≤15 words).
