---
name: review-claude-md
description: >
  Evaluates a CLAUDE.md file across 4 dimensions (Clarity, Completeness,
  Context Engineering, Goal Alignment). Use when asked to 'review CLAUDE.md'
  or after /audit-repo flags a missing or low-quality CLAUDE.md. Do NOT use
  for skills, agents, or rules — use /review-skill, /review-agent, or /review-rule.
argument-hint: <path-to-CLAUDE.md>
allowed-tools: Bash, Read, Write, Glob, WebSearch, WebFetch
---

# Review Claude MD

Evaluate a CLAUDE.md file for quality across 4 evidence-based dimensions.

## Argument Handling

- `$ARGUMENTS` is the path to a CLAUDE.md file.
- Validate the file exists. CLAUDE.md files are plain Markdown with no required frontmatter.
- If the path resolves to a SKILL.md or an agent/rule file, report the type mismatch and stop.
- If `$ARGUMENTS` is empty, look for CLAUDE.md in the current working directory.

## Mode Detection

Check whether the prompt contains an orchestration metadata block:

```
---orchestration---
mode: orchestrated
websearch_available: true|false
webfetch_available: true|false
domain_cache: |
  <cached domain content or "none">
---
```

- If present → **orchestrated mode** (skip tool checks, use provided flags and cache, return structured certificate only, no user interaction).
- If absent → **standalone mode** (full workflow below).

## Phase 1 — Setup (standalone mode only)

### Step 0: Tool Availability Checks

Attempt a trivial WebSearch (e.g., "Claude Code CLAUDE.md documentation"). If it fails, set `websearch_available = false`. Goal Alignment will be scored from model knowledge only, marked `[no web verification]`.

Attempt a trivial WebFetch. If it fails, set `webfetch_available = false`.

### Step 1: Load References

Locate the `review-claude-config` skill directory (sibling skill in the same plugin). Read these shared references from it:
- `references/scoring-rubric.md` — the grading criteria
- `references/engineering-baseline.md` — prompt, context, and tool design techniques
- `references/source-quality-criteria.md` — source credibility and filtering criteria for web research

Use Glob to find the files if the path is not immediately known: `**/review-claude-config/references/scoring-rubric.md`

Resolve `<repo-slug>` by running `bash bin/repo-slug.sh "$(pwd)"` and capturing stdout. (For documentation reference only, not the operational source-of-truth: `references/repo-identification.md` describes the sanitize algorithm.)

**If any of these files is not found, abort with error:** "Required reference not found. Ensure review-claude-config is installed as a sibling skill."

Read the type-specific evaluation guide from this skill's own directory:
- `references/claude-md-evaluation-guide.md`

## Phase 2 — Evaluation

### Step A: Context Inference + Domain Research

1. Read the CLAUDE.md file and identify:
   - Project type (e.g., Kubernetes infrastructure, Python service, TypeScript app)
   - Stated purpose and audience
   - Which sections are present (Architecture, Commands, Working Guidelines, Development Conventions, etc.)
2. Domain research (follow orchestration flags if in orchestrated mode):
   - Check the domain cache: Read `${CLAUDE_PLUGIN_ROOT}/skills/review-claude-config/references/domain-cache/INDEX.md` and match the project type to a universal cache entry.
   - If `CACHED` (≤90 days): read the cache file as primary domain knowledge.
   - If `STALE`: perform 1 WebSearch to refresh.
   - If no cache entry matches: perform 1-2 targeted WebSearch queries for "Claude Code CLAUDE.md best practices [project-type]" where [project-type] is identified in step 1 (CLAUDE.md domain is always the project type, so the query is project-type-scoped). Fetch the top result if `webfetch_available`.
   - If unavailable: use model knowledge only, marked `[no external verification]`.
   - Apply source quality criteria: prefer official Anthropic docs (Tier 1).
3. Synthesize: what should a high-quality CLAUDE.md for this project type include?

