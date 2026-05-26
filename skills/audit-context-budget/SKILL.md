---
name: audit-context-budget
description: >
  Estimates token cost of a repo's Claude Code configuration (CLAUDE.md, rules,
  skills, MCP servers, agents) and recommends optimizations. Use when context
  feels cramped at session start, after adding MCP servers or skills, or before
  optimizing a Claude Code setup. Do NOT use to audit source code tokens — use
  /audit-repo for that.
argument-hint: "[folder]"
allowed-tools: Agent, Bash, Read, Write, Glob, Grep
disable-model-invocation: true
---

# Audit Context Budget

You are a configuration cost analyst that estimates and visualizes the token footprint of a repo's Claude Code setup. Your job is to measure what loads into context at session start, identify the largest cost drivers, and surface optimization options — without judging whether any particular configuration is wrong.

Stop conditions:
- If the target folder does not exist, report the error and stop.
- If no Claude Code configuration is detected, produce a baseline-only report and stop.
- If the scanner subagent fails to return structured results, report what failed and stop.

## Phase 1 — Setup

**Step 1: Load references.**

Read these files from this skill's `references/` directory:
- `references/context-budget-heuristics.md` — estimation formulas and optimization multipliers
- `references/context-report-schema.md` — report structure and YAML schema
- `references/healthy-baselines.md` — per-component thresholds

Resolve `<repo-slug>` by running `bash bin/repo-slug.sh "$(pwd)"` and capturing stdout. (For documentation reference only, not the operational source-of-truth: `**/review-claude-config/references/repo-identification.md` describes the sanitize algorithm.)

**Step 2: Resolve target.**

`$ARGUMENTS` is the target folder path. Use the current working directory when empty.

Validate the folder exists via Glob (`<folder>/**`). Stop with an error if the folder has no files.

**Step 3: Detect configuration presence.**

Glob for:
- `<folder>/CLAUDE.md`
- `<folder>/.claude/` (any contents)
- `<folder>/.mcp.json`
- `<folder>/settings.json` or `<folder>/.claude/settings.json`

If none found: produce a minimal report with only the unavoidable baseline (system prompt + tools + git + environment) and stop. Note that without Claude Code config, these baseline costs are the only session-start tokens.

Also check if the target is a plugin repo: Glob for `<folder>/skills/*/SKILL.md` at root level. If found, set `is_plugin_repo = true`.

## Phase 2 — Collection

Launch a **Context Budget Scanner Agent** to collect raw measurements. The agent returns structured facts only — no recommendations or interpretations.

Agent allowed-tools: `Glob, Grep, Read, Bash`

---

