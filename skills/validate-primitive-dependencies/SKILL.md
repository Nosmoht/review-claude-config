---
name: validate-primitive-dependencies
description: >
  Maps cross-primitive references and flags integrity problems: broken refs,
  orphaned files, cycles. Triggered manually via
  `/validate-primitive-dependencies [folder]`. Use when a commit diff touches
  `skills/*/SKILL.md`, `agents/*.md`, `hooks/*.py`, or files under
  `.claude/skills/`; or after renaming a primitive (`name:` field change); or
  as a pre-release gate. Do NOT use for quality review — use
  /review-claude-config.
argument-hint: "[folder]"
allowed-tools: Agent, Bash, Read, Glob, Grep, Write
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

## Task C: Scan docs/research-references.md

Read <folder>/docs/research-references.md (the canonical research-index file).
This is the authoritative list of repo-internal research files; CLAUDE.md only contains a topic-cluster routing table that points here.
For each line matching: `[^\]]+\]\(([^)]+\.md)\)` — capture the path.
Paths in this file are written **relative to `docs/`** (e.g., `(../research/foo.md)`). Normalise each captured path to repo-root-relative before recording (e.g., `(../research/foo.md)` → `research/foo.md`; `(evidence-maintenance.md)` → `docs/evidence-maintenance.md`).
Record each as a forward reference of type "research-ref" from `docs/research-references.md` to the normalised path.
If `docs/research-references.md` does not exist, skip Task C and note the skip; the orphan-check in Phase 3 Step 2 must also degrade gracefully.

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
- **research-ref**: The path was already normalised to repo-root-relative in Phase 2 Task C (paths in `docs/research-references.md` are written relative to `docs/`).
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
`research/**/*.md`, verify it appears as a target in `docs/research-references.md`
(from Phase 2 Task C). If not, classify as ORPHANED. If `docs/research-references.md`
does not exist, skip this orphan check and note the skip.

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
| research/some/file.md | research-file | Not in docs/research-references.md |

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

Resolve `<repo-slug>` by running `bash bin/repo-slug.sh "$(pwd)"` and capturing stdout. (For documentation reference only, not the operational source-of-truth: `references/repo-identification.md` describes the sanitize algorithm.)

Confirm via AskUserQuestion (header: "Save report"):
- Option 1 label: "Save report" (Recommended) — description: `"Write to ${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-validate-deps.md"`
- Option 2 label: "Skip" — description: `"Display the path that would have been used"`

On "Save report": write the report file. On "Skip": display the path that would have been used.

---

If any dependencies are broken, present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Fix broken references" (Recommended) — description: `"Edit files manually to fix broken dependencies, then re-run /validate-primitive-dependencies"`
- Option 2 label: "Check repo health" — description: `"Run /check-repo-health for a broader health overview"`
- Option 3 label: "Done" — description: `"End the workflow"`

On "Fix broken references": acknowledge and remind them to re-run this skill after fixing. On "Check repo health": invoke `/check-repo-health`. On "Done": acknowledge and stop.

If the overall verdict is HEALTHY, skip the menu — just present the report.

## Quality measurement (mandatory before Output)

Per `docs/skill-verification-architecture.md` (2026-05-26 retrofit), MAINTAIN-class verification is deterministic: schema invariants (closed-set status vocab, four required report sections), idempotency `f(f(x)) == f(x)` (sort all edge lists before comparison; re-run produces byte-identical canonical row set), and forward-reference evidence predicates fully cover this skill's failure surface. There is no judgment-shaped output to evaluate, so the historical Layer B (adversarial critic) and Layer C (binary rubric) were dropped — they added token cost and false-positive surface without raising assurance. Layer A below is the complete verification.

This skill produces a dependency-graph integrity report (Markdown). Layer A idempotency requires the dependency-graph itself to be deterministic — sort all edge lists before comparison.

Capture the report and a deterministic re-run snapshot to a tempdir so subsequent steps can read both:

```bash
TMPDIR=$(mktemp -d -t vpd-XXXX)
CURRENT="$TMPDIR/current-report.md"
RERUN="$TMPDIR/rerun-report.md"
# Write the report the skill just produced to "$CURRENT".
# Re-run the same scan on the unchanged target folder and write to "$RERUN".
# If a prior-run report snapshot is available, export PRE_VERDICT=<path>;
# otherwise leave unset and SOFT-2 row is skipped.
```

