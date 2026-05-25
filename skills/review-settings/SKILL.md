---
name: review-settings
description: >
  Evaluates Claude Code settings.json (deny-rules, env-vars, statusline)
  across 4 dimensions (Completeness, Goal Alignment, Safety, Metadata).
  Use when asked to 'review settings', 'review settings.json', or
  'check settings'. Do NOT use for .mcp.json, skills, agents, rules, or hooks.
argument-hint: <path-to-settings.json>
allowed-tools: Bash, Read, Write, Glob, Grep, WebSearch
---

# Review Settings

Evaluate a Claude Code `settings.json` for quality across 4 evidence-based dimensions. Project-level scope by default (`.claude/settings.json`). Standalone mode accepts any explicit path (including user-level `~/.claude/settings.json`).

## Argument Handling

- `$ARGUMENTS` is a path to a `settings.json` file.
- If given a directory, look for `.claude/settings.json` in that directory.
- If `.claude/settings.local.json` also exists, read both and note local overrides.
- If no settings file found, report the error and stop.
- **Parse the JSON first.** Invalid JSON silently disables ALL permission rules — this is a Critical finding.

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

- If present → **orchestrated mode** (return structured certificate only).
- If absent → **standalone mode** (full workflow below).

## Phase 1 — Setup (standalone mode only)

1. **Load references.** Read:
   - Scoring rubric: Glob `**/review-claude-config/references/scoring-rubric.md`
   - Source quality criteria: Glob `**/review-claude-config/references/source-quality-criteria.md`
   - Repo identification: Resolve `<repo-slug>` by running `bash bin/repo-slug.sh "$(pwd)"` and capturing stdout. (For documentation reference only, not the operational source-of-truth: `references/repo-identification.md` describes the sanitize algorithm.)
   - Settings evaluation guide: `references/settings-evaluation-guide.md`

2. **Probe tool availability.** Test WebSearch with a trivial query. Record `websearch_available`.

## Phase 2 — Evaluation

### Step A: Context Inference + Domain Research

1. Read the settings file. Parse JSON. If parse fails → Critical finding, stop.
2. Identify project context: read `CLAUDE.md` or `README.md` if available.
3. Domain research:
   - Check domain cache: Read `${CLAUDE_PLUGIN_ROOT}/skills/review-claude-config/references/domain-cache/INDEX.md`.
   - If `CACHED`: use cache. If `STALE`: refresh via WebSearch.
   - If no match: perform 1-2 targeted WebSearch queries for Claude Code settings security best practices.
   - If unavailable: use model knowledge only, marked `[no external verification]`.
4. Synthesize: what security posture should this project's settings have?

### Step B: Checklist Evaluation

1. Load `references/settings-evaluation-guide.md`.
2. Evaluate every checklist item: PASS | FAIL | NA.
3. If `.claude/settings.local.json` exists, check for scope conflicts with main settings.
4. Score each dimension using the rubric. Cite evidence before grading.
   - Grade derivation: A=0 FAILs; B=≤25% (no High); C=any High or >25%; D=>50% High; F=>50% total.
5. Calculate overall grade: Completeness 25%, Goal Alignment 25%, Safety 30%, Metadata 20%.

### Step C: Output

Produce the certificate (same format as review-mcp-server).

## Quality measurement (mandatory before Phase 3)