```
You are scanning a repository to collect Claude Code configuration facts for a context budget audit.
Return facts only — no recommendations or interpretations.

SCAN LIMITS:
- Read at most 50 lines per file
- Scan at most 4 directory levels deep
- Cap file listings at 200 entries per glob
- BASH RESTRICTIONS: Only read-only commands allowed (wc, grep, git).
  Never use: rm, mv, cp, tee, >, >>, mkdir, touch, or any write command.

ERROR HANDLING:
- If a glob returns no results, report "NOT FOUND" for that item.
- If a file cannot be read (permission error, missing), report "ERROR: [path] — [reason]" and continue.
- If a bash command fails, report the command and error under the category.
- Always produce output for every category, even if empty.

TARGET FOLDER: [insert target folder]

## Category A: CLAUDE.md Files

1. Check for user-global file: `~/.claude/CLAUDE.md`. If accessible: char_count via `wc -c`, line_count via `wc -l`.
2. Read `<folder>/CLAUDE.md` (project root). char_count, line_count.
3. Walk parent directories from `<folder>` looking for additional CLAUDE.md files (up to 3 levels up).
4. For each CLAUDE.md found: count lines matching imperative-verb or list pattern (proxy for instruction count).
   Pattern: lines starting with `- `, `* `, a digit+`.`, or words: Add|Run|Use|Check|Do|Set|Never|Always|Avoid|Prefer|Keep|Load|Read|Create|Write|Ensure|Follow|Apply|Review|Report
5. Check `<folder>/.claude/settings.json` for `claudeMdExcludes` key. Report: present or absent.
6. Check `~/.claude/settings.json` for `claudeMdExcludes`. Report: present or absent.

## Category B: Rules

1. Glob `<folder>/.claude/rules/*.md`. For each file: `wc -c` for char_count.
   Read first 10 lines of each file to check for `paths:` in frontmatter.
   Classify as: unconditional (no `paths:`) or path-scoped (has `paths:`).

2. Glob `~/.claude/rules/*.md`. Same collection.
   Note: global rules without `paths:` re-inject on every tool call.

## Category C: MCP Servers

1. Read `<folder>/.mcp.json` (project-level). List server names.
2. Read `<folder>/.claude/settings.json`. Extract `mcpServers` keys.
3. Read `~/.claude/settings.json`. Extract `mcpServers` keys.
4. For each server: check if it has a `disabled: true` field.
5. Check for `ENABLE_TOOL_SEARCH` in any of: `.env`, `.envrc`, shell profiles accessible. Report found/not found.
6. For each server: count tools if a local schema file exists (e.g., in `.claude/` or repo root). Otherwise estimate 10 tools as default.

## Category D: Skills and Agents

1. Glob `<folder>/.claude/skills/*/SKILL.md`. For each: `wc -c`, read frontmatter (first 15 lines) to check `disable-model-invocation`.
2. Glob `<folder>/skills/*/SKILL.md` (plugin skills). For each: `wc -c`, read frontmatter. These load full content at session start.
3. Glob `<folder>/.claude/agents/*.md`. For each: `wc -c`, read frontmatter (first 15 lines).

## Category E: Git Context

1. Run `git -C <folder> rev-parse --is-inside-work-tree 2>/dev/null`. Report: git repo or not.
2. If git repo:
   - `git -C <folder> status --porcelain | wc -l` — dirty file count.
   - `git -C <folder> log --oneline | wc -l` — commit count.

## Category F: Other

1. Check `<folder>/.claude/MEMORY.md`. If exists: `wc -c`.
2. Read `<folder>/.claude/settings.json` or `~/.claude/settings.json`. Count entries in `permissions.deny` list.

---
COMPLETION: End your response with "SCAN COMPLETE" on its own line.
```

---

Wait for the scanner to return "SCAN COMPLETE" before proceeding.

## Phase 3 — Analysis

Using the scanner output and the loaded reference files, compute estimates and classifications inline.

**Step 0: Validate scanner output against detection.**

For every artifact flagged present in Phase 1 Step 3 (`CLAUDE.md`, `.mcp.json`, `settings.json`, plugin skills), confirm a corresponding non-`NOT FOUND` entry exists in the scanner's Categories A/C/D/F. If any detected artifact maps to `NOT FOUND` or is absent from the scanner output, abort and re-dispatch the scanner with the missing path enumerated. Also confirm every Category A–F header is present in the response.

**Step 1: Compute token ranges.**

For each measured component, apply chars/4 (low) and chars/3 (high) from `context-budget-heuristics.md`.

Fixed values:
- System prompt: 5,000 tokens
- Built-in tools: 6,000 (ENABLE_TOOL_SEARCH found/default) or 16,000 (not found in env)
- Environment: 280 tokens
- Git context: apply the formula from `context-budget-heuristics.md`

For MCP servers: apply per-tool heuristic from `context-budget-heuristics.md` based on tool counts and deferred/eager mode.

**Step 2: Compute instruction density.**

Sum instruction-proxy line counts from: all CLAUDE.md files + unconditional rule files. Add the fixed Claude Code base of 50. Compare against thresholds in `healthy-baselines.md`.

**Step 3: Classify each component.**

Apply thresholds from `healthy-baselines.md`. Assign OK / WARN / CRITICAL per component. Overall status = highest severity.

**Step 4: Generate optimization recommendations.**

For each WARN or CRITICAL component, generate a specific recommendation using multipliers from `context-budget-heuristics.md`:

- CLAUDE.md > 200 lines or > 3K tokens: "Convert prose rules to tables. Based on measured compression of 82%, this file (~X chars) could reduce to ~Y-Z tokens."
- Unconditional rules present: "These N rules re-inject on every tool call. Session cost at 20 tool calls: ~X tokens. Adding `paths:` frontmatter where applicable could reduce re-injection by ~24%."
- Plugin skills (under `skills/*/SKILL.md`) without `disable-model-invocation`: "Plugin skills load full SKILL.md content at session start. The stub + Read-on-invoke pattern reduces this by ~91%."
- Project skills without `disable-model-invocation`: "Consider adding `disable-model-invocation: true` to skills invoked only by user command. Reduces always-on cost to 0 tokens."
- MCP servers in eager mode: "ENABLE_TOOL_SEARCH not detected. With tool search disabled, MCP tool schemas load fully (~480 tokens/tool). Enabling defers all to ~0.85 tokens/tool."
- Disabled MCP servers: "Disabled servers still inject tool names. Remove them from config to recover ~10 tokens/tool."
- claudeMdExcludes absent in apparent monorepo: "CLAUDE.md files in parent directories may load unexpectedly. `claudeMdExcludes` in settings.json prevents this."

Frame each recommendation as cost visibility, not removal. Do not recommend removing any MCP server, skill, or rule.

**Step 5: Rank by savings.**

Sort recommendations: highest estimated savings first. Assign P0 (>5K tokens saved or instruction density CRITICAL), P1 (1-5K), P2 (<1K or informational).

## Phase 4 — Report

Build the report using the schema from `context-report-schema.md`.

**Body sections in order:**

### Context Budget Summary

Total estimated config context (excluding unavoidable baseline): X–Y tokens (Z–W% of 200K).
Overall status: healthy / warning / critical.
Instruction density: N estimated instructions. Status: healthy / warning / critical.

If `is_plugin_repo = true`: "This is a plugin repo. For internal reference file budgets, use `/check-repo-health tokens`."

### Limitations

Estimation method: character count divided by 3–4. Actual tokens depend on tokenizer, language mix, and content structure. Estimates may be off by ±30% for code-heavy content.

Base overhead: system prompt and built-in tool costs derive from community measurements, not official Anthropic documentation [Tier 3: community observation].

Unmeasured factors: actual API token consumption (no access), prompt cache hit rates (cached tokens cost 10× less — a "costly" config that caches well may be cheaper than a "lean" one that cache-misses), rule re-injection multiplier depends on conversation length, context compaction behavior.

Cache alignment warning: splitting a large CLAUDE.md or rule file can break the stable prefix required for prompt caching. Measure the cache hit rate before and after significant splits.

### Component Breakdown

Table: Component | Token Range (Low–High) | Est. % of 200K | Status | Key Observation

Include one row per measured component, plus the unavoidable baseline as an informational row.

### Optimization Recommendations

Grouped by P0 / P1 / P2. Each recommendation: specific file(s), what to change, estimated savings range, evidence tier.

### Action Plan

Checkbox list: one item per recommendation with specific file path and action.

---

**Present the full report in the conversation. Then confirm before writing the report file.**

Offer to write to: `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/<YYYY-MM-DDTHHMMSS>-audit-context-budget.md`

Use the `<repo-slug>` value already resolved via `bash bin/repo-slug.sh "$(pwd)"`. Include `repo: <slug>` and optionally `origin: <git-remote-url>` in frontmatter.

## Quality measurement (mandatory before report persistence)

Without verification, this skill fails at **predicate-incompleteness and evidence-fabrication** — e.g., the Component Breakdown table silently omits a 10K-token rule file present in the target, or an Optimization Recommendation cites a phantom file path that does not exist under `<folder>`. The literature converges on a three-layer pipeline (CheckEval arXiv:2403.18771, G-Eval arXiv:2303.16634, position bias Shi et al. arXiv:2406.07791, IFEval arXiv:2311.07911); each layer alone is insufficient for audit reports.

Hold the assembled report in a tempfile so subsequent layers read it deterministically:

```bash
TMPDIR=$(mktemp -d -t audit-cb-XXXX)
REPORT="$TMPDIR/report.md"
TARGET_MANIFEST="$TMPDIR/target-manifest.txt"
# write proposed report to "$REPORT" (do NOT yet Write to plugins/data path)
# write the assemblage of detected sources (CLAUDE.md paths, rule paths,
# skill paths, agent paths, MCP server names) as one path per line to
# "$TARGET_MANIFEST" — this is the multi-source target for Layer A/B.
```

### Layer A — mechanical invariants (deterministic, fail-fast)

Any `STRICT` row failure → abort, do not Write the report. Any `SOFT` row warning → log inline as a report footnote and proceed.

```bash
python3 - "$REPORT" "$TARGET_MANIFEST" <<'PY'
import re, sys, os
from pathlib import Path

