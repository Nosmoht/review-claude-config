---
name: review-claude-config
description: >
  Audits all skills, agents, and rules in a folder and produces quality
  certificates. Use when asked to 'audit quality', 'review skills', or before
  shipping new skills. Do NOT use for a single item — use /review-skill,
  /review-agent, or /review-rule.
argument-hint: "[folder] [--validation]"
allowed-tools: Agent, Bash, Read, Write, Glob, WebSearch, WebFetch
---

# Review Claude Config

Analyze all Claude Code skills, agents, and rules in a target folder and produce per-item quality certificates with optimization recommendations.

## Argument Handling

Parse `$ARGUMENTS` into:
- `validation_mode = true` if the standalone token `--validation` is present
- `target_folder` = the remaining argument text after removing `--validation`

If `target_folder` is empty, use the current working directory.

Validate the folder exists. If no `.claude/` directory is found at any level, report that and stop.

Validation mode is a bounded release/CI path. It is not the default user flow.

## Phase 1 — Setup and Discovery

### Step 0: Tool Availability Checks

If `validation_mode = true`:
- set `websearch_available = false`
- set `webfetch_available = false`
- skip live tool probes entirely

Otherwise:
- Attempt a trivial WebSearch (e.g., "Claude Code documentation"). If it fails or is unavailable, set `websearch_available = false` and continue. Goal Alignment will be scored from model knowledge only, marked `[no web verification]` on the certificate.
- Attempt a trivial WebFetch (e.g., fetch "https://docs.anthropic.com"). If it fails or is unavailable, set `webfetch_available = false` and continue. Analysis agents will use WebSearch snippets only instead of fetching full article content.

### Steps 1-2: Launch in parallel

**1. Load References**

Read these files from the skill's own `references/` directory:
- `references/scoring-rubric.md` — the grading criteria
- `references/engineering-baseline.md` — prompt, context, and tool design techniques with canonical evidence-class labels
- `references/source-quality-criteria.md` — source credibility criteria for web research

Check `last_refreshed` date in the baseline frontmatter. If older than 3 months, warn the user: "Baseline was last refreshed on [date]. Consider running `/refresh-engineering-baseline` for current best practices."

**2. Discovery Agent**

Launch an Agent (allowed-tools: Glob, Read) to discover all Claude Code primitives in the target folder:

```
Discover all Claude Code skills, agents, rules, MCP server configs, and settings. Use Glob/Read with these patterns:
- <folder>/.claude/skills/*/SKILL.md
- <folder>/.claude/agents/*.md
- <folder>/.claude/rules/*.md
- <folder>/**/.claude/skills/*/SKILL.md (monorepo support)
- <folder>/**/.claude/agents/*.md (monorepo support)
- <folder>/**/.claude/rules/*.md (monorepo support)
- <folder>/.mcp.json (MCP server config)
- <folder>/.claude/settings.json (project settings)
- <folder>/.claude/settings.local.json (local settings, if exists)

Exclude paths containing: node_modules, .git, vendor, dist, build, reports

For each discovered file:
- Read the full content
- Classify as "Skill", "Agent", "Rule", "MCP", or "Settings"

Return results in this exact format per item:

### [file path]
**Type:** Skill | Agent | Rule | MCP | Settings
**Content:**
[full file content]

If a file cannot be read, return:
### [file path]
**Type:** Unknown
**Error:** [reason]

If a Glob pattern returns no results, skip it silently (not all repos have all types).

Also note (but do not analyze): existence of CLAUDE.md

COMPLETION: You are done when all Glob patterns have been checked and all readable files are classified.
```

If no primitives are discovered at all, report that and stop.

Sort the discovered items lexicographically by file path before returning them to the orchestrator.

## Phase 2 — Per-Item Analysis

### Step 0: Domain Cache Lookup

If `validation_mode = true`, skip the cache workflow entirely:
- assign every item `Domain: none`
- assign `Cache Status: NONE`
- assign `Role: consumer`
- do not load `domain-cache/INDEX.md`
- do not infer domains
- do not designate researchers
- do not persist cache updates later

Otherwise continue with the normal cache workflow below.

Before dispatching analysis agents, the orchestrator performs domain cache lookup:

1. **Load knowledge base index.** Read `${CLAUDE_PLUGIN_ROOT}/skills/review-claude-config/references/domain-cache/INDEX.md`. INDEX.md contains only universal methodology entries (context-engineering, research-sourcing, etc.). Domain-specific knowledge is researched at runtime.

2. **Match items against universal cache.** For each discovered item:
   - Match against the INDEX.md entries (keys + descriptions).
   - If a universal entry matches: check `last_refreshed` date. **CACHED** (<90 days), **STALE** (≥90 days). Read `${CLAUDE_PLUGIN_ROOT}/skills/review-claude-config/references/domain-cache/{key}.md` on-demand. If file is missing despite being in INDEX.md, downgrade to RUNTIME_RESEARCH.
   - If no universal entry matches: extract the single most specific technology or workflow term from (1) frontmatter description, (2) parent directory name, (3) explicit technology references in body. If multiple candidates, prefer the term appearing in both description and body. Assign status **RUNTIME_RESEARCH**.
   - If no clear domain is inferable (e.g., generic "code-review"): assign `Domain: none`, `Cache Status: NONE`.

