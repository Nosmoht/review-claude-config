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

## Quality measurement (mandatory before commit suggestion)

Per `docs/skill-verification-architecture.md` (2026-05-26 retrofit), MAINTAIN-class verification is deterministic: schema invariants (entry format, relative-to-docs/ paths), idempotency via roundtrip consistency `f(f(x)) == f(x)` (a second classification pass on POST reports zero residual drift, a second sync attempt is a no-op), and filesystem ↔ index sync-pair predicates fully cover this skill's failure surface. There is no judgment-shaped output to evaluate, so the historical Layer B (adversarial critic) and Layer C (binary rubric) were dropped — they added token cost and false-positive surface without raising assurance. Layer A below is the complete verification.

Capture the working snapshots so each layer reads deterministically:

```bash
TMPDIR=$(mktemp -d -t sync-research-index-XXXX)
PRE_INDEX="$TMPDIR/research-references.pre.md"
POST_INDEX="$TMPDIR/research-references.post.md"
POST2_INDEX="$TMPDIR/research-references.post2.md"
cp <target>/docs/research-references.md "$PRE_INDEX"
# (run Step 5 edits) — then snapshot POST
cp <target>/docs/research-references.md "$POST_INDEX"
# Re-run classification (Step 3) on the post state, then snapshot POST2 once a
# second sync pass would settle. If the skill correctly reports "in sync", POST2
# == POST (no further mutations attempted).
cp <target>/docs/research-references.md "$POST2_INDEX"
```

### Layer A — mechanical invariants (roundtrip consistency, fail-fast)

Run on PRE / POST / POST2 plus the live `research/` glob. Any `STRICT` failure → abort and report; any `SOFT` delta → log as warning, surface in drift report, do not auto-suggest commit.

```bash
python3 - "$PRE_INDEX" "$POST_INDEX" "$POST2_INDEX" "<target>" <<'PY'
import sys, re
from pathlib import Path

PRE, POST, POST2, ROOT = sys.argv[1], sys.argv[2], sys.argv[3], Path(sys.argv[4])

LINK_RE = re.compile(r"-\s*\[([^\]]+)\]\(([^)]+)\)\s*(?:[—-]\s*(.*))?")

def parse_index(p):
    """Yield (title, repo_rel_path) per link entry; resolve ../research → research."""
    out = []
    for line in Path(p).read_text().splitlines():
        m = LINK_RE.match(line.strip())
        if not m: continue
        title, link, _desc = m.group(1), m.group(2), m.group(3) or ""
        # Index paths are relative to docs/; normalize to repo-root form.
        rel = link.lstrip("./")
        if rel.startswith("../"): rel = rel[3:]
        out.append((title.strip(), rel.strip()))
    return out

def disk_files(root):
    """Yield (repo_rel_path, first_h1_title)."""
    res_dir = root / "research"
    if not res_dir.is_dir(): return []
    out = []
    for f in sorted(res_dir.rglob("*.md")):
        title = ""
        for ln in f.read_text(errors="ignore").splitlines()[:5]:
            if ln.startswith("# "):
                title = ln[2:].strip()
                break
        out.append((str(f.relative_to(root)), title))
    return out

pre_idx, post_idx, post2_idx = parse_index(PRE), parse_index(POST), parse_index(POST2)
disk = disk_files(ROOT)

pre_paths   = {p for _t, p in pre_idx}
post_paths  = {p for _t, p in post_idx}
post2_paths = {p for _t, p in post2_idx}
disk_paths  = {p for p, _t in disk}
disk_titles = dict(disk)
post_titles = {p: t for t, p in post_idx}

# STRICT-1 IDEMPOTENT_ROUNDTRIP — re-classification on POST must report zero drift
# (path-sets must converge and titles must match).
unlinked_post = disk_paths - post_paths
broken_post   = post_paths - disk_paths
stale_post    = {p for p in post_paths & disk_paths
                 if disk_titles.get(p) and post_titles.get(p) != disk_titles.get(p)}
residual = len(unlinked_post) + len(broken_post) + len(stale_post)

# STRICT-2 NO_GHOST_MUTATIONS — POST2 must equal POST byte-for-byte (a second
# sync attempt on the resolved state must mutate nothing).
post_bytes  = Path(POST).read_bytes()
post2_bytes = Path(POST2).read_bytes()

# STRICT-3 NO_NEW_BROKEN — POST must not introduce a path that does not exist
# on disk (catches a "fix" that added a typo'd relative path).
new_broken = (post_paths - pre_paths) - disk_paths

# STRICT-4 NO_LOST_OK — entries that were OK in PRE (path exists + title matches)
# must not disappear from POST without their disk file also disappearing.
pre_ok = {p for _t, p in pre_idx if p in disk_paths}
lost_ok = pre_ok - post_paths

# SOFT-1 MUTATION_VOLUME — surface large changes for operator glance.
added   = post_paths - pre_paths
removed = pre_paths  - post_paths

rows = [
    ("STRICT", "idempotent_roundtrip_residual_drift", 0, residual,
     f"+{residual}" if residual else "0",
     f" FAIL unlinked={sorted(unlinked_post)[:3]} broken={sorted(broken_post)[:3]} stale={sorted(stale_post)[:3]}"
     if residual else ""),
    ("STRICT", "no_ghost_mutations_post_eq_post2", 0,
     0 if post_bytes == post2_bytes else 1,
     "0" if post_bytes == post2_bytes else "+1",
     " FAIL second pass mutated the index" if post_bytes != post2_bytes else ""),
    ("STRICT", "new_broken_paths_introduced", 0, len(new_broken),
     f"+{len(new_broken)}" if new_broken else "0",
     f" FAIL paths={sorted(new_broken)[:3]}" if new_broken else ""),
    ("STRICT", "lost_ok_entries", 0, len(lost_ok),
     f"+{len(lost_ok)}" if lost_ok else "0",
     f" FAIL paths={sorted(lost_ok)[:3]}" if lost_ok else ""),
    ("SOFT",   "entries_added",   0, len(added),   f"+{len(added)}",   ""),
    ("SOFT",   "entries_removed", 0, len(removed), f"+{len(removed)}", ""),
]
fail = 0
print(f"{'severity':9} {'metric':40} {'before':>8} {'after':>8} {'delta':>8}")
for sev, k, b, a, d, flag in rows:
    if "FAIL" in flag: fail += 1
    print(f"{sev:9} {k:40} {b:>8} {a:>8} {d:>8}{flag}")
sys.exit(1 if fail else 0)
PY
```