report_path = sys.argv[1]
manifest_path = sys.argv[2] if len(sys.argv) > 2 else None

STATUS_VOCAB = {"healthy", "warning", "critical"}
EVIDENCE_TIERS = {"Tier 1", "Tier 2", "Tier 3"}
PRIORITY_TIERS = {"P0", "P1", "P2"}

with open(report_path) as f:
    t = f.read()

fm_match = re.match(r"^---\n(.*?)\n---\n", t, re.S)
if not fm_match:
    print("STRICT frontmatter_present FAIL no_yaml_frontmatter")
    sys.exit(1)
fm = fm_match.group(1)
body = t[fm_match.end():]

REQUIRED_FM = ["generated_by", "schema_version", "date", "target", "summary"]
missing_fm = [k for k in REQUIRED_FM if not re.search(rf"^{k}:", fm, re.M)]

schema_v_match = re.search(r"^schema_version:\s*(\d+)", fm, re.M)
schema_v = int(schema_v_match.group(1)) if schema_v_match else None

# audit-context-budget uses inline phrase, NOT a `### Status` heading.
# Per template Acknowledged Residual #5 — SOFT-warn on absence.
overall_status_match = re.search(
    r"Overall status:\s+(healthy|warning|critical)\b", body, re.I
)

# Token ranges: every component row in the breakdown must cite Low-High,
# not a point estimate. Match table rows that include numeric-numeric.
breakdown = re.search(
    r"### Component Breakdown\s*\n(.*?)(?=\n### |\Z)", body, re.S
)
point_estimate_rows = []
if breakdown:
    for line in breakdown.group(1).splitlines():
        # skip header / separator / informational baseline notes
        if not line.strip().startswith("|") or "---" in line or "Token Range" in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2:
            tok_cell = cells[1]
            # accept any of: "1,200-2,400", "1.2K-2.4K", "N/A", "—"
            if tok_cell and tok_cell not in {"N/A", "—", "-", ""}:
                if not re.search(r"\d[\d,.kKM]*\s*[-–]\s*\d", tok_cell):
                    point_estimate_rows.append(cells[0])

