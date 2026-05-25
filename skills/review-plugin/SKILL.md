---
name: review-plugin
description: >
  Evaluates a Claude Code plugin (.claude-plugin/plugin.json + components)
  across 4 dimensions (Completeness, Goal Alignment, Safety, Metadata).
  Use when asked to 'review plugin', 'review claude-plugin', or
  '/review-plugin'. Do NOT use for individual skills, agents, hooks,
  or .mcp.json — use the per-primitive /review-* skills instead.
argument-hint: <path-to-plugin-root>
allowed-tools: Read, Grep, Glob
disallowedTools: Bash, Write, Edit, WebFetch
---

# Review Claude Code Plugin

Evaluate a `.claude-plugin/plugin.json` manifest and the surrounding
plugin component layout for quality across 4 dimensions: Completeness,
Goal Alignment, Safety, Metadata. Skip Clarity, PE, CE (plugin
manifests are declarations, not prompts or workflows).

This skill is **read-only on every file it inspects**. It writes no
report (no Write tool), runs no commands (no Bash), and never fetches
remote content (no WebFetch). The `disallowedTools` declaration in
frontmatter enforces this — adding any of those tools requires a plan
revision.

## Argument Handling

- `$ARGUMENTS` is a path to a plugin root directory (the directory that
  contains `.claude-plugin/`).
- If the path is omitted, default to the current working directory.
- If `.claude-plugin/plugin.json` is missing at the resolved root,
  report "no plugin manifest at <path>/.claude-plugin/plugin.json" and
  stop.
- Parse the manifest JSON. If parsing fails, raise a Critical finding
  and stop (all subsequent checks are meaningless without the manifest).

## Phase 1 — Setup

1. **Load references.** Read:
   - Scoring rubric: Glob `**/review-claude-config/references/scoring-rubric.md`
   - Source quality criteria: Glob `**/review-claude-config/references/source-quality-criteria.md`
   - Plugin evaluation guide: `references/plugin-evaluation-guide.md`
   - Injection regex library (shared with `/review-mcp-server`): Glob `**/review-mcp-server/references/injection-regex-library.md`. If Glob returns 0 hits, skip Step D and surface `IJ-skipped: injection-regex-library.md not found — install the /review-mcp-server skill or pass --skip-injection-scan` in the certificate.
2. Build a primitive inventory of the plugin via Glob:
   - `<plugin-root>/skills/*/SKILL.md`
   - `<plugin-root>/agents/*.md`
   - `<plugin-root>/hooks/hooks.json`
   - `<plugin-root>/commands/*.md` (legacy)

## Phase 2 — Evaluation

### Step A: Manifest schema check

Apply checklist items PM-1 through PM-12 from the evaluation guide
(required field presence, kebab-case `name`, semver `version`,
description max-length, no XML tags in description, optional-field
type validity, no reserved marketplace names, no "anthropic"/"claude"
substring in `name`, and so on).

### Step B: Component layout check