### Layer A — mechanical invariants (deterministic, fail-fast)

Run against the produced report, its deterministic re-run, and (if available) the prior-run snapshot. `STRICT` rows abort; `SOFT` rows warn and continue.

```bash
python3 - "$CURRENT" "$RERUN" "${PRE_VERDICT:-/dev/null}" <<'PY'
import sys, re, os
from pathlib import Path

CURRENT, RERUN, PRE_VERDICT = (Path(p) for p in sys.argv[1:4])

VERDICT_STATUSES = {"OK", "MISSING", "ORPHANED", "UNREGISTERED", "PARTIAL", "GHOST", "HEALTHY"}

def canonicalize_rows(text):
    """Return sorted set of pipe-table rows, dropping non-load-bearing
    timestamp/date lines so idempotency check isn't poisoned by run-id."""
    out = []
    for line in text.splitlines():
        if not line.startswith("|") or line.startswith("|--"): continue
        if re.match(r"^\s*\|\s*(Source|File|Skill|Ref Type)\s*\|", line): continue
        out.append(line.strip())
    return sorted(set(out))

cur_text = CURRENT.read_text(errors="ignore")
re_text = RERUN.read_text(errors="ignore") if RERUN.exists() else ""

rows = []  # (sev, metric, before, after, delta, flag)

# STRICT-1 IDEMPOTENT_RERUN_DIFF — second run on unchanged target must produce
# byte-identical row sets (after canonicalizing). Catches F1 IDEMPOTENCY_BREAK.
cur_rows = canonicalize_rows(cur_text)
re_rows = canonicalize_rows(re_text) if re_text else cur_rows
idem_diff = set(cur_rows) ^ set(re_rows)
rows.append(("STRICT", "idempotent_rerun_row_diff",
             0, len(idem_diff), f"+{len(idem_diff)}" if idem_diff else "0",
             f" FAIL diff_rows={sorted(idem_diff)[:3]}" if idem_diff else ""))

# STRICT-2 VERDICT_STATUS_VOCAB — every status cell must be in the closed set
status_cells = re.findall(r"\|\s*(OK|MISSING|ORPHANED|UNREGISTERED|PARTIAL|GHOST|HEALTHY|[A-Z][A-Z_-]+)\s*\|", cur_text)
bad = [s for s in status_cells if s not in VERDICT_STATUSES]
rows.append(("STRICT", "verdict_status_vocab_violations",
             0, len(bad), f"+{len(bad)}" if bad else "0",
             f" FAIL unknown={sorted(set(bad))[:5]}" if bad else ""))

# STRICT-3 FORWARD_REF_EVIDENCE — every Forward References row must cite a
# non-empty Source and Target. Catches D5 VERDICT_HONESTY violations.
empty_target = 0
in_fwd = False
for line in cur_text.splitlines():
    if line.startswith("## Forward References"): in_fwd = True; continue
    if line.startswith("## ") and in_fwd: in_fwd = False; continue
    if not in_fwd: continue
    if not line.startswith("|") or line.startswith("|--"): continue
    cells = [c.strip() for c in line.split("|")[1:-1]]
    if len(cells) < 4: continue
    if cells[0] in ("Source",) or set(cells[0]) <= {"-"}: continue
    # cells[2] is Target; allow "NONE" but not empty
    if not cells[2]:
        empty_target += 1
rows.append(("STRICT", "forward_refs_without_target",
             0, empty_target, f"+{empty_target}" if empty_target else "0",
             f" FAIL empty_target_rows={empty_target}" if empty_target else ""))

# STRICT-4 REPORT_SECTION_PRESENCE — the four canonical sections must exist
REQUIRED_SECTIONS = {"Forward References", "Orphaned References",
                     "Circular Dependencies", "Registration Consistency"}
present = {h for h in REQUIRED_SECTIONS
           if re.search(rf"^##\s+{re.escape(h)}\s*$", cur_text, re.M)}
missing = REQUIRED_SECTIONS - present
rows.append(("STRICT", "required_sections_present",
             len(REQUIRED_SECTIONS), len(present),
             f"-{len(missing)}" if missing else "0",
             f" FAIL missing={sorted(missing)}" if missing else ""))

# SOFT-1 VERDICT_ROW_COUNT_DELTA — vs prior snapshot (NULL_VERDICT_REGRESSION smell)
if PRE_VERDICT.exists() and str(PRE_VERDICT) != "/dev/null":
    prev = PRE_VERDICT.read_text(errors="ignore")
    prev_rows = len(re.findall(r"^\|", prev, re.M))
    curr_rows = len(re.findall(r"^\|", cur_text, re.M))
    delta = curr_rows - prev_rows
    flag = ""
    if prev_rows and abs(delta) >= max(5, prev_rows // 4):
        flag = f" warn prev={prev_rows} curr={curr_rows}"
    rows.append(("SOFT", "verdict_row_count_delta",
                 prev_rows, curr_rows, f"{delta:+d}", flag))

# SOFT-2 NON_OK_TOTAL — count of MISSING+ORPHANED+UNREGISTERED+PARTIAL+GHOST rows
non_ok = sum(1 for s in status_cells
             if s in {"MISSING", "ORPHANED", "UNREGISTERED", "PARTIAL", "GHOST"})
rows.append(("SOFT", "non_ok_rows", 0, non_ok, f"+{non_ok}", ""))

fail = 0
print(f"{'severity':9} {'metric':40} {'before':>8} {'after':>8} {'delta':>8}")
for sev, metric, before, after, delta, flag in rows:
    if "FAIL" in flag: fail += 1
    print(f"{sev:9} {metric:40} {str(before):>8} {str(after):>8} {delta:>8}{flag}")
sys.exit(1 if fail else 0)
PY
```