# Evidence tier per recommendation (every P0/P1/P2 item cites a Tier).
recs = re.search(
    r"### Optimization Recommendations\s*\n(.*?)(?=\n### |\Z)", body, re.S
)
missing_tier = []
if recs:
    for block in re.split(r"\n(?=####|\*\*P[0-2])", recs.group(1)):
        if re.search(r"\b(P0|P1|P2)\b", block):
            if not re.search(r"Tier\s*[1-3]", block):
                missing_tier.append(block[:60].replace("\n", " "))

# Required body sections.
REQUIRED_SECTIONS = [
    "Context Budget Summary",
    "Limitations",
    "Component Breakdown",
    "Optimization Recommendations",
    "Action Plan",
]
missing_sections = [
    s for s in REQUIRED_SECTIONS if not re.search(rf"^#{{1,4}}\s+{re.escape(s)}\b", body, re.M)
]

# File-path evidence in recommendations must resolve under the target
# folder (manifest). Sample up to 5 backtick-quoted paths.
cited_paths = re.findall(r"`([^`]+\.(?:md|json|yaml|sh|py))`", body)
manifest_paths = set()
if manifest_path and os.path.exists(manifest_path):
    with open(manifest_path) as mf:
        manifest_paths = {ln.strip() for ln in mf if ln.strip()}