Apply checklist items CL-1 through CL-5: components in plugin root
(NOT in `.claude-plugin/`); declared `skills`/`agents`/`commands`/
`hooks` paths resolve under the plugin root; namespacing test
(skill name does not collide with another loaded plugin's skill).

### Step C: Top-5 failure mode check

Apply F1 through F5 from the evaluation guide (the canonical "top 5
failure modes" from the plugin-system research). Each F-item is a
single binary check.

### Step D: Injection-hardening check

Two-tier scan over plugin manifest body:

1. **Tier A (regex)**: scan `description`, `keywords[]`, `metadata.*`
   string values for system-prompt syntax (`<system>`, `[INST]`,
   `### System`), imperative verbs followed by tool/action vocabulary,
   and any pattern matching `injection-regex-library.md`.
2. **Tier B (LLM)**: only if Tier A returns ≥1 hit, escalate to
   manual confirmation. Without LLM access in this skill, surface
   the Tier-A hit at severity Low pending external confirmation; do
   NOT auto-confirm.

### Step E: Marketplace compliance subset

Apply MS-1 through MS-3: kebab-case discipline, no hardcoded
credentials in any inspected file (regex over `plugin.json` and
`marketplace.json`), and meaningful description (length ≥40 chars,
no placeholder text like "TODO" or "Lorem ipsum").

### Step F: Score

For each dimension (Completeness, Goal Alignment, Safety, Metadata),
derive a grade A–F per the canonical rubric (A=0 FAILs; B=≤25%, no
High; C=any High or >25%; D=>50% High; F=>50% total). Compute the
overall grade with weights: Completeness 25%, Goal Alignment 25%,
Safety 30%, Metadata 20%.

## Phase 3 — Output

Emit the certificate to stdout (no file writes — the user copies the
certificate into their preferred report location).

**Complete when**: every dimension (Completeness, Goal Alignment, Safety,
Metadata) carries a non-null A–F grade, every FAIL in Phase 2 produced
a recommendation with `ID:`, `Evidence:` (with file:line), and
`Validation:` lines, and the certificate table has been emitted to
stdout. If any dimension is null or any FAIL lacks a recommendation,
return to Phase 2 Step F before emitting.

```
### Goal
[One sentence: what this plugin should achieve]

### Certificate

| Dimension | Grade | Weight | Key Evidence |
|-----------|-------|--------|--------------|
| Completeness | [grade] | 25% | [checklist IDs] |
| Goal Alignment | [grade] | 25% | [checklist IDs] |
| Safety | [grade] | 30% | [checklist IDs] |
| Metadata | [grade] | 20% | [checklist IDs] |
| **Overall** | **[grade]** | | **[score]** |

### Strengths
- [up to 3 bullet points]

### Recommendations
[For each FAIL with High/Medium impact:]
#### N. [Title] (Impact: [H/M/L], Category: [...], ID: {checklist-item}:{path}:{dim}/v1)
**Evidence:** [exact quote or reference, file:line]
**Why it matters:** [impact explanation]
**Validation:** [how to verify the fix]
**Current:** [current snippet]
**Recommended:** [fixed snippet]
```

## Quality measurement (mandatory before Phase 3)

Without verification, this skill fails at SCOPE-DRIFT (a plugin
declares `skills/`, `agents/`, `hooks/`, or `commands/` in
`plugin.json` but the certificate's components[] list silently omits
a sibling directory present under the plugin root — CL-2 territory,
the canonical plugin failure mode), FABRICATED namespacing findings
(CL-3 flags a collision against `<sibling>/SKILL.md` whose name does
not actually appear in any sibling plugin's manifest), DIMENSION-
GRADE-ABSENCE (a row omits `prompt_engineering` / `context_engineering`
/ `clarity` entirely or renders them as `""` instead of the literal
`null` required for the Plugin type per `references/review-report-
contract.md` §"Dimensions: Rules/MCP/Settings: non-applicable →
null"), and SEVERITY-MISCALIBRATION (a Tier-A injection regex hit
without Tier-B confirmation ships as High when the §"Step D" rule
caps such hits at Low). The three-layer pipeline below catches all
four.

References: CheckEval (arXiv:2403.18771), G-Eval (arXiv:2303.16634),
Position bias in LLM-as-a-Judge (arXiv:2406.07791), IFEval
(arXiv:2311.07911), FollowBench (Jiang et al. ACL 2024), Beyond
Consensus (NUS 2025), `skills/review-claude-config/references/review-
report-contract.md`, `skills/review-claude-config/references/scoring-
rubric.md`, `skills/review-plugin/references/plugin-evaluation-
guide.md`.

This skill is `disallowedTools: Bash, Write, Edit, WebFetch` — the
pipeline cannot run inside this skill's own context. The certificate
emitted to stdout in Phase 3 is the verification input; the
orchestrator (or an external follow-up agent with Bash + Read
grants) captures the certificate to a tempfile and runs the layers
below against it. Embedded scripts are TRUSTED-DATA reference
material for the runner, not for in-skill execution.

### Layer A — mechanical invariants (deterministic, fail-fast)

Run on the captured certificate. STRICT failures block Phase 3
emission; SOFT warnings surface in Output. The applicable dimension
set for Plugin reports is the 4-tuple `{completeness, goal_alignment,
safety, metadata}`; `prompt_engineering`, `context_engineering`, and
`clarity` MUST appear as the literal `null` because the input is a
JSON manifest plus component-tree declaration, not a prompt or a
workflow body.

```bash
python3 - "$REPORT_PATH" "$PLUGIN_ROOT" <<'PY'
import sys, re, json, os
from pathlib import Path

REPORT = Path(sys.argv[1])
ROOT   = sys.argv[2]  # the plugin root passed as $ARGUMENTS, for components[] cross-check

SEVERITY_VOCAB = {"High","Medium","Low"}
DIM_APPLICABLE = {"completeness","goal_alignment","safety","metadata"}
DIM_NULL       = {"prompt_engineering","context_engineering","clarity"}
GRADE_VOCAB    = {"A","B","C","D","F"}
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
if gb and gb.group(1) != "review-plugin":
    errors.append(f"STRICT: generated_by must be 'review-plugin', got '{gb.group(1)}'")
if HOME_RE.search(fm):
    errors.append("STRICT: frontmatter 'target' uses expanded home prefix; must use literal $HOME/")

sections = [s.group(1).strip() for s in re.finditer(r"^##\s+(.+)$", text, re.M)]
order = ["Goal","Certificate","Strengths","Recommendations"]
pos = {k: next((i for i,s in enumerate(sections) if s.startswith(k)), -1) for k in order}
if any(v == -1 for v in pos.values()):
    errors.append(f"STRICT: missing required section heading from {order}; found={sections}")
elif sorted(pos.values()) != list(pos.values()):
    errors.append(f"STRICT: section order violates Goal->Certificate->Strengths->Recommendations")

for dim in DIM_APPLICABLE:
    mm = re.search(rf"\b{dim}\s*:\s*(\S+)", fm)
    if not mm:
        errors.append(f"STRICT: summary missing required dimension '{dim}'")
        continue
    v = mm.group(1).rstrip(",")
    if v not in GRADE_VOCAB and v != "null":
        errors.append(f"STRICT: dimension {dim}='{v}' not in {{A,B,C,D,F,null}}")
for dim in DIM_NULL:
    mm = re.search(rf"\b{dim}\s*:\s*(\S+)", fm)
    if mm:
        v = mm.group(1).rstrip(",")
        if v != "null":
            errors.append(f"STRICT: non-applicable dim {dim}='{v}' must be literal 'null' (not '' or absent)")

findings = re.findall(FIND_RE, text, re.M)
for sev in findings:
    if sev not in SEVERITY_VOCAB:
        errors.append(f"STRICT: finding severity '{sev}' not in {SEVERITY_VOCAB}")
blocks = re.split(r"^####\s+\d+\.", text, flags=re.M)[1:]
for i, b in enumerate(blocks, 1):
    for sub in ["Evidence","Why it matters","Validation"]:
        if not re.search(rf"\b{sub}\b", b):
            errors.append(f"STRICT: finding #{i} missing required sub-block '{sub}'")

# D6 SCOPE_DISCIPLINE — every component under plugin root appears in components[].
# Plugin's components are skills/<name>/SKILL.md, agents/<name>.md, hooks/hooks.json,
# commands/<name>.md (legacy). The certificate must reference each discovered
# component or carry an explicit out-of-scope note.
if ROOT and os.path.isdir(ROOT):
    discovered = set()
    for p in Path(ROOT).glob("skills/*/SKILL.md"):
        discovered.add(str(p.relative_to(ROOT)))
    for p in Path(ROOT).glob("agents/*.md"):
        discovered.add(str(p.relative_to(ROOT)))
    if (Path(ROOT) / "hooks" / "hooks.json").exists():
        discovered.add("hooks/hooks.json")
    for p in Path(ROOT).glob("commands/*.md"):
        discovered.add(str(p.relative_to(ROOT)))
    missing = [c for c in discovered if c not in text]
    if discovered and missing:
        errors.append(f"STRICT: components present under plugin root not referenced in report: {missing}")
    # Also assert the declared plugin.json entries resolve under root.
    pj = Path(ROOT) / ".claude-plugin" / "plugin.json"
    if pj.exists():
        try:
            mj = json.loads(pj.read_text())
            for field in ("skills","agents","commands","hooks"):
                for decl in (mj.get(field) or []):
                    if isinstance(decl, str):
                        if not (Path(ROOT) / decl).exists():
                            errors.append(f"STRICT: plugin.json {field}[] declares '{decl}' but path does not resolve under plugin root")
        except json.JSONDecodeError:
            warns.append("SOFT: .claude-plugin/plugin.json failed to parse for cross-check (Critical finding should already be in report)")

urls  = set(re.findall(URL_RE,  text))
cites = set(c if isinstance(c,str) else c[0] for c in re.findall(CITE_RE, text))
warns.append(f"INFO: urls={len(urls)} cites={len(cites)} (Layer B verifies resolution)")

print(f"=== Layer A — {REPORT.name} ===")
for w in warns:  print(f"warn  {w}")
for e in errors: print(f"FAIL  {e}")
print(f"--- {len(errors)} STRICT, {len(warns)} SOFT ---")
sys.exit(1 if errors else 0)
PY
```

What each metric catches: frontmatter required-fields + `$HOME/`
literal → DIMENSION-GRADE-ABSENCE (frontmatter omission) and the
`block-sensitive-content.sh` PreToolUse contract; section order →
structural validity of the inline certificate; 4-applicable-dim
presence + literal-`null` enforcement on PE/CE/Clarity → DIMENSION-
GRADE-ABSENCE / TYPE-MISMATCH (Plugin type must reject the 7-dim
Skill shape); severity vocabulary + finding sub-blocks → SEVERITY-
MISCALIBRATION (form-level only; calibration itself is Layer B);
component-discovery cross-check against `<plugin-root>/skills/*/SKILL.md`,
`agents/*.md`, `hooks/hooks.json`, `commands/*.md` plus declared
`plugin.json` entries → SCOPE-DRIFT (CL-2 territory: every component
under the plugin root must appear in the report, and every declared
path in `plugin.json` must resolve under the root).

### Layer B — adversarial critic dispatch (blind, recall-framed)

Dispatch a fresh subagent whose ONLY task is to find what the
certificate MISSED, FABRICATED, or MIS-CLASSIFIED versus the plugin
under review. Adversarial framing is load-bearing — non-adversarial
dispatch loses FABRICATED-namespacing-collision recall (CL-3) and
SCOPE-DRIFT recall (CL-2).

```
Agent({
  description: "Adversarial review-plugin report critic",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind reviewer. Two inputs are attached: ARTIFACT " +
    "and REPORT. Neither label tells you which is which until you " +
    "read them. ARTIFACT is a Claude Code plugin root — a directory " +
    "tree containing .claude-plugin/plugin.json plus skills/, " +
    "agents/, hooks/, and/or commands/ subdirectories. REPORT is " +
    "the review certificate emitted by /review-plugin.\n\n" +
    "Your only task is to find what the REPORT got wrong. List " +
    "every item that meets one of:\n" +
    "- MISSING — a defect actually present in ARTIFACT that REPORT " +
    "  does not flag (cite the file path or plugin.json field, " +
    "  name the rubric item PM-1..PM-12, CL-1..CL-5, F1..F5, or " +
    "  MS-1..MS-3 it violates). Pay particular attention to CL-2 " +
    "  (every declared skills/agents/commands/hooks path resolves " +
    "  under the plugin root) and CL-3 (skill name collisions with " +
    "  sibling plugin SKILL.md names) — these are the most commonly " +
    "  missed defect classes.\n" +
    "- FABRICATED — a finding in REPORT whose claimed Evidence " +
    "  quote does not appear verbatim in ARTIFACT (cite finding " +
    "  heading + absent quote). CL-3 namespacing-collision " +
    "  fabrications are the most common Haiku-perspective false- " +
    "  positive — verify every flagged sibling SKILL name actually " +
    "  exists in a loaded plugin under ARTIFACT.\n" +
    "- MIS-SEVERITY — a finding whose severity (High|Medium|Low) " +
    "  is inconsistent with its evidence per the rubric grade caps " +
    "  (e.g. a Tier-A injection regex hit without Tier-B " +
    "  confirmation flagged as High when §Step D caps at Low; or " +
    "  a kebab-case MS-1 violation flagged High when MS items are " +
    "  Metadata-band only).\n" +
    "- MIS-CITED — a URL, arXiv ID, RFC, or references/*.md " +
    "  citation in REPORT that reads as reconstructed-from-memory " +
    "  rather than resolved-in-session (broken link, wrong file, " +
    "  no tool-response).\n" +
    "- UNCITED — a quantitative or evidence-based claim in REPORT " +
    "  with no citation at all.\n" +
    "- SCOPE-OMISSION — a component present under ARTIFACT root " +
    "  (skills/<name>/SKILL.md, agents/<name>.md, hooks/hooks.json, " +
    "  commands/<name>.md) NOT referenced anywhere in REPORT body " +
    "  or summary[].\n" +
    "- TYPE-MISMATCH — REPORT emits a grade (A|B|C|D|F) for " +
    "  prompt_engineering, context_engineering, or clarity; for a " +
    "  Plugin the only valid value for those dimensions is literal " +
    "  `null`.\n\n" +
    "Do not rate quality. Do not praise. Do not propose fixes. " +
    "List items only. Quote the literal sentence, file path, or " +
    "plugin.json field and name which input. Report under 500 " +
    "words.\n\n" +
    "ARTIFACT:\n<paste plugin root contents — plugin.json plus " +
    "directory listing plus each component file>\n\n" +
    "REPORT:\n<paste certificate contents>"
})
```

**Dispatch twice with order swapped** (ARTIFACT↔REPORT label
position) — position bias is the dominant pairwise-judge artifact
(Shi et al. 2024 arXiv:2406.07791). Take the union of items flagged
across both runs.

### Layer C — binary rubric reconciliation

Six binary dimensions, each yes/no, each tied to ≥1 failure class.
Any `NO` blocks Phase 3 emission until resolved.

```
D1 CONVERGENCE_STABILITY  Re-running the skill on the unchanged plugin
                          root produces a byte-identical set of
                          finding_id values at severity in {High,
                          Medium} on the deterministic subset (binary-
                          item finding_ids from PM-1..PM-12, CL-1..CL-5,
                          F1..F5, MS-1..MS-3). N/A when no prior
                          certificate is captured.
                          (Catches: CONVERGENCE-DRIFT)

D2 SEVERITY_JUSTIFIED     Every finding's severity matches its
                          evidence per the rubric §"Grade Caps" + the
                          plugin-evaluation-guide checklist tiers; no
                          Layer-B MIS-SEVERITY item open; Tier-A
                          injection regex hits without Tier-B
                          confirmation never ship above Low (§Step D
                          rule).
                          (Catches: SEVERITY-MISCALIBRATION)

D3 DIMENSION_COVERAGE     All 4 applicable dimensions for Plugin type
                          ({completeness, goal_alignment, safety,
                          metadata}) appear in summary[] with grade in
                          {A,B,C,D,F,null}; the 3 non-applicable
                          dimensions ({prompt_engineering,
                          context_engineering, clarity}) appear as the
                          LITERAL `null` (never `""`, never absent,
                          never a grade). Weights are 25/25/30/20.
                          (Catches: DIMENSION-GRADE-ABSENCE,
                          TYPE-MISMATCH)

D4 EVIDENCE_RESOLVED      Every URL, arXiv ID, RFC, and references/*.md
                          path cited in REPORT was either resolved in
                          the producing session (verifiable from
                          tool-use log) OR carries an explicit
                          `[no web verification]` / `[unverified-url]`
                          marker; no MIS-CITED or UNCITED Layer-B item
                          open.
                          (Catches: CITATION-ROT, UNCITED)

D5 NO_FABRICATED_FINDINGS Every finding's Evidence block contains a
                          literal quote from the plugin.json manifest
                          or a literal file path under the plugin
                          root (skills/<name>/SKILL.md, agents/<name>.md,
                          etc.); no FABRICATED Layer-B item open;
                          every CL-3 namespacing collision cites the
                          actual sibling plugin's SKILL.md path, not
                          a fabricated sibling name (Haiku-fabrication
                          guard).
                          (Catches: FABRICATED namespacing-collision
                          class, FALSE-FIX-PASS)

D6 SCOPE_DISCIPLINE       Every component discovered under the plugin
                          root via Glob (skills/*/SKILL.md,
                          agents/*.md, hooks/hooks.json,
                          commands/*.md) appears in REPORT body or
                          summary[]; every entry declared in
                          plugin.json's skills/agents/commands/hooks
                          fields resolves under the plugin root (CL-2);
                          no Layer-B SCOPE-OMISSION item open. When
                          plugin.json fails to parse, the report
                          carries exactly one Critical finding and no
                          further per-dimension grades (parse-fail =
                          stop).
                          (Catches: SCOPE-DRIFT, CL-2 violations,
                          parse-fail bypass)
```

Map Layer-A failures → D3/D6. Map Layer-B `MISSING` / `FABRICATED`
→ D5. Map `MIS-SEVERITY` → D2. Map `MIS-CITED` / `UNCITED` → D4.
Map `SCOPE-OMISSION` → D6. Map `TYPE-MISMATCH` → D3.

### Reconciliation outcomes

- **All Layer-A STRICT pass + zero Layer-B `MISSING` / `FABRICATED`
  / `SCOPE-OMISSION` / `TYPE-MISMATCH`** → proceed to Phase 3
  emission.
- **Any Layer-A STRICT fail OR any of those Layer-B classes** →
  propose restorations inline (name each finding to add/remove with
  the file path or plugin.json field + rubric citation), re-run
  Layer A on the patched certificate. Max two iterations. If still
  failing at iteration 2, surface to user and do NOT emit the
  certificate to stdout as-final.
- **Only Layer-A SOFT warnings + Layer-B `MIS-SEVERITY` /
  `MIS-CITED` / `UNCITED` items** → record in Phase 3 Output under
  `### Layer-B Findings (Advisory)` and proceed. These do not block
  ship; reviewer triages.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **Calibration drift vs the baseline** — D2 verifies severity is
   internally consistent with cited rubric evidence; it does NOT
   verify that `engineering-baseline.md` or `plugin-evaluation-
   guide.md` itself is calibrated against current best practice. A
   stale baseline (>90 days, per CLAUDE.md) silently inflates High
   counts on Safety without triggering any pipeline layer.
   `/refresh-engineering-baseline` is out-of-band.
2. **Report-vs-tool-use-log audit** — D4's URL set is extracted
   from the certificate text; verifying each citation was actually
   resolved in the producing session requires reading the session
   JSONL under `$HOME/.claude/projects/<project>/<sessionId>.jsonl`.
   The pipeline does not auto-parse JSONL — Layer B asks the critic
   to flag obvious reconstructed-from-memory URLs but cannot prove
   resolution.
3. **Cross-plugin namespacing reality** — CL-3 collision detection
   in D5 requires the critic to know which sibling plugins are
   actually loaded in the consumer's session. The pipeline cannot
   enumerate the consumer's active plugin set offline; it can only
   verify that a flagged sibling SKILL name resolves to a real file
   somewhere on the search path. A real-world collision against a
   plugin that is not on the reviewer's disk is undetectable.
4. **Component behavior** — the skill reviews the manifest and
   component declarations statically; it cannot observe what each
   skill/agent/hook actually does when invoked. A plugin with a
   well-formed `plugin.json` and clean `skills/*/SKILL.md` headers
   may still ship behavior that violates the host's policy at
   runtime. Runtime audit lives in `/audit-trust-chain` and
   `/audit-policy-compliance`, not here.
5. **Tier-B injection confirmation** — §Step D Tier-A regex hits
   ship at Low pending Tier-B (LLM) confirmation, which the read-
   only skill cannot perform. D2 enforces the Low cap, but a true-
   positive injection that needs escalation to High remains capped
   until an external Tier-B pass runs. Reviewer must escalate
   manually when warranted.

The Output report MUST list which residual classes apply when the
critic returns any `UNCERTAIN` flags or when the plugin under review
touches an out-of-pipeline path (unloaded sibling plugin set, novel
injection technique, runtime behavior beyond static manifest, etc.).

## Hard Rules

- **Read-only on every file.** Frontmatter `disallowedTools` enforces
  no Bash/Write/Edit/WebFetch. Findings are surfaced, not auto-fixed.
- **No remote fetches.** Plugin reviews must work offline; remote
  marketplace verification is out of scope for the local skill.
- **Apply the rubric strictly.** Do not inflate grades. Tier-A
  injection hits without Tier-B confirmation are Low only.
- **Every High or Medium recommendation must include evidence (file
  path + line) and a concrete rewrite.**
- **Parse failure = Critical.** Invalid JSON in `plugin.json` is the
  most dangerous finding.