3. **Assign researchers.** For STALE universal entries shared by multiple items, designate one agent as researcher (existing pattern). For RUNTIME_RESEARCH domains, designate one researcher per unique domain keyword.

### Step 0b: Domain Deep Research (parallel with Step 1; Step 2 waits for both to complete)

If any items have `RUNTIME_RESEARCH` status and `websearch_available = true`:

1. From the discovery results (Phase 1) and the detected runtime domain keywords, derive 2-3 **specific** research questions. Not generic "best practices" — targeted questions from the repo context. Examples:
   - Technology: "SwiftUI AudioSession best practices for recording + offline storage"
   - Workflow: "corpus canonization quality criteria for chat exports"
   - Quality: "requirement traceability validation patterns for specification documents"
2. Launch a Domain Research Agent (allowed-tools: WebSearch, WebFetch, Read) that executes 2-3 WebSearch queries per domain (max 5 total, hard cap). Apply `source-quality-criteria.md` discard rules. Tag each source with tier.
3. Collect structured domain knowledge per domain (max 500 tokens each).
4. This research is **ephemeral** — it is injected into the per-item orchestration suffix but NOT persisted to disk.

If `websearch_available = false`, skip this step. Items with RUNTIME_RESEARCH proceed with model knowledge only.

### Step 1: Load Specialized Skill Content

Locate the specialized review skills (sibling directories in the same plugin). Use Glob if paths are not immediately known.

Read the SKILL.md and evaluation guide for each type that has discovered items:
- Skills: `review-skill/SKILL.md` + `review-skill/references/skill-evaluation-guide.md`
- Agents: `review-agent/SKILL.md` + `review-agent/references/agent-evaluation-guide.md`
- Rules: `review-rule/SKILL.md` + `review-rule/references/rule-evaluation-guide.md`
- MCP: `review-mcp-server/SKILL.md` + `review-mcp-server/references/mcp-evaluation-guide.md`
- Settings: `review-settings/SKILL.md` + `review-settings/references/settings-evaluation-guide.md`

Only load the types that have discovered items (e.g., skip MCP content if no `.mcp.json` found).

### Step 2: Dispatch Analysis Agents

Group discovered items by type (Skill, Agent, Rule, MCP, Settings). For each type group, construct a **type-specific shared prefix** that is **byte-identical** across all items of the same type. MCP and Settings are typically single-item groups (one `.mcp.json`, one `settings.json` per repo) — dispatch as batch of 1, same pattern.

**Type-specific shared prefix structure:**
```
[Specialized SKILL.md instructions for this type]

## Reference Materials

### Scoring Rubric
[Insert scoring-rubric.md content — identical across all types]

### Engineering Baseline
[Insert engineering-baseline.md content — identical across all types]

### Source Quality Criteria
[Insert source-quality-criteria.md content — identical across all types]

### Type-Specific Evaluation Guide
[Insert the evaluation guide for this type]
```

**Per-item suffix** (appended after the shared prefix):

```
---orchestration---
mode: orchestrated
websearch_available: [true/false]
webfetch_available: [true/false]
domain_cache: |
  Domain: [domain key or "none"]
  Cache Status: [CACHED | STALE | RUNTIME_RESEARCH | NONE]
  Role: [researcher | consumer]

  [If CACHED: insert cached content + "Use as domain knowledge, skip WebSearch.
  1 supplemental query if insufficient."]

  [If STALE + researcher: insert cached content + "Use as starting point +
  1 WebSearch to verify/update. Apply discard rules from source-quality-criteria.md.
  Tag each source with tier (1/2/3). Return Domain Cache Update section."]

  [If STALE + consumer: insert cached content + "Use as-is, another agent
  is refreshing."]

  [If RUNTIME_RESEARCH + research available: insert runtime research content +
  "Use as domain context. This research is ephemeral — do NOT return a
  Domain Cache Update section."]

  [If RUNTIME_RESEARCH + no research: "No cache. Use model knowledge only."]

  [If NONE: "No domain inferred. WebSearch as normal."]
---

## Item Under Review

**Path:** [file path]
**Content:**
[Insert full file content]
```

If `validation_mode = true`, select a deterministic validation sample before dispatch:
- take the first lexicographic Skill, if any
- then the first lexicographic Agent, if any
- then the first lexicographic Rule, if any
- if fewer than 3 items were selected, fill the remaining slots with the next lexicographic undispatched items regardless of type
- analyze at most 3 items total

**Dispatch rules:**
- Allowed-tools per agent: WebSearch, WebFetch, Read (no Write, Edit, or Bash). Omit WebFetch if `webfetch_available = false`.
- If `validation_mode = true`, dispatch the sampled items in a single batch and do not present intermediate per-batch output.
- Otherwise process in parallel, batched in groups of 8. Present each batch's results before starting the next.
- Each agent returns a structured certificate (or an `## ERROR` block on failure).
- On agent error: log failure, continue with remaining items.

### Domain Cache Update Collection