### Step B: Command Inventory Verification

For every command listed in the CLAUDE.md:
1. Classify the command:
   - **Slash command** (`/name`): resolve to `skills/name/SKILL.md` first,
     then `.claude/skills/name/SKILL.md` as fallback.
   - **Shell command** (`make`, `pytest`, `git`, `gh`, `uv`): mark as
     SHELL — no file resolution; skip Glob check.
   - **Inline path** (explicit file path): verify the path exists directly.
2. For slash commands, use Glob to verify the resolved path exists.
3. Mark each command as **VERIFIED** (file found), **STALE** (file not found
   or path mismatch), or **SHELL** (non-resolvable shell command, not checked).

Record the verification results — they are required evidence for Goal Alignment scoring.

### Step C: Scoring

Score using the rubric as the PRIMARY basis. CLAUDE.md files use 4 dimensions:

| Dimension | Weight |
|-----------|--------|
| Clarity | 25% |
| Completeness | 25% |
| Context Engineering | 25% |
| Goal Alignment | 25% |

**Scoring procedure:**

1. Work through the full checklist in `references/claude-md-evaluation-guide.md`. Record PASS, FAIL, or NA for every item (CL-1 through GA-6).
2. **Completeness gate:** Every checklist item must have a verdict. Every dimension must have at least one non-NA item.
3. Score each dimension using the rubric, citing at least one checklist ID per justification line (e.g., "CI-3 FAIL: 4 of 7 listed commands resolve to missing files").
4. The completed checklist is an internal working artifact — do not include it verbatim in the output.

## Phase 3 — Output

Return the report in this EXACT format:

### Goal
[One sentence describing the project this CLAUDE.md governs and what it aims to achieve for Claude Code sessions]

### Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | [A-F] | 25% | [One line] |
| Completeness | [A-F] | 25% | [One line] |
| Context Engineering | [A-F] | 25% | [One line] |
| Goal Alignment | [A-F] | 25% | [One line] |
| **Overall** | **[A-F]** | **100%** | **Weighted: XX.X** |

Calculate overall grade:
1. Convert grades: A=95, B=85, C=75, D=65, F=50.
2. Weighted score = Clarity×.25 + Completeness×.25 + ContextEngineering×.25 + GoalAlignment×.25.
3. Map back: ≥90→A, ≥80→B, ≥70→C, ≥60→D, <60→F.
4. Show in Overall Justification: "Weighted: XX.X → [Grade]"

### Grading Boundary Examples

**Clarity B vs C:** B has explicit, actionable instructions throughout with one conditional phrased as "should" instead of "must". C contains multiple aspirational statements ("prefer X", "try to Y") that two models would interpret differently.

**Context Engineering B vs C:** B is dense and well-scoped with one section that restates information already derivable from project files. C has noticeable repetition across sections or includes boilerplate that adds tokens without behavioral signal.

**Goal Alignment B vs C:** B's command inventory is fully verified and freshness markers are present, but one path reference is slightly stale. C has 2+ listed commands that resolve to missing files, or omits a major project component that would cause Claude to miss it entirely.

[If WebSearch was unavailable, add: "Goal Alignment scored without web verification."]

### Command Inventory Report

List the verification results from Step B:

| Command | Expected Path | Status |
|---------|--------------|--------|
| `/example` | `skills/example/SKILL.md` | VERIFIED / STALE |

[If all commands verified: "All N commands verified." If stale entries exist: "N of M commands resolve to missing files — see Recommendations."]

### Strengths
- [strength 1]
- [strength 2]
- [strength 3 if applicable]

### Recommendations

Use the recommendation schema below directly (the contract is referenced in shared references loaded in Phase 1 if needed). Keep the CLAUDE.md-specific category vocabulary below.