If exit non-zero → STOP, do not present the report. Report failures, propose specific restorations (sort the edge lists deterministically, fix the bad status cell, add the missing required section), then re-run Layer A.

### Reconciliation outcomes

- **All STRICT pass** → present the report.
- **Any STRICT fail** → propose targeted restorations (sort the edge lists deterministically, restore the dropped row, fix the bad status cell, add the missing required section) and re-run Layer A on the patched report. **Hard cap: 2 iterations** (per `rules/contract-authoring.md §Small-bound carve-out`; bound = 2 → hard rule, no graceful +1). If still failing after iteration 2, surface to the user; do not auto-publish the report.
- **Only SOFT warnings** (`verdict_row_count_delta` jump, large `non_ok_rows` total) → present the report but include the warnings in the Summary line so the operator has a final-glance opportunity.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **Whole reference-pattern class omitted from the scanner.** Layer A verifies status/section/idempotency invariants; it does NOT verify the scanner's edge-type taxonomy is complete. If an entire reference class (CI workflow YAML, conditional `if`-pattern references) is absent from the scanner regex, the pipeline sees no missing edges. External corpus reference (manually-curated edge-class taxonomy refreshed quarterly) is required and out of this pipeline's scope.
2. **Semantic correctness of slash-command resolution.** Layer A checks status-vocabulary validity but cannot catch the case where a slash-command name has two plausible disambiguations (`/review` → `review-skill` or `review-agent`) and the scanner picked wrong — both ends of the edge still exist.
3. **Ghost registrations from non-Markdown sources.** Slash-commands invoked from CI workflows, shell scripts, or hooks/JSON commands are not in the Phase 2 scanner's scope. A ghost registration living only in `.github/workflows/*.yml` is invisible.

## Hard Rules

- **Read-only on analyzed files.** Never modify any primitive. The only file
  this skill writes is the health report.
- **Graceful degradation.** If hooks.json is missing, skip hook checks and note
  the skip. If registration docs are missing, skip those checks and note the skip.
  If `docs/research-references.md` is missing, skip Task C and the research-file orphan check.
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

## Tier A Tool Justification

**Tier A tool justification (Bash):** Bash is granted exclusively for
`bash bin/repo-slug.sh "$(pwd)"` to compute the canonical `<repo-slug>`
deterministically per `references/repo-identification.md`. The
command-level allowlist `Bash(bash bin/repo-slug.sh:*)` enforces scope.
The script is read-only (stdout slug, no FS writes), so this Tier-A grant
carries no write-amplification risk.