After all agents complete, collect "Domain Cache Update" sections from researcher agents that had STALE cache status for universal entries only. RUNTIME_RESEARCH results are ephemeral and must NOT be collected for persistence. Hold updates for Phase 3.5.

If `validation_mode = true`, skip this collection step entirely.

## Phase 3 — Presentation

If `validation_mode = true`, do not print full per-item reports. Instead present only:

```markdown
## Validation Summary

- Mode: validation
- Target: <folder>
- Items discovered: N
- Items analyzed: M
- Sampled paths:
  - <path 1>
  - <path 2>
  - <path 3>

| Item | Type | Overall | Score |
|------|------|---------|-------|
| ... | ... | ... | ... |
```

If any sampled item returns an `## ERROR` block, surface it directly under `## Validation Summary`.

Skip the normal full report presentation, Cross-Cutting Observations, Phase 3.5, Phase 4, and the follow-up menu in validation mode.

Otherwise continue with the normal presentation below.

Present each item's report to the user. After all items, add:

### Summary Table

```
## Summary

| Item | Type | Overall | Clarity | Completeness | PE | CE | Goal | Safety | Meta |
|------|------|---------|---------|--------------|----|----|------|--------|------|
| ... | Skill/Agent | ... | ... | ... | ... | ... | ... | ... | ... |
| ... | Rule | ... | ... | ... | — | — | ... | — | — |
| ... | MCP | ... | — | ... | — | — | ... | ... | ... |
| ... | Settings | ... | — | ... | — | — | ... | ... | ... |
```

### Cross-Cutting Observations

Identify patterns across items:
- Common anti-patterns (e.g., consistent tool bloat, missing output formats)
- Consistent strengths (e.g., good safety practices across all items)
- Systemic recommendations (e.g., "all agents would benefit from reference files")
- Missing CLAUDE.md guidance that would benefit all items
- Where possible, cite one concrete example path per pattern so the observation is easy to verify

## Phase 3.5 — Domain Cache Drift (read-only)

Aggregate any "Domain Cache Update" sections from researcher agents into a `### Domain Cache Drift` block in the review report (Phase 4) — list affected universal-entry keys + 1-line summary per key. Do **not** write to `references/domain-cache/` at runtime; entries are maintainer-driven on a 90-day cadence (direct edit + commit in source repo). Skip this block entirely if `websearch_available = false` and `webfetch_available = false`.

## Quality measurement (mandatory before Phase 4)

Without verification, this skill — the BATCH orchestrator over the 10 single-target `/review-*` skills — fails at SCOPE-DRIFT (a discoverable primitive in `<folder>/.claude/` is silently absent from `summary[]` because the Discovery Agent's Glob output was truncated or one type-bucket's parallel batch returned an `## ERROR` block that was logged but not retried, so the aggregate report certifies a portfolio it did not actually audit), TYPE-MISMATCH (a `summary[i].type` says `Skill` but the per-item Recommendations block emits only the 3-dim rule-subset because the dispatcher routed the item to the wrong specialized reviewer), CONVERGENCE-DRIFT (the aggregate union of per-item `finding_id`s at High+Medium on the deterministic subset varies across consecutive runs on the same target folder because per-item perspective dispatch is non-deterministic and merge does not deduplicate across items), and ADVISORY-LEAKAGE (a per-item slot embeds an advisory checklist item like `WS-1` / `OF-3` / `PD-1` at High or Medium because the dispatched specialized reviewer failed to apply the merge-time Low cap per `references/merge-rules.md` §"Perspective Finding Handling"). The three-layer pipeline below catches all four; D6 is load-bearing for SCOPE-DRIFT.

References: CheckEval (arXiv:2403.18771), G-Eval (arXiv:2303.16634), Position bias in LLM-as-a-Judge (arXiv:2406.07791), IFEval (arXiv:2311.07911), FollowBench (Jiang et al. ACL 2024), Beyond Consensus (NUS 2025), `references/review-report-contract.md`, `references/merge-rules.md`, `references/scoring-rubric.md`.

Run the pipeline against the assembled Phase 4 Step 1 report body BEFORE writing the file in Phase 4 Step 2. Compute `REPORT_PATH` as the path the Phase 4 Step 2 Write will use; if not yet finalized, serialize the assembled body to a tempfile for the duration of this section. Compute `SCOPE_INVENTORY` by re-running the same Glob patterns used by the Discovery Agent in Phase 1 (Step 2) and capturing the file-path set; pass it to Layer A as the second positional argument.

### Layer A — mechanical invariants (deterministic, fail-fast)

Run on the assembled aggregate report. STRICT failures block Phase 4 Step 2; SOFT warnings surface in the Output report.

