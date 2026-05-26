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

Without verification, this skill fails at **F4 PARTIAL_UPDATE**: the Edit loop in Step 5 exits on the first non-unique-match failure, so an UNLINKED file may be added to the index while a sibling BROKEN entry remains uncorrected — leaving the repo in a state where the drift report says "fixed" but the filesystem ↔ index invariant is half-restored. The 3-layer pipeline (mechanical roundtrip / adversarial critic / binary rubric) is the converging recommendation in the LLM-evaluation literature; any one layer alone misses a documented failure class.

References: CheckEval (arXiv:2403.18771), G-Eval (arXiv:2303.16634), Position bias in LLM-as-a-Judge (arXiv:2406.07791), IFEval (arXiv:2311.07911), FollowBench (ACL 2024), Beyond Consensus (NUS 2025).

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
| `idempotent_roundtrip_residual_drift` | **F1** + **F4** — a sync pass that exited early on Edit failure leaves UNLINKED/BROKEN/STALE entries the rerun re-detects |
| `no_ghost_mutations_post_eq_post2` | **F1** — a second pass that mutates further (e.g. unstable title parsing) |
| `new_broken_paths_introduced` | **F4** + **F7-analogue** — a "fix" that added a typo'd relative path |
| `lost_ok_entries` | **F10** — silently dropping a previously-valid entry without a disk-side reason |

SOFT rows surface mutation volume so the operator gets a glance opportunity.

### Layer B — adversarial critic dispatch (blind, recall-framed)

Dispatch a fresh subagent twice with order swapped (Shi et al. 2024, arXiv:2406.07791 — pairwise position bias is the dominant LLM-judge artifact). The critic is given PRE, POST, the live `research/` filesystem listing, and the relevant CLAUDE.md conventions.

```
You are a blind reviewer auditing a research-index sync skill's effect on
docs/research-references.md.

You are given:
  A: <pre-run snapshot of docs/research-references.md>
  B: <post-run snapshot of the same file>
  L: <list of every research/**/*.md path on disk, each annotated with its
      first `# ` heading>
  C: <CLAUDE.md §Research References + the skill's own classification rules
      from Step 3 — OK / UNLINKED / BROKEN / STALE>

Neither A/B label tells you which is the original.

Find:
1. UNLINKED_MISS — a path in L absent from BOTH A and B (an unlinked file
   the sync pass should have added but did not).
2. BROKEN_MISS — an entry in B whose path is absent from L (a broken link
   the sync pass should have removed but did not).
3. STALE_MISS — an entry in B whose title differs from the disk file's
   first `# ` heading per L.
4. PARTIAL_UPDATE — pairs of expected mutations where one was applied in
   A→B and a sibling was not (e.g. one UNLINKED added but a second UNLINKED
   under the same topical cluster left missing; one BROKEN removed but a
   sibling BROKEN preserved).
5. CLUSTER_DRIFT — a new entry placed in a topical cluster section that
   does not match the subject of the linked file (per the CLAUDE.md
   cluster taxonomy in C).
6. ADDED — entries in B with no corresponding file in L and no
   structured reason (catches fabricated paths or hallucinated titles).
7. WEAKENED — descriptions in B that are vaguer than A's for the same
   path (the skill must produce concise ≤15-word descriptions, not
   vacuous one-liners).
8. NON_SCOPE_EDIT — any mutation in B affecting lines outside the link
   list region (preamble, cluster headings) — the skill MUST only edit
   link entries.

For each item: quote the literal line, name file:line, classify with one
of the eight tokens above. Report under 600 words. Do not rate quality.
Do not praise the skill's design.
```

Then dispatch a **second time with A and B swapped**, and with L's order shuffled, to attenuate position bias. Take the union of items flagged across both runs.

### Layer C — rubric reconciliation (binary CheckEval-style)

Six yes/no dimensions. Any `NO` blocks the "Suggest commit" step (Step 6) until resolved. CheckEval (arXiv:2403.18771) reports +0.45 inter-evaluator agreement for binary vs. Likert.

```
D1 IDEMPOTENT_ROUNDTRIP    A second classification pass on the POST state
                           reports zero residual drift (no UNLINKED, no
                           BROKEN, no STALE), and a second sync attempt
                           is a no-op (POST == POST2 byte-for-byte).
                           Layer A STRICT-1 + STRICT-2 pass.
                           Ties to F1, F4.

D2 FRESHNESS_RESPECT       Title-comparison reads the file's first `# `
                           heading (canonical source), not body markers
                           or YAML frontmatter. STALE entries are flagged
                           when titles diverge; OK entries are not
                           falsely flagged.
                           Layer B finds zero STALE_MISS / FALSE_STALE.
                           Ties to F2, F3.

D3 SYNC_INTEGRITY          Filesystem ↔ index is fully restored:
                           every research/**/*.md file appears in the
                           index, and every index entry resolves to an
                           existing file. PARTIAL_UPDATE on sibling
                           UNLINKED/BROKEN pairs is rejected.
                           Layer B finds zero PARTIAL_UPDATE.
                           Ties to F4.