What each STRICT row catches:

| Row | Failure class |
|---|---|
| `idempotent_roundtrip_residual_drift` | a sync pass that exited early on Edit failure leaves UNLINKED/BROKEN/STALE entries the rerun re-detects |
| `no_ghost_mutations_post_eq_post2` | a second pass that mutates further (e.g. unstable title parsing) |
| `new_broken_paths_introduced` | a "fix" that added a typo'd relative path |
| `lost_ok_entries` | silently dropping a previously-valid entry without a disk-side reason |

SOFT rows surface mutation volume so the operator gets a glance opportunity.

### Reconciliation outcomes

- **All STRICT pass** → proceed to Step 6 (Suggest commit).
- **Any STRICT fail** → propose targeted restoration (re-apply the missed Edit, revert mutations affecting non-link lines, relocate a misclassified entry, sharpen a vacuous description) and re-run Layer A on the patched state. **Hard cap: 2 iterations** (per `rules/contract-authoring.md §Small-bound carve-out`; bound = 2 → hard rule, no graceful +1). If still failing after iteration 2, surface to the user with the full residual list and do not suggest commit.
- **Only SOFT warnings** (`entries_added` or `entries_removed` exceeds an operator-defined glance threshold) → proceed but report the deltas in the drift report so the operator gets a final-glance opportunity.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **Cluster taxonomy semantic correctness.** A research file with a generic title placed in a plausible-but-wrong topical cluster (e.g. a "context-engineering" file landed in "prompt-engineering") may pass schema checks because both clusters are semantically adjacent. NLI on the file body vs. the cluster's description would be required and is out of scope.
2. **Description quality beyond length.** The ≤15-word concision rule is mechanical; a description that is concise AND vacuous ("Notes on the topic.") passes the schema gate while failing the spirit. Only register-aware human review catches this.
3. **Concurrent-edit races.** If a maintainer edits `docs/research-references.md` by hand between the PRE snapshot and the POST snapshot, the Layer A diff will misattribute the manual changes to the skill. Operator discipline upstream.

## Hard Rules

- **Only modify `docs/research-references.md`.** Never edit CLAUDE.md or research files. The CLAUDE.md `## Research References` section now contains a topic-cluster routing table only — it is not the authoritative index.
- **Present the full report before offering to sync.** User sees all drift before deciding.
- **Preserve existing entry format and relative-to-docs/ paths.** New entries match the style of existing entries; paths are written relative to `docs/` (e.g., `../research/...`).
- **Never modify research files.** This skill only reads research files and edits the index.
- **One-line descriptions only.** Generated descriptions for new entries are concise (≤15 words).