```bash
python3 - "$REPORT_PATH" "$SCOPE_INVENTORY_FILE" "${PRIOR_MERGED_JSON:-}" <<'PY'
import sys, re, json, os
from pathlib import Path

REPORT = Path(sys.argv[1])
SCOPE  = sys.argv[2]   # path to a newline-separated re-glob of primitives
PRIOR  = sys.argv[3]

SEVERITY_VOCAB = {"High","Medium","Low"}
GRADE_VOCAB    = {"A","B","C","D","F"}
DIM_BY_TYPE = {
    "Skill":    {"clarity","completeness","prompt_engineering","context_engineering","goal_alignment","safety","metadata"},
    "Agent":    {"clarity","completeness","prompt_engineering","context_engineering","goal_alignment","safety","metadata"},
    "Hook":     {"clarity","completeness","goal_alignment","safety","metadata"},
    "Rule":     {"clarity","completeness","goal_alignment"},
    "MCP":      {"completeness","goal_alignment","safety","metadata"},
    "Settings": {"completeness","goal_alignment","safety","metadata"},
    "ClaudeMD": {"clarity","completeness","context_engineering","goal_alignment"},
    "Plugin":   {"completeness","goal_alignment","safety","metadata"},
}
URL_RE   = r"https?://[^\s)`\"<>]+"
CITE_RE  = r"\b(arXiv:[0-9.]+|RFC\s*[0-9]+|DOI:[^\s)]+)"
FIND_RE  = r"^####\s+\d+\.\s+.+\(Impact:\s*(High|Medium|Low)"
FM_RE    = r"\A---\n(.*?)\n---\n"
ID_RE    = r"ID:\s*([A-Z][A-Z0-9-]+:[^,\s)]+/v1)"
HOME_RE  = re.compile(r"^target\s*:\s*/(?:Users|home)/[^/\s]+/", re.M)

errors, warns = [], []
text = REPORT.read_text()
m = re.match(FM_RE, text, re.S)
if not m:
    errors.append("STRICT: report missing YAML frontmatter"); print("\n".join(errors)); sys.exit(1)
fm = m.group(1)

for k in ["generated_by","schema_version","date","repo","target","items_reviewed"]:
    if not re.search(rf"^{k}\s*:", fm, re.M):
        errors.append(f"STRICT: frontmatter missing required field '{k}'")
gb = re.search(r"^generated_by\s*:\s*(\S+)", fm, re.M)
if gb and gb.group(1) != "review-claude-config":
    errors.append(f"STRICT: generated_by must be 'review-claude-config', got '{gb.group(1)}'")
if HOME_RE.search(fm):
    errors.append("STRICT: frontmatter 'target' uses expanded home prefix; must use literal $HOME/")

# --- Section order at aggregate level (STRICT) ---
sections = [s.group(1).strip() for s in re.finditer(r"^##\s+(.+)$", text, re.M)]
required = ["Summary","Cross-Cutting Observations"]
pos = {k: next((i for i,s in enumerate(sections) if s.startswith(k)), -1) for k in required}
for k,v in pos.items():
    if v == -1:
        errors.append(f"STRICT: aggregate report missing required section '{k}'; found={sections}")

# --- summary[] rows: type ↔ dimension-set consistency (STRICT) ---
# Parse YAML-ish per-row block by name.
row_blocks = re.findall(r"-\s+name:\s*(\S+)(.*?)(?=^-\s+name:|\Z)", fm, re.S | re.M)
items_summary = re.search(r"^items_reviewed\s*:\s*(\d+)", fm, re.M)
if items_summary and len(row_blocks) != int(items_summary.group(1)):
    errors.append(f"STRICT: len(summary[])={len(row_blocks)} != items_reviewed={items_summary.group(1)}")

summary_paths = []
for name, body in row_blocks:
    tm = re.search(r"^\s*type\s*:\s*(\w+)", body, re.M)
    pm = re.search(r"^\s*path\s*:\s*(\S+)", body, re.M)
    om = re.search(r"^\s*overall\s*:\s*(\w+)", body, re.M)
    if not tm or not pm:
        errors.append(f"STRICT: row name={name} missing type or path")
        continue
    typ, path = tm.group(1), pm.group(1)
    summary_paths.append(path)
    if om and om.group(1) not in GRADE_VOCAB:
        errors.append(f"STRICT: row name={name} overall '{om.group(1)}' not in {GRADE_VOCAB}")
    expected_dims = DIM_BY_TYPE.get(typ)
    if expected_dims is None:
        errors.append(f"STRICT: row name={name} unknown type '{typ}'")
        continue
    for dim in expected_dims:
        dm = re.search(rf"^\s*{dim}\s*:\s*(\S+)", body, re.M)
        if not dm:
            errors.append(f"STRICT: row name={name} (type={typ}) missing dim '{dim}'")
            continue
        v = dm.group(1).rstrip(",")
        if v not in GRADE_VOCAB and v != "null":
            errors.append(f"STRICT: row name={name} dim {dim}='{v}' not in {{A,B,C,D,F,null}}")

# --- D6 SCOPE_DISCIPLINE: every Glob-discovered primitive appears in summary[] (STRICT for primary set; SOFT for skipped) ---
if SCOPE and os.path.exists(SCOPE):
    inv = {ln.strip() for ln in Path(SCOPE).read_text().splitlines() if ln.strip()}
    rep = set(summary_paths)
    missing = inv - rep
    extra   = rep - inv
    if missing:
        errors.append(f"STRICT: SCOPE_DISCIPLINE — primitives discovered but absent from summary[]: {sorted(missing)}")
    if extra:
        warns.append(f"SOFT: summary[] paths not in re-glob inventory (symlinks / dotfiles / .gitignore-d per Residual #5): {sorted(extra)}")