Without verification, this skill fails at SEVERITY-MISCALIBRATION (a fabricated `Critical` finding fires on a valid JSON manifest because a perspective re-litigates a Safety item that the rubric resolves to a lower band — D5 high relevance per `.work/skill-verification/review-template.md §"### review-settings"`), DIMENSION-GRADE-ABSENCE (a row omits `prompt_engineering` / `context_engineering` / `clarity` entirely or renders them as `""` instead of the literal `null` required for type=`Settings` by `references/review-report-contract.md` §"Dimensions: Rules/MCP/Settings: non-applicable → null"), and MISSING Critical on JSON parse failure (the skill's contract states parse-fail = single Critical finding + stop; a report that grades a parse-fail manifest as anything other than that single Critical violates the contract). The three-layer pipeline below catches all three.

References: CheckEval (arXiv:2403.18771), G-Eval (arXiv:2303.16634), Position bias in LLM-as-a-Judge (arXiv:2406.07791), IFEval (arXiv:2311.07911), FollowBench (Jiang et al. ACL 2024), Beyond Consensus (NUS 2025), `skills/review-claude-config/references/review-report-contract.md`, `skills/review-claude-config/references/scoring-rubric.md`, `references/settings-evaluation-guide.md`.

Run the pipeline against the assembled Phase 2 Step C certificate. Compute `REPORT_PATH` as the path the Phase 3 step 1 Write will use; if no path is available yet (orchestrated mode, no report write), serialize the certificate to a tempfile for the duration of this section. `SETTINGS_JSON_PATH` is the `settings.json` under review; `SETTINGS_LOCAL_JSON_PATH` is the optional `.claude/settings.local.json` (empty string when absent).

### Layer A — mechanical invariants (deterministic, fail-fast)

Run on the assembled report. STRICT failures block Phase 3; SOFT warnings surface in Output. The applicable dimension set for Settings reports is the 4-tuple `{completeness, goal_alignment, safety, metadata}`; `prompt_engineering`, `context_engineering`, and `clarity` MUST appear as the literal `null` (never `""`, never absent) because the input is a JSON config, not a prompt and not free-prose.

```bash
python3 - "$REPORT_PATH" "$SETTINGS_JSON_PATH" "$SETTINGS_LOCAL_JSON_PATH" <<'PY'
import sys, re, json, os
from pathlib import Path

REPORT  = Path(sys.argv[1])
SETJ    = sys.argv[2]                       # settings.json under review
LOCALJ  = sys.argv[3] if len(sys.argv) > 3 else ""  # optional settings.local.json

SEVERITY_VOCAB = {"High","Medium","Low"}
DIM_APPLICABLE = {"completeness","goal_alignment","safety","metadata"}
DIM_NULL       = {"prompt_engineering","context_engineering","clarity"}
GRADE_VOCAB    = {"A","B","C","D","F"}
URL_RE   = r"https?://[^\s)`\"<>]+"
CITE_RE  = r"\b(arXiv:[0-9.]+|RFC\s*[0-9]+|DOI:[^\s)]+)"
FIND_RE  = r"^####\s+\d+\.\s+.+\(Impact:\s*(High|Medium|Low)"
FM_RE    = r"\A---\n(.*?)\n---\n"
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
if gb and gb.group(1) != "review-settings":
    errors.append(f"STRICT: generated_by must be 'review-settings', got '{gb.group(1)}'")
if HOME_RE.search(fm):
    errors.append("STRICT: frontmatter 'target' uses expanded home prefix; must use literal $HOME/")

sections = [s.group(1).strip() for s in re.finditer(r"^##\s+(.+)$", text, re.M)]
order = ["Goal","Certificate","Strengths","Recommendations"]
pos = {k: next((i for i,s in enumerate(sections) if s.startswith(k)), -1) for k in order}
if any(v == -1 for v in pos.values()):
    errors.append(f"STRICT: missing required section heading from {order}; found={sections}")
elif sorted(pos.values()) != list(pos.values()):
    errors.append("STRICT: section order violates Goal->Certificate->Strengths->Recommendations")

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

# Parse-fail contract: when SETTINGS_JSON_PATH does not parse, the report MUST
# carry exactly one Critical/High finding citing parse failure and no further
# per-dimension grades (per skill Hard Rules: "Parse failure = Critical").
parse_failed = False
if SETJ and os.path.exists(SETJ):
    try:
        json.loads(Path(SETJ).read_text())
    except json.JSONDecodeError:
        parse_failed = True
if parse_failed:
    if not re.search(r"\b(invalid JSON|parse fail|JSONDecodeError|fails to parse)\b", text, re.I):
        errors.append("STRICT: SETTINGS_JSON_PATH fails to parse but report does not surface a parse-failure finding (Hard Rule: parse fail = Critical)")

# settings.local.json conflict-scan: when a local overlay exists, the body
# MUST mention a conflict / overlay / override scan note per template
# §"### review-settings" Layer A specifics.
if LOCALJ and os.path.exists(LOCALJ):
    if not re.search(r"settings\.local\.json|local override|local overlay|scope conflict", text, re.I):
        errors.append("STRICT: settings.local.json present but report body lacks the conflict / overlay / override scan note")

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

What each metric catches: frontmatter required-fields + `$HOME/` literal check → DIMENSION-GRADE-ABSENCE and the `block-sensitive-content.sh` PreToolUse contract; section order → structural validity; 4-applicable-dim presence + literal-`null` enforcement on PE/CE/Clarity → DIMENSION-GRADE-ABSENCE / TYPE-MISMATCH (Settings type must reject the 7-dim Skill shape); severity vocabulary + finding sub-blocks → SEVERITY-MISCALIBRATION (form-level only); parse-fail contract → MISSING Critical on JSON parse failure; settings.local.json conflict-scan note → overlay-drift detection per the template's review-settings Layer A specifics.

### Layer B — adversarial critic dispatch (blind, recall-framed)

Dispatch a fresh subagent whose ONLY task is to find what the report MISSED, FABRICATED, or MIS-CLASSIFIED versus the `settings.json` (and optional `settings.local.json` overlay) under review. Adversarial framing is load-bearing — non-adversarial dispatch loses FABRICATED-Critical and CITATION-ROT recall.

```
Agent({
  description: "Adversarial review-settings report critic",
  subagent_type: "general-purpose",
  prompt:
    "You are a blind reviewer. Two or three files are attached: " +
    "ARTIFACT (a Claude Code settings.json), optional ARTIFACT-LOCAL " +
    "(a sibling settings.local.json overlay), and REPORT (the review " +
    "certificate emitted by /review-settings). Neither ARTIFACT/REPORT " +
    "label tells you which is which until you read them.\n\n" +
    "Your only task is to find what the REPORT got wrong. List every " +
    "item that meets one of:\n" +
    "- MISSING — a defect actually present in ARTIFACT (or the " +
    "  ARTIFACT+ARTIFACT-LOCAL merged view) that REPORT does not " +
    "  flag (cite the JSON path, name the rubric dimension it " +
    "  violates). Pay particular attention to: invalid JSON that the " +
    "  report fails to surface as a Critical finding (Hard Rule: " +
    "  parse failure = Critical; invalid JSON silently disables ALL " +
    "  permission rules); permissions.allow entries that grant tools " +
    "  without command-level scoping; missing permissions.deny rules " +
    "  on sensitive paths (.env, .ssh, .kube, *.key, *.pem); hooks " +
    "  with unbounded shell expansion; env vars that leak secrets " +
    "  into the model context; scope conflicts between settings.json " +
    "  and settings.local.json that the report does not call out.\n" +
    "- FABRICATED — a finding in REPORT whose claimed Evidence quote " +
    "  does not appear verbatim in ARTIFACT or ARTIFACT-LOCAL (cite " +
    "  finding heading + absent quote). A Critical fabricated on a " +
    "  valid-and-parseable JSON manifest is the highest-impact " +
    "  false-positive — verify every flagged JSON key/value appears " +
    "  literally in ARTIFACT(-LOCAL).\n" +
    "- MIS-SEVERITY — a finding whose severity (High|Medium|Low) is " +
    "  inconsistent with its evidence per the rubric grade caps and " +
    "  the settings-evaluation-guide.md scope-tiers (Safety is " +
    "  weighted 30% per the skill's overall-grade formula; do not " +
    "  inflate Low-tier scope items to High).\n" +
    "- MIS-CITED — a URL, arXiv ID, RFC, or references/*.md citation " +
    "  in REPORT that reads as reconstructed-from-memory rather than " +
    "  resolved-in-session (broken link, wrong file, no tool-response).\n" +
    "- UNCITED — a quantitative or evidence-based claim in REPORT " +
    "  with no citation at all.\n" +
    "- OVERLAY-DRIFT — REPORT does not mention settings.local.json " +
    "  even though ARTIFACT-LOCAL is present and overrides a field " +
    "  in ARTIFACT (e.g. local broadens a permissions rule that " +
    "  main settings denies). The skill's Phase 2 Step B explicitly " +
    "  requires scope-conflict reporting when the overlay exists.\n" +
    "- TYPE-MISMATCH — REPORT emits a grade (A|B|C|D|F) for " +
    "  prompt_engineering, context_engineering, or clarity; for a " +
    "  Settings file the only valid value for those dimensions is " +
    "  literal `null` (input is JSON, not prose).\n\n" +
    "Do not rate quality. Do not praise. Do not propose fixes. List " +
    "items only. Quote the literal sentence or JSON path and name " +
    "which file. Report under 500 words.\n\n" +
    "ARTIFACT:\n<paste settings.json contents>\n\n" +
    "ARTIFACT-LOCAL:\n<paste settings.local.json contents or 'absent'>\n\n" +
    "REPORT:\n<paste certificate contents>"
})
```

**Dispatch twice with order swapped** (ARTIFACT↔REPORT label position; keep ARTIFACT-LOCAL in its original slot) — position bias is the dominant pairwise-judge artifact (Shi et al. 2024 arXiv:2406.07791). Take the union of items flagged across both runs.

### Layer C — binary rubric reconciliation

Six binary dimensions, each yes/no, each tied to ≥1 failure class. Any `NO` blocks Phase 3 until resolved.

```
D1 CONVERGENCE_STABILITY  Re-running the skill on the unchanged settings.json
                          (and unchanged settings.local.json if present)
                          produces a byte-identical set of finding_id values
                          at severity in {High, Medium} on the deterministic
                          subset (binary-item finding_ids from the rubric).
                          N/A when no prior report exists in the archive.
                          (Catches: CONVERGENCE-DRIFT)

D2 SEVERITY_JUSTIFIED     Every finding's severity matches its evidence per
                          the rubric §"Grade Caps" + the settings-evaluation-
                          guide.md scope-tiers; no Layer-B MIS-SEVERITY item
                          open. Safety dimension is weighted highest (30% of
                          overall per Phase 2 Step B) — Low-tier scope items
                          MUST NOT inflate to High solely on Safety weight.
                          A Critical finding fires ONLY on JSON parse failure
                          or an equivalently load-bearing failure named in the
                          evaluation guide.
                          (Catches: SEVERITY-MISCALIBRATION, fabricated-Critical
                          false-positive class)

D3 DIMENSION_COVERAGE     All 4 applicable dimensions for Settings type
                          ({completeness, goal_alignment, safety, metadata})
                          appear in summary[] with grade in {A,B,C,D,F,null};
                          the 3 non-applicable dimensions
                          ({prompt_engineering, context_engineering, clarity})
                          appear as the LITERAL `null` (never `""`, never
                          absent, never a grade). Weights are 25/25/30/20.
                          (Catches: DIMENSION-GRADE-ABSENCE, TYPE-MISMATCH)

D4 EVIDENCE_RESOLVED      Every URL, arXiv ID, RFC, and references/*.md path
                          cited in REPORT was either resolved in the producing
                          session (verifiable from the tool-use log) OR carries
                          an explicit `[no web verification]` /
                          `[unverified-url]` marker; no MIS-CITED or UNCITED
                          Layer-B item open.
                          (Catches: CITATION-ROT, UNCITED)

D5 NO_FABRICATED_FINDINGS Every finding's Evidence block contains a literal
                          quote from the analyzed settings.json (or the
                          settings.local.json overlay): a JSON key, a value,
                          a permissions entry, a hook command, an env-var
                          name, or a statusline string. No FABRICATED Layer-B
                          item open. In particular, a Critical finding on a
                          valid-and-parseable JSON manifest is forbidden
                          unless the evaluation guide names a
                          parse-equivalent load-bearing failure.
                          (Catches: FABRICATED-Critical false-positive class)

D6 SCOPE_DISCIPLINE       When settings.local.json is present, the report
                          body MUST surface the overlay scan (no Layer-B
                          OVERLAY-DRIFT item open) and call out any scope
                          conflict where the local broadens what the main
                          settings denies. When settings.json fails to parse,
                          the report carries exactly one Critical finding
                          citing parse failure and no further per-dimension
                          grades (Hard Rule: parse-fail = stop).
                          (Catches: OVERLAY-DRIFT, parse-fail bypass)
```

Map Layer-A failures → D3/D4/D6. Map Layer-B `MISSING` / `FABRICATED` → D5. Map `MIS-SEVERITY` → D2. Map `MIS-CITED` / `UNCITED` → D4. Map `OVERLAY-DRIFT` → D6. Map `TYPE-MISMATCH` → D3.

### Reconciliation outcomes

- **All Layer-A STRICT pass + zero Layer-B `MISSING` / `FABRICATED` / `OVERLAY-DRIFT` / `TYPE-MISMATCH`** → proceed to Phase 3.
- **Any Layer-A STRICT fail OR any of those Layer-B classes** → propose restorations inline (name each finding to add/remove with the JSON path + rubric citation), re-run Layer A on the patched report. Max two iterations. If still failing at iteration 2, surface to user and do NOT auto-write the report.
- **Only Layer-A SOFT warnings + Layer-B `MIS-SEVERITY` / `MIS-CITED` / `UNCITED` items** → record in Phase 3 Output under `### Layer-B Findings (Advisory)` and proceed. These do not block ship; reviewer triages.

### Acknowledged residuals (the pipeline does NOT catch these)

1. **Calibration drift vs the baseline** — D2 verifies severity is internally consistent with cited rubric evidence; it does NOT verify that `engineering-baseline.md` or `references/settings-evaluation-guide.md` itself is calibrated against current best practice. A stale baseline (>90 days, per CLAUDE.md) silently inflates High counts on Safety without triggering any pipeline layer. `/refresh-engineering-baseline` is out-of-band.
2. **Report-vs-tool-use-log audit** — D4's URL set is extracted from the report text; verifying each citation was actually resolved in the producing session requires reading the session JSONL under `$HOME/.claude/projects/<project>/<sessionId>.jsonl`. The pipeline does not auto-parse JSONL — Layer B asks the critic to flag obvious reconstructed-from-memory URLs but cannot prove resolution.
3. **Runtime hook behaviour** — the skill reviews `settings.json` as a static config; it cannot observe what hook scripts referenced from `hooks.*[].command` actually do at runtime (a benign-looking command may exfiltrate data once executed). The pipeline accepts config-only inspection as the contract and cannot bridge to runtime audit (which lives in `/audit-trust-chain`, `/audit-policy-compliance`, and `/review-hook`).
4. **Effective-permission semantics under overlay merge** — D6 verifies the overlay scan note exists and that obvious broadenings are surfaced; it does NOT compute the full merged-effective-permission set (Claude Code's documented merge order is project > local > user, but precedence interactions on edge cases like duplicate matchers are not exhaustively modeled here). Reviewer must spot-check effective-permission diffs on conflicting allow / deny pairs.
5. **Schema completeness vs current Claude Code release** — the evaluation guide enumerates the keys it knows about; new keys added in a Claude Code release between the 90-day refresh cycles produce no finding and no Layer-B `MISSING` (the critic is bounded by the same evaluation guide). The 90-day evidence-coverage audit is the refresh primitive.

The Output report MUST list which residual classes apply when the critic returns any `UNCERTAIN` flags or when the `settings.json` under review touches an out-of-pipeline path (novel key added by a fresh Claude Code release, complex overlay-merge edge case, etc.).

## Phase 3 — Report (standalone mode only)

1. Create the `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/` directory if it does not exist. Write to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-review-settings.md` with `repo: <slug>` and optionally `origin: <git-remote-url>` in the frontmatter (after `date`).
2. Suggest commit message.

## Hard Rules

- **Read-only on analyzed files.** Never modify settings.json. Write only to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`.
- **Apply the rubric strictly.**
- **Every High or Medium recommendation must include evidence and a concrete rewrite.**
- **Parse failure = Critical.** Invalid JSON disables ALL permission rules.

## Tier A Tool Justification

**Tier A tool justification (Bash):** Bash is granted exclusively for
`bash bin/repo-slug.sh "$(pwd)"` to compute the canonical `<repo-slug>`
deterministically per `references/repo-identification.md`. The
command-level allowlist `Bash(bash bin/repo-slug.sh:*)` enforces scope.
The script is read-only (stdout slug, no FS writes), so this Tier-A grant
carries no write-amplification risk.