bad_paths = []
if manifest_paths and cited_paths:
    for p in cited_paths[:5]:
        # accept a citation if any manifest path ends with the cited fragment
        if not any(mp.endswith(p) or p in mp for mp in manifest_paths):
            bad_paths.append(p)

rows = []
def add(sev, name, val, ok, note=""):
    flag = "" if ok else (" FAIL" if sev == "STRICT" else " warn")
    rows.append((sev, name, val, flag, note))

add("STRICT", "frontmatter_present",       "yes",                     True)
add("STRICT", "required_frontmatter_keys", f"missing={missing_fm}",   not missing_fm)
add("STRICT", "schema_version_pinned",     f"v{schema_v}",            schema_v == 1,
    note="schema_version=1 invariant; bump invalidates analytics")
add("STRICT", "required_body_sections",    f"missing={missing_sections}",
    not missing_sections)
add("STRICT", "token_estimate_is_range",   f"point_rows={point_estimate_rows}",
    not point_estimate_rows,
    note="every component must cite Low-High, never a point value")
add("STRICT", "evidence_tier_cited",       f"missing_tier={len(missing_tier)}",
    not missing_tier,
    note="every recommendation must cite Tier 1/2/3")
add("SOFT",   "overall_status_in_vocab",
    overall_status_match.group(1) if overall_status_match else "absent",
    bool(overall_status_match),
    note="inline 'Overall status: <vocab>' phrase; SOFT per template residual #5")
add("STRICT", "cited_paths_resolve",       f"bad={bad_paths}",
    not bad_paths,
    note="backtick-quoted file paths in recommendations must exist in target manifest")

fail = 0
print(f"{'severity':8} {'metric':30} {'value':40} {'flag':>6}  note")
for sev, name, val, flag, note in rows:
    if "FAIL" in flag: fail += 1
    print(f"{sev:8} {name:30} {str(val)[:40]:40} {flag:>6}  {note}")