else:
    warns.append("SOFT: SCOPE_INVENTORY_FILE not provided — D6 cannot verify scope completeness")

# --- Finding headings + severity vocab (STRICT) ---
findings = re.findall(FIND_RE, text, re.M)
for sev in findings:
    if sev not in SEVERITY_VOCAB:
        errors.append(f"STRICT: finding severity '{sev}' not in {SEVERITY_VOCAB}")
blocks = re.split(r"^####\s+\d+\.", text, flags=re.M)[1:]
for i, b in enumerate(blocks, 1):
    for sub in ["Evidence","Why it matters","Validation"]:
        if not re.search(rf"\b{sub}\b", b):
            errors.append(f"STRICT: finding #{i} missing required sub-block '{sub}'")

# --- Advisory leakage at aggregate level (STRICT) ---
advisory_ids = {"WS-1","OF-3","OF-4","PE-4","CE-3","PD-1","RF-1"}
leaked = []
for h in re.finditer(r"####\s+\d+\.\s+.+\(Impact:\s*(High|Medium|Low)[^)]*ID:\s*([A-Z0-9-]+):", text):
    sev, item = h.group(1), h.group(2)
    if item in advisory_ids and sev in {"High","Medium"}:
        leaked.append(f"{item}@{sev}")
if leaked:
    errors.append(f"STRICT: advisory items leaked at High/Medium severity: {leaked}")

# --- URL / citation set (SOFT — Layer B verifies resolution) ---
urls  = set(re.findall(URL_RE,  text))
cites = set(c if isinstance(c,str) else c[0] for c in re.findall(CITE_RE, text))
warns.append(f"INFO: urls={len(urls)} cites={len(cites)} (Layer B verifies resolution)")

# --- Convergence vs prior merged.json (STRICT only when provided) ---
if PRIOR and os.path.exists(PRIOR):
    prior = json.loads(Path(PRIOR).read_text())
    cur = set(re.findall(ID_RE, text))
    prev = {f["finding_id"] for f in prior.get("findings",[])
            if f.get("severity") in {"High","Medium"}
            and f.get("checklist_item") not in advisory_ids}
    drift = cur ^ prev
    if drift:
        errors.append(f"STRICT: convergence drift on H+M deterministic-subset (aggregate union): lost={sorted(prev-cur)} gained={sorted(cur-prev)}")