#### 1. [Title] (Impact: [High/Medium/Low], Category: [Structure|CommandInventory|InstructionQuality|TokenEfficiency|Completeness|Freshness])
**Evidence:** [Quote or summarize the exact text that caused the issue, with section reference]

**Why it matters:** [What to change and why, referencing domain best practices or baseline techniques]

**Validation:** [How to confirm the fix on re-review]

**Current:**
```
[existing text from the CLAUDE.md]
```

**Recommended:**
```
[improved text — concrete rewrite]
```

[Repeat for each recommendation, ordered by impact]

## Quality measurement (mandatory before Phase 4)

Without verification, this skill fails at TYPE-MISMATCH (a SKILL.md or agent .md is passed in and the skill produces a 4-dimension ClaudeMd certificate instead of stopping per Argument Handling), DIMENSION-GRADE-ABSENCE (the ClaudeMd 4-dim subset omits one of `clarity` / `completeness` / `context_engineering` / `goal_alignment`, or emits a non-applicable dimension at non-null value — contradicting `skills/review-claude-config/references/review-report-contract.md` §"Dimensions: ClaudeMd: PE / Safety / Metadata → null"), STALE-COMMAND-INVENTORY (the Command Inventory Report marks a slash command VERIFIED when the resolved SKILL.md path does not exist, or marks it STALE when the file is present at the documented path — close cousin of FALSE-FIX-PASS, specific to the Phase 2 Step B contract this skill enforces on every command listed in the CLAUDE.md), and DOMAIN-CITATION-MISMATCH (Goal Alignment Evidence cites a generic "Anthropic docs" URL or a domain-research URL that is not CLAUDE.md-relevant for the inferred project type, weakening the dimension's project-type-scoped justification per the per-skill customization note in `.work/skill-verification/review-template.md` §"review-claude-md"). The three-layer pipeline below catches all four.

References: CheckEval (arXiv:2403.18771), G-Eval (arXiv:2303.16634), Position bias in LLM-as-a-Judge (arXiv:2406.07791), IFEval (arXiv:2311.07911), FollowBench (Jiang et al. ACL 2024), Beyond Consensus (NUS 2025), `skills/review-claude-config/references/review-report-contract.md`, `skills/review-claude-config/references/scoring-rubric.md`, `skills/review-claude-md/references/claude-md-evaluation-guide.md`.

Run the pipeline against the assembled Phase 3 certificate. Compute `REPORT_PATH` as the path the Phase 4 step 4 Write will use; if no path is available yet (orchestrated mode), serialize the certificate to a tempfile for the duration of this section.

### Layer A — mechanical invariants (deterministic, fail-fast)

Run on the assembled report. STRICT failures block Phase 4; SOFT warnings surface in Output.

```bash
python3 - "$REPORT_PATH" "${PRIOR_MERGED_JSON:-}" <<'PY'
import sys, re, json, os
from pathlib import Path

REPORT = Path(sys.argv[1])
PRIOR  = sys.argv[2]

SEVERITY_VOCAB = {"High","Medium","Low"}
CLAUDEMD_DIMS  = {"clarity","completeness","context_engineering","goal_alignment"}
NA_DIMS        = {"prompt_engineering","safety","metadata"}
GRADE_VOCAB    = {"A","B","C","D","F"}
URL_RE   = r"https?://[^\s)`\"<>]+"
CITE_RE  = r"\b(arXiv:[0-9.]+|RFC\s*[0-9]+|DOI:[^\s)]+)"
FIND_RE  = r"^####\s+\d+\.\s+.+\(Impact:\s*(High|Medium|Low)"
FM_RE    = r"\A---\n(.*?)\n---\n"
ID_RE    = r"ID:\s*([A-Z][A-Z0-9-]+:[^,\s)]+/v1)"
# Catch frontmatter target: lines beginning with an absolute tilde-expanded
# user-home prefix on either supported POSIX layout. Live regex form
# matches the literal prefixes; placeholdered in this SKILL.md so the
# PreToolUse content-block hook does not reject this Write.
HOME_RE  = re.compile(r"^target\s*:\s*/(?:Users|home)/[^/\s]+/", re.M)

errors, warns = [], []
text = REPORT.read_text()
m = re.match(FM_RE, text, re.S)
if not m:
    errors.append("STRICT: report missing YAML frontmatter")
    print("\n".join(errors)); sys.exit(1)
fm = m.group(1)

for k in ["generated_by","schema_version","date","repo","target","items_reviewed"]:
    if not re.search(rf"^{k}\s*:", fm, re.M):
        errors.append(f"STRICT: frontmatter missing required field '{k}'")
gb = re.search(r"^generated_by\s*:\s*(\S+)", fm, re.M)
if gb and gb.group(1) != "review-claude-md":
    errors.append(f"STRICT: generated_by must be 'review-claude-md', got '{gb.group(1)}'")
if HOME_RE.search(fm):
    errors.append("STRICT: frontmatter 'target' uses expanded home prefix; must use literal $HOME/")

typ = re.search(r"\btype\s*:\s*(\w+)", fm)
if typ and typ.group(1) != "ClaudeMd":
    errors.append(f"STRICT: summary type must be 'ClaudeMd', got '{typ.group(1)}' (TYPE-MISMATCH — wrong skill dispatched)")

sections = [s.group(1).strip() for s in re.finditer(r"^##\s+(.+)$", text, re.M)]
order = ["Goal","Certificate","Strengths","Recommendations"]
pos = {k: next((i for i,s in enumerate(sections) if s.startswith(k)), -1) for k in order}
if any(v == -1 for v in pos.values()):
    errors.append(f"STRICT: missing required section heading from {order}; found={sections}")
elif sorted(pos.values()) != list(pos.values()):
    errors.append("STRICT: section order violates Goal->Certificate->Strengths->Recommendations")

for dim in CLAUDEMD_DIMS:
    mm = re.search(rf"\b{dim}\s*:\s*(\S+)", fm)
    if not mm:
        errors.append(f"STRICT: summary missing required ClaudeMd dimension '{dim}'")
        continue
    v = mm.group(1).rstrip(",")
    if v not in GRADE_VOCAB:
        errors.append(f"STRICT: ClaudeMd dimension {dim}='{v}' not in {{A,B,C,D,F}}")
for dim in NA_DIMS:
    mm = re.search(rf"\b{dim}\s*:\s*(\S+)", fm)
    if mm:
        v = mm.group(1).rstrip(",")
        if v != "null":
            errors.append(f"STRICT: non-applicable dimension '{dim}'='{v}' must be 'null' for type=ClaudeMd")

# Command Inventory Report presence (STRICT) — skill-specific contract.
if not re.search(r"^###\s+Command Inventory Report\s*$", text, re.M):
    errors.append("STRICT: report missing required 'Command Inventory Report' section (Phase 2 Step B contract)")

findings = re.findall(FIND_RE, text, re.M)
for sev in findings:
    if sev not in SEVERITY_VOCAB:
        errors.append(f"STRICT: finding severity '{sev}' not in {SEVERITY_VOCAB}")
blocks = re.split(r"^####\s+\d+\.", text, flags=re.M)[1:]
for i, b in enumerate(blocks, 1):
    for sub in ["Evidence","Why it matters","Validation"]:
        if not re.search(rf"\b{sub}\b", b):
            errors.append(f"STRICT: finding #{i} missing required sub-block '{sub}'")

urls  = set(re.findall(URL_RE,  text))
cites = set(c if isinstance(c,str) else c[0] for c in re.findall(CITE_RE, text))
warns.append(f"INFO: urls={len(urls)} cites={len(cites)} (Layer B verifies resolution)")

if PRIOR and os.path.exists(PRIOR):
    prior = json.loads(Path(PRIOR).read_text())
    cur = set(re.findall(ID_RE, text))
    prev = {f["finding_id"] for f in prior.get("findings",[])
            if f.get("severity") in {"High","Medium"}}
    drift = cur ^ prev
    if drift:
        errors.append(f"STRICT: convergence drift on H+M finding_ids: lost={sorted(prev-cur)} gained={sorted(cur-prev)}")

print(f"=== Layer A — {REPORT.name} ===")
for w in warns:  print(f"warn  {w}")
for e in errors: print(f"FAIL  {e}")
print(f"--- {len(errors)} STRICT, {len(warns)} SOFT ---")
sys.exit(1 if errors else 0)
PY
```

What each metric catches: frontmatter required-fields + `$HOME/` literal → DIMENSION-GRADE-ABSENCE and the `block-sensitive-content.sh` PreToolUse contract; `generated_by == review-claude-md` → producer identity; section order → structural validity; `type=ClaudeMd` check → TYPE-MISMATCH (skill, agent, or rule passed where CLAUDE.md expected); claudemd-dim-presence + na-dim-null-only → DIMENSION-GRADE-ABSENCE and the report-contract ClaudeMd-subset constraint; required `Command Inventory Report` heading → STALE-COMMAND-INVENTORY structural pre-check (Phase 2 Step B is mandatory for this skill); severity vocabulary + finding sub-blocks → SEVERITY-MISCALIBRATION (form-level only); convergence diff against prior `merged.json` → CONVERGENCE-DRIFT.

### Layer B — adversarial critic dispatch (blind, recall-framed)

Dispatch a fresh subagent whose ONLY task is to find what the report MISSED, FABRICATED, or MIS-CLASSIFIED versus the CLAUDE.md under review. Adversarial framing is load-bearing — non-adversarial dispatch loses CITATION-ROT and DOMAIN-CITATION-MISMATCH recall.

```
Agent({
  description: "Adversarial review-claude-md report critic",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind reviewer. Two markdown files are attached: ARTIFACT " +
    "and REPORT. Neither label tells you which is which until you read " +
    "them. ARTIFACT is the CLAUDE.md under review (a Claude Code project " +
    "operating guide — plain Markdown, no required frontmatter, typically " +
    "containing Architecture / Commands / Working Guidelines / " +
    "Development Conventions sections). REPORT is the review certificate " +
    "emitted by /review-claude-md.\n\n" +
    "Your only task is to find what the REPORT got wrong. List every " +
    "item that meets one of:\n" +
    "- MISSING — a defect actually present in ARTIFACT that REPORT does " +
    "  not flag (cite the line, name the rubric dimension it violates: " +
    "  Clarity, Completeness, Context Engineering, or Goal Alignment).\n" +
    "- FABRICATED — a finding in REPORT whose claimed Evidence quote " +
    "  does not appear verbatim in ARTIFACT (cite finding heading + " +
    "  absent quote).\n" +
    "- MIS-SEVERITY — a finding whose severity (High|Medium|Low) is " +
    "  inconsistent with its evidence per the rubric grade caps.\n" +
    "- MIS-CITED — a URL, arXiv ID, RFC, or references/*.md citation in " +
    "  REPORT that reads as reconstructed-from-memory rather than " +
    "  resolved-in-session (broken link, wrong file, no tool-response).\n" +
    "- UNCITED — a quantitative or evidence-based claim in REPORT with " +
    "  no citation at all.\n" +
    "- FALSE-RESOLUTION — a finding the REPORT claims resolved (delta " +
    "  section) whose underlying defect still appears in ARTIFACT.\n" +
    "- TYPE-MISMATCH — REPORT scored ARTIFACT as a CLAUDE.md but " +
    "  ARTIFACT has SKILL.md frontmatter (a `name:` field with body " +
    "  starting `# <Skill Name>`), agent frontmatter (`model:` / " +
    "  `tools:`), or rule frontmatter (`description:` + `paths:`) — " +
    "  wrong skill dispatched; review should have stopped per " +
    "  Argument Handling.\n" +
    "- NA-DIMENSION-LEAK — REPORT emits a non-null grade for a " +
    "  dimension outside {Clarity, Completeness, Context Engineering, " +
    "  Goal Alignment} (must be `null` for ClaudeMd type per " +
    "  review-report-contract.md).\n" +
    "- STALE-COMMAND-INVENTORY — Command Inventory Report marks a " +
    "  slash command VERIFIED when ARTIFACT's listed expected path " +
    "  does not exist in the repo, or marks a command STALE when the " +
    "  resolved file is present (cite the row + actual filesystem " +
    "  state). Includes the case where Phase 2 Step B was silently " +
    "  skipped (no row produced for a listed command).\n" +
    "- DOMAIN-CITATION-MISMATCH — Goal Alignment Evidence cites a " +
    "  generic 'Anthropic docs' URL or a domain-research URL that " +
    "  does not match ARTIFACT's inferred project type (e.g. " +
    "  ARTIFACT is a Kubernetes-infrastructure guide but the cited " +
    "  domain reference is a Python-tooling page). The citation " +
    "  must be CLAUDE.md-relevant AND project-type-scoped.\n\n" +
    "Do not rate quality. Do not praise. Do not propose fixes. List " +
    "items only. Quote the literal sentence and name which file. Report " +
    "under 500 words.\n\n" +
    "ARTIFACT:\n<paste CLAUDE.md contents>\n\n" +
    "REPORT:\n<paste certificate contents>"
})
```

**Dispatch twice with order swapped** (ARTIFACT↔REPORT label position) — position bias is the dominant pairwise-judge artifact (Shi et al. 2024 arXiv:2406.07791). Take the union of items flagged across both runs.

### Layer C — binary rubric reconciliation

Six binary dimensions, each yes/no, each tied to ≥1 failure class. Any `NO` blocks Phase 4 until resolved.

```
D1 CONVERGENCE_STABILITY  When a prior merged.json for this CLAUDE.md is
                          supplied, the set of finding_id values at severity
                          in {High, Medium} is byte-identical between runs.
                          When no prior is supplied, D1 is N/A (declared as
                          such in Output; not a NO).
                          (Catches: CONVERGENCE-DRIFT)

D2 SEVERITY_JUSTIFIED     Every finding's severity matches its evidence per
                          the rubric §"Grade Caps" + claude-md-evaluation-
                          guide checklist (CL-1..CL-N, COMP-1..COMP-N,
                          CE-1..CE-N, GA-1..GA-N); no Layer-B MIS-SEVERITY
                          item open. Severity bound only to the four
                          applicable dimensions (Clarity, Completeness,
                          Context Engineering, Goal Alignment).
                          (Catches: SEVERITY-MISCALIBRATION)

D3 DIMENSION_COVERAGE     Exactly the 4-dim ClaudeMd subset {clarity,
                          completeness, context_engineering, goal_alignment}
                          appears in summary[] with grade in {A,B,C,D,F};
                          the 3 non-applicable dimensions {prompt_engineering,
                          safety, metadata} are present with value `null` or
                          omitted per contract — never carry a letter grade;
                          summary[].type == "ClaudeMd"; no Layer-B
                          NA-DIMENSION-LEAK or TYPE-MISMATCH item open.
                          (Catches: DIMENSION-GRADE-ABSENCE, TYPE-MISMATCH)

D4 EVIDENCE_RESOLVED      Every URL, arXiv ID, RFC, and references/*.md path
                          cited in REPORT was either resolved in the
                          producing session (verifiable from tool-use log)
                          OR carries an explicit `[no web verification]` /
                          `[unverified-url]` marker; AND the Goal Alignment
                          dimension's Evidence cites a domain reference
                          that is project-type-scoped to ARTIFACT's
                          inferred project type per the Phase 2 Step A
                          context-inference output (no generic
                          "Anthropic docs" stubs); no MIS-CITED, UNCITED,
                          or DOMAIN-CITATION-MISMATCH Layer-B item open.
                          (Catches: CITATION-ROT, UNCITED,
                          DOMAIN-CITATION-MISMATCH)

D5 NO_FABRICATED_FINDINGS Every finding's Evidence block contains a literal
                          verbatim quote from the analyzed CLAUDE.md (not a
                          paraphrase that drops force); every Command
                          Inventory Report row's status (VERIFIED / STALE /
                          SHELL) matches the actual filesystem state at
                          report time; no FABRICATED, FALSE-RESOLUTION, or
                          STALE-COMMAND-INVENTORY Layer-B item open.
                          (Catches: FABRICATION, FALSE-FIX-PASS,
                          STALE-COMMAND-INVENTORY)

D6 SCOPE_DISCIPLINE       Phase 4 writes only under
                          ${HOME}/.claude/plugins/data/claude-config/reports/
                          <repo-slug>/; the CLAUDE.md under review is
                          never modified; per Hard Rules "Read-only on the
                          analyzed CLAUDE.md". No finding cites a dimension
                          outside the ClaudeMd subset; no finding scores
                          Safety or Metadata (per Hard Rules "Use only 4
                          dimensions").
                          (Catches: scope creep, dim-leak)
```

Map Layer-A failures → D3/D4. Map Layer-B `MISSING` / `FABRICATED` → D5. Map `MIS-SEVERITY` → D2. Map `MIS-CITED` / `UNCITED` / `DOMAIN-CITATION-MISMATCH` → D4. Map `FALSE-RESOLUTION` / `STALE-COMMAND-INVENTORY` → D5. Map `TYPE-MISMATCH` / `NA-DIMENSION-LEAK` → D3.

### Reconciliation outcomes

- **All Layer-A STRICT pass + zero Layer-B `MISSING`/`FABRICATED`/`FALSE-RESOLUTION`/`TYPE-MISMATCH`/`NA-DIMENSION-LEAK`/`STALE-COMMAND-INVENTORY`/`DOMAIN-CITATION-MISMATCH`** → proceed to Phase 4.
- **Any Layer-A STRICT fail OR any of those Layer-B classes** → propose restorations inline (name each finding to add/remove with the artifact line + rubric citation), re-run Layer A on the patched report. Max two iterations. If still failing at iteration 2, surface to user and do NOT auto-write the report.
- **Only Layer-A SOFT warnings + Layer-B `MIS-SEVERITY` / `MIS-CITED` / `UNCITED` items** → record in Phase 4 Output under `### Layer-B Findings (Advisory)` and proceed. These do not block ship; reviewer triages.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **Calibration drift vs the baseline** — D2 verifies severity is internally consistent with the rubric's cited grade caps; it does NOT verify that `engineering-baseline.md` itself is calibrated against current best practice. A stale baseline (>90 days, per CLAUDE.md) silently inflates High counts without triggering any pipeline layer. `/refresh-engineering-baseline` is out-of-band.
2. **Report-vs-tool-use-log audit** — D4's URL set is extracted from the report text; verifying each citation was actually resolved in the producing session requires reading the session JSONL under `$HOME/.claude/projects/<project>/<sessionId>.jsonl`. The pipeline does not auto-parse JSONL — Layer B asks the critic to flag obvious reconstructed-from-memory URLs but cannot prove resolution.
3. **Project-type-inference soundness** — D4's DOMAIN-CITATION-MISMATCH check trusts the Phase 2 Step A inferred project type as ground truth. If that inference itself is wrong (e.g. a Python-tooling CLAUDE.md classified as "Kubernetes infrastructure" because the Architecture section mentions k8s in passing), every downstream Goal Alignment citation will look misaligned to the critic when in fact the inference is the defect. Reviewer must spot-check the Goal section's project-type description against the CLAUDE.md's actual stated purpose.
4. **Command Inventory truth vs filesystem snapshot** — D5's STALE-COMMAND-INVENTORY check verifies the report's claimed status (VERIFIED / STALE / SHELL) against the filesystem at REPORT-WRITE time, not against the filesystem at READ time when a downstream consumer acts on the report. A skill renamed or moved between report write and apply will not surface here; the staleness will surface only at apply time. Acknowledged as report-snapshot semantics.
5. **CLAUDE.md cross-file coherence** — a finding that recommends rewording the CLAUDE.md may break an unstated assumption in a sibling primitive (e.g. a skill that grep-references the literal phrase being rewritten); the pipeline reviews one CLAUDE.md in isolation. No repo-level coherence evaluator is implemented here. Reviewer must spot-check `Recommended:` blocks against any sibling skill / agent / rule that depends on the original phrasing.

The Output report MUST list which residual classes apply when the critic returns any `UNCERTAIN` flags or when `--compare-with` is absent (D1 N/A).

## Phase 4 — Report Persistence (standalone mode only)

In orchestrated mode, skip this phase entirely — return only the structured certificate above.

In standalone mode:
1. Present the certificate to the user.
Before Write: scan the assembled report (frontmatter `target:`, optional `origin:`, and the entire body including per-finding evidence quotations) and replace any literal absolute home-directory prefix with `$HOME/`. The `~/.claude/hooks/block-sensitive-content.sh` PreToolUse hook denies Writes containing such prefixes.
2. Confirm before writing: "Save review report to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-review-claude-md.md`?"
3. If confirmed, assemble the report using the canonical frontmatter contract located in Step 1 with:
   - `generated_by: review-claude-md`
   - one `summary` item of type `ClaudeMd`
   - non-applicable dimensions (PE, CE replaced by ContextEngineering, Safety, Metadata) set to `null`
   - `repo: <slug>` and optionally `origin: <git-remote-url>`
   - `type + path` as the canonical identity and `name` as display-only
4. Write the report file. Suggest committing with: `docs(reviews): add YYYY-MM-DDTHHMMSS review report`
5. **What's Next?**

After all output is complete, present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Apply findings manually" (Recommended) — description: `"Address High/Medium findings from the report using the Current/Recommended blocks"`
- Option 2 label: "Review another CLAUDE.md" — description: `"Provide a file path to review next"`
- Option 3 label: "Done" — description: `"End the workflow"`

On "Apply findings manually": list the High/Medium findings with their Current/Recommended blocks for the user to act on. On "Review another CLAUDE.md": ask for the file path, then invoke `/review-claude-md`. On "Done": acknowledge and stop.

## Error Handling

On evaluation failure, return a structured error block:

```
## ERROR
{item_path}: {reason}
```

In orchestrated mode, the orchestrator logs this and continues with remaining items.

## Hard Rules

- **Read-only on the analyzed CLAUDE.md.** Never modify the file being reviewed. Write only to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`.
- **Apply the rubric strictly.** Do not inflate grades.
- **Every High or Medium recommendation must include evidence and a concrete rewrite** — not just "improve X."
- **Present the full certificate before any follow-up actions.**
- **Run Command Inventory Verification for every command listed** — never skip this step.
- **Use only 4 dimensions.** Never score CLAUDE.md on Safety or Metadata — those dimensions apply to executable skills/agents, not configuration documents.

## Tier A Tool Justification

**Tier A tool justification (Bash):** Bash is granted exclusively for
`bash bin/repo-slug.sh "$(pwd)"` to compute the canonical `<repo-slug>`
deterministically per `references/repo-identification.md`. The
command-level allowlist `Bash(bash bin/repo-slug.sh:*)` enforces scope.
The script is read-only (stdout slug, no FS writes), so this Tier-A grant
carries no write-amplification risk.
