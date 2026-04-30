# Sync Research Index

> Scan the research/ directory and compare with `docs/research-references.md`. Reports drift (unlinked files, broken links, description mismatches) and can update `docs/research-references.md` to sync.

**Command:** `/sync-research-index [folder]`
**Location:** `.claude/skills/sync-research-index/SKILL.md`
**Type:** Maintenance (repo-internal)
**Allowed Tools:** Read, Edit, Glob
**Mode Support:** Standalone only (no orchestrated mode)

## Overview

The sync-research-index skill is a maintenance utility that keeps `docs/research-references.md` aligned with actual research files on disk. Over time, research files are added, renamed, or removed, but the index can fall out of date. This skill detects that drift and offers a one-step fix.

The skill operates in three phases: discovery, analysis, and reporting/sync. It first scans the `research/` directory tree for all Markdown files and parses the existing entries in `docs/research-references.md`. It then classifies every entry into one of four statuses: OK, UNLINKED, BROKEN, or STALE. Finally, it presents a drift report table and, if drift is found, offers to update the index automatically.

Because the skill has `disable-model-invocation: true`, it runs without spawning sub-agents. It never modifies research files themselves and only edits `docs/research-references.md`. This makes it safe to run at any time as a quick health check after adding or removing research files.

> Historical note: prior to commit `2ee0ae9` (2026-04-30) the canonical index lived inline in `CLAUDE.md §Research References`. It was extracted to `docs/research-references.md` to keep CLAUDE.md under the 40k-character performance threshold. CLAUDE.md now retains only a topic-cluster routing table.

## Process Steps

### Phase 1 -- Discovery

**Step 1: Discover research files.** The skill resolves the target folder from `$ARGUMENTS` (or defaults to the current working directory). It verifies the target exists by reading `<target>/docs/research-references.md` via Read. If the file is missing, the skill stops with an error message. It then globs `<target>/research/**/*.md` to find all research Markdown files. If none are found, it stops. For each discovered file, the skill reads the first 5 lines to extract the title from the first `# ` heading.

**Step 2: Parse research-references.md.** The skill reads `<target>/docs/research-references.md` and parses each entry in the expected format `- [Title](relative/path) -- Description`. Paths inside the file are written **relative to `docs/`** (e.g., `(../research/foo.md)`); the skill normalises each parsed link to a repo-root-relative path before comparing with the Glob results.

### Phase 2 -- Analysis

**Step 3: Compare and classify.** The skill builds two sets -- files on disk (with extracted titles) and entries in `docs/research-references.md` (with their titles and normalised paths). Each item is classified into one of four statuses:

| Status | Meaning |
|--------|---------|
| **OK** | File exists on disk AND is referenced in the index with a matching title |
| **UNLINKED** | File exists on disk but is NOT referenced in the index |
| **BROKEN** | Referenced in the index but file does NOT exist on disk |
| **STALE** | File exists and is referenced, but the index title does not match the file heading |

### Phase 3 -- Reporting and Sync

**Step 4: Present drift report.** The skill outputs a table with Status, Path, and Detail columns, followed by a summary line showing counts (files on disk, linked in index, unlinked, broken). If all entries are OK, the skill reports that the index is in sync and stops.

**Step 5: Offer to sync.** If drift is detected, the skill asks the user whether to update `docs/research-references.md`. On confirmation:
- **UNLINKED files:** The skill reads each file to extract its title and generates a one-line summary (max 15 words). It adds a new entry following the existing format, with the path expressed relative to `docs/` (e.g., `../research/topic/file.md`). New entries are placed in the topical cluster section that best fits their subject; if uncertain, they are appended to the closing `## Supporting Research` section.
- **BROKEN links:** The skill removes the entry from the index.

The skill uses Edit to make targeted changes to `docs/research-references.md` only. After editing, it re-runs the comparison from Step 3 against the updated file. If drift remains, it reports the remaining issues and offers another fix pass. Otherwise it confirms all drift is resolved.

**Step 6: Suggest commit.** The skill outputs a suggested commit message:
```
docs(research-index): sync entries in docs/research-references.md
```

## Research Behavior

None. This skill performs no web research. It operates entirely on local files.

## Reference Files

None. This skill does not use shared reference files (rubric, baseline, or domain cache).

## Interactions with Other Skills

- **Called by:** No other skill invokes sync-research-index. It is user-invoked only.
- **Calls:** No other skills.
- **Shares references with:** None.
- **Related maintenance skills:** `/check-repo-health` checks reference freshness and token budgets, including the integrity of links in `docs/research-references.md` (Step 5a). Running sync-research-index after adding research files ensures the index stays current before a health check. `/validate-primitive-dependencies` (Phase 2 Task C) likewise treats `docs/research-references.md` as the canonical research-index source.

## Hard Rules

1. **Only modify `docs/research-references.md`.** Never edit CLAUDE.md or research files. The CLAUDE.md `## Research References` section is now a topic-cluster routing table only — it is not the authoritative index.
2. **Present the full report before offering to sync.** The user sees all drift before deciding whether to apply changes.
3. **Preserve existing entry format and relative-to-docs/ paths.** New entries match the style of existing entries (`- [Title](path) -- Description`); paths are written relative to `docs/`.
4. **Never modify research files.** This skill only reads research files and edits the index.
5. **One-line descriptions only.** Generated descriptions for new entries are concise (15 words or fewer).

## Output Format

The skill produces a drift report table followed by optional edits to `docs/research-references.md` and a commit suggestion:

```
## Research Index Report

| Status   | Path                              | Detail                              |
|----------|-----------------------------------|-------------------------------------|
| OK       | research/prompt-engineering/...   | Linked                              |
| UNLINKED | research/new-topic/file.md        | Not in docs/research-references.md  |
| BROKEN   | research/removed/old.md           | File missing                        |

**Summary:** X files on disk, Y linked in index, Z unlinked, W broken links.
```

If sync is performed, the skill confirms the edit and suggests the commit message. If no drift is found, it reports that the index is in sync with no changes needed.