print(f"=== Layer A — {REPORT.name} ===")
for w in warns:  print(f"warn  {w}")
for e in errors: print(f"FAIL  {e}")
print(f"--- {len(errors)} STRICT, {len(warns)} SOFT ---")
sys.exit(1 if errors else 0)
PY
```

What each metric catches: frontmatter required-fields + `$HOME/` literal → DIMENSION-GRADE-ABSENCE and the `block-sensitive-content.sh` PreToolUse contract; aggregate section order → structural validity; `len(summary[]) == items_reviewed` → SCOPE-DRIFT lower bound; type ↔ dimension-set table → TYPE-MISMATCH; re-glob inventory vs `summary[].path` → SCOPE-DRIFT (STRICT-missing / SOFT-extra per Residual #5); severity vocabulary + finding sub-blocks → SEVERITY-MISCALIBRATION (form-level); advisory-leakage scan → ADVISORY-LEAKAGE; convergence diff against prior `merged.json` → CONVERGENCE-DRIFT on the aggregate union.

### Layer B — adversarial critic dispatch (blind, recall-framed)

Dispatch a fresh subagent per per-item slot in `summary[]` AND once at the aggregate level. Per-item critic compares the original primitive file (Skill SKILL.md / Agent .md / Rule .md / hooks.json / .mcp.json / settings.json / plugin.json / CLAUDE.md) against the per-item Recommendations block emitted by the orchestrator. Aggregate critic compares the re-glob inventory against `summary[]`. Adversarial framing is load-bearing — non-adversarial dispatch loses CITATION-ROT, FALSE-RESOLUTION, and SCOPE-MISSING recall.

```
Agent({
  description: "Adversarial review-claude-config per-item critic",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind reviewer. Two files are attached: ARTIFACT and " +
    "REPORT_SLOT. Neither label tells you which is which until you read " +
    "them. ARTIFACT is one primitive file from the audited folder (a " +
    "SKILL.md, agent .md, rule .md, hooks.json, .mcp.json, settings.json, " +
    "plugin.json, or CLAUDE.md). REPORT_SLOT is the per-item Goal + " +
    "Certificate + Strengths + Recommendations block emitted by " +
    "/review-claude-config for that primitive.\n\n" +
    "Your only task is to find what the REPORT_SLOT got wrong. List " +
    "every item that meets one of:\n" +
    "- MISSING — a defect actually present in ARTIFACT that REPORT_SLOT " +
    "  does not flag (cite the line, name the rubric dimension it " +
    "  violates).\n" +
    "- FABRICATED — a finding in REPORT_SLOT whose claimed Evidence " +
    "  quote does not appear verbatim in ARTIFACT (cite finding heading " +
    "  + absent quote).\n" +
    "- MIS-SEVERITY — a finding whose severity (High|Medium|Low) is " +
    "  inconsistent with its evidence per the rubric grade caps.\n" +
    "- MIS-CITED — a URL, arXiv ID, RFC, or references/*.md citation " +
    "  in REPORT_SLOT that reads as reconstructed-from-memory rather " +
    "  than resolved-in-session (broken link, wrong file, no tool-" +
    "  response).\n" +
    "- UNCITED — a quantitative or evidence-based claim in REPORT_SLOT " +
    "  with no citation at all.\n" +
    "- FALSE-RESOLUTION — a finding REPORT_SLOT claims resolved (delta " +
    "  section) whose underlying defect still appears in ARTIFACT.\n" +
    "- TYPE-MISROUTE — REPORT_SLOT's emitted dimension set does not " +
    "  match ARTIFACT's primitive kind (e.g. ARTIFACT is a SKILL.md but " +
    "  REPORT_SLOT emitted only the rule 3-dim subset).\n" +
    "- ADVISORY-AT-HIGH — a finding whose checklist_item is in the " +
    "  advisory set {WS-1, OF-3, OF-4, PE-4, CE-3, PD-1, RF-1} shipped " +
    "  at severity High or Medium (must be Low per merge-rules).\n\n" +
    "Do not rate quality. Do not praise. Do not propose fixes. List " +
    "items only. Quote the literal sentence and name which file. " +
    "Report under 500 words.\n\n" +
    "ARTIFACT:\n<paste primitive file contents>\n\n" +
    "REPORT_SLOT:\n<paste per-item block contents>"
})
```

**Dispatch each per-item pair twice with order swapped** (ARTIFACT↔REPORT_SLOT label position) — position bias is the dominant pairwise-judge artifact (Shi et al. 2024 arXiv:2406.07791). Take the union of items flagged across both runs per slot.

Then dispatch the aggregate-level critic once:

```
Agent({
  description: "Adversarial review-claude-config scope critic",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind reviewer. Two text blocks are attached: INVENTORY " +
    "and AGGREGATE. INVENTORY is a newline-separated list of primitive " +
    "file paths discovered under the audited folder's .claude/ tree. " +
    "AGGREGATE is the orchestrator-level Summary Table + Cross-Cutting " +
    "Observations sections of a /review-claude-config report.\n\n" +
    "Your only task is to find what AGGREGATE got wrong about scope. " +
    "List items meeting one of:\n" +
    "- SCOPE-MISSING — an INVENTORY path that AGGREGATE's Summary Table " +
    "  does not list.\n" +
    "- SCOPE-EXTRA — an AGGREGATE Summary Table path absent from " +
    "  INVENTORY (may be legitimate per Residual #5 — symlinks, " +
    "  dotfiles, .gitignore-d; flag for human triage).\n" +
    "- PATTERN-OVERREACH — a Cross-Cutting Observation claiming a " +
    "  pattern 'across all items' that has no cited example, or whose " +
    "  cited example path is not in AGGREGATE's Summary Table.\n\n" +
    "Do not rate quality. Do not praise. Report under 300 words.\n\n" +
    "INVENTORY:\n<paste re-glob output>\n\n" +
    "AGGREGATE:\n<paste Summary Table + Cross-Cutting Observations>"
})
```

### Layer C — binary rubric reconciliation

Six binary dimensions, each yes/no, each tied to ≥1 failure class. Any `NO` blocks Phase 4 Step 2 (report write) until resolved.

```
D1 CONVERGENCE_STABILITY  When a prior report exists in the report archive, the
                          set of finding_id values at severity in {High, Medium}
                          on the deterministic subset (per merge-rules.md
                          §"Perspective Finding Handling"), taken as the UNION
                          across all summary[i] rows, is byte-identical between
                          consecutive runs on the same target folder.
                          (Catches: CONVERGENCE-DRIFT)

D2 SEVERITY_JUSTIFIED     Every finding (in every per-item Recommendations
                          block) has severity matching its evidence per the
                          rubric §"Grade Caps" + §"Item Inventory"; no Layer-B
                          MIS-SEVERITY or ADVISORY-AT-HIGH item open.
                          (Catches: SEVERITY-MISCALIBRATION, ADVISORY-LEAKAGE)

D3 DIMENSION_COVERAGE     For every summary[i] row, the dimension set emitted
                          matches DIM_BY_TYPE[summary[i].type] with grade in
                          {A,B,C,D,F,null}; no row is missing a required dim;
                          no row emits a dim not in its type's set.
                          (Catches: DIMENSION-GRADE-ABSENCE, TYPE-MISMATCH,
                          TYPE-MISROUTE)