sys.exit(1 if fail else 0)
PY
```

**Metric coverage matrix:**

| Layer-A row                  | Catches                              |
|------------------------------|--------------------------------------|
| `frontmatter_present`        | F5 (report-shape break)              |
| `required_frontmatter_keys`  | F5                                   |
| `schema_version_pinned`      | F10                                  |
| `required_body_sections`     | F1 (predicate-incompleteness)        |
| `token_estimate_is_range`    | skill-specific: point-estimate drift |
| `evidence_tier_cited`        | skill-specific: tier-attribution gap |
| `overall_status_in_vocab`    | F5 (SOFT — inline phrase form)       |
| `cited_paths_resolve`        | F9 (evidence fabrication)            |

### Layer B — adversarial critic dispatch (blind, recall-framed)

**Layer-B-Gate.** Per `docs/skill-verification-architecture.md`, AUDIT
output is structured extraction when predicates are mechanical. Layer B
fires ONLY when ≥30% of this skill's predicates require LLM judgment
(closed-set classification, taxonomy ambiguity, behavioral-signal
detection). For pure-mechanical audits (file exists / regex matches /
exit code only), SKIP Layer B and rely on Layer A + Layer C alone.
Document the gate decision in the report frontmatter as
`layer_b_fired: true|false (rationale)`.

Dispatch a fresh subagent whose single task is to find Component Breakdown rows the audit MISSED (`DROPPED`) and rows it ADDED without evidence in the target assemblage.

```
Agent({
  description: "Adversarial context-budget critic",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind audit-critic. You are given two artifacts:\n" +
    "\n" +
    "A: a manifest of the source assemblage that the audit consumed\n" +
    "   — paths to CLAUDE.md files, rule files, skill SKILL.md files,\n" +
    "   agent files, MCP server names from .mcp.json / settings.json.\n" +
    "\n" +
    "B: the audit report produced from A.\n" +
    "\n" +
    "The audit applied a closed catalog: every component in A that\n" +
    "loads at session start should appear as a row in B's Component\n" +
    "Breakdown, and every Optimization Recommendation in B should\n" +
    "cite a concrete file path present in A.\n" +
    "\n" +
    "Your task:\n" +
    "\n" +
    "1. For each row in B's Component Breakdown, locate the\n" +
    "   corresponding entry in A. Classify as:\n" +
    "   - GROUNDED — entry in A matches the row's path and category\n" +
    "   - WEAKENED — the row understates token impact vs. evidence in A\n" +
    "     (e.g., severity should be CRITICAL, report says WARN)\n" +
    "   - ADDED   — no entry in A supports the row (false positive)\n" +
    "\n" +
    "2. Scan A for components NOT represented in B's Component\n" +
    "   Breakdown. The catalog is closed: every CLAUDE.md file, every\n" +
    "   rule file, every plugin or project SKILL.md, every MCP server,\n" +
    "   every agent must appear. Classify as:\n" +
    "   - DROPPED — component in A with no row in B\n" +
    "\n" +
    "3. Report ONE block per item:\n" +
    "\n" +
    "   [GROUNDED|WEAKENED|ADDED|DROPPED]: <component-name-or-path>\n" +
    "   evidence_in_A: \"<path or manifest entry>\"\n" +
    "   evidence_in_B: \"<row excerpt or 'absent'>\"\n" +
    "   reason: <<=2 sentences>\n" +
    "\n" +
    "Do not rate quality. Do not praise compression. Do not write a\n" +
    "summary paragraph. Report under 500 words.\n" +
    "\n" +
    "A:\n<paste $TARGET_MANIFEST contents>\n\n" +
    "B:\n<paste $REPORT contents>"
})
```

**Order-swap mandate:** dispatch a second time with `A` and `B` reversed (position bias is the dominant pairwise-judge artifact, Shi et al. 2024 arXiv:2406.07791). Take the union of items flagged across both runs, de-duplicated by `(class, component-name)`.

Mapping: `ADDED` → D2 NO; `WEAKENED` → D4 NO; `DROPPED` → D5 NO; `GROUNDED` → no action.

### Layer C — binary rubric (CheckEval-style)

Six yes/no dimensions. Any `NO` blocks report Write until resolved.

```
D1 STATUS_VOCAB_CONFORMANT   The inline "Overall status:" phrase in the
                              body cites one of {healthy, warning, critical},
                              and every `summary[].status` in frontmatter
                              uses the same vocabulary. SOFT-skip if the
                              inline phrase form is absent (per template
                              residual #5). Catches F5.

D2 EVIDENCE_GROUNDED          Every backtick-quoted file path in
                              Optimization Recommendations resolves to a
                              real entry in the target manifest (Layer A
                              `cited_paths_resolve` passed AND Layer B
                              surfaced ZERO `ADDED` items). Catches F2, F9.

D3 TAXONOMY_DISJOINT          No component appears under two distinct
                              category labels (CLAUDE.md / Rules / MCP /
                              Skills / Agents / Other). Component count
                              in Breakdown matches manifest cardinality
                              minus the unavoidable baseline rows.
                              Catches F4.

D4 SEVERITY_CALIBRATED        Each component cites exactly one status
                              token in {OK, WARN, CRITICAL}; status
                              matches the documented thresholds in
                              `references/healthy-baselines.md` (Layer B
                              surfaced ZERO `WEAKENED` items). Catches F8.

D5 RULE_CATALOG_COMPLETENESS  Layer-B critic surfaced ZERO `DROPPED`
                              items: every component in the target
                              manifest appears as a row in the Component
                              Breakdown (or is explicitly classified as
                              unavoidable baseline). Catches F1, F3.

D6 DISCOVERY_PRECISION        Every Optimization Recommendation is
                              tagged with priority in {P0, P1, P2}, cites
                              evidence tier in {Tier 1, Tier 2, Tier 3},
                              names a specific file path, and reports an
                              estimated savings range (not a point
                              value). Layer A `evidence_tier_cited` passed.
                              Catches F7.
```

**Layer-A row → Dimension mapping:**
- `frontmatter_present`, `required_frontmatter_keys`, `overall_status_in_vocab` → D1
- `cited_paths_resolve` → D2
- `required_body_sections` → D3, D5
- `token_estimate_is_range` → D6
- `evidence_tier_cited` → D6
- `schema_version_pinned` → D1

**Layer-B item → Dimension mapping:**
- `ADDED` → D2 NO
- `WEAKENED` → D4 NO
- `DROPPED` → D5 NO
- `GROUNDED` → no impact (expected)

### Reconciliation outcomes

- **All STRICT pass + zero ADDED/WEAKENED/DROPPED** → proceed to confirm-then-Write the report file to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`.
- **Any STRICT fail OR any ADDED/WEAKENED/DROPPED** → patch inline: drop fabricated paths/rows, re-classify any weakened component severity, add missing components to the Breakdown. Re-run Layer A on the patched report. Max 2 iterations. If still failing, surface the full ledger to the user and do NOT Write the report to the persisted path.
- **Only SOFT warnings** (e.g., `overall_status_in_vocab` absent because the inline phrase is missing) → add a one-line footnote to the report ("Layer A SOFT: <metric> warned") and proceed.

### Acknowledged residuals (this pipeline does NOT close)

1. **Status-line ambiguity (template residual #5)** — this skill uses the inline phrase `Overall status: healthy / warning / critical` rather than a discrete `### Status` heading. Layer A's `overall_status_in_vocab` row is SOFT, not STRICT; a missing phrase warns but does not block. Documented in the AUDIT category template as an accepted divergence from the canonical heading form.
2. **Token-estimate calibration** — Layer A enforces *form* (Low–High range, never point) but cannot validate the *magnitude* of the range. A breakdown row of `1–2 tokens` for a 10K-line CLAUDE.md passes form-check but is wrong. Magnitude correctness requires re-running the chars/4 ↔ chars/3 heuristic against the actual file lengths, which Layer B's critic does only when explicitly prompted.
3. **Cache-alignment heuristic absence** — the report's Limitations section warns that splitting a CLAUDE.md may break the cache prefix; the pipeline cannot verify whether the report's recommendations would actually preserve or break the cache (no API/cache-hit telemetry available in-session).
4. **Cross-config drift** — the audit captures one repo's static config; if the user combines this repo's settings with a user-global `~/.claude/settings.json` that the scanner did not enumerate, the budget estimate is incomplete. The scanner does read `~/.claude/settings.json` for MCP servers and `claudeMdExcludes`, but not for hooks, permissions, or env-injected tool grants.
5. **LLM-judged baseline thresholds** — `healthy-baselines.md` thresholds are heuristic; Layer C D4's "matches documented thresholds" check is form-level (status token in {OK, WARN, CRITICAL}), not threshold-derivation correctness.

## Hard Rules

- Read-only on the target repository. Write only the report file to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`. Before Write, scan the assembled report (frontmatter `target:`, optional `origin:`, and the entire body) and replace any literal absolute home-directory prefix with `$HOME/`. The `~/.claude/hooks/block-sensitive-content.sh` PreToolUse hook denies Writes containing such prefixes.
- Token estimates are always ranges (chars/4 to chars/3), always labeled "estimated".
- Every recommendation cites the evidence tier and specific file paths measured.
- Never recommend removing MCP servers, skills, or rules. Report cost only.
- Limitations section appears before recommendations in every report.
- Bash is restricted to the scanner subagent. Top-level workflow uses Read/Glob/Grep only.
- When the target is a plugin repo (`skills/*/SKILL.md` at root), note that `/check-repo-health tokens` handles internal reference budgets.

## Tier A Tool Justification

**Tier A tool justification (Bash):** Bash is granted exclusively for
`bash bin/repo-slug.sh "$(pwd)"` to compute the canonical `<repo-slug>`
deterministically per `references/repo-identification.md`. The
command-level allowlist `Bash(bash bin/repo-slug.sh:*)` enforces scope.
The script is read-only (stdout slug, no FS writes), so this Tier-A grant
carries no write-amplification risk.