D4 SCHEMA_AND_CONTRACT     Mutations preserve the existing entry format:
                           `- [Title](relative/path) — Description`, with
                           paths expressed relative to docs/ (`../research/...`),
                           and descriptions ≤15 words. No mutation
                           outside the link-list region.
                           Layer B finds zero NON_SCOPE_EDIT / WEAKENED.
                           Ties to F5.

D5 VERDICT_HONESTY         Every drift-report row (OK / UNLINKED / BROKEN /
                           STALE) traces to evidence in the post-state.
                           No entry claimed "linked" that is absent from
                           the index; no UNLINKED row hides an unfixed
                           BROKEN sibling; no row dropped from a prior
                           report without an underlying fix.
                           Layer B finds zero ADDED / DROPPED-without-fix.
                           Ties to F7, F10.

D6 DEPGRAPH_COMPLETENESS   N/A — this skill operates on a single index
                           file, not a dependency graph. Auto-PASS with
                           note. (Cluster-routing is judged under D4, not
                           D6.)
                           Ties to F8 (vacuously).
```

Map Layer-A failures → rubric:

- STRICT-1 fail (`idempotent_roundtrip_residual_drift`) → D1 NO + D3 NO
- STRICT-2 fail (`no_ghost_mutations_post_eq_post2`) → D1 NO
- STRICT-3 fail (`new_broken_paths_introduced`) → D3 NO + D5 NO
- STRICT-4 fail (`lost_ok_entries`) → D5 NO

Map Layer-B critic tokens → rubric:

- `UNLINKED_MISS` / `BROKEN_MISS` → D3 NO
- `STALE_MISS` → D2 NO
- `PARTIAL_UPDATE` → D3 NO
- `CLUSTER_DRIFT` → D4 NO
- `ADDED` → D5 NO
- `WEAKENED` → D4 NO (description-quality is a schema concern, not honesty)
- `NON_SCOPE_EDIT` → D4 NO

### Reconciliation outcomes

- **All STRICT pass + Layer B yields zero `UNLINKED_MISS` / `BROKEN_MISS` / `STALE_MISS` / `PARTIAL_UPDATE` / `CLUSTER_DRIFT` / `ADDED` / `WEAKENED` / `NON_SCOPE_EDIT`** → proceed to Step 6 (Suggest commit).
- **Any STRICT fail OR any blocking critic token** → propose targeted restoration (re-apply the missed Edit, revert a `NON_SCOPE_EDIT`, relocate a misclassified cluster placement, sharpen a `WEAKENED` description) and re-run Layers A + B on the patched state. **Hard cap: 2 iterations** (per `rules/contract-authoring.md §Small-bound carve-out`; bound = 2 → hard rule, no graceful +1). If still failing after iteration 2, surface to the user with the full residual list and do not suggest commit.
- **Only SOFT warnings** (`entries_added` or `entries_removed` exceeds an operator-defined glance threshold) → proceed but report the deltas in the drift report so the operator gets a final-glance opportunity.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **Cluster taxonomy semantic correctness.** Layer B flags placement under the wrong topical cluster only when the mismatch is detectable from the file's title or first-paragraph subject. A research file with a generic title placed in a plausible-but-wrong cluster (e.g. a "context-engineering" file landed in "prompt-engineering") may pass D4 because both clusters are semantically adjacent. NLI on the file body vs. the cluster's description would be required and is out of scope here.
2. **Description quality beyond length.** D4 enforces the ≤15-word concision rule mechanically, but a description that is concise AND vacuous ("Notes on the topic.") passes the schema gate while failing the spirit. Only register-aware human review catches this.
3. **External-link rot inside research files.** This skill audits the index ↔ filesystem invariant. URLs cited inside individual research files can break independently; that drift is the domain of `maintain-evidence-layer` and `refresh-evidence-coverage`, not this skill. D5 explicitly scopes "verdict honesty" to the OK/UNLINKED/BROKEN/STALE classification, not to deeper link health.
4. **Concurrent-edit races.** If a maintainer edits `docs/research-references.md` by hand between the PRE snapshot and the POST snapshot, the Layer A diff will misattribute the manual changes to the skill. The pipeline assumes the skill is the sole writer for the duration of one invocation; operator discipline upstream.
5. **Cross-rule consistency with CLAUDE.md §Research References.** The CLAUDE.md table is a topic-cluster routing surface, not an authoritative entry list. If a maintainer renames a cluster in CLAUDE.md but not in `docs/research-references.md`, this skill cannot detect the divergence — CLAUDE.md is explicitly out of scope per the existing Hard Rules. A separate audit would be required.

The drift report at Step 4 MUST surface which residual classes apply to any entry the critic flagged as `UNCERTAIN`, giving the operator one final glance before confirming the sync.

## Hard Rules

- **Only modify `docs/research-references.md`.** Never edit CLAUDE.md or research files. The CLAUDE.md `## Research References` section now contains a topic-cluster routing table only — it is not the authoritative index.
- **Present the full report before offering to sync.** User sees all drift before deciding.
- **Preserve existing entry format and relative-to-docs/ paths.** New entries match the style of existing entries; paths are written relative to `docs/` (e.g., `../research/...`).
- **Never modify research files.** This skill only reads research files and edits the index.
- **One-line descriptions only.** Generated descriptions for new entries are concise (≤15 words).
