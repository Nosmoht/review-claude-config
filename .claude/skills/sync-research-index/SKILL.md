---
name: sync-research-index
description: >
  Scans research/ and docs/research-references.md for drift — unlinked
  files, broken links, description mismatches. Use after adding or removing
  research files. Do NOT use to check skill quality — use /review-claude-config.
argument-hint: "[folder]"
allowed-tools: Read, Edit, Glob, AskUserQuestion
disable-model-invocation: true
---

# Research Index

You are an index maintainer ensuring `docs/research-references.md` stays in sync with research files on disk. Your job is to detect drift and offer to fix it.

## Workflow

### 1. Discover research files

If `$ARGUMENTS` contains a non-empty folder path, use it as the target. If `$ARGUMENTS` is empty, absent, or whitespace-only, use the current working directory.

Verify `<target>` exists by reading `<target>/docs/research-references.md`. If it does not exist or cannot be read, tell the user: "Target folder has no research index at `<target>/docs/research-references.md`." Stop.

Glob `<target>/research/**/*.md` to find all research files. If the `research/` directory does not exist or contains no `.md` files, tell the user: "No research files found in `<target>/research/`. Nothing to sync." Stop.

For each research file, read the first 5 lines to extract the title (first `# ` heading).

### 2. Parse research-references.md

Read `<target>/docs/research-references.md`. Parse each Markdown link entry. Expected format:
```
- [Title](relative/path) — Description
```

Paths inside this file are **relative to `docs/`** (the file's parent directory). For example, `(../research/foo.md)` resolves to `<target>/research/foo.md`. Convert each parsed link to a repo-root-relative path before comparing with the Glob results from Step 1.

Extract for each entry: title, repo-root-relative path, description.

### 3. Compare and classify

Build two sets:
- **On disk:** All research file paths found by Glob, with their extracted titles (already repo-root-relative).
- **In index:** All paths referenced in `docs/research-references.md`, normalised to repo-root-relative.

Classify each item:
- **OK** — File exists on disk AND is referenced in the index with a matching title.
- **UNLINKED** — File exists on disk but is NOT referenced in `docs/research-references.md`.
- **BROKEN** — Referenced in `docs/research-references.md` but file does NOT exist on disk.
- **STALE** — File exists and is referenced, but the index link text (inside `[...]`) does not match the file's first `# ` heading.

### 4. Present drift report

```
## Research Index Report

| Status | Path | Detail |
|--------|------|--------|
| OK | research/prompt-engineering/... | Linked |
| UNLINKED | research/new-topic/file.md | Not in docs/research-references.md |
| BROKEN | research/removed/old.md | File missing |

**Summary:** X files on disk, Y linked in index, Z unlinked, W broken links.
```

If all files are OK (no UNLINKED, BROKEN, or STALE entries), tell the user: "Research index is in sync. No changes needed." Stop.

### 5. Offer to sync

Confirm via AskUserQuestion (header: "Sync research index"):
- Option 1 label: "Update index to fix drift" (Recommended) — description: `"Add unlinked files, remove broken links, update stale titles"`
- Option 2 label: "Cancel" — description: `"Stop without making changes"`

On "Cancel": stop. On "Update index to fix drift":
- **For UNLINKED files:** Read each file to extract its title and a one-line summary. Add an entry to `docs/research-references.md` following the existing format: `- [Title](relative/path) — Description`. The relative path must be expressed relative to `docs/` (e.g., `../research/topic/file.md`). Place each new entry in the topical cluster section that best fits its subject; if uncertain, append to the closing `## Supporting Research` section.
- **For BROKEN links:** Remove the entry from `docs/research-references.md`.
- **For STALE entries:** Update the title in the index entry to match the file's current `# ` heading.

Use Edit to make targeted changes to `docs/research-references.md` only. Never modify CLAUDE.md or research files. Apply changes one entry at a time. If an Edit fails (e.g., non-unique match), stop applying further edits and report to the user: "Edit failed for [entry]. Applied N of M changes successfully. Remaining changes: [list]. Review docs/research-references.md before continuing." Ask the user via AskUserQuestion whether to retry the remaining changes or stop.

After editing, re-run the comparison from Step 3 against the updated file (at most once). If drift remains after one fix cycle, report the remaining issues to the user and stop — do not attempt further fixes without user confirmation. Otherwise, confirm: "All drift resolved."

### 6. Suggest commit

Tell the user:
```
Research index synced. Suggested commit:
  docs(research-index): sync entries in docs/research-references.md
```

## Hard Rules

- **Only modify `docs/research-references.md`.** Never edit CLAUDE.md or research files. The CLAUDE.md `## Research References` section now contains a topic-cluster routing table only — it is not the authoritative index.
- **Present the full report before offering to sync.** User sees all drift before deciding.
- **Preserve existing entry format and relative-to-docs/ paths.** New entries match the style of existing entries; paths are written relative to `docs/` (e.g., `../research/...`).
- **Never modify research files.** This skill only reads research files and edits the index.
- **One-line descriptions only.** Generated descriptions for new entries are concise (≤15 words).