D4 EVIDENCE_RESOLVED      Every URL, arXiv ID, RFC, and references/*.md path
                          cited in ANY per-item block was either resolved in
                          the producing session (verifiable from tool-use log)
                          OR carries an explicit `[no web verification]` /
                          `[unverified-url]` marker; no MIS-CITED or UNCITED
                          Layer-B item open.
                          (Catches: CITATION-ROT, UNCITED)

D5 NO_FABRICATED_FINDINGS Every finding's Evidence block contains a literal
                          quote from its primitive file; no FABRICATED or
                          FALSE-RESOLUTION Layer-B item open across any
                          per-item slot.
                          (Catches: SEVERITY-MISCALIBRATION false-positive
                          class, FALSE-FIX-PASS)

D6 SCOPE_DISCIPLINE       Every primitive in the Phase-1 re-glob inventory of
                          <folder>/.claude/ appears in summary[].path; zero
                          Layer-B SCOPE-MISSING items open; SCOPE-EXTRA items
                          documented as the Residual #5 case (symlink /
                          dotfile / .gitignore-d) or removed; every Cross-
                          Cutting Observation cites at least one Summary
                          Table path.
                          (Catches: SCOPE-DRIFT, PATTERN-OVERREACH)
```

Map Layer-A failures → D3/D6. Map Layer-B `MISSING` / `FABRICATED` → D5. Map `MIS-SEVERITY` / `ADVISORY-AT-HIGH` → D2. Map `MIS-CITED` / `UNCITED` → D4. Map `FALSE-RESOLUTION` → D5. Map `TYPE-MISROUTE` → D3. Map `SCOPE-MISSING` / `PATTERN-OVERREACH` → D6.

### Reconciliation outcomes

- **All Layer-A STRICT pass + zero Layer-B `MISSING`/`FABRICATED`/`FALSE-RESOLUTION`/`ADVISORY-AT-HIGH`/`SCOPE-MISSING`/`TYPE-MISROUTE`** → proceed to Phase 4 Step 2.
- **Any Layer-A STRICT fail OR any of those Layer-B classes** → propose restorations inline (name each finding to add/remove with the primitive line + rubric citation; name each missing primitive path), re-dispatch the affected per-item slot or re-glob, re-run Layer A on the patched report. Max two iterations. If still failing at iteration 2, surface to user and do NOT auto-write the report.
- **Only Layer-A SOFT warnings + Layer-B `MIS-SEVERITY` / `MIS-CITED` / `UNCITED` / `SCOPE-EXTRA`** → record in the Output report under `### Layer-B Findings (Advisory)` and proceed. These do not block ship; reviewer triages.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **Cross-report convergence beyond H+M deterministic subset** — D1 is bounded to High+Medium finding_ids on the deterministic subset per `merge-rules.md` §"Convergence Policy". Low-severity advisory drift across the aggregate union is by-design unbounded. If a per-item slot silently moves a deterministic finding into the advisory class (emitting it with an `ADHOC:` id instead of a `WS-2b:` id), Layer A's deterministic-subset filter misses it. Reviewer must spot-check `ADHOC:`-prefixed finding_ids across all per-item slots.
2. **Calibration drift vs the baseline** — D2 verifies severity is internally consistent with cited rubric evidence; it does NOT verify that `engineering-baseline.md` itself is calibrated against current best practice. A stale baseline (>90 days, per CLAUDE.md) silently inflates High counts across every per-item slot without triggering any pipeline layer. `/refresh-engineering-baseline` is out-of-band.
3. **Report-vs-tool-use-log audit** — D4's URL set is extracted from the report text; verifying each citation was actually resolved in the producing session requires reading the session JSONL under `$HOME/.claude/projects/<project>/<sessionId>.jsonl`. The pipeline does not auto-parse JSONL — Layer B asks the per-item critic to flag obvious reconstructed-from-memory URLs but cannot prove resolution.
4. **Specialized reviewer soundness** — `merge-rules.md` §"Layer 1.5 — Binary Boundary Caps" pins per-item grade caps (e.g. CLAR-2 FAIL → Clarity ≤ C); the pipeline checks the cap was applied but does NOT verify that the dispatched specialized reviewer (`/review-skill`, `/review-agent`, etc.) ran its own Layer A/B/C correctly on the primitive. A poisoned per-item certificate propagates silently through the aggregate.
5. **Glob discovery completeness** — D6 trusts the re-glob inventory passed in as `SCOPE_INVENTORY_FILE`, computed with the same patterns the Discovery Agent used in Phase 1. Symlinked, dot-prefixed, or git-untracked primitive directories are matched by neither pass and silently missed by both. SCOPE-EXTRA items in summary[] (paths the re-glob does not see but the discovery did, e.g. via a follow-symlinks variation) are downgraded to SOFT and surfaced under Residual #5 — reviewer must spot-check that `items_reviewed` matches expected directory inventory.

The Output report MUST list which residual classes apply when the critic returns any `UNCERTAIN` flags, when no prior report exists (D1 N/A), or when SCOPE-EXTRA items are reported (Residual #5 applies).

## Phase 4 — Report Persistence

If `validation_mode = true`, skip this entire phase.

After presenting all reports to the user, confirm before writing:
"Save review report to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-review-claude-config.md`?"

Resolve `<repo-slug>` by running `bash bin/repo-slug.sh "$(pwd)"` and capturing stdout. (For documentation reference only, not the operational source-of-truth: `references/repo-identification.md` describes the sanitize algorithm.) Include `repo: <slug>` and optionally `origin: <git-remote-url>` in frontmatter.

If the user declines, skip report writing but still display the report path that would have been used.

### Step 1: Assemble report

Construct a Markdown file with canonical YAML frontmatter from `references/review-report-contract.md` and a full body.

Required producer-specific values:
- `generated_by: review-claude-config`
- one `summary` entry per discovered item
- `type + path` as the canonical portfolio identity
- `null` for rule-only non-applicable dimensions

**Body:** All per-item reports (Goal + Certificate + Strengths + Recommendations), Summary Table, Cross-Cutting Observations.

For every High or Medium recommendation in the body, preserve the shared recommendation schema from `references/review-report-contract.md`.

**Large codebase handling:** If more than 20 items are reviewed, include full per-item reports only for items scoring C or below. A/B items get a one-line summary row only. All items are still analyzed and included in the Summary Table and frontmatter summary (preserves the "Analyze every discovered item" hard rule — analysis is not skipped, only report detail is reduced).

### Step 2: Write the report

Before Write: scan the assembled report (frontmatter `target:`, optional `origin:`, and the entire body including per-item recommendation evidence) and replace any literal absolute home-directory prefix with `$HOME/`. The `~/.claude/hooks/block-sensitive-content.sh` PreToolUse hook denies Writes containing such prefixes.

Write to: `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-review-claude-config.md`

Use the current date and time for the timestamp. Create the `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/` directory if it does not exist. Timestamp ensures each run produces a unique file, supporting the "iterate until convergence" workflow.

### Step 3: Delta comparison

If a previous review report exists in `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`:
- Read the most recent prior report's frontmatter `summary` block and `baseline_version`
- **Baseline check:** If the prior report's `baseline_version` differs from the current engineering baseline, apply the Baseline version lock hard rule (present choice to user before proceeding)
- Compare each item's current grades against prior grades
- Append a "Delta from Prior Review" section to the report body:

```
## Delta from Prior Review ([prior report date])

| Item | Dimension | Previous | Current | Change |
|------|-----------|----------|---------|--------|
| [only rows where grades changed] |
```

If the prior report contains `finding_id` values in recommendation headings, also append a finding-level delta:

```
## Finding Delta from Prior Review

| finding_id | Status | Prior Impact | Current Impact |
|------------|--------|-------------|----------------|
| [rows for: new, recurring, fixed, regressed] |
```

Status definitions (SARIF/SonarQube pattern):
- **new:** finding_id in current but NOT in prior
- **recurring:** finding_id in BOTH current AND prior
- **fixed:** finding_id in prior but NOT in current
- **regressed:** finding_id was `verified` in prior `.finding-state` section but reappears as FAIL

If the prior report has no finding_ids, skip the finding delta (backward-compatible).

If no prior report exists, skip this step entirely.

### Step 4: Confirm

Tell the user the report file path and suggest committing with: `docs(reviews): add YYYY-MM-DDTHHMMSS review report` (using the timestamp from the report filename). This ensures the docs commit and subsequent fix commits (`fix(<scope>): address findings from YYYY-MM-DDTHHMMSS review`) share the same identifier for traceability.

### Step 5: What's Next?

After all output is complete, present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Apply review findings" (Recommended) — description: `"Run /apply-review-findings <report-path> to address High/Medium findings"`
- Option 2 label: "View grade analytics" — description: `"Run /review-analytics to track quality trends over time"`
- Option 3 label: "Done" — description: `"End the workflow"`

On "Apply review findings": invoke `/apply-review-findings` with the report path. On "View grade analytics": invoke `/review-analytics`. On "Done": acknowledge and stop.

## Hard Rules

- **Read-only on analyzed files.** Never modify any discovered skill, agent, or reference file. The only files this skill writes are the review report at `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-review-claude-config.md`. Plugin-internal paths (skills, agents, references, domain-cache) are read-only at runtime.
- **Domain cache entries must come from web research (WebSearch and/or WebFetch) only.** Never write cache entries based on model knowledge alone. If WebSearch is unavailable, skip cache persistence entirely.
- **Analyze every discovered item.** Skip none in the normal mode. Validation mode is the only exception and must stay capped at the deterministic sample described above.
- **Apply the rubric strictly.** Do not inflate grades.
- **Every High or Medium recommendation must include evidence and a concrete rewrite** — not just "improve X."
- **Present all reports before asking** about follow-up actions.
- **Error handling:** If an analysis agent fails, report the failure with partial results and continue with remaining items. Never silently skip.
- **Baseline version lock.** When a prior review report exists for the same target directory, use the same `baseline_version` as the prior report. If the current engineering baseline is newer, present the user with a choice: "Prior review used baseline v{prior}. Current baseline is v{current}. Use [prior|current]?" A baseline change is equivalent to a rubric change and must be a conscious decision, not an implicit drift.

## Tier A Tool Justification

**Tier A tool justification (Bash):** Bash is granted exclusively for
`bash bin/repo-slug.sh "$(pwd)"` to compute the canonical `<repo-slug>`
deterministically per `references/repo-identification.md`. The
command-level allowlist `Bash(bash bin/repo-slug.sh:*)` enforces scope.
The script is read-only (stdout slug, no FS writes), so this Tier-A grant
carries no write-amplification risk.
