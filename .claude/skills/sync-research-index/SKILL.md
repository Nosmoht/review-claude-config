---
name: sync-research-index
description: >
  Scan the research/ directory and compare with CLAUDE.md Research References
  section. Reports drift — unlinked files, broken links, description mismatches.
  Can update CLAUDE.md to sync. Use after adding or removing research files.
argument-hint: "[folder]"
allowed-tools: Read, Edit, Glob
disable-model-invocation: true
---

# Research Index

You are an index maintainer ensuring the CLAUDE.md Research References section stays in sync with research files on disk. Your job is to detect drift and offer to fix it.

## Workflow

### 1. Discover research files

If `$ARGUMENTS` contains a folder path, use it as the target. Otherwise, use the current working directory.

Verify `<target>` exists using Glob on `<target>/CLAUDE.md`. If it does not exist, tell the user: "Target folder not found or has no CLAUDE.md." Stop.

Glob `<target>/research/**/*.md` to find all research files. If the `research/` directory does not exist or contains no `.md` files, tell the user: "No research files found in `<target>/research/`." Stop.

For each research file, read the first 5 lines to extract the title (first `# ` heading).

### 2. Parse CLAUDE.md references

Read `<target>/CLAUDE.md`. Locate the `## Research References` section. If the section does not exist, tell the user: "No Research References section found in CLAUDE.md." Stop.

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
- **STALE** — File exists and is referenced, but the CLAUDE.md title does not match the file's heading.

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

Ask: "Update CLAUDE.md Research References section to fix drift? (yes/no)"

If no, stop.

If yes:
- **For UNLINKED files:** Read each file to extract its title and a one-line summary. Add an entry to the Research References section following the existing format: `- [Title](relative/path) — Description`
- **For BROKEN links:** Remove the entry from the Research References section.
- **For STALE files:** Update the CLAUDE.md entry title to match the file's current `# ` heading.

Use Edit to make targeted changes to the `## Research References` section only. Never modify other sections of CLAUDE.md.

After editing, re-run the comparison from Step 3 against the updated CLAUDE.md. If drift remains, report the remaining issues and offer to fix. Otherwise, confirm: "All drift resolved."

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
